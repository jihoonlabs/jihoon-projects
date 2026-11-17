<script setup lang="ts">
import ForgotPasswordForm from '~/features/auth/components/ForgotPasswordForm/ForgotPasswordForm.vue';
import { pageTitle } from '~/shared/utils/pageTitle';

definePageMeta({ layout: 'auth', middleware: 'guest' });
useHead({ title: pageTitle('パスワードをお忘れの方') });
</script>

<template>
  <ForgotPasswordForm />
</template>
