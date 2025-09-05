<template>
  <div class="stats">
    <div class="pill">演员 <b>{{ stats.actors }}</b></div>
    <div class="pill">影片 <b>{{ stats.movies }}</b></div>
    <div class="pill">连边 <b>{{ stats.edges }}</b></div>
    <div class="spacer" />
    <div class="pill muted">布局：{{ layoutLabel }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{ stats?: { actors: number; movies: number; edges: number }, layout?: string }>()
const stats = computed(() => props.stats ?? { actors: 0, movies: 0, edges: 0 })
const layoutLabel = computed(() => props.layout ?? 'force')
</script>

<style scoped>
.stats { display:flex; align-items:center; gap:8px; padding:8px 12px; background:#0e141b; }
.pill { display:flex; align-items:center; gap:6px; padding:6px 10px; border-radius:999px; background:#0b1117; border:1px solid var(--border); color:#dbe7f3; font-size:12px; }
.pill b { font-weight:600; color:#fff; }
.muted { color:#9fb1c7; }
.spacer { flex:1; }
</style>

