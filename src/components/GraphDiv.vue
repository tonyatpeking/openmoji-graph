<script setup lang="ts">
import { ref, onMounted } from "vue";
//import { invoke } from "@tauri-apps/api/tauri";
import openmoji_data from '../assets/data/openmoji.json';
import special_cases from '../assets/data/special-cases.json';
import ForceGraph3D from '3d-force-graph';
import { SVGLoader } from 'three/addons/loaders/SVGLoader.js';
import * as THREE from 'three';
import tigerUrl from '../assets/tiger.svg';

const greetMsg = ref("");

const om = openmoji_data[0]
console.log(om)
const count = openmoji_data.length
console.log(count)
let str = ""
const ZERO_WIDTH_JOINER = "\u200D";


// Display all emojis
let valid_count = 0
for (let i = 0; i < count; i++) {


  const emoji_data = openmoji_data[i]
  let emoji = emoji_data.emoji
  let annotation = emoji_data.annotation;
  if (annotation == "") {
    console.log(`WARNING empty annotation ${emoji}`)
  }
  else if (annotation.includes(":")) {
    //console.log(`Variation ${emoji}`)
    continue
  }
  if (emoji_data.subgroups == "skin-tone") {
    continue;
  }
  if (emoji_data.subgroups == "regional-indicator") {
    continue;
  }



  // add zero width joiner if missing
  // is compatible if this gets updated
  if (special_cases.missing_zero_width_joiner.includes(emoji)) {
    emoji = emoji.replace(ZERO_WIDTH_JOINER, "")
    emoji = [...emoji].join(ZERO_WIDTH_JOINER)
  }
  else if (special_cases.missing_font.includes(emoji)) {
    continue;
  }
  str += emoji
  valid_count += 1
  //console.log(openmoji_data[i].hexcode)
  if (valid_count % 15 == 0) {
    str += "\n"
  }
}


// Graph Data
const N = 300;
const gData = {
  nodes: [...Array(N).keys()].map(i => ({ id: i })),
  links: [...Array(N).keys()]
    .filter(id => id)
    .map(id => ({
      source: id,
      target: Math.round(Math.random() * (id - 1))
    }))
};


// SVG test
function loadSVG(url: string, scene: THREE.Scene) {
  console.log(url);
  const helper = new THREE.GridHelper(160, 10, 0x8d8d8d, 0xc1c1c1);
  helper.rotation.x = Math.PI / 2;
  scene.add(helper);
  const loader = new SVGLoader();
  loader.load(url, function (data) {
    const group = new THREE.Group();
    group.scale.multiplyScalar(0.25);
    group.position.x = - 70;
    group.position.y = 70;
    group.scale.y *= - 1;
    console.log(url)
    console.log(data)
    let renderOrder = 0;
    for (const path of data.paths) {
      if (!path.userData) {
        continue;
      }
      const fillColor = path.userData.style.fill;
      if (fillColor !== undefined && fillColor !== 'none') {
        const material = new THREE.MeshBasicMaterial({
          color: new THREE.Color().setStyle(fillColor),
          opacity: path.userData.style.fillOpacity,
          transparent: true,
          side: THREE.DoubleSide,
          depthWrite: false
        });
        const shapes = SVGLoader.createShapes(path);
        for (const shape of shapes) {
          const geometry = new THREE.ShapeGeometry(shape);
          const mesh = new THREE.Mesh(geometry, material);
          mesh.renderOrder = renderOrder++;
          group.add(mesh);
        }
      }
      const strokeColor = path.userData.style.stroke;
      if (strokeColor !== undefined && strokeColor !== 'none') {
        const material = new THREE.MeshBasicMaterial({
          color: new THREE.Color().setStyle(strokeColor),
          opacity: path.userData.style.strokeOpacity,
          transparent: true,
          side: THREE.DoubleSide,
          depthWrite: false
        });
        for (const subPath of path.subPaths) {
          const geometry = SVGLoader.pointsToStroke(subPath.getPoints(), path.userData.style);
          if (geometry) {
            const mesh = new THREE.Mesh(geometry, material);
            mesh.renderOrder = renderOrder++;
            group.add(mesh);
          }
        }
      }
    }
    scene.add(group);
  });

}


// Mount
let canvas_div = ref<HTMLDivElement>();

onMounted(() => {
  const Graph = ForceGraph3D()
    (canvas_div.value!)
    .graphData(gData);
  console.log(Graph.height());
  loadSVG(tigerUrl, Graph.scene());
})



</script>

<template>
  <div ref="canvas_div"></div>
  <div class="openmoji-color">{{ str }}</div>
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