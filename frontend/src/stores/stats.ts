import { defineStore } from 'pinia'
import { ref } from 'vue'

import { http } from '@/lib/http'
import type { DashboardStats } from '@/types/api'

export const useStatsStore = defineStore('stats', () => {
  const data = ref<DashboardStats | null>(null)
  const loading = ref(false)

  async function load(): Promise<void> {
    loading.value = true
    try {
      data.value = await http.get<DashboardStats>('/api/stats')
    } finally {
      loading.value = false
    }
  }

  return { data, loading, load }
})
