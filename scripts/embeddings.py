from openai import OpenAI
import os
import json
import numpy as np
from pathlib import Path
import pandas as pd


# see openai.com for how to set up your api key

OPEN_AI_ORG = os.environ['OPEN_AI_ORG']
EMBEDDING_MODEL_NAME = 'text-embedding-3-small'
FIELDS_TO_PARSE = []

ANNOTATION_WEIGHT = 1.0
TAG_FIRST_ENTRY_WEIGHT = 0.9
TAG_LATER_ENTRY_WEIGHT = 0.7

# Top N similar emoji

# 6 connections from annotations
# Max 12 connections from tags

# How weights get combined - asymptotic approach 1
# w1 = 0.6 w2 = 0.3 w3 = 0.1
# w123 = 1 - (1-w1)(1-w2)(1-w3) = 0.748



client = OpenAI(
    organization = OPEN_AI_ORG,
)


def is_base_emoji(emoji_data):
    if not emoji_data['skintone_base_emoji']:
        return True
    if emoji_data['skintone_base_emoji'] == emoji_data['emoji']:
        return True
    return False

# shape of dict_list: {key: [value1, value2, ...]}
def add_to_dict_list(d, key, value):
    if key not in d:
        d[key] = [value]
    else:
        d[key].append(value)

def parse_annotations(emoji_data):
    return emoji_data['annotation'].strip()

def parse_tags(emoji_data):
    tag_list = emoji_data['tags'].split(', ')
    tag_list = [tag.strip() for tag in tag_list]
    openmoji_tag_list = emoji_data['openmoji_tags'].split(', ')
    openmoji_tag_list = [tag.strip() for tag in openmoji_tag_list]
    tag_list.extend(openmoji_tag_list)
    tag_list = list(set(tag_list))
    return tag_list

def export_word_dicts(filepath, export_dir):
    with open(filepath, 'r', encoding='utf-8') as f:
        all_emoji_data = json.load(f)
    group_to_idx = {}
    subgroups_to_idx = {}
    annotations_to_idx = {}
    tags_to_idx = {}
    tags_and_annotations_to_idx = {}
    hex_to_idx = {}

    for idx, emoji_data in enumerate(all_emoji_data):

        hexcode_s = emoji_data['hexcode'].strip()
        hexcode = emoji_data['hexcode']
        if hexcode != hexcode_s:
            print('WARNING hexcode has space:', hexcode)

        hex_to_idx[hexcode] = idx


        if not is_base_emoji(emoji_data):
            continue

        group = emoji_data['group'].strip()
        subgroup = emoji_data['subgroups'].strip()
        annotation = parse_annotations(emoji_data)
        # skip groups
        if group in ['component']:
            continue

        # skip regional indicators
        if subgroup in ['regional-indicator']:
            continue


        add_to_dict_list(group_to_idx, group, idx)
        add_to_dict_list(subgroups_to_idx, subgroup, idx)
        add_to_dict_list(annotations_to_idx, annotation, idx)


        # skip flag tags
        if group == 'flags':
            continue

        tag_list = parse_tags(emoji_data)

        for tag in tag_list:
            add_to_dict_list(tags_to_idx, tag, idx)


    # remove empty tags and annotations
    for key in list(tags_to_idx.keys()):
        if not key:
            del tags_to_idx[key]
    for key in list(annotations_to_idx.keys()):
        if not key:
            del annotations_to_idx[key]

    # merge tags and annotations
    for key in annotations_to_idx.keys():
        tags_and_annotations_to_idx[key] = annotations_to_idx[key].copy()
        if key in tags_to_idx:
            tags_and_annotations_to_idx[key].extend(tags_to_idx[key])
            tags_and_annotations_to_idx[key] = list(set(tags_and_annotations_to_idx[key]))
    for key in tags_to_idx.keys():
        if key not in tags_and_annotations_to_idx:
            tags_and_annotations_to_idx[key] = tags_to_idx[key].copy()


    # print('group_to_idx:', len(group_to_idx))
    # print('subgroups_to_idx:', len(subgroups_to_idx))
    # print('annotations_to_idx:', len(annotations_to_idx))
    # print('tags_to_idx:', len(tags_to_idx))
    # print('tags_and_annotations_to_idx:', len(tags_and_annotations_to_idx))
    # print('hex_to_idx:', len(hex_to_idx))

    with open(f'{export_dir}group-to-idx.json', 'w', encoding='utf-8') as f:
        json.dump(group_to_idx, f, indent=2, ensure_ascii=False)
    with open(f'{export_dir}subgroups-to-idx.json', 'w', encoding='utf-8') as f:
        json.dump(subgroups_to_idx, f, indent=2, ensure_ascii=False)
    with open(f'{export_dir}annotations-to-idx.json', 'w', encoding='utf-8') as f:
        json.dump(annotations_to_idx, f, indent=2, ensure_ascii=False)
    with open(f'{export_dir}tags-to-idx.json', 'w', encoding='utf-8') as f:
        json.dump(tags_to_idx, f, indent=2, ensure_ascii=False)
    with open(f'{export_dir}tags-and-annotations-to-idx.json', 'w', encoding='utf-8') as f:
        json.dump(tags_and_annotations_to_idx, f, indent=2, ensure_ascii=False)
    with open(f'{export_dir}hex-to-idx.json', 'w', encoding='utf-8') as f:
        json.dump(hex_to_idx, f, indent=2, ensure_ascii=False)

    return group_to_idx, subgroups_to_idx, annotations_to_idx, tags_to_idx, tags_and_annotations_to_idx, hex_to_idx




