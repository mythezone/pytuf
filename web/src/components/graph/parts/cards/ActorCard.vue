<template>
  <div class="card">
    <div class="header">
      <div class="avatar" />
      <div class="meta">
        <h3>演员名称</h3>
        <p class="muted">Roman Name</p>
      </div>
    </div>
    <div class="grid">
      <div>
        <span class="label">参演数</span>
        <div class="value">—</div>
      </div>
      <div>
        <span class="label">平均分</span>
        <div class="value">—</div>
      </div>
      <div>
        <span class="label">活跃期</span>
        <div class="value">—</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ actor?: { name?: string; avatar?: string; publisher?: string } }>()
</script>

<style scoped>
.card { border:1px solid var(--border); background:#0e141b; border-radius:12px; padding:12px; }
.header { display:flex; gap:12px; align-items:center; margin-bottom:10px; }
.avatar { width:48px; height:48px; background:#1a2531; border-radius:10px; }
.meta h3 { margin:0; font-size:14px; }
.muted { margin:4px 0 0; color:#8ea3b8; font-size:12px; }
.grid { display:grid; grid-template-columns: repeat(3, 1fr); gap:10px; }
.label { color:#9fb1c7; font-size:12px; }
.value { font-size:14px; margin-top:6px; }
</style>
