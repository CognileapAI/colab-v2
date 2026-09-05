/**
 * S-05 데이터셋 상세 — **파일 관리** (`PLAN-SoT §9 〈339〉` · 회의 결정 · 정본 카피 없음).
 *
 * 정본이 못 박은 두 문장은 그대로다 — 「파일」 칸은 `조각 N개 · 합계 MB` 만 말하고,
 * 「목록은 사람이 눌렀을 때 연다」(`Policy_데이터셋_상세 §5`). 나머지 라벨은 `[정본 무근거 · 〈339〉]`.
 *
 * 서버는 아직 이 op 들에 501/409 를 낸다 — 시험은 `FileSource` 스텁으로 계약만 본다.
 * 다운로드는 `<a href>` 가 아니라 **티켓**이다 (`〈339〉-(다)` — Bearer 는 링크에 실리지 않는다).
 * fireEvent 를 쓴다 — user-event 를 새로 들이지 않는다 (집 관례).
 */
import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { DatasetDetailPage } from '../src/routes/DatasetDetailPage';
import { FIXTURE_DETAILS } from '../src/components/detail/fixture';
import { DownloadContext, startDownload } from '../src/components/detail/download';
import { formatFileSize } from '../src/components/detail/format';
import { LastBodyFile } from '../src/components/detail/types';
import type {
  DatasetDetail,
  DatasetFile,
  DetailSource,
  DownloadTicket,
  FileSource,
} from '../src/components/detail/types';
import { SessionProvider } from '../src/permission/session';
import type { PermissionSwitchSet } from '../src/api/client';
import { account } from './factories';

const OPEN_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA1'; // 낙동강 유역 강우 (2025) — 조각 4개
const LOCKED_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA5';
const F1 = '01JYZ9K7WQ3N8V4M2X6C5B0F01'; // 2025/06/nakdong_0601.nc
const F2 = '01JYZ9K7WQ3N8V4M2X6C5B0F02'; // 2025/07/nakdong_0701.nc
const F3 = '01JYZ9K7WQ3N8V4M2X6C5B0F03'; // README.txt — 루트 · 크기 모름
const G1 = '01JYZ9K7WQ3N8V4M2X6C5B0G01'; // lat.npy — 기준 격자 파일
const NEW = '01JYZ9K7WQ3N8V4M2X6C5B0F09';

const MB = 1024 * 1024;

function FILES(): DatasetFile[] {
  return [
    {
      fileId: F1,
      fileName: 'nakdong_0601.nc',
      kind: '본체',
      byteSize: 148 * MB,
      createdAt: '2026-07-30T09:15:00Z',
      relativePath: '2025/06/nakdong_0601.nc',
    },
    {
      fileId: F2,
      fileName: 'nakdong_0701.nc',
      kind: '본체',
      byteSize: 37 * MB,
      createdAt: '2026-07-30T09:15:00Z',
      relativePath: '2025/07/nakdong_0701.nc',
    },
    {
      fileId: F3,
      fileName: 'README.txt',
      kind: '본체',
      byteSize: null, // `d3_file.size_bytes` NULL — 0 이 아니다 (`〈339〉-(가)`)
      createdAt: '2026-08-11T00:00:00Z',
    },
    {
      fileId: G1,
      fileName: 'lat.npy',
      kind: '기준 격자 파일',
      byteSize: 4096,
      createdAt: '2026-08-12T00:00:00Z',
      gridAxis: { carriesLat: true, carriesLon: false },
    },
  ];
}

type Perm = Partial<PermissionSwitchSet>;

