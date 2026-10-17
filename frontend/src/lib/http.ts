import type { ApiError, SessionResponse } from '@/types/api'

/*
 * Cliente HTTP do FeedLens.
 *
 * O front é servido pelo próprio Flask (mesma origem), então as requisições
 * levam o cookie de sessão do login automaticamente (`credentials: 'same-origin'`).
 * Métodos que alteram estado (login e API de settings) exigem o header
 * X-CSRF-Token, cujo valor vem de GET /auth/session ou de GET
 * /api/settings/providers e é guardado aqui.
 */

const CSRF_HEADER = 'X-CSRF-Token'
const LOGIN_PATH = '/login'

let csrfToken: string | null = null

export function setCsrfToken(token: string | null): void {
  csrfToken = token
}

export class HttpError extends Error {
  status: number
  code?: string
  body?: ApiError

  constructor(status: number, body?: ApiError) {
    super(body?.error ?? `HTTP ${status}`)
    this.name = 'HttpError'
    this.status = status
    this.code = body?.code
    this.body = body
  }
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE'
  body?: unknown
  /** Anexa o header CSRF (login e escritas na API de settings). */
  csrf?: boolean
  signal?: AbortSignal
}

/**
 * Um 401 no meio do uso costuma ser a sessão que expirou: manda ao login e
 * volta para onde estava depois. Só redireciona se o servidor confirmar que há
 * login e a sessão acabou; com o login desligado, um 401 vem de outra regra
 * (ex.: só API_READ_TOKEN) e ir ao /login viraria um loop de redirects.
 */
async function redirectToLoginIfSessionEnded(): Promise<void> {
  if (window.location.pathname === LOGIN_PATH) return
  try {
    const response = await fetch('/auth/session', { credentials: 'same-origin' })
    if (!response.ok) return
    const state = (await response.json()) as SessionResponse
    if (state.auth_enabled && !state.authenticated) {
      const here = window.location.pathname + window.location.search
      window.location.assign(`${LOGIN_PATH}?next=${encodeURIComponent(here)}`)
    }
  } catch {
    // Sem resposta do servidor: a tela mostra o erro da requisição original.
  }
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, csrf = false, signal } = options
  const headers: Record<string, string> = {}

  if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
  }
  if (csrf && csrfToken) {
    headers[CSRF_HEADER] = csrfToken
  }

  const response = await fetch(path, {
    method,
    headers,
    credentials: 'same-origin',
    body: body !== undefined ? JSON.stringify(body) : undefined,
    signal,
  })

  if (response.status === 204) {
    return undefined as T
  }

  const isJson = response.headers.get('content-type')?.includes('application/json')
  const payload = isJson ? await response.json().catch(() => undefined) : undefined

  if (!response.ok) {
    // O 401 do próprio login é "senha incorreta", não sessão expirada.
    if (response.status === 401 && !path.startsWith(LOGIN_PATH)) {
      await redirectToLoginIfSessionEnded()
    }
    throw new HttpError(response.status, payload as ApiError)
  }
  return payload as T
}

export const http = {
  get: <T>(path: string, signal?: AbortSignal) => request<T>(path, { signal }),
  post: <T>(path: string, body?: unknown, csrf = false) =>
    request<T>(path, { method: 'POST', body, csrf }),
  patch: <T>(path: string, body?: unknown, csrf = false) =>
    request<T>(path, { method: 'PATCH', body, csrf }),
  delete: <T>(path: string, csrf = false) => request<T>(path, { method: 'DELETE', csrf }),
}
