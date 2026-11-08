<script setup lang="ts">
import { computed, ref } from 'vue';

import { useRuntimeConfig } from '#imports';

import { LoginError, useAuthApi } from '../api/authApi';
import { socialLoginUrl } from '../navigation';
import { useAuthStore } from '../stores/authStore';
import type { LoginNotice, SocialProvider, User } from '../types';
import {
  hasValidationErrors,
  validateLogin,
  type LoginValidationErrors,
} from '../validation/loginValidation';

import PasswordVisibilityIcon from './PasswordVisibilityIcon.vue';

const props = withDefaults(
  defineProps<{
    notice?: LoginNotice;
    /** セッション期限切れ後の再ログインでは、ソーシャルログインを出さない */
    allowSocialLogin?: boolean;
  }>(),
  { notice: () => ({}), allowSocialLogin: true },
);

const emit = defineEmits<{ 'signed-in': [user: User] }>();

const DEMO_ACCOUNTS = {
  user: { email: 'demo@example.com', password: 'TicketDemo2026!' },
  admin: { email: 'demo-admin@example.com', password: 'TicketAdmin2026!' },
} as const;

type DemoAccount = keyof typeof DEMO_ACCOUNTS;

const config = useRuntimeConfig();
const demoMode = config.public.demoMode === true;
const authApi = useAuthApi();
const auth = useAuthStore();

const email = ref(demoMode ? DEMO_ACCOUNTS.user.email : '');
const password = ref(demoMode ? DEMO_ACCOUNTS.user.password : '');
const showPassword = ref(false);
const loading = ref(false);
const errors = ref<LoginValidationErrors>({});

const providerLabel = (provider?: string) => {
  if (provider === 'google') return 'Google';
  if (provider === 'line') return 'LINE';

  return null;
};

// 表示メッセージは画面を開いた時点のクエリだけで決める
const initialServerError = () => {
  if (props.notice.error === 'social_login_failed') {
    const label = providerLabel(props.notice.provider);

    return label
      ? `${label}認証に失敗しました。`
      : 'ソーシャルログインに失敗しました。';
  }

  if (props.notice.error === 'account_unavailable') {
    return 'このアカウントは現在利用できません。';
  }

  return '';
};

const initialSuccessMessage = () => {
  if (props.notice.verified === '1') {
    return 'メールアドレスの認証が完了しました。ログインしてください。';
  }

  if (props.notice.registered === '1') {
    return '認証メールを送信しました。メールをご確認ください。';
  }

  return '';
};

const serverError = ref(initialServerError());
const successMessage = ref(initialSuccessMessage());

const showSocialLogin = computed(() => props.allowSocialLogin && !demoMode);

const socialHref = (provider: SocialProvider) =>
  socialLoginUrl(config.public.apiUrl, provider);

const clearMessages = () => {
  serverError.value = '';
  successMessage.value = '';
};

const selectDemoAccount = (account: DemoAccount) => {
  email.value = DEMO_ACCOUNTS[account].email;
  password.value = DEMO_ACCOUNTS[account].password;
  errors.value = {};
  clearMessages();
};

const onEmailInput = () => {
  if (errors.value.email) {
    errors.value = { ...errors.value, email: undefined };
  }
};

const onPasswordInput = () => {
  if (errors.value.password) {
    errors.value = { ...errors.value, password: undefined };
  }
};

const preventWhileLoading = (event: MouseEvent) => {
  if (loading.value) {
    event.preventDefault();
  }
};

