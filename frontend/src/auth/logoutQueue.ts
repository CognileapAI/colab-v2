export type RevocationEntry = {
  sessionId: string;
  revocationToken: string;
  expiresAt: string;
  attempts?: number;
  nextAttemptAt?: number;
  halted?: boolean;
};
const KEY = 'colab.logout-queue.v1';
let memoryQueue: RevocationEntry[] = [];
export type LogoutQueueStatus = 'idle' | 'server-unconfirmed' | 'storage-unavailable' | 'manual-check';
let status: LogoutQueueStatus = 'idle';
const statusListeners = new Set<() => void>();
function setStatus(next: LogoutQueueStatus): void {
  status = next;
  statusListeners.forEach((listener) => listener());
}
export function getLogoutQueueStatus(): LogoutQueueStatus { return status; }
export function subscribeLogoutQueueStatus(listener: () => void): () => void {
  statusListeners.add(listener);
  return () => statusListeners.delete(listener);
}
function load(): RevocationEntry[] {
  try {
    const parsed = JSON.parse(window.localStorage.getItem(KEY) ?? '[]') as unknown;
    return Array.isArray(parsed) ? parsed as RevocationEntry[] : [];
  } catch { return memoryQueue; }
}
function save(entries: RevocationEntry[]): boolean {
  memoryQueue = entries;
  try { window.localStorage.setItem(KEY, JSON.stringify(entries)); return true; }
  catch { return false; }
}
export function enqueueRevocation(entry: RevocationEntry): boolean {
  const safeEntry: RevocationEntry = {
    sessionId: entry.sessionId,
    revocationToken: entry.revocationToken,
    expiresAt: entry.expiresAt,
    attempts: 0,
    nextAttemptAt: 0,
  };
  const stored = save([...load().filter((item) => item.sessionId !== entry.sessionId), safeEntry]);
  setStatus(stored ? 'server-unconfirmed' : 'storage-unavailable');
  return stored;
}
export function inspectLogoutQueue(): RevocationEntry[] { return load(); }
let activeFlush: Promise<void> | null = null;
let retryTimer: number | null = null;
function scheduleNextFlush(revoke: (capability: string) => Promise<number> = revokeSession): void {
  if (retryTimer !== null) window.clearTimeout(retryTimer);
  const next = load()
    .filter((entry) => !entry.halted)
    .map((entry) => entry.nextAttemptAt ?? 0)
    .sort((a, b) => a - b)[0];
  if (next === undefined) { retryTimer = null; return; }
  retryTimer = window.setTimeout(() => {
    retryTimer = null;
    void flushLogoutQueue(revoke);
  }, Math.max(0, next - Date.now()));
}
export async function flushLogoutQueue(
  revoke: (capability: string) => Promise<number> = revokeSession,
): Promise<void> {
  if (activeFlush) {
    await activeFlush;
    const now = Date.now();
    if (load().some((entry) => !entry.halted && (entry.nextAttemptAt ?? 0) <= now)) {
      return flushLogoutQueue(revoke);
    }
    return;
  }
  activeFlush = flushOnce(revoke).finally(() => {
    activeFlush = null;
    scheduleNextFlush(revoke);
  });
  return activeFlush;
}
async function flushOnce(revoke: (capability: string) => Promise<number>): Promise<void> {
  const now = Date.now(); const remaining: RevocationEntry[] = [];
  const started = load();
  for (const entry of started) {
    if (Date.parse(entry.expiresAt) <= now) continue;
    if (entry.halted) { remaining.push(entry); continue; }
    if ((entry.nextAttemptAt ?? 0) > now) { remaining.push(entry); continue; }
    try {
      const status = await revoke(entry.revocationToken);
      if (status === 204) continue;
      if (status === 400) {
        remaining.push({ ...entry, halted: true });
        setStatus('manual-check');
        continue;
      }
    } catch { /* retry below */ }
    const attempts = (entry.attempts ?? 0) + 1;
    remaining.push({ ...entry, attempts,
      nextAttemptAt: now + Math.min(60, 2 ** Math.max(0, attempts - 1)) * 1000 });
  }
  const startedIds = new Set(started.map((entry) => entry.sessionId));
  const addedDuringFlush = load().filter((entry) => !startedIds.has(entry.sessionId));
  save([...remaining, ...addedDuringFlush]);
  if (remaining.length === 0 && addedDuringFlush.length === 0) setStatus('idle');
}
async function revokeSession(revocationToken: string): Promise<number> {
  const response = await fetch('/api/v1/sessions/revoke', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ revocationToken }),
  });
  return response.status;
}
export function startLogoutQueue(): () => void {
  const flush = () => void flushLogoutQueue();
  const queued = load();
  if (queued.some((entry) => entry.halted)) setStatus('manual-check');
  else if (queued.length > 0) setStatus('server-unconfirmed');
  window.addEventListener('online', flush); flush();
  const timer = window.setInterval(flush, 60_000);
  return () => {
    window.removeEventListener('online', flush);
    window.clearInterval(timer);
    if (retryTimer !== null) window.clearTimeout(retryTimer);
    retryTimer = null;
  };
}
export function resetLogoutQueueForTests(): void {
  memoryQueue = [];
  activeFlush = null;
  if (retryTimer !== null) window.clearTimeout(retryTimer);
  retryTimer = null;
  setStatus('idle');
  try { window.localStorage.removeItem(KEY); } catch { /* memory is enough */ }
}
