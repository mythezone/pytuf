<template>
  <div v-if="variant==='detailed'" class="card">
    <div class="header">
      <ImageView v-if="img" :src="img" class="avatar" :alt="actor?.name" />
      <div class="meta">
        <h3>{{ actor?.name || '演员' }}</h3>
        <p class="muted">{{ actor?.title }}</p>
        <p class="muted">分类：{{ actor?.category || '-' }}</p>
      </div>
    </div>
    <div class="grid">
      <div>
        <span class="label">参演数</span>
        <div class="value">{{ actor?.movies_count ?? actor?.movies?.length ?? '—' }}</div>
      </div>
    </div>
    <div v-if="tags && tags.length" class="tags">
      <span v-for="(t,i) in (showAll ? tags : tags.slice(0,10))" :key="i" class="tag" :class="color(t)">{{ t }}</span>
      <button v-if="tags.length>10" class="more" @click="showAll=!showAll">{{ showAll?'收起':'更多' }}</button>
    </div>
  </div>
  <div v-else class="card simple">
    <ImageView v-if="img" :src="img" class="avatar sm" :alt="actor?.name" />
    <div class="meta sm">
      <div class="t">{{ actor?.name || '演员' }}</div>
      <div class="s" v-if="actor?.category">{{ actor?.category }}</div>
    </div>
  </div>
  </template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import ImageView from '../../../ui/ImageView.vue'
const props = defineProps<{ actor?: { name?: string; title?: string; avatar?: string|boolean; category?: string; movies_count?: number; movies?: any[]; href?: string; tags?: string[] }, variant?: 'detailed'|'simple' }>()
const variant = computed(()=> props.variant ?? 'detailed')
const img = computed(() => {
  if (!props.actor) return undefined
  if (props.actor.avatar === 'local' && props.actor.href) return `http://10.16.100.180:8000/media${props.actor.href}.jpg`
  return typeof props.actor.avatar === 'string' ? props.actor.avatar : undefined
})
const tags = computed(()=> props.actor?.tags || [])
const showAll = ref(false)
function color(t:string){
  const h = Math.abs(hash(t)) % 360
  return `h${h}`
}
function hash(s:string){ let h=0; for(let i=0;i<s.length;i++){ h=(h<<5)-h+s.charCodeAt(i); h|=0 } return h }
</script>

<style scoped>
.card { border:1px solid var(--border); background:#0e141b; border-radius:12px; padding:12px; }
.header { display:flex; gap:12px; align-items:center; margin-bottom:10px; }
.avatar { width:48px; height:48px; background:#1a2531; border-radius:10px; }
.avatar.sm { width:40px; height:40px; border-radius:8px; }
.meta h3 { margin:0; font-size:14px; }
.muted { margin:4px 0 0; color:#8ea3b8; font-size:12px; }
.grid { display:grid; grid-template-columns: repeat(3, 1fr); gap:10px; }
.label { color:#9fb1c7; font-size:12px; }
.value { font-size:14px; margin-top:6px; }
.tags { margin-top:8px; display:flex; flex-wrap:wrap; gap:6px; }
.tag { font-size:11px; padding:3px 8px; border-radius:999px; background:#10212e; border:1px solid var(--border); }
.more { margin-left:auto; height:22px; padding:0 8px; border:1px solid var(--border); background:#0b1117; color:#cfe1f0; border-radius:6px; cursor:pointer; font-size:11px; }
[class^="h"] { background: #10212e; }
.card.simple { display:flex; align-items:center; gap:8px; padding:8px; width:100%; }
.card.simple .meta.sm { display:flex; flex-direction:column; }
.card.simple .t { font-size:12px; }
.card.simple .s { font-size:11px; color:#9fb1c7; }
</style>