const submit = async () => {
  clearMessages();

  const validationErrors = validateLogin(email.value, password.value);

  if (hasValidationErrors(validationErrors)) {
    errors.value = validationErrors;
    return;
  }

  errors.value = {};
  loading.value = true;

  try {
    const user = await authApi.login({
      email: email.value,
      password: password.value,
    });

    auth.signIn(user);
    emit('signed-in', user);
  } catch (error) {
    serverError.value =
      error instanceof LoginError
        ? error.message
        : 'ログイン中にエラーが発生しました。';
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div :class="$style.card">
    <header :class="$style.heading">
      <div :class="$style.identity">
        <span :class="$style.mark" aria-hidden="true">T</span>
        <span :class="$style.eyebrow">TICKET WORKSPACE</span>
      </div>
      <h1>タスク管理</h1>
      <p>チケット管理</p>
    </header>

    <div v-if="successMessage" :class="$style.success" role="status">
      {{ successMessage }}
    </div>

    <div v-if="serverError" :class="$style.error" role="alert">
      {{ serverError }}
    </div>

    <form :class="$style.form" novalidate @submit.prevent="submit">
      <div
        v-if="demoMode"
        :class="$style.demoAccounts"
        role="group"
        aria-label="デモ用アカウント"
      >
        <button
          type="button"
          :class="$style.demoAccount"
          :aria-pressed="email === DEMO_ACCOUNTS.user.email"
          :disabled="loading"
          @click="selectDemoAccount('user')"
        >
          一般ユーザー
          <span>1プロジェクト</span>
        </button>
        <button
          type="button"
          :class="$style.demoAccount"
          :aria-pressed="email === DEMO_ACCOUNTS.admin.email"
          :disabled="loading"
          @click="selectDemoAccount('admin')"
        >
          管理者
          <span>2プロジェクト</span>
        </button>
      </div>

      <div :class="$style.field">
        <label for="login-email">メールアドレス</label>
        <input
          id="login-email"
          v-model="email"
          type="email"
          autocomplete="email"
          placeholder="user@example.com"
          :aria-invalid="Boolean(errors.email)"
          :aria-describedby="errors.email ? 'login-email-error' : undefined"
          :disabled="loading"
          required
          @input="onEmailInput"
        />
        <span
          v-if="errors.email"
          id="login-email-error"
          :class="$style.fieldError"
        >
          {{ errors.email }}
        </span>
      </div>

      <div :class="$style.field">
        <label for="login-password">パスワード</label>
        <div :class="$style.passwordField">
          <input
            id="login-password"
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            autocomplete="current-password"
            placeholder="••••••••"
            :aria-invalid="Boolean(errors.password)"
            :aria-describedby="
              errors.password ? 'login-password-error' : undefined
            "
            :disabled="loading"
            required
            @input="onPasswordInput"
          />
          <button
            type="button"
            :class="$style.passwordToggle"
            :aria-label="showPassword ? 'パスワードを隠す' : 'パスワードを表示'"
            :aria-pressed="showPassword"
            aria-controls="login-password"
            @click="showPassword = !showPassword"
          >
            <PasswordVisibilityIcon :visible="showPassword" />
          </button>
        </div>
        <span
          v-if="errors.password"
          id="login-password-error"
          :class="$style.fieldError"
        >
          {{ errors.password }}
        </span>
      </div>

      <button type="submit" :class="$style.submit" :disabled="loading">
        {{ loading ? 'ログイン中...' : 'ログイン' }}
      </button>

      <template v-if="showSocialLogin">
        <div :class="$style.alternative">その他のログイン方法</div>
        <div :class="$style.socialGroup">
          <a
            :href="socialHref('google')"
            :class="$style.social"
            :aria-disabled="loading || undefined"
            @click="preventWhileLoading"
          >
            <img src="/auth/google-g.svg" width="20" height="20" alt="" />
            <span>Googleでログイン</span>
          </a>
          <a
            :href="socialHref('line')"
            :class="$style.social"
            :aria-disabled="loading || undefined"
            @click="preventWhileLoading"
          >
            <img src="/auth/line-login.png" width="28" height="28" alt="" />
            <span>LINEでログイン</span>
          </a>
        </div>
      </template>
    </form>
  </div>
</template>

<style module lang="scss">
$border: #dce2eb;
$text: #17243b;
$muted: #64748b;
$accent: #295dcc;

.card {
  width: 100%;
  max-width: 440px;
  padding: 2rem;
  background: #fff;
  color: $text;
  border: 1px solid #e4e8ef;
  border-radius: 16px;
  box-shadow: 0 12px 36px rgb(23 36 59 / 6%);
  color-scheme: light;
}

.heading {
  margin-bottom: 1.75rem;

  h1 {
    margin-bottom: 0.35rem;
    font-size: 1.45rem;
    font-weight: 650;
  }

  p {
    color: $muted;
    font-size: 0.85rem;
  }
}

.identity {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  margin-bottom: 1.5rem;
}

.mark {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border: 1px solid #d6e3fa;
  border-radius: 9px;
  background: #eef4ff;
  color: $accent;
  font-weight: 700;
}

.eyebrow {
  color: $muted;
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.12em;
}

.success,
.error {
  margin-bottom: 1rem;
  padding: 0.75rem 0.9rem;
  border-radius: 8px;
  font-size: 0.85rem;
}

.success {
  background: #ecfdf3;
  color: #166534;
}

.error {
  background: #fef2f2;
  color: #b91c1c;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.demoAccounts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.6rem;
}

.demoAccount {
  display: grid;
  min-height: 52px;
  align-content: center;
  justify-items: center;
  gap: 0.15rem;
  border: 1px solid $border;
  border-radius: 8px;
  background: #fff;
  color: #475569;
  font: inherit;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;

  span {
    color: $muted;
    font-size: 0.7rem;
    font-weight: 400;
  }

  &[aria-pressed='true'] {
    border-color: $accent;
    background: #eef4ff;
    color: #1d4ed8;
  }
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;

  label {
    color: #475569;
    font-size: 0.8rem;
    font-weight: 600;
  }

  input {
    width: 100%;
    min-height: 44px;
    padding: 0.7rem 0.85rem;
    color: $text;
    background: #f8fafc;
    border: 1px solid $border;
    border-radius: 8px;
    font: inherit;
    font-size: 0.9rem;

    &:focus-visible {
      outline: 2px solid #3b6de0;
      outline-offset: 2px;
    }

    &[aria-invalid='true'] {
      border-color: #c66565;
    }
  }
}

.passwordField {
  position: relative;

  input {
    padding-right: 3.5rem;
  }
}

.passwordToggle {
  position: absolute;
  inset-block: 5px;
  right: 5px;
  display: grid;
  place-items: center;
  min-width: 36px;
  border: 0;
  border-radius: 5px;
  background: transparent;
  color: #475569;
  cursor: pointer;

  &:hover {
    background: #e9eef5;
  }
}

.fieldError {
  color: #b91c1c;
  font-size: 0.75rem;
}

.submit,
.social {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  min-height: 44px;
  padding: 0.7rem 0.85rem;
  border-radius: 8px;
  font: inherit;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
}

.submit {
  border: 1px solid $accent;
  background: $accent;
  color: #fff;

  &:hover {
    background: #224fac;
  }

  &:disabled {
    opacity: 0.55;
    cursor: wait;
  }
}

.alternative {
  color: $muted;
  font-size: 0.75rem;
  text-align: center;
}

.socialGroup {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.65rem;
}

.social {
  border: 1px solid $border;
  background: #fff;
  color: #475569;
  font-size: 0.8rem;
  white-space: nowrap;

  &[aria-disabled='true'] {
    opacity: 0.55;
    cursor: wait;
  }
}
</style>
