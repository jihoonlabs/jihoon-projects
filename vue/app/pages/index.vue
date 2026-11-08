<script setup lang="ts">
import { LOGIN_PATH, useHomePath } from '~/features/auth/utils/navigation';
import { useAuthStore } from '~/features/auth/store/useAuthStore';

// トップは状態に応じて振り分ける（Next.js 版はログイン画面を経由するが、ここでは一度の遷移で済ませる）
definePageMeta({
  middleware: () =>
    navigateTo(useAuthStore().isAuthenticated ? useHomePath() : LOGIN_PATH, {
      replace: true,
    }),
});
</script>

<template>
  <NuxtLink to="/login">ログイン画面へ</NuxtLink>
</template>
