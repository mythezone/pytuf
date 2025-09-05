<template>
  <div v-if="node" class="popover">
    <div class="head">
      <div class="icon" :class="node.type" />
      <div class="titles">
        <div class="kicker">{{ node.type === 'actress' ? '演员' : '影片' }}</div>
        <div class="title">{{ title }}</div>
        <div class="sub" v-if="subtitle">{{ subtitle }}</div>
      </div>
      <button class="close" @click="$emit('close')">✕</button>
    </div>
    <div class="body">
      <div v-if="node.type==='actress'" class="grid">
        <div><span class="label">发布商</span><div class="value">{{ node.data?.publisher ?? '-' }}</div></div>
        <div><span class="label">作品数</span><div class="value">—</div></div>
      </div>
      <div v-else class="grid">
        <div><span class="label">代码</span><div class="value">{{ node.data?.code ?? '-' }}</div></div>
        <div><span class="label">发布商</span><div class="value">{{ node.data?.publisher ?? '-' }}</div></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

defineEmits<{ (e: 'close'): void }>()
const props = defineProps<{ node?: { id: string; type: 'actress'|'movie'; label: string; data?: Record<string, any> } }>()

const title = computed(() => props.node?.type === 'actress' ? (props.node?.label ?? '') : (props.node?.data?.title ?? props.node?.label ?? ''))
const subtitle = computed(() => props.node?.type === 'movie' ? props.node?.label : '')
</script>

<style scoped>
.popover {
  position:absolute; right:12px; top:12px; width:320px;
  border:1px solid var(--border); background:#0e141b; color:var(--text);
  border-radius:14px; box-shadow:0 10px 30px rgba(0,0,0,.4), inset 0 0 0 1px rgba(106,227,255,.08);
  overflow:hidden;
}
.head { display:flex; align-items:center; gap:12px; padding:12px; border-bottom:1px solid var(--border); background:rgba(10,16,23,.4); backdrop-filter: blur(8px); }
.icon { width:28px; height:28px; border-radius:8px; box-shadow:0 0 24px rgba(106,227,255,.35); }
.icon.actress { background: linear-gradient(135deg,#6f7dff,#9aa2ff); }
.icon.movie   { background: linear-gradient(135deg,#6ae3ff,#86f0ff); }
.titles { flex:1; min-width:0; }
.kicker { color:#9fb1c7; font-size:11px; letter-spacing:.4px; }
.title { font-size:14px; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.sub { color:#8ea3b8; font-size:12px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.close { border:none; background:#0b1117; color:#cbd7e6; width:28px; height:28px; border-radius:8px; cursor:pointer; border:1px solid var(--border); }
.body { padding:12px; }
.grid { display:grid; grid-template-columns: 1fr 1fr; gap:10px; }
.label { color:#9fb1c7; font-size:12px; }
.value { font-size:13px; margin-top:4px; }
</style>

