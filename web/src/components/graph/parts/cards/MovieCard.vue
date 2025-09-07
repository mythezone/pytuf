<template>
  <div v-if="variant==='detailed'" class="card">
    <div class="header">
      <ImageView v-if="img" :src="img" class="poster" :alt="movie?.title || movie?.code" />
      <div class="meta">
        <h3>{{ movie?.title || '影片' }}</h3>
        <p class="muted">代码 {{ movie?.code || '-' }} · {{ movie?.duration_minutes || '-' }} min</p>
      </div>
    </div>
    <div class="grid">
      <div>
        <span class="label">发布日期</span>
        <div class="value">{{ movie?.publish_date || '—' }}</div>
      </div>
      <div>
        <span class="label">评分</span>
        <div class="value">{{ movie?.rating ?? '—' }} ({{ movie?.rater ?? 0 }})</div>
      </div>
      <div>
        <span class="label">标签</span>
        <div class="value">{{ (movie?.tags || []).slice(0,8).join(' / ') }}</div>
      </div>
    </div>
    <div v-if="shots?.length" class="section">
      <div class="row"><span>剧照</span></div>
      <Gallery :images="shots" />
    </div>
    <div v-if="mags?.length" class="section">
      <div class="row"><span>磁力</span></div>
      <MagnetsList :items="mags" />
    </div>
  </div>
  <div v-else class="card simple">
    <ImageView v-if="img" :src="img" class="poster sm" :alt="movie?.title || movie?.code" />
    <div class="meta sm">
      <div class="t">{{ movie?.title || movie?.code || '影片' }}</div>
      <div class="s">{{ movie?.code }}<template v-if="movie?.publish_date"> · {{ movie?.publish_date }}</template></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import ImageView from '../../../ui/ImageView.vue'
import Gallery from '../Gallery.vue'
import MagnetsList from '../MagnetsList.vue'
type Magnet = { magnet?: string; name?: string; meta_text?: string }
const props = defineProps<{ movie?: { title?: string; code?: string; cover?: string; duration_minutes?: number; publish_date?: string; rating?: number|null; rater?: number|null; tags?: string[] }, variant?: 'detailed'|'simple', screenshots?: string[], magnets?: Magnet[] }>()
const img = computed(() => props.movie?.cover)
const variant = computed(() => props.variant ?? 'detailed')
const shots = computed(() => props.screenshots || [])
const mags = computed(() => props.magnets || [])
</script>

<style scoped>
.card { border:1px solid var(--border); background:#0e141b; border-radius:12px; padding:12px; }
.header { display:flex; gap:12px; align-items:center; margin-bottom:10px; }
.poster { width:48px; height:48px; background:#1a2531; border-radius:6px; }
.poster.sm { width:40px; height:40px; border-radius:6px; }
.meta h3 { margin:0; font-size:14px; }
.muted { margin:4px 0 0; color:#8ea3b8; font-size:12px; }
.grid { display:grid; grid-template-columns: repeat(3, 1fr); gap:10px; }
.label { color:#9fb1c7; font-size:12px; }
.value { font-size:14px; margin-top:6px; }
.section { margin-top:10px; }
.row { display:flex; justify-content:space-between; margin-bottom:6px; }
.row span { color:#9fb1c7; font-size:12px; }
.card.simple { display:flex; align-items:center; gap:8px; padding:8px; width:100%; }
.card.simple .meta.sm { display:flex; flex-direction:column; }
.card.simple .t { font-size:12px; }
.card.simple .s { font-size:11px; color:#9fb1c7; }
</style>
