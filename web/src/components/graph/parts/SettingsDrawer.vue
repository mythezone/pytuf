<template>
  <div
    class="drawer"
    :class="{ open: isOpen }"
    ref="root"
    tabindex="0"
    @focusout="onFocusOut"
    @keydown.esc.prevent="close"
  >
    <div class="content">
      <h3>显示</h3>
      <label class="row"><input type="checkbox" v-model="showLabels" /> 显示标签</label>
      <label class="row"><input type="checkbox" v-model="highlightNeighbors" /> 高亮邻接</label>

      <h3>节点</h3>
      <div class="row">
        <label>大小</label>
        <input type="range" min="4" max="24" v-model.number="nodeSize" />
      </div>

      <h3>连边</h3>
      <div class="row">
        <label>粗细</label>
        <input type="range" min="1" max="8" v-model.number="edgeWidth" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'

const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{ (e: 'update:open', v: boolean): void }>()

const isOpen = computed({
  get: () => props.open,
  set: (v: boolean) => emit('update:open', v),
})

const root = ref<HTMLDivElement | null>(null)
const close = () => { isOpen.value = false }

function onFocusOut(e: FocusEvent) {
  const next = e.relatedTarget as Node | null
  if (!root.value) return
  // If focus moves outside of the drawer, close it
  if (!next || !root.value.contains(next)) close()
}

let removeOutsideListener: (() => void) | null = null

watch(() => isOpen.value, async (v) => {
  if (v) {
    await nextTick()
    root.value?.focus()
    // Close when clicking outside
    const onDocPointerDown = (e: PointerEvent) => {
      const t = e.target as Node | null
      if (!root.value) return
      if (!t || !root.value.contains(t)) close()
    }
    document.addEventListener('pointerdown', onDocPointerDown, true)
    removeOutsideListener = () => document.removeEventListener('pointerdown', onDocPointerDown, true)
  } else {
    if (removeOutsideListener) { removeOutsideListener(); removeOutsideListener = null }
  }
})

const showLabels = ref(true)
const highlightNeighbors = ref(true)
const nodeSize = ref(10)
const edgeWidth = ref(2)
</script>

<style scoped>
.drawer { position: fixed; left: 0; top: 80px; width: 0; overflow: hidden; transition: width .25s ease; z-index: 50; outline: none; }
.drawer.open { width: 280px; }
.content { height: calc(100vh - 120px); overflow:auto; background:#0e141b; border-right:1px solid var(--border); padding:12px; }
h3 { margin:12px 0 8px; color:#9fb1c7; font-size:12px; }
.row { display:flex; align-items:center; gap:8px; color:#c5d2e0; font-size:12px; padding:6px 0; }
input[type=range] { flex:1; }
</style>
