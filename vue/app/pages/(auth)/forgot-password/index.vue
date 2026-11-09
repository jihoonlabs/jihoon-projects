<script setup lang="ts">
import ForgotPasswordForm from '~/features/auth/components/ForgotPasswordForm/ForgotPasswordForm.vue';

definePageMeta({ middleware: 'guest' });
</script>

<template>
  <ForgotPasswordForm />
</template>
