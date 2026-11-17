import { describe, expect, it } from 'vitest';

import { getProjectBorderColor } from '../projectColor';

describe('プロジェクトの色', () => {
  it('サーバーの色をそのまま使い、名前やキーから色を作らないこと', () => {
    expect(getProjectBorderColor('#e3f2fd')).toBe('#e3f2fd');
    expect(getProjectBorderColor('#dff6f2')).not.toBe(
      getProjectBorderColor('#e3f2fd'),
    );
  });

  it.each([
    ['色がない', null],
    ['# がない', 'ABC'],
    ['空白だけ', '   '],
    ['短い 16 進数', '#fff'],
    ['CSS の式', 'url(example)'],
  ])('%s場合は中立（null）のままにすること', (_label, color) => {
    expect(getProjectBorderColor(color)).toBeNull();
  });
});
