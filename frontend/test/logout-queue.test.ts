import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  enqueueRevocation,
  flushLogoutQueue,
  inspectLogoutQueue,
  resetLogoutQueueForTests,
  startLogoutQueue,
} from '../src/auth/logoutQueue';

beforeEach(() => resetLogoutQueueForTests());

describe('offline logout queue', () => {
  it('persists only the revocation capability and session metadata', () => {
    enqueueRevocation({
      sessionId: 'S',
      revocationToken: 'cap',
      expiresAt: '2030-01-01T00:00:00Z',
      token: 'access-token-must-not-be-stored',
    } as Parameters<typeof enqueueRevocation>[0] & { token: string });
    const encoded = [...Array(localStorage.length)]
      .map((_unused, index) => localStorage.getItem(localStorage.key(index) ?? ''))
      .join('');
    expect(encoded).toContain('cap');
    expect(encoded).not.toContain('access-token-must-not-be-stored');
  });

  it('removes 204 entries while keeping 503 entries', async () => {
    enqueueRevocation({
      sessionId: 'A',
      revocationToken: 'one',
      expiresAt: '2030-01-01T00:00:00Z',
    });
    enqueueRevocation({
      sessionId: 'B',
      revocationToken: 'two',
      expiresAt: '2030-01-01T00:00:00Z',
    });
    const revoke = vi.fn(async (cap: string) => (cap === 'one' ? 204 : 503));
    await flushLogoutQueue(revoke);
    expect(inspectLogoutQueue().map((item) => item.sessionId)).toEqual(['B']);
  });

  it('keeps a 400 entry halted for a visible manual check', async () => {
    enqueueRevocation({
      sessionId: 'A',
      revocationToken: 'bad',
      expiresAt: '2030-01-01T00:00:00Z',
    });
    await flushLogoutQueue(async () => 400);
    expect(inspectLogoutQueue()).toMatchObject([{ sessionId: 'A', halted: true }]);
  });

  it('retries a transient failure after the one-second backoff without waiting for the interval', async () => {
    vi.useFakeTimers();
    const revoke = vi.fn()
      .mockResolvedValueOnce(503)
      .mockResolvedValueOnce(204);
    enqueueRevocation({
      sessionId: 'A', revocationToken: 'cap', expiresAt: '2030-01-01T00:00:00Z',
    });
    await flushLogoutQueue(revoke);
    expect(revoke).toHaveBeenCalledTimes(1);
    await vi.advanceTimersByTimeAsync(1_000);
    expect(revoke).toHaveBeenCalledTimes(2);
    expect(inspectLogoutQueue()).toEqual([]);
    vi.useRealTimers();
  });

  it('surfaces a persisted unconfirmed logout when the queue restarts', () => {
    enqueueRevocation({
      sessionId: 'A', revocationToken: 'cap', expiresAt: '2030-01-01T00:00:00Z',
    });
    const stop = startLogoutQueue();
    expect(inspectLogoutQueue()).toHaveLength(1);
    stop();
  });
});
