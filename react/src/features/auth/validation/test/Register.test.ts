import { describe, expect, it } from 'vitest';

import { validateRegisterForm } from '../auth';

describe('validateRegisterForm', () => {
  it('正しい入力内容の場合、エラーがないこと', () => {
    expect(
      validateRegisterForm(
        'テストユーザー',
        'user@example.com',
        'password123',
        'password123',
      ),
    ).toEqual({});
  });

  it('すべての入力項目が必須であること', () => {
    expect(validateRegisterForm('', '', '', '')).toEqual({
      name: '名前を入力してください。',
      email: 'メールアドレスを入力してください。',
      password: 'パスワードを入力してください。',
      passwordConfirmation: '確認用のパスワードを入力してください。',
    });
  });

  it('パスワードが8文字未満の場合、エラーになること', () => {
    expect(
      validateRegisterForm(
        'テストユーザー',
        'user@example.com',
        'pass1',
        'pass1',
      ),
    ).toEqual({
      password: 'パスワードは8文字以上で入力してください。',
    });
  });

  it('パスワードに英字が含まれない場合、エラーになること', () => {
    expect(
      validateRegisterForm(
        'テストユーザー',
        'user@example.com',
        '12345678',
        '12345678',
      ),
    ).toEqual({
      password: 'パスワードには英字を含めてください。',
    });
  });

  it('パスワードに数字が含まれない場合、エラーになること', () => {
    expect(
      validateRegisterForm(
        'テストユーザー',
        'user@example.com',
        'password',
        'password',
      ),
    ).toEqual({
      password: 'パスワードには数字を含めてください。',
    });
  });

  it('確認用パスワードが一致しない場合、エラーになること', () => {
    expect(
      validateRegisterForm(
        'テストユーザー',
        'user@example.com',
        'password123',
        'different123',
      ),
    ).toEqual({
      passwordConfirmation: 'パスワードが一致しません。',
    });
  });
});
