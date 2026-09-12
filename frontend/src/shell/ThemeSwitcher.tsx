import { useSyncExternalStore } from 'react';
import { getThemePreference, setThemePreference, subscribeTheme, type ThemePreference } from './theme';

export function ThemeSwitcher() {
  const preference = useSyncExternalStore(subscribeTheme, getThemePreference, () => 'system');
  return (
    <select className="theme-switcher" aria-label="화면 테마" value={preference}
      onChange={(event) => setThemePreference(event.target.value as ThemePreference)}>
      <option value="system">기기 설정</option>
      <option value="light">밝게</option>
      <option value="dark">어둡게</option>
    </select>
  );
}
