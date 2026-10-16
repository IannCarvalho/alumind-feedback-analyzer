<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import Card from 'primevue/card'
import Message from 'primevue/message'
import Tag from 'primevue/tag'
import ProgressSpinner from 'primevue/progressspinner'

import { useProvidersStore } from '@/stores/providers'
import { HttpError } from '@/lib/http'

const store = useProvidersStore()
const error = ref<string | null>(null)

const hasChain = computed(() => store.environmentChain.length > 0)

onMounted(async () => {
  try {
    await store.load()
  } catch (e) {
    // O backend recusa (403/401) sem DASHBOARD_PASSWORD ou sessão — mostramos
    // a razão em vez de uma tela vazia.
    error.value =
      e instanceof HttpError ? e.message : 'Não foi possível carregar os provedores.'
  }
})
</script>

<template>
  <section class="fl-page">
    <header class="fl-page__head">
      <h1>Provedores de IA <span class="fl-byok">· traga sua chave</span></h1>
      <p class="fl-muted">
        Ordene os provedores que analisam os feedbacks. A chave principal é
        tentada primeiro; as demais entram como reserva.
      </p>
    </header>

    <div v-if="store.loading" class="fl-loading">
      <ProgressSpinner style="width: 2.5rem; height: 2.5rem" />
    </div>

    <Message v-else-if="error" severity="warn" :closable="false">{{ error }}</Message>

    <template v-else>
      <Message v-if="!store.vaultEnabled" severity="info" :closable="false">
        O cofre de chaves está desligado (defina <code>FEEDLENS_ENCRYPTION_KEY</code>).
        A análise usa apenas as chaves do ambiente, listadas abaixo.
      </Message>

      <Card class="fl-chain">
        <template #title>Cadeia do ambiente</template>
        <template #content>
          <p class="fl-muted fl-chain__hint">
            Chaves definidas por variável de ambiente no servidor, usadas quando
            não há chave salva nem BYOK por requisição.
          </p>
          <ol v-if="hasChain" class="fl-chain__list">
            <li v-for="(modelRef, i) in store.environmentChain" :key="modelRef">
              <span class="fl-chain__pos">{{ i + 1 }}</span>
              <code>{{ modelRef }}</code>
            </li>
          </ol>
          <p v-else class="fl-muted">Nenhuma chave de provedor no ambiente.</p>
        </template>
      </Card>

      <Card class="fl-saved">
        <template #title>Chaves salvas</template>
        <template #content>
          <ol v-if="store.credentials.length" class="fl-saved__list">
            <li v-for="c in store.credentials" :key="c.id" class="fl-saved__row">
              <span class="fl-chain__pos">{{ c.priority }}</span>
              <code>{{ c.provider }} · {{ c.model }}</code>
              <code class="fl-hint">{{ c.key_hint }}</code>
              <Tag
                :value="c.enabled ? 'ativa' : 'desativada'"
                :severity="c.enabled ? 'success' : 'secondary'"
              />
              <Tag
                v-if="c.verified"
                value="verificada"
                severity="info"
                icon="pi pi-check"
              />
            </li>
          </ol>
          <p v-else class="fl-muted">
            Nenhuma chave salva ainda. O formulário de cadastro chega no PR da
            tela de provedores.
          </p>
        </template>
      </Card>
    </template>
  </section>
</template>

<style scoped>
.fl-page__head h1 {
  margin: 0 0 0.25rem;
  font-size: 1.5rem;
}
.fl-byok {
  color: var(--fl-text-muted);
  font-weight: 400;
  font-size: 1rem;
}
.fl-muted {
  color: var(--fl-text-muted);
}
.fl-page__head .fl-muted {
  margin: 0 0 1.5rem;
}
.fl-loading {
  display: flex;
  justify-content: center;
  padding: 3rem;
}
.fl-chain,
.fl-saved {
  margin-top: 1rem;
}
.fl-chain__hint {
  margin-top: 0;
}
.fl-chain__list,
.fl-saved__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  font-family: var(--fl-font-mono);
  font-size: 0.85rem;
}
.fl-saved__row {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex-wrap: wrap;
}
.fl-chain__pos {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.5rem;
  height: 1.5rem;
  border-radius: 50%;
  background: color-mix(in srgb, var(--fl-cyan) 16%, transparent);
  color: var(--fl-cyan);
  font-weight: 600;
  flex-shrink: 0;
}
.fl-hint {
  color: var(--fl-text-muted);
}
</style>
