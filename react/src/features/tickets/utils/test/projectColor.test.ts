import { describe, expect, it } from 'vitest';
import { getProjectBorderColor } from '../projectColor';

describe('project border color', () => {
  it('returns a stable color for the fixed project key', () => {
    expect(getProjectBorderColor('ABC')).toBe(getProjectBorderColor('ABC'));
    expect(getProjectBorderColor('abc')).toBe(getProjectBorderColor('ABC'));
    expect(getProjectBorderColor('ABC')).not.toBe(getProjectBorderColor('XYZ'));
  });

  it('leaves legacy projects without a key on the default card border', () => {
    expect(getProjectBorderColor(null)).toBeNull();
    expect(getProjectBorderColor('   ')).toBeNull();
  });
});
