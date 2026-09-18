'use client';

import Link from 'next/link';
import { useState } from 'react';

import { requestPasswordResetApi } from '@/features/auth/api/requestPasswordReset';
import type { PasswordResetLinkValidationErrors } from '@/features/auth/types/auth';
import { validatePasswordResetLinkForm } from '@/features/auth/validation/auth';

import styles from './ForgotPasswordForm.module.css';

export function ForgotPasswordForm() {
  const [email, setEmail] = useState('');
  const [errors, setErrors] = useState<PasswordResetLinkValidationErrors>({});
  const [serverError, setServerError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    setServerError('');
    setSuccessMessage('');

    const validationErrors = validatePasswordResetLinkForm(email);

    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setErrors({});
    setLoading(true);

    try {
      const data = await requestPasswordResetApi({
        email,
      });

      setSuccessMessage(data.message);
    } catch (error) {
      if (error instanceof Error) {
        setServerError(error.message);
        return;
      }

      setServerError('パスワード再設定メールの送信中にエラーが発生しました。');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <h1>パスワードをお忘れの方</h1>
        <p>
          登録したメールアドレスを入力してください。
          パスワード再設定用のリンクを送信します。
        </p>

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

        <form onSubmit={handleSubmit} className={styles.form} noValidate>
          <div className={styles.inputGroup}>
            <label htmlFor="email">メールアドレス</label>

            <input
              id="email"
              type="email"
              autoComplete="email"
              placeholder="user@example.com"
              value={email}
              onChange={(event) => {
                setEmail(event.target.value);
                setServerError('');
                setSuccessMessage('');

                if (errors.email) {
                  setErrors((previousErrors) => ({
                    ...previousErrors,
                    email: undefined,
                  }));
                }
              }}
              aria-invalid={Boolean(errors.email)}
              aria-describedby={errors.email ? 'email-error' : undefined}
              required
              disabled={loading}
            />

            {errors.email && (
              <span id="email-error" className={styles.fieldError}>
                {errors.email}
              </span>
            )}
          </div>

          <button type="submit" className={styles.submitBtn} disabled={loading}>
            {loading ? '送信中...' : '再設定メールを送信'}
          </button>
        </form>

        <div className={styles.loginGuide}>
          <Link href="/login" className={styles.loginLink}>
            ログイン画面に戻る
          </Link>
        </div>
      </div>
    </div>
  );
}
