/**
 * S-04 업로드 전체화면 모달 — 정본 대비 시험.
 * 오라클 = `E-04_업로드와_계보_확정/documents/Policy_업로드와_계보_확정.md` (v2.4) §7 · §8 · §9 와 그 목업.
 * 화면 글자는 정본에서 그대로 온다 — 여기서 새 한국어 라벨을 만들지 않는다.
 *
 * ③ 계보 확정은 이 레인이 아니다 (`P2-EXEC §3` — `P2-fe-lineage`, W4).
 * 여기서는 **③ 이 얹힐 자리(슬롯)** 가 골격에 있는지까지만 본다.
 *
 * fireEvent 를 쓴다 — user-event 를 새로 들이지 않는다(집 관례, `test/members.test.tsx`).
 */
import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter, useLocation } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { SessionProvider } from '../src/permission/session';
import { UploadEntry } from '../src/components/upload/UploadEntry';
import { PREVIEW_STATE_KEY, previewPath } from '../src/components/preview/handoff';
import type { PreviewHandoff } from '../src/components/preview/types';
import { UploadGone } from '../src/components/upload/types';
import type {
  LineageStepContext,
  PreviewSource,
  ProjectSource,
  UploadSource,
  UploadSources,
} from '../src/components/upload/types';
import type {
  DatasetRow,
  LineageSource,
  LineageSuggestionResponse,
} from '../src/components/lineage/types';
import type { CurrentAccount, Schemas } from '../src/api/client';

const UPLOAD_ID = '01JYZ9K7WQ3N8V4M2X6C5B0UP1';
const FILE_ID = '01JYZ9K7WQ3N8V4M2X6C5B0FI1';
const FILE_ID2 = '01JYZ9K7WQ3N8V4M2X6C5B0FI2';
const RENDER_ID = '01JYZ9K7WQ3N8V4M2X6C5B0RE1';
const DATASET_ID = '01JYZ9K7WQ3N8V4M2X6C5B0DS1';
const PROJECT_ID = '01JYZ9K7WQ3N8V4M2X6C5B0PR1';
// KWRA 다운스케일 묶음 (`SEED-DATA §4.1`) — 부모 1(NDVI 2 km) + 보조입력 DEM.
// **화면이 이 묶음을 못 담으면 화면이 틀린 것이다** (`P2-EXEC §4`).
const NDVI_ID = '01JYZ9K7WQ3N8V4M2X6C5B0PA1';
const DEM_ID = '01JYZ9K7WQ3N8V4M2X6C5B0PA2';
const SG1 = '01JYZ9K7WQ3N8V4M2X6C5B0SG1';
const SG2 = '01JYZ9K7WQ3N8V4M2X6C5B0SG2';
const SG3 = '01JYZ9K7WQ3N8V4M2X6C5B0SG3';

function catalogRow(datasetId: string, name: string, level: number): DatasetRow {
  return {
    datasetId,
    name,
    fileCount: 1,
    topic: '식생·NDVI',
    processingLevel: level,
    projects: { representative: null, moreCount: 0, names: [] },
    uploader: { accountId: '01JYZ9K7WQ3N8V4M2X6C5B0AC1', name: '호랑이' },
    lastModifiedAt: '2026-08-01T00:00:00Z',
    lineageState: '원천',
    lineageConfirmedAt: null,
    verified: true,
    accessState: '열림',
    bodyAccessible: true,
  } as unknown as DatasetRow;
}

type Perm = Partial<Record<Schemas['PermissionSwitch'], boolean>>;

function account(perm: Perm): CurrentAccount {
  return {
    accountId: '01JYZ9K7WQ3N8V4M2X6C5B0AC1',
    name: '호랑이',
    email: 'tiger@example.ac.kr',
    role: '연구원',
    labId: '01JYZ9K7WQ3N8V4M2X6C5B0LB1',
    labName: '수자원순환연구실',
    permissions: perm as CurrentAccount['permissions'],
  } as CurrentAccount;
}

/** 조작 가능한 가짜 출처 — 화면이 무엇을 부르는지 세고, 무엇을 돌려줄지 정한다. */
function fakes(
  over: {
    status?: Partial<Schemas['UploadStatus']>;
    jobs?: unknown[];
    palettes?: { palette: string; label: string }[];
    projects?: Schemas['ProjectRow'][];
    registerThrows?: unknown;
    attachThrows?: unknown;
    suggestions?: Partial<LineageSuggestionResponse>;
    suggestionsThrows?: unknown;
    candidates?: DatasetRow[];
  } = {},
) {
  const calls = {
    create: 0,
    status: 0,
    register: 0,
    createRender: [] as Record<string, unknown>[],
    getRender: 0,
    palettes: 0,
    listProjects: 0,
    createProject: 0,
    registered: [] as Record<string, unknown>[],
    /** 후주입 확정이 실제로 실어 보낸 짝 — **화면이 들고 있던 것**이 이 배열에 남는다. */
    attached: [] as { datasetId: string; uploadId: string }[],
    suggestions: 0,
    suggestionsQuery: [] as Record<string, unknown>[],
    candidates: 0,
  };
  const status: Schemas['UploadStatus'] = {
    uploadId: UPLOAD_ID,
    files: [
      {
        fileId: FILE_ID,
        fileName: 'nakdong_precip_2025_Lv2.nc',
        kind: '본체',
        byteSize: 148_000_000,
      },
    ],
    ready: true,
    renderable: true,
    metadataComplete: true,
    expiresAt: '2026-08-24T00:00:00Z',
    failure: null,
    ...over.status,
  };
  const jobs = over.jobs ?? [
    { renderId: RENDER_ID, status: '그리는 중', stage: '파일 읽는 중' },
    { renderId: RENDER_ID, status: '그리는 중', stage: '지도 그리는 중' },
    { renderId: RENDER_ID, status: '그리는 중', stage: '범례 만드는 중' },
    {
      renderId: RENDER_ID,
      status: '완료',
      result: {
        tileUrlTemplate: 'https://tiles.example/renders/R1/{z}/{x}/{y}.png?sig=ABC.DEF',
        bounds: { west: 127, south: 34, east: 130, north: 38 },
        legend: { palette: 'viridis', classes: [{ color: '#440154', from: 0, to: 120 }] },
      },
    },
  ];
  let jobIdx = 0;

  const upload: UploadSource = {
    async create(files) {
      calls.create += 1;
      return {
        uploadId: UPLOAD_ID,
        files: files.map((f, i) => ({
          fileId: i === 0 ? FILE_ID : FILE_ID2,
          fileName: f.file.name,
          kind: f.kind,
          byteSize: f.file.size,
        })),
      };
    },
    async status() {
      calls.status += 1;
      return status;
    },
    async register(body) {
      calls.register += 1;
      calls.registered.push(body as unknown as Record<string, unknown>);
      if (over.registerThrows) throw over.registerThrows;
      return { datasetId: DATASET_ID };
    },
    async attachGrid(datasetId, uploadId) {
      calls.attached.push({ datasetId, uploadId });
      if (over.attachThrows) throw over.attachThrows;
      return [
        {
          fileId: FILE_ID2,
          fileName: 'lat.npy',
          kind: '기준 격자 파일',
          gridAxis: { carriesLat: true, carriesLon: false },
        },
      ];
    },
  };
  const preview: PreviewSource = {
    async palettes() {
      calls.palettes += 1;
      return (
        over.palettes ?? [
          { palette: 'viridis', label: '비리디스' },
          { palette: 'blues', label: '블루' },
        ]
      );
    },
    async createRender(req) {
      calls.createRender.push(req as unknown as Record<string, unknown>);
      return jobs[0] as never;
    },
    async getRender() {
      calls.getRender += 1;
      const j = jobs[Math.min(jobIdx, jobs.length - 1)];
      jobIdx += 1;
      return j as never;
    },
  };
  const projects: ProjectSource = {
    async list() {
      calls.listProjects += 1;
      return (
        over.projects ?? [
          {
            projectId: PROJECT_ID,
            name: '낙동강 유역 홍수기 강우-유출 응답 분석',
            type: '국가과제',
            status: '진행 중',
            period: null,
            description: null,
            datasetCount: 0,
            verifiedCount: 0,
            unknownLineageCount: 0,
          } as Schemas['ProjectRow'],
        ]
      );
    },
    async create(body) {
      calls.createProject += 1;
      return { projectId: '01JYZ9K7WQ3N8V4M2X6C5B0PR9', name: body.name };
    },
  };
  const lineage: LineageSource = {
    async suggestions(uploadId, q) {
      calls.suggestions += 1;
      calls.suggestionsQuery.push({ uploadId, ...q });
      if (over.suggestionsThrows) throw over.suggestionsThrows;
      return {
        degraded: false,
        scope: {
          labId: '01JYZ9K7WQ3N8V4M2X6C5B0LB1',
          labName: '수자원순환연구실',
          searchedCount: 12,
        },
        rawDataLikely: false,
        suggestions: [],
        ...over.suggestions,
      } as LineageSuggestionResponse;
    },
    async candidates() {
      calls.candidates += 1;
      return (
        over.candidates ?? [
          catalogRow(NDVI_ID, 'KWRA NDVI 2 km 일별', 0),
          catalogRow(DEM_ID, 'SRTM DEM 30 m', 0),
        ]
      );
    },
  };
  return { sources: { upload, preview, projects, lineage } as UploadSources, calls };
}

