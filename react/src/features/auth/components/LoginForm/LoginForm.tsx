'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

import { LoginApiError, loginApi } from '@/features/auth/api/login';
import { resendVerificationEmailApi } from '@/features/auth/api/resendVerificationEmail';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import type {
  LoginRedirectParams,
  LoginValidationErrors,
} from '@/features/auth/types/auth';
import { validateLoginForm } from '@/features/auth/validation/auth';

import styles from './LoginForm.module.css';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export function LoginForm({
  error,
  provider,
  verified,
  registered,
}: LoginRedirectParams) {
  const router = useRouter();

  const login = useAuthStore((state) => state.login);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<LoginValidationErrors>({});
const [serverError, setServerError] = useState(() => {
  if (error === 'social_login_failed') {
    const providerName =
      provider === 'google' ? 'Google' : provider === 'line' ? 'LINE' : null;

    return providerName
      ? `${providerName}認証に失敗しました。`
      : 'ソーシャルログインに失敗しました。';
  }

  if (error === 'account_unavailable') {
    return 'このアカウントは現在利用できません。';
  }

  return '';
});

const [successMessage, setSuccessMessage] = useState(() => {
  if (verified === '1') {
    return 'メールアドレスの認証が完了しました。ログインしてください。';
  }

  if (registered === '1') {
    return '認証メールを送信しました。メールをご確認ください。';
  }

  return '';
});
  const [showPassword, setShowPassword] = useState(false);
  const [verificationEmailRequired, setVerificationEmailRequired] =
    useState(false);
  const [resendingVerificationEmail, setResendingVerificationEmail] =
    useState(false);

useEffect(() => {
  // 表示済みのクエリパラメータをURLから削除する
  if (window.location.search) {
    window.history.replaceState({}, '', '/login');
  }
}, []);

  const handleSocialLogin = (provider: 'google' | 'line') => {
    window.location.href = `${API_URL}/api/auth/${provider}/redirect`;
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    setServerError('');
    setSuccessMessage('');
    setVerificationEmailRequired(false);

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
      if (error instanceof LoginApiError) {
        setServerError(error.message);

        if (error.code === 'email_not_verified') {
          setVerificationEmailRequired(true);
        }

        return;
      }

      if (error instanceof Error) {
        setServerError(error.message);
        return;
      }

      setServerError('ログイン中にエラーが発生しました。');
    } finally {
      setLoading(false);
    }
  };

  const handleResendVerificationEmail = async () => {
    setServerError('');
    setSuccessMessage('');
    setResendingVerificationEmail(true);

    try {
      const data = await resendVerificationEmailApi({
        email,
      });

      setSuccessMessage(data.message);
      setVerificationEmailRequired(false);
    } catch (error) {
      if (error instanceof Error) {
        setServerError(error.message);
        return;
      }

      setServerError('認証メールの再送中にエラーが発生しました。');
    } finally {
      setResendingVerificationEmail(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <h1>タスク管理</h1>
        <p>チケット管理</p>

        {successMessage && (
          <div className={styles.successMessage} role="status">
            {successMessage}
          </div>
        )}

        {serverError && (
          <div className={styles.errorMessage}>{serverError}</div>
        )}

        {verificationEmailRequired && (
          <button
            type="button"
            className={styles.resendButton}
            onClick={handleResendVerificationEmail}
            disabled={resendingVerificationEmail}
          >
            {resendingVerificationEmail
              ? '認証メールを再送中...'
              : '認証メールを再送する'}
          </button>
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
                setVerificationEmailRequired(false);

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
              type={showPassword ? 'text' : 'password'}
              autoComplete="current-password"
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

            <button
              type="button"
              onClick={() => setShowPassword((prev) => !prev)}
              aria-label={
                showPassword ? 'パスワードを隠す' : 'パスワードを表示'
              }
            >
              {showPassword ? '隠す' : '表示'}
            </button>

            {errors.password && (
              <span className={styles.fieldError}>{errors.password}</span>
            )}
          </div>

          <div className={styles.forgotPasswordGuide}>
            <Link
              href="/forgot-password"
              className={styles.forgotPasswordLink}
            >
              パスワードをお忘れですか？
            </Link>
          </div>

          <button type="submit" className={styles.submitBtn} disabled={loading}>
            {loading ? 'ログイン中...' : 'ログイン'}
          </button>

          <button
            type="button"
            onClick={() => handleSocialLogin('google')}
            disabled={loading}
          >
            Googleでログイン
          </button>

          <button
            type="button"
            onClick={() => handleSocialLogin('line')}
            disabled={loading}
          >
            LINEでログイン
          </button>
        </form>

        <div className={styles.registerGuide}>
          <span>アカウントをお持ちでない方は</span>
          <Link href="/register" className={styles.registerLink}>
            新規会員登録へ
          </Link>
        </div>
      </div>
    </div>
  );
}
