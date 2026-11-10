<script setup lang="ts">
import TicketsPage from '~/features/tickets/components/TicketsPage/TicketsPage.vue';
import { pageTitle } from '~/shared/utils/pageTitle';

definePageMeta({ layout: 'dashboard', middleware: 'auth' });
useHead({ title: pageTitle('チケット管理') });
</script>

<template>
  <TicketsPage />
</template>
