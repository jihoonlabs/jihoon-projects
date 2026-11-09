<script setup lang="ts">
import AuthCard from '~/features/auth/components/AuthCard/AuthCard.vue';
import FormMessage from '~/shared/components/FormMessage/FormMessage.vue';
import TextInput from '~/shared/components/TextInput/TextInput.vue';

const {
  email,
  errors,
  serverError,
  successMessage,
  loading,
  onEmailChange,
  submit,
} = usePasswordResetRequest();
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
      <TextInput
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
