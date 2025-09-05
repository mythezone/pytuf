<template>
  <div class="card">
    <div class="header">
      <div class="poster" />
      <div class="meta">
        <h3>影片标题</h3>
        <p class="muted">代码 CODE-000 · 120min</p>
      </div>
    </div>
    <div class="grid">
      <div>
        <span class="label">发行商</span>
        <div class="value">—</div>
      </div>
      <div>
        <span class="label">发布日期</span>
        <div class="value">—</div>
      </div>
      <div>
        <span class="label">评分</span>
        <div class="value">—</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ movie?: { code?: string; title?: string; publisher?: string } }>()
</script>

<style scoped>
.card { border:1px solid var(--border); background:#0e141b; border-radius:12px; padding:12px; }
.header { display:flex; gap:12px; align-items:center; margin-bottom:10px; }
.poster { width:48px; height:48px; background:#1a2531; border-radius:6px; }
.meta h3 { margin:0; font-size:14px; }
.muted { margin:4px 0 0; color:#8ea3b8; font-size:12px; }
.grid { display:grid; grid-template-columns: repeat(3, 1fr); gap:10px; }
.label { color:#9fb1c7; font-size:12px; }
.value { font-size:14px; margin-top:6px; }
</style>
