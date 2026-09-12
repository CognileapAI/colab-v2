import { discardDrafts } from './draftVault';
import { getSession } from './store';

export type WorkState = {
  accountId: string;
  dirty: boolean;
  inFlight: boolean;
  discard?: () => void | Promise<void>;
  abort?: () => void;
};
const work = new Map<string, WorkState & { ownerSessionId: string | undefined }>();
type RemoteState = { dirty: boolean; inFlight: boolean; accountId: string | null; ackAt: number };
const remote = new Map<string, RemoteState>();
const prepared = new Map<string, Set<string>>();
const discarded = new Map<string, Set<string>>();
let transitionPending = false;
let currentAccountId: string | null = null;
let currentSessionId: string | undefined;
const frozenRoots = new Set<Element>();
function setTransitionPending(value: boolean): void {
  transitionPending = value;
  if (value) {
    for (const root of document.querySelectorAll('[data-session-work-root]')) {
      if (!root.hasAttribute('inert')) { root.setAttribute('inert', ''); frozenRoots.add(root); }
    }
  } else {
    for (const root of frozenRoots) {
      if (root.getAttribute('aria-hidden') !== 'true') root.removeAttribute('inert');
    }
    frozenRoots.clear();
  }
}
const tabId = crypto.randomUUID();
const TAB_REGISTRY_KEY = 'colab.live-tabs.v1';
function knownTabs(): string[] {
  try {
    const value = JSON.parse(window.localStorage.getItem(TAB_REGISTRY_KEY) ?? '[]') as unknown;
    return Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string') : [];
  } catch { return []; }
}
function writeKnownTabs(values: string[]): void {
  try { window.localStorage.setItem(TAB_REGISTRY_KEY, JSON.stringify([...new Set(values)])); }
  catch { /* Web Locks still make unknown tabs fail closed. */ }
}
writeKnownTabs([...knownTabs(), tabId]);
const channel = typeof BroadcastChannel === 'undefined'
  ? null
  : new BroadcastChannel('colab-work-guard.v1');

function localSummary() {
  return {
    type: 'state',
    tabId,
    accountId: currentAccountId,
    dirty: [...work.values()].some((item) => item.dirty),
    inFlight: [...work.values()].some((item) => item.inFlight),
  };
}
function publish(): void { channel?.postMessage(localSummary()); }
if (channel) {
  channel.onmessage = (event: MessageEvent) => {
    const message = event.data as { type?: string; tabId?: string; nonce?: string; accountId?: string | null; dirty?: boolean; inFlight?: boolean; preserveAccountId?: string; ownerSessionId?: string };
    if (message.tabId === tabId) return;
    if (message.type === 'probe') { publish(); return; }
    if (message.type === 'prepare' && message.nonce) {
      setTransitionPending(true);
      const mayPreserve = Boolean(message.preserveAccountId) &&
        currentAccountId === message.preserveAccountId;
      if (mayPreserve || !hasAccountWork()) {
        channel.postMessage({ type: 'prepared', tabId, nonce: message.nonce });
      }
      return;
    }
    if (message.type === 'finish') { setTransitionPending(false); return; }
    if (message.type === 'prepared' && message.nonce && message.tabId) {
      const acknowledgements = prepared.get(message.nonce);
      acknowledgements?.add(message.tabId);
      return;
    }
    if (message.type === 'discard' && message.nonce && message.accountId) {
      if (message.ownerSessionId !== currentSessionId) return;
      void discardAccountWork(message.accountId, message.ownerSessionId).then(() => {
        channel.postMessage({ type: 'discarded', tabId, nonce: message.nonce });
      });
      return;
    }
    if (message.type === 'discarded' && message.nonce && message.tabId) {
      discarded.get(message.nonce)?.add(message.tabId);
      return;
    }
    if (message.type !== 'state') return;
    if (!message.tabId) return;
    remote.set(message.tabId, {
      accountId: message.accountId ?? null,
      dirty: Boolean(message.dirty),
      inFlight: Boolean(message.inFlight),
      ackAt: Date.now(),
    });
  };
}
const locks = (navigator as Navigator & {
  locks?: { request<T>(name: string, callback: () => Promise<T>): Promise<T> };
}).locks;
if (locks) {
  void locks.request('colab-tab-alive:' + tabId, () => new Promise<void>(() => undefined));
}

export function setCurrentAccountId(accountId: string | null): void {
  currentAccountId = accountId;
  currentSessionId = getSession()?.sessionId;
  for (const item of work.values()) {
    if (item.accountId === accountId) item.ownerSessionId = currentSessionId;
  }
  publish();
}
export function getCurrentAccountId(): string | null { return currentAccountId; }
export function registerWork(key: string, state: WorkState): () => void {
  const owned = { ...state, ownerSessionId: currentSessionId };
  work.set(key, owned);
  publish();
  return () => {
    if (work.get(key) === owned) work.delete(key);
    publish();
  };
}
export function updateWork(key: string, state: WorkState): void { registerWork(key, state); }
export function hasAccountWork(accountId?: string): boolean {
  return [...work.values()].some((item) =>
    (!accountId || item.accountId === accountId) && (item.dirty || item.inFlight));
}
export function canTransition(): boolean { return !hasAccountWork(); }
export async function canTransitionAcrossTabs(preserveAccountId?: string): Promise<boolean> {
  if (!channel || !locks) return (Boolean(preserveAccountId) && currentAccountId === preserveAccountId) ||
    (currentAccountId === null && canTransition());
  channel.postMessage({ type: 'probe', tabId });
  await new Promise((resolve) => window.setTimeout(resolve, 120));
  for (const otherTabId of knownTabs().filter((id) => id !== tabId)) {
    const state = remote.get(otherTabId);
    if (!state) {
      const closed = await tabClosed(otherTabId);
      if (closed) { writeKnownTabs(knownTabs().filter((id) => id !== otherTabId)); continue; }
      return false;
    }
    if ((state.dirty || state.inFlight) && state.accountId !== preserveAccountId) {
      const closed = await tabClosed(otherTabId);
      if (closed) {
        remote.delete(otherTabId);
        writeKnownTabs(knownTabs().filter((id) => id !== otherTabId));
        continue;
      }
      return false;
    }
    if (Date.now() - state.ackAt <= 250) continue;
    const closed = await tabClosed(otherTabId);
    if (closed) remote.delete(otherTabId);
    else return false;
  }
  return currentAccountId === preserveAccountId || canTransition();
}
async function tabClosed(otherTabId: string): Promise<boolean> {
  if (!locks) return false;
  return new Promise<boolean>((resolve) => {
    void (navigator as Navigator & { locks: { request<T>(
      name: string, options: { ifAvailable: boolean },
      callback: (lock: unknown | null) => T): Promise<T> } }).locks.request(
      'colab-tab-alive:' + otherTabId, { ifAvailable: true },
      (lock) => Boolean(lock),
    ).then(resolve);
  });
}
export async function prepareTransitionAcrossTabs(preserveAccountId?: string): Promise<() => void> {
  if (!channel || !locks) return () => undefined;
  const nonce = crypto.randomUUID();
  const acknowledgements = new Set<string>();
  prepared.set(nonce, acknowledgements);
  channel.postMessage({ type: 'prepare', tabId, nonce, preserveAccountId });
  await new Promise((resolve) => window.setTimeout(resolve, 120));
  const expected: string[] = [];
  for (const otherTabId of knownTabs().filter((id) => id !== tabId)) {
    if (await tabClosed(otherTabId)) {
      remote.delete(otherTabId);
      writeKnownTabs(knownTabs().filter((id) => id !== otherTabId));
    } else {
      expected.push(otherTabId);
    }
  }
  const allPreparedAndStillClean = expected.every((id) => {
    const state = remote.get(id);
    const mayPreserve = preserveAccountId && state?.accountId === preserveAccountId;
    return acknowledgements.has(id) && state && (mayPreserve || (!state.dirty && !state.inFlight));
  });
  const localMayPreserve = preserveAccountId && currentAccountId === preserveAccountId;
  if (!allPreparedAndStillClean || (!localMayPreserve && !canTransition())) {
    channel.postMessage({ type: 'finish', tabId, nonce });
    prepared.delete(nonce);
    throw new Error('다른 탭의 작업 상태를 확인하지 못했습니다.');
  }
  return () => {
    channel.postMessage({ type: 'finish', tabId, nonce });
    prepared.delete(nonce);
  };
}
export function beginTransition(): () => void {
  setTransitionPending(true);
  return () => { setTransitionPending(false); };
}
export function mutationsAllowed(): boolean { return !transitionPending; }
export async function discardAccountWork(accountId: string, ownerSessionId?: string): Promise<void> {
  const entries = [...work.entries()].filter(([, item]) => item.accountId === accountId &&
    (!ownerSessionId || item.ownerSessionId === ownerSessionId));
  for (const [, item] of entries) item.abort?.();
  await Promise.all(entries.map(([, item]) => item.discard?.()));
  for (const [key, item] of entries) if (work.get(key) === item) work.delete(key);
  if (!ownerSessionId || currentSessionId === ownerSessionId) discardDrafts(accountId);
  publish();
}
export async function discardAccountWorkAcrossTabs(
  accountId: string,
  proceedOnUnresponsive: boolean,
): Promise<boolean> {
  const ownerSessionId = currentSessionId;
  await discardAccountWork(accountId, ownerSessionId);
  if (!channel || !locks) return proceedOnUnresponsive;
  const nonce = crypto.randomUUID();
  const acknowledgements = new Set<string>();
  discarded.set(nonce, acknowledgements);
  const expected = knownTabs().filter((id) => id !== tabId);
  channel.postMessage({ type: 'discard', tabId, nonce, accountId, ownerSessionId });
  await new Promise((resolve) => window.setTimeout(resolve, 200));
  discarded.delete(nonce);
  return proceedOnUnresponsive || expected.every((id) => acknowledgements.has(id));
}
window.addEventListener('colab-session-retired', (event) => {
  const retired = (event as CustomEvent<string>).detail;
  for (const [key, item] of work) {
    if (item.ownerSessionId !== retired) continue;
    item.abort?.();
    void item.discard?.();
    if (work.get(key) === item) work.delete(key);
  }
  if (currentSessionId === retired && currentAccountId) discardDrafts(currentAccountId);
  publish();
});
export function resetWorkGuardForTests(): void {
  work.clear(); remote.clear(); setTransitionPending(false); currentAccountId = null; currentSessionId = undefined;
}

/** 모든 폼 표면의 비밀이 아닌 입력을 현재 탭의 메모리 그대로 보호한다. */
export function installDomWorkTracking(): () => void {
  const tracked = new Map<HTMLFormElement, () => void>();
  const mark = (event: Event) => {
    const target = event.target;
    if (!(target instanceof HTMLInputElement ||
      target instanceof HTMLTextAreaElement ||
      target instanceof HTMLSelectElement)) return;
    if (target instanceof HTMLInputElement && target.type === 'password') return;
    const form = target.form;
    if (!form || !currentAccountId || tracked.has(form)) return;
    const release = registerWork('form:' + crypto.randomUUID(), {
      accountId: currentAccountId,
      dirty: true,
      inFlight: false,
    });
    tracked.set(form, release);
  };
  const clear = (event: Event) => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement)) return;
    tracked.get(form)?.();
    tracked.delete(form);
  };
  document.addEventListener('input', mark, true);
  document.addEventListener('change', mark, true);
  document.addEventListener('reset', clear, true);
  const observer = new MutationObserver(() => {
    for (const [form, release] of tracked) {
      if (!form.isConnected) { release(); tracked.delete(form); }
    }
  });
  observer.observe(document.body, { childList: true, subtree: true });
  return () => {
    document.removeEventListener('input', mark, true);
    document.removeEventListener('change', mark, true);
    document.removeEventListener('reset', clear, true);
    observer.disconnect();
    for (const release of tracked.values()) release();
  };
}

export function trackMutation(key: string): () => void {
  if (!currentAccountId) return () => undefined;
  return registerWork('mutation:' + key, {
    accountId: currentAccountId,
    dirty: false,
    inFlight: true,
  });
}
