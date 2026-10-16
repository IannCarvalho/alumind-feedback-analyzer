<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'

import BrandLogo from '@/components/BrandLogo.vue'

const route = useRoute()
const isDark = ref(false)

const nav = [
  { to: '/', label: 'Visão geral', icon: 'pi pi-chart-bar' },
  { to: '/feedbacks', label: 'Feedbacks', icon: 'pi pi-comments' },
  { to: '/providers', label: 'Provedores de IA', icon: 'pi pi-sliders-h' },
]

function isActive(to: string): boolean {
  // '/' casa só exato; as demais casam a seção inteira (ex /feedbacks/:id).
  return to === '/' ? route.path === '/' : route.path.startsWith(to)
}

function applyTheme(dark: boolean) {
  isDark.value = dark
  document.documentElement.classList.toggle('dark', dark)
  document.documentElement.classList.toggle('light', !dark)
  localStorage.setItem('fl-theme', dark ? 'dark' : 'light')
}

function toggleTheme() {
  applyTheme(!isDark.value)
}

onMounted(() => {
  const saved = localStorage.getItem('fl-theme')
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
  applyTheme(saved ? saved === 'dark' : prefersDark)
})
</script>

<template>
  <div class="fl-shell">
    <aside class="fl-sidebar">
      <div class="fl-brand">
        <BrandLogo :size="34" />
        <div>
          <div class="fl-brand__name">FeedLens</div>
          <div class="fl-brand__tag">traga sua lente</div>
        </div>
      </div>
      <nav class="fl-nav">
        <RouterLink
          v-for="item in nav"
          :key="item.to"
          :to="item.to"
          class="fl-nav__link"
          :class="{ 'fl-nav__link--active': isActive(item.to) }"
        >
          <i :class="item.icon" aria-hidden="true" />
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>
      <div class="fl-sidebar__foot">
        <button type="button" class="fl-theme-toggle" @click="toggleTheme">
          <i :class="isDark ? 'pi pi-sun' : 'pi pi-moon'" aria-hidden="true" />
          <span>{{ isDark ? 'Tema claro' : 'Tema escuro' }}</span>
        </button>
        <form action="/logout" method="post" class="fl-logout">
          <button type="submit" class="fl-logout__btn">
            <i class="pi pi-sign-out" aria-hidden="true" /> Sair
          </button>
        </form>
      </div>
    </aside>
    <main class="fl-main">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.fl-shell {
  display: grid;
  grid-template-columns: 248px 1fr;
  min-height: 100vh;
}
.fl-sidebar {
  display: flex;
  flex-direction: column;
  background: var(--fl-surface);
  border-right: 1px solid var(--fl-border);
  padding: 1.25rem 1rem;
}
.fl-brand {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  color: var(--fl-text);
  padding: 0.25rem 0.5rem 1.25rem;
}
.fl-brand__name {
  font-weight: 700;
  font-size: 1.15rem;
}
.fl-brand__tag {
  font-size: 0.72rem;
  color: var(--fl-text-muted);
  font-family: var(--fl-font-mono);
}
.fl-nav {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  flex: 1;
}
.fl-nav__link {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.55rem 0.75rem;
  border-radius: var(--fl-radius);
  color: var(--fl-text-muted);
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 500;
  transition: background 0.15s, color 0.15s;
}
.fl-nav__link:hover {
  background: var(--fl-surface-2);
  color: var(--fl-text);
}
.fl-nav__link--active {
  background: color-mix(in srgb, var(--fl-cyan) 14%, transparent);
  color: var(--fl-cyan);
}
.fl-sidebar__foot {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  border-top: 1px solid var(--fl-border);
  padding-top: 0.75rem;
}
.fl-theme-toggle,
.fl-logout__btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  background: transparent;
  border: 1px solid var(--fl-border);
  color: var(--fl-text-muted);
  padding: 0.5rem 0.75rem;
  border-radius: var(--fl-radius);
  font: inherit;
  font-size: 0.85rem;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.fl-theme-toggle:hover,
.fl-logout__btn:hover {
  background: var(--fl-surface-2);
  color: var(--fl-text);
}
.fl-logout {
  margin: 0;
}
.fl-main {
  padding: 2rem 2.25rem;
  overflow-x: hidden;
}
@media (max-width: 720px) {
  .fl-shell {
    grid-template-columns: 1fr;
  }
  .fl-sidebar {
    border-right: none;
    border-bottom: 1px solid var(--fl-border);
  }
}
</style>
