<template>
  <div class="filters">
    <section>
      <h3>发布商</h3>
      <div class="chips">
        <button
          v-for="p in publishers"
          :key="p"
          class="chip"
          :class="{ active: selected.publishers.has(p) }"
          @click="toggle('publishers', p)"
        >{{ p }}</button>
      </div>
    </section>

    <section>
      <h3>时间范围</h3>
      <div class="row">
        <input type="number" v-model.number="yearFrom" class="input" placeholder="起始年" />
        <span>—</span>
        <input type="number" v-model.number="yearTo" class="input" placeholder="终止年" />
      </div>
    </section>

    <section>
      <h3>筛选</h3>
      <label class="ck"><input type="checkbox" v-model="onlyLocal" /> 仅本地有片源</label>
      <label class="ck"><input type="checkbox" v-model="highRated" /> 高评分优先</label>
    </section>

    <section>
      <h3>布局</h3>
      <div class="row">
        <select v-model="layout" class="select">
          <option value="force">力导向</option>
          <option value="grid">网格</option>
          <option value="radial">放射</option>
        </select>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { useGraphStore } from '@/stores/graph'

const publishers = ['s1s1s1', 'ideapocket', 'attackers', 'premium', 'mvg', 'moodyz']
const selected = reactive({ publishers: new Set<string>() })
const yearFrom = ref<number | null>(2010)
const yearTo = ref<number | null>(2025)
const onlyLocal = ref(false)
const highRated = ref(true)
const layout = ref<'force' | 'grid' | 'radial'>('force')
const store = useGraphStore()

function toggle(key: 'publishers', value: string) {
  const set = selected[key]
  set.has(value) ? set.delete(value) : set.add(value)
}

watch(layout, (v) => store.setLayout(v))
</script>

<style scoped>
.filters { padding: 16px; display:flex; flex-direction:column; gap:18px; }
section { border:1px solid var(--border); background:#0e141b; border-radius:12px; padding:12px; }
h3 { font-size:12px; color:#9fb1c7; margin:0 0 8px; letter-spacing:.5px; }
.chips { display:flex; flex-wrap:wrap; gap:8px; }
.chip { padding:6px 10px; border-radius:20px; border:1px solid var(--border); background:#0b1117; color:var(--text); cursor:pointer; }
.chip.active { background: rgba(106,227,255,.12); border-color:#2d3c4d; box-shadow:0 0 20px rgba(106,227,255,.1) inset; }
.row { display:flex; align-items:center; gap:8px; }
.input, .select { flex:1; height:32px; border-radius:8px; border:1px solid var(--border); background:#0b1117; color:var(--text); padding:0 8px; }
.ck { display:flex; align-items:center; gap:8px; color:#b8c7d9; font-size:12px; }
</style>
