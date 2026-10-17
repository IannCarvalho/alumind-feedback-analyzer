import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// O build sai em ../app/static/spa e é servido pelo próprio Flask (mesma
// origem do painel), então o cookie de sessão do login continua valendo e
// não há CORS com credenciais. `base` casa com a rota que serve os assets.
export default defineConfig({
  plugins: [vue()],
  base: '/static/spa/',
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  build: {
    outDir: fileURLToPath(new URL('../app/static/spa', import.meta.url)),
    emptyOutDir: true,
    sourcemap: true,
  },
  server: {
    port: 5173,
    // Em dev o Vite serve o front e encaminha a API/login para o Flask
    // (localhost:5000), mantendo a mesma origem do ponto de vista do browser.
    proxy: {
      '/api': 'http://127.0.0.1:5000',
      '/auth': 'http://127.0.0.1:5000',
      '/login': 'http://127.0.0.1:5000',
      '/logout': 'http://127.0.0.1:5000',
      '/health': 'http://127.0.0.1:5000',
    },
  },
})
