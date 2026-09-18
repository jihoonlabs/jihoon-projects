import { describe, expect, it } from 'vitest';

import { validateLoginForm } from '../auth';

describe('validateLoginForm', () => {
  it('正しいメールアドレスとパスワードの場合、エラーがないこと', () => {
    expect(validateLoginForm('user@example.com', 'password123')).toEqual({});
  });

  it('メールアドレスとパスワードが必須であること', () => {
    expect(validateLoginForm('', '')).toEqual({
      email: 'メールアドレスを入力してください。',
      password: 'パスワードを入力してください。',
    });
  });

  it('メールアドレスの形式が不正な場合、エラーになること', () => {
    expect(validateLoginForm('invalid-email', 'password123')).toEqual({
      email: '有効なメールアドレス形式で入力してください。',
    });
  });

  it('パスワードが8文字未満の場合、エラーになること', () => {
    expect(validateLoginForm('user@example.com', 'pass123')).toEqual({
      password: 'パスワードは8文字以上で入力してください。',
    });
  });
});
