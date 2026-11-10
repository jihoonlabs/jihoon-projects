<script setup lang="ts">
import RegisterForm from '~/features/auth/components/RegisterForm/RegisterForm.vue';
import { pageTitle } from '~/shared/utils/pageTitle';

definePageMeta({ layout: 'auth', middleware: 'guest' });
useHead({ title: pageTitle('会員登録') });
</script>

<template>
  <RegisterForm />
</template>
