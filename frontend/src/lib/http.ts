import type { ApiError } from '@/types/api'

/*
 * Cliente HTTP do FeedLens.
 *
 * O front é servido pelo próprio Flask (mesma origem), então as requisições
 * levam o cookie de sessão do login automaticamente (`credentials: 'same-origin'`).
 * Métodos que alteram estado na API de settings exigem o header X-CSRF-Token,
 * cujo valor vem do GET /api/settings/providers e é guardado aqui.
 */

const CSRF_HEADER = 'X-CSRF-Token'

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
  /** Anexa o header CSRF (para escritas na API de settings). */
  csrf?: boolean
  signal?: AbortSignal
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