/** 조작 가능한 가짜 출처 — 화면이 무엇을 부르는지 세고, 무엇을 돌려줄지 정한다. */
function fakeFiles(
  over: { files?: DatasetFile[]; removeThrows?: unknown; addThrows?: unknown } = {},
) {
  let files = over.files ?? FILES();
  const calls = {
    list: 0,
    tickets: [] as { datasetId: string; fileId: string | undefined }[],
    added: [] as { datasetId: string; name: string; kind: string; relativePath: string | undefined }[],
    replaced: [] as { datasetId: string; fileId: string; name: string }[],
    removed: [] as { datasetId: string; fileId: string }[],
  };
  const source: FileSource = {
    async list() {
      calls.list += 1;
      return files;
    },
    async downloadTicket(datasetId, fileId) {
      calls.tickets.push({ datasetId, fileId });
      const t: DownloadTicket = fileId
        ? { url: `/api/v1/downloads/T-${fileId}`, expiresAt: '2026-08-29T00:10:00Z',
            fileName: files.find((f) => f.fileId === fileId)?.fileName ?? 'f', byteSize: 4, scope: '파일' }
        : { url: '/api/v1/downloads/T-ALL', expiresAt: '2026-08-29T00:10:00Z',
            fileName: '낙동강 유역 강우 (2025).zip', byteSize: null, scope: '묶음' };
      return t;
    },
    async add(datasetId, file, kind, relativePath) {
      calls.added.push({ datasetId, name: file.name, kind, relativePath });
      if (over.addThrows) throw over.addThrows;
      const nf: DatasetFile = {
        fileId: NEW, fileName: file.name, kind, byteSize: file.size,
        createdAt: '2026-08-29T00:00:00Z', ...(relativePath ? { relativePath } : {}),
      };
      files = [...files, nf];
      return nf;
    },
    async replace(datasetId, fileId, file) {
      calls.replaced.push({ datasetId, fileId, name: file.name });
      const cur = files.find((f) => f.fileId === fileId)!;
      const nf: DatasetFile = { ...cur, fileName: file.name, byteSize: file.size };
      files = files.map((f) => (f.fileId === fileId ? nf : f));
      return nf;
    },
    async remove(datasetId, fileId) {
      calls.removed.push({ datasetId, fileId });
      if (over.removeThrows) throw over.removeThrows;
      files = files.filter((f) => f.fileId !== fileId);
    },
  };
  return { source, calls };
}

function detailWith(datasetId: string, canDownload: boolean): DetailSource {
  const base = FIXTURE_DETAILS[datasetId]!;
  const d: DatasetDetail = { ...base, actions: { ...base.actions, canDownload } };
  return { async get() { return d; } };
}

function mount(opts: {
  files: FileSource;
  perm?: Perm;
  canDownload?: boolean;
  datasetId?: string;
}) {
  const downloads: DownloadTicket[] = [];
  const datasetId = opts.datasetId ?? OPEN_ID;
  render(
    <MemoryRouter initialEntries={[`/datasets/${datasetId}`]}>
      <SessionProvider account={account(opts.perm ?? { '업로드·편집': true })}>
        <DownloadContext.Provider value={(t) => { downloads.push(t); }}>
          <Routes>
            <Route
              path="/datasets/:datasetId"
              element={
                <DatasetDetailPage
                  source={detailWith(datasetId, opts.canDownload ?? true)}
                  fileSource={opts.files}
                />
              }
            />
          </Routes>
        </DownloadContext.Provider>
      </SessionProvider>
    </MemoryRouter>,
  );
  return { downloads };
}

async function settle() {
  await screen.findByRole('heading', { level: 1, name: '낙동강 유역 강우 (2025)' });
}

async function click(el: Element | null) {
  fireEvent.click(el as HTMLElement);
  await act(async () => {});
}

async function openList() {
  await click(screen.getByTestId('dt-files-toggle'));
  return screen.findByTestId('dt-files');
}

async function pick(el: Element | null, name: string) {
  fireEvent.change(el as HTMLElement, { target: { files: [new File(['x'], name)] } });
  await act(async () => {});
}

afterEach(() => {
  vi.restoreAllMocks();
});

