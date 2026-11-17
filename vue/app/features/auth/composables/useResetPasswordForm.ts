import { ref } from 'vue';

import { useRoute } from '#imports';
import { useApiClient } from '~/shared/api/apiClient';

import { AccountError } from '../api/accountRequest';
import { resetPassword } from '../api/resetPassword';
import {
  hasErrors,
  validateNewPassword,
  type NewPasswordErrors,
} from '../validation/auth';

// vue-router を直接の依存に加えず、Nuxt の useRoute から型を得る
type RouteQuery = ReturnType<typeof useRoute>['query'];

export interface ResetLink {
  email: string;
  token: string;
  isValid: boolean;
}

/**
 * メールの再設定リンクのクエリから、対象のメールアドレスとトークンを読み取る
 */
export function readResetLink(query: RouteQuery): ResetLink {
  // 同じ名前のパラメータが複数ある URL は、どちらが正しいか判断できないため不正なリンクとして扱う
  const single = (key: string): string => {
    const value = query[key];

    return typeof value === 'string' ? value : '';
  };

  const email = single('email');
  const token = single('token');

  return { email, token, isValid: email !== '' && token !== '' };
}

/**
 * 新しいパスワードを入力し直したときの入力エラー。
 * パスワード欄のエラーは消し、確認欄と一致したら確認欄の不一致エラーも一緒に消す。
 */
export function errorsAfterPasswordChange(
  errors: NewPasswordErrors,
  password: string,
  confirmation: string,
): NewPasswordErrors {
  return {
    password: undefined,
    passwordConfirmation:
      password === confirmation ? undefined : errors.passwordConfirmation,
  };
}

/**
 * メールの再設定リンクから開く、新しいパスワードの入力・検証・送信
 */
export function useResetPasswordForm() {
  const client = useApiClient();
  const link = readResetLink(useRoute().query);

  const password = ref('');
  const passwordConfirmation = ref('');
  const errors = ref<NewPasswordErrors>({});
  const serverError = ref('');
  const successMessage = ref('');
  const loading = ref(false);

  const onPasswordChange = (value: string) => {
    serverError.value = '';
    errors.value = errorsAfterPasswordChange(
      errors.value,
      value,
      passwordConfirmation.value,
    );
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
      const response = await resetPassword(client, {
        email: link.email,
        token: link.token,
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

  return {
    linkIsInvalid: !link.isValid,
    password,
    passwordConfirmation,
    errors,
    serverError,
    successMessage,
    loading,
    onPasswordChange,
    onConfirmationChange,
    submit,
  };
}
