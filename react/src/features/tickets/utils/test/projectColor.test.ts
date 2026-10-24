import { describe, expect, it } from 'vitest';
import { getProjectBorderColor } from '../projectColor';
describe('stored project color', () => {
  it('uses the server color verbatim, without hashing project names or keys', () => {
    expect(getProjectBorderColor('#e3f2fd')).toBe('#e3f2fd');
    expect(getProjectBorderColor('#dff6f2')).not.toBe(
      getProjectBorderColor('#e3f2fd'),
    );
  });
  it('keeps a missing legacy color neutral', () => {
    expect(getProjectBorderColor(null)).toBeNull();
  });
  it('keeps a color without a leading hash neutral', () => {
    expect(getProjectBorderColor('ABC')).toBeNull();
  });
  it('keeps a whitespace-only color neutral', () => {
    expect(getProjectBorderColor('   ')).toBeNull();
  });
  it('keeps a short hex color neutral', () => {
    expect(getProjectBorderColor('#fff')).toBeNull();
  });
  it('keeps a CSS expression neutral', () => {
    expect(getProjectBorderColor('url(example)')).toBeNull();
  });
});