// ───────────────────────────────────────────────────────────────────────────
describe('§5 목록은 사람이 눌렀을 때 연다', () => {
  it('기본은 접혀 있고, `보기` 전에는 목록 op 을 부르지 않는다', async () => {
    const { source, calls } = fakeFiles();
    mount({ files: source });
    await settle();
    expect(screen.queryByTestId('dt-files')).toBeNull();
    expect(calls.list).toBe(0);
    // 「파일」 칸은 여전히 조각 수와 합계만 말한다
    expect(screen.getByTestId('ig-파일')).toHaveTextContent('조각 4개 · 합계 148 MB');
    await openList();
    expect(calls.list).toBe(1);
  });

  it('토글 낱말은 `파일 관리` 다 — 조각 목록 토글(`보기`)과 겹치지 않는다 (〈346〉)', async () => {
    const { source } = fakeFiles();
    mount({ files: source });
    await settle();
    expect(screen.getByTestId('dt-files-toggle')).toHaveTextContent('파일 관리');
    await openList();
    expect(screen.getByTestId('dt-files-toggle')).toHaveTextContent('접기');
  });

  it('잠긴 상세에는 파일 목록 자리 자체가 없다 (본체 쪽이다 · P-34)', async () => {
    const { source, calls } = fakeFiles();
    mount({ files: source, datasetId: LOCKED_ID });
    await screen.findByRole('heading', { level: 1, name: '낙동강 유역 유출량 (2025)' });
    expect(screen.queryByTestId('dt-files-toggle')).toBeNull();
    expect(screen.queryByTestId('dt-download')).toBeNull();
    expect(calls.list).toBe(0);
  });
});

describe('트리 — 폴더는 경로대로, 경로 없는 파일은 루트, 격자는 따로', () => {
  it('`relativePath` 로 폴더 노드를 세우고 파일을 그 안에 놓는다', async () => {
    const { source } = fakeFiles();
    mount({ files: source });
    await settle();
    const list = await openList();
    const y2025 = within(list).getByTestId('dt-folder-2025');
    const m06 = within(y2025).getByTestId('dt-folder-2025/06');
    expect(within(m06).getByTestId(`dt-file-${F1}`)).toBeInTheDocument();
    expect(within(y2025).getByTestId('dt-folder-2025/07')).toContainElement(
      screen.getByTestId(`dt-file-${F2}`),
    );
  });

  it('경로 없는 파일은 어느 폴더에도 들어가지 않는다', async () => {
    const { source } = fakeFiles();
    mount({ files: source });
    await settle();
    await openList();
    const root = screen.getByTestId(`dt-file-${F3}`);
    expect(root.closest('[data-testid^="dt-folder-"]')).toBeNull();
  });

  it('`기준 격자 파일` 은 별도 묶음에만 있다', async () => {
    const { source } = fakeFiles();
    mount({ files: source });
    await settle();
    await openList();
    const grid = screen.getByTestId('dt-files-grid');
    expect(within(grid).getByTestId(`dt-file-${G1}`)).toBeInTheDocument();
    expect(within(screen.getByTestId('dt-files-body')).queryByTestId(`dt-file-${G1}`)).toBeNull();
  });

  it('격자가 없으면 없다고 적는다 — 목업 문구 `기준 격자 파일 없음`', async () => {
    const { source } = fakeFiles({ files: FILES().filter((f) => f.kind === '본체') });
    mount({ files: source });
    await settle();
    await openList();
    expect(screen.getByTestId('dt-files-grid')).toHaveTextContent('기준 격자 파일 없음');
  });
});

describe('파일별 종류 · 크기 · 시각', () => {
  it('종류는 계약 값 그대로, 크기는 단위 표기, 시각은 날짜다', async () => {
    const { source } = fakeFiles();
    mount({ files: source });
    await settle();
    await openList();
    const f1 = screen.getByTestId(`dt-file-${F1}`);
    expect(f1).toHaveTextContent('nakdong_0601.nc');
    expect(f1).toHaveTextContent('본체');
    expect(f1).toHaveTextContent('148 MB');
    expect(f1).toHaveTextContent('2026-07-30');
    const g1 = screen.getByTestId(`dt-file-${G1}`);
    expect(g1).toHaveTextContent('기준 격자 파일');
    expect(g1).toHaveTextContent('4 KB');
  });

  it('크기를 모르면 `모름` — 0 B 도 `—` 도 아니다', async () => {
    const { source } = fakeFiles();
    mount({ files: source });
    await settle();
    await openList();
    expect(screen.getByTestId(`dt-file-${F3}`)).toHaveTextContent('모름');
    expect(screen.getByTestId(`dt-file-${F3}`).textContent).not.toContain('0 B');
  });

  it('formatFileSize — null 은 `모름`, 0 은 `0 B` (기존 formatBytes 의 `—` 규칙과 갈라 둔다)', () => {
    expect(formatFileSize(null)).toBe('모름');
    expect(formatFileSize(0)).toBe('0 B');
    expect(formatFileSize(4096)).toBe('4 KB');
    expect(formatFileSize(148 * MB)).toBe('148 MB');
    expect(formatFileSize(1.5 * 1024 * MB)).toBe('1.5 GB');
  });
});

