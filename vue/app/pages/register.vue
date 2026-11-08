<script setup lang="ts">
import { ref } from 'vue';

import { AccountError, useAccountApi } from '~/features/auth/api/accountApi';
import AuthCard from '~/features/auth/components/AuthCard.vue';
import { socialLoginUrl } from '~/features/auth/navigation';
import type { SocialProvider } from '~/features/auth/types';
import {
  hasErrors,
  validateRegistration,
  type RegistrationErrors,
} from '~/features/auth/validation/accountValidation';
import FormMessage from '~/shared/components/FormMessage.vue';
import TextField from '~/shared/components/TextField.vue';

definePageMeta({ middleware: 'guest' });

const config = useRuntimeConfig();
const accountApi = useAccountApi();

const name = ref('');
const email = ref('');
const password = ref('');
const passwordConfirmation = ref('');
const errors = ref<RegistrationErrors>({});
const serverError = ref('');
const loading = ref(false);

// 入力し直した項目のエラーだけを消す
const clearError = (field: keyof RegistrationErrors) => {
  if (errors.value[field]) {
    errors.value = { ...errors.value, [field]: undefined };
  }
};

const socialHref = (provider: SocialProvider) =>
  socialLoginUrl(config.public.apiUrl, provider);

const preventWhileLoading = (event: MouseEvent) => {
  if (loading.value) {
    event.preventDefault();
  }
};

const submit = async () => {
  serverError.value = '';

  const validationErrors = validateRegistration(
    name.value,
    email.value,
    password.value,
    passwordConfirmation.value,
  );

  if (hasErrors(validationErrors)) {
    errors.value = validationErrors;
    return;
  }

  errors.value = {};
  loading.value = true;

  try {
    await accountApi.register({
      name: name.value,
      email: email.value,
      password: password.value,
      passwordConfirmation: passwordConfirmation.value,
    });
    // 認証メールを送ったことをログイン画面で伝える
    await navigateTo({ path: '/login', query: { registered: '1' } });
  } catch (error) {
    serverError.value =
      error instanceof AccountError
        ? error.message
        : '会員登録中にエラーが発生しました。';
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <AuthCard title="会員登録" description="登録方法を選択してください。">
    <FormMessage v-if="serverError" variant="error">
      {{ serverError }}
    </FormMessage>

    <form :class="$style.form" novalidate @submit.prevent="submit">
      <TextField
        id="register-name"
        v-model="name"
        label="名前"
        autocomplete="name"
        :error="errors.name"
        :disabled="loading"
        @update:model-value="clearError('name')"
      />
      <TextField
        id="register-email"
        v-model="email"
        label="メールアドレス"
        type="email"
        autocomplete="email"
        placeholder="user@example.com"
        :error="errors.email"
        :disabled="loading"
        @update:model-value="clearError('email')"
      />
      <TextField
        id="register-password"
        v-model="password"
        label="パスワード"
        type="password"
        autocomplete="new-password"
        placeholder="8文字以上の英字と数字"
        :error="errors.password"
        :disabled="loading"
        @update:model-value="clearError('password')"
      />
      <TextField
        id="register-password-confirmation"
        v-model="passwordConfirmation"
        label="パスワード確認"
        type="password"
        autocomplete="new-password"
        :error="errors.passwordConfirmation"
        :disabled="loading"
        @update:model-value="clearError('passwordConfirmation')"
      />

      <button type="submit" :class="$style.submit" :disabled="loading">
        {{ loading ? '登録中...' : 'メールアドレスで登録' }}
      </button>

      <a
        :href="socialHref('google')"
        :class="$style.social"
        :aria-disabled="loading || undefined"
        @click="preventWhileLoading"
      >
        Googleで続ける
      </a>
      <a
        :href="socialHref('line')"
        :class="$style.social"
        :aria-disabled="loading || undefined"
        @click="preventWhileLoading"
      >
        LINEで続ける
      </a>
    </form>

    <template #footer>
      すでにアカウントをお持ちの方は
      <NuxtLink to="/login">ログインへ</NuxtLink>
    </template>
  </AuthCard>
</template>

<style module lang="scss">
@use '~/assets/styles/form';

.form {
  @include form.form;
}

.submit {
  @include form.primary-button;
}

.social {
  @include form.secondary-button;
}
</style>
