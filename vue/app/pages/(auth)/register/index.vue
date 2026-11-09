<script setup lang="ts">
import RegisterForm from '~/features/auth/components/RegisterForm/RegisterForm.vue';

definePageMeta({ middleware: 'guest' });
</script>

<template>
  <RegisterForm />
</template>
