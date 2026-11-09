import { ref } from 'vue';

import { useApiClient } from '~/shared/api/apiClient';

import { AccountError } from '../api/accountRequest';
import { requestPasswordReset } from '../api/requestPasswordReset';
import {
  hasErrors,
  validatePasswordResetRequest,
  type PasswordResetRequestErrors,
} from '../validation/auth';

/**
 * パスワード再設定メールの送信フォーム
 */
export function usePasswordResetRequest() {
  const client = useApiClient();

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
      const response = await requestPasswordReset(client, email.value);
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

  return {
    email,
    errors,
    serverError,
    successMessage,
    loading,
    onEmailChange,
    submit,
  };
}
