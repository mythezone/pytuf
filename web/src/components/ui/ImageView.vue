<template>
  <div class="image-view" :class="rootClass">
    <img v-if="src" :src="resolved" :alt="alt" @click="open=true" />

    <div v-if="open" class="overlay" @click.self="close" @keydown.esc.prevent.stop="close" tabindex="0" ref="overlay">
      <img :src="resolved" :alt="alt" class="preview" />
      <button class="close" @click="close">×</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

const props = defineProps<{ src?: string; alt?: string; class?: string }>()
const rootClass = computed(() => props.class)
function resolve(src?: string) {
  if (!src) return ''
  if (src.startsWith('http')) return src
  if (src.startsWith('/')) return `http://10.16.100.180:8000/media${src}`
  return src
}
const resolved = computed(() => resolve(props.src))
const open = ref(false)
const overlay = ref<HTMLDivElement|null>(null)
const close = () => { open.value = false }

watch(open, (v) => { if (v) setTimeout(()=>overlay.value?.focus(), 0) })
</script>

<style scoped>
.image-view > img { display:block; width:100%; height:100%; object-fit:cover; cursor: zoom-in; }
.overlay { position:fixed; inset:0; background:rgba(0,0,0,.85); display:grid; place-items:center; z-index:1000; outline:none; }
.preview { max-width:90vw; max-height:90vh; box-shadow:0 10px 30px rgba(0,0,0,.5); border-radius:8px; }
.close { position:fixed; top:16px; right:16px; width:36px; height:36px; border-radius:50%; border:1px solid #2a3a4d; background:#0e141b; color:#e7edf5; cursor:pointer; font-size:20px; line-height:1; }
</style>

