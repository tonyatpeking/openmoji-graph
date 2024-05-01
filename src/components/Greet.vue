<script setup lang="ts">
import { ref } from "vue";
import { invoke } from "@tauri-apps/api/tauri";
import openmoji_data from '../assets/data/openmoji.json';
import special_cases from '../assets/data/special-cases.json';


const greetMsg = ref("");
const name = ref("");

const om = openmoji_data[0]
console.log(om)
const count = openmoji_data.length
console.log(count)
let str = ""
const ZERO_WIDTH_JOINER = "\u200D";

let valid_count = 0
for (let i = 0; i < count; i++) {

  if(openmoji_data[i].skintone_base_emoji != ""){
    continue;
  }
  if (openmoji_data[i].subgroups == "skin-tone"){
    continue;
  }
  if (openmoji_data[i].subgroups == "regional-indicator"){
    continue;
  }

  


  let emoji = openmoji_data[i].emoji

  // add zero width joiner if missing
  // is compatible if this gets updated
  if(special_cases.missing_zero_width_joiner.includes(emoji) ){
    emoji = emoji.replace(ZERO_WIDTH_JOINER, "")
    emoji = [...emoji].join(ZERO_WIDTH_JOINER)
  }
  else if(special_cases.missing_font.includes(emoji) ){
    continue;
  }
  str += emoji
  valid_count += 1
  //console.log(openmoji_data[i].hexcode)
  if (valid_count % 20 == 0) {
  str += "\n"
}
}


//str = String.fromCodePoint(0x2B21, 0xFE0F,  0x1F7EB)

async function greet() {
  // Learn more about Tauri commands at https://tauri.app/v1/guides/features/command
  greetMsg.value = await invoke("greet", { name: name.value });
}
</script>

<template>
  <form class="row" @submit.prevent="greet">
    <input id="greet-input" v-model="name" placeholder="Enter a name..." />
    <button type="submit">Greet</button>
    <button>Count is: {{ count }}</button>


  </form>
  <div class="openmoji-color">ABC 👨‍💻 &#x1F976;  XYZ &#x1F4BB; &#x1F468; &#x1F9DF; Lorem &#xE380;  ipsum &#x1F4AF;</div><div class="openmoji-black">ABC 👨‍💻 &#x1F976;  XYZ &#x1F4BB; &#x1F468; &#x1F9DF; Lorem &#xE380;  ipsum &#x1F4AF;</div>
  <div class="openmoji-color">{{str}}</div>
  <p>{{ greetMsg }}</p>
</template>

<style>
@font-face {
  font-family: OpenMojiColorFont;
  src: url('../assets/fonts/OpenMoji-color-glyf_colr_0.woff2') format('woff2');
}
@font-face {
  font-family: OpenMojiBlack;
  src: url('../assets/fonts/OpenMoji-black-glyf.woff2') format('woff2');
}

.openmoji-color {
  white-space: pre-line;
  font-family: OpenMojiColorFont, sans-serif;
}
.openmoji-black {
  font-family: OpenMojiBlack, sans-serif;
}
</style>