import { createApp } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'

import App from './App.vue'
import router from './router'
import { FeedLensPreset } from './theme/preset'

import 'primeicons/primeicons.css'
import './assets/theme.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(PrimeVue, {
  theme: {
    preset: FeedLensPreset,
    options: {
      // Segue o tema do painel/SO; a classe .dark é alternada no App.vue.
      darkModeSelector: '.dark',
      cssLayer: false,
    },
  },
})

// Monta depois de resolver a primeira rota: a tela de login não tem a barra
// lateral, e montar antes faria o shell do painel piscar por um instante.
router.isReady().then(() => app.mount('#app'))
