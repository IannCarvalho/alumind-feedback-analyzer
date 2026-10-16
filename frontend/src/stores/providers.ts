import { defineStore } from 'pinia'
import { ref } from 'vue'

import { http, setCsrfToken } from '@/lib/http'
import type {
  ProviderCatalogEntry,
  ProviderCredential,
  ProviderTestResult,
  ProvidersResponse,
} from '@/types/api'

const BASE = '/api/settings/providers'

/*
 * Estado do cofre de chaves de provedor (a tela de configuração BYOK).
 * A chave em claro nunca entra aqui: o backend só devolve `key_hint`.
 */
export const useProvidersStore = defineStore('providers', () => {
  const vaultEnabled = ref(false)
  const catalog = ref<ProviderCatalogEntry[]>([])
  const environmentChain = ref<string[]>([])
  const credentials = ref<ProviderCredential[]>([])
  const loading = ref(false)
  const loaded = ref(false)

  async function load(): Promise<void> {
    loading.value = true
    try {
      const data = await http.get<ProvidersResponse>(BASE)
      setCsrfToken(data.csrf_token)
      vaultEnabled.value = data.vault_enabled
      catalog.value = data.catalog
      environmentChain.value = data.environment_chain
      credentials.value = data.providers
      loaded.value = true
    } finally {
      loading.value = false
    }
  }

  async function create(payload: {
    provider: string
    api_key: string
    model?: string
    priority?: number
  }): Promise<ProviderCredential> {
    const row = await http.post<ProviderCredential>(BASE, payload, true)
    credentials.value = [...credentials.value, row].sort((a, b) => a.priority - b.priority)
    return row
  }

  async function update(
    id: string,
    changes: Partial<Pick<ProviderCredential, 'enabled' | 'priority' | 'model'>> & {
      api_key?: string
    },
  ): Promise<void> {
    const row = await http.patch<ProviderCredential>(`${BASE}/${id}`, changes, true)
    credentials.value = credentials.value.map((c) => (c.id === id ? row : c))
  }

  async function remove(id: string): Promise<void> {
    await http.delete(`${BASE}/${id}`, true)
    credentials.value = credentials.value.filter((c) => c.id !== id)
  }

  async function reorder(ids: string[]): Promise<void> {
    const data = await http.post<{ providers: ProviderCredential[] }>(
      `${BASE}/reorder`,
      { ids },
      true,
    )
    credentials.value = data.providers
  }

  async function test(id: string): Promise<ProviderTestResult> {
    const result = await http.post<ProviderTestResult>(`${BASE}/${id}/test`, undefined, true)
    credentials.value = credentials.value.map((c) => (c.id === id ? result.provider : c))
    return result
  }

  return {
    vaultEnabled,
    catalog,
    environmentChain,
    credentials,
    loading,
    loaded,
    load,
    create,
    update,
    remove,
    reorder,
    test,
  }
})
