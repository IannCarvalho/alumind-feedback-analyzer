<script setup lang="ts">
import { RouterLink } from 'vue-router'
import Button from 'primevue/button'
</script>

<template>
  <section class="fl-404">
    <h1>404</h1>
    <p class="fl-muted">Essa página não existe no painel.</p>
    <RouterLink to="/">
      <Button label="Voltar à visão geral" icon="pi pi-arrow-left" text />
    </RouterLink>
  </section>
</template>

<style scoped>
.fl-404 {
  text-align: center;
  padding: 4rem 1rem;
}
.fl-404 h1 {
  font-size: 3rem;
  margin: 0;
  color: var(--fl-amber);
}
.fl-muted {
  color: var(--fl-text-muted);
  margin: 0.5rem 0 1.5rem;
}
</style>
