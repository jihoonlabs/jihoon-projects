<script setup lang="ts">
import { ref } from 'vue';

import { AccountError, useAccountApi } from '~/features/auth/api/accountApi';
import AuthCard from '~/features/auth/components/AuthCard.vue';
import {
  hasErrors,
  validatePasswordResetRequest,
  type PasswordResetRequestErrors,
} from '~/features/auth/validation/accountValidation';
import FormMessage from '~/shared/components/FormMessage.vue';
import TextField from '~/shared/components/TextField.vue';

definePageMeta({ middleware: 'guest' });

const accountApi = useAccountApi();

const email = ref('');
const errors = ref<PasswordResetRequestErrors>({});
const serverError = ref('');
const successMessage = ref('');
const loading = ref(false);

// 入力を変えたら、前回の送信結果と入力エラーを消す
const onEmailChange = () => {
  serverError.value = '';
  successMessage.value = '';
  errors.value = {};
};

const submit = async () => {
  serverError.value = '';
  successMessage.value = '';

  const validationErrors = validatePasswordResetRequest(email.value);

  if (hasErrors(validationErrors)) {
    errors.value = validationErrors;
    return;
  }

  errors.value = {};
  loading.value = true;

  try {
    const response = await accountApi.requestPasswordReset(email.value);
    successMessage.value = response.message;
  } catch (error) {
    serverError.value =
      error instanceof AccountError
        ? error.message
        : 'パスワード再設定メールの送信中にエラーが発生しました。';
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <AuthCard
    title="パスワードをお忘れの方"
    description="登録したメールアドレスを入力してください。パスワード再設定用のリンクを送信します。"
  >
    <FormMessage v-if="successMessage" variant="success">
      {{ successMessage }}
    </FormMessage>
    <FormMessage v-if="serverError" variant="error">
      {{ serverError }}
    </FormMessage>

    <form :class="$style.form" novalidate @submit.prevent="submit">
      <TextField
        id="forgot-email"
        v-model="email"
        label="メールアドレス"
        type="email"
        autocomplete="email"
        placeholder="user@example.com"
        :error="errors.email"
        :disabled="loading"
        @update:model-value="onEmailChange"
      />
      <button type="submit" :class="$style.submit" :disabled="loading">
        {{ loading ? '送信中...' : '再設定メールを送信' }}
      </button>
    </form>

    <template #footer>
      <NuxtLink to="/login">ログイン画面に戻る</NuxtLink>
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
</style>
