<script setup lang="ts">
import { ref } from 'vue';

import { useAuthApi } from '~/features/auth/api/authApi';
import { LOGIN_PATH } from '~/features/auth/navigation';
import { useAuthStore } from '~/features/auth/stores/authStore';

const auth = useAuthStore();
const authApi = useAuthApi();

const pending = ref(false);
const error = ref('');

const logout = async () => {
  if (pending.value) {
    return;
  }

  pending.value = true;
  error.value = '';

  try {
    await authApi.logout();
    auth.signOut();
    await navigateTo(LOGIN_PATH, { replace: true });
  } catch {
    // Laravel 側のセッションが残っている可能性があるため、画面の状態は変えない
    error.value = 'ログアウトできませんでした。もう一度お試しください。';
  } finally {
    pending.value = false;
  }
};
</script>

<template>
  <header :class="$style.header">
    <span :class="$style.brand">WORKSPACE</span>

    <div :class="$style.user">
      <span>
        ようこそ、<strong>{{ auth.user?.name }}</strong> さん（{{
          auth.user?.role === 'admin' ? '管理者' : '一般ユーザー'
        }}）
      </span>
      <button
        type="button"
        :class="$style.logout"
        :disabled="pending"
        @click="logout"
      >
        {{ pending ? 'ログアウト中...' : 'ログアウト' }}
      </button>
    </div>

    <p v-if="error" :class="$style.error" role="alert">{{ error }}</p>
  </header>
</template>

<style module lang="scss">
.header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.65rem;
  min-height: 4.25rem;
  padding: 0.8rem 1.5rem;
  background: #fff;
  color: #17243b;
  border-bottom: 1px solid #e4e8ef;
  color-scheme: light;
}

.brand {
  font-size: 1.1rem;
  font-weight: 650;
  letter-spacing: -0.02em;
}

.user {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.85rem;

  span {
    color: #64748b;
    font-size: 0.75rem;
  }
}

.logout {
  padding: 0.35rem 0.65rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  background: #fff;
  color: #64748b;
  font: inherit;
  font-size: 0.75rem;
  cursor: pointer;

  &:hover {
    background: #f8fafc;
    color: #b91c1c;
  }

  &:disabled {
    opacity: 0.5;
    cursor: wait;
  }
}

.error {
  flex-basis: 100%;
  color: #b91c1c;
}

@media (max-width: 600px) {
  .header {
    padding: 0.75rem 1rem;
  }
}
</style>
