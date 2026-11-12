import { describe, expect, it } from 'vitest';

import { validatePasswordResetLinkForm } from '../auth';

describe('パスワード再設定メール送信フォームの入力検証', () => {
  it('正しいメールアドレスの場合、エラーがないこと', () => {
    expect(validatePasswordResetLinkForm('user@example.com')).toEqual({});
  });

  it('メールアドレスが必須であること', () => {
    expect(validatePasswordResetLinkForm('')).toEqual({
      email: 'メールアドレスを入力してください。',
    });
  });

  it('メールアドレスの形式が不正な場合、エラーになること', () => {
    expect(validatePasswordResetLinkForm('invalid-email')).toEqual({
      email: '有効なメールアドレス形式で入力してください。',
    });
  });
});
