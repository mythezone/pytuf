<template>
  <div class="graph-shell" :class="{ dark: isDark }">
    <header class="graph-header">
      <HeaderBar @toggleTheme="isDark = !isDark" />
    </header>


    <main class="graph-main">
      <GraphCanvas class="canvas" />
    </main>

    <section class="graph-details">
      <DetailsPanel />
    </section>

    <SidebarFilters />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import HeaderBar from './parts/HeaderBar.vue'
import GraphCanvas from './parts/GraphCanvas.vue'
import DetailsPanel from './parts/DetailsPanel.vue'
import SidebarFilters from './parts/SidebarFilters.vue'
import { useGraphStore } from '@/stores/graph'

const isDark = ref(false)
const store = useGraphStore()
// controls moved into GraphCanvas toolbar
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
  grid-template-columns: 1fr 360px;
  grid-template-rows: 64px 1fr;
  grid-template-areas:
    "header header"
    "main details";
  height: 100vh;
  background: var(--bg);
  color: var(--text);
}
.graph-shell.dark { filter: none; }

.graph-header { grid-area: header; border-bottom: 1px solid var(--border); background: rgba(18,24,32,.7); backdrop-filter: blur(8px); }
.graph-main   { grid-area: main; display:flex; flex-direction:column; min-height:0; overflow:hidden; }
.graph-details{ grid-area: details; border-left: 1px solid var(--border); background: var(--panel); overflow: hidden; }

/* toolbar lives inside GraphCanvas now */
.legend { margin-top: 12px; }
.canvas { flex:1; min-height:0; }
.filter-btn { position: fixed; left: 12px; top: 76px; z-index: 40; padding:6px 10px; background:#0e141b; color:#cfe1f0; border:1px solid var(--border); border-radius:8px; cursor:pointer; }
.settings-btn { position: fixed; left: 12px; top: 116px; z-index: 40; padding:6px 10px; background:#0e141b; color:#cfe1f0; border:1px solid var(--border); border-radius:8px; cursor:pointer; }
.backdrop { position:fixed; inset:0; background:rgba(0,0,0,.3); z-index: 48; }
</style>
