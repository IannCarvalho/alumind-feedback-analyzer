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

app.mount('#app')
