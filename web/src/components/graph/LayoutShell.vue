<template>
  <div class="graph-shell" :class="{ dark: isDark }">
    <header class="graph-header">
      <HeaderBar @toggleTheme="isDark = !isDark" />
    </header>

    <aside class="graph-aside">
      <SidebarFilters />
      <LegendPanel class="legend" />
    </aside>

    <main class="graph-main">
      <StatsBar class="stats" :stats="stats" :layout="store.layout" />
      <GraphCanvas class="canvas" />
    </main>

    <section class="graph-details">
      <DetailsPanel />
    </section>

    <SettingsDrawer />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import HeaderBar from './parts/HeaderBar.vue'
import SidebarFilters from './parts/SidebarFilters.vue'
import GraphCanvas from './parts/GraphCanvas.vue'
import DetailsPanel from './parts/DetailsPanel.vue'
import LegendPanel from './parts/LegendPanel.vue'
import StatsBar from './parts/StatsBar.vue'
import SettingsDrawer from './parts/SettingsDrawer.vue'
import { useGraphStore } from '@/stores/graph'

const isDark = ref(false)
const store = useGraphStore()
const stats = computed(() => ({
  actors: store.nodes.filter(n => n.type === 'actress').length,
  movies: store.nodes.filter(n => n.type === 'movie').length,
  edges: store.edges.length,
}))
</script>

<style scoped>
.graph-shell {
  --bg: #0b0f14;
  --panel: #121820;
  --muted: #7b8da0;
  --text: #e7edf5;
  --accent: #6ae3ff;
  --border: #22303f;

  display: grid;
  grid-template-columns: 280px 1fr 360px;
  grid-template-rows: 64px 1fr;
  grid-template-areas:
    "header header header"
    "aside main details";
  height: 100vh;
  background: var(--bg);
  color: var(--text);
}
.graph-shell.dark { filter: none; }

.graph-header { grid-area: header; border-bottom: 1px solid var(--border); background: rgba(18,24,32,.7); backdrop-filter: blur(8px); }
.graph-aside  { grid-area: aside;  border-right: 1px solid var(--border); background: var(--panel); overflow: auto; }
.graph-main   { grid-area: main;   display: grid; grid-template-rows: auto 1fr; }
.graph-details{ grid-area: details; border-left: 1px solid var(--border); background: var(--panel); overflow: auto; }

.stats { border-bottom: 1px solid var(--border); }
.legend { margin-top: 12px; }
.canvas { height: 100%; }
</style>
