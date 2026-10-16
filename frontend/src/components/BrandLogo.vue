<script setup lang="ts">
withDefaults(defineProps<{ size?: number }>(), { size: 32 })
</script>

<template>
  <!-- A lente que recolhe o feixe disperso de feedbacks e o põe em foco. -->
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 48 48"
    role="img"
    aria-label="FeedLens"
    fill="none"
  >
    <circle cx="24" cy="24" r="19" fill="none" stroke="currentColor" stroke-width="3" />
    <path
      d="M2 14 L30 24 M2 24 L30 24 M2 34 L30 24"
      stroke="currentColor"
      stroke-width="2"
      stroke-linecap="round"
      opacity="0.5"
    />
    <circle cx="31" cy="24" r="4.5" fill="var(--fl-amber)" />
  </svg>
</template>
