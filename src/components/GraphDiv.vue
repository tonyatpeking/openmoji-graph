<script setup lang="ts">
import { ref, onMounted } from "vue";
//import { invoke } from "@tauri-apps/api/tauri";
import openMojiData from '../assets/data/openmoji.json';
import specialCases from '../assets/data/special-cases.json';
import ForceGraph3D from '3d-force-graph';
import { SVGLoader } from 'three/addons/loaders/SVGLoader.js';
import * as THREE from 'three';
import { forceCollide, forceManyBody, forceLink, forceCenter } from 'd3-force-3d';
import { useResizeObserver } from '@vueuse/core'

const DEBUG_COUNT = 100
const loadingManager = new THREE.LoadingManager();
const loader = new SVGLoader(loadingManager);
const SVGOffsetX = -36;
const SVGOffsetY = 36;
const NodeCollisionRadius = 30;

const greetMsg = ref("");

const om = openMojiData[0]
console.log(om)
const count = openMojiData.length
console.log(count)
let str = ""
const ZERO_WIDTH_JOINER = "\u200D";

let loadedEmojis = new Map<string, THREE.Object3D>();
let loadedEmojisIndexed = new Map<number, THREE.Object3D>();

let Graph: any = null;

// Finished loading all svg files
loadingManager.onLoad = function () {
  console.log('Loading complete!');
  console.log(loadedEmojis);

  loadedEmojisIndexed = new Map([...loadedEmojis.entries()].map(([_, v], i) => [i, v]));

  Graph = ForceGraph3D({controlType: 'orbit'})
    (canvasDiv.value!)
    .nodeRelSize(NodeCollisionRadius);


  Graph
    .nodeThreeObject((o: any) => { return loadedEmojisIndexed.get(o.id)! })
    .graphData(gData)
    .numDimensions(2)
    .onNodeDrag((node: any) => {
      // setting fx and fy will pin the node
      //node.fx = node.x;
      //node.fy = node.y;
      node.z = 0;
    });

  Graph.d3Force('collide', forceCollide(Graph.nodeRelSize()))

  Graph.d3Force('charge')!
    .strength(-300)
    .distanceMin(1)
    .distanceMax(300);


  Graph.d3Force('link')!
    .distance(30)
    .strength(1);
  console.log(Graph.length);
  let tigerUrl = `${import.meta.env.BASE_URL}tiger.svg`
  //loadSVGtoScene(tigerUrl, Graph.scene());


  let renderer = Graph.renderer();

  let { nodes, links } = Graph.graphData();
  console.log(nodes);

  const controls = Graph.controls();

  controls.mouseButtons.LEFT = THREE.MOUSE.PAN; 
  controls.mouseButtons.MIDDLE = THREE.MOUSE.DOLLY; 
  controls.mouseButtons.RIGHT = undefined; 
  controls.touches.ONE = THREE.TOUCH.PAN;
  controls.touches.TWO = THREE.TOUCH.DOLLY_PAN;

  let scene = Graph.scene();
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
  nodes: [...Array(N).keys()].map(i => ({ id: i, fz: 0 })),
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
          mesh.position.x += SVGOffsetX;
          mesh.position.y += SVGOffsetY;
          mesh.scale.y *= -1;
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
            mesh.position.x += SVGOffsetX;
            mesh.position.y += SVGOffsetY;
            mesh.scale.y *= -1;
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

// container resize
useResizeObserver(canvasDiv, (entries) => {
  console.log(entries[0].contentRect.width, entries[0].contentRect.height)
  if(Graph) {
    Graph.width(entries[0].contentRect.width);
    Graph.height(entries[0].contentRect.height);
  }
})

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