<template>
  <div class="header">
    <div class="brand">
      <div class="logo" />
      <h1>Actors × Movies</h1>
    </div>

    <div class="actions">
      <input
        v-model="q"
        class="search"
        type="search"
        placeholder="搜索演员 / 影片 / 代码"
      />
      <button class="btn" title="切换主题" @click="$emit('toggleTheme')">🌓</button>
      <button class="btn" title="设置" @click="openSettings = true">⚙️</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useGraphStore } from '@/stores/graph'

const q = ref('')
const openSettings = ref(false)
const store = useGraphStore()

let t: number | null = null
watch(q, (v) => {
  if (t) window.clearTimeout(t)
  t = window.setTimeout(() => {
    if (v && v.trim().length > 0) store.searchGraph(v.trim())
  }, 400)
})
</script>

<style scoped>
.header { display:flex; align-items:center; justify-content:space-between; height:64px; padding:0 16px; }
.brand { display:flex; align-items:center; gap:12px; }
.logo { width:28px; height:28px; background: linear-gradient(135deg, #6ae3ff, #6f7dff); border-radius:8px; box-shadow:0 0 24px rgba(106,227,255,.4); }
h1 { font-size:16px; letter-spacing:.4px; margin:0; }
.actions { display:flex; align-items:center; gap:8px; }
.search { width:360px; height:36px; border:1px solid var(--border); background:#0e141b; color:var(--text); border-radius:8px; padding:0 12px; outline:none; }
.search::placeholder { color: #5b6a7a; }
.btn { height:36px; padding:0 10px; background:#0e141b; border:1px solid var(--border); color:var(--text); border-radius:8px; cursor:pointer; }
.btn:hover { border-color:#2d3c4d; }
</style>
