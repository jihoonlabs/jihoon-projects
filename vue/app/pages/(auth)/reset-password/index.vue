<script setup lang="ts">
import ResetPasswordForm from '~/features/auth/components/ResetPasswordForm/ResetPasswordForm.vue';

// 再設定リンクはログイン状態に関係なく開けるようにする（Next.js 版と同じ）
definePageMeta({ layout: 'auth' });
</script>

<template>
  <ResetPasswordForm />
</template>
