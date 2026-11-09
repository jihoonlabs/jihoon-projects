<script setup lang="ts">
/**
 * 認証まわりの画面（会員登録・パスワード再設定）で共通のカード
 */
defineProps<{ title: string; description: string }>();
</script>

<template>
  <div :class="$style.card">
    <h1 :class="$style.title">{{ title }}</h1>
    <p :class="$style.description">{{ description }}</p>
    <div :class="$style.body">
      <slot />
    </div>
    <div v-if="$slots.footer" :class="$style.footer">
      <slot name="footer" />
    </div>
  </div>
</template>

<style module lang="scss">
.card {
  width: 100%;
  max-width: 440px;
  padding: 2rem;
  background: #fff;
  border: 1px solid #e4e8ef;
  border-radius: 16px;
  box-shadow: 0 12px 36px rgb(23 36 59 / 6%);
}

.title {
  margin-bottom: 0.35rem;
  font-size: 1.45rem;
  font-weight: 650;
}

.description {
  margin-bottom: 1.5rem;
  color: #64748b;
  font-size: 0.85rem;
}

.body {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.footer {
  margin-top: 1.25rem;
  color: #64748b;
  font-size: 0.8rem;
  text-align: center;

  a {
    color: #295dcc;
    font-weight: 600;
  }
}
</style>
