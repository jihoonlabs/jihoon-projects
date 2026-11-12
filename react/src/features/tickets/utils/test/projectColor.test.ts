import { describe, expect, it } from 'vitest';
import { getProjectBorderColor } from '../projectColor';
describe('保存済みプロジェクト色', () => {
  it('プロジェクト名やキーをハッシュ化せず、サーバーの色をそのまま使う', () => {
    expect(getProjectBorderColor('#e3f2fd')).toBe('#e3f2fd');
    expect(getProjectBorderColor('#dff6f2')).not.toBe(
      getProjectBorderColor('#e3f2fd'),
    );
  });
  it('色が保存されていない旧データには色を付けない', () => {
    expect(getProjectBorderColor(null)).toBeNull();
  });
  it('先頭に#がない値は色として使わない', () => {
    expect(getProjectBorderColor('ABC')).toBeNull();
  });
  it('空白だけの値は色として使わない', () => {
    expect(getProjectBorderColor('   ')).toBeNull();
  });
  it('短縮形の16進数カラーは使わない', () => {
    expect(getProjectBorderColor('#fff')).toBeNull();
  });
  it('CSS式は色として使わない', () => {
    expect(getProjectBorderColor('url(example)')).toBeNull();
  });
});
