<script setup lang="ts">
import { computed } from 'vue';

import type { NuxtError } from '#app';
import AuthCard from '~/features/auth/components/AuthCard/AuthCard.vue';
import { pageTitle } from '~/shared/utils/pageTitle';

const props = defineProps<{ error: NuxtError }>();

// 原因の詳細（メッセージ・スタック）は内部情報を含みうるため画面に出さず、状況の種類だけを伝える
const notFound = computed(() => props.error.statusCode === 404);
const heading = computed(() =>
  notFound.value ? 'ページが見つかりません' : 'エラーが発生しました',
);
const description = computed(() =>
  notFound.value
    ? 'URL が正しいかご確認ください。'
    : '時間をおいて、もう一度お試しください。',
);

useHead({ title: () => pageTitle(heading.value) });

// トップはログイン状態に応じてログイン画面か利用者のホームへ振り分ける
const backToTop = () => clearError({ redirect: '/' });
</script>

<template>
  <NuxtLayout name="auth">
    <AuthCard :title="heading" :description="description">
      <button type="button" :class="$style.back" @click="backToTop">
        トップへ戻る
      </button>
    </AuthCard>
  </NuxtLayout>
</template>

<style module lang="scss">
@use '~/assets/styles/form';

.back {
  @include form.primary-button;
}
</style>
