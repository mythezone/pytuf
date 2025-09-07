<template>
  <transition name="fade-scale">
  <div v-if="node && pos" class="popover" :style="{ left: pos.x + 12 + 'px', top: pos.y + 12 + 'px' }">
    <div class="body">
      <ActorCard v-if="node.type==='actress'" :actor="actorCard" variant="simple" />
      <MovieCard v-else :movie="movieCard" variant="simple" />
    </div>
  </div>
  </transition>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useGraphStore } from '@/stores/graph'
import ActorCard from './cards/ActorCard.vue'
import MovieCard from './cards/MovieCard.vue'

defineEmits<{ (e: 'close'): void }>()
const props = defineProps<{ node?: { id: string; type: 'actress'|'movie'; label: string; data?: Record<string, any> }, pos?: { x:number; y:number } }>()

// Popover now only shows simple cards; no header/title/subtitle

const store = useGraphStore()
const actorCard = computed(() => {
  const n = props.node
  if (!n || n.type !== 'actress') return undefined
  let avatar = n.data?.avatar as any
  if (avatar === 'local' && n.data?.href) avatar = `http://127.0.0.1:8000/media${n.data.href}.jpg`
  else avatar = store.resolveImg(avatar)
  return {
    name: n.label,
    avatar,
    category: n.data?.category,
  }
})
const movieCard = computed(() => {
  const n = props.node
  if (!n || n.type !== 'movie') return undefined
  return {
    title: n.data?.title ?? n.label,
    code: n.data?.code,
    cover: store.resolveImg(n.data?.cover),
    publish_date: n.data?.publish_date,
  }
})
</script>

<style scoped>
.popover {
  position:fixed; width:250px;
  border:1px solid var(--border); background:#0e141b; color:var(--text);
  border-radius:14px; box-shadow:0 10px 30px rgba(0,0,0,.4), inset 0 0 0 1px rgba(106,227,255,.08);
  overflow:hidden;
}
.body { padding:0px; }
.grid { display:grid; grid-template-columns: 1fr 1fr; gap:10px; }
.label { color:#9fb1c7; font-size:12px; }
.value { font-size:13px; margin-top:4px; }
.fade-scale-enter-active, .fade-scale-leave-active { transition: all .12s ease; }
.fade-scale-enter-from, .fade-scale-leave-to { opacity:0; transform: translateY(-4px) scale(.98); }
</style>
