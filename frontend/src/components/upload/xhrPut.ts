// S3 로 나가는 PUT — 반드시 XMLHttpRequest. fetch 는 업로드 진행
// 이벤트가 없다. Blob 을 그대로 보낸다 — FileReader 로 읽으면 메모리가 파일 크기만큼 든다.
// 타임아웃 대신 스톨 감지(30초간 loaded 정지 → abort) — 느린 회선의 정상 전송과
// 죽은 연결을 구분한다. 근거: dev-package/PLAN-SoT.md §9 〈277〉

export type PutFailure = 'network' | 'stall' | 'aborted';

export class PutError extends Error {
  constructor(
    public readonly kind: PutFailure,
    message: string,
  ) {
    super(message);
  }
}

export interface XhrPutOptions {
  onProgress?: (loadedBytes: number) => void;
  stallMs?: number;
  signal?: AbortSignal;
}

/** 성공하면 HTTP 상태 코드를 돌려준다 (403 도 그대로 — 재발급 판단은 호출자 몫). */
export function xhrPut(url: string, body: Blob, opts: XhrPutOptions = {}): Promise<number> {
  const stallMs = opts.stallMs ?? 30_000;
  return new Promise<number>((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    let stallTimer: ReturnType<typeof setTimeout> | undefined;
    let stalled = false;

    const clearStall = () => {
      if (stallTimer !== undefined) clearTimeout(stallTimer);
    };
    const armStall = () => {
      clearStall();
      stallTimer = setTimeout(() => {
        stalled = true;
        xhr.abort();
      }, stallMs);
    };

    xhr.open('PUT', url, true);
    xhr.timeout = 0; // 대용량에 타임아웃을 걸지 않는다 — 스톨 감지가 대신한다
    xhr.upload.onprogress = (e) => {
      armStall();
      if (e.lengthComputable) opts.onProgress?.(e.loaded);
    };
    xhr.onload = () => {
      clearStall();
      resolve(xhr.status);
    };
    xhr.onerror = () => {
      clearStall();
      reject(new PutError('network', 'PUT 네트워크 오류'));
    };
    xhr.onabort = () => {
      clearStall();
      reject(new PutError(stalled ? 'stall' : 'aborted',
        stalled ? '30초간 진행이 없어 중단했다' : '호출자가 중단했다'));
    };
    opts.signal?.addEventListener('abort', () => xhr.abort(), { once: true });
    armStall();
    xhr.send(body);
  });
}
