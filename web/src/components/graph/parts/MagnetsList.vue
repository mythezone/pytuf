<template>
  <div class="magnets" v-if="items?.length">
    <div v-for="(m,i) in items" :key="i" class="row">
      <div class="name">{{ m.name || m.meta_text || '磁力' }}</div>
      <div class="ops">
        <button class="btn" @click="copy(m.magnet)">复制</button>
        <button class="btn sec" @click="download(m.magnet)">下载</button>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
const props = defineProps<{ items?: { magnet?: string; name?: string; meta_text?: string }[] }>()
function copy(text?: string) {
  if (text) navigator.clipboard?.writeText(text)
}
function download(text?: string) {
  // TODO: integrate qBittorrent API
  if (text) navigator.clipboard?.writeText(text)
}
</script>
<style scoped>
.magnets { display:flex; flex-direction:column; gap:6px; }
.row { display:flex; align-items:center; justify-content:space-between; padding:6px 8px; border:1px solid var(--border); border-radius:6px; background:#0e141b; }
.name { font-size:12px; color:#dbe7f3; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.ops { display:flex; gap:6px; }
.btn { height:24px; padding:0 8px; background:#0b1117; color:#cfe1f0; border:1px solid var(--border); border-radius:6px; cursor:pointer; font-size:12px; }
.btn.sec { background:#10212e; }
</style>