describe('다운로드 — 링크가 아니라 티켓이다 (`〈339〉-(다)`)', () => {
  it('행 다운로드는 `downloadTicket(datasetId, fileId)` 를 부르고 그 티켓이 startDownload 로 간다', async () => {
    const { source, calls } = fakeFiles();
    const { downloads } = mount({ files: source });
    await settle();
    await openList();
    await click(screen.getByTestId(`dt-file-download-${F1}`));
    await waitFor(() => expect(downloads).toHaveLength(1));
    expect(calls.tickets).toEqual([{ datasetId: OPEN_ID, fileId: F1 }]);
    expect(downloads[0]!.url).toBe(`/api/v1/downloads/T-${F1}`);
    expect(downloads[0]!.scope).toBe('파일');
  });

  it('묶음 다운로드는 `downloadTicket(datasetId)` — fileId 없이', async () => {
    const { source, calls } = fakeFiles();
    const { downloads } = mount({ files: source });
    await settle();
    await click(screen.getByTestId('dt-download'));
    await waitFor(() => expect(downloads).toHaveLength(1));
    expect(calls.tickets).toEqual([{ datasetId: OPEN_ID, fileId: undefined }]);
    expect(downloads[0]!.scope).toBe('묶음');
  });

  it('`<a href=…/download>` 가 어디에도 없다 — Bearer 는 링크에 실리지 않는다', async () => {
    const { source } = fakeFiles();
    mount({ files: source });
    await settle();
    await openList();
    expect(document.querySelector('a[href*="/download"]')).toBeNull();
  });

  it('`canDownload` 가 꺼지면 묶음·행 다운로드 버튼이 **없다** — 판정은 서버가 한다 (P-7)', async () => {
    const { source } = fakeFiles();
    mount({ files: source, canDownload: false });
    await settle();
    expect(screen.queryByTestId('dt-download')).toBeNull();
    await openList();
    expect(screen.queryByTestId(`dt-file-download-${F1}`)).toBeNull();
  });

  it('startDownload 는 `<a download>` 를 만들어 누른다 — 상대 경로는 현재 오리진, 절대 URL 은 그대로', () => {
    const seen: { href: string; download: string }[] = [];
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (this: HTMLAnchorElement) {
      seen.push({ href: this.href, download: this.download });
    });
    const base: DownloadTicket = {
      url: '/api/v1/downloads/T-1', expiresAt: 'x', fileName: 'a.zip', byteSize: null, scope: '묶음',
    };
    startDownload(base);
    startDownload({ ...base, url: 'https://bucket.s3.example/k?X-Amz-Signature=abc', fileName: 'k.nc', scope: '파일' });
    expect(seen).toEqual([
      { href: `${window.location.origin}/api/v1/downloads/T-1`, download: 'a.zip' },
      { href: 'https://bucket.s3.example/k?X-Amz-Signature=abc', download: 'k.nc' },
    ]);
    // 눌렀던 앵커가 문서에 남지 않는다
    expect(document.querySelector('a[download]')).toBeNull();
  });
});

