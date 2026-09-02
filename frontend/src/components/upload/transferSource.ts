// 프리사인드 전송 오케스트레이션 — 브라우저→S3 직행 (동결 해제 8차 · `PLAN-SoT §9 〈174〉`).
//
// 컨트롤 플레인(계획·URL·검증·완결)은 api 클라이언트로(Bearer 가 붙는다), 바이트 PUT 은
// raw XHR 로(S3 프리사인드 URL 에 Bearer 를 붙이면 서명이 어긋난다 — `client.ts` 미들웨어 우회).
// **파트의 정본은 S3 다** — 재개는 서버가 ListParts 로 실측해 준 `uploadedParts` 에서
// 빠진 파트만 다시 올린다. 저장 모드 local 인 서버는 501 을 내고, 호출자는 그 신호로
// form-data 경로(`createUpload`)에 폴백한다.
import { api } from '../../api/client';
import { MAX_ATTEMPTS, backoffDelay, sleep } from './backoff';
import { Scheduler } from './scheduler';
import { xhrPut } from './xhrPut';
import { NotImplemented, TransferInterrupted, type PickedFile, type UploadReceipt } from './types';
import { normalizeName } from './normalizeName';

export interface TransferProgress {
  sentBytes: number;
  totalBytes: number;
}

export interface TransferOptions {
  sourceLabel?: string;
  /** 미완결 전송을 이어올릴 때 — 같은 파일을 다시 고른 뒤 이 id 로 재개한다. */
  resumeUploadId?: string;
  onProgress?: (p: TransferProgress) => void;
}

interface PlanFile {
  fileId: string;
  fileName: string;
  kind: string;
  byteSize: number;
  relativePath?: string;
  strategy: '단일' | '멀티파트';
  partSize: number | null;
  partCount: number | null;
  outcome?: '대기' | '올라감' | '실패';
  uploadedParts?: number[] | null;
}

/** 계획(서버)과 선택(브라우저)을 맞물리는 열쇠.
 *
 * ⚠ **양쪽을 같은 규칙으로 정규화한다.** 맥은 한글 이름을 NFD 로 주고 서버는 NFC 로 돌려주므로,
 * 정규화 없이는 **같은 파일인데 못 찾는다** — 「계획에 있는 파일이 선택에 없어요」의 정체다.
 * 여기 한 자리만 고치면 계획·재개 조회가 전부 맞물린다(모든 조회가 이 함수를 지난다).
 */
function identity(name: string, relativePath?: string | null): string {
  return normalizeName(relativePath ?? name);
}

async function initiate(picked: PickedFile[], sourceLabel?: string) {
  const r = await api.POST('/uploads/transfers', {
    body: {
      ...(sourceLabel ? { sourceLabel } : {}),
      files: picked.map((p) => ({
        fileName: p.file.name,
        byteSize: p.file.size,
        kind: p.kind,
        ...(p.relativePath ? { relativePath: p.relativePath } : {}),
      })),
    },
  });
  if (r.response.status === 501) throw new NotImplemented();
  if (!r.data) throw new Error('전송 계획을 세우지 못했어요.');
  if (r.data.rejected.length > 0) {
    // ⚠ 서버는 성한 파일이 하나라도 있으면 **201 + 원장**을 낸다. 여기서 그냥 던지면 그 원장이
    //   남아 「실패 세트」가 된다. 그리고 이건 **재개하면 안 되는 실패**다 — 재개는 계획을 그대로
    //   따르므로 **거부된 파일이 말없이 빠진 채 완결된다.** 사람이 다 올렸다고 믿는 것이 더 나쁘다.
    await abortTransfer(r.data.uploadId as string);
    const first = r.data.rejected[0];
    throw new Error(`받을 수 없는 파일이 있어요 — ${first?.fileName}: ${first?.reason}`);
  }
  return r.data;
}