/** KWRA 묶음의 제안 응답 — 부모 후보 2건(주입력 NDVI · 보조입력 DEM) + 가공 방식 1건. */
function kwraSuggestions(): Partial<LineageSuggestionResponse> {
  return {
    rawDataLikely: false,
    suggestions: [
      {
        suggestionId: SG1,
        kind: '가공 전 데이터',
        confidence: '확실',
        rationale: '이름과 기간이 겹치고 격자만 다릅니다.',
        parentDatasetId: NDVI_ID,
        parentDatasetName: 'KWRA NDVI 2 km 일별',
        suggestedParentRole: '주입력',
      },
      {
        suggestionId: SG2,
        kind: '가공 전 데이터',
        confidence: '애매',
        rationale: '고도 보정에 쓰였을 수 있습니다.',
        parentDatasetId: DEM_ID,
        parentDatasetName: 'SRTM DEM 30 m',
        suggestedParentRole: '보조입력',
      },
      {
        suggestionId: SG3,
        kind: '가공 방식',
        confidence: '모름',
        rationale: '파일 이름에 보간 방식이 적혀 있지 않습니다.',
        methodText: 'Co-Kriging 으로 250 m 다운스케일',
        appliesToParentDatasetId: NDVI_ID,
      },
    ],
  } as Partial<LineageSuggestionResponse>;
}

function makeFile(name: string, size = 148_000_000) {
  const f = new File(['x'], name, { type: 'application/octet-stream' });
  Object.defineProperty(f, 'size', { value: size });
  return f;
}

async function click(el: Element | null) {
  fireEvent.click(el as HTMLElement);
  await act(async () => {});
}

async function change(el: Element | null, value: string) {
  fireEvent.change(el as HTMLElement, { target: { value } });
  await act(async () => {});
}

function mount(opts: {
  sources: UploadSources;
  perm?: Perm | undefined;
  lineageStep?: ((ctx: LineageStepContext) => React.ReactNode) | undefined;
}) {
  return render(
    <MemoryRouter initialEntries={['/datasets']}>
      <SessionProvider account={account(opts.perm ?? { '업로드·편집': true })}>
        <UploadEntry sources={opts.sources} lineageStep={opts.lineageStep} />
      </SessionProvider>
    </MemoryRouter>,
  );
}

async function openModal(sources: UploadSources, perm?: Perm) {
  mount({ sources, perm });
  await click(screen.getByTestId('gnb-upload'));
  await screen.findByTestId('upload-modal');
}

async function dropFiles(files: File[]) {
  const input = screen.getByTestId('up-drop-input');
  fireEvent.change(input, { target: { files } });
  await act(async () => {});
  await screen.findByTestId('up-files');
}

async function openRegister() {
  await click(await screen.findByTestId('reg-open'));
  await screen.findByTestId('reg-steps');
}

const stepBtn = (n: '①' | '②' | '③') => screen.getByRole('button', { name: new RegExp(`^${n}`) });

// ───────────────────────────────────────────────────────────────────────────
describe('§8 업로드 모달 — 전체 화면이고 뒤 화면은 문맥으로 남는다', () => {
  it('업로드 버튼을 누르면 전체 화면 모달이 뜬다', async () => {
    const { sources } = fakes();
    await openModal(sources);
    const modal = screen.getByTestId('upload-modal');
    expect(modal).toHaveAttribute('role', 'dialog');
    expect(modal).toHaveAttribute('aria-modal', 'true');
  });

  it('헤더가 대상 연구실을 글자로 세운다 — `…에 올려요`', async () => {
    const { sources } = fakes();
    await openModal(sources);
    expect(screen.getByTestId('upload-lab')).toHaveTextContent('수자원순환연구실에 올려요');
  });

  it('업로드는 라우트가 아니다 — 주소가 바뀌지 않는다', async () => {
    const { sources } = fakes();
    await openModal(sources);
    expect(screen.getByTestId('upload-modal').closest('a')).toBeNull();
    expect(window.location.pathname).not.toContain('upload');
  });

  it('`업로드·편집` 이 꺼지면 버튼이 **숨는다** — 비활성이 아니다', () => {
    const { sources } = fakes();
    mount({ sources, perm: { '업로드·편집': false } });
    expect(screen.queryByTestId('gnb-upload')).toBeNull();
  });
});

describe('§8 모달 닫기 — 잃을 것이 있을 때만 묻는다', () => {
  it('뷰어만 보던 상태면 확인 없이 바로 닫힌다', async () => {
    const { sources } = fakes();
    await openModal(sources);
    await click(screen.getByTestId('upload-close'));
    expect(screen.queryByTestId('upload-modal')).toBeNull();
  });

  it('등록 단계가 열려 있으면 확인을 받는다 — 정본 문구 그대로', async () => {
    const { sources } = fakes();
    await openModal(sources);
    await dropFiles([makeFile('nakdong_precip_2025_Lv2.nc')]);
    await openRegister();
    await click(screen.getByTestId('upload-close'));
    const confirm = await screen.findByTestId('upload-close-confirm');
    expect(confirm).toHaveTextContent(
      '확인한 계보와 입력한 내용이 사라져요. 데이터셋은 만들어지지 않아요.',
    );
    expect(within(confirm).getByRole('button', { name: '계속 작성' })).toBeInTheDocument();
    expect(within(confirm).getByRole('button', { name: '닫고 나가기' })).toBeInTheDocument();
    expect(screen.getByTestId('upload-modal')).toBeInTheDocument();
  });
});

describe('§8 파일 놓기 — 여러 개 · 조각 요약 · 파일 종류 2값', () => {
  it('여러 개를 한 번에 받는다', async () => {
    const { sources } = fakes();
    await openModal(sources);
    expect(screen.getByTestId('up-drop-input')).toHaveAttribute('multiple');
    expect(screen.getByTestId('up-drop')).toHaveTextContent('여러 개를 한 번에 놓아도 돼요');
    await dropFiles([makeFile('a.nc'), makeFile('b.nc')]);
    expect(screen.getByTestId('up-files')).toBeInTheDocument();
  });

  it('파일 종류는 `본체` / `기준 격자 파일` 두 값이다', async () => {
    const { sources } = fakes();
    await openModal(sources);
    await dropFiles([makeFile('nakdong_precip_2025_Lv2.nc')]);
    const kind = screen.getAllByTestId('up-file-kind')[0] as HTMLSelectElement;
    expect(Array.from(kind.options).map((o) => o.value)).toEqual(['본체', '기준 격자 파일']);
  });

  it('축(위도·경도)을 사람에게 묻지 않는다 — 서버가 파일에서 판별한다', async () => {
    const { sources } = fakes();
    await openModal(sources);
    await dropFiles([makeFile('lat.npy'), makeFile('lon.npy')]);
    expect(screen.queryByTestId('up-file-axis')).toBeNull();
    // 축을 고르게 하는 입력이 화면에 하나도 없다 — 값 목록에도, 라벨에도 없다
    const modal = screen.getByTestId('upload-modal');
    modal.querySelectorAll('option').forEach((o) => {
      expect(['위도', '경도']).not.toContain(o.value);
      expect(['위도', '경도']).not.toContain(o.textContent);
    });
    modal.querySelectorAll('label').forEach((l) => {
      expect(l.textContent ?? '').not.toMatch(/축|위도|경도/);
    });
  });

  it('본체가 여러 건이면 요약 한 줄 + `조각 N` 칩이고 목록은 눌렀을 때만 편다', async () => {
    const { sources } = fakes();
    await openModal(sources);
    await dropFiles([makeFile('g_0000.nc'), makeFile('g_0010.nc'), makeFile('g_0020.nc')]);
    expect(screen.getByTestId('up-bundle')).toHaveTextContent('조각 3');
    expect(screen.queryByTestId('up-slices')).toBeNull();
    await click(screen.getByRole('button', { name: '조각 3개 모두 보기' }));
    expect(screen.getByTestId('up-slices')).toBeInTheDocument();
  });

  it('기준 격자 파일은 본체 목록과 **따로** 세운다', async () => {
    const { sources } = fakes();
    await openModal(sources);
    await dropFiles([makeFile('body.HDF5'), makeFile('GK2A_latlon_grid.HDF5')]);
    // 본체가 둘이라 요약 한 줄로 접혀 있다 — 종류를 바꾸려면 목록을 편다
    await click(screen.getByRole('button', { name: '조각 2개 모두 보기' }));
    const kinds = screen.getAllByTestId('up-file-kind');
    await change(kinds[1] ?? null, '기준 격자 파일');
    const companion = await screen.findByTestId('up-companion');
    expect(companion).toHaveTextContent('기준 격자 파일');
    expect(companion).toHaveTextContent('GK2A_latlon_grid.HDF5');
    expect(within(screen.getByTestId('up-files')).queryByText('GK2A_latlon_grid.HDF5')).toBeNull();
  });
});

