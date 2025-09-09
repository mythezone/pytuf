<!-- eslint-disable @typescript-eslint/no-explicit-any -->
<template>
  <div class="graph-canvas">
    <div class="toolbar">
      <button class="btn" @click="fitView">适配</button>
      <button class="btn" @click="centerView">居中</button>
      <button class="btn" @click="randomize">重排</button>
      <span class="sep" />
      <span class="label">布局:</span>
      <button class="btn" :class="{active: store.layout==='force'}" @click="store.setLayout('force')">力导向</button>
      <button class="btn" :class="{active: store.layout==='grid'}" @click="store.setLayout('grid')">网格</button>
      <button class="btn" :class="{active: store.layout==='radial'}" @click="store.setLayout('radial')">径向</button>
      <label class="toggle"><input type="checkbox" v-model="d3Force" /> 3D-Force</label>
      <span class="muted" v-if="store.loading">加载中…</span>
      <span class="err" v-if="store.error">{{ store.error }}</span>
    </div>
    <div class="stage">
      <v-network-graph
        ref="graph"
        class="vng"
        v-model:selected-nodes="selectedNodes"
        :nodes="nodes"
        :edges="edges"
        :layouts="store.layouts"
        :configs="configs"
        :event-handlers="eventHandlers"
      >
        <defs>
          <clipPath id="clipCircle" clipPathUnits="objectBoundingBox">
            <circle cx="0.5" cy="0.5" r="0.5" />
          </clipPath>
          <clipPath id="clipRect" clipPathUnits="objectBoundingBox">
            <rect x="0" y="0" width="1" height="1" rx="0.2" ry="0.2" />
          </clipPath>
        </defs>
        <template #override-node="{ nodeId, scale, config, ...slotProps }">
          <g>
            <template v-if="nodeType(nodeId)==='actress'">
              <circle :r="config.radius * scale" :class="['n','actress']" v-bind="slotProps" />
              <image
                v-if="nodeImg(nodeId)"
                :x="-config.radius * scale"
                :y="-config.radius * scale"
                :width="config.radius * scale * 2"
                :height="config.radius * scale * 2"
                :href="nodeImg(nodeId)"
                clip-path="url(#clipCircle)"
              />
            </template>
            <template v-else>
              <rect
                :x="-config.width * scale / 2"
                :y="-config.height * scale / 2"
                :width="config.width * scale"
                :height="config.height * scale"
                :rx="config.borderRadius"
                :ry="config.borderRadius"
                :class="['n','movie']"
                v-bind="slotProps"
              />
              <image
                v-if="nodeImg(nodeId)"
                :x="-config.width * scale / 2"
                :y="-config.height * scale / 2"
                :width="config.width * scale"
                :height="config.height * scale"
                :href="nodeImg(nodeId)"
                clip-path="url(#clipRect)"
              />
            </template>
            <title>{{ nodeLabel(nodeId) }}</title>
          </g>
        </template>
      </v-network-graph>
      <NodePopover :node="currentNode" :pos="hoverPos" v-if="currentNode && hoverPos" @close="store.selectedNodeId=null" />
    </div>
  </div>
  
</template>

<script setup lang="ts">
import { computed, ref, reactive, watch, nextTick } from 'vue'
import * as vNG from 'v-network-graph'
import { useGraphStore } from '@/stores/graph'
import NodePopover from './NodePopover.vue'
import { ForceLayout } from 'v-network-graph/lib/force-layout'

const store = useGraphStore()

const nodes = computed(() => store.nodeMap)
const edges = computed(() => store.edgeMap)
const selectedNodes = ref<string[]>([])
const d3Force = ref(false)
const graph = ref<any>(null)

function randomize() {
  const spread = 600
  for (const id of Object.keys(store.nodeMap)) {
    store.layouts.nodes[id] = { x: (Math.random() - 0.5) * spread, y: (Math.random() - 0.5) * spread }
  }
}

function fitView() {
  // use component method if available
  try { graph.value?.fitView?.() } catch {}
}

function centerView() {
  fitView()
}

// 不再自动搜索，等待用户点击随机或搜索

const hoverNodeId = ref<string|null>(null)
const hoverPos = ref<{x:number;y:number}|null>(null)
const currentNode = computed(() => {
  const id = hoverNodeId.value || store.selectedNodeId
  return id ? store.nodeMap[id] : null
})

function nodeType(id: string) { return store.nodeMap[id]?.type || 'node' }
function nodeLabel(id: string) { return store.nodeMap[id]?.label || '' }
function nodeRadius(id: string) { return nodeType(id) === 'actress' ? 24 : 20 }
function nodeImg(id: string) {
  const n = store.nodeMap[id]
  if (!n) return undefined
  if (n.type === 'actress') {
    let avatar = n?.data?.avatar as any
    if (avatar === 'local' && n?.data?.href) return `http://10.16.100.180:8000/media${n.data.href}.jpg`
    return store.resolveImg(avatar)
  }
  return store.resolveImg(n?.data?.cover)
}
function edgeType(id: string) {
  const e = store.edgeMap[id]
  return e?.type || 'acted_in'
}

