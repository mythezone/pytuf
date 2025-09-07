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
        <div v-if="current">
          <div v-if="current.type==='actress'">
            <ActorCard :actor="actorInfo" />
          </div>
          <div v-else>
            <MovieCard :movie="movieInfo" :screenshots="movieShots" :magnets="movieMagnets" />
          </div>
        </div>
        <div v-else class="empty">选择节点以查看详情</div>
      </template>
      <template v-else-if="tab==='actor'">
        <div class="cards scroll">
          <ActorCard v-for="a in allActors" :key="a.id" :actor="a" variant="simple" />
        </div>
      </template>
      <template v-else-if="tab==='movie'">
        <div class="cards scroll">
          <MovieCard v-for="m in allMovies" :key="m.id" :movie="m" variant="simple" />
        </div>
      </template>
      <template v-else>
        <div class="relations">
          <div class="row"><span>相关影片</span></div>
          <div class="cards">
            <MovieCard v-for="m in relatedMovies" :key="m.id" :movie="m" variant="simple" />
          </div>
          
          <div class="row"><span>本次图 · 演员</span></div>
          <div class="cards scroll">
            <ActorCard v-for="a in allActors" :key="a.id" :actor="a" variant="simple" />
          </div>
          <div class="row"><span>本次图 · 影片</span></div>
          <div class="cards scroll">
            <MovieCard v-for="m in allMovies" :key="m.id" :movie="m" variant="simple" />
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useGraphStore } from '@/stores/graph'
import ActorCard from './cards/ActorCard.vue'
import MovieCard from './cards/MovieCard.vue'

const tab = ref<'overview'|'actor'|'movie'|'relations'>('overview')
const store = useGraphStore()
const current = computed(() => store.selectedNodeId ? store.nodeMap[store.selectedNodeId] : null)
const actorInfo = computed(() => {
  const n:any = current.value
  if (!n || n.type !== 'actress') return null
  // avatar 'local' => href + .jpg
  let avatar = n?.data?.avatar
  if (avatar === 'local' && n?.data?.href) avatar = `http://127.0.0.1:8000/media${n.data.href}.jpg`
  // movies_count: count neighbor movies
  const moviesCount = Object.values(store.edgeMap)
    .filter(e => e.source === n.id || e.target === n.id)
    .map(e => e.source === n.id ? e.target : e.source)
    .map(id => store.nodeMap[id])
    .filter(x => x && x.type==='movie').length
  return { name: n.label, title: n.data?.title, category: n.data?.category, avatar, movies_count: moviesCount, href: n.data?.href }
})
const movieInfo = computed(() => {
  const n:any = current.value
  if (!n || n.type !== 'movie') return null
  // prefer detailed if available
  const d:any = store.detailMovie && (store.selectedNodeId===n.id) ? store.detailMovie : null
  return {
    title: d?.title ?? n.data?.title,
    code: d?.code ?? n.data?.code,
    cover: store.resolveImg((d?.cover ?? n.data?.cover) as any),
    publish_date: d?.publish_date,
    rating: d?.rating,
    rater: d?.rater,
    tags: d?.tags,
    duration_minutes: d?.duration_minutes,
    maker: d?.maker?.name,
    publisher: d?.publisher?.name,
    series: d?.series,
  }
})
const movieShots = computed(() => store.detailMovie?.screenshots?.map((s:string)=>store.resolveImg(s)) || [])
const movieMagnets = computed(() => store.detailMovie?.magnets || [])
const relatedMovies = computed(() => {
  const n = current.value
  if (!n) return [] as any[]
  const neighbors = Object.values(store.edgeMap)
    .filter(e => e.source === n.id || e.target === n.id)
    .map(e => e.source === n.id ? e.target : e.source)
  const uniq = Array.from(new Set(neighbors))
  let movies: any[] = []
  if (n.type === 'movie') {
    // via actors to movies
    const actorIds = uniq.filter(id => store.nodeMap[id]?.type==='actress')
    const mset = new Set<string>()
    for (const aid of actorIds) {
      const mvIds = Object.values(store.edgeMap)
        .filter(e => e.source === aid || e.target === aid)
        .map(e => e.source === aid ? e.target : e.source)
      for (const mid of mvIds) {
        if (mid !== n.id && store.nodeMap[mid]?.type==='movie') mset.add(mid)
      }
    }
    movies = Array.from(mset).slice(0, 12).map(id => ({
      id,
      title: store.nodeMap[id]?.data?.title,
      code: store.nodeMap[id]?.data?.code,
      cover: store.resolveImg(store.nodeMap[id]?.data?.cover),
    }))
  } else {
    // actress -> her movies
    movies = uniq.filter(id => store.nodeMap[id]?.type==='movie').slice(0, 20).map(id => ({
      id,
      title: store.nodeMap[id]?.data?.title,
      code: store.nodeMap[id]?.data?.code,
      cover: store.resolveImg(store.nodeMap[id]?.data?.cover),
    }))
  }
  return movies
})
const allActors = computed(() => Object.values(store.nodeMap)
  .filter(n => n.type==='actress')
  .map(n => ({ id:n.id, name:n.label, avatar: (n.data?.avatar==='local' && n.data?.href) ? `http://127.0.0.1:8000/media${n.data.href}.jpg` : store.resolveImg(n.data?.avatar) })))
const allMovies = computed(() => Object.values(store.nodeMap)
  .filter(n => n.type==='movie')
  .map(n => ({ id:n.id, title:n.data?.title, code:n.data?.code, publish_date: n.data?.publish_date, cover: store.resolveImg(n.data?.cover) })))
</script>

<style scoped>
.details { display:flex; flex-direction:column; height:100%; }
.tabs { display:flex; gap:6px; padding:8px; border-bottom:1px solid var(--border); background:#0e141b; position:sticky; top:0; z-index:2; }
.tab { height:30px; padding:0 10px; border-radius:8px; border:1px solid var(--border); background:#0b1117; color:var(--text); cursor:pointer; }
.tab.active { background: rgba(106,227,255,.12); border-color:#2d3c4d; }
.body { padding:12px; flex:1; overflow:auto; min-height:0; }
.empty { color:#8ea3b8; font-size:13px; padding:12px; text-align:center; }
.relations { display:flex; flex-direction:column; gap:10px; }
.row { display:flex; justify-content:space-between; }
.pill { padding:2px 8px; background:#0b1117; border:1px solid var(--border); border-radius:999px; color:#8ea3b8; }
.cards { display:flex; flex-wrap:wrap; gap:8px; }
.cards.scroll { overflow:auto; }
.mini { display:flex; align-items:center; gap:8px; padding:6px; border:1px solid var(--border); border-radius:8px; background:#0e141b; width:100%; }
.mini img { width:40px; height:40px; object-fit:cover; border-radius:6px; }
.mini .info { display:flex; flex-direction:column; }
.mini .t { font-size:12px; }
.mini .s { font-size:11px; color:#9fb1c7; }
</style>
