import { defineStore } from 'pinia'
import { api, type GraphNode, type GraphEdge, type GraphResult } from '@/lib/api'

type NodeMap = Record<string, { id: string; type: string; label: string; data?: Record<string, any> }>
type EdgeMap = Record<string, { id: string; source: string; target: string; type?: string }>

export const useGraphStore = defineStore('graph', {
  state: () => ({
    nodes: [] as GraphNode[],
    edges: [] as GraphEdge[],
    selectedNodeId: null as string | null,
    layout: 'force' as 'force' | 'grid' | 'radial',
    childLimit: 50,
    loading: false,
    error: '' as string | null,
    // v-network-graph layouts: positions by node id
    layouts: { nodes: {} as Record<string, { x: number; y: number }> },
  }),
  getters: {
    nodeMap(state): NodeMap {
      const map: NodeMap = {}
      for (const n of state.nodes) map[n.id] = n
      return map
    },
    edgeMap(state): EdgeMap {
      const map: EdgeMap = {}
      for (const e of state.edges) map[e.id] = e
      return map
    },
  },
  actions: {
    resolveImg(src?: string): string | undefined {
      if (!src || typeof src !== 'string') return undefined
      if (src.startsWith('http')) return src
      if (src.startsWith('/')) return `http://127.0.0.1:8000/media${src}`
      return src
    },
    reset() {
      this.nodes = []
      this.edges = []
      this.layouts.nodes = {}
      this.selectedNodeId = null
      this.error = ''
    },
    merge(result: GraphResult) {
      const existing = new Set(this.nodes.map(n => n.id))
      for (const n of result.nodes) {
        if (!existing.has(n.id)) {
          this.nodes.push(n)
          // random-ish position for first render; can be replaced by real layout
          const spread = 600
          if (!this.layouts.nodes[n.id]) this.layouts.nodes[n.id] = { x: (Math.random() - 0.5) * spread, y: (Math.random() - 0.5) * spread }
        }
      }
      const existingE = new Set(this.edges.map(e => e.id))
      for (const e of result.edges) if (!existingE.has(e.id)) this.edges.push(e)
    },
    async searchGraph(keyword: string) {
      this.loading = true
      this.error = ''
      try {
        const res = await api.graph.search(keyword, 30)
        this.reset()
        this.merge(res)
      } catch (e: any) {
        this.error = e?.message || String(e)
      } finally {
        this.loading = false
      }
    },
    async expandNode(id: string) {
      const node = this.nodes.find(n => n.id === id)
      if (!node) return
      try {
        this.loading = true
        if (node.type === 'actress') {
          const oid = id.split(':')[1] || id
          const res = await api.graph.actress(oid, this.childLimit)
          this.merge(res)
          try { this.detailActor = await api.actresses.get(oid) } catch {}
        } else if (node.type === 'movie') {
          const oid = id.split(':')[1] || id
          const res = await api.graph.movie(oid, this.childLimit)
          this.merge(res)
          try { this.detailMovie = await api.movies.get(oid) } catch {}
        }
        this.selectedNodeId = id
      } catch (e: any) {
        this.error = e?.message || String(e)
      } finally {
        this.loading = false
      }
    },
    setLayout(name: 'force' | 'grid' | 'radial') {
      this.layout = name
      // TODO: implement real layout strategies; keep positions for now
    },
    async randomMovie() {
      this.reset()
      try {
        this.loading = true
        const m = await api.movies.random()
        const id = typeof m._id === 'string' ? m._id : (m._id?.$oid ?? '')
        if (!id) throw new Error('no movie id')
        const base = await api.graph.movie(id, this.childLimit)
        this.merge(base)
        // select base movie node
        const baseMovieNode = this.nodes.find(n => n.type === 'movie')
        if (baseMovieNode) this.selectedNodeId = baseMovieNode.id
        // expand each actress to get their movies and add movie-movie edges to base
        const baseId = baseMovieNode?.id
        // second layer only actors; no further expansion here
      } finally {
        this.loading = false
      }
    },
    async randomActress() {
      this.reset()
      try {
        this.loading = true
        const a = await api.actresses.random()
        const id = typeof a._id === 'string' ? a._id : (a._id?.$oid ?? '')
        if (!id) throw new Error('no actress id')
        const g = await api.graph.actress(id, this.childLimit)
        this.merge(g)
        const baseAct = this.nodes.find(n => n.type === 'actress')
        if (baseAct) this.selectedNodeId = baseAct.id
      } finally {
        this.loading = false
      }
    },
    applyLayout(name: 'force'|'grid'|'radial') {
      const ids = Object.keys(this.nodeMap)
      const n = ids.length
      if (name === 'grid') {
        const cols = Math.ceil(Math.sqrt(n)) || 1
        const gap = 100
        ids.forEach((id, i) => {
          const r = Math.floor(i / cols)
          const c = i % cols
          this.layouts.nodes[id] = { x: c * gap, y: r * gap }
        })
      } else if (name === 'radial') {
        const R = 220
        ids.forEach((id, i) => {
          const ang = (2 * Math.PI * i) / (n || 1)
          this.layouts.nodes[id] = { x: Math.cos(ang) * R, y: Math.sin(ang) * R }
        })
      } else {
        const R = 180
        ids.forEach((id, i) => {
          const ang = (2 * Math.PI * i) / (n || 1)
          const jitter = 60
          this.layouts.nodes[id] = { x: Math.cos(ang)*R + (Math.random()-0.5)*jitter, y: Math.sin(ang)*R + (Math.random()-0.5)*jitter }
        })
      }
    },
    setLayout(name: 'force' | 'grid' | 'radial') {
      this.layout = name
      this.applyLayout(name)
    },
  },
})
