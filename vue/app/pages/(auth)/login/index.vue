<script setup lang="ts">
import { onMounted } from 'vue';

import LoginForm from '~/features/auth/components/LoginForm/LoginForm.vue';
import { LOGIN_PATH, useHomePath } from '~/features/auth/utils/navigation';
import type { LoginNotice } from '~/features/auth/types/auth';

definePageMeta({ middleware: 'guest' });

const route = useRoute();
const router = useRouter();
const demoMode = useRuntimeConfig().public.demoMode === true;
const homePath = useHomePath();

const queryValue = (key: string) => {
  const value = route.query[key];

  return typeof value === 'string' ? value : undefined;
};

const notice: LoginNotice = {
  error: queryValue('error'),
  provider: queryValue('provider'),
  verified: queryValue('verified'),
  registered: queryValue('registered'),
};

onMounted(() => {
  // 表示し終えた結果をアドレスバーから消し、再読み込みで同じ通知を出さない
  if (Object.keys(route.query).length > 0) {
    void router.replace({ path: LOGIN_PATH });
  }
});

const goHome = () => navigateTo(homePath, { replace: true });
</script>

<template>
  <div :class="$style.page">
    <aside v-if="demoMode" :class="$style.demo">
      <strong>公開デモ</strong>
      <p>
        一般ユーザーと管理者を選んで、プロジェクトの表示範囲を比べられます。
      </p>
      <p>
        データは全員で共有する架空データです。個人情報は入力しないでください。
      </p>
      <p>新規登録・メール送信・Google/LINE認証はデモでは利用できません。</p>
    </aside>
    <LoginForm :notice="notice" @signed-in="goHome" />
  </div>
</template>

<style module lang="scss">
.page {
  display: grid;
  flex: 1;
  place-items: center;
  align-content: center;
  gap: 1rem;
  min-height: 100vh;
  min-height: 100svh;
  padding: 2rem 1.25rem;
  background: #f3f5f9;
  color: #17243b;
}

.demo {
  max-width: 440px;
  font-size: 0.85rem;
  text-align: center;
}
</style>