def clean_text(text):
    text = text.replace('\n', ' ')
    return text

def get_embedding(text):
    # replace newlines, which can negatively affect performance.
    text = clean_text(text)
    response = client.embeddings.create(input=[text], model=EMBEDDING_MODEL_NAME)
    return response.data[0].embedding


def make_similarity_matrix(embeddings_filepath, output_filepath ):
    with open(embeddings_filepath, 'r', encoding='utf-8') as f:
        embeddings = json.load(f)
    embeddings_array = np.array(list(embeddings.values()))
    similarity_matrix = np.dot(embeddings_array, embeddings_array.T)
    np.save(output_filepath, similarity_matrix)
    # texts = list(embeddings.keys())
    # df = pd.DataFrame(similarity_matrix, index=texts, columns=texts)
    # df.to_excel(output_filepath + '.xlsx')

def make_top_n_similar_text(similarity_matrix_filepath, output_dir, texts, n):
    similarity_matrix = np.load(similarity_matrix_filepath)
    assert similarity_matrix.shape[0] == len(texts)
    assert similarity_matrix.shape[1] == len(texts)

    top_n_similar_idxs = np.argsort(similarity_matrix, axis=1)[:, -n-1:-1]
    # print(top_n_similar_idxs.shape)
    # (5313, 10)


    top_n_similar_dict = {}

    for i, text in enumerate(texts):
        top_n_similar_to_text = {}
        for j in reversed(range(n)):
            similar_text_idx = top_n_similar_idxs[i, j]
            similar_text = texts[similar_text_idx]
            similarity = similarity_matrix[i, similar_text_idx]
            top_n_similar_to_text[similar_text] = similarity

        top_n_similar_dict[text] = top_n_similar_to_text

    with open(f'{output_dir}top_{n}_similar.json', 'w', encoding='utf-8') as f:
        json.dump(top_n_similar_dict, f, indent=2, ensure_ascii=False)


def adjust_similar_text_by_weight(similar_text_dict, first_weight, later_weights):
    first_processed = False
    for text, similarity in similar_text_dict.items():
        if not first_processed:
            similar_text_dict[text] = similarity * first_weight
            first_processed = True
        else:
            similar_text_dict[text] = similarity * later_weights
    return similar_text_dict

