const EMAIL_PATTERN = /\S+@\S+\.\S+/;

export interface RegistrationErrors {
  name?: string;
  email?: string;
  password?: string;
  passwordConfirmation?: string;
}

export interface PasswordResetRequestErrors {
  email?: string;
}

export interface NewPasswordErrors {
  password?: string;
  passwordConfirmation?: string;
}

/**
 * どれか 1 つでも項目にメッセージがあれば、送信を止める
 */
export const hasErrors = (errors: object): boolean =>
  Object.values(errors).some(Boolean);

const emailError = (email: string): string | undefined => {
  if (!email) return 'メールアドレスを入力してください。';
  if (!EMAIL_PATTERN.test(email)) {
    return '有効なメールアドレス形式で入力してください。';
  }

  return undefined;
};

// 新しいパスワードは登録・再設定で同じ規則（8文字以上・英字と数字を含む）
const newPasswordErrors = (
  password: string,
  passwordConfirmation: string,
): NewPasswordErrors => {
  const errors: NewPasswordErrors = {};

  if (!password) {
    errors.password = 'パスワードを入力してください。';
  } else if (password.length < 8) {
    errors.password = 'パスワードは8文字以上で入力してください。';
  } else if (!/[A-Za-z]/.test(password)) {
    errors.password = 'パスワードには英字を含めてください。';
  } else if (!/\d/.test(password)) {
    errors.password = 'パスワードには数字を含めてください。';
  }

  if (!passwordConfirmation) {
    errors.passwordConfirmation = '確認用のパスワードを入力してください。';
  } else if (password !== passwordConfirmation) {
    errors.passwordConfirmation = 'パスワードが一致しません。';
  }

  return errors;
};

export function validateRegistration(
  name: string,
  email: string,
  password: string,
  passwordConfirmation: string,
): RegistrationErrors {
  const errors: RegistrationErrors = {
    email: emailError(email),
    ...newPasswordErrors(password, passwordConfirmation),
  };

  if (!name.trim()) {
    errors.name = '名前を入力してください。';
  } else if (name.length > 255) {
    errors.name = '名前は255文字以内で入力してください。';
  }

  return errors;
}

export function validatePasswordResetRequest(
  email: string,
): PasswordResetRequestErrors {
  return { email: emailError(email) };
}

export function validateNewPassword(
  password: string,
  passwordConfirmation: string,
): NewPasswordErrors {
  return newPasswordErrors(password, passwordConfirmation);
}
