<script setup lang="ts">
import Card from 'primevue/card'
import Tag from 'primevue/tag'
</script>

<template>
  <section class="fl-page">
    <header class="fl-page__head">
      <h1>Visão geral</h1>
      <p class="fl-muted">
        Foco no que seus usuários pedem, com a IA que você escolher.
      </p>
    </header>

    <Card class="fl-note">
      <template #content>
        <div class="fl-note__body">
          <i class="pi pi-wrench" aria-hidden="true" />
          <div>
            <strong>Andaime do novo front.</strong>
            Esta é a base Vue 3 + Vite + PrimeVue. As estatísticas e os gráficos
            do dashboard chegam no próximo PR; aqui provamos a arquitetura
            (layout, tema, roteamento e a tela de provedores já ligada à API).
            <div class="fl-note__tags">
              <Tag value="Vue 3" severity="secondary" />
              <Tag value="Vite" severity="secondary" />
              <Tag value="PrimeVue" severity="secondary" />
              <Tag value="TypeScript" severity="secondary" />
            </div>
          </div>
        </div>
      </template>
    </Card>
  </section>
</template>

<style scoped>
.fl-page__head h1 {
  margin: 0 0 0.25rem;
  font-size: 1.5rem;
}
.fl-muted {
  color: var(--fl-text-muted);
  margin: 0 0 1.5rem;
}
.fl-note__body {
  display: flex;
  gap: 0.75rem;
  align-items: flex-start;
  line-height: 1.6;
}
.fl-note__body i {
  color: var(--fl-amber);
  font-size: 1.2rem;
  margin-top: 0.15rem;
}
.fl-note__tags {
  display: flex;
  gap: 0.4rem;
  margin-top: 0.75rem;
  flex-wrap: wrap;
}
</style>
