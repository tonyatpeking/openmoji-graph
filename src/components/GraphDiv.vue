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

// Types

interface Node {
  id: number;
  outLinks: Link[];
  inLinks: Link[];
  expanded: boolean;
  mesh: THREE.Object3D | null;
}

interface Link {
  source: Node;
  target: Node;
  weight: number;
}



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


let allEmojiStr = ref("")
const ZERO_WIDTH_JOINER = "\u200D";


let Graph: any = null;

const linkMaterial = new THREE.MeshBasicMaterial()
linkMaterial.color.set(.2, .2, .2)


const displayData: { nodes: Node[], links: Link[] } = {
  nodes: [],
  links: []
}

let startingNodeIdx = 3;

// Finished loading all svg files
function initGraph() {


  Graph = ForceGraph3D({ controlType: 'orbit' })(canvasDiv.value!)

  Graph.backgroundColor('#040e36')
    .showNavInfo(false)



  Graph
    .nodeRelSize(NodeCollisionRadius)
    .nodeOpacity(NODE_OPACITY)
    .nodeThreeObject((o: any) => {
      return o.mesh;
    })
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
    .linkMaterial(linkMaterial)
    .linkDirectionalArrowLength(13)
    .linkDirectionalArrowRelPos(1)
    .linkDirectionalArrowResolution(4)
  // .linkDirectionalParticles(2)
  // .linkDirectionalParticleSpeed(0.007)
  // .linkDirectionalParticleWidth(5)
  // .linkDirectionalParticleResolution(4);

  Graph.d3Force('link')!
    .distance(80)
    .strength(0.1);


  // Click
  Graph.onNodeClick((engineNode: any) => {
    const node = getNode(engineNode.id);
    toggleNodeExpansion(node);
  });

  // Hover
  //Graph.onNodeHover((node, prevNode) => { console.log(node); console.log(prevNode); })

  // Threejs camera controls
  const controls = Graph.controls();
  controls.mouseButtons.LEFT = THREE.MOUSE.PAN;
  controls.mouseButtons.MIDDLE = THREE.MOUSE.DOLLY;
  controls.mouseButtons.RIGHT = undefined;
  controls.touches.ONE = THREE.TOUCH.PAN;
  controls.touches.TWO = THREE.TOUCH.DOLLY_PAN;

  Graph.graphData(displayData);

};


// returned array in the shape of [{id: similarity}, ...]
function getTopNSimilarIdxs(idx: Number, n: Number) {

  let topIdxs = topSimilarEmoji[idx.toString()].idxs.slice(0, n);
  return topIdxs;
}

function getTopNSimilarWeights(idx: Number, n: Number) {
  let topWeights = topSimilarEmoji[idx.toString()].weights.slice(0, n);
  return topWeights;
}

function getNode(nodeIdx: number): Node | undefined {
  return displayData.nodes.find((node: any) => node.id == nodeIdx);
}


function loadOrGetNode(nodeIdx: number): Promise<Node> {
  let node = getNode(nodeIdx);
  return new Promise(function (resolve, reject) {
    if (node) {
      resolve(node);
    }
    else {
      loadNode(nodeIdx).then((node: Node) => {
        resolve(node);
      });
    }
  });
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

}

function expandNode(sourceNode: any) {
  // get top x similar emojis
  const topIdxs = getTopNSimilarIdxs(sourceNode.id, LINK_COUNT);
  const topWeights = getTopNSimilarWeights(sourceNode.id, LINK_COUNT);
  const nodePromises: Promise<Node>[] = [];
  for (let i = 0; i < topIdxs.length; i++) {
    let idx = topIdxs[i];
    nodePromises.push(loadOrGetNode(idx));
  }
  Promise.all(nodePromises).then((nodes: Node[]) => {
    for (let i = 0; i < nodes.length; i++) {
      let targetNode = nodes[i];
      addOrGetLink(sourceNode, targetNode, topWeights[i]);
    }
    Graph.graphData(displayData);
  });
}

function collapseNode(node: any, initialCallerNode: any) {

  let outLinks = node.outLinks;
  for (let i = 0; i < outLinks.length; i++) {
    let link = outLinks[i];
    let targetNode = link.target;

    // don't remove any inLinks to the initial caller node
    if (targetNode.id == initialCallerNode.id) {
      continue;
    }
    removeLink(node, targetNode);

    if (targetNode.inLinks.length == 0) {
      collapseNode(targetNode, initialCallerNode);
      if (targetNode.outLinks.length == 0) {
        removeNode(targetNode);
      }
    }
  }
  Graph.graphData(displayData);
}


function displayAllEmojiChars() {
  const count = openMojiData.length
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
    allEmojiStr.value += emoji
    validCount += 1
    if (validCount % 15 == 0) {
      allEmojiStr.value += "\n"
    }
  }
}

function loadNode(nodeIdx: number): Promise<Node> {
  const emojiData = openMojiData[nodeIdx]
  const url = `${import.meta.env.BASE_URL}openmoji/color/svg/${emojiData.hexcode}.svg`
  const node: Node = { id: nodeIdx, outLinks: [], inLinks: [], expanded: false, mesh: null };

  return new Promise(function (resolve, reject) {
    loadSVG(url).then((mesh: any) => {
      node.mesh = mesh;
      displayData.nodes.push(node);
      resolve(node);
    });
  });

}

function SVGToMesh(data: any) {
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
  return group;
}

function loadSVG(url: string): Promise<THREE.Object3D> {
  return new Promise<THREE.Object3D>(function (resolve, reject) {
    loader.load(url, (data) => {
      const mesh = SVGToMesh(data);
      resolve(mesh);
    });
  });
}


// Mount
let canvasDiv = ref<HTMLDivElement>();



onMounted(() => {
  loadOrGetNode(startingNodeIdx).then((node: Node) => {
    initGraph();
  });
  //displayAllEmojiChars();
  // resize
  window.addEventListener("resize", () => {
    if (Graph) {
      Graph.width(window.innerWidth);
      Graph.height(window.innerHeight);
      console.log("resize")
    }
  });
})



</script>

<template>
  <div ref="canvasDiv" class="webgl"></div>
  <div class="openmoji-color">{{ allEmojiStr }}</div>
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

.webgl {
  position: fixed;
  top: 0;
  left: 0;
  outline: none;
}
</style>