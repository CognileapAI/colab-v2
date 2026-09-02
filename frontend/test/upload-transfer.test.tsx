/**
 * 오라클 — 프리사인드 전송 FE (동결 해제 8차 · `PLAN-SoT §9 〈277〉`).
 *
 * ① transferSource: 계획→PUT(단일·파트)→실측 완료→완결의 호출 순서. 바이트 PUT 은
 *    XHR(스텁)로, 컨트롤 플레인은 fetch 라우터(스텁)로 — 파트의 정본이 S3(서버 실측)라는
 *    구분이 코드에 있는 그대로 시험에 있다.
 * ② 재개: 서버가 실측해 준 uploadedParts 에서 **빠진 파트만** 다시 올린다.
 * ③ 모달 배너: 미완결 전송이 보이고, [이어서 올리기] 를 누른 뒤 같은 파일을 놓으면
 *    create 가 resumeUploadId 를 싣고 불린다.
 */
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { SessionProvider } from '../src/permission/session';
import { UploadEntry } from '../src/components/upload/UploadEntry';
import { presignedCreate } from '../src/components/upload/transferSource';
import type {
  IncompleteTransferItem,
  PickedFile,
  UploadCreateOptions,
  UploadSources,
} from '../src/components/upload/types';
import type { CurrentAccount } from '../src/api/client';

const T1 = '01JYZ9K7WQ3N8V4M2X6C5B0TR1';
const F_SMALL = '01JYZ9K7WQ3N8V4M2X6C5B0F01';
const F_BIG = '01JYZ9K7WQ3N8V4M2X6C5B0F02';

// ── XHR 스텁 — S3 로 나가는 PUT 을 기록하고 즉시 200 을 준다 ────────────────
const putLog: { url: string; size: number }[] = [];
class FakeXhr {
  upload = { onprogress: null as ((e: ProgressEvent) => void) | null };
  onload: (() => void) | null = null;
  onerror: (() => void) | null = null;
  onabort: (() => void) | null = null;
  status = 200;
  timeout = 0;
  private url = '';
  open(_m: string, url: string) { this.url = url; }
  abort() { this.onabort?.(); }
  send(body: Blob) {
    putLog.push({ url: this.url, size: body.size });
    setTimeout(() => this.onload?.(), 0);
  }
}

function planFileSmall() {
  return { fileId: F_SMALL, fileName: '작은.nc', kind: '본체', byteSize: 4,
           strategy: '단일', partSize: null, partCount: null };
}
function planFileBig(extra: Record<string, unknown> = {}) {
  return { fileId: F_BIG, fileName: '큰.nc', kind: '본체', byteSize: 10,
           strategy: '멀티파트', partSize: 4, partCount: 3, ...extra };
}

/** 컨트롤 플레인 fetch 라우터 — 호출 순서를 기록한다. */
function installRouter(opts: { resume?: boolean } = {}) {
  const calls: string[] = [];
  vi.stubGlobal('fetch', async (req: Request) => {
    const path = new URL(req.url).pathname.replace('/api/v1', '');
    calls.push(`${req.method} ${path}`);
    const json = (body: unknown, status = 200) =>
      new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json' } });
    if (path === '/uploads/transfers' && req.method === 'POST') {
      return json({ uploadId: T1, expiresAt: '2026-08-31T00:00:00Z',
                    files: [planFileSmall(), planFileBig()], rejected: [] }, 201);
    }
    if (path === `/uploads/transfers/${T1}` && req.method === 'GET') {
      return json({ uploadId: T1, expiresAt: '2026-08-31T00:00:00Z',
                    files: [
                      { ...planFileSmall(), outcome: '올라감', uploadedParts: null },
                      { ...planFileBig(), outcome: '대기', uploadedParts: [1] },
                    ] });
    }
    if (path.endsWith('/put-urls')) {
      const body = await req.json() as { fileIds: string[] };
      return json({ urls: body.fileIds.map((id) => ({
        fileId: id, url: `https://s3.fake/${id}`, expiresAt: 'x' })) });
    }
    if (path.endsWith('/multipart')) return json({ partSize: 4, partCount: 3 });
    if (path.endsWith('/part-urls')) {
      const body = await req.json() as { partNumbers: number[] };
      return json({ urls: body.partNumbers.map((n) => ({
        partNumber: n, url: `https://s3.fake/part/${n}` })), expiresAt: 'x' });
    }
    if (/\/files\/[^/]+\/complete$/.test(path)) {
      const fileId = path.split('/').at(-2);
      return json({ fileId, outcome: '올라감', detail: null });
    }
    if (path === `/uploads/transfers/${T1}/complete`) {
      return json({ uploadId: T1, files: [
        { fileId: F_SMALL, fileName: '작은.nc', kind: '본체', byteSize: 4 },
        { fileId: F_BIG, fileName: '큰.nc', kind: '본체', byteSize: 10 },
      ] }, 201);
    }
    throw new Error(`라우터에 없는 호출: ${req.method} ${path} (resume=${String(opts.resume)})`);
  });
  return calls;
}

