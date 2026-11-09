import { describe, expect, it } from 'vitest';

import { loginNoticeMessages } from '../useLoginNotice';

describe('ログイン画面の通知文言', () => {
  it('通知がなければ何も表示しないこと', () => {
    expect(loginNoticeMessages({})).toEqual({ error: '', success: '' });
  });

  describe('ソーシャルログインの失敗', () => {
    it('Google なら提供元の名前を入れて伝えること', () => {
      expect(
        loginNoticeMessages({
          error: 'social_login_failed',
          provider: 'google',
        }),
      ).toEqual({ error: 'Google認証に失敗しました。', success: '' });
    });

    it('LINE なら提供元の名前を入れて伝えること', () => {
      expect(
        loginNoticeMessages({ error: 'social_login_failed', provider: 'line' }),
      ).toEqual({ error: 'LINE認証に失敗しました。', success: '' });
    });

    it('提供元が不明なら一般的な文言にすること', () => {
      expect(
        loginNoticeMessages({
          error: 'social_login_failed',
          provider: 'unknown',
        }),
      ).toEqual({ error: 'ソーシャルログインに失敗しました。', success: '' });
    });
  });

  it('利用できないアカウントであることを伝えること', () => {
    expect(loginNoticeMessages({ error: 'account_unavailable' })).toEqual({
      error: 'このアカウントは現在利用できません。',
      success: '',
    });
  });

  it('知らないエラーの種類は表示しないこと', () => {
    expect(loginNoticeMessages({ error: 'something_else' })).toEqual({
      error: '',
      success: '',
    });
  });

  it('メール認証の完了を伝えること', () => {
    expect(loginNoticeMessages({ verified: '1' })).toEqual({
      error: '',
      success: 'メールアドレスの認証が完了しました。ログインしてください。',
    });
  });

  it('会員登録後は認証メールの送信を伝えること', () => {
    expect(loginNoticeMessages({ registered: '1' })).toEqual({
      error: '',
      success: '認証メールを送信しました。メールをご確認ください。',
    });
  });

  it('認証完了と会員登録が両方あれば、認証完了を優先すること', () => {
    expect(
      loginNoticeMessages({ verified: '1', registered: '1' }).success,
    ).toBe('メールアドレスの認証が完了しました。ログインしてください。');
  });
});