/** 원장을 되돌린다 — S3 조각·객체·행을 서버가 함께 지운다. 실패해도 삼킨다(원래 오류가 더 중요하다). */
async function abortTransfer(uploadId: string): Promise<void> {
  try {
    await api.DELETE('/uploads/transfers/{uploadId}', { params: { path: { uploadId } } });
  } catch {
    /* 정리에 실패해도 사람에게는 원래 실패를 말한다. 72h 뒤 지연 정리가 백스톱이다. */
  }
}

async function resumePlan(uploadId: string, picked: PickedFile[]) {
  const r = await api.GET('/uploads/transfers/{uploadId}', {
    params: { path: { uploadId } },
  });
  if (r.response.status === 501) throw new NotImplemented();
  if (r.response.status === 404) throw new Error('이어올릴 업로드가 더 이상 없어요 — 처음부터 올려 주세요.');
  if (!r.data) throw new Error('전송 상태를 읽지 못했어요.');
  // 같은 파일인지 이름(경로)·크기로 대조한다 — 다른 파일을 이어 붙이면 조각이 섞인다.
  const byIdentity = new Map(picked.map((p) => [identity(p.file.name, p.relativePath), p]));
  for (const f of r.data.files as PlanFile[]) {
    const p = byIdentity.get(identity(f.fileName, f.relativePath));
    if (!p || p.file.size !== f.byteSize) {
      throw new Error(`이어올리려면 같은 파일을 다시 골라야 해요 — 「${f.relativePath ?? f.fileName}」`);
    }
  }
  return r.data;
}

async function putWithRetry(getUrl: () => Promise<string>, body: Blob,
                            onProgress: (loaded: number) => void): Promise<void> {
  for (let attempt = 0; attempt < MAX_ATTEMPTS; attempt += 1) {
    try {
      // URL 은 수명이 짧다 — 매 시도마다 다시 발급받는다 (403 재발급을 겸한다)
      const status = await xhrPut(await getUrl(), body, { onProgress });
      if (status >= 200 && status < 300) return;
    } catch {
      // 네트워크/스톨 — 아래 백오프로
    }
    if (attempt < MAX_ATTEMPTS - 1) await sleep(backoffDelay(attempt));
  }
  throw new Error('여러 번 시도했지만 올리지 못했어요 — 연결을 확인하고 이어올려 주세요.');
}

export async function presignedCreate(picked: PickedFile[],
                                      opts: TransferOptions = {}): Promise<UploadReceipt> {
  const plan = opts.resumeUploadId
    ? await resumePlan(opts.resumeUploadId, picked)
    : await initiate(picked, opts.sourceLabel);
  const uploadId = plan.uploadId as string;
  try {
    return await runTransfer(plan, picked, opts);
  } catch (e) {
    // **원장이 이미 섰다.** 그 전송은 살아 있고 재개할 수 있다 — 화면이 그 사실을 알아야
    // 재시도를 「새로 시작」이 아니라 「이어서」로 보낼 수 있다.
    // 재개(`resumeUploadId`) 중의 실패는 새로 만든 것이 없으므로 감싸지 않는다.
    if (opts.resumeUploadId || e instanceof TransferInterrupted) throw e;
    throw new TransferInterrupted(e instanceof Error ? e.message : '전송이 끊겼어요.', uploadId);
  }
}

