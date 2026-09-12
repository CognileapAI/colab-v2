import { clearSession, getSession, getSessionEpoch, markLogoutEpoch, setSession, type BrowserSession } from './store';
import { enqueueRevocation, flushLogoutQueue } from './logoutQueue';
import {
  beginTransition,
  canTransition,
  canTransitionAcrossTabs,
  getCurrentAccountId,
  prepareTransitionAcrossTabs,
} from './workGuard';

type LockManagerLike = {
  request<T>(
    name: string,
    options: { mode: 'exclusive'; ifAvailable?: boolean },
    callback: (lock: unknown | null) => Promise<T>,
  ): Promise<T>;
};

async function withTransitionLock<T>(
  work: () => Promise<T>,
  allowWithoutLocks: boolean,
): Promise<T | null> {
  const locks = (navigator as Navigator & { locks?: LockManagerLike }).locks;
  // 첫 로그인에는 전환할 기존 계정/작업이 없다. Web Locks가 없는 브라우저에서도
  // 최초 진입은 허용하되, 활성 계정 교체는 fail-closed다.
  if (!locks) return !getSession() || allowWithoutLocks ? work() : null;
  return locks.request(
    'colab-session-transition',
    { mode: 'exclusive', ifAvailable: true },
    async (lock) => (lock ? work() : null),
  );
}

export async function transitionTo(
  next: BrowserSession,
  verifiedAccountId: string,
): Promise<boolean> {
  const sameAccountRecovery = getCurrentAccountId() === verifiedAccountId;
  const result = await withTransitionLock(async () => {
    const finish = beginTransition();
    let finishTabs: () => void = () => undefined;
    try {
      const sameAccountInsideLock = getCurrentAccountId() === verifiedAccountId;
      if (!(await canTransitionAcrossTabs(verifiedAccountId))) return false;
      finishTabs = await prepareTransitionAcrossTabs(verifiedAccountId);
      if (!sameAccountInsideLock && !canTransition()) return false;
      setSession(next);
      return true;
    } finally {
      finishTabs();
      finish();
    }
  }, sameAccountRecovery);
  if (result === true) return true;
  enqueueRevocation(next);
  void flushLogoutQueue();
  return false;
}

export async function logoutCurrent(
  session: BrowserSession | null = getSession(),
  epoch: string = getSessionEpoch(),
): Promise<void> {
  if (!session) return;
  const current = getSession();
  const stillCurrent = current?.sessionId === session.sessionId &&
    current.token === session.token && getSessionEpoch() === epoch;
  enqueueRevocation(session);
  markLogoutEpoch(session.sessionId);
  if (stillCurrent) clearSession();
  void fetch(new Request(new URL('/api/v1/sessions/current', window.location.origin), {
    method: 'DELETE',
    headers: { Authorization: 'Bearer ' + session.token },
  })).catch(() => undefined);
  void flushLogoutQueue();
}
