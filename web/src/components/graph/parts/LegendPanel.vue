<template>
  <div class="legend">
    <h3>图例</h3>
    <div class="rows">
      <div class="row"><span class="dot actor" /> 演员</div>
      <div class="row"><span class="dot movie" /> 影片</div>
      <div class="row"><span class="line" /> 参演关系</div>
    </div>
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped>
.legend { border:1px solid var(--border); background:#0e141b; border-radius:12px; padding:12px; }
h3 { margin:0 0 8px; color:#9fb1c7; font-size:12px; }
.rows { display:flex; flex-direction:column; gap:8px; }
.row { display:flex; align-items:center; gap:8px; color:#c5d2e0; font-size:12px; }
.dot { width:10px; height:10px; border-radius:50%; display:inline-block; }
.actor { background:#6f7dff; box-shadow:0 0 8px rgba(111,125,255,.5); }
.movie { background:#6ae3ff; box-shadow:0 0 8px rgba(106,227,255,.5); }
.line { width:20px; height:2px; background:linear-gradient(90deg,#6f7dff,#6ae3ff); display:inline-block; border-radius:2px; }
</style>

