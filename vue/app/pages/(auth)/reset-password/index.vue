<script setup lang="ts">
import ResetPasswordForm from '~/features/auth/components/ResetPasswordForm/ResetPasswordForm.vue';
import { pageTitle } from '~/shared/utils/pageTitle';

// 再設定リンクはログイン状態に関係なく開けるようにする（Next.js 版と同じ）
definePageMeta({ layout: 'auth' });
useHead({ title: pageTitle('パスワード再設定') });
</script>

<template>
  <ResetPasswordForm />
</template>
