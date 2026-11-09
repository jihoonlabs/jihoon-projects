import { describe, expect, it } from 'vitest';

import {
  errorsAfterPasswordChange,
  readResetLink,
} from '../useResetPasswordForm';

describe('パスワード再設定の規則', () => {
  describe('再設定リンクの読み取り', () => {
    it('メールアドレスとトークンがそろえば正しいリンクとして読み取ること', () => {
      expect(
        readResetLink({ email: 'user@example.com', token: 'reset-token' }),
      ).toEqual({
        email: 'user@example.com',
        token: 'reset-token',
        isValid: true,
      });
    });

    it('トークンがなければ正しくないリンクとすること', () => {
      expect(readResetLink({ email: 'user@example.com' })).toEqual({
        email: 'user@example.com',
        token: '',
        isValid: false,
      });
    });

    it('メールアドレスが空文字なら正しくないリンクとすること', () => {
      expect(readResetLink({ email: '', token: 'reset-token' })).toEqual({
        email: '',
        token: 'reset-token',
        isValid: false,
      });
    });

    it('同じ名前のパラメータが複数あれば、その値を使わず正しくないリンクとすること', () => {
      expect(
        readResetLink({
          email: ['a@example.com', 'b@example.com'],
          token: 'reset-token',
        }),
      ).toEqual({ email: '', token: 'reset-token', isValid: false });
    });
  });

  describe('パスワードを入力し直したときの入力エラー', () => {
    it('パスワード欄のエラーを消すこと', () => {
      expect(
        errorsAfterPasswordChange(
          { password: 'パスワードを入力してください。' },
          'abc12345',
          '',
        ),
      ).toEqual({ password: undefined, passwordConfirmation: undefined });
    });

    it('確認欄と一致したら、確認欄の不一致エラーも消すこと', () => {
      expect(
        errorsAfterPasswordChange(
          { passwordConfirmation: 'パスワードが一致しません。' },
          'abc12345',
          'abc12345',
        ),
      ).toEqual({ password: undefined, passwordConfirmation: undefined });
    });

    it('確認欄と一致しなければ、確認欄のエラーを残すこと', () => {
      expect(
        errorsAfterPasswordChange(
          { passwordConfirmation: 'パスワードが一致しません。' },
          'abc12345',
          'abc1234',
        ),
      ).toEqual({
        password: undefined,
        passwordConfirmation: 'パスワードが一致しません。',
      });
    });
  });
});
