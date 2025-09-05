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
          const res = await api.graph.actress(oid)
          this.merge(res)
        } else if (node.type === 'movie') {
          const oid = id.split(':')[1] || id
          const res = await api.graph.movie(oid)
          this.merge(res)
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
  },
})

