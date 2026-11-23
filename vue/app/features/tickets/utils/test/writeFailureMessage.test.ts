import { describe, expect, it } from 'vitest';

import { TicketApiError } from '../../api/apiErrors';
import { writeFailureMessage } from '../writeFailureMessage';

describe('書き込み失敗の文言', () => {
  it('API の文言は使わず、定数の文言に状態コードを添えること', () => {
    const error = new TicketApiError('internal detail', 500);

    expect(writeFailureMessage(error, '保存に失敗しました。')).toBe(
      '保存に失敗しました。 (500)',
    );
  });

  it('状態コードがなければ、文言だけを返すこと', () => {
    expect(
      writeFailureMessage(new TicketApiError('x'), '保存に失敗しました。'),
    ).toBe('保存に失敗しました。');
  });

  it('その他の例外は、内部のメッセージを出さず定数の文言にすること', () => {
    expect(
      writeFailureMessage(new Error('stack detail'), '削除に失敗しました。'),
    ).toBe('削除に失敗しました。');
  });
});
