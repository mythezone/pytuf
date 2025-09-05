import './assets/main.css'
import VNetworkGraph from "v-network-graph"
import "v-network-graph/lib/style.css"

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'

const app = createApp(App)


app.use(VNetworkGraph)
app.use(createPinia())
app.use(router)

app.mount('#app')
