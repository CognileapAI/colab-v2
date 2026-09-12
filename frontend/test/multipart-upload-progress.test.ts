import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const UPLOAD_ID = '01JYZ9K7WQ3N8V4M2X6C5B0UP1';
const FILE_ID = '01JYZ9K7WQ3N8V4M2X6C5B0FI1';

type Listener = (event: Event) => void;

class FakeEventTarget {
  private listeners = new Map<string, Set<Listener>>();
  onprogress: ((event: ProgressEvent) => void) | null = null;

  addEventListener(type: string, listener: EventListenerOrEventListenerObject | null) {
    if (!listener) return;
    const callback: Listener = typeof listener === 'function'
      ? listener
      : (event) => listener.handleEvent(event);
    const listeners = this.listeners.get(type) ?? new Set<Listener>();
    listeners.add(callback);
    this.listeners.set(type, listeners);
  }

  removeEventListener(type: string, listener: EventListenerOrEventListenerObject | null) {
    if (!listener) return;
    const listeners = this.listeners.get(type);
    if (typeof listener === 'function') listeners?.delete(listener);
  }

  dispatch(type: string, event: Event = new Event(type)) {
    if (type === 'progress') this.onprogress?.(event as ProgressEvent);
    for (const listener of [...(this.listeners.get(type) ?? [])]) listener(event);
  }

  listenerCount() {
    return (this.onprogress ? 1 : 0)
      + [...this.listeners.values()].reduce((sum, listeners) => sum + listeners.size, 0);
  }
}

class FakeXhr extends FakeEventTarget {
  static instances: FakeXhr[] = [];

  readonly upload = new FakeEventTarget();
  method = '';
  url = '';
  requestHeaders: [string, string][] = [];
  sentBody: Document | XMLHttpRequestBodyInit | null | undefined;
  response: string | null = null;
  responseType: XMLHttpRequestResponseType = '';
  status = 0;
  statusText = '';
  responseHeaders = '';
  abortCalls = 0;

  constructor() {
    super();
    FakeXhr.instances.push(this);
  }

  open(method: string, url: string) {
    this.method = method;
    this.url = url;
  }

  setRequestHeader(name: string, value: string) {
    this.requestHeaders.push([name, value]);
  }

  send(body?: Document | XMLHttpRequestBodyInit | null) {
    this.sentBody = body;
  }

  abort() {
    this.abortCalls += 1;
    this.dispatch('abort');
  }

  getAllResponseHeaders() {
    return this.responseHeaders;
  }

  progress(loaded: number, total: number, lengthComputable = true) {
    this.upload.dispatch('progress', new ProgressEvent('progress', { loaded, total, lengthComputable }));
  }

  respond(status: number, body: unknown) {
    this.status = status;
    this.statusText = status === 201 ? 'Created' : 'Error';
    this.responseHeaders = 'content-type: application/json\r\nx-test: multipart\r\n';
    // jsdom Blob과 Node Response는 서로 다른 realm이라 BodyInit 호환이 아니다.
    // XHR이 돌려준 JSON bytes라는 계약만 재현하도록 문자열 body를 쓴다.
    this.response = JSON.stringify(body);
    this.dispatch('load');
  }

  failNetwork() {
    this.dispatch('error');
  }
}

function receipt() {
  return {
    uploadId: UPLOAD_ID,
    files: [{
      fileId: FILE_ID,
      fileName: 'a.nc',
      kind: '본체',
      byteSize: 3,
    }],
  };
}

function installXhr() {
  FakeXhr.instances = [];
  vi.stubGlobal('XMLHttpRequest', FakeXhr);
}

function installControlPlane(routes: { incomplete501?: boolean } = {}) {
  const calls: string[] = [];
  vi.stubGlobal('fetch', vi.fn(async (request: Request) => {
    const path = new URL(request.url).pathname.replace('/api/v1', '');
    calls.push(`${request.method} ${path}`);
    if (path === '/uploads/transfers/incomplete' && routes.incomplete501) {
      return new Response(JSON.stringify({ code: 'NOT_IMPLEMENTED' }), {
        status: 501,
        headers: { 'content-type': 'application/json' },
      });
    }
    if (path === '/uploads/transfers' && request.method === 'POST') {
      return new Response(JSON.stringify({ code: 'NOT_IMPLEMENTED' }), {
        status: 501,
        headers: { 'content-type': 'application/json' },
      });
    }
    throw new Error(`multipart POST가 fetch로 새면 안 된다: ${request.method} ${path}`);
  }));
  return calls;
}

