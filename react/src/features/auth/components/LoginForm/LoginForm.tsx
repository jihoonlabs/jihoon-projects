'use client';

import Link from 'next/link';
import Image from 'next/image';
import { Eye, EyeOff } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

import { useAuthStore } from '@/features/auth/store/useAuthStore';
import type { LoginRedirectParams } from '@/features/auth/types/auth';

import styles from './LoginForm.module.css';
import { useLoginSubmit } from './useLoginSubmit';
import { useVerificationResend } from './useVerificationResend';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
const DEMO_ACCOUNTS = {
  user: { email: 'demo@example.com', password: 'TicketDemo2026!' },
  admin: { email: 'demo-admin@example.com', password: 'TicketAdmin2026!' },
};

export function LoginForm({
  error,
  provider,
  verified,
  registered,
}: LoginRedirectParams) {
  const router = useRouter();
  const DEMO_MODE = process.env.NEXT_PUBLIC_DEMO_MODE === 'true';

  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const isInitialized = useAuthStore((state) => state.isInitialized);

  useEffect(() => {
    // 履歴移動やセッション復元でも、認証済みのログイン画面を残さない。
    if (isInitialized && isAuthenticated)
      router.replace(DEMO_MODE ? '/tickets' : '/attendance');
  }, [isInitialized, isAuthenticated, router, DEMO_MODE]);

  const [email, setEmail] = useState(() =>
    DEMO_MODE ? 'demo@example.com' : '',
  );
  const [password, setPassword] = useState(() =>
    DEMO_MODE ? 'TicketDemo2026!' : '',
  );
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
  const { isResending, cancelResend, resend } = useVerificationResend({
    onStart: () => {
      setServerError('');
      setSuccessMessage('');
    },
    onSuccess: (message) => {
      setSuccessMessage(message);
      setVerificationEmailRequired(false);
    },
    onError: setServerError,
  });

  const { loading, errors, clearError, resetErrors, submit } = useLoginSubmit({
    onStart: () => {
      cancelResend();
      setServerError('');
      setSuccessMessage('');
      setVerificationEmailRequired(false);
    },
    onError: (message, requiresVerification) => {
      setServerError(message);
      if (requiresVerification) setVerificationEmailRequired(true);
    },
  });

  const selectDemoAccount = (account: keyof typeof DEMO_ACCOUNTS) => {
    cancelResend();
    setEmail(DEMO_ACCOUNTS[account].email);
    setPassword(DEMO_ACCOUNTS[account].password);
    resetErrors();
    setServerError('');
    setSuccessMessage('');
    setVerificationEmailRequired(false);
  };

  useEffect(() => {
    // 表示済みのクエリパラメータをURLから削除する
    if (window.location.search) {
      window.history.replaceState({}, '', '/login');
    }
  }, []);

  const handleSocialLogin = (socialProvider: 'google' | 'line') => {
    window.location.href = `${API_URL}/api/auth/${socialProvider}/redirect`;
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    void submit(email, password);
  };

  if (!isInitialized || isAuthenticated) {
    return <p role="status">認証情報を確認中...</p>;
  }

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <header className={styles.heading}>
          <div className={styles.identity}>
            <span className={styles.mark} aria-hidden="true">
              T
            </span>
            <span className={styles.eyebrow}>TICKET WORKSPACE</span>
          </div>
          <h1>タスク管理</h1>
          <p>チケット管理</p>
        </header>

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

        {verificationEmailRequired && (
          <button
            type="button"
            className={styles.resendButton}
            onClick={() => void resend(email)}
            disabled={isResending}
          >
            {isResending ? '認証メールを再送中...' : '認証メールを再送する'}
          </button>
        )}

        <form onSubmit={handleSubmit} className={styles.form} noValidate>
          {DEMO_MODE && (
            <div
              className={styles.demoAccountChoices}
              role="group"
              aria-label="デモ用アカウント"
            >
              <button
                type="button"
                className={styles.demoAccountButton}
                aria-pressed={email === DEMO_ACCOUNTS.user.email}
                disabled={loading}
                onClick={() => selectDemoAccount('user')}
              >
                一般ユーザー
                <span>1プロジェクト</span>
              </button>
              <button
                type="button"
                className={styles.demoAccountButton}
                aria-pressed={email === DEMO_ACCOUNTS.admin.email}
                disabled={loading}
                onClick={() => selectDemoAccount('admin')}
              >
                管理者
                <span>2プロジェクト</span>
              </button>
            </div>
          )}

          <div className={styles.inputGroup}>
            <label htmlFor="email">メールアドレス</label>

            <input
              id="email"
              type="email"
              autoComplete="email"
              placeholder="user@example.com"
              aria-invalid={Boolean(errors.email)}
              aria-describedby={errors.email ? 'email-error' : undefined}
              value={email}
              onChange={(event) => {
                cancelResend();
                setEmail(event.target.value);
                setVerificationEmailRequired(false);

                clearError('email');
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

            <div className={styles.passwordField}>
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                placeholder="••••••••"
                aria-invalid={Boolean(errors.password)}
                aria-describedby={
                  errors.password ? 'password-error' : undefined
                }
                value={password}
                onChange={(event) => {
                  setPassword(event.target.value);

                  clearError('password');
                }}
                required
                disabled={loading}
              />

              <button
                type="button"
                className={styles.passwordToggle}
                onClick={() => setShowPassword((prev) => !prev)}
                aria-label={
                  showPassword ? 'パスワードを隠す' : 'パスワードを表示'
                }
                aria-pressed={showPassword}
                aria-controls="password"
              >
                {showPassword ? (
                  <EyeOff size={20} aria-hidden="true" />
                ) : (
                  <Eye size={20} aria-hidden="true" />
                )}
              </button>
            </div>

            {errors.password && (
              <span id="password-error" className={styles.fieldError}>
                {errors.password}
              </span>
            )}
          </div>

          {!DEMO_MODE && (
            <div className={styles.forgotPasswordGuide}>
              <Link
                href="/forgot-password"
                className={styles.forgotPasswordLink}
              >
                パスワードをお忘れですか？
              </Link>
            </div>
          )}

          <button type="submit" className={styles.submitBtn} disabled={loading}>
            {loading ? 'ログイン中...' : 'ログイン'}
          </button>

          {!DEMO_MODE && (
            <>
              <div className={styles.alternativeLabel}>
                その他のログイン方法
              </div>
              <div className={styles.socialGroup}>
                <button
                  type="button"
                  className={`${styles.socialButton} ${styles.googleButton}`}
                  onClick={() => handleSocialLogin('google')}
                  disabled={loading}
                >
                  <Image
                    src="/auth/google-g.svg"
                    width={20}
                    height={20}
                    alt=""
                    aria-hidden="true"
                  />
                  <span>Googleでログイン</span>
                </button>

                <button
                  type="button"
                  className={`${styles.socialButton} ${styles.lineButton}`}
                  onClick={() => handleSocialLogin('line')}
                  disabled={loading}
                >
                  <Image
                    src="/auth/line-login.png"
                    width={28}
                    height={28}
                    alt=""
                    aria-hidden="true"
                    unoptimized
                  />
                  <span>LINEでログイン</span>
                </button>
              </div>
            </>
          )}
        </form>

        {!DEMO_MODE && (
          <div className={styles.registerGuide}>
            <span>アカウントをお持ちでない方は</span>
            <Link href="/register" className={styles.registerLink}>
              新規会員登録へ
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
