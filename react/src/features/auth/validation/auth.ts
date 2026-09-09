import { LoginValidationErrors } from '@/features/auth/types/auth';

export const validateLoginForm = (email: string, password: string): LoginValidationErrors => {
  const errors: LoginValidationErrors = {};

  if (!email) {
    errors.email = 'メールアドレスを入力してください。';
  } else if (!/\S+@\S+\.\S+/.test(email)) {
    errors.email = '有効なメールアドレス形式で入力してください。';
  }

  if (!password) {
    errors.password = 'パスワードを入力してください。';
  } else if (password.length < 8) {
    errors.password = 'パスワードは8文字以上で入力してください。';
  }

  return errors;
};