<script setup lang="ts">
import { computed } from 'vue'
import { Pie } from 'vue-chartjs'
import { ArcElement, Chart as ChartJS, Legend, Tooltip, type ChartOptions } from 'chart.js'

import type { SentimentCounts } from '@/types/api'
import { sentimentMeta } from '@/lib/sentiment'

ChartJS.register(ArcElement, Tooltip, Legend)

const props = defineProps<{ counts: SentimentCounts }>()

const chartData = computed(() => ({
  labels: [
    sentimentMeta('POSITIVO').label,
    sentimentMeta('NEGATIVO').label,
    sentimentMeta('INCONCLUSIVO').label,
  ],
  datasets: [
    {
      data: [props.counts.POSITIVO, props.counts.NEGATIVO, props.counts.INCONCLUSIVO],
      backgroundColor: [
        sentimentMeta('POSITIVO').color,
        sentimentMeta('NEGATIVO').color,
        sentimentMeta('INCONCLUSIVO').color,
      ],
      borderWidth: 0,
    },
  ],
}))

const options: ChartOptions<'pie'> = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { position: 'right', labels: { boxWidth: 12, padding: 14 } },
    tooltip: {
      callbacks: {
        label: (ctx) => {
          const value = ctx.raw as number
          const total = (ctx.dataset.data as number[]).reduce((a, b) => a + b, 0)
          const pct = total ? Math.round((value / total) * 100) : 0
          return `${ctx.label}: ${value} (${pct}%)`
        },
      },
    },
  },
}
</script>

<template>
  <div class="fl-chart">
    <Pie :data="chartData" :options="options" />
  </div>
</template>

<style scoped>
.fl-chart {
  position: relative;
  height: 260px;
}
</style>
