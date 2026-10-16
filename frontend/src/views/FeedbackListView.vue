<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import DataTable, { type DataTablePageEvent } from 'primevue/datatable'
import Column from 'primevue/column'
import Select from 'primevue/select'
import Message from 'primevue/message'

import { useFeedbacksStore } from '@/stores/feedbacks'
import { HttpError } from '@/lib/http'
import { formatDate, sentimentMeta } from '@/lib/sentiment'
import type { Feedback, Sentiment } from '@/types/api'

const store = useFeedbacksStore()
const router = useRouter()
const error = ref<string | null>(null)
const perPage = 20

const sentimentFilter = ref<Sentiment | null>(null)
const sentimentOptions = [
  { label: 'Todos os sentimentos', value: null },
  { label: 'Positivo', value: 'POSITIVO' as const },
  { label: 'Negativo', value: 'NEGATIVO' as const },
  { label: 'Inconclusivo', value: 'INCONCLUSIVO' as const },
]

async function load(page = 1) {
  error.value = null
  try {
    await store.list({ page, perPage, sentiment: sentimentFilter.value })
  } catch (e) {
    error.value = e instanceof HttpError ? e.message : 'Não foi possível carregar os feedbacks.'
  }
}

function onPage(event: DataTablePageEvent) {
  load(event.page + 1)
}

function onFilterChange() {
  load(1)
}

function openDetail(feedback: Feedback) {
  router.push({ name: 'feedback-detail', params: { id: feedback.id } })
}

function truncate(text: string, max = 80): string {
  return text.length > max ? `${text.slice(0, max)}…` : text
}

onMounted(() => load(1))
</script>

<template>
  <section class="fl-page">
    <header class="fl-page__head">
      <h1>Feedbacks</h1>
      <Select
        v-model="sentimentFilter"
        :options="sentimentOptions"
        option-label="label"
        option-value="value"
        class="fl-filter"
        @change="onFilterChange"
      />
    </header>

    <Message v-if="error" severity="warn" :closable="false">{{ error }}</Message>

    <DataTable
      :value="store.items"
      :loading="store.loading"
      lazy
      paginator
      :rows="perPage"
      :total-records="store.pagination?.total ?? 0"
      :first="((store.pagination?.page ?? 1) - 1) * perPage"
      data-key="id"
      selection-mode="single"
      @page="onPage"
      @row-select="openDetail($event.data)"
    >
      <template #empty>Nenhum feedback encontrado.</template>

      <Column header="Sentimento" style="width: 10rem">
        <template #body="{ data }">
          <span :class="sentimentMeta(data.sentiment).chipClass">
            <i :class="sentimentMeta(data.sentiment).icon" aria-hidden="true" />
            {{ sentimentMeta(data.sentiment).label }}
          </span>
        </template>
      </Column>

      <Column header="Feedback">
        <template #body="{ data }">{{ truncate(data.feedback) }}</template>
      </Column>

      <Column header="Funcionalidades" style="width: 9rem">
        <template #body="{ data }">
          <span class="fl-count">{{ data.requested_features.length }}</span>
        </template>
      </Column>

      <Column header="Data" style="width: 12rem">
        <template #body="{ data }">
          <time class="fl-date">{{ formatDate(data.created_at) }}</time>
        </template>
      </Column>
    </DataTable>
  </section>
</template>

<style scoped>
.fl-page__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.25rem;
}
.fl-page__head h1 {
  margin: 0;
  font-size: 1.5rem;
}
.fl-filter {
  min-width: 15rem;
}
.fl-count {
  font-family: var(--fl-font-mono);
  color: var(--fl-text-muted);
}
.fl-date {
  font-family: var(--fl-font-mono);
  font-size: 0.82rem;
  color: var(--fl-text-muted);
}
</style>
