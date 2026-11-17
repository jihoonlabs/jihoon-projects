import { ref } from 'vue';

import { navigateTo } from '#imports';
import { useApiClient } from '~/shared/api/apiClient';

import { AccountError } from '../api/accountRequest';
import { register } from '../api/register';
import { LOGIN_PATH } from '../utils/navigation';
import {
  hasErrors,
  validateRegistration,
  type RegistrationErrors,
} from '../validation/auth';

/**
 * 会員登録フォームの入力・検証・送信。
 * 登録後はログイン画面へ移り、認証メールを送ったことをそこで伝える。
 */
export function useRegisterForm() {
  const client = useApiClient();

  const name = ref('');
  const email = ref('');
  const password = ref('');
  const passwordConfirmation = ref('');
  const errors = ref<RegistrationErrors>({});
  const serverError = ref('');
  const loading = ref(false);

  // 入力し直した項目のエラーだけを消す
  const clearError = (field: keyof RegistrationErrors) => {
    if (errors.value[field]) {
      errors.value = { ...errors.value, [field]: undefined };
    }
  };

  const submit = async () => {
    serverError.value = '';

    const validationErrors = validateRegistration(
      name.value,
      email.value,
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
      await register(client, {
        name: name.value,
        email: email.value,
        password: password.value,
        passwordConfirmation: passwordConfirmation.value,
      });
      await navigateTo({ path: LOGIN_PATH, query: { registered: '1' } });
    } catch (error) {
      serverError.value =
        error instanceof AccountError
          ? error.message
          : '会員登録中にエラーが発生しました。';
    } finally {
      loading.value = false;
    }
  };

  return {
    name,
    email,
    password,
    passwordConfirmation,
    errors,
    serverError,
    loading,
    clearError,
    submit,
  };
}
