<template>
  <div class="details">
    <div class="tabs">
      <button class="tab" :class="{active: tab==='overview'}" @click="tab='overview'">概览</button>
      <button class="tab" :class="{active: tab==='actor'}" @click="tab='actor'">演员</button>
      <button class="tab" :class="{active: tab==='movie'}" @click="tab='movie'">影片</button>
      <button class="tab" :class="{active: tab==='relations'}" @click="tab='relations'">关系</button>
    </div>

    <div class="body">
      <template v-if="tab==='overview'">
        <div class="empty">选择节点以查看详情</div>
      </template>
      <template v-else-if="tab==='actor'">
        <ActorCard v-if="current" :actor="{ name: current.label, ...current.data }" />
      </template>
      <template v-else-if="tab==='movie'">
        <MovieCard v-if="current" :movie="{ code: current.data?.code, title: current.data?.title, publisher: current.data?.publisher }" />
      </template>
      <template v-else>
        <div class="relations">
          <div class="row"><span>合作演员</span><span class="pill">—</span></div>
          <div class="row"><span>同系列影片</span><span class="pill">—</span></div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useGraphStore } from '@/stores/graph'
import ActorCard from './cards/ActorCard.vue'
import MovieCard from './cards/MovieCard.vue'

const tab = ref<'overview'|'actor'|'movie'|'relations'>('overview')
const store = useGraphStore()
const current = computed(() => store.selectedNodeId ? store.nodeMap[store.selectedNodeId] : null)

watch(current, (n) => {
  if (!n) { tab.value = 'overview'; return }
  tab.value = n.type === 'actress' ? 'actor' : 'movie'
})
</script>

<style scoped>
.details { display:flex; flex-direction:column; height:100%; }
.tabs { display:flex; gap:6px; padding:8px; border-bottom:1px solid var(--border); background:#0e141b; position:sticky; top:0; z-index:2; }
.tab { height:30px; padding:0 10px; border-radius:8px; border:1px solid var(--border); background:#0b1117; color:var(--text); cursor:pointer; }
.tab.active { background: rgba(106,227,255,.12); border-color:#2d3c4d; }
.body { padding:12px; }
.empty { color:#8ea3b8; font-size:13px; padding:12px; text-align:center; }
.relations { display:flex; flex-direction:column; gap:10px; }
.row { display:flex; justify-content:space-between; }
.pill { padding:2px 8px; background:#0b1117; border:1px solid var(--border); border-radius:999px; color:#8ea3b8; }
</style>
