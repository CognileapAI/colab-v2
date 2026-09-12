import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { useState } from 'react';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthGate } from '../src/auth/AuthGate';
import { useAccount } from '../src/permission/session';
import { account } from './factories';
import * as store from '../src/auth/store';
import { logoutCurrent } from '../src/auth/sessionCoordinator';
import { beginTransition, registerWork, resetWorkGuardForTests, setCurrentAccountId } from '../src/auth/workGuard';

const session = (id: string) => ({ token: id, sessionId: id, revocationToken: 'revoke-' + id, expiresAt: '2030-01-01T00:00:00Z' });
beforeEach(() => { localStorage.clear(); store.clearSession(); resetWorkGuardForTests(); });
afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); document.body.innerHTML = ''; });

it('logout cannot resurrect a token when storage reads work but writes fail', async () => {
  store.setSession(session('storage-failure'));
  vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('quota'); });
  vi.spyOn(Storage.prototype, 'removeItem').mockImplementation(() => { throw new Error('denied'); });
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')));
  await logoutCurrent();
  expect(store.getSession()).toBeNull();
  expect(store.getToken()).toBeNull();
});

it('a delayed old logout event cannot discard new session work', () => {
  store.setSession(session('new-session'));
  setCurrentAccountId('A');
  const discard = vi.fn();
  registerWork('new-draft', { accountId: 'A', dirty: true, inFlight: false, discard });
  window.dispatchEvent(new StorageEvent('storage', {
    key: 'colab.logout-epoch.v1', newValue: JSON.stringify({ sessionId: 'old-session', at: Date.now() }),
  }));
  expect(discard).not.toHaveBeenCalled();
});

it('logout finishes against its original session when another login wins during confirmation', async () => {
  store.setSession(session('logout-original'));
  const original = store.getSession();
  const epoch = store.getSessionEpoch();
  store.setSession(session('login-winner'));
  const fetcher = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
  vi.stubGlobal('fetch', fetcher);
  await logoutCurrent(original, epoch);
  expect(store.getSession()?.sessionId).toBe('login-winner');
  const requests = fetcher.mock.calls.map(([request]) => request).filter((request): request is Request => request instanceof Request);
  expect(requests.some(request => request.headers.get('Authorization') === 'Bearer logout-original')).toBe(true);
  expect(requests.some(request => request.headers.get('Authorization') === 'Bearer login-winner')).toBe(false);
});

it('preparing a session transition freezes real application inputs', () => {
  document.body.innerHTML = '<div data-session-work-root><input value="draft"></div>';
  const root = document.querySelector('[data-session-work-root]')!;
  const finish = beginTransition();
  expect(root.hasAttribute('inert')).toBe(true);
  finish();
  expect(root.hasAttribute('inert')).toBe(false);
});

it('a server 401 suspends the matching session in another loaded tab', async () => {
  store.setSession(session('shared-invalidated'));
  vi.resetModules();
  const otherTab = await import('../src/auth/store');
  expect(otherTab.getToken()).toBe('shared-invalidated');
  store.clearIfCurrent('shared-invalidated');
  window.dispatchEvent(new StorageEvent('storage', { key: 'colab.browser-session.v1' }));
  expect(otherTab.getToken()).toBeNull();
});

it('an API read before the storage event cannot swallow the UI notification', async () => {
  store.setSession(session('before-api-read'));
  vi.resetModules();
  const otherTab = await import('../src/auth/store');
  store.setSession(session('after-api-read'));
  otherTab.getSession();
  const changed = vi.fn();
  const unsubscribe = otherTab.subscribe(changed);
  window.dispatchEvent(new StorageEvent('storage', { key: 'colab.browser-session.v1' }));
  expect(changed).toHaveBeenCalled();
  unsubscribe();
});

it('preserves same-account drafts but removes previous-account component data', async () => {
  function AccountPage() {
    const current = useAccount();
    const [draft, setDraft] = useState('');
    const [loadedFor] = useState(current?.accountId);
    return <><p>{current?.accountId}:{loadedFor}</p><input aria-label="draft" value={draft} onChange={e => setDraft(e.target.value)} /></>;
  }
  let currentId = 'account-A';
  vi.stubGlobal('fetch', vi.fn().mockImplementation(() => Promise.resolve(new Response(
    JSON.stringify({ ...account(), accountId: currentId }), { status: 200, headers: { 'Content-Type': 'application/json' } },
  ))));
  store.setSession(session('isolation-A'));
  render(<MemoryRouter><AuthGate><AccountPage /></AuthGate></MemoryRouter>);
  await screen.findByText('account-A:account-A');
  fireEvent.change(screen.getByLabelText('draft'), { target: { value: 'keep for A' } });
  act(() => store.setSession(session('isolation-A-relogin')));
  await waitFor(() => expect(screen.getByLabelText('draft')).toHaveValue('keep for A'));
  currentId = 'account-B';
  act(() => store.setSession(session('isolation-B')));
  await screen.findByText('account-B:account-B');
  expect(screen.getByLabelText('draft')).toHaveValue('');
});