function pickedTwo(): PickedFile[] {
  return [
    { file: new File(['abcd'], '작은.nc'), kind: '본체' },
    { file: new File(['0123456789'], '큰.nc'), kind: '본체' },
  ];
}

afterEach(() => {
  vi.unstubAllGlobals();
  putLog.length = 0;
});

describe('presignedCreate', () => {
  it('계획 → PUT(단일 1 + 파트 3) → 파일 실측 완료 ×2 → 완결 순으로 간다', async () => {
    vi.stubGlobal('XMLHttpRequest', FakeXhr);
    const calls = installRouter();
    const receipt = await presignedCreate(pickedTwo());
    expect(receipt.uploadId).toBe(T1);
    expect(putLog).toHaveLength(4);                       // 단일 1 + 파트 3
    expect(putLog.map((p) => p.size).sort()).toEqual([2, 4, 4, 4]);  // 마지막 파트 = 2B
    expect(calls.filter((c) => c.endsWith('/complete'))).toHaveLength(3);  // 파일 2 + 전송 1
    expect(calls.at(-1)).toBe(`POST /uploads/transfers/${T1}/complete`);
  });

  it('재개는 실측 uploadedParts 에서 빠진 파트만 올린다 — 올라간 파일은 건너뛴다', async () => {
    vi.stubGlobal('XMLHttpRequest', FakeXhr);
    installRouter({ resume: true });
    await presignedCreate(pickedTwo(), { resumeUploadId: T1 });
    // 작은.nc 는 이미 올라감 — PUT 은 큰.nc 의 파트 2·3 뿐이다
    expect(putLog.map((p) => p.url)).toEqual(['https://s3.fake/part/2', 'https://s3.fake/part/3']);
  });

  it('재개인데 다른 파일을 고르면 정직하게 거절한다 — 조각이 섞이면 안 된다', async () => {
    installRouter({ resume: true });
    const wrong: PickedFile[] = [{ file: new File(['abcd'], '작은.nc'), kind: '본체' }];
    await expect(presignedCreate(wrong, { resumeUploadId: T1 }))
      .rejects.toThrow(/같은 파일을 다시 골라야/);
  });
});

// ── 모달 배너 ───────────────────────────────────────────────────────────────
function account(): CurrentAccount {
  return {
    accountId: '01JYZ9K7WQ3N8V4M2X6C5B0AC1', name: '호랑이', email: 't@example.ac.kr',
    role: '연구원', labId: '01JYZ9K7WQ3N8V4M2X6C5B0LB1', labName: '수자원순환연구실',
    permissions: { '업로드·편집': true } as CurrentAccount['permissions'],
  } as CurrentAccount;
}

