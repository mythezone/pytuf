<template>
  <div class="gallery" v-if="images?.length">
    <div v-for="(src,i) in images" :key="i" class="shot" @click="openAt(i)">
      <img :src="resolve(src)" />
    </div>

    <div v-if="open" class="overlay" @click.self="close" @keydown.esc.prevent.stop="close" tabindex="0" ref="overlay">
      <button class="nav left" @click.stop="prev">‹</button>
      <img :src="resolve(images[index])" class="preview" />
      <button class="nav right" @click.stop="next">›</button>
      <button class="close" @click.stop="close">×</button>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, watch } from 'vue'
const props = defineProps<{ images?: string[] }>()
const open = ref(false)
const index = ref(0)
const overlay = ref<HTMLDivElement|null>(null)
function resolve(src?: string) {
  if (!src) return ''
  if (src.startsWith('http')) return src
  if (src.startsWith('/')) return `http://10.16.100.180:8000/media${src}`
  return src
}
function openAt(i:number){ index.value = i; open.value = true }
function close(){ open.value = false }
function prev(){ if (!props.images) return; index.value = (index.value - 1 + props.images.length) % props.images.length }
function next(){ if (!props.images) return; index.value = (index.value + 1) % props.images.length }
watch(open, v => { if (v) setTimeout(()=>overlay.value?.focus(), 0) })
</script>
<style scoped>
.gallery { display:flex; flex-wrap:wrap; gap:6px; }
.shot { width: calc(33% - 4px); aspect-ratio: 16/9; background:#0b1117; border:1px solid var(--border); border-radius:6px; overflow:hidden; cursor: zoom-in; }
.shot img { width:100%; height:100%; object-fit:cover; display:block; }
.overlay { position:fixed; inset:0; background:rgba(0,0,0,.85); display:grid; grid-template-columns:auto; place-items:center; z-index:1000; outline:none; }
.preview { max-width:90vw; max-height:90vh; border-radius:8px; box-shadow:0 10px 30px rgba(0,0,0,.5); }
.nav { position:fixed; top:50%; transform:translateY(-50%); width:42px; height:42px; border-radius:50%; border:1px solid #2a3a4d; background:#0e141b; color:#e7edf5; cursor:pointer; font-size:28px; line-height:1; }
.nav.left { left:16px; }
.nav.right { right:16px; }
.close { position:fixed; top:16px; right:16px; width:36px; height:36px; border-radius:50%; border:1px solid #2a3a4d; background:#0e141b; color:#e7edf5; cursor:pointer; font-size:20px; line-height:1; }
</style>
