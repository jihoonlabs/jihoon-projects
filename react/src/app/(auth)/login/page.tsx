'use client';

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/useAuthStore";
import { validateLoginForm } from "@/utils/validation/auth";
import styles from  './page.module.scss';
import { LoginValidationErrors, User } from "@/types";

export default function LoginPage() {
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
      await new Promise((resolve) => setTimeout(resolve, 600));

      const dummyUser: User = {
        id: 1,
        name: 'Test User',
        email,
        companyId: 101,
        companyName: 'Tech Corp',
        role: 'member',
        status: 'active',
        createdAt: new Date().toISOString(),
      };

      const dummyToken = 'mock-jwt-token-123456';

      login(dummyUser, dummyToken);
      router.push('/tickets');
    } catch (error) {
      if (error instanceof Error) {
          setServerError(error.message);
        } else {
          setServerError('ログイン中にエラーが発生しました。');
        }
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
              onChange={(e) => {
                setEmail(e.target.value);
                if (errors.email) setErrors((prev) => ({ ...prev, email: undefined }));
              }}
              required 
              disabled={loading}
            />
            {errors.email && <span className={styles.fieldError}>{errors.email}</span>}
          </div>

          <div className={styles.inputGroup}>
            <label htmlFor="password">パスワード</label>
            <input 
              id="password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                if (errors.password) setErrors((prev) => ({ ...prev, password: undefined }));
              }}
              disabled={loading}
              required 
            />
            {errors.password && <span className={styles.fieldError}>{errors.password}</span>}
          </div>

          <button type="submit" className={styles.submitBtn} disabled={loading}>
            {loading ? 'ログイン中...' : 'ログイン'}
          </button>
        </form>
      </div>
    </div>
  )
}