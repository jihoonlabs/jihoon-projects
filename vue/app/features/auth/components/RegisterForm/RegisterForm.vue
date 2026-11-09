<script setup lang="ts">
import AuthCard from '~/features/auth/components/AuthCard/AuthCard.vue';
import type { SocialProvider } from '~/features/auth/types/auth';
import { socialLoginUrl } from '~/features/auth/utils/navigation';
import FormMessage from '~/shared/components/FormMessage/FormMessage.vue';
import TextInput from '~/shared/components/TextInput/TextInput.vue';

const {
  name,
  email,
  password,
  passwordConfirmation,
  errors,
  serverError,
  loading,
  clearError,
  submit,
} = useRegisterForm();

const apiUrl = useRuntimeConfig().public.apiUrl;
const socialHref = (provider: SocialProvider) =>
  socialLoginUrl(apiUrl, provider);

// 登録の送信中は画面を離れないよう、ソーシャルログインへのリンクを押せなくする
const preventWhileLoading = (event: MouseEvent) => {
  if (loading.value) {
    event.preventDefault();
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