async function nextXhr() {
  await vi.waitFor(() => expect(FakeXhr.instances).toHaveLength(1));
  return FakeXhr.instances[0]!;
}

beforeEach(async () => {
  const auth = await import('../src/auth/store');
  auth.setSession({
    token: 'upload-test-token',
    sessionId: '01JYZ9K7WQ3N8V4M2X6C5B0SS1',
    expiresAt: '2099-01-01T00:00:00Z',
    revocationToken: 'upload-test-revocation',
  });
});

afterEach(() => {
  vi.unstubAllGlobals();
  window.localStorage.clear();
  vi.resetModules();
});

describe('local multipart 업로드 진행률 배선', () => {
  it('초기 프리사인드 계획이 501이면 같은 create에서 multipart XHR로 폴백한다', async () => {
    installXhr();
    const calls = installControlPlane();
    const { apiUploadSource } = await import('../src/components/upload/uploadSource');

    const created = apiUploadSource().create([{ file: new File(['abc'], 'a.nc'), kind: '본체' }]);
    const xhr = await nextXhr();
    expect(calls).toEqual(['POST /uploads/transfers']);
    expect(xhr.method).toBe('POST');
    expect(new URL(xhr.url).pathname).toBe('/api/v1/uploads');

    xhr.respond(201, receipt());
    await expect(created).resolves.toEqual(receipt());
  });

  it('미완결 조회가 501이면 계획을 다시 두드리지 않고 multipart XHR로 간다', async () => {
    installXhr();
    const calls = installControlPlane({ incomplete501: true });
    const { apiUploadSource } = await import('../src/components/upload/uploadSource');
    const source = apiUploadSource();

    await expect(source.incomplete!()).resolves.toEqual([]);
    const created = source.create([{ file: new File(['abc'], 'a.nc'), kind: '본체' }]);
    const xhr = await nextXhr();
    expect(calls).toEqual(['GET /uploads/transfers/incomplete']);

    xhr.respond(201, receipt());
    await expect(created).resolves.toEqual(receipt());
  });

  it('파일명·배열 순서와 auth는 보존하고 Request의 Content-Type은 복사하지 않는다', async () => {
    installXhr();
    installControlPlane();
    const { setSession } = await import('../src/auth/store');
    const { sessionFixture } = await import('./sessionFixture');
    const { apiUploadSource } = await import('../src/components/upload/uploadSource');
    setSession(sessionFixture('staging-token'));

    const created = apiUploadSource().create([
      { file: new File(['a'], 'a.nc'), kind: '본체', relativePath: '2025/a.nc' },
      { file: new File(['bb'], 'lat.npy'), kind: '기준 격자 파일' },
    ]);
    const xhr = await nextXhr();
    const form = xhr.sentBody as FormData;
    expect([...form.entries()].map(([key, value]) => [
      key,
      typeof value === 'string' ? value : value.name,
    ])).toEqual([
      ['files', 'a.nc'], ['files', 'lat.npy'],
      ['fileKinds', '본체'], ['fileKinds', '기준 격자 파일'],
      ['relativePaths', '2025/a.nc'], ['relativePaths', ''],
    ]);
    expect(xhr.requestHeaders).toContainEqual(['authorization', 'Bearer staging-token']);
    expect(xhr.requestHeaders.map(([name]) => name.toLowerCase())).not.toContain('content-type');

    xhr.respond(201, receipt());
    await created;
  });

  it('계산 가능한 0→75→100만 전달하고 응답 load 전에는 완료하지 않는다', async () => {
    installXhr();
    installControlPlane();
    const { apiUploadSource } = await import('../src/components/upload/uploadSource');
    const progress = vi.fn();

    let settled = false;
    const created = apiUploadSource().create(
      [{ file: new File(['abc'], 'a.nc'), kind: '본체' }],
      { onProgress: progress },
    ).finally(() => { settled = true; });
    const xhr = await nextXhr();
    expect(progress).not.toHaveBeenCalled();
    xhr.progress(5, 0, true);
    xhr.progress(5, 10, false);
    xhr.progress(0, 100);
    xhr.progress(75, 100);
    xhr.progress(100, 100);
    expect(progress.mock.calls.map(([value]) => value)).toEqual([
      { sentBytes: 0, totalBytes: 100 },
      { sentBytes: 75, totalBytes: 100 },
      { sentBytes: 100, totalBytes: 100 },
    ]);
    await Promise.resolve();
    expect(settled).toBe(false);

    xhr.respond(201, receipt());
    await expect(created).resolves.toEqual(receipt());
  });

  it('401 응답도 기존 응답 미들웨어를 지나 토큰을 지운다', async () => {
    installXhr();
    installControlPlane();
    const auth = await import('../src/auth/store');
    const { sessionFixture } = await import('./sessionFixture');
    const { apiUploadSource } = await import('../src/components/upload/uploadSource');
    auth.setSession(sessionFixture('expired-token'));

    const created = apiUploadSource().create([{ file: new File(['abc'], 'a.nc'), kind: '본체' }]);
    const xhr = await nextXhr();
    xhr.respond(401, { code: 'UNAUTHORIZED' });

    await expect(created).rejects.toThrow('파일을 올리지 못했어요.');
    expect(auth.getToken()).toBeNull();
  });

  it.each([501, 500])('multipart HTTP %i를 성공으로 오인하지 않는다', async (status) => {
    installXhr();
    installControlPlane();
    const { apiUploadSource } = await import('../src/components/upload/uploadSource');
    const { NotImplemented } = await import('../src/components/upload/types');

    const created = apiUploadSource().create([{ file: new File(['abc'], 'a.nc'), kind: '본체' }]);
    const xhr = await nextXhr();
    xhr.respond(status, { code: 'FAILED' });

    const error = await created.catch((caught: unknown) => caught);
    expect(error).toBeInstanceOf(Error);
    if (status === 501) expect(error).toBeInstanceOf(NotImplemented);
    else expect(error).not.toBeInstanceOf(NotImplemented);
  });
});

