<template>
  <transition name="fade">
    <div v-if="open" class="backdrop" @click="close"></div>
  </transition>
  <transition name="slide">
    <aside v-if="open" class="drawer" ref="root" tabindex="0" @keydown.esc.prevent="close">
      <div class="head">
        <div class="title">设置</div>
        <button class="close" @click="close">×</button>
      </div>
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
        <section>
          <h3>子节点上限</h3>
          <div class="row">
            <input type="range" min="1" max="200" v-model.number="childLimit" class="input" />
            <span style="width:40px; text-align:right;">{{ childLimit }}</span>
          </div>
        </section>
      </div>
    </aside>
  </transition>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { useGraphStore } from '@/stores/graph'

const publishers = ['s1s1s1', 'ideapocket', 'attackers', 'premium', 'mvg', 'moodyz']
const selected = reactive({ publishers: new Set<string>() })
const yearFrom = ref<number | null>(2010)
const yearTo = ref<number | null>(2025)
const onlyLocal = ref(false)
const highRated = ref(true)
const layout = ref<'force' | 'grid' | 'radial'>('force')
const store = useGraphStore()
const childLimit = ref<number>(store.childLimit)
const open = ref(false)
const root = ref<HTMLElement|null>(null)

function toggle(key: 'publishers', value: string) {
  const set = selected[key]
  set.has(value) ? set.delete(value) : set.add(value)
}

function close(){ open.value = false }

function onToggle(){ open.value = !open.value }

onMounted(() => {
  window.addEventListener('ui:toggle-settings', onToggle)
})
onBeforeUnmount(() => {
  window.removeEventListener('ui:toggle-settings', onToggle)
})

watch(layout, (v) => store.setLayout(v))
watch(childLimit, (v) => store.childLimit = v)
</script>

<style scoped>
.backdrop { position:fixed; inset:0; background:rgba(0,0,0,.35); z-index: 60; }
.drawer { position:fixed; left:0; top:64px; bottom:0; width:320px; background:#0e141b; border-right:1px solid var(--border); z-index:61; display:flex; flex-direction:column; box-shadow: 0 10px 30px rgba(0,0,0,.4); }
.head { display:flex; align-items:center; justify-content:space-between; padding:10px 12px; border-bottom:1px solid var(--border); }
.close { height:28px; width:28px; border-radius:6px; border:1px solid var(--border); background:#0b1117; color:var(--text); cursor:pointer; }
.filters { padding: 16px; display:flex; flex-direction:column; gap:18px; overflow:auto; }
section { border:1px solid var(--border); background:#0e141b; border-radius:12px; padding:12px; }
h3 { font-size:12px; color:#9fb1c7; margin:0 0 8px; letter-spacing:.5px; }
.chips { display:flex; flex-wrap:wrap; gap:8px; }
.chip { padding:6px 10px; border-radius:20px; border:1px solid var(--border); background:#0b1117; color:var(--text); cursor:pointer; }
.chip.active { background: rgba(106,227,255,.12); border-color:#2d3c4d; box-shadow:0 0 20px rgba(106,227,255,.1) inset; }
.row { display:flex; align-items:center; gap:8px; min-width:0; }
.input, .select { flex:1; min-width:0; width:0; height:32px; box-sizing:border-box; border-radius:8px; border:1px solid var(--border); background:#0b1117; color:var(--text); padding:0 8px; overflow:hidden; }
.ck { display:flex; align-items:center; gap:8px; color:#b8c7d9; font-size:12px; }

/* transitions */
.fade-enter-active, .fade-leave-active { transition: opacity .15s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.slide-enter-active, .slide-leave-active { transition: transform .2s ease; }
.slide-enter-from, .slide-leave-to { transform: translateX(-100%); }
</style>