describe('§8·§9 기준 격자 없음 — 그릴 수 없는 것과 등록할 수 없는 것은 다르다', () => {
  it('없으면 알리되 등록을 막지 않고 `짝 파일 없이 그려 보기`를 준다', async () => {
    const { sources } = fakes();
    await openModal(sources);
    await dropFiles([makeFile('body.HDF5')]);
    expect(await screen.findByTestId('up-nogrid')).toHaveTextContent(
      '위경도를 담은 짝 파일이 없어요.',
    );
    expect(screen.getByTestId('up-preview-without-grid')).toBeEnabled();
    expect(screen.getByTestId('reg-open')).toBeEnabled();
  });

  it('`짝 파일 없이 그려 보기`가 요청에 `withoutReferenceGrid: true` 를 싣는다', async () => {
    const { sources, calls } = fakes();
    await openModal(sources);
    await dropFiles([makeFile('body.HDF5')]);
    await click(await screen.findByTestId('up-preview-without-grid'));
    await waitFor(() => expect(calls.createRender.length).toBe(1));
    expect(calls.createRender[0]?.withoutReferenceGrid).toBe(true);
  });

  it('격자 파일이 붙어 있으면 그 안내를 세우지 않는다', async () => {
    const { sources } = fakes();
    await openModal(sources);
    await dropFiles([makeFile('body.HDF5'), makeFile('grid.HDF5')]);
    await click(screen.getByRole('button', { name: '조각 2개 모두 보기' }));
    await change(screen.getAllByTestId('up-file-kind')[1] ?? null, '기준 격자 파일');
    await waitFor(() => expect(screen.queryByTestId('up-nogrid')).toBeNull());
  });
});

describe('§8 미리보기 — 서버가 그리고, 진행을 **세 단계**로 말한다', () => {
  it('세 문구가 차례로 흐른다. 한 덩어리 `로딩 중`이 없다', async () => {
    const { sources } = fakes();
    await openModal(sources);
    await dropFiles([makeFile('nakdong_precip_2025_Lv2.nc')]);
    await click(await screen.findByTestId('up-preview-draw'));

    const seen: string[] = [];
    for (const want of ['파일 읽는 중', '지도 그리는 중', '범례 만드는 중']) {
      await waitFor(() =>
        expect(screen.getByTestId('up-preview-stage').textContent).toContain(want),
      );
      seen.push(want);
    }
    expect(seen).toEqual(['파일 읽는 중', '지도 그리는 중', '범례 만드는 중']);
    expect(screen.queryByText('로딩 중')).toBeNull();
    await screen.findByTestId('up-preview-map', undefined, { timeout: 4000 });
  });

  it('진행 안내는 `aria-live=polite`, 오류는 `assertive`', async () => {
    const { sources } = fakes({
      jobs: [
        { renderId: RENDER_ID, status: '그리는 중', stage: '파일 읽는 중' },
        {
          renderId: RENDER_ID,
          status: '실패',
          failure: {
            code: 'RENDER_UNAVAILABLE',
            message: '지금 미리보기를 만들 수 없어요. 잠시 뒤 다시 시도해 주세요.',
          },
        },
      ],
    });
    await openModal(sources);
    await dropFiles([makeFile('a.nc')]);
    await click(await screen.findByTestId('up-preview-draw'));
    expect(screen.getByTestId('up-preview-stage')).toHaveAttribute('aria-live', 'polite');
    const err = await screen.findByTestId('up-preview-error');
    expect(err).toHaveAttribute('aria-live', 'assertive');
    expect(err).toHaveTextContent('지금 미리보기를 만들 수 없어요. 잠시 뒤 다시 시도해 주세요.');
  });

  it('실패는 **200 + `failure`** 다 — HTTP 오류로 판정하지 않는다', async () => {
    const { sources } = fakes({
      jobs: [
        {
          renderId: RENDER_ID,
          status: '실패',
          failure: {
            code: 'RENDER_TIMEOUT',
            message: '그리는 데 너무 오래 걸려요. 조각 하나나 좁은 기간으로 다시 해 보세요.',
          },
        },
      ],
    });
    await openModal(sources);
    await dropFiles([makeFile('a.nc')]);
    await click(await screen.findByTestId('up-preview-draw'));
    expect(await screen.findByTestId('up-preview-error')).toHaveTextContent(
      '그리는 데 너무 오래 걸려요',
    );
    // 그려지지 않아도 등록은 그대로 한다 (§9)
    expect(screen.getByTestId('reg-open')).toBeEnabled();
  });

  it('`stage` 는 `그리는 중` 일 때만 읽는다 — 완료 뒤에는 단계 줄이 사라진다', async () => {
    const { sources } = fakes();
    await openModal(sources);
    await dropFiles([makeFile('a.nc')]);
    await click(await screen.findByTestId('up-preview-draw'));
    await screen.findByTestId('up-preview-map', undefined, { timeout: 4000 });
    expect(screen.queryByTestId('up-preview-stage')).toBeNull();
  });

  it('`partialFailure` 는 실패가 아니다 — 완료로 그리고 안내만 붙인다', async () => {
    const { sources } = fakes({
      jobs: [
        {
          renderId: RENDER_ID,
          status: '완료',
          partialFailure: {
            totalParts: 72,
            renderedParts: 69,
            missingParts: [{ fileName: 'g_0601_0300.HDF5' }],
          },
          result: {
            tileUrlTemplate: 'https://tiles.example/r/{z}/{x}/{y}.png?sig=A',
            bounds: { west: 127, south: 34, east: 130, north: 38 },
            legend: { palette: 'viridis', classes: [] },
          },
        },
      ],
    });
    await openModal(sources);
    await dropFiles([makeFile('a.nc')]);
    await click(await screen.findByTestId('up-preview-draw'));
    await screen.findByTestId('up-preview-map', undefined, { timeout: 4000 });
    expect(screen.queryByTestId('up-preview-error')).toBeNull();
    expect(screen.getByTestId('up-preview-partial')).toHaveTextContent(
      '조각 72개 중 3개를 읽지 못했어요',
    );
    expect(screen.getByTestId('up-preview-partial')).toHaveTextContent('g_0601_0300.HDF5');
  });

  it('타일 주소는 `tileUrlTemplate` 을 그대로 쓴다 — `{z}·{x}·{y}` 만 치환한다', async () => {
    const { sources } = fakes();
    await openModal(sources);
    await dropFiles([makeFile('a.nc')]);
    await click(await screen.findByTestId('up-preview-draw'));
    const img = await screen.findByTestId('up-preview-tile', undefined, { timeout: 4000 });
    expect(img.getAttribute('src')).toBe(
      'https://tiles.example/renders/R1/0/0/0.png?sig=ABC.DEF',
    );
  });

  it('만료된 렌더의 타일은 `401` 로 온다 — 권한 문제가 아니라 **만료**로 다룬다', async () => {
    const { sources } = fakes();
    await openModal(sources);
    await dropFiles([makeFile('a.nc')]);
    await click(await screen.findByTestId('up-preview-draw'));
    const img = await screen.findByTestId('up-preview-tile', undefined, { timeout: 4000 });
    fireEvent.error(img);
    await act(async () => {});
    const expired = await screen.findByTestId('up-preview-expired');
    expect(expired).toHaveTextContent('미리보기를 다시 그려 주세요');
    expect(expired.textContent).not.toContain('권한');
  });

  it('컨트롤은 팔레트와 구간 수 둘뿐이고, 팔레트 값은 **출처에서** 온다 (하드코딩 금지)', async () => {
    const { sources, calls } = fakes({ palettes: [{ palette: 'p-only', label: '하나뿐' }] });
    await openModal(sources);
    await dropFiles([makeFile('a.nc')]);
    const palette = (await screen.findByTestId('up-style-palette')) as HTMLSelectElement;
    await waitFor(() => expect(calls.palettes).toBeGreaterThan(0));
    await waitFor(() =>
      expect(Array.from(palette.options).map((o) => o.value)).toEqual(['p-only']),
    );
    const cls = screen.getByTestId('up-style-classcount') as HTMLInputElement;
    expect(cls.value).toBe('6');
    expect(cls.min).toBe('3');
    expect(cls.max).toBe('9');
    expect(screen.queryByTestId('up-style-kind')).toBeNull();
  });

  it('팔레트 출처가 닿지 않으면 정직하게 알리고 **등록은 막지 않는다**', async () => {
    const { sources } = fakes();
    sources.preview.palettes = async () => {
      throw new Error('no path');
    };
    await openModal(sources);
    await dropFiles([makeFile('a.nc')]);
    expect(await screen.findByTestId('up-preview-error')).toHaveTextContent(
      '지금 미리보기를 만들 수 없어요. 잠시 뒤 다시 시도해 주세요.',
    );
    expect(screen.getByTestId('reg-open')).toBeEnabled();
  });
});

describe('§8 등록 결정 게이트 — 등록이 의무가 아님이 화면에서 읽힌다', () => {
  it('미리보기 아래에 두 행동이 나란히 상시로 있다', async () => {
    const { sources } = fakes();
    await openModal(sources);
    await dropFiles([makeFile('a.nc')]);
    const gate = await screen.findByTestId('reg-gate');
    expect(within(gate).getByTestId('reg-viewonly')).toHaveTextContent('보기만 할게요');
    expect(within(gate).getByTestId('reg-open')).toHaveTextContent('연구실에 등록');
    expect(
      screen.getByTestId('up-preview').compareDocumentPosition(gate) &
        Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
  });

  it('`보기만 할게요` 는 아무것도 등록하지 않는다 — `createDataset` 0회', async () => {
    const { sources, calls } = fakes();
    await openModal(sources);
    await dropFiles([makeFile('a.nc')]);
    await click(await screen.findByTestId('reg-viewonly'));
    expect(calls.register).toBe(0);
    expect(screen.queryByTestId('upload-modal')).toBeNull();
  });
});

describe('§8 등록 3단계 표시기 — ①② 는 이 레인, ③ 은 얹히는 자리', () => {
  it('세 칸이고 한 번에 한 단계만 보인다', async () => {
    const { sources } = fakes();
    await openModal(sources);
    await dropFiles([makeFile('nakdong_precip_2025_Lv2.nc')]);
    await openRegister();
    const steps = screen.getByTestId('reg-steps');
    expect(within(steps).getAllByRole('button', { name: /^[①②③]/ })).toHaveLength(3);
    expect(screen.getByTestId('reg-s1')).toBeInTheDocument();
    expect(screen.queryByTestId('reg-s2')).toBeNull();
    expect(screen.queryByTestId('reg-s3')).toBeNull();
  });

  it('앞 단계를 채웠는지 검사하지 않는다 — 어느 칸이든 눌러서 간다', async () => {
    const { sources } = fakes();
    await openModal(sources);
    await dropFiles([makeFile('a.nc')]);
    await openRegister();
    await click(stepBtn('③'));
    expect(await screen.findByTestId('reg-s3')).toBeInTheDocument();
    expect(screen.queryByTestId('reg-s1')).toBeNull();
  });

  it('앞의 `파일 놓기`·`바로 미리보기` 에는 번호를 붙이지 않는다', async () => {
    const { sources } = fakes();
    await openModal(sources);
    await dropFiles([makeFile('a.nc')]);
    expect(screen.getByTestId('up-drop').textContent).not.toMatch(/[①②③]/);
    expect(screen.getByTestId('up-preview').textContent).not.toMatch(/[①②③]/);
  });

  it('줄 끝에 등록할 파일 이름을 고정한다', async () => {
    const { sources } = fakes();
    await openModal(sources);
    await dropFiles([makeFile('nakdong_precip_2025_Lv2.nc')]);
    await openRegister();
    expect(screen.getByTestId('reg-file')).toHaveTextContent('nakdong_precip_2025_Lv2.nc');
  });

  it('확정할 제안이 0건이면 건수를 붙이지 않고, 1건 이상이면 `0 / 3` 을 붙인다', async () => {
    const { sources } = fakes();
    let ctx: LineageStepContext | null = null;
    mount({
      sources,
      lineageStep: (c) => {
        ctx = c;
        return <div data-testid="fake-lineage">③ 자리</div>;
      },
    });
    await click(screen.getByTestId('gnb-upload'));
    await dropFiles([makeFile('a.nc')]);
    await openRegister();
    await click(stepBtn('③')); // ③ 을 열어야 슬롯이 붙는다
    expect(stepBtn('③').textContent).not.toContain('/');
    await act(async () => {
      ctx!.onLineageProgress({ confirmed: 0, total: 3 });
    });
    await waitFor(() => expect(stepBtn('③')).toHaveTextContent('0 / 3'));
    await act(async () => {
      ctx!.onLineageProgress({ confirmed: 2, total: 3 });
    });
    await waitFor(() => expect(stepBtn('③')).toHaveTextContent('2 / 3'));
  });

  it('③ 자리에 W4 가 얹힌다 — 슬롯이 `uploadId` 와 콜백을 넘긴다', async () => {
    const { sources } = fakes();
    let ctx: LineageStepContext | null = null;
    mount({
      sources,
      lineageStep: (c) => {
        ctx = c;
        return <div data-testid="fake-lineage">③ 자리</div>;
      },
    });
    await click(screen.getByTestId('gnb-upload'));
    await dropFiles([makeFile('a.nc')]);
    await openRegister();
    await click(stepBtn('③'));
    expect(await screen.findByTestId('fake-lineage')).toBeInTheDocument();
    expect(ctx!.uploadId).toBe(UPLOAD_ID);
    expect(typeof ctx!.onLineageProgress).toBe('function');
    expect(typeof ctx!.onLineageParentsChange).toBe('function');
  });

  it('③ 자리는 슬롯이고, 아무도 얹지 않으면 **집 안의 계보 확정**이 들어온다', async () => {
    // `S1-fe`(W3) 이전에는 이 자리가 빈 자리였다. 지금은 `components/lineage/` 가 채운다 —
    // 슬롯 자체는 그대로라 바깥에서 갈아 끼우는 길(위 두 시험)이 남아 있다.
    const { sources } = fakes();
    await openModal(sources);
    await dropFiles([makeFile('a.nc')]);
    await openRegister();
    await click(stepBtn('③'));
    expect(await screen.findByTestId('reg-s3')).toBeInTheDocument();
    const slot = screen.getByTestId('reg-lineage-slot');
    expect(within(slot).getByTestId('lin-step')).toBeInTheDocument();
  });
});

describe('§8 등록 단계 배치 — 미리보기는 등록 내내 접히지 않는다', () => {
  it('등록 카드가 미리보기 **아래로 이어 붙고** 미리보기는 그대로 남는다', async () => {
    const { sources } = fakes();
    await openModal(sources);
    await dropFiles([makeFile('a.nc')]);
    await openRegister();
    const preview = screen.getByTestId('up-preview');
    const reg = screen.getByTestId('reg-area');
    expect(preview).toBeInTheDocument();
    expect(preview.compareDocumentPosition(reg) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(screen.queryByTestId('up-summary-rail')).toBeNull();
  });

  it('단계 이동 — 첫 단계에 `← 이전` 없고 마지막 단계에 `다음 →` 없다', async () => {
    const { sources } = fakes();
    await openModal(sources);
    await dropFiles([makeFile('a.nc')]);
    await openRegister();
    expect(screen.queryByTestId('reg-prev')).toBeNull();
    expect(screen.getByTestId('reg-next')).toBeInTheDocument();
    await click(screen.getByTestId('reg-next'));
    await click(screen.getByTestId('reg-next'));
    expect(screen.queryByTestId('reg-next')).toBeNull();
    expect(screen.getByTestId('reg-prev')).toBeInTheDocument();
  });

  it('`데이터셋 만들기` 는 ③ 에서만 나오고, 그 전에는 그 자리가 `다음 →` 이다', async () => {
    const { sources } = fakes();
    await openModal(sources);
    await dropFiles([makeFile('a.nc')]);
    await openRegister();
    expect(screen.queryByTestId('reg-done')).toBeNull();
    await click(stepBtn('③'));
    expect(await screen.findByTestId('reg-done')).toHaveTextContent('데이터셋 만들기');
  });

  it('`등록 취소` 는 같은 줄 왼쪽 끝에 따로 떨어져 있다', async () => {
    const { sources } = fakes();
    await openModal(sources);
    await dropFiles([makeFile('a.nc')]);
    await openRegister();
    const bar = screen.getByTestId('reg-actions');
    expect(bar.firstElementChild).toBe(screen.getByTestId('reg-cancel'));
    await click(screen.getByTestId('reg-cancel'));
    expect(screen.queryByTestId('reg-area')).toBeNull();
    expect(screen.getByTestId('up-preview')).toBeInTheDocument();
  });
});

describe('§8 ① 자동 메타데이터 확인', () => {
  it('변수·기간·좌표계는 사람이 적는 칸이다 — 자동 칸에 없다 (`VAL-006` · `#62`)', async () => {
    const { sources } = fakes();
    await openModal(sources);
    await dropFiles([makeFile('a.nc')]);
    await openRegister();
    const auto = screen.getByTestId('reg-auto');
    expect(auto).not.toHaveTextContent('변수');
    expect(auto).not.toHaveTextContent('좌표계');
    for (const id of ['reg-variables', 'reg-crs', 'reg-period-start', 'reg-period-end']) {
      expect(screen.getByTestId(id)).not.toHaveAttribute('readonly');
    }
  });

  it('적은 세 값이 등록 요청에 계약 형상으로 실린다 (`#62`)', async () => {
    const { sources, calls } = fakes();
    await openModal(sources);
    await dropFiles([makeFile('a.nc')]);
    await openRegister();
    await change(screen.getByTestId('reg-variables'), ' tp · t2m ');
    await change(screen.getByTestId('reg-crs'), 'EPSG:5179');
    await change(screen.getByTestId('reg-period-start'), '2025-06-01');
    await change(screen.getByTestId('reg-period-end'), '2025-09-30');
    await click(stepBtn('③'));
    await click(await screen.findByTestId('reg-done'));
    await waitFor(() => expect(calls.registered.length).toBe(1));
    const body = calls.registered[0] ?? {};
    expect(body.variables).toEqual(['tp', 't2m']);
    expect(body.crs).toBe('EPSG:5179');
    expect(body.period).toEqual({ start: '2025-06-01T00:00:00Z', end: '2025-09-30T00:00:00Z' });
  });

  it('자동으로 읽은 칸은 읽기 전용 + `자동` 표시다', async () => {
    const { sources } = fakes();
    await openModal(sources);
    await dropFiles([makeFile('nakdong_precip_2025_Lv2.nc')]);
    await openRegister();
    const auto = screen.getByTestId('reg-auto');
    expect(within(auto).getAllByText('자동').length).toBeGreaterThan(0);
    within(auto)
      .getAllByRole('textbox')
      .forEach((i) => expect(i).toHaveAttribute('readonly'));
  });

  it('조각이 여러 건이면 라벨이 `조각 합계`·`조각 합집합` 으로 바뀐다', async () => {
    const { sources } = fakes({
      status: {
        files: [
          { fileId: FILE_ID, fileName: 'g_0000.nc', kind: '본체', byteSize: 100 },
          { fileId: FILE_ID2, fileName: 'g_0010.nc', kind: '본체', byteSize: 100 },
        ],
      },
    });
    await openModal(sources);
    await dropFiles([makeFile('g_0000.nc'), makeFile('g_0010.nc')]);
    await openRegister();
    expect(screen.getByTestId('reg-auto')).toHaveTextContent('조각 합계');
    // ⭑ `#62` — 기간은 자동 칸이 아니라 입력 칸이다. 라벨은 그대로 붙는다.
    expect(screen.getByTestId('reg-s1')).toHaveTextContent('조각 합집합');
  });

  it('가공 단계 칸은 입력 불가이고 `계보를 확정하면 정해져요` 라 적는다', async () => {
    const { sources } = fakes();
    await openModal(sources);
    await dropFiles([makeFile('a.nc')]);
    await openRegister();
    const lv = screen.getByTestId('reg-lv') as HTMLInputElement;
    expect(lv).toHaveAttribute('readonly');
    expect(lv.value).toBe('계보를 확정하면 정해져요');
  });

  it('주제는 고정 4값이고 **미정 상태를 표현할 수 있다**', async () => {
    const { sources } = fakes();
    await openModal(sources);
    await dropFiles([makeFile('a.nc')]);
    await openRegister();
    const topic = screen.getByTestId('reg-topic') as HTMLSelectElement;
    expect(Array.from(topic.options).map((o) => o.value)).toEqual([
      '',
      '강우·강수',
      '식생·NDVI',
      '지형·DEM',
      '토지피복·LULC',
    ]);
    expect(topic.value).toBe('');
  });

  it('데이터셋 이름 기본값은 파일명에서 만든다', async () => {
    const { sources } = fakes();
    await openModal(sources);
    await dropFiles([makeFile('nakdong_precip_2025_Lv2.nc')]);
    await openRegister();
    expect((screen.getByTestId('reg-name') as HTMLInputElement).value).toBe(
      'nakdong_precip_2025_Lv2',
    );
  });

  it('헤더를 못 읽으면 정본 문구로 알리되 등록은 막지 않는다', async () => {
    const { sources } = fakes({ status: { metadataComplete: false } });
    await openModal(sources);
    await dropFiles([makeFile('a.nc')]);
    await openRegister();
    expect(screen.getByTestId('reg-auto-failed')).toHaveTextContent(
      '파일에서 정보를 읽지 못했어요. 기간·좌표계를 직접 적어 주세요.',
    );
    await click(stepBtn('③'));
    expect(await screen.findByTestId('reg-done')).toBeEnabled();
  });
});

describe('§8 ② 소속 프로젝트 지정', () => {
  it('고른 프로젝트가 칩으로 쌓이고 ×로 뺀다. 0건이면 안내가 칩 자리를 대신한다', async () => {
    const { sources } = fakes();
    await openModal(sources);
    await dropFiles([makeFile('a.nc')]);
    await openRegister();
    await click(stepBtn('②'));
    expect(await screen.findByTestId('reg-proj-empty')).toHaveTextContent(
      '아직 고른 프로젝트가 없어요.',
    );
    await change(await screen.findByTestId('reg-proj-select'), PROJECT_ID);
    await click(screen.getByRole('button', { name: '+ 추가' }));
    const chips = await screen.findByTestId('reg-proj-chips');
    expect(chips).toHaveTextContent('낙동강 유역 홍수기 강우-유출 응답 분석');
    await click(within(chips).getByRole('button', { name: /빼기/ }));
    expect(await screen.findByTestId('reg-proj-empty')).toBeInTheDocument();
  });

  it('같은 프로젝트를 두 번 담을 수 없다 — 정본 문구로 알린다', async () => {
    const { sources } = fakes();
    await openModal(sources);
    await dropFiles([makeFile('a.nc')]);
    await openRegister();
    await click(stepBtn('②'));
    await change(await screen.findByTestId('reg-proj-select'), PROJECT_ID);
    await click(screen.getByRole('button', { name: '+ 추가' }));
    await click(screen.getByRole('button', { name: '+ 추가' }));
    expect(await screen.findByTestId('reg-proj-dup')).toHaveTextContent('이미 담은 프로젝트예요');
  });

  it('빠른 생성은 `프로젝트 생성` 이 켜진 사람에게만 보이고 **인라인**이다 (모달을 또 얹지 않는다)', async () => {
    const { sources } = fakes();
    await openModal(sources, { '업로드·편집': true, '프로젝트 생성': true });
    await dropFiles([makeFile('a.nc')]);
    await openRegister();
    await click(stepBtn('②'));
    await click(await screen.findByTestId('reg-proj-quick-open'));
    const form = await screen.findByTestId('reg-proj-quick');
    expect(form.closest('[role="dialog"]')).toBe(screen.getByTestId('upload-modal'));
    expect(screen.getAllByRole('dialog')).toHaveLength(1);
    expect(form).toHaveTextContent('프로젝트 화면에서 나중에 채우면 돼요');
  });

  it('`프로젝트 생성` 이 꺼지면 빠른 생성 버튼 자체를 숨긴다', async () => {
    const { sources } = fakes();
    await openModal(sources, { '업로드·편집': true, '프로젝트 생성': false });
    await dropFiles([makeFile('a.nc')]);
    await openRegister();
    await click(stepBtn('②'));
    await screen.findByTestId('reg-proj-select');
    expect(screen.queryByTestId('reg-proj-quick-open')).toBeNull();
  });

  it('연구실 프로젝트가 0건이면 목록·`+ 추가` 를 끄고 빠른 생성만 남긴다', async () => {
    const { sources } = fakes({ projects: [] });
    await openModal(sources, { '업로드·편집': true, '프로젝트 생성': true });
    await dropFiles([makeFile('a.nc')]);
    await openRegister();
    await click(stepBtn('②'));
    expect(await screen.findByTestId('reg-proj-none')).toHaveTextContent(
      '아직 연구실에 만들어진 프로젝트가 없어요.',
    );
    expect(screen.queryByTestId('reg-proj-select')).toBeNull();
    expect(screen.getByTestId('reg-proj-quick-open')).toBeInTheDocument();
  });
});

describe('§7.1 등록 결정 게이트 전에는 아무것도 저장되지 않는다 (`〈64〉` — D3 카탈로그 기준)', () => {
  it('`데이터셋 만들기` 를 누르기 전까지 `createDataset` 이 한 번도 불리지 않는다', async () => {
    const { sources, calls } = fakes();
    await openModal(sources);
    await dropFiles([makeFile('a.nc')]);
    await click(await screen.findByTestId('up-preview-draw'));
    await screen.findByTestId('up-preview-map', undefined, { timeout: 4000 });
    await openRegister();
    await click(stepBtn('②'));
    await click(stepBtn('③'));
    expect(calls.register).toBe(0);
    await click(await screen.findByTestId('reg-done'));
    await waitFor(() => expect(calls.register).toBe(1));
  });

  it('등록 요청은 사람이 적는 값만 싣는다 — 자동으로 읽은 정보를 싣지 않는다', async () => {
    const { sources, calls } = fakes();
    await openModal(sources);
    await dropFiles([makeFile('nakdong_precip_2025_Lv2.nc')]);
    await openRegister();
    await click(stepBtn('③'));
    await click(await screen.findByTestId('reg-done'));
    await waitFor(() => expect(calls.registered.length).toBe(1));
    const body = calls.registered[0] ?? {};
    expect(body.uploadId).toBe(UPLOAD_ID);
    expect(Object.keys(body).sort()).toEqual(
      ['lineageParents', 'name', 'projectIds', 'sourceLabel', 'summary', 'topic', 'uploadId'].sort(),
    );
    expect(body.topic).toBeNull();
  });

  it('이름이 비면 정본 문구로 막고 등록하지 않는다', async () => {
    const { sources, calls } = fakes();
    await openModal(sources);
    await dropFiles([makeFile('a.nc')]);
    await openRegister();
    await change(screen.getByTestId('reg-name'), '');
    await click(stepBtn('③'));
    await click(await screen.findByTestId('reg-done'));
    expect(await screen.findByTestId('reg-name-error')).toHaveTextContent(
      '데이터셋 이름을 적어 주세요',
    );
    expect(calls.register).toBe(0);
  });

  it('수명이 다한 업로드로 등록하면 정본 문구로 알린다', async () => {
    const { sources } = fakes({ registerThrows: new UploadGone() });
    await openModal(sources);
    await dropFiles([makeFile('a.nc')]);
    await openRegister();
    await click(stepBtn('③'));
    await click(await screen.findByTestId('reg-done'));
    expect(await screen.findByTestId('reg-error')).toHaveTextContent(
      '이 파일은 더 이상 없어요. 다시 올려 주세요.',
    );
  });
});


// ───────────────────────────────────────────────────────────────────────────
// ③ 계보 확정 (`P2-EXEC §4` `P2-fe-lineage` · `CLAUDE.md §3` AI 응답 규격)
//
// 이 화면은 **아무것도 저장하지 않는다.** 확인·수정·거절은 클라이언트 상태이고,
// 사람이 확인한 것만 `createDataset` 의 `lineageParents` 에 실린다.

async function openLineage(sources: UploadSources, perm?: Perm) {
  await openModal(sources, perm);
  await dropFiles([makeFile('nakdong_ndvi_250m.nc')]);
  await openRegister();
  await click(stepBtn('③'));
  await screen.findByTestId('lin-step');
}

/** 마지막 `createDataset` 요청에 실린 계보 관계들. */
function sentParents(calls: { registered: Record<string, unknown>[] }) {
  const last = calls.registered[calls.registered.length - 1] ?? {};
  return (last.lineageParents ?? []) as Record<string, unknown>[];
}

describe('③ 계보 확정 — 뒤진 범위를 먼저 밝힌다', () => {
  it('제안보다 **앞에** 뒤진 범위(연구실·개수)가 선다', async () => {
    const { sources } = fakes({ suggestions: kwraSuggestions() });
    await openLineage(sources);
    const scope = await screen.findByTestId('lin-scope');
    expect(scope).toHaveTextContent('수자원순환연구실');
    expect(scope).toHaveTextContent('12');
    const cards = screen.getByTestId('lin-cards');
    expect(
      scope.compareDocumentPosition(cards) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
  });

  it('이름 초안과 주제를 해석 단서로 넘긴다 — 주제를 안 골랐으면 안 넘긴다', async () => {
    const { sources, calls } = fakes({ suggestions: kwraSuggestions() });
    await openLineage(sources);
    const q = calls.suggestionsQuery[0]!;
    expect(q.uploadId).toBe(UPLOAD_ID);
    expect(q.datasetNameDraft).toBe('nakdong_ndvi_250m');
    expect(q.subject).toBeUndefined();
  });
});

describe('③ 계보 확정 — 정직한 빈 상태 (AI 없이도 완결된다)', () => {
  it('제안 0건이면 억지 카드를 만들지 않고 빈 상태를 말한다', async () => {
    const { sources } = fakes();
    await openLineage(sources);
    expect(await screen.findByTestId('lin-empty')).toBeInTheDocument();
    expect(screen.queryByTestId('lin-card')).toBeNull();
    // 빈 상태여도 범위는 그대로 밝힌다 — 「무엇을 근거로 못 찾았는가」가 빈 상태의 내용이다.
    expect(screen.getByTestId('lin-scope')).toHaveTextContent('수자원순환연구실');
  });

  // ── **0건의 뜻 셋을 가른다** (`PLAN-SoT §9 〈211〉`-㉮-⑵) ────────────────────
  // 제안 기능은 데이터가 없으면 무엇이든 0건이라, **음성 판정이 공짜로 통과한다.**
  // 그래서 「제안이 가능했는데 안 했다」와 「애초에 가능하지 않았다」를 화면에서 가른다.
  it('㈏ 뒤질 대상이 있었고 서비스가 답했는데 0건 — **가능했으나 제안하지 않았다**', async () => {
    const { sources } = fakes({
      suggestions: {
        degraded: false,
        scope: { labId: '01JYZ9K7WQ3N8V4M2X6C5B0LB1', labName: '수자원순환연구실', searchedCount: 12 },
        suggestions: [],
      },
    });
    await openLineage(sources);
    const empty = await screen.findByTestId('lin-empty');
    expect(empty).toHaveAttribute('data-kind', 'searched-none');
    expect(empty).toHaveTextContent('12건을 살펴봤지만');
    expect(empty).toHaveTextContent('찾지 못했어요');
    // 「살펴볼 것이 없었다」로 말하면 거짓이다 — 살펴볼 것은 12건 있었다.
    expect(empty).not.toHaveTextContent('살펴볼 것이 없었어요');
    expect(screen.queryByTestId('lin-degraded')).toBeNull();
  });

  it('㈎ 뒤질 대상이 0건 — **제안이 가능했던 적이 없다**. 「찾지 못했다」로 말하지 않는다', async () => {
    const { sources } = fakes({
      suggestions: {
        degraded: false,
        scope: { labId: '01JYZ9K7WQ3N8V4M2X6C5B0LB1', labName: '수자원순환연구실', searchedCount: 0 },
        suggestions: [],
      },
    });
    await openLineage(sources);
    const empty = await screen.findByTestId('lin-empty');
    expect(empty).toHaveAttribute('data-kind', 'nothing-to-search');
    expect(empty).toHaveTextContent('살펴볼 것이 없었어요');
    expect(empty).not.toHaveTextContent('찾지 못했어요');
    // 범위 줄도 「0건을 살펴봤다」로 거짓말하지 않는다.
    expect(screen.getByTestId('lin-scope')).toHaveTextContent('살펴볼 데이터가 없어요');
  });

  it('㈐ 물어보지 못했다 — 「없다」가 아니라 **모른다**로 적는다', async () => {
    const { sources } = fakes({
      suggestions: {
        degraded: true,
        degradedReason: '계보 제안 서비스에 닿지 못했다',
        scope: { labId: '01JYZ9K7WQ3N8V4M2X6C5B0LB1', labName: '수자원순환연구실', searchedCount: 12 },
        suggestions: [],
      },
    });
    await openLineage(sources);
    const empty = await screen.findByTestId('lin-empty');
    expect(empty).toHaveAttribute('data-kind', 'not-asked');
    expect(empty).toHaveTextContent('확인하지 못했어요');
    expect(empty).not.toHaveTextContent('찾지 못했어요');
  });

  it('제안 0건이어도 등록이 끝까지 간다 — `기록 없음` 으로 등록된다', async () => {
    const { sources, calls } = fakes();
    await openLineage(sources);
    await click(screen.getByTestId('reg-done'));
    expect(calls.register).toBe(1);
    expect(sentParents(calls)).toHaveLength(0);
  });

  it('제안 조회가 실패해도 등록을 막지 않는다 — 못 그리는 것과 못 등록하는 것은 다르다', async () => {
    const { sources, calls } = fakes({ suggestionsThrows: new Error('down') });
    await openLineage(sources);
    expect(await screen.findByTestId('lin-unavailable')).toBeInTheDocument();
    await click(screen.getByTestId('reg-done'));
    expect(calls.register).toBe(1);
  });

  it('`degraded` 면 그 사실을 알리고 등록 경로는 그대로 둔다', async () => {
    const { sources } = fakes({
      suggestions: { degraded: true, degradedReason: 'ai timeout', suggestions: [] },
    });
    await openLineage(sources);
    expect(await screen.findByTestId('lin-degraded')).toBeInTheDocument();
    // core 가 정할 문구를 화면이 그대로 옮기지 않는다 (`core-ai.yaml Degradable`).
    expect(screen.getByTestId('lin-step').textContent).not.toContain('ai timeout');
    expect(screen.getByTestId('lin-add')).toBeEnabled();
  });

  it('`rawDataLikely` 면 원천 표기만 적고 등록하도록 안내한다', async () => {
    const { sources } = fakes({ suggestions: { rawDataLikely: true, suggestions: [] } });
    await openLineage(sources);
    expect(await screen.findByTestId('lin-raw')).toBeInTheDocument();
  });
});

describe('③ 계보 확정 — AI 응답 규격 (`CLAUDE.md §3`)', () => {
  it('**[모두 승인] 이 없다** — 확인은 항목마다 받는다', async () => {
    const { sources } = fakes({ suggestions: kwraSuggestions() });
    await openLineage(sources);
    await screen.findByTestId('lin-cards');
    expect(screen.queryByText(/모두 승인|전체 승인|일괄/)).toBeNull();
    expect(screen.getAllByTestId('lin-confirm')).toHaveLength(3);
  });

  it('확신도는 3값 enum 이고 **퍼센트·점수가 없다**. 근거는 한 줄로 반드시 붙는다', async () => {
    const { sources } = fakes({ suggestions: kwraSuggestions() });
    await openLineage(sources);
    const chips = await screen.findAllByTestId('lin-confidence');
    expect(chips.map((c) => c.textContent)).toEqual(['확실', '애매', '모름']);
    expect(screen.getByTestId('lin-step').textContent).not.toMatch(/\d+\s*%/);
    const reasons = screen.getAllByTestId('lin-rationale');
    expect(reasons).toHaveLength(3);
    for (const r of reasons) {
      expect(r.textContent?.trim().length).toBeGreaterThan(0);
      expect(r.textContent).not.toContain('\n');
    }
  });
});

describe('③ 계보 확정 — 확인 / 수정 / 거절', () => {
  it('확인한 것만 등록 요청에 실리고, 경로는 `ai` 이다', async () => {
    const { sources, calls } = fakes({ suggestions: kwraSuggestions() });
    await openLineage(sources);
    const cards = await screen.findAllByTestId('lin-card');
    await click(within(cards[0]!).getByTestId('lin-confirm'));
    await click(screen.getByTestId('reg-done'));
    const parents = sentParents(calls);
    expect(parents).toHaveLength(1);
    expect(parents[0]!.parentDatasetId).toBe(NDVI_ID);
    expect(parents[0]!.origin).toBe('ai');
  });

  it('거절한 것은 카드에서 빠지고 아무것도 실리지 않는다', async () => {
    const { sources, calls } = fakes({ suggestions: kwraSuggestions() });
    await openLineage(sources);
    const cards = await screen.findAllByTestId('lin-card');
    await click(within(cards[0]!).getByTestId('lin-reject'));
    expect(screen.queryAllByTestId('lin-card')).toHaveLength(1);
    await click(screen.getByTestId('reg-done'));
    expect(sentParents(calls)).toHaveLength(0);
  });

  it('**수정하면 AI 행동이 아니다** — 확신도 칩이 걷히고 경로가 `직접` 이 되며 확인을 다시 받는다', async () => {
    const { sources, calls } = fakes({ suggestions: kwraSuggestions() });
    await openLineage(sources);
    const cards = await screen.findAllByTestId('lin-card');
    const card = cards[0]!;
    expect(within(card).getByTestId('lin-confidence')).toBeInTheDocument();
    await click(within(card).getByTestId('lin-confirm'));
    await click(within(card).getByTestId('lin-edit'));
    // 고른 대상을 바꾼다 — 그 순간 이 관계는 사람이 만든 것이다.
    await click(await within(card).findByTestId(`lin-pick-${DEM_ID}`));
    expect(within(card).queryByTestId('lin-confidence')).toBeNull();
    // **확인이 풀렸다** — 확정 건수가 1 에서 0 으로 돌아간다. 다시 확인해야 실린다.
    await waitFor(() => expect(stepBtn('③')).toHaveTextContent('0 / 2'));
    expect(within(card).queryByText('확인함')).toBeNull();

    await click(within(card).getByTestId('lin-confirm'));
    await click(screen.getByTestId('reg-done'));
    const parents = sentParents(calls);
    expect(parents).toHaveLength(1);
    expect(parents[0]!.parentDatasetId).toBe(DEM_ID);
    expect(parents[0]!.origin).toBe('manual');
  });
});

describe('③ 계보 확정 — 부모 역할 2값 · 직접 추가 · 가공 방식', () => {
  it('부모 역할은 `주입력`·`보조입력` 둘뿐이고 제안값이 기본으로 선다', async () => {
    const { sources, calls } = fakes({ suggestions: kwraSuggestions() });
    await openLineage(sources);
    const cards = await screen.findAllByTestId('lin-card');
    const roles = within(cards[0]!).getByTestId('lin-role') as HTMLSelectElement;
    expect([...roles.options].map((o) => o.value)).toEqual(['주입력', '보조입력']);
    expect(roles.value).toBe('주입력');
    expect((within(cards[1]!).getByTestId('lin-role') as HTMLSelectElement).value).toBe('보조입력');

    await click(within(cards[0]!).getByTestId('lin-confirm'));
    await click(within(cards[1]!).getByTestId('lin-confirm'));
    await click(screen.getByTestId('reg-done'));
    const parents = sentParents(calls);
    expect(parents).toHaveLength(2);
    expect(parents.map((p) => p.parentRole)).toEqual(['주입력', '보조입력']);
  });

  it('안내가 **정할 수 없는 값**을 설명하지 않는다 — 화면은 부모 역할을 묻지 않는다', async () => {
    // `PLAN-SoT §9 〈139〉`(Ted 2026-08-27) — 부모 역할은 화면에서 묻지 않고 서버 기본값
    // `주입력` 이며, 고치는 자리는 **상세의 계보 수정**이다. 그런데 종전 안내는
    // 「`보조입력` 으로 표시한 부모는…」이라 **표시할 방법이 없는 값을 설명**했다.
    // 사용자는 그 표시를 찾다가 못 찾고, 안 보이는 기능이 있다고 믿는다.
    const { sources } = fakes({ suggestions: kwraSuggestions() });
    await openLineage(sources);
    const note = await screen.findByTestId('lin-lv-note');
    expect(note.textContent).not.toMatch(/보조입력/);
    // Lv 는 파생값이라 등록 뒤 core 가 계산한다 (`PLAN-SoT §9-⑳`) — 여기서 숫자를 짓지 않는다.
    expect(note.textContent).not.toMatch(/Lv\s*\d/);
    // **고칠 수 있다는 사실은 말한다** — `〈127〉` 로 상세에서 고치는 길이 열렸다.
    expect(note).toHaveTextContent('상세');
  });

  it('제안이 0건이어도 **직접 추가**로 계보를 세운다 — 경로는 `manual`', async () => {
    const { sources, calls } = fakes();
    await openLineage(sources);
    await click(await screen.findByTestId('lin-add'));
    await click(await screen.findByTestId(`lin-pick-${NDVI_ID}`));
    const card = await screen.findByTestId('lin-card');
    expect(within(card).queryByTestId('lin-confidence')).toBeNull();
    await click(within(card).getByTestId('lin-confirm'));
    await click(screen.getByTestId('reg-done'));
    const parents = sentParents(calls);
    expect(parents).toHaveLength(1);
    expect(parents[0]!.origin).toBe('manual');
    expect(parents[0]!.parentDatasetId).toBe(NDVI_ID);
  });

  it('가공 방식은 **관계에 붙는다** — 확인하면 그 부모의 `confirmedMethodText` 로 실린다', async () => {
    const { sources, calls } = fakes({ suggestions: kwraSuggestions() });
    await openLineage(sources);
    const cards = await screen.findAllByTestId('lin-card');
    await click(within(cards[0]!).getByTestId('lin-confirm'));
    const method = screen.getByTestId('lin-method-card');
    expect(within(method).getByTestId('lin-method-parent')).toHaveTextContent(
      'KWRA NDVI 2 km 일별',
    );
    await click(within(method).getByTestId('lin-confirm'));
    await click(screen.getByTestId('reg-done'));
    const parents = sentParents(calls);
    expect(parents).toHaveLength(1);
    expect(parents[0]!.confirmedMethodText).toBe('Co-Kriging 으로 250 m 다운스케일');
    // `method` 와 `confirmedMethodText` 가 둘 다 오면 400 이다 — 한 자리로 접힌다.
    expect(parents[0]!.method ?? null).toBeNull();
  });

  it('직접 적은 가공 방식은 `method` 로 실린다 — 제안 확인 자리와 섞이지 않는다', async () => {
    const { sources, calls } = fakes();
    await openLineage(sources);
    await click(await screen.findByTestId('lin-add'));
    await click(await screen.findByTestId(`lin-pick-${NDVI_ID}`));
    const card = await screen.findByTestId('lin-card');
    await change(within(card).getByTestId('lin-method'), 'IDW 로 250 m 다운스케일');
    await click(within(card).getByTestId('lin-confirm'));
    await click(screen.getByTestId('reg-done'));
    const parents = sentParents(calls);
    expect(parents[0]!.method).toBe('IDW 로 250 m 다운스케일');
    expect(parents[0]!.confirmedMethodText ?? null).toBeNull();
  });

  it('확정 건수가 ③ 표시기로 간다 — 0건이면 건수를 붙이지 않는다', async () => {
    const { sources } = fakes({ suggestions: kwraSuggestions() });
    await openLineage(sources);
    await waitFor(() => expect(stepBtn('③')).toHaveTextContent('0 / 2'));
    const cards = screen.getAllByTestId('lin-card');
    await click(within(cards[0]!).getByTestId('lin-confirm'));
    await waitFor(() => expect(stepBtn('③')).toHaveTextContent('1 / 2'));
  });
});

// ───────────────────────────────────────────────────────────────────────────
// `S1-PLAN-REFOUND §E.0-1` — **등록은 미리보기에 인질이 아니다.**
// 격자 흐름이 새 실패 경로를 여럿 만들었으므로, 그 하나하나에서 등록이 살아 있음을 본다.
// (이전에는 이 성질의 실동작 증명이 `test_preview_relay.py:169` **한 건**뿐이었다.)
describe('§E.0-1 그릴 수 없는 것과 등록할 수 없는 것은 다르다 — 격자 흐름 전 경로', () => {
  const REJECT = (detail: string) => [
    {
      renderId: RENDER_ID,
      status: '실패',
      failure: { code: 'REFERENCE_GRID_MISSING', message: '위경도를 담은 짝 파일이 없어요.', details: { detail } },
    },
  ];

  it('격자가 없어 지도형이 보류돼도 등록 버튼은 살아 있다', async () => {
    const { sources } = fakes({
      jobs: [
        {
          renderId: RENDER_ID,
          status: '완료',
          result: {
            imageUrl: 'https://viz.example/p/detail.png',
            legend: { palette: 'viridis', classes: [] },
            precisionBadge: '격자 없음 — 지도형 보류',
            colorRangeStage: '잠정',
          },
        },
      ],
    });
    await openModal(sources);
    await dropFiles([makeFile('rdr.bin')]);
    await click(await screen.findByTestId('up-preview-draw'));
    const block = await screen.findByTestId('up-grid-block', undefined, { timeout: 4000 });
    expect(block).toHaveTextContent('이 파일은 좌표를 자체적으로 갖고 있지 않습니다.');
    expect(screen.getByTestId('reg-open')).toBeEnabled();
  });

  it('격자가 형상 불일치로 거절돼도 등록 버튼은 살아 있다', async () => {
    const { sources } = fakes({
      jobs: REJECT('격자 형상이 데이터와 안 맞는다: 데이터 (2881, 2305) vs 격자 (1200, 1200)'),
    });
    await openModal(sources);
    await dropFiles([makeFile('rdr.bin')]);
    await click(await screen.findByTestId('up-preview-draw'));
    const block = await screen.findByTestId('up-grid-block', undefined, { timeout: 4000 });
    expect(block).toHaveTextContent('이 격자는 이 파일의 것이 아닙니다.');
    expect(screen.getByTestId('reg-open')).toBeEnabled();
  });

  it('건너뛰기를 누르면 지도 없이 등록한다고 말하고 등록은 그대로 열린다', async () => {
    const { sources } = fakes({
      jobs: [
        {
          renderId: RENDER_ID,
          status: '완료',
          result: {
            imageUrl: 'https://viz.example/p/detail.png',
            legend: { palette: 'viridis', classes: [] },
            precisionBadge: '격자 없음 — 지도형 보류',
            colorRangeStage: '잠정',
          },
        },
      ],
    });
    await openModal(sources);
    await dropFiles([makeFile('rdr.bin')]);
    await click(await screen.findByTestId('up-preview-draw'));
    await click(await screen.findByTestId('up-grid-skip', undefined, { timeout: 4000 } as never));
    expect(await screen.findByTestId('up-grid-block')).toHaveTextContent('지도 없이 등록합니다.');
    expect(screen.getByTestId('reg-open')).toBeEnabled();
  });

  it('격자 파일을 고르면 `기준 격자 파일` 로 다시 접수한다 — 축은 싣지 않는다', async () => {
    const { sources, calls } = fakes({
      jobs: [
        {
          renderId: RENDER_ID,
          status: '완료',
          result: {
            imageUrl: 'https://viz.example/p/detail.png',
            legend: { palette: 'viridis', classes: [] },
            precisionBadge: '격자 없음 — 지도형 보류',
            colorRangeStage: '잠정',
          },
        },
      ],
    });
    await openModal(sources);
    await dropFiles([makeFile('rdr.bin')]);
    await click(await screen.findByTestId('up-preview-draw'));
    const before = calls.create;
    fireEvent.change(await screen.findByTestId('up-grid-input', undefined, { timeout: 4000 }), {
      target: { files: [makeFile('Lat_HSR.npy'), makeFile('Lon_HSR.npy')] },
    });
    await act(async () => {});
    await waitFor(() => expect(calls.create).toBeGreaterThan(before));
    expect(await screen.findByTestId('up-companion')).toHaveTextContent('Lat_HSR.npy');
  });
});

/**
 * Ted 2026-08-28 완료 정의 ① 도달 경로 — **모달 쪽 절반.**
 * 정본 §7.2 전이표: 「보기만 할게요」의 도착지는 `미등록 파일 미리보기(S-08)` 다.
 * 배선을 되돌리면(=버튼이 닫기만 하면) 이 describe 가 red 가 된다.
 */
function LocationProbe() {
  const loc = useLocation();
  return (
    <div
      data-testid="loc"
      data-path={loc.pathname}
      data-search={loc.search}
      data-state={JSON.stringify(loc.state ?? null)}
    />
  );
}

async function openModalWithProbe(sources: UploadSources) {
  render(
    <MemoryRouter initialEntries={['/datasets']}>
      <SessionProvider account={account({ '업로드·편집': true })}>
        <UploadEntry sources={sources} />
        <LocationProbe />
      </SessionProvider>
    </MemoryRouter>,
  );
  await click(screen.getByTestId('gnb-upload'));
  await screen.findByTestId('upload-modal');
}

describe('§7.2 전이 — `보기만 할게요` 는 S-08 로 보낸다', () => {
  it('모달이 닫히고 주소가 미등록 미리보기 화면으로 바뀐다', async () => {
    const { sources, calls } = fakes();
    await openModalWithProbe(sources);
    await dropFiles([makeFile('nakdong_precip_2025_Lv2.nc')]);
    await screen.findByTestId('up-preview');
    await click(await screen.findByTestId('reg-viewonly'));

    const loc = screen.getByTestId('loc');
    expect(loc.getAttribute('data-path')).toBe(previewPath(UPLOAD_ID).split('?')[0]);
    expect(screen.queryByTestId('upload-modal')).toBeNull();
    // **아무것도 등록하지 않는다** — 이동은 사실을 만드는 것이 아니다 (§7.1)
    expect(calls.register).toBe(0);
  });

  it('그리던 미리보기를 짐으로 넘긴다 — S-08 이 다시 그리지 않고 이어 본다 (§8.1)', async () => {
    const { sources, calls } = fakes();
    await openModalWithProbe(sources);
    await dropFiles([makeFile('nakdong_precip_2025_Lv2.nc')]);
    await screen.findByTestId('up-preview');
    await click(await screen.findByTestId('up-preview-draw'));
    await waitFor(() => expect(calls.createRender.length).toBeGreaterThan(0));
    await click(await screen.findByTestId('reg-viewonly'));

    const loc = screen.getByTestId('loc');
    expect(loc.getAttribute('data-search')).toBe(`?render=${RENDER_ID}`);
    const state = JSON.parse(loc.getAttribute('data-state') ?? 'null') as Record<
      string,
      PreviewHandoff
    >;
    const handoff = state[PREVIEW_STATE_KEY]!;
    expect(handoff.uploadId).toBe(UPLOAD_ID);
    expect(handoff.renderId).toBe(RENDER_ID);
    // 헤더에서 읽은 값만 간다 — 사람이 붙이는 이름·주제는 자리 자체가 없다
    expect(handoff.basicInfo).toEqual({ byteSize: 148_000_000 });
    expect(handoff.files.map((f) => f.fileName)).toEqual(['nakdong_precip_2025_Lv2.nc']);
  });
});
