import type {
  LoginValidationErrors,
  PasswordResetLinkValidationErrors,
  PasswordResetValidationErrors,
  RegisterValidationErrors,
} from '@/features/auth/types/auth';

export const validateLoginForm = (
  email: string,
  password: string,
): LoginValidationErrors => {
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

export const validateRegisterForm = (
  name: string,
  email: string,
  password: string,
  passwordConfirmation: string,
): RegisterValidationErrors => {
  const errors: RegisterValidationErrors = {};

  if (!name.trim()) {
    errors.name = '名前を入力してください。';
  } else if (name.length > 255) {
    errors.name = '名前は255文字以内で入力してください。';
  }

  if (!email) {
    errors.email = 'メールアドレスを入力してください。';
  } else if (!/\S+@\S+\.\S+/.test(email)) {
    errors.email = '有効なメールアドレス形式で入力してください。';
  }

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

export const validatePasswordResetLinkForm = (
  email: string,
): PasswordResetLinkValidationErrors => {
  const errors: PasswordResetLinkValidationErrors = {};

  if (!email) {
    errors.email = 'メールアドレスを入力してください。';
  } else if (!/\S+@\S+\.\S+/.test(email)) {
    errors.email = '有効なメールアドレス形式で入力してください。';
  }

  return errors;
};

export const validatePasswordResetForm = (
  password: string,
  passwordConfirmation: string,
): PasswordResetValidationErrors => {
  const errors: PasswordResetValidationErrors = {};

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
    errors.passwordConfirmation =
      '確認用のパスワードを入力してください。';
  } else if (password !== passwordConfirmation) {
    errors.passwordConfirmation = 'パスワードが一致しません。';
  }

  return errors;
};