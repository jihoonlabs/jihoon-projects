<script setup lang="ts">
/**
 * 送信結果のメッセージ。失敗は alert として即座に、成功は status として読み上げる。
 */
defineProps<{ variant: 'error' | 'success' }>();
</script>

<template>
  <div
    :class="[$style.message, $style[variant]]"
    :role="variant === 'error' ? 'alert' : 'status'"
  >
    <slot />
  </div>
</template>

<style module lang="scss">
.message {
  padding: 0.75rem 0.9rem;
  border-radius: 8px;
  font-size: 0.85rem;
}

.error {
  background: #fef2f2;
  color: #b91c1c;
}

.success {
  background: #ecfdf3;
  color: #166534;
}
</style>
