'use client';

import Link from 'next/link';
import { useState } from 'react';

import { resetPasswordApi } from '@/features/auth/api/resetPassword';
import type { PasswordResetValidationErrors } from '@/features/auth/types/auth';
import { validatePasswordResetForm } from '@/features/auth/validation/auth';

import styles from './ResetPasswordForm.module.css';

interface ResetPasswordFormProps {
  email: string;
  token: string;
}

export function ResetPasswordForm({ email, token }: ResetPasswordFormProps) {
  const [password, setPassword] = useState('');
  const [passwordConfirmation, setPasswordConfirmation] = useState('');
  const [errors, setErrors] = useState<PasswordResetValidationErrors>({});
  const [serverError, setServerError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const linkIsInvalid = !email || !token;

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    setServerError('');
    setSuccessMessage('');

    const validationErrors = validatePasswordResetForm(
      password,
      passwordConfirmation,
    );

    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setErrors({});
    setLoading(true);

    try {
      const data = await resetPasswordApi({
        email,
        token,
        password,
        passwordConfirmation,
      });

      setSuccessMessage(data.message);
      setPassword('');
      setPasswordConfirmation('');
    } catch (error) {
      if (error instanceof Error) {
        setServerError(error.message);
        return;
      }

      setServerError('パスワードの再設定中にエラーが発生しました。');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <h1>パスワード再設定</h1>
        <p>新しいパスワードを入力してください。</p>

        {linkIsInvalid && (
          <div className={styles.errorMessage} role="alert">
            再設定リンクが正しくありません。もう一度メールを送信してください。
          </div>
        )}

        {successMessage && (
          <div className={styles.successMessage} role="status">
            {successMessage}
          </div>
        )}

        {serverError && (
          <div className={styles.errorMessage} role="alert">
            {serverError}
          </div>
        )}

        {!linkIsInvalid && !successMessage && (
          <form onSubmit={handleSubmit} className={styles.form} noValidate>
            <div className={styles.inputGroup}>
              <label htmlFor="password">新しいパスワード</label>

              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="new-password"
                placeholder="••••••••"
                value={password}
                aria-invalid={Boolean(errors.password)}
                aria-describedby={
                  errors.password ? 'password-error' : undefined
                }
                onChange={(event) => {
                  const nextPassword = event.target.value;

                  setPassword(nextPassword);

                  if (serverError) {
                    setServerError('');
                  }

                  if (
                    errors.password ||
                    (errors.passwordConfirmation &&
                      nextPassword === passwordConfirmation)
                  ) {
                    setErrors((previousErrors) => ({
                      ...previousErrors,
                      password: undefined,
                      passwordConfirmation:
                        nextPassword === passwordConfirmation
                          ? undefined
                          : previousErrors.passwordConfirmation,
                    }));
                  }
                }}
                required
                disabled={loading}
              />

              {errors.password && (
                <span id="password-error" className={styles.fieldError}>
                  {errors.password}
                </span>
              )}
            </div>

            <div className={styles.inputGroup}>
              <label htmlFor="passwordConfirmation">
                新しいパスワード（確認）
              </label>

              <input
                id="passwordConfirmation"
                aria-invalid={Boolean(errors.passwordConfirmation)}
                aria-describedby={
                  errors.passwordConfirmation
                    ? 'password-confirmation-error'
                    : undefined
                }
                type={showPassword ? 'text' : 'password'}
                autoComplete="new-password"
                placeholder="••••••••"
                value={passwordConfirmation}
                onChange={(event) => {
                  setPasswordConfirmation(event.target.value);
                  if (serverError) {
                    setServerError('');
                  }
                  if (errors.passwordConfirmation) {
                    setErrors((previousErrors) => ({
                      ...previousErrors,
                      passwordConfirmation: undefined,
                    }));
                  }
                }}
                required
                disabled={loading}
              />

              {errors.passwordConfirmation && (
                <span
                  id="password-confirmation-error"
                  className={styles.fieldError}
                >
                  {errors.passwordConfirmation}
                </span>
              )}
            </div>

            <button
              type="button"
              className={styles.visibilityButton}
              onClick={() => setShowPassword((previous) => !previous)}
              disabled={loading}
            >
              {showPassword ? 'パスワードを隠す' : 'パスワードを表示'}
            </button>

            <button
              type="submit"
              className={styles.submitBtn}
              disabled={loading}
            >
              {loading ? '再設定中...' : 'パスワードを再設定'}
            </button>
          </form>
        )}

        <div className={styles.loginGuide}>
          {linkIsInvalid ? (
            <Link href="/forgot-password" className={styles.loginLink}>
              再設定メールをもう一度送信する
            </Link>
          ) : (
            <Link href="/login" className={styles.loginLink}>
              ログイン画面に戻る
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}
