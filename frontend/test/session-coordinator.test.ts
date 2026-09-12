import { beforeEach, describe, expect, it } from 'vitest';
import {
  clearIfCurrent,
  clearSession,
  getSession,
  markLogoutEpoch,
  setSession,
} from '../src/auth/store';
import { transitionTo } from '../src/auth/sessionCoordinator';
import {
  getCurrentAccountId,
  registerWork,
  resetWorkGuardForTests,
  setCurrentAccountId,
} from '../src/auth/workGuard';

const session = (token: string) => ({
  token,
  sessionId: `sid-${token}`,
  expiresAt: '2030-01-01T00:00:00Z',
  revocationToken: `cap-${token}`,
});

beforeEach(() => { clearSession(); resetWorkGuardForTests(); });

describe('session publication is conditional', () => {
  it('an old 401 cannot clear a newer session', () => {
    setSession(session('old-token'));
    setSession(session('new-token'));
    clearIfCurrent('old-token');
    expect(getSession()?.token).toBe('new-token');
  });

  it('legacy token-only storage is rejected for reauthentication', () => {
    localStorage.setItem('colab.session.token', 'legacy-token');
    window.dispatchEvent(
      new StorageEvent('storage', { key: 'colab.session.token' }),
    );
    expect(getSession()).toBeNull();
  });

  it('an old logout tombstone cannot clear a newer session', () => {
    setSession(session('old-token'));
    markLogoutEpoch('sid-old-token');
    setSession(session('new-token'));
    window.dispatchEvent(new StorageEvent('storage', {
      key: 'colab.logout-epoch.v1',
      newValue: JSON.stringify({ sessionId: 'sid-old-token', at: Date.now() }),
    }));
    expect(getSession()?.token).toBe('new-token');
  });

  it('a sleeping tab old 401 cannot overwrite a newer durable session', () => {
    setSession(session('old-token'));
    const newer = { ...session('new-token'), epoch: crypto.randomUUID(), suspended: false };
    localStorage.setItem('colab.browser-session.v1', JSON.stringify(newer));
    clearIfCurrent('old-token');
    expect(getSession()?.token).toBe('new-token');
    expect(JSON.parse(localStorage.getItem('colab.browser-session.v1') ?? '{}').token)
      .toBe('new-token');
  });

  it('preserves dirty work while the same account recovers an expired session', async () => {
    setCurrentAccountId('A');
    registerWork('account-form', { accountId: 'A', dirty: true, inFlight: false });
    const recovered = session('recovered-token');
    expect(await transitionTo(recovered, 'A')).toBe(true);
    expect(getSession()?.token).toBe('recovered-token');
    expect(getCurrentAccountId()).toBe('A');
  });
});
