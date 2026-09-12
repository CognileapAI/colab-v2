import { beforeEach, expect, it, vi } from 'vitest';
import { clearSession, setSession } from '../src/auth/store';
import { sessionBoundFetch } from '../src/auth/sessionFetch';

beforeEach(() => clearSession());

it('aborts a file request when its starting session is replaced', async () => {
  setSession({ token: 'old', sessionId: 'S1', expiresAt: '2099-01-01T00:00:00Z', revocationToken: 'C1' });
  let requestSignal: AbortSignal | undefined;
  const transport = vi.fn(async (request: Request) => {
    requestSignal = request.signal;
    await new Promise<void>((resolve) => request.signal.addEventListener('abort', () => resolve(), { once: true }));
    throw new DOMException('aborted', 'AbortError');
  });
  const pending = sessionBoundFetch(new Request('https://example.test/upload'), transport);
  setSession({ token: 'new', sessionId: 'S2', expiresAt: '2099-01-01T00:00:00Z', revocationToken: 'C2' });
  await expect(pending).rejects.toMatchObject({ name: 'AbortError' });
  expect(requestSignal?.aborted).toBe(true);
});
