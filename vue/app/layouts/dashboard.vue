<script setup lang="ts">
import { computed } from 'vue';

import LoginForm from '~/features/auth/components/LoginForm.vue';
import { useAuthStore } from '~/features/auth/stores/authStore';
import AppHeader from '~/shared/components/AppHeader.vue';

const auth = useAuthStore();

// 別のアカウントで再ログインしたら、前の利用者の画面状態を作り直す
const userKey = computed(() => auth.user?.id ?? 'guest');
</script>

<template>
  <div :class="$style.layout">
    <section
      v-if="auth.sessionExpired"
      :class="$style.relogin"
      aria-label="再ログイン"
    >
      <p role="alert">
        セッションの有効期限が切れました。再ログインしてください。未保存の入力はこのタブ内で同じアカウントに再ログインした場合のみ保持されます。再読み込み・画面移動で失われます。
      </p>
      <LoginForm :allow-social-login="false" />
    </section>

    <!-- 期限切れの間は操作できないよう隠し、入力中の内容は同じアカウントの再ログインまで保持する -->
    <div
      :key="userKey"
      :class="$style.application"
      :hidden="auth.sessionExpired"
      :inert="auth.sessionExpired"
    >
      <AppHeader v-if="!auth.sessionExpired" />
      <main :class="$style.main">
        <slot />
      </main>
    </div>
  </div>
</template>

<style module lang="scss">
.layout {
  display: flex;
  flex: 1;
  flex-direction: column;
}

.relogin {
  display: grid;
  justify-items: center;
  gap: 1rem;
  padding: 2rem 1.25rem;
  background: #f3f5f9;
  color: #17243b;

  p {
    max-width: 440px;
    font-size: 0.85rem;
  }
}

.application {
  min-height: 100vh;
  background: #fff;
  color: #17243b;
}

.main {
  min-width: 0;
  padding: 1.5rem;
}
</style>
