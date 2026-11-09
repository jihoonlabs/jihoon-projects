<script setup lang="ts">
import type { SocialProvider } from '../../types/auth';
import { socialLoginUrl } from '../../utils/navigation';

/**
 * Google・LINE のログイン開始リンク。ログイン送信中は画面を離れないよう押せなくする
 */
const props = defineProps<{ disabled: boolean }>();

const apiUrl = useRuntimeConfig().public.apiUrl;
const href = (provider: SocialProvider) => socialLoginUrl(apiUrl, provider);

const preventWhileDisabled = (event: MouseEvent) => {
  if (props.disabled) {
    event.preventDefault();
  }
};
</script>

<template>
  <div :class="$style.alternative">その他のログイン方法</div>
  <div :class="$style.group">
    <a
      :href="href('google')"
      :class="$style.link"
      :aria-disabled="disabled || undefined"
      @click="preventWhileDisabled"
    >
      <img src="/auth/google-g.svg" width="20" height="20" alt="" />
      <span>Googleでログイン</span>
    </a>
    <a
      :href="href('line')"
      :class="$style.link"
      :aria-disabled="disabled || undefined"
      @click="preventWhileDisabled"
    >
      <img src="/auth/line-login.png" width="28" height="28" alt="" />
      <span>LINEでログイン</span>
    </a>
  </div>
</template>

<style module lang="scss">
.alternative {
  color: #64748b;
  font-size: 0.75rem;
  text-align: center;
}

.group {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.65rem;
}

.link {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  min-height: 44px;
  padding: 0.7rem 0.85rem;
  border: 1px solid #dce2eb;
  border-radius: 8px;
  background: #fff;
  color: #475569;
  font: inherit;
  font-size: 0.8rem;
  font-weight: 600;
  white-space: nowrap;
  cursor: pointer;

  &[aria-disabled='true'] {
    opacity: 0.55;
    cursor: wait;
  }
}
</style>
