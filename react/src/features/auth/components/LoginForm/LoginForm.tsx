'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

import { loginApi } from '@/features/auth/api/login';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import type { LoginValidationErrors } from '@/features/auth/types/auth';
import { validateLoginForm } from '@/features/auth/validation/auth';

import styles from './LoginForm.module.css';

export function LoginForm() {
  const router = useRouter();

  const login = useAuthStore((state) => state.login);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<LoginValidationErrors>({});
  const [serverError, setServerError] = useState('');

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    setServerError('');

    const validationErrors = validateLoginForm(email, password);

    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setErrors({});
    setLoading(true);

    try {
      const data = await loginApi({
        email,
        password,
      });

      login(data.user);

      router.push('/tickets');
    } catch (error) {
      if (error instanceof Error) {
        setServerError(error.message);
        return;
      }

      setServerError('ログイン中にエラーが発生しました。');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <h1>タスク管理</h1>
        <p>チケット管理</p>

        {serverError && (
          <div className={styles.errorMessage}>{serverError}</div>
        )}

        <form onSubmit={handleSubmit} className={styles.form} noValidate>
          <div className={styles.inputGroup}>
            <label htmlFor="email">メールアドレス</label>

            <input
              id="email"
              type="email"
              placeholder="user@example.com"
              value={email}
              onChange={(event) => {
                setEmail(event.target.value);

                if (errors.email) {
                  setErrors((prev) => ({
                    ...prev,
                    email: undefined,
                  }));
                }
              }}
              required
              disabled={loading}
            />

            {errors.email && (
              <span className={styles.fieldError}>{errors.email}</span>
            )}
          </div>

          <div className={styles.inputGroup}>
            <label htmlFor="password">パスワード</label>

            <input
              id="password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(event) => {
                setPassword(event.target.value);

                if (errors.password) {
                  setErrors((prev) => ({
                    ...prev,
                    password: undefined,
                  }));
                }
              }}
              required
              disabled={loading}
            />

            {errors.password && (
              <span className={styles.fieldError}>{errors.password}</span>
            )}
          </div>

          <button
            type="submit"
            className={styles.submitBtn}
            disabled={loading}
          >
            {loading ? 'ログイン中...' : 'ログイン'}
          </button>
        </form>
      </div>
    </div>
  );
}