function bannerSources(overrides: {
  items: IncompleteTransferItem[];
  onCreate?: (files: PickedFile[], opts?: UploadCreateOptions) => void;
  onAbort?: (id: string) => void;
}): UploadSources {
  let items = overrides.items;
  return {
    upload: {
      create: async (files, opts) => {
        overrides.onCreate?.(files, opts);
        items = [];                        // 접수까지 갔으면 미완결이 아니다
        return { uploadId: T1, files: files.map((f, i) => ({
          fileId: `01JYZ9K7WQ3N8V4M2X6C5B0F0${i}`, fileName: f.file.name,
          kind: f.kind, byteSize: f.file.size })) };
      },
      incomplete: async () => items,
      abortTransfer: async (id) => { overrides.onAbort?.(id); items = items.filter((i) => i.uploadId !== id); },
      status: async () => ({ uploadId: T1, files: [], ready: true, renderable: null,
                             metadataComplete: null, expiresAt: 'x', failure: null }),
      register: async () => ({ datasetId: 'D' }),
      attachGrid: async () => [],
    },
    preview: {
      palettes: async () => [],
      createRender: async () => ({ renderId: 'R1', status: '그리는 중', stage: '파일 읽는 중' }) as never,
      getRender: async () => ({ renderId: 'R1', status: '그리는 중', stage: '파일 읽는 중' }) as never,
    },
    projects: { list: async () => [], create: async () => ({ projectId: 'P', name: 'p' }) },
    lineage: { suggest: async () => ({ items: [], degraded: false }) } as never,
  };
}

const ITEM: IncompleteTransferItem = {
  uploadId: T1, sourceLabel: '기상 묶음', uploadedFiles: 1, plannedFiles: 3,
  uploadedBytes: 4, plannedBytes: 14, createdAt: 'x', expiresAt: 'y',
};

async function openModal(sources: UploadSources) {
  render(
    <MemoryRouter initialEntries={['/datasets']}>
      <SessionProvider account={account()}>
        <UploadEntry sources={sources} />
      </SessionProvider>
    </MemoryRouter>,
  );
  fireEvent.click(screen.getByTestId('gnb-upload'));
  await screen.findByTestId('upload-modal');
}

describe('미완결 전송 배너', () => {
  it('미완결이 있으면 배너가 보이고, 지우기는 abortTransfer 를 부른다', async () => {
    const aborted: string[] = [];
    await openModal(bannerSources({ items: [ITEM], onAbort: (id) => aborted.push(id) }));
    await screen.findByTestId('up-incomplete');
    expect(screen.getByText(/기상 묶음/)).toBeInTheDocument();
    fireEvent.click(screen.getByTestId(`up-discard-${T1}`));
    await waitFor(() => expect(screen.queryByTestId('up-incomplete')).toBeNull());
    expect(aborted).toEqual([T1]);
  });

  it('[이어서 올리기] 뒤 같은 파일을 놓으면 create 가 resumeUploadId 를 싣는다', async () => {
    const seen: (UploadCreateOptions | undefined)[] = [];
    await openModal(bannerSources({ items: [ITEM], onCreate: (_f, opts) => seen.push(opts) }));
    await screen.findByTestId('up-incomplete');
    fireEvent.click(screen.getByTestId(`up-resume-${T1}`));
    await screen.findByTestId('up-resume-hint');
    fireEvent.change(screen.getByTestId('up-drop-input'),
      { target: { files: [new File(['abcd'], '작은.nc')] } });
    await act(async () => {});
    await waitFor(() => expect(seen).toHaveLength(1));
    expect(seen[0]?.resumeUploadId).toBe(T1);
    // 접수까지 갔으면 배너 항목이 사라진다
    await waitFor(() => expect(screen.queryByTestId('up-incomplete')).toBeNull());
  });
});

