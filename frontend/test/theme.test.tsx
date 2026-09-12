import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { startThemeSync, setThemePreference, getThemePreference } from '../src/shell/theme';
import { ThemeSwitcher } from '../src/shell/ThemeSwitcher';

let dark = false;
let listener: (() => void) | undefined;
let stop: (() => void) | undefined;
beforeEach(() => {
  localStorage.clear();
  delete document.documentElement.dataset.theme;
  delete document.documentElement.dataset.themePreference;
  dark = false;
  vi.stubGlobal('matchMedia', () => ({ get matches() { return dark; }, addEventListener: (_: string, fn: () => void) => { listener = fn; }, removeEventListener: () => { listener = undefined; } }));
});
afterEach(() => { stop?.(); stop = undefined; vi.restoreAllMocks(); vi.unstubAllGlobals(); });

it('처음에는 OS를 따르고 OS 변경을 반영한다', () => {
  stop = startThemeSync();
  expect(getThemePreference()).toBe('system');
  expect(document.documentElement.dataset.theme).toBe('light');
  dark = true; listener?.();
  expect(document.documentElement.dataset.theme).toBe('dark');
});
it('명시 선택을 저장하고 재시작 후 복구하며 OS 변경보다 우선한다', () => {
  stop = startThemeSync();
  setThemePreference('dark');
  expect(localStorage.getItem('colab.theme')).toBe('dark');
  listener?.();
  expect(document.documentElement.dataset.theme).toBe('dark');
  stop(); delete document.documentElement.dataset.themePreference;
  stop = startThemeSync();
  expect(getThemePreference()).toBe('dark');
  expect(document.documentElement.dataset.theme).toBe('dark');
});
it('유효하지 않은 저장값은 시스템으로 처리하고 다른 탭 변경을 반영한다', () => {
  localStorage.setItem('colab.theme', 'invalid');
  stop = startThemeSync();
  expect(getThemePreference()).toBe('system');
  window.dispatchEvent(new StorageEvent('storage', { key: 'colab.theme', newValue: 'dark' }));
  expect(getThemePreference()).toBe('dark');
  expect(document.documentElement.dataset.theme).toBe('dark');
});
it('저장소가 차단되어도 현재 창에서 선택을 적용한다', () => {
  vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => { throw new Error('blocked'); });
  vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('blocked'); });
  stop = startThemeSync();
  expect(() => setThemePreference('dark')).not.toThrow();
  expect(document.documentElement.dataset.theme).toBe('dark');
});
describe('화면 테마 조작', () => {
  it('이름이 있는 컨트롤로 시스템·밝게·어둡게를 선택하고 현재 선택을 읽는다', () => {
    stop = startThemeSync();
    render(<ThemeSwitcher />);
    const control = screen.getByRole('combobox', { name: '화면 테마' });
    fireEvent.change(control, { target: { value: 'dark' } });
    expect(control).toHaveValue('dark');
    expect(document.documentElement.dataset.theme).toBe('dark');
    fireEvent.change(control, { target: { value: 'system' } });
    expect(control).toHaveValue('system');
    expect(document.documentElement.dataset.theme).toBe('light');
  });
});
