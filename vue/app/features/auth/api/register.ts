import type { ApiClient } from '~/shared/api/apiClient';

import type { Registration } from '../types/auth';

import { sendAccountRequest } from './accountRequest';

export function register(client: ApiClient, registration: Registration) {
  return sendAccountRequest(
    client,
    '/api/auth/register',
    {
      name: registration.name.trim(),
      email: registration.email.trim(),
      password: registration.password,
      password_confirmation: registration.passwordConfirmation,
    },
    {
      fields: ['email', 'password', 'name'],
      invalid: '入力内容を確認してください。',
      tooMany: '登録試行回数が多すぎます。しばらくしてから再度お試しください。',
      fallback: '会員登録処理に失敗しました。',
    },
  );
}
