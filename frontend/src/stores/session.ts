import { defineStore } from 'pinia'
import { ref } from 'vue'

import { HttpError, http, setCsrfToken } from '@/lib/http'
import type { LoginResponse, SessionResponse } from '@/types/api'

/*
 * Sessão do painel. Quem decide tudo é o servidor (senha, CSRF, rate limit,
 * sessão nova no login, filtro do `next`); aqui só se guarda o estado que a
 * interface precisa: se há login, se a sessão vale e o token CSRF.
 */
export const useSessionStore = defineStore('session', () => {
  const authEnabled = ref(false)
  const authenticated = ref(false)
  const loaded = ref(false)

  let inflight: Promise<SessionResponse> | null = null

  /** GET /auth/session. Chamadas simultâneas (shell + tela de login) viram uma só. */
  function load(): Promise<SessionResponse> {
    if (!inflight) {
      inflight = http
        .get<SessionResponse>('/auth/session')
        .then((state) => {
          authEnabled.value = state.auth_enabled
          authenticated.value = state.authenticated
          setCsrfToken(state.csrf_token)
          loaded.value = true
          return state
        })
        .finally(() => {
          inflight = null
        })
    }
    return inflight
  }

  /** POST /login. Devolve o destino que o servidor aprovou. */
  async function login(password: string, next?: string): Promise<string> {
    const path = next ? `/login?next=${encodeURIComponent(next)}` : '/login'
    const attempt = async () => (await http.post<LoginResponse>(path, { password }, true)).next
    try {
      return await attempt()
    } catch (e) {
      // Token velho (a sessão expirou ou o servidor reiniciou com outra
      // SECRET_KEY): pega um novo e tenta uma única vez, sem incomodar ninguém.
      if (e instanceof HttpError && e.code === 'csrf') {
        await load()
        return attempt()
      }
      throw e
    }
  }

  return { authEnabled, authenticated, loaded, load, login }
})
