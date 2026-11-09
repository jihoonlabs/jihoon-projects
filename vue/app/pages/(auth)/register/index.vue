<script setup lang="ts">
import RegisterForm from '~/features/auth/components/RegisterForm/RegisterForm.vue';

definePageMeta({ layout: 'auth', middleware: 'guest' });
</script>

<template>
  <RegisterForm />
</template>
