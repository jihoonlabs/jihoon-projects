<script setup lang="ts">
import TicketsPage from '~/features/tickets/components/TicketsPage/TicketsPage.vue';

definePageMeta({ layout: 'dashboard', middleware: 'auth' });
</script>

<template>
  <TicketsPage />
</template>