/** 본체 — 계획을 받아 바이트를 올리고 완결한다. */
async function runTransfer(plan: { uploadId: string; files: unknown[] },
                           picked: PickedFile[],
                           opts: TransferOptions): Promise<UploadReceipt> {
  const uploadId = plan.uploadId as string;
  const files = plan.files as PlanFile[];
  const byIdentity = new Map(picked.map((p) => [identity(p.file.name, p.relativePath), p]));

  const totalBytes = files.reduce((s, f) => s + f.byteSize, 0);
  let doneBytes = files.filter((f) => f.outcome === '올라감').reduce((s, f) => s + f.byteSize, 0);
  const inflight = new Map<string, number>();
  const report = () => {
    let sent = doneBytes;
    for (const v of inflight.values()) sent += v;
    opts.onProgress?.({ sentBytes: Math.min(sent, totalBytes), totalBytes });
  };

  const completeFile = async (f: PlanFile) => {
    const r = await api.POST('/uploads/transfers/{uploadId}/files/{fileId}/complete', {
      params: { path: { uploadId, fileId: f.fileId } },
    });
    if (!r.data) throw new Error('파일 확인에 실패했어요.');
    if (r.data.outcome !== '올라감') {
      throw new Error(`「${f.fileName}」 — ${r.data.detail ?? '확인에 실패했어요. 다시 올려 주세요.'}`);
    }
  };

  const sendSingle = async (f: PlanFile) => {
    const p = byIdentity.get(identity(f.fileName, f.relativePath));
    if (!p) throw new Error(`계획에 있는 파일이 선택에 없어요 — 「${f.fileName}」`);
    await putWithRetry(async () => {
      const r = await api.POST('/uploads/transfers/{uploadId}/put-urls', {
        params: { path: { uploadId } }, body: { fileIds: [f.fileId] },
      });
      const url = r.data?.urls[0]?.url;
      if (!url) throw new Error('전송 URL 을 받지 못했어요.');
      return url;
    }, p.file, (loaded) => { inflight.set(f.fileId, loaded); report(); });
    inflight.delete(f.fileId);
    doneBytes += f.byteSize;
    report();
    await completeFile(f);
  };

  const sendMultipart = async (f: PlanFile) => {
    const p = byIdentity.get(identity(f.fileName, f.relativePath));
    if (!p) throw new Error(`계획에 있는 파일이 선택에 없어요 — 「${f.fileName}」`);
    const init = await api.POST('/uploads/transfers/{uploadId}/files/{fileId}/multipart', {
      params: { path: { uploadId, fileId: f.fileId } },
    });
    if (!init.data) throw new Error('멀티파트를 시작하지 못했어요.');
    const partSize = init.data.partSize;
    const partCount = init.data.partCount;
    const already = new Set(f.uploadedParts ?? []);
    let uploadedBytes = 0;
    for (const n of already) {
      uploadedBytes += n === partCount ? f.byteSize - partSize * (partCount - 1) : partSize;
    }
    doneBytes += uploadedBytes;
    report();
    const missing = Array.from({ length: partCount }, (_v, i) => i + 1)
      .filter((n) => !already.has(n));
    for (let i = 0; i < missing.length; i += 16) {
      const batch = missing.slice(i, i + 16);
      const urls = await api.POST('/uploads/transfers/{uploadId}/files/{fileId}/part-urls', {
        params: { path: { uploadId, fileId: f.fileId } }, body: { partNumbers: batch },
      });
      const byNumber = new Map((urls.data?.urls ?? []).map((u) => [u.partNumber, u.url]));
      for (const n of batch) {
        const slice = p.file.slice(partSize * (n - 1), Math.min(partSize * n, f.byteSize));
        const key = `${f.fileId}:${n}`;
        await putWithRetry(async () => {
          const url = byNumber.get(n);
          if (url) { byNumber.delete(n); return url; }  // 첫 시도는 배치 URL, 재시도는 재발급
          const r = await api.POST('/uploads/transfers/{uploadId}/files/{fileId}/part-urls', {
            params: { path: { uploadId, fileId: f.fileId } }, body: { partNumbers: [n] },
          });
          const fresh = r.data?.urls[0]?.url;
          if (!fresh) throw new Error('파트 URL 을 받지 못했어요.');
          return fresh;
        }, slice, (loaded) => { inflight.set(key, loaded); report(); });
        inflight.delete(key);
        doneBytes += slice.size;
        report();
      }
    }
    await completeFile(f);
  };

  const sched = new Scheduler();
  await Promise.all(files
    .filter((f) => f.outcome !== '올라감')
    .map((f) => sched.run(
      () => (f.strategy === '멀티파트' ? sendMultipart(f) : sendSingle(f)),
      { multipart: f.strategy === '멀티파트' },
    )));

  const done = await api.POST('/uploads/transfers/{uploadId}/complete', {
    params: { path: { uploadId } },
  });
  if (!done.data) throw new Error('업로드를 접수하지 못했어요.');
  return done.data;
}
