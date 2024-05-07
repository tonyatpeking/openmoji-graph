from openai import OpenAI
import os
import json
import numpy as np
from pathlib import Path
import pandas as pd


# see openai.com for how to set up your api key

OPEN_AI_ORG = 'YOUR_ORG_KEY'
EMBEDDING_MODEL_NAME = 'text-embedding-3-small'
FIELDS_TO_PARSE = []

client = OpenAI(
    organization = OPEN_AI_ORG,
)


def is_base_emoji(emoji):
    if not emoji['skintone_base_emoji']:
        return True
    if emoji['skintone_base_emoji'] == emoji['emoji']:
        return True
    return False

# shape of dict_list: {key: [value1, value2, ...]}
def add_to_dict_list(d, key, value):
    if key not in d:
        d[key] = [value]
    else:
        d[key].append(value)

def export_word_dicts(filepath, export_dir):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    group_to_hex = {}
    subgroups_to_hex = {}
    annotations_to_hex = {}
    tags_to_hex = {}
    tags_and_annotations_to_hex = {}
    hex_to_idx = {}

    for idx, emoji in enumerate(data):

        hexcode_s = emoji['hexcode'].strip()
        hexcode = emoji['hexcode']
        if hexcode != hexcode_s:
            print('WARNING hexcode has space:', hexcode)

        hex_to_idx[hexcode] = idx


        if not is_base_emoji(emoji):
            continue

        group = emoji['group'].strip()
        subgroup = emoji['subgroups'].strip()
        annotation = emoji['annotation'].strip()
        # skip groups
        if group in ['component']:
            continue

        # skip regional indicators
        if subgroup in ['regional-indicator']:
            continue


        add_to_dict_list(group_to_hex, group, hexcode)
        add_to_dict_list(subgroups_to_hex, subgroup, hexcode)
        add_to_dict_list(annotations_to_hex, annotation, hexcode)


        # skip flag tags
        if group == 'flags':
            continue

        tag_list = emoji['tags'].split(', ')
        tag_list = [tag.strip() for tag in tag_list]
        openmoji_tag_list = emoji['openmoji_tags'].split(', ')
        openmoji_tag_list = [tag.strip() for tag in openmoji_tag_list]
        tag_list.extend(openmoji_tag_list)
        tag_list = list(set(tag_list))

        for tag in tag_list:
            add_to_dict_list(tags_to_hex, tag, hexcode)


    # remove empty tags and annotations
    for key in list(tags_to_hex.keys()):
        if not key:
            del tags_to_hex[key]
    for key in list(annotations_to_hex.keys()):
        if not key:
            del annotations_to_hex[key]

    # merge tags and annotations
    for key in annotations_to_hex.keys():
        tags_and_annotations_to_hex[key] = annotations_to_hex[key].copy()
        if key in tags_to_hex:
            tags_and_annotations_to_hex[key].extend(tags_to_hex[key])
            tags_and_annotations_to_hex[key] = list(set(tags_and_annotations_to_hex[key]))
    for key in tags_to_hex.keys():
        if key not in tags_and_annotations_to_hex:
            tags_and_annotations_to_hex[key] = tags_to_hex[key].copy()


    # print('group_to_hex:', len(group_to_hex))
    # print('subgroups_to_hex:', len(subgroups_to_hex))
    # print('annotations_to_hex:', len(annotations_to_hex))
    # print('tags_to_hex:', len(tags_to_hex))
    # print('tags_and_annotations_to_hex:', len(tags_and_annotations_to_hex))
    # print('hex_to_idx:', len(hex_to_idx))

    with open(f'{export_dir}group-to-hex.json', 'w', encoding='utf-8') as f:
        json.dump(group_to_hex, f, indent=2, ensure_ascii=False)
    with open(f'{export_dir}subgroups-to-hex.json', 'w', encoding='utf-8') as f:
        json.dump(subgroups_to_hex, f, indent=2, ensure_ascii=False)
    with open(f'{export_dir}annotations-to-hex.json', 'w', encoding='utf-8') as f:
        json.dump(annotations_to_hex, f, indent=2, ensure_ascii=False)
    with open(f'{export_dir}tags-to-hex.json', 'w', encoding='utf-8') as f:
        json.dump(tags_to_hex, f, indent=2, ensure_ascii=False)
    with open(f'{export_dir}tags-and-annotations-to-hex.json', 'w', encoding='utf-8') as f:
        json.dump(tags_and_annotations_to_hex, f, indent=2, ensure_ascii=False)
    with open(f'{export_dir}hex-to-idx.json', 'w', encoding='utf-8') as f:
        json.dump(hex_to_idx, f, indent=2, ensure_ascii=False)

    return group_to_hex, subgroups_to_hex, annotations_to_hex, tags_to_hex, tags_and_annotations_to_hex, hex_to_idx




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

def make_top_n_similar(similarity_matrix_filepath, output_dir, texts, n):
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
    

if __name__ == '__main__':
    data_dir = '../src/assets/data/'

    (group_to_hex,
    subgroups_to_hex, 
    annotations_to_hex, 
    tags_to_hex, 
    tags_and_annotations_to_hex, 
    hex_to_idx
    ) = export_word_dicts(f'{data_dir}openmoji.json', data_dir)

    print('group_to_hex:', len(group_to_hex))
    print('subgroups_to_hex:', len(subgroups_to_hex))
    print('annotations_to_hex:', len(annotations_to_hex))
    print('tags_to_hex:', len(tags_to_hex))
    print('tags_and_annotations_to_hex:', len(tags_and_annotations_to_hex))
    print('hex_to_idx:', len(hex_to_idx))

    embeddings_path = 'embeddings.json'
    texts = list(tags_and_annotations_to_hex.keys())

    # make_embeddings(embeddings_path, texts, -1, update_existing=True )
 
    # make_similarity_matrix(embeddings_path, 'similarity_matrix.npy')
    make_top_n_similar('similarity_matrix.npy', '', texts, 30)


    # eb = get_embedding('pine decoration')
    # eb1 = get_embedding('bamboo')
    # eb = np.array(eb)
    # eb1 = np.array(eb1)
    # d = np.dot(eb,eb1)
    # print(d)