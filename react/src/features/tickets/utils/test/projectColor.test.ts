import { describe, expect, it } from 'vitest';
import { getProjectBorderColor } from '../projectColor';
describe('stored project color', () => {
  it('uses the server color verbatim, without hashing project names or keys', () => {
    expect(getProjectBorderColor('#e3f2fd')).toBe('#e3f2fd');
    expect(getProjectBorderColor('#dff6f2')).not.toBe(
      getProjectBorderColor('#e3f2fd'),
    );
  });
  it('keeps missing or malformed legacy data neutral', () => {
    for (const value of [null, 'ABC', '   ', '#fff', 'url(example)'])
      expect(getProjectBorderColor(value)).toBeNull();
  });
});