describe('권한 게이트 — `업로드·편집` 이 꺼지면 추가·교체·삭제가 **숨는다** (P-12)', () => {
  it('꺼진 계정에는 세 조작이 DOM 에 없다', async () => {
    const { source } = fakeFiles();
    mount({ files: source, perm: {} });
    await settle();
    expect(screen.queryByTestId('dt-file-add')).toBeNull();
    await openList();
    expect(screen.queryByTestId(`dt-file-replace-${F1}`)).toBeNull();
    expect(screen.queryByTestId(`dt-file-delete-${F1}`)).toBeNull();
    // 읽기(목록·다운로드)는 그대로다 — 두 축을 섞지 않는다 (P-14)
    expect(screen.getByTestId(`dt-file-download-${F1}`)).toBeInTheDocument();
  });

  it('켜진 계정에는 셋이 있다', async () => {
    const { source } = fakeFiles();
    mount({ files: source });
    await settle();
    expect(screen.getByTestId('dt-file-add')).toBeInTheDocument();
    await openList();
    expect(screen.getByTestId(`dt-file-replace-${F1}`)).toBeInTheDocument();
    expect(screen.getByTestId(`dt-file-delete-${F1}`)).toBeInTheDocument();
  });
});

describe('추가 · 교체 · 삭제 — 성공하면 목록을 서버에게 다시 묻는다', () => {
  it('파일 추가는 `add(datasetId, file, 본체)` — 종류는 본체로 고정이다', async () => {
    const { source, calls } = fakeFiles();
    mount({ files: source });
    await settle();
    await openList();
    await pick(screen.getByTestId('dt-file-add'), 'nakdong_0801.nc');
    await waitFor(() => expect(calls.added).toHaveLength(1));
    expect(calls.added[0]).toEqual({
      datasetId: OPEN_ID, name: 'nakdong_0801.nc', kind: '본체', relativePath: undefined,
    });
    await waitFor(() => expect(calls.list).toBe(2));
    expect(await screen.findByTestId(`dt-file-${NEW}`)).toHaveTextContent('nakdong_0801.nc');
  });

  it('교체는 `replace(datasetId, fileId, file)` 이고 그 뒤 다시 읽는다', async () => {
    const { source, calls } = fakeFiles();
    mount({ files: source });
    await settle();
    await openList();
    await pick(screen.getByTestId(`dt-file-replace-${F1}`), 'nakdong_0601_v2.nc');
    await waitFor(() => expect(calls.replaced).toEqual([
      { datasetId: OPEN_ID, fileId: F1, name: 'nakdong_0601_v2.nc' },
    ]));
    await waitFor(() => expect(calls.list).toBe(2));
    expect(await screen.findByTestId(`dt-file-${F1}`)).toHaveTextContent('nakdong_0601_v2.nc');
  });

  it('삭제는 `remove(datasetId, fileId)` 이고, 다시 읽은 목록에서 그 행이 사라진다', async () => {
    const { source, calls } = fakeFiles();
    mount({ files: source });
    await settle();
    await openList();
    await click(screen.getByTestId(`dt-file-delete-${F3}`));
    await waitFor(() => expect(calls.removed).toEqual([{ datasetId: OPEN_ID, fileId: F3 }]));
    await waitFor(() => expect(calls.list).toBe(2));
    await waitFor(() => expect(screen.queryByTestId(`dt-file-${F3}`)).toBeNull());
    expect(screen.getByTestId(`dt-file-${F1}`)).toBeInTheDocument();
  });

  it('409 (마지막 본체) — 서버 문장을 **그대로** 보여 주고 행은 남는다', async () => {
    const { source, calls } = fakeFiles({
      removeThrows: new LastBodyFile('마지막 본체 파일은 지울 수 없어요. 본체가 하나는 있어야 해요.'),
    });
    mount({ files: source });
    await settle();
    await openList();
    await click(screen.getByTestId(`dt-file-delete-${F1}`));
    const err = await screen.findByTestId('dt-files-error');
    expect(err).toHaveTextContent('마지막 본체 파일은 지울 수 없어요. 본체가 하나는 있어야 해요.');
    expect(err).toHaveAttribute('role', 'alert');
    expect(screen.getByTestId(`dt-file-${F1}`)).toBeInTheDocument();
    // 실패는 재조회를 부르지 않는다 — 실패를 성공처럼 그리지 않는다
    expect(calls.list).toBe(1);
  });
});
