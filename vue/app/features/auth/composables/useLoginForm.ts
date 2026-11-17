import { ref } from 'vue';

import { navigateTo, useRuntimeConfig } from '#imports';
import { useApiClient } from '~/shared/api/apiClient';

import { login, LoginError } from '../api/login';
import { useAuthStore } from '../store/useAuthStore';
import type { FormMessages, LoginNoticeMessages } from '../types/auth';
import { useHomePath } from '../utils/navigation';
import {
  hasErrors,
  validateLogin,
  type LoginValidationErrors,
} from '../validation/auth';
import { useVerificationResend } from './useVerificationResend';

export const DEMO_ACCOUNTS = {
  user: { email: 'demo@example.com', password: 'TicketDemo2026!' },
  admin: { email: 'demo-admin@example.com', password: 'TicketAdmin2026!' },
} as const;

export type DemoAccount = keyof typeof DEMO_ACCOUNTS;

/**
 * ログインフォームの入力・検証・送信。
 * 通常のログイン画面ではログイン後にホームへ移り、再ログインの窓では今の画面に留まる。
 */
export function useLoginForm(options: {
  relogin: boolean;
  initialMessages: LoginNoticeMessages;
}) {
  const demoMode = useRuntimeConfig().public.demoMode === true;
  const client = useApiClient();
  const auth = useAuthStore();
  const homePath = useHomePath();

  const email = ref(demoMode ? DEMO_ACCOUNTS.user.email : '');
  const password = ref(demoMode ? DEMO_ACCOUNTS.user.password : '');
  const errors = ref<LoginValidationErrors>({});
  const loading = ref(false);

  const messages: FormMessages = {
    error: ref(options.initialMessages.error),
    success: ref(options.initialMessages.success),
    clear: () => {
      messages.error.value = '';
      messages.success.value = '';
    },
  };

  const verification = useVerificationResend(email, messages);

  const selectDemoAccount = (account: DemoAccount) => {
    verification.reset();
    email.value = DEMO_ACCOUNTS[account].email;
    password.value = DEMO_ACCOUNTS[account].password;
    errors.value = {};
    messages.clear();
  };

  const onEmailInput = () => {
    // 別のメールアドレスに対する再送を続けない
    verification.reset();

    if (errors.value.email) {
      errors.value = { ...errors.value, email: undefined };
    }
  };

  const onPasswordInput = () => {
    if (errors.value.password) {
      errors.value = { ...errors.value, password: undefined };
    }
  };

  const submit = async () => {
    verification.reset();
    messages.clear();

    const validationErrors = validateLogin(email.value, password.value);

    if (hasErrors(validationErrors)) {
      errors.value = validationErrors;
      return;
    }

    errors.value = {};
    loading.value = true;

    try {
      const user = await login(client, {
        email: email.value,
        password: password.value,
      });

      auth.signIn(user);

      if (!options.relogin) {
        await navigateTo(homePath, { replace: true });
      }
    } catch (error) {
      messages.error.value =
        error instanceof LoginError
          ? error.message
          : 'ログイン中にエラーが発生しました。';
      verification.required.value =
        error instanceof LoginError && error.reason === 'email_not_verified';
    } finally {
      loading.value = false;
    }
  };

  return {
    email,
    password,
    errors,
    loading,
    serverError: messages.error,
    successMessage: messages.success,
    verification,
    selectDemoAccount,
    onEmailInput,
    onPasswordInput,
    submit,
  };
}
