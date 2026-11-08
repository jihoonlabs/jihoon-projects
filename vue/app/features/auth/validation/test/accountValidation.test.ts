import { describe, expect, it } from 'vitest';

import {
  hasErrors,
  validateNewPassword,
  validatePasswordResetRequest,
  validateRegistration,
} from '../auth';

describe('アカウント入力の検証', () => {
  describe('会員登録', () => {
    it('すべて正しければエラーなしとして扱うこと', () => {
      expect(
        hasErrors(
          validateRegistration(
            '山田 花子',
            'hanako@example.com',
            'password123',
            'password123',
          ),
        ),
      ).toBe(false);
    });

    it('空白だけの名前は未入力として扱うこと', () => {
      expect(
        validateRegistration('   ', 'a@example.com', 'password1', 'password1')
          .name,
      ).toBe('名前を入力してください。');
    });

    it('256文字の名前は長すぎるとして扱うこと', () => {
      expect(
        validateRegistration(
          'あ'.repeat(256),
          'a@example.com',
          'password1',
          'password1',
        ).name,
      ).toBe('名前は255文字以内で入力してください。');
    });

    it('255文字の名前は受け付けること', () => {
      expect(
        validateRegistration(
          'あ'.repeat(255),
          'a@example.com',
          'password1',
          'password1',
        ).name,
      ).toBeUndefined();
    });

    it('形式が正しくないメールアドレスはエラーにすること', () => {
      expect(
        validateRegistration('a', 'not-an-email', 'password1', 'password1')
          .email,
      ).toBe('有効なメールアドレス形式で入力してください。');
    });
  });

  describe('新しいパスワード', () => {
    it('未入力ならパスワードと確認用の両方の入力を求めること', () => {
      expect(validateNewPassword('', '')).toEqual({
        password: 'パスワードを入力してください。',
        passwordConfirmation: '確認用のパスワードを入力してください。',
      });
    });

    it('7文字ならエラーにすること', () => {
      expect(validateNewPassword('abc1234', 'abc1234').password).toBe(
        'パスワードは8文字以上で入力してください。',
      );
    });

    it('数字だけなら英字を含めるよう求めること', () => {
      expect(validateNewPassword('12345678', '12345678').password).toBe(
        'パスワードには英字を含めてください。',
      );
    });

    it('英字だけなら数字を含めるよう求めること', () => {
      expect(validateNewPassword('abcdefgh', 'abcdefgh').password).toBe(
        'パスワードには数字を含めてください。',
      );
    });

    it('確認用が一致しなければ不一致を伝えること', () => {
      expect(
        validateNewPassword('password123', 'password124').passwordConfirmation,
      ).toBe('パスワードが一致しません。');
    });

    it('8文字で英字と数字を含み、確認用が一致すればエラーなしとすること', () => {
      expect(hasErrors(validateNewPassword('abcdefg1', 'abcdefg1'))).toBe(
        false,
      );
    });
  });

  describe('パスワード再設定メール', () => {
    it('未入力ならメールアドレスの入力を求めること', () => {
      expect(validatePasswordResetRequest('').email).toBe(
        'メールアドレスを入力してください。',
      );
    });

    it('正しいメールアドレスならエラーなしとすること', () => {
      expect(hasErrors(validatePasswordResetRequest('a@example.com'))).toBe(
        false,
      );
    });
  });
});
