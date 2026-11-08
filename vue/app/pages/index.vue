<script setup lang="ts">
import { LOGIN_PATH } from '~/features/auth/navigation';

// Next.js 版と同じく、トップはログイン画面へ移す（ログイン済みならログイン画面が最初の画面へ移す）
definePageMeta({
  middleware: () => navigateTo(LOGIN_PATH, { replace: true }),
});
</script>

<template>
  <NuxtLink to="/login">ログイン画面へ</NuxtLink>
</template>