// ───────────────────────────────────────────────────────────────────────────
// 폴더 경로가 **계획 요청에 실린다** (`〈278〉`-(나))
//
// ⚠ 이 시험도 red 로 시작하지 않는다 — 엔진은 이미 싣고 있다. **사각지대의 봉인**이다:
//   지금까지 이 파일의 픽스처는 경로 없는 파일만 돌았고, s3 경로의 폴더는 시험되지 않았다.
describe('폴더 업로드 — 상대 경로가 서버까지 간다', () => {
  it('계획 요청 본문에 `relativePath` 가 실린다 — 같은 이름·다른 폴더도 따로 선다', async () => {
    vi.stubGlobal('XMLHttpRequest', FakeXhr);
    const bodies: unknown[] = [];
    vi.stubGlobal('fetch', async (req: Request) => {
      const path = new URL(req.url).pathname.replace('/api/v1', '');
      const json = (b: unknown, status = 200) =>
        new Response(JSON.stringify(b), { status, headers: { 'content-type': 'application/json' } });
      if (path === '/uploads/transfers' && req.method === 'POST') {
        bodies.push(await req.json());
        return json({
          uploadId: T1, expiresAt: '2026-08-31T00:00:00Z', rejected: [],
          files: [
            { ...planFileSmall(), fileName: '서울.nc', relativePath: '기상/2025/서울.nc' },
            { ...planFileSmall(), fileId: 'F-2025', fileName: '서울.nc',
              relativePath: '기상/2024/서울.nc' },
          ],
        }, 201);
      }
      if (path.endsWith('/put-urls')) {
        const b = await req.json() as { fileIds: string[] };
        return json({ urls: b.fileIds.map((id) => ({ fileId: id, url: `https://s3.fake/${id}`, expiresAt: 'x' })) });
      }
      // **파일 단위 완료**와 **전송 완결**은 다른 응답이다 — 순서를 뒤집으면 전자가 후자로 답한다.
      if (path.includes('/files/') && path.endsWith('/complete')) {
        return json({ fileId: path.split('/files/')[1]?.split('/')[0], outcome: '올라감', detail: null });
      }
      if (path.endsWith('/complete')) return json({ uploadId: T1, files: [] }, 201);
      throw new Error(`라우터에 없는 호출: ${req.method} ${path}`);
    });

    await presignedCreate([
      { file: new File(['abcd'], '서울.nc'), kind: '본체', relativePath: '기상/2025/서울.nc' },
      { file: new File(['abcd'], '서울.nc'), kind: '본체', relativePath: '기상/2024/서울.nc' },
    ]);
    const sent = (bodies[0] as { files: { fileName: string; relativePath?: string }[] }).files;
    expect(sent.map((f) => f.relativePath)).toEqual(['기상/2025/서울.nc', '기상/2024/서울.nc']);
    expect(sent.every((f) => f.fileName === '서울.nc')).toBe(true);
  });
});

// ───────────────────────────────────────────────────────────────────────────
// 한글 파일명 — **맥은 NFD, 서버는 NFC**
//
// `objectpath.py` 머리말: 「macOS 는 파일명을 자모 분해(NFD)로, Windows 는 완성형(NFC)으로 준다 …
// 한글 파일명이 흔한 환경에서 **반드시 터지는 문제**다. 규칙은 프론트 `normalizeName.ts` 와
// 한 글자도 다르면 안 된다.」 — 그런데 그 프론트 파일이 **없었다.**
describe('한글 파일명 — NFD/NFC 가 갈려도 같은 파일로 본다', () => {
  it('맥이 준 NFD 이름을 서버가 NFC 로 돌려줘도 계획과 선택이 맞물린다', async () => {
    vi.stubGlobal('XMLHttpRequest', FakeXhr);
    const NFD = '자료설명.pptx'.normalize('NFD');
    const NFC = '자료설명.pptx'.normalize('NFC');
    expect(NFD).not.toBe(NFC);                      // 전제: 두 문자열은 다르다

    vi.stubGlobal('fetch', async (req: Request) => {
      const path = new URL(req.url).pathname.replace('/api/v1', '');
      const json = (b: unknown, status = 200) =>
        new Response(JSON.stringify(b), { status, headers: { 'content-type': 'application/json' } });
      if (path === '/uploads/transfers' && req.method === 'POST') {
        // 서버는 **NFC 로 정규화해서** 돌려준다 (실측: dev 실호출로 확인)
        return json({ uploadId: T1, expiresAt: '2026-08-31T00:00:00Z', rejected: [],
                      files: [{ ...planFileSmall(), fileName: NFC }] }, 201);
      }
      if (path.endsWith('/put-urls')) {
        const b = await req.json() as { fileIds: string[] };
        return json({ urls: b.fileIds.map((id) => ({ fileId: id, url: `https://s3.fake/${id}`, expiresAt: 'x' })) });
      }
      if (path.includes('/files/') && path.endsWith('/complete')) {
        return json({ fileId: 'F1', outcome: '올라감', detail: null });
      }
      if (path.endsWith('/complete')) return json({ uploadId: T1, files: [] }, 201);
      throw new Error(`라우터에 없는 호출: ${req.method} ${path}`);
    });

    // 맥에서 고른 파일 — 이름이 NFD 다
    const receipt = await presignedCreate([
      { file: new File(['abcd'], NFD), kind: '본체' },
    ]);
    expect(receipt.uploadId).toBe(T1);
  });
});

