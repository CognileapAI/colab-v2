import { setSession } from '../src/auth/store';

export function sessionFixture(token: string) {
  return {
    token,
    sessionId: '01JYZ9K7WQ3N8V4M2X6C5B0SS1',
    expiresAt: '2099-01-01T00:00:00Z',
    revocationToken: 'test-revocation-capability',
  };
}

export function setToken(token: string): void {
  setSession({ ...sessionFixture(token), sessionId: crypto.randomUUID() });
}
