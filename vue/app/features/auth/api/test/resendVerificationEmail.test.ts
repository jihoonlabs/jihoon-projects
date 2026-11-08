import { describe, expect, it } from 'vitest';

import { useApiClient } from '~/shared/api/apiClient';
import { accountApi } from '~/test/mocks/auth/accountApiHandlers';
import { overrideApi } from '~/test/mocks/overrideApi';

import { resendVerificationEmail } from '../resendVerificationEmail';

describe('認証メールの再送 API', () => {
  it('前後の空白を除いたメールアドレスを送ること', async () => {
    const received: { body?: unknown } = {};
    overrideApi(
      accountApi.records(
        '/api/auth/email/verification-notification',
        received,
      ),
    );

    await resendVerificationEmail(useApiClient(), ' user@example.com ');

    expect(received.body).toEqual({ email: 'user@example.com' });
  });

  it('中断したときは利用者向けの文言に変えず、中断として伝えること', async () => {
    overrideApi(
      accountApi.succeeds(
        '/api/auth/email/verification-notification',
        '送信しました。',
      ),
    );
    const controller = new AbortController();
    controller.abort();

    await expect(
      resendVerificationEmail(useApiClient(), 
        'user@example.com',
        controller.signal,
      ),
    ).rejects.toMatchObject({ name: 'AbortError' });
  });

  it('試行回数の上限（429）では再送回数が多いことを伝えること', async () => {
    overrideApi(
      accountApi.fails('/api/auth/email/verification-notification', 429),
    );

    await expect(
      resendVerificationEmail(useApiClient(), 'user@example.com'),
    ).rejects.toThrow(
      '認証メールの再送回数が多すぎます。しばらくしてから再度お試しください。',
    );
  });
});
