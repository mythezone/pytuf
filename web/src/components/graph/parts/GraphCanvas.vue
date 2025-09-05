<template>
  <div class="graph-canvas">
    <div class="toolbar">
      <button class="btn" @click="fitView">适配</button>
      <button class="btn" @click="centerView">居中</button>
      <button class="btn" @click="randomize">重排</button>
      <span class="muted" v-if="store.loading">加载中…</span>
      <span class="err" v-if="store.error">{{ store.error }}</span>
    </div>
    <div class="stage">
      <v-network-graph
        class="vng"
        v-model:selected-nodes="selectedNodes"
        :nodes="nodes"
        :edges="edges"
        :layouts="store.layouts"
        @node:click="onNodeClick"
      >
        <template #node="{ nodeId }">
          <g>
            <circle :r="nodeRadius(nodeId)" :class="['n', nodeType(nodeId)]" />
            <title>{{ nodeLabel(nodeId) }}</title>
          </g>
        </template>
      </v-network-graph>
      <NodePopover :node="currentNode" v-if="currentNode" @close="store.selectedNodeId=null" />
    </div>
  </div>
  
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useGraphStore } from '@/stores/graph'
import NodePopover from './NodePopover.vue'

const store = useGraphStore()

const nodes = computed(() => store.nodeMap)
const edges = computed(() => store.edgeMap)
const selectedNodes = ref<string[]>([])

function onNodeClick({ node }: any) {
  store.expandNode(node)
}

function randomize() {
  const spread = 600
  for (const id of Object.keys(store.nodeMap)) {
    store.layouts.nodes[id] = { x: (Math.random() - 0.5) * spread, y: (Math.random() - 0.5) * spread }
  }
}

function fitView() {
  // v-network-graph 自带 fitView API 需通过 ref 访问；这里先简单居中
  centerView()
}

function centerView() {
  // 这里保留为简单实现；可通过 viewport API 实现真正居中
}

// 初始载入一批搜索结果以便有图可看
if (store.nodes.length === 0) {
  store.searchGraph('S1')
}

const currentNode = computed(() => store.selectedNodeId ? store.nodeMap[store.selectedNodeId] : null)

function nodeType(id: string) { return store.nodeMap[id]?.type || 'node' }
function nodeLabel(id: string) { return store.nodeMap[id]?.label || '' }
function nodeRadius(id: string) { return nodeType(id) === 'actress' ? 9 : 7 }
</script>

<style scoped>
.graph-canvas { position:relative; display:flex; flex-direction:column; height:100%; }
.toolbar { display:flex; gap:8px; padding:8px; border-bottom:1px solid var(--border); background:#0e141b; }
.btn { height:30px; padding:0 10px; background:#0b1117; color:var(--text); border:1px solid var(--border); border-radius:8px; cursor:pointer; }
.stage { position:relative; flex:1; }
.vng { position:absolute; inset:0; }
.muted { color:#9fb1c7; margin-left:8px; }
.err { color:#ff7b7b; margin-left:8px; }
.n { fill:#1a2531; stroke: var(--border); stroke-width:1.2px; cursor:pointer; }
.n.actress { fill:#1c2335; stroke:#6f7dff; filter: drop-shadow(0 0 6px rgba(111,125,255,.35)); }
.n.movie { fill:#12212a; stroke:#6ae3ff; filter: drop-shadow(0 0 6px rgba(106,227,255,.35)); }
</style>
