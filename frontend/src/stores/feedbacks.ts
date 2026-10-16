import { defineStore } from 'pinia'
import { ref } from 'vue'

import { http } from '@/lib/http'
import type { Feedback, FeedbackListResponse, Pagination, Sentiment } from '@/types/api'

export const useFeedbacksStore = defineStore('feedbacks', () => {
  const items = ref<Feedback[]>([])
  const pagination = ref<Pagination | null>(null)
  const loading = ref(false)

  async function list(params: {
    page?: number
    perPage?: number
    sentiment?: Sentiment | null
  }): Promise<void> {
    loading.value = true
    try {
      const query = new URLSearchParams()
      query.set('page', String(params.page ?? 1))
      query.set('per_page', String(params.perPage ?? 20))
      if (params.sentiment) query.set('sentiment', params.sentiment)
      const data = await http.get<FeedbackListResponse>(`/api/feedbacks?${query.toString()}`)
      items.value = data.items
      pagination.value = data.pagination
    } finally {
      loading.value = false
    }
  }

  async function getById(id: string): Promise<Feedback> {
    return http.get<Feedback>(`/api/feedbacks/${id}`)
  }

  return { items, pagination, loading, list, getById }
})
