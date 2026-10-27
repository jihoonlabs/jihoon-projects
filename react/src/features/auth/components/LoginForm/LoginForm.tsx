'use client';

import Link from 'next/link';
import Image from 'next/image';
import { Eye, EyeOff } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';

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
  const DEMO_MODE = process.env.NEXT_PUBLIC_DEMO_MODE === 'true';

  const login = useAuthStore((state) => state.login);
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
  const verificationRevision = useRef(0);
  const verificationRequest = useRef<AbortController | null>(null);

  // 古い再送応答のSet-Cookieで新しいログインを取り消さない。
  const cancelVerificationRequest = () => {
    verificationRequest.current?.abort();
    verificationRequest.current = null;
    setResendingVerificationEmail(false);
  };

  useEffect(() => () => verificationRequest.current?.abort(), []);

  useEffect(() => {
    // 表示済みのクエリパラメータをURLから削除する
    if (window.location.search) {
      window.history.replaceState({}, '', '/login');
    }
  }, []);

  const handleSocialLogin = (socialProvider: 'google' | 'line') => {
    window.location.href = `${API_URL}/api/auth/${socialProvider}/redirect`;
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    cancelVerificationRequest();
    verificationRevision.current += 1;

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
    cancelVerificationRequest();
    const controller = new AbortController();
    verificationRequest.current = controller;
    const revision = verificationRevision.current;
    setServerError('');
    setSuccessMessage('');
    setResendingVerificationEmail(true);

    try {
      const data = await resendVerificationEmailApi(
        { email },
        controller.signal,
      );

      // 入力変更・新しいログイン後に、古い再送応答を表示へ反映しない。
      if (revision !== verificationRevision.current) return;
      setSuccessMessage(data.message);
      setVerificationEmailRequired(false);
    } catch (error) {
      if (revision !== verificationRevision.current) return;
      if (error instanceof Error) {
        setServerError(error.message);
        return;
      }

      setServerError('認証メールの再送中にエラーが発生しました。');
    } finally {
      if (verificationRequest.current === controller) {
        verificationRequest.current = null;
        setResendingVerificationEmail(false);
      }
    }
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
              aria-invalid={Boolean(errors.email)}
              aria-describedby={errors.email ? 'email-error' : undefined}
              value={email}
              onChange={(event) => {
                cancelVerificationRequest();
                verificationRevision.current += 1;
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
