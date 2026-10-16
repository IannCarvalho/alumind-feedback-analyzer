import type { Sentiment } from '@/types/api'

/*
 * Apresentação do sentimento: rótulo, classe do chip (theme.css), ícone e a
 * cor usada nos gráficos. Fonte única para Dashboard e lista de feedbacks.
 * Cor sempre acompanha ícone + rótulo (paleta Okabe-Ito, legível a daltônicos).
 */
export interface SentimentMeta {
  label: string
  chipClass: string
  icon: string
  color: string
}

const META: Record<Sentiment, SentimentMeta> = {
  POSITIVO: {
    label: 'Positivo',
    chipClass: 'fl-sentiment fl-sentiment--positive',
    icon: 'pi pi-arrow-up-right',
    color: '#009e73',
  },
  NEGATIVO: {
    label: 'Negativo',
    chipClass: 'fl-sentiment fl-sentiment--negative',
    icon: 'pi pi-arrow-down-right',
    color: '#d55e00',
  },
  INCONCLUSIVO: {
    label: 'Inconclusivo',
    chipClass: 'fl-sentiment fl-sentiment--inconclusive',
    icon: 'pi pi-circle',
    color: '#8a8fa3',
  },
}

export function sentimentMeta(sentiment: Sentiment | null | undefined): SentimentMeta {
  return META[sentiment ?? 'INCONCLUSIVO'] ?? META.INCONCLUSIVO
}

export function formatDate(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return iso
  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}
