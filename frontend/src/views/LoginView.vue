<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'

import BrandLogo from '@/components/BrandLogo.vue'
import { HttpError } from '@/lib/http'
import { useSessionStore } from '@/stores/session'

const session = useSessionStore()
const route = useRoute()
const router = useRouter()

const password = ref('')
const error = ref<string | null>(null)
const submitting = ref(false)
const ready = ref(false)

// Repassado ao servidor, que só aceita caminhos locais e devolve o destino
// aprovado. A tela nunca navega para o `next` cru da URL.
const next = computed(() => (typeof route.query.next === 'string' ? route.query.next : undefined))

function selectPassword() {
  nextTick(() => {
    const input = document.getElementById('fl-password') as HTMLInputElement | null
    input?.focus()
    input?.select()
  })
}

function messageFor(e: unknown): string {
  // O servidor já manda a orientação (senha incorreta, sessão expirada,
  // muitas tentativas); sem resposta dele, o problema é a conexão.
  if (e instanceof HttpError && e.body?.error) return e.message
  return 'Não foi possível entrar. Verifique sua conexão e tente de novo.'
}

async function submit() {
  error.value = null
  if (!password.value) {
    error.value = 'Digite a senha de acesso do painel para entrar.'
    selectPassword()
    return
  }
  submitting.value = true
  try {
    const target = await session.login(password.value, next.value)
    // Navegação completa: o painel recarrega já com a sessão nova.
    window.location.assign(target)
  } catch (e) {
    error.value = messageFor(e)
    submitting.value = false
    selectPassword()
  }
}

onMounted(async () => {
  try {
    await session.load()
    if (!session.authEnabled || session.authenticated) {
      // Login desligado ou sessão ativa: não há o que fazer aqui.
      await router.replace('/')
      return
    }
  } catch {
    error.value =
      'Não foi possível falar com o servidor. Recarregue a página; se persistir, verifique se ele está no ar.'
  }
  ready.value = true
  selectPassword()
})
</script>

<template>
  <main class="fl-login">
    <section class="fl-login__card" aria-labelledby="fl-login-title">
      <header class="fl-login__brand">
        <BrandLogo :size="44" />
        <h1 id="fl-login-title" class="fl-login__title">Entrar no FeedLens</h1>
        <p class="fl-login__tag">análise de feedback</p>
      </header>

      <form class="fl-login__form" novalidate @submit.prevent="submit">
        <label for="fl-password" class="fl-login__label">Senha de acesso</label>
        <InputText
          id="fl-password"
          v-model="password"
          type="password"
          autocomplete="current-password"
          aria-describedby="fl-login-help"
          :invalid="Boolean(error)"
          :disabled="!ready || submitting"
          fluid
        />
        <small id="fl-login-help" class="fl-login__help">
          A senha compartilhada do painel, definida por quem administra o FeedLens.
        </small>

        <Message v-if="error" severity="error" :closable="false" role="alert">
          {{ error }}
        </Message>

        <Button
          type="submit"
          label="Entrar"
          icon="pi pi-sign-in"
          :loading="submitting"
          :disabled="!ready"
          fluid
        />
      </form>
    </section>
  </main>
</template>

<style scoped>
.fl-login {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 1.5rem;
  background: var(--fl-bg);
  color: var(--fl-text);
}
.fl-login__card {
  width: 100%;
  max-width: 24rem;
  background: var(--fl-surface);
  color: var(--fl-text);
  border: 1px solid var(--fl-border);
  border-radius: calc(var(--fl-radius) + 2px);
  box-shadow: var(--fl-shadow);
  padding: 2rem 1.75rem;
}
.fl-login__brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  margin-bottom: 1.75rem;
}
.fl-login__title {
  margin: 0.6rem 0 0;
  font-size: 1.3rem;
  font-weight: 700;
}
.fl-login__tag {
  margin: 0.2rem 0 0;
  font-family: var(--fl-font-mono);
  font-size: 0.72rem;
  color: var(--fl-text-muted);
}
.fl-login__form {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.fl-login__label {
  font-size: 0.88rem;
  font-weight: 500;
}
.fl-login__help {
  margin-top: -0.35rem;
  font-size: 0.78rem;
  color: var(--fl-text-muted);
}
</style>
