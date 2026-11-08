<script setup lang="ts">
import { ref } from 'vue';

import { AccountError, useAccountApi } from '~/features/auth/api/accountApi';
import AuthCard from '~/features/auth/components/AuthCard.vue';
import {
  hasErrors,
  validateNewPassword,
  type NewPasswordErrors,
} from '~/features/auth/validation/accountValidation';
import FormMessage from '~/shared/components/FormMessage.vue';
import TextField from '~/shared/components/TextField.vue';

const route = useRoute();
const accountApi = useAccountApi();

// 同じ名前のパラメータが複数ある URL は、どちらが正しいか判断できないため不正なリンクとして扱う
const singleQuery = (key: string): string => {
  const value = route.query[key];

  return typeof value === 'string' ? value : '';
};

const email = singleQuery('email');
const token = singleQuery('token');
const linkIsInvalid = !email || !token;

const password = ref('');
const passwordConfirmation = ref('');
const showPassword = ref(false);
const errors = ref<NewPasswordErrors>({});
const serverError = ref('');
const successMessage = ref('');
const loading = ref(false);

const onPasswordChange = (value: string) => {
  serverError.value = '';

  // 確認欄と一致したら、確認欄の不一致エラーも一緒に消す
  errors.value = {
    password: undefined,
    passwordConfirmation:
      value === passwordConfirmation.value
        ? undefined
        : errors.value.passwordConfirmation,
  };
};

const onConfirmationChange = () => {
  serverError.value = '';
  errors.value = { ...errors.value, passwordConfirmation: undefined };
};

const submit = async () => {
  serverError.value = '';
  successMessage.value = '';

  const validationErrors = validateNewPassword(
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
    const response = await accountApi.resetPassword({
      email,
      token,
      password: password.value,
      passwordConfirmation: passwordConfirmation.value,
    });
    successMessage.value = response.message;
    password.value = '';
    passwordConfirmation.value = '';
  } catch (error) {
    serverError.value =
      error instanceof AccountError
        ? error.message
        : 'パスワードの再設定中にエラーが発生しました。';
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <AuthCard
    title="パスワード再設定"
    description="新しいパスワードを入力してください。"
  >
    <FormMessage v-if="linkIsInvalid" variant="error">
      再設定リンクが正しくありません。もう一度メールを送信してください。
    </FormMessage>
    <FormMessage v-if="successMessage" variant="success">
      {{ successMessage }}
    </FormMessage>
    <FormMessage v-if="serverError" variant="error">
      {{ serverError }}
    </FormMessage>

    <form
      v-if="!linkIsInvalid && !successMessage"
      :class="$style.form"
      novalidate
      @submit.prevent="submit"
    >
      <TextField
        id="reset-password"
        v-model="password"
        label="新しいパスワード"
        :type="showPassword ? 'text' : 'password'"
        autocomplete="new-password"
        placeholder="••••••••"
        :error="errors.password"
        :disabled="loading"
        @update:model-value="onPasswordChange"
      />
      <TextField
        id="reset-password-confirmation"
        v-model="passwordConfirmation"
        label="新しいパスワード（確認）"
        :type="showPassword ? 'text' : 'password'"
        autocomplete="new-password"
        placeholder="••••••••"
        :error="errors.passwordConfirmation"
        :disabled="loading"
        @update:model-value="onConfirmationChange"
      />
      <button
        type="button"
        :class="$style.toggle"
        :aria-pressed="showPassword"
        :disabled="loading"
        @click="showPassword = !showPassword"
      >
        {{ showPassword ? 'パスワードを隠す' : 'パスワードを表示' }}
      </button>
      <button type="submit" :class="$style.submit" :disabled="loading">
        {{ loading ? '再設定中...' : 'パスワードを再設定' }}
      </button>
    </form>

    <template #footer>
      <NuxtLink v-if="linkIsInvalid" to="/forgot-password">
        再設定メールをもう一度送信する
      </NuxtLink>
      <NuxtLink v-else to="/login">ログイン画面に戻る</NuxtLink>
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

.toggle {
  @include form.secondary-button;
}
</style>
