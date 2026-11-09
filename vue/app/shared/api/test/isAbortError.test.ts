import { describe, expect, it } from 'vitest';

import { isAbortError } from '../isAbortError';

describe('中断の判定', () => {
  it('DOMException の AbortError を中断と判定すること', () => {
    expect(isAbortError(new DOMException('中断', 'AbortError'))).toBe(true);
  });

  it('name が AbortError の Error も中断と判定すること', () => {
    const error = new Error('中断');
    error.name = 'AbortError';

    expect(isAbortError(error)).toBe(true);
  });

  it('ほかの DOMException は中断と判定しないこと', () => {
    expect(isAbortError(new DOMException('失敗', 'NetworkError'))).toBe(false);
  });

  it('通常のエラーや値は中断と判定しないこと', () => {
    expect(isAbortError(new TypeError('Failed to fetch'))).toBe(false);
    expect(isAbortError(null)).toBe(false);
    expect(isAbortError('AbortError')).toBe(false);
  });
});