// v-network-graph configs for node style
const configs = reactive(
  vNG.defineConfigs<any, any>({
    view: {
      layoutHandler: new vNG.SimpleLayout(),
    },
    node: {
      selectable: true,
      normal: {
        type: (n:any) => (n?.type === 'actress' ? 'circle' : 'rect'),
        radius: (n:any) => (n?.type === 'actress' ? 24 : 0),
        width: (n:any) => {
          if (n?.type === 'movie') {
            return n?.data?.video ? 56 : 40
          }
          return 0
        },
        height: (n:any) => {
          if (n?.type === 'movie') {
            return n?.data?.video ? 56 : 40
          }
          return 0
        },
        borderRadius: 8,
        color: (n:any) => {
          if (n?.type === 'actress') return '#ff9acb'
          if (n?.type === 'movie') {
            return n?.data?.video ? '#4ade80' : '#7bb6ff' // 绿色: #4ade80
          }
          return '#7bb6ff'
        },
      },
      hover: {
        radius: (n:any) => (n?.type === 'actress' ? 26 : 0),
        width: (n:any) => {
          if (n?.type === 'movie') {
            return n?.data?.video ? 62 : 44
          }
          return 0
        },
        height: (n:any) => {
          if (n?.type === 'movie') {
            return n?.data?.video ? 62 : 44
          }
          return 0
        },
        color: (n:any) => {
          if (n?.type === 'actress') return '#ff7ab9'
          if (n?.type === 'movie') {
            return n?.data?.video ? '#22c55e' : '#5aa3ff' // 深绿色: #22c55e
          }
          return '#5aa3ff'
        },
      },
      label: { visible: false },
      focusring: { color: '#cccccc' },
    },
    edge: {
      normal: {
        width: (e:any) => (e?.type === 'movie_movie' ? 2 : 2),
        color: (e:any) => (e?.type === 'movie_movie' ? '#36d99a' : '#ff6b6b'),
      },
      hover: { color: '#ffffff' },
    },
  })
)

watch(() => d3Force.value, (v) => {
  if (v) {
    configs.view.layoutHandler = new ForceLayout()
  } else {
    configs.view.layoutHandler = new vNG.SimpleLayout()
  }
}, { immediate: true })

// auto-fit when data or layout toggles change
let fitTimer: any
watch(
  [() => Object.keys(nodes.value).length, () => Object.keys(edges.value).length, () => store.layout, () => d3Force.value],
  () => {
    clearTimeout(fitTimer)
    fitTimer = setTimeout(() => { nextTick().then(() => fitView()) }, 120)
  },
  { immediate: true }
)

// update hover position on pointer move
const eventHandlers: vNG.EventHandlers = {
  'node:click': ({ node }) => store.expandNode(node),
  'node:pointerover': ({ node, event }) => { hoverNodeId.value = node; if (event && 'clientX' in event) hoverPos.value = { x: (event as MouseEvent).clientX, y: (event as MouseEvent).clientY } },
  'node:pointermove': ({ event }) => { if (event && 'clientX' in event) hoverPos.value = { x: (event as MouseEvent).clientX, y: (event as MouseEvent).clientY } },
  'node:pointerout': () => { hoverNodeId.value = null; hoverPos.value = null },
}
</script>

<style scoped>
.graph-canvas { position:relative; display:flex; flex-direction:column; height:100%; }
.toolbar { display:flex; gap:8px; padding:8px; border-bottom:1px solid var(--border); background:#0e141b; }
.btn { height:30px; padding:0 10px; background:#0b1117; color:var(--text); border:1px solid var(--border); border-radius:8px; cursor:pointer; }
.btn.active { background: rgba(106,227,255,.12); border-color:#2d3c4d; }
.label { color:#9fb1c7; font-size:12px; align-self:center; }
.toggle { margin-left:auto; display:flex; align-items:center; gap:6px; color:#cfe1f0; font-size:12px; }
.sep { width:1px; align-self:stretch; background: var(--border); margin:0 4px; }
.stage { position:relative; flex:1; }
.vng { position:absolute; inset:0; }
.muted { color:#9fb1c7; margin-left:8px; }
.err { color:#ff7b7b; margin-left:8px; }
.n { fill:#1a2531; stroke: var(--border); stroke-width:1.2px; cursor:pointer; }
.n.actress { fill:#ff9acb; stroke:#ff3e8e; filter: drop-shadow(0 0 6px rgba(255,62,142,.35)); }
.n.movie { fill:#7bb6ff; stroke:#2f89ff; filter: drop-shadow(0 0 6px rgba(47,137,255,.35)); }
.e { stroke-width: 2px; }
.e.acted_in { stroke: #ff6b6b; }
.e.movie_movie { stroke: #36d99a; }
</style>
