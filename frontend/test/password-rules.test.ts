import { describe, expect, it } from 'vitest';
import { passwordLength, validNewPassword } from '../src/auth/passwordRules';

describe('password rules use Unicode code points', () => {
  it.each([
    ['ascii 9', 'a'.repeat(9), false],
    ['ascii 10', 'a'.repeat(10), true],
    ['emoji 9', '😀'.repeat(9), false],
    ['emoji 10', '😀'.repeat(10), true],
    ['emoji 512', '😀'.repeat(512), true],
    ['emoji 513', '😀'.repeat(513), false],
  ])('%s', (_label, value, valid) => {
    expect(passwordLength(value)).toBe(Array.from(value).length);
    expect(validNewPassword(value)).toBe(valid);
  });
});
