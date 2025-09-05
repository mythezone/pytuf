<template>
  <div class="drawer" :class="{ open }">
    <div class="handle" @click="open = !open">设置</div>
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
import { ref } from 'vue'
const open = ref(false)
const showLabels = ref(true)
const highlightNeighbors = ref(true)
const nodeSize = ref(10)
const edgeWidth = ref(2)
</script>

<style scoped>
.drawer { position: fixed; right: 0; top: 80px; width: 0; overflow: hidden; transition: width .25s ease; z-index: 30; }
.drawer.open { width: 280px; }
.handle { position:absolute; left:-48px; top:0; height:36px; display:grid; place-items:center; padding:0 8px; background:#0e141b; color:#c5d2e0; border:1px solid var(--border); border-right: none; border-radius:8px 0 0 8px; cursor:pointer; }
.content { height: calc(100vh - 120px); overflow:auto; background:#0e141b; border-left:1px solid var(--border); padding:12px; }
h3 { margin:12px 0 8px; color:#9fb1c7; font-size:12px; }
.row { display:flex; align-items:center; gap:8px; color:#c5d2e0; font-size:12px; padding:6px 0; }
input[type=range] { flex:1; }
</style>

