export interface LoginValidationErrors {
  email?: string;
  password?: string;
}

const EMAIL_PATTERN = /\S+@\S+\.\S+/;

/**
 * Next.js 版と同じ規則・文言でログイン入力を検証する
 */
export function validateLogin(
  email: string,
  password: string,
): LoginValidationErrors {
  const errors: LoginValidationErrors = {};

  if (!email) {
    errors.email = 'メールアドレスを入力してください。';
  } else if (!EMAIL_PATTERN.test(email)) {
    errors.email = '有効なメールアドレス形式で入力してください。';
  }

  if (!password) {
    errors.password = 'パスワードを入力してください。';
  } else if (password.length < 8) {
    errors.password = 'パスワードは8文字以上で入力してください。';
  }

  return errors;
}

export const hasValidationErrors = (errors: LoginValidationErrors) =>
  Boolean(errors.email || errors.password);
