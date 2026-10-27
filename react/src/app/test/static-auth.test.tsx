import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import LoginPage from '../(auth)/login/page';
import ResetPasswordPage from '../(auth)/reset-password/page';
import { useAuthStore } from '@/features/auth/store/useAuthStore';

const query = vi.hoisted(() => ({ value: '' }));
vi.mock('next/navigation', () => ({
  useSearchParams: () => new URLSearchParams(query.value),
  useRouter: () => ({ replace: vi.fn() }),
}));

describe('静的認証ページのクエリ引き継ぎ', () => {
  beforeEach(() => {
    useAuthStore.setState({
      user: null,
      isAuthenticated: false,
      isInitialized: true,
    });
  });
  it('メール確認の結果をログイン画面に表示する', () => {
    query.value = 'verified=1';
    render(<LoginPage />);
    expect(
      screen.getByText(
        'メールアドレスの認証が完了しました。ログインしてください。',
      ),
    ).toBeInTheDocument();
  });
  it('OAuth失敗の結果を保持する', () => {
    query.value = 'error=social_login_failed&provider=google';
    render(<LoginPage />);
    expect(screen.getByText('Google認証に失敗しました。')).toBeInTheDocument();
  });
  it('有効なresetリンクは入力フォームを表示する', () => {
    query.value = 'email=demo%40example.com&token=sample';
    render(<ResetPasswordPage />);
    expect(
      screen.getByRole('button', { name: 'パスワードを再設定' }),
    ).toBeInTheDocument();
  });
  it('重複したresetパラメータを受け入れない', () => {
    query.value = 'email=demo%40example.com&token=a&token=b';
    render(<ResetPasswordPage />);
    expect(screen.getByRole('alert')).toHaveTextContent(
      '再設定リンクが正しくありません',
    );
    expect(
      screen.queryByRole('button', { name: 'パスワードを再設定' }),
    ).not.toBeInTheDocument();
  });
});
