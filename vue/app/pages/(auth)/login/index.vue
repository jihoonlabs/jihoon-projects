<script setup lang="ts">
import DemoNotice from '~/features/auth/components/DemoNotice/DemoNotice.vue';
import LoginForm from '~/features/auth/components/LoginForm/LoginForm.vue';

definePageMeta({ layout: 'auth', middleware: 'guest' });
</script>

<template>
  <div :class="$style.contents">
    <!-- ページの根は 1 要素にし、中身はレイアウトの並びにそのまま加える -->
    <DemoNotice />
    <LoginForm />
  </div>
</template>

<style module lang="scss">
.contents {
  display: contents;
}
</style>
