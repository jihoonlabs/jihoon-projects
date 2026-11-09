<script setup lang="ts">
import { computed, ref } from 'vue';

import DemoAccountPicker from '../DemoAccountPicker/DemoAccountPicker.vue';
import PasswordVisibilityIcon from '../PasswordVisibilityIcon/PasswordVisibilityIcon.vue';
import SocialLoginLinks from '../SocialLoginLinks/SocialLoginLinks.vue';

const props = withDefaults(
  defineProps<{
    /**
     * セッション期限切れ後の同じタブでの再ログイン。
     * 画面を離れると未保存の入力が失われるため、外部へ移る導線（ソーシャルログイン・会員登録など）を出さず、ログイン後も今の画面に留まる。
     */
    relogin?: boolean;
  }>(),
  { relogin: false },
);

const demoMode = useRuntimeConfig().public.demoMode === true;

// 再ログインの窓では、開いている画面のクエリを通知として読まない
const initialMessages = props.relogin
  ? { error: '', success: '' }
  : useLoginNotice();

const {
  email,
  password,
  errors,
  loading,
  serverError,
  successMessage,
  verification,
  selectDemoAccount,
  onEmailInput,
  onPasswordInput,
  submit,
} = useLoginForm({ relogin: props.relogin, initialMessages });

const {
  required: verificationRequired,
  resending: resendingVerification,
  resend: resendVerification,
} = verification;

const showPassword = ref(false);

// 公開デモでは新規登録・メール送信・ソーシャルログインを使えないため導線を出さない
const showExternalLinks = computed(() => !props.relogin && !demoMode);
</script>

<template>
  <div :class="$style.card">
    <div :class="$style.heading">
      <div :class="$style.identity">
        <span :class="$style.mark" aria-hidden="true">T</span>
        <span :class="$style.eyebrow">TICKET WORKSPACE</span>
      </div>
      <h1>タスク管理</h1>
      <p>チケット管理</p>
    </div>

    <div v-if="successMessage" :class="$style.success" role="status">
      {{ successMessage }}
    </div>

    <div v-if="serverError" :class="$style.error" role="alert">
      {{ serverError }}
    </div>

    <button
      v-if="verificationRequired"
      type="button"
      :class="$style.resend"
      :disabled="resendingVerification"
      @click="resendVerification"
    >
      {{
        resendingVerification ? '認証メールを再送中...' : '認証メールを再送する'
      }}
    </button>

    <form :class="$style.form" novalidate @submit.prevent="submit">
      <DemoAccountPicker
        v-if="demoMode"
        :selected-email="email"
        :disabled="loading"
        @select="selectDemoAccount"
      />

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

      <div v-if="showExternalLinks" :class="$style.forgot">
        <NuxtLink to="/forgot-password">パスワードをお忘れですか？</NuxtLink>
      </div>

      <button type="submit" :class="$style.submit" :disabled="loading">
        {{ loading ? 'ログイン中...' : 'ログイン' }}
      </button>

      <SocialLoginLinks v-if="showExternalLinks" :disabled="loading" />
    </form>

    <div v-if="showExternalLinks" :class="$style.register">
      <span>アカウントをお持ちでない方は</span>
      <NuxtLink to="/register">新規会員登録へ</NuxtLink>
    </div>
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

.resend {
  width: 100%;
  min-height: 44px;
  margin-bottom: 1rem;
  border: 1px solid $accent;
  border-radius: 8px;
  background: #fff;
  color: $accent;
  font: inherit;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;

  &:disabled {
    opacity: 0.55;
    cursor: wait;
  }
}

.forgot {
  text-align: right;
  font-size: 0.8rem;

  a {
    color: $accent;
  }
}

.register {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.35rem;
  margin-top: 1.25rem;
  color: $muted;
  font-size: 0.8rem;

  a {
    color: $accent;
    font-weight: 600;
  }
}

.fieldError {
  color: #b91c1c;
  font-size: 0.75rem;
}

.submit {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  min-height: 44px;
  padding: 0.7rem 0.85rem;
  border: 1px solid $accent;
  border-radius: 8px;
  background: $accent;
  color: #fff;
  font: inherit;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;

  &:hover {
    background: #224fac;
  }

  &:disabled {
    opacity: 0.55;
    cursor: wait;
  }
}
</style>