describe('XHR multipart fetch 어댑터 종료 계약', () => {
  async function start(signal?: AbortSignal) {
    installXhr();
    const module = await import('../src/components/upload/uploadSource');
    const form = new FormData();
    form.append('files', new File(['abc'], 'a.nc'), 'a.nc');
    const request = new Request('https://example.test/api/v1/uploads', {
      method: 'POST',
      headers: {
        authorization: 'Bearer token',
        'content-type': 'multipart/form-data; boundary=request-owned',
        'x-upload-context': 'trace-1',
      },
      body: form,
      ...(signal ? { signal } : {}),
    });
    const progress = vi.fn();
    const response = module.xhrMultipartFetch(request, form, progress);
    return { response, progress };
  }

  it('Content-Type만 제외한 Request 헤더와 최종 201 Response를 보존한다', async () => {
    const { response } = await start();
    const xhr = await nextXhr();
    expect(xhr.requestHeaders).toContainEqual(['authorization', 'Bearer token']);
    expect(xhr.requestHeaders).toContainEqual(['x-upload-context', 'trace-1']);
    expect(xhr.requestHeaders.map(([name]) => name.toLowerCase())).not.toContain('content-type');

    xhr.respond(201, receipt());
    const completed = await response;
    expect(completed.status).toBe(201);
    expect(completed.headers.get('x-test')).toBe('multipart');
    expect(xhr.listenerCount()).toBe(0);
    expect(xhr.upload.listenerCount()).toBe(0);
  });

  it('네트워크 오류는 한 번만 거절하고 모든 XHR listener를 치운다', async () => {
    const { response } = await start();
    const xhr = await nextXhr();
    xhr.failNetwork();
    xhr.failNetwork();

    await expect(response).rejects.toBeInstanceOf(TypeError);
    expect(xhr.listenerCount()).toBe(0);
    expect(xhr.upload.listenerCount()).toBe(0);
  });

  it('이미 취소된 signal은 XHR을 시작하지 않고 AbortError로 거절한다', async () => {
    const controller = new AbortController();
    controller.abort();
    const { response } = await start(controller.signal);

    await expect(response).rejects.toMatchObject({ name: 'AbortError' });
    expect(FakeXhr.instances).toHaveLength(0);
  });

  it('진행 중 signal 취소는 XHR을 한 번 abort하고 listener를 치운다', async () => {
    const controller = new AbortController();
    const { response } = await start(controller.signal);
    const xhr = await nextXhr();
    controller.abort();

    await expect(response).rejects.toMatchObject({ name: 'AbortError' });
    expect(xhr.abortCalls).toBe(1);
    expect(xhr.listenerCount()).toBe(0);
    expect(xhr.upload.listenerCount()).toBe(0);
  });
});