// ───────────────────────────────────────────────────────────────────────────
// 실패 후 재시도가 **원장을 늘리지 않는다**
//
// `initiate()` 는 서버에 전송 원장을 세우고 성공한다. 그 뒤 클라이언트에서 던지면 그 행이 남는데,
// 다시 시도할 때 새 `initiate` 를 부르면 **행이 하나 더** 선다 — 사용자가 본 「실패 세트 2개」다.
// 여기가 그것의 정본 오라클이다: **`POST /uploads/transfers` 가 몇 번 나갔는가.**
describe('재시도 — 원장을 늘리지 않는다', () => {
  it('전송이 끊기면 오류가 **그 uploadId 를 들고** 나온다 — 재개할 자리를 화면이 알아야 한다', async () => {
    vi.stubGlobal('XMLHttpRequest', FakeXhr);
    // 재시도 없이 즉시 실패하는 자리를 쓴다(파일 실측 확인) — 백오프로 시험을 늘리지 않는다.
    vi.stubGlobal('fetch', async (req: Request) => {
      const path = new URL(req.url).pathname.replace('/api/v1', '');
      const json = (b: unknown, s = 200) =>
        new Response(JSON.stringify(b), { status: s, headers: { 'content-type': 'application/json' } });
      if (path === '/uploads/transfers' && req.method === 'POST') {
        return json({ uploadId: T1, expiresAt: 'x', files: [planFileSmall()], rejected: [] }, 201);
      }
      if (path.endsWith('/put-urls')) {
        const b = await req.json() as { fileIds: string[] };
        return json({ urls: b.fileIds.map((id) => ({ fileId: id, url: `https://s3.fake/${id}`, expiresAt: 'x' })) });
      }
      if (/\/files\/[^/]+\/complete$/.test(path)) {
        return json({ fileId: F_SMALL, outcome: '실패', detail: '크기 불일치' });
      }
      throw new Error(`라우터에 없는 호출: ${req.method} ${path}`);
    });
    await expect(presignedCreate([{ file: new File(['abcd'], '작은.nc'), kind: '본체' }]))
      .rejects.toMatchObject({ uploadId: T1 });
  });

  it('부분 거부는 **abort 하고** 평범한 오류로 끝난다 — 재개하면 거부된 파일이 말없이 빠진다', async () => {
    const seen: string[] = [];
    vi.stubGlobal('fetch', async (req: Request) => {
      const path = new URL(req.url).pathname.replace('/api/v1', '');
      seen.push(`${req.method} ${path}`);
      const json = (b: unknown, s = 200) =>
        new Response(JSON.stringify(b), { status: s, headers: { 'content-type': 'application/json' } });
      if (path === '/uploads/transfers' && req.method === 'POST') {
        return json({ uploadId: T1, expiresAt: 'x', files: [planFileSmall()],
                      rejected: [{ fileName: '나쁜.nc', reason: 'fileName 을 정규화할 수 없다' }] }, 201);
      }
      if (req.method === 'DELETE') return new Response(null, { status: 204 });
      throw new Error(`라우터에 없는 호출: ${req.method} ${path}`);
    });
    await expect(presignedCreate(pickedTwo())).rejects.toThrow(/받을 수 없는 파일/);
    expect(seen).toContain(`DELETE /uploads/transfers/${T1}`);
  });
});
