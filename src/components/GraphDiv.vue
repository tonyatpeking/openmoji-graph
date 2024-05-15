<script setup lang="ts">
import { ref, onMounted } from "vue";
//import { invoke } from "@tauri-apps/api/tauri";
import openMojiData from '../assets/data/openmoji.json';
import topSimilarEmoji from '../assets/data/top_30_similar_emojis.json';
import specialCases from '../assets/data/special-cases.json';
import ForceGraph3D from '3d-force-graph';
import { SVGLoader } from 'three/addons/loaders/SVGLoader.js';
import * as THREE from 'three';
import { forceCollide, forceManyBody, forceLink, forceCenter } from 'd3-force-3d';
import { useResizeObserver } from '@vueuse/core'


const DEBUG_COUNT = 200
const loadingManager = new THREE.LoadingManager();
const loader = new SVGLoader(loadingManager);



// Node styling
const NODE_OPACITY = 1;
const NodeCollisionRadius = 30;
const SVGOffsetX = -36;
const SVGOffsetY = 36;

// Link styling
const LINK_WIDTH = 3;
const LINK_RESOLUTION = 2;
const LINK_OPACITY = 1;
const LINK_COUNT = 10

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

const linkMaterial = new THREE.MeshBasicMaterial()
linkMaterial.color.set(.2, .2, .2)


const displayData: any = {
  nodes: [],
  links: []
}

let startingNodeIdx = 3;


// returned array in the shape of [{id: similarity}, ...]
function getTopNSimilarIdxs(idx: Number, n: Number) {

  let topIdxs = topSimilarEmoji[idx.toString()].idxs.slice(0, n);
  return topIdxs;
}

function getTopNSimilarWeights(idx: Number, n: Number) {
  let topWeights = topSimilarEmoji[idx.toString()].weights.slice(0, n);
  return topWeights;
}

function getNode(nodeIdx: number) {
  return displayData.nodes.find((node: any) => node.id == nodeIdx);
}


function addOrGetNode(nodeIdx: number) {
  let node = getNode(nodeIdx);
  if (!node) {
    node = { id: nodeIdx, outLinks: [], inLinks: [], parant: null, children: [], expanded: false };
    displayData.nodes.push(node);
  }
  return node;
}

// also removes any links connected to the node
function removeNode(nodeToRemove: any) {

  // copy the array because removeLink modifies the array
  let outLinks = [...nodeToRemove.outLinks];
  for (let i = 0; i < outLinks.length; i++) {
    let link = outLinks[i];
    let targetNode = link.target;
    removeLink(nodeToRemove, targetNode);
  }
  let inLinks = [...nodeToRemove.inLinks];
  for (let i = 0; i < inLinks.length; i++) {
    let link = inLinks[i];
    let sourceNode = link.source;
    removeLink(sourceNode, nodeToRemove);
  }
  displayData.nodes = displayData.nodes.filter((node: any) => node.id != nodeToRemove.id);
}


function getLink(sourceNode: any, targetNode: any) {
  return displayData.links.find((link: any) => link.source.id == sourceNode.id && link.target.id == targetNode.id);
}

// also adds to source and target node outLinks and inLinks
function addOrGetLink(sourceNode: any, targetNode: any, weight: number) {
  let link = getLink(sourceNode, targetNode);
  if (!link) {
    link = { source: sourceNode, target: targetNode, weight: weight }
    displayData.links.push(link);
    sourceNode.outLinks.push(link);
    targetNode.inLinks.push(link);
  }
  return link
}

// also removes from source and target node outLinks and inLinks
function removeLink(sourceNode: any, targetNode: any) {
  let link = getLink(sourceNode, targetNode);
  if (!link) {
    return;
  }
  link.source.outLinks = link.source.outLinks.filter((l: any) => l != link);
  link.target.inLinks = link.target.inLinks.filter((l: any) => l != link);
  displayData.links = displayData.links.filter((l: any) => l != link);
}


function toggleNodeExpansion(node: any) {
  if (node.expanded) {
    collapseNode(node, node);
  } else {
    expandNode(node);
  }
  node.expanded = !node.expanded;
  Graph.graphData(displayData);
}

function expandNode(sourceNode: any) {
  // get top x similar emojis
  const topIdxs = getTopNSimilarIdxs(sourceNode.id, LINK_COUNT);
  const topWeights = getTopNSimilarWeights(sourceNode.id, LINK_COUNT);
  for (let i = 0; i < topIdxs.length; i++) {
    let idx = topIdxs[i];
    let weight = topWeights[i];
    let targetNode = addOrGetNode(idx);
    addOrGetLink(sourceNode, targetNode, weight);
  }

}

function collapseNode(node: any, initialCallerNode: any) {

  let outLinks = node.outLinks;
  for (let i = 0; i < outLinks.length; i++) {
    let link = outLinks[i];
    let targetNode = link.target;

    removeLink(node, targetNode);

    // don't collapse or remove the initial node that called this function
    if (targetNode.id == initialCallerNode.id) {
      console.log("Skipping collapse of initial caller node")
      continue;
    }

    if (targetNode.inLinks.length == 0) {
      collapseNode(targetNode, initialCallerNode);

    }
    removeNode(targetNode)
  }

}


// Finished loading all svg files
loadingManager.onLoad = function () {
  console.log('Loading complete!');
  console.log(loadedEmojis);

  loadedEmojisIndexed = new Map([...loadedEmojis.entries()].map(([_, v], i) => [i, v]));

  Graph = ForceGraph3D({ controlType: 'orbit' })
    (canvasDiv.value!)
    .nodeRelSize(NodeCollisionRadius)
    .nodeOpacity(NODE_OPACITY)

  Graph
    .nodeThreeObject((o: any) => {
      let obj = loadedEmojisIndexed.get(o.id)
      if (obj) {
        return obj.clone()
      }
      return null

    })
    .graphData(displayData)
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

  // Link styling
  Graph.linkWidth(LINK_WIDTH)
    .linkResolution(LINK_RESOLUTION)
    .linkOpacity(LINK_OPACITY)
    .linkMaterial(linkMaterial);

  Graph.d3Force('link')!
    .distance(60)
    .strength(0.2);



  // Click
  Graph.onNodeClick((engineNode: any) => {
    const node = getNode(engineNode.id);
    toggleNodeExpansion(node);
  });

  // Hover
  Graph.onNodeHover((node, prevNode) => { console.log(node); console.log(prevNode); })


  // let tigerUrl = `${import.meta.env.BASE_URL}tiger.svg`
  //loadSVGtoScene(tigerUrl, Graph.scene());


  let renderer = Graph.renderer();

  let { nodes, links } = Graph.graphData();

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
// const gData = {
//   nodes: [...Array(N).keys()].map(i => ({ id: i, fz: 0 })),
//   links: [...Array(N).keys()]
//     .filter(id => id)
//     .map(id => ({
//       source: id,
//       target: Math.round(Math.random() * (id - 1))
//     }))
// };

addOrGetNode(startingNodeIdx);


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
  if (Graph) {
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