import { getSession, getToken, subscribe } from './store';

export async function sessionBoundFetch(
  request: Request,
  transport: (request: Request) => Promise<Response> = (next) => globalThis.fetch(next),
): Promise<Response> {
  const session = getSession();
  const token = getToken();
  if (!session || !token) throw new Error('로그인 상태를 다시 확인해 주세요.');
  const controller = new AbortController();
  const abort = () => controller.abort();
  request.signal.addEventListener('abort', abort, { once: true });
  const unsubscribe = subscribe(() => {
    const current = getSession();
    if (!current || current.sessionId !== session.sessionId || getToken() !== token) abort();
  });
  try {
    return await transport(new Request(request, { signal: controller.signal }));
  } finally {
    unsubscribe();
    request.signal.removeEventListener('abort', abort);
  }
}
