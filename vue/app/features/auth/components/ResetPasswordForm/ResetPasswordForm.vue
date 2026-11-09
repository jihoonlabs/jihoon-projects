<script setup lang="ts">
import { ref } from 'vue';

import AuthCard from '~/features/auth/components/AuthCard/AuthCard.vue';
import FormMessage from '~/shared/components/FormMessage/FormMessage.vue';
import TextInput from '~/shared/components/TextInput/TextInput.vue';

const {
  linkIsInvalid,
  password,
  passwordConfirmation,
  errors,
  serverError,
  successMessage,
  loading,
  onPasswordChange,
  onConfirmationChange,
  submit,
} = useResetPasswordForm();

const showPassword = ref(false);
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
      <TextInput
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
      <TextInput
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
