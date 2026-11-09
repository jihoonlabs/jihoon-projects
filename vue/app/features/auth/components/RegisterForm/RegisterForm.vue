<script setup lang="ts">
import { ref } from 'vue';

import { AccountError } from '~/features/auth/api/accountRequest';
import AuthCard from '~/features/auth/components/AuthCard/AuthCard.vue';
import { register } from '~/features/auth/api/register';
import type { SocialProvider } from '~/features/auth/types/auth';
import { socialLoginUrl } from '~/features/auth/utils/navigation';
import {
  hasErrors,
  validateRegistration,
  type RegistrationErrors,
} from '~/features/auth/validation/auth';
import FormMessage from '~/shared/components/FormMessage/FormMessage.vue';
import TextInput from '~/shared/components/TextInput/TextInput.vue';
import { useApiClient } from '~/shared/api/apiClient';

const config = useRuntimeConfig();
const client = useApiClient();

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
    await register(client, {
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
      <TextInput
        id="register-name"
        v-model="name"
        label="名前"
        autocomplete="name"
        :error="errors.name"
        :disabled="loading"
        @update:model-value="clearError('name')"
      />
      <TextInput
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
      <TextInput
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
      <TextInput
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
