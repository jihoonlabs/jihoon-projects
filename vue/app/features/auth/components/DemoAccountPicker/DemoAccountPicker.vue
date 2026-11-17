<script setup lang="ts">
import {
  DEMO_ACCOUNTS,
  type DemoAccount,
} from '../../composables/useLoginForm';

/**
 * 公開デモのアカウント選択。選んだアカウントの認証情報をフォームに入れる
 */
defineProps<{ selectedEmail: string; disabled: boolean }>();

defineEmits<{ select: [account: DemoAccount] }>();
</script>

<template>
  <div :class="$style.accounts" role="group" aria-label="デモ用アカウント">
    <button
      type="button"
      :class="$style.account"
      :aria-pressed="selectedEmail === DEMO_ACCOUNTS.user.email"
      :disabled="disabled"
      @click="$emit('select', 'user')"
    >
      一般ユーザー
      <span>1プロジェクト</span>
    </button>
    <button
      type="button"
      :class="$style.account"
      :aria-pressed="selectedEmail === DEMO_ACCOUNTS.admin.email"
      :disabled="disabled"
      @click="$emit('select', 'admin')"
    >
      管理者
      <span>2プロジェクト</span>
    </button>
  </div>
</template>

<style module lang="scss">
.accounts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.6rem;
}

.account {
  display: grid;
  min-height: 52px;
  align-content: center;
  justify-items: center;
  gap: 0.15rem;
  border: 1px solid #dce2eb;
  border-radius: 8px;
  background: #fff;
  color: #475569;
  font: inherit;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;

  span {
    color: #64748b;
    font-size: 0.7rem;
    font-weight: 400;
  }

  &[aria-pressed='true'] {
    border-color: #295dcc;
    background: #eef4ff;
    color: #1d4ed8;
  }
}
</style>
