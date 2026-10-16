<script setup lang="ts">
import { computed } from 'vue'
import { Bar } from 'vue-chartjs'
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  LinearScale,
  Tooltip,
  type ChartOptions,
} from 'chart.js'

import type { FeatureStat } from '@/types/api'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip)

const props = defineProps<{ features: FeatureStat[] }>()

const top = computed(() => props.features.slice(0, 5))

const chartData = computed(() => ({
  labels: top.value.map((f) => f.code),
  datasets: [
    {
      label: 'Solicitações',
      data: top.value.map((f) => f.count),
      backgroundColor: '#2ba6b5',
      borderRadius: 4,
    },
  ],
}))

const options: ChartOptions<'bar'> = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
}
</script>

<template>
  <div class="fl-chart">
    <Bar :data="chartData" :options="options" />
  </div>
</template>

<style scoped>
.fl-chart {
  position: relative;
  height: 260px;
}
</style>
