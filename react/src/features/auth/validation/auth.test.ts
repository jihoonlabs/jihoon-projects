import { describe, expect, it } from 'vitest';

import { validateLoginForm } from './auth';

describe('validateLoginForm', () => {
  it('accepts a valid email and password', () => {
    expect(validateLoginForm('user@example.com', 'password123')).toEqual({});
  });

  it('requires an email and password', () => {
    expect(validateLoginForm('', '')).toEqual({
      email: 'メールアドレスを入力してください。',
      password: 'パスワードを入力してください。',
    });
  });

  it('rejects an invalid email format', () => {
    expect(validateLoginForm('invalid-email', 'password123')).toEqual({
      email: '有効なメールアドレス形式で入力してください。',
    });
  });

  it('rejects a password shorter than eight characters', () => {
    expect(validateLoginForm('user@example.com', 'pass123')).toEqual({
      password: 'パスワードは8文字以上で入力してください。',
    });
  });
});
