<script setup lang="ts">
import { ref, onMounted } from "vue";
//import { invoke } from "@tauri-apps/api/tauri";
import openMojiData from '../assets/data/openmoji.json';
import specialCases from '../assets/data/special-cases.json';
import ForceGraph3D from '3d-force-graph';
import { SVGLoader } from 'three/addons/loaders/SVGLoader.js';
import * as THREE from 'three';

const DEBUG_COUNT = 300
const loadingManager = new THREE.LoadingManager();
const loader = new SVGLoader(loadingManager);

const greetMsg = ref("");

const om = openMojiData[0]
console.log(om)
const count = openMojiData.length
console.log(count)
let str = ""
const ZERO_WIDTH_JOINER = "\u200D";

let loadedEmojis = new Map<string, THREE.Object3D>();
let loadedEmojisIndexed = new Map<number, THREE.Object3D>();

// Finished loading all svg files
loadingManager.onLoad = function () {
  console.log('Loading complete!');
  console.log(loadedEmojis);

  loadedEmojisIndexed = new Map([...loadedEmojis.entries()].map(([_, v], i) => [i, v]));

  const Graph = ForceGraph3D()
    (canvasDiv.value!)
    .nodeThreeObject((o: any) => { return loadedEmojisIndexed.get(o.id)! })
    .graphData(gData);
  console.log(Graph.length);
  //loadSVGtoScene(tigerUrl, Graph.scene());
};

// Display all emojis
let validCount = 0
for (let i = 0; i < count; i++) {


  const emojiData = openMojiData[i]
  let emoji = emojiData.emoji
  let annotation = emojiData.annotation;
  if (annotation == "") {
    console.log(`WARNING empty annotation ${emoji}`)
  }
  else if (annotation.includes(":")) {
    //console.log(`Variation ${emoji}`)
    continue
  }
  if (emojiData.subgroups == "skin-tone") {
    continue;
  }
  if (emojiData.subgroups == "regional-indicator") {
    continue;
  }



  // add zero width joiner if missing
  // is compatible if this gets updated
  if (specialCases.missingZeroWidthJoiner.includes(emoji)) {
    emoji = emoji.replace(ZERO_WIDTH_JOINER, "")
    emoji = [...emoji].join(ZERO_WIDTH_JOINER)
  }
  else if (specialCases.missingFont.includes(emoji)) {
    continue;
  }
  str += emoji
  validCount += 1
  if (validCount % 15 == 0) {
    str += "\n"
  }
}



// Graph Data
const N = DEBUG_COUNT;
const gData = {
  nodes: [...Array(N).keys()].map(i => ({ id: i })),
  links: [...Array(N).keys()]
    .filter(id => id)
    .map(id => ({
      source: id,
      target: Math.round(Math.random() * (id - 1))
    }))
};


function loadSVG(loader: SVGLoader, url: string, id: string) {
  loader.load(url, function (data: any) {
    const group = new THREE.Group();
    group.scale.multiplyScalar(0.25);
    group.position.x = - 70;
    group.position.y = 70;
    group.scale.y *= - 1;
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
    loadedEmojis.set(id, group);
  });
}

function loadAllSVG(loader: SVGLoader) {
  let count = 0

  for (let i = 0; i < openMojiData.length; i++) {
    const emojiData = openMojiData[i]
    let emoji = emojiData.emoji
    let annotation = emojiData.annotation;
    if (annotation == "") {
      console.log(`WARNING empty annotation ${emoji}`)
    }
    else if (annotation.includes(":")) {
      //console.log(`Variation ${emoji}`)
      continue
    }
    if (emojiData.subgroups == "skin-tone") {
      continue;
    }
    if (emojiData.subgroups == "regional-indicator") {
      continue;
    }

    // add zero width joiner if missing
    // is compatible if this gets updated
    if (specialCases.missingZeroWidthJoiner.includes(emoji)) {
      emoji = emoji.replace(ZERO_WIDTH_JOINER, "")
      emoji = [...emoji].join(ZERO_WIDTH_JOINER)
    }
    else if (specialCases.missingFont.includes(emoji)) {
      continue;
    }
    console.log(import.meta.env.BASE_URL)
    const url = `${import.meta.env.BASE_URL}openmoji/color/svg/${emojiData.hexcode}.svg`
    loadSVG(loader, url, emojiData.hexcode)
    count += 1;
    if (count > DEBUG_COUNT) {
      break;
    }
  }
}
// SVG test
function loadSVGtoScene(url: string, scene: THREE.Scene) {
  console.log(url);
  const helper = new THREE.GridHelper(160, 10, 0x8d8d8d, 0xc1c1c1);
  helper.rotation.x = Math.PI / 2;
  scene.add(helper);
  const loader = new SVGLoader();
  loader.load(url, function (data: any) {
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
let canvasDiv = ref<HTMLDivElement>();

onMounted(() => {
  loadAllSVG(loader);

})



</script>

<template>
  <div ref="canvasDiv"></div>
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