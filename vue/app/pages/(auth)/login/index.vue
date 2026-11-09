<script setup lang="ts">
import DemoNotice from '~/features/auth/components/DemoNotice/DemoNotice.vue';
import LoginForm from '~/features/auth/components/LoginForm/LoginForm.vue';

definePageMeta({ layout: 'auth', middleware: 'guest' });
</script>

<template>
  <DemoNotice />
  <LoginForm />
</template>
