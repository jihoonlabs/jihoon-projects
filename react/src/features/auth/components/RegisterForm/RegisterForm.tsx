'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { registerApi } from '@/features/auth/api/register';
import type { RegisterValidationErrors } from '@/features/auth/types/auth';
import { validateRegisterForm } from '@/features/auth/validation/auth';

import styles from './RegisterForm.module.css';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
const handleSocialLogin = (provider: 'google' | 'line') => {
  window.location.href = `${API_URL}/api/auth/${provider}/redirect`;
};

export function RegisterForm() {
  const router = useRouter();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirmation, setPasswordConfirmation] = useState('');
  const [errors, setErrors] = useState<RegisterValidationErrors>({});
  const [serverError, setServerError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setServerError('');

    const validationErrors = validateRegisterForm(
      name,
      email,
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
      await registerApi({
        name,
        email,
        password,
        passwordConfirmation,
      });

      router.push('/login?registered=1');
    } catch (error) {
      if (error instanceof Error) {
        setServerError(error.message);

        return;
      }

      setServerError('会員登録中にエラーが発生しました。');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <h1>会員登録</h1>
        <p>登録方法を選択してください。</p>

        {serverError && (
          <div className={styles.errorMessage} role="alert">
            {serverError}
          </div>
        )}

        <form onSubmit={handleSubmit} className={styles.form} noValidate>
          <div className={styles.inputGroup}>
            <label htmlFor="name">名前</label>
            <input
              id="name"
              type="text"
              autoComplete="name"
              value={name}
              aria-invalid={Boolean(errors.name)}
              aria-describedby={errors.name ? 'name-error' : undefined}
              onChange={(event) => {
                setName(event.target.value);

                if (errors.name) {
                  setErrors((previous) => ({
                    ...previous,
                    name: undefined,
                  }));
                }
              }}
              required
              disabled={loading}
            />
            {errors.name && (
              <span id="name-error" className={styles.fieldError}>
                {errors.name}
              </span>
            )}
          </div>

          <div className={styles.inputGroup}>
            <label htmlFor="email">メールアドレス</label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              placeholder="user@example.com"
              value={email}
              aria-invalid={Boolean(errors.email)}
              aria-describedby={errors.email ? 'email-error' : undefined}
              onChange={(event) => {
                setEmail(event.target.value);

                if (errors.email) {
                  setErrors((previous) => ({
                    ...previous,
                    email: undefined,
                  }));
                }
              }}
              required
              disabled={loading}
            />
            {errors.email && (
              <span id="email-error" className={styles.fieldError}>
                {errors.email}
              </span>
            )}
          </div>

          <div className={styles.inputGroup}>
            <label htmlFor="password">パスワード</label>
            <input
              id="password"
              type="password"
              autoComplete="new-password"
              placeholder="8文字以上の英字と数字"
              aria-invalid={Boolean(errors.password)}
              aria-describedby={errors.password ? 'password-error' : undefined}
              value={password}
              onChange={(event) => {
                setPassword(event.target.value);

                if (errors.password) {
                  setErrors((previous) => ({
                    ...previous,
                    password: undefined,
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
            <label htmlFor="passwordConfirmation">パスワード確認</label>
            <input
              id="passwordConfirmation"
              type="password"
              autoComplete="new-password"
              value={passwordConfirmation}
              aria-invalid={Boolean(errors.passwordConfirmation)}
              aria-describedby={
                errors.passwordConfirmation
                  ? 'password-confirmation-error'
                  : undefined
              }
              onChange={(event) => {
                setPasswordConfirmation(event.target.value);

                if (errors.passwordConfirmation) {
                  setErrors((previous) => ({
                    ...previous,
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

          <button type="submit" className={styles.submitBtn} disabled={loading}>
            {loading ? '登録中...' : 'メールアドレスで登録'}
          </button>

          <button
            type="button"
            onClick={() => handleSocialLogin('google')}
            disabled={loading}
          >
            Googleで続ける
          </button>

          <button
            type="button"
            onClick={() => handleSocialLogin('line')}
            disabled={loading}
          >
            LINEで続ける
          </button>
        </form>
        <div className={styles.loginGuide}>
          <span>すでにアカウントをお持ちの方は</span>
          <Link href="/login" className={styles.loginLink}>
            ログインへ
          </Link>
        </div>
      </div>
    </div>
  );
}
