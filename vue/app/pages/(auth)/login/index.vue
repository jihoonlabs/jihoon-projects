<script setup lang="ts">
import LoginPage from '~/features/auth/components/LoginPage/LoginPage.vue';

definePageMeta({ middleware: 'guest' });
</script>

<template>
  <LoginPage />
</template>
