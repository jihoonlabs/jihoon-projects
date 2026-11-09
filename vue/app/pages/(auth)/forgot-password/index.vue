<script setup lang="ts">
import ForgotPasswordForm from '~/features/auth/components/ForgotPasswordForm/ForgotPasswordForm.vue';

definePageMeta({ layout: 'auth', middleware: 'guest' });
</script>

<template>
  <ForgotPasswordForm />
</template>