def make_top_n_similar_emoji(top_n_similar_text_filepath, output_dir, emoji_json_filepath, tags_and_annotations_to_idx_filepath, n):
    '''


    '''
    with open(top_n_similar_text_filepath, 'r', encoding='utf-8') as f:
        top_n_similar_text_dict = json.load(f)
    with open(emoji_json_filepath, 'r', encoding='utf-8') as f:
        all_emoji_data = json.load(f)
    with open(tags_and_annotations_to_idx_filepath, 'r', encoding='utf-8') as f:
        tags_and_annotations_to_idx = json.load(f)
    
    similar_emojis_all = {}
    for idx, emoji_data in enumerate(all_emoji_data):
        if not is_base_emoji(emoji_data):
            continue
        annotation = parse_annotations(emoji_data)
        tag_list = parse_tags(emoji_data)
        tag_list = [tag for tag in tag_list if tag not in annotation]

        similar_texts = top_n_similar_text_dict.get(annotation, {})
        similar_texts = adjust_similar_text_by_weight(similar_texts, ANNOTATION_WEIGHT, ANNOTATION_WEIGHT)

        for tag in tag_list:
            similar_text_tag = top_n_similar_text_dict.get(tag, {})
            similar_text_tag = adjust_similar_text_by_weight(similar_text_tag, TAG_FIRST_ENTRY_WEIGHT, TAG_LATER_ENTRY_WEIGHT)
            for text, similarity in similar_text_tag.items():
                if text not in similar_texts:
                    similar_texts[text] = similarity
                elif similar_texts[text] < similarity:
                    similar_texts[text] = similarity
                else:
                    pass

        similar_emojis_to_emoji = {}
        for text in similar_texts:
            assert text in tags_and_annotations_to_idx
            similar_emojis = tags_and_annotations_to_idx[text]
            for emoji_idx in similar_emojis:
                if emoji_idx == idx:
                    continue
                if emoji_idx in similar_emojis_to_emoji:
                    w1 = similar_emojis_to_emoji[emoji_idx]
                    w2 = similar_texts[text]
                    w12 = 1.0 - (1.0-w1)*(1.0-w2)
                    similar_emojis_to_emoji[emoji_idx] = w12
                else:
                    similar_emojis_to_emoji[emoji_idx] = similar_texts[text]
        similar_emojis_to_emoji = dict(sorted(similar_emojis_to_emoji.items(), key=lambda item: item[1], reverse=True))
        similar_emojis_to_emoji_dict = {'idxs': [], 'weights': []}
        similar_emojis_to_emoji_dict['idxs'] = list(similar_emojis_to_emoji.keys())[:n]
        similar_emojis_to_emoji_dict['weights'] = list(similar_emojis_to_emoji.values())[:n]


         

        similar_emojis_all[idx] = similar_emojis_to_emoji_dict
        
    with open(f'{output_dir}top_{n}_similar_emojis.json', 'w', encoding='utf-8') as f:
        json.dump(similar_emojis_all, f, indent=2, ensure_ascii=False)
                    


        
        

def make_embeddings(output_filepath, texts, max_count = -1, update_existing=True):
    '''
    set mex_count to -1 to get all embeddings
    '''
    save_every = 100
    path = Path(output_filepath)
    data = {}

    if update_existing and path.is_file():
        with open(output_filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

    
    for text in texts:
        if len(data) >= max_count and max_count != -1:
            break
        if text in data:
            continue
        embedding = get_embedding(text)
        data[text] = embedding
        if len(data) % save_every == 0:
            print(f'entires: {len(data)} saving...')
            with open(output_filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)




    with open(output_filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    

def get_top_n_frequent_emoji(tsv_filepath, n=None):
    df = pd.read_csv(tsv_filepath, sep='\t')
    top_n_emoji = df.loc[:n, 'Emoji'].tolist()
    return top_n_emoji



if __name__ == '__main__':
    data_dir = '../src/assets/data/'

    (group_to_idx,
    subgroups_to_idx, 
    annotations_to_idx, 
    tags_to_idx, 
    tags_and_annotations_to_idx, 
    hex_to_idx
    ) = export_word_dicts(f'{data_dir}openmoji.json', data_dir)

    print('group_to_idx:', len(group_to_idx))
    print('subgroups_to_idx:', len(subgroups_to_idx))
    print('annotations_to_idx:', len(annotations_to_idx))
    print('tags_to_idx:', len(tags_to_idx))
    print('tags_and_annotations_to_idx:', len(tags_and_annotations_to_idx))
    print('hex_to_idx:', len(hex_to_idx))



    # embeddings_path = 'embeddings.json'
    # texts = list(tags_and_annotations_to_idx.keys())
    # make_embeddings(embeddings_path, texts, -1, update_existing=True )
 
    # make_similarity_matrix(embeddings_path, 'similarity_matrix.npy')
    # make_top_n_similar_text('similarity_matrix.npy', '', texts, 30)

    make_top_n_similar_emoji('top_30_similar.json', '', f'{data_dir}openmoji.json', f'{data_dir}tags-and-annotations-to-idx.json', 30)

    # --- embeddings for 2021 frequent emojis ---

    # frequent_emojis = get_top_n_frequent_emoji(f'2021_ranked.tsv')
    # frequent_emoji_embeddings_path = 'frequent_emoji_embeddings.json'

    # make_embeddings(frequent_emoji_embeddings_path, frequent_emojis, -1, update_existing=True )

    # make_similarity_matrix(frequent_emoji_embeddings_path, 'frequent_emoji_similarity_matrix.npy')
    # make_top_n_similar_text('frequent_emoji_similarity_matrix.npy', 'frequent_emoji_', frequent_emojis, 30)