import { describe, expect, it } from 'vitest';

import { hasValidationErrors, validateLogin } from '../loginValidation';

describe('ログイン入力の検証', () => {
  describe('メールアドレス', () => {
    it('未入力ならメールアドレスの入力を求めること', () => {
      expect(validateLogin('', 'password123').email).toBe(
        'メールアドレスを入力してください。',
      );
    });

    it('形式が正しくなければ形式の誤りを伝えること', () => {
      expect(validateLogin('user@example', 'password123').email).toBe(
        '有効なメールアドレス形式で入力してください。',
      );
    });
  });

  describe('パスワード', () => {
    it('未入力ならパスワードの入力を求めること', () => {
      expect(validateLogin('user@example.com', '').password).toBe(
        'パスワードを入力してください。',
      );
    });

    it('7文字ならエラーにすること', () => {
      expect(validateLogin('user@example.com', '1234567').password).toBe(
        'パスワードは8文字以上で入力してください。',
      );
    });

    it('8文字ならエラーにしないこと', () => {
      expect(validateLogin('user@example.com', '12345678').password).toBe(
        undefined,
      );
    });
  });

  describe('全体', () => {
    it('正しい入力ならエラーなしとして扱うこと', () => {
      expect(
        hasValidationErrors(validateLogin('user@example.com', 'password123')),
      ).toBe(false);
    });

    it('どちらかの項目にエラーがあればエラーありとして扱うこと', () => {
      expect(hasValidationErrors(validateLogin('', 'password123'))).toBe(true);
    });
  });
});
