// 세션 토큰의 **유일한 보관소**. 다른 화면은 이 파일을 거치지 않고 토큰을 읽지 않는다
// (`PLAN-SoT §9 〈90〉-㉮` — 인증 세부를 한 모듈 안에 가둔다).
//
// 어디에 두는가 — `localStorage`. 무상태 서명 세션(`〈90〉-㉯`)이라 서버가 쿠키를 심을 자리가
// 없고, FE 는 정적 배포다(`frontend/README`). 새로고침으로 로그인이 풀리면 사람이 화면을
// 못 쓰므로 세션 스토리지가 아니라 로컬 스토리지를 쓴다.
//
// ⚠ **되돌림 비용이 낮은 선택이다.** 보관 위치를 쿠키로 옮기려면 이 파일과 `client.ts` 의
// 미들웨어만 바뀐다 — 화면은 `useAuth()` 밖을 모른다.

const SESSION_KEY = 'colab.browser-session.v1';
const LEGACY_KEY = 'colab.session.token';
const LOGOUT_EPOCH_KEY = 'colab.logout-epoch.v1';

type Listener = () => void;
const listeners = new Set<Listener>();
export type BrowserSession = {
  token: string;
  sessionId: string;
  expiresAt: string;
  revocationToken: string;
};
type StoredSession = BrowserSession & { epoch: string; suspended?: boolean };

// jsdom·프라이빗 모드처럼 저장소 접근 자체가 던지는 환경이 있다. 던지면 **로그인 안 된 것**으로
// 본다 — fail-closed. 조용히 통과시키지 않는다.
function safeGet(): StoredSession | null {
  try {
    const raw = window.localStorage.getItem(SESSION_KEY);
    if (!raw) return null;
    const value = JSON.parse(raw) as Partial<StoredSession>;
    if (typeof value.token !== 'string' || typeof value.sessionId !== 'string' ||
      typeof value.expiresAt !== 'string' || typeof value.revocationToken !== 'string' ||
      typeof value.epoch !== 'string') return null;
    return value as StoredSession;
  } catch {
    return null;
  }
}

let cached: StoredSession | null = safeGet();
let memoryOnly = false;
const locallyRetired = new Set<string>();
const suppressedEpochs = new Set<string>();
try { window.localStorage.removeItem(LEGACY_KEY); } catch { /* reauthenticate */ }

function durableSession(): StoredSession | null {
  const stored = safeGet();
  if (stored && (locallyRetired.has(stored.sessionId) || suppressedEpochs.has(stored.epoch))) return null;
  try {
    const raw = window.localStorage.getItem(LOGOUT_EPOCH_KEY);
    const tombstone = raw ? JSON.parse(raw) as { sessionId?: string } : null;
    if (stored && tombstone?.sessionId === stored.sessionId) return null;
  } catch {
    // A malformed tombstone never creates an authenticated session.
  }
  return stored;
}
export function getSession(): BrowserSession | null {
  if (memoryOnly) return cached;
  const durable = durableSession();
  if ((durable?.epoch ?? null) !== (cached?.epoch ?? null)) {
    cached = durable;
    // A request can observe storage before its queued browser event. Publish the
    // observation after this read, including when it happened during render.
    queueMicrotask(() => listeners.forEach((listener) => listener()));
  }
  return cached;
}
export function getSessionEpoch(): string { getSession(); return cached?.epoch ?? ''; }
export function isSessionExpired(session: BrowserSession | null = cached): boolean {
  return Boolean(session && Date.parse(session.expiresAt) <= Date.now());
}
export function requiresReauthentication(): boolean {
  return Boolean(cached && (cached.suspended || isSessionExpired(cached)));
}

export function getToken(): string | null {
  getSession();
  return cached && !requiresReauthentication() ? cached.token : null;
}

export function setSession(session: BrowserSession): void {
  cached = { ...session, epoch: crypto.randomUUID(), suspended: false };
  try {
    window.localStorage.setItem(SESSION_KEY, JSON.stringify(cached));
    window.localStorage.removeItem(LEGACY_KEY);
    memoryOnly = false;
  } catch {
    memoryOnly = true;
    /* 저장이 안 되면 이 탭 안에서만 산다. 그 사실을 거짓말로 덮지 않는다. */
  }
  listeners.forEach((l) => l());
}

export function clearSession(): void {
  if (cached) suppressedEpochs.add(cached.epoch);
  cached = null;
  memoryOnly = false;
  try {
    window.localStorage.removeItem(SESSION_KEY);
  } catch {
    /* 위와 같다 */
  }
  listeners.forEach((l) => l());
}
export const clearToken = clearSession;
export function clearIfCurrent(token: string): void {
  // 잠든 탭의 캐시보다 localStorage에 발표된 새 세션을 먼저 읽는다.
  getSession();
  if (cached?.token !== token) return;
  cached = { ...cached, epoch: crypto.randomUUID(), suspended: true };
  try { window.localStorage.setItem(SESSION_KEY, JSON.stringify(cached)); }
  catch { memoryOnly = true; }
  listeners.forEach((listener) => listener());
}
export function markLogoutEpoch(sessionId: string): void {
  locallyRetired.add(sessionId);
  window.dispatchEvent(new CustomEvent('colab-session-retired', { detail: sessionId }));
  try { window.localStorage.setItem(LOGOUT_EPOCH_KEY, JSON.stringify({ sessionId, at: Date.now() })); }
  catch { /* memory session is still removed */ }
}

export function subscribe(listener: Listener): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

if (typeof window !== 'undefined') {
  window.addEventListener('storage', (event) => {
    if (event.key === LEGACY_KEY) {
      try { window.localStorage.removeItem(LEGACY_KEY); } catch { /* reauthenticate */ }
    }
    if (event.key !== SESSION_KEY && event.key !== LOGOUT_EPOCH_KEY) return;
    let tombstoneSessionId: string | null = null;
    try {
      tombstoneSessionId = event.key === LOGOUT_EPOCH_KEY && event.newValue
        ? (JSON.parse(event.newValue) as { sessionId?: string }).sessionId ?? null
        : null;
    } catch {
      return;
    }
    if (tombstoneSessionId) {
      locallyRetired.add(tombstoneSessionId);
      window.dispatchEvent(new CustomEvent('colab-session-retired', { detail: tombstoneSessionId }));
    }
    cached = durableSession();
    memoryOnly = false;
    listeners.forEach((listener) => listener());
  });
}
