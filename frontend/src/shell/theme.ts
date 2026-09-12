export type ThemePreference = 'system' | 'light' | 'dark';
const storageKey = 'colab.theme';
const changeEvent = 'colab:theme';
const valid = (value: string | null | undefined): ThemePreference =>
  value === 'light' || value === 'dark' ? value : 'system';

export function getThemePreference(): ThemePreference {
  return valid(document.documentElement.dataset.themePreference);
}

function apply(preference: ThemePreference) {
  const root = document.documentElement;
  root.dataset.themePreference = preference;
  root.dataset.theme = preference === 'system'
    ? (window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
    : preference;
  window.dispatchEvent(new Event(changeEvent));
}

export function setThemePreference(preference: ThemePreference) {
  try { localStorage.setItem(storageKey, preference); } catch { /* Current-window selection still works. */ }
  apply(preference);
}

export function subscribeTheme(listener: () => void) {
  window.addEventListener(changeEvent, listener);
  return () => window.removeEventListener(changeEvent, listener);
}

export function startThemeSync() {
  let saved: string | null = null;
  try { saved = localStorage.getItem(storageKey); } catch { /* Use the device preference. */ }
  apply(valid(saved));
  const media = window.matchMedia?.('(prefers-color-scheme: dark)');
  const onMedia = () => { if (getThemePreference() === 'system') apply('system'); };
  const onStorage = (event: StorageEvent) => {
    if (event.key === storageKey || event.key === null) apply(valid(event.newValue));
  };
  media?.addEventListener('change', onMedia);
  window.addEventListener('storage', onStorage);
  return () => {
    media?.removeEventListener('change', onMedia);
    window.removeEventListener('storage', onStorage);
  };
}
