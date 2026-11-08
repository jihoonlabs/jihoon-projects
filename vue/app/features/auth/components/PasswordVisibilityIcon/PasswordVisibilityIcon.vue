<script setup lang="ts">
defineProps<{ visible: boolean }>();
</script>

<template>
  <!-- 表示中は「隠す」操作を示す斜線付きの目、非表示中は目の形を出す -->
  <svg
    width="20"
    height="20"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12Z" />
    <circle cx="12" cy="12" r="3" />
    <path v-if="visible" d="m3 3 18 18" />
  </svg>
</template>
