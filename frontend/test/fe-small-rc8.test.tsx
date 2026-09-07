/**
 * WU-C8 · FE 소형 5건 — R-B 묶음 질의 §5-14·16·28·31·43 의 판정을 잠근다.
 *
 * 오라클 = `dev-package/prd/rounds/R-C-2-frontend.md §2 WU-C8` **수용 기준 5건 축자**
 *   ㈎ (§5-16) `연구실 정보` 공개 범위 셀렉트 **옵션 3개** — `지정 공개` 를 고를 수 있다
 *   ㈏ (§5-31) 등록 실패 — 서버 **400 은 그 문면 그대로**, 그 밖(500)은 종전 일반 문구
 *   ㈐ (§5-14) 등록 ② 기간 — **인라인 칸 0개 ＋ 달력 팝오버 1개**, 팝오버가 같은 열쇠를 싣는다
 *   ㈑ (§5-28) 상세 Lv0 출처 안내 — **사람 Lv 기준**(사람 0·파생≠0 → 뜬다 / 사람≠0·파생 0 → 안 뜬다)
 *   ㈒ (§5-43) 계보 빈 상태 — `canEdit=false` 계정도 **3문면 전부**, 행동만 가려진다
 *
 * ⛔ **문면을 이 파일에서 새로 짓지 않는다** — 비교 대상은 전부 소스의 상수이거나
 *    서버가 적어 보낸 문자열이다. 시험이 문면의 두 번째 원본이 되면 한쪽만 고쳐진다.
 * 모든 단언은 **대상 건수를 먼저 잰다** — 빈 집합 통과(green-by-skip)를 막는다.
 */
import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { SessionProvider } from '../src/permission/session';
import { UploadEntry } from '../src/components/upload/UploadEntry';
import { LabInfoPanel } from '../src/components/lab/LabInfoPanel';
import { ACCESS_LABEL, ACCESS_STATES } from '../src/components/common/accessState';
import { DatasetDetailPage } from '../src/routes/DatasetDetailPage';
import { FIXTURE_DETAILS } from '../src/components/detail/fixture';
import { LV0_SOURCE_MISSING_NOTICE } from '../src/components/detail/format';
import { apiUploadSource } from '../src/components/upload/uploadSource';
import { RegisterRejected } from '../src/components/upload/types';
import { LineageSection } from '../src/components/lineage/LineageSection';
import type { LabSource } from '../src/components/lab/labSource';
import type { DatasetDetail, DetailSource } from '../src/components/detail/types';
import type { LineageGraph } from '../src/components/lineage/graphTypes';
import type {
  LineageSource,
  LineageSuggestionResponse,
} from '../src/components/lineage/types';
import type {
  PreviewSource,
  ProjectSource,
  UploadSource,
  UploadSources,
} from '../src/components/upload/types';
import type { CurrentAccount, Schemas } from '../src/api/client';

const UPLOAD_ID = '01JYZ9K7WQ3N8V4M2X6C5B0UP1';
const FILE_ID = '01JYZ9K7WQ3N8V4M2X6C5B0FI1';
const FILE_NAME = 'nakdong_precip_2025_Lv2.nc';
const SELF = '01JYZ9K7WQ3N8V4M2X6C5B0AA3';

// ─────────────────────────── 공통 대역 ───────────────────────────

function account(extra?: Partial<CurrentAccount>): CurrentAccount {
  return {
    accountId: '01JYZ9K7WQ3N8V4M2X6C5B0AC1',
    name: '호랑이',
    email: 'tiger@example.ac.kr',
    role: '연구원',
    labId: '01JYZ9K7WQ3N8V4M2X6C5B0LB1',
    labName: '수자원순환연구실',
    permissions: { '업로드·편집': true } as CurrentAccount['permissions'],
    ...extra,
  } as CurrentAccount;
}

async function click(el: Element | null) {
  fireEvent.click(el as HTMLElement);
  await act(async () => {});
}

async function change(el: Element | null, value: string) {
  fireEvent.change(el as HTMLElement, { target: { value } });
  await act(async () => {});
}

// ═══════════════ ㈎ §5-16 · 연구실 기본 공개 범위 셀렉트 3값 ═══════════════

function labSource(): LabSource {
  const lab = {
    labId: '01JYZ9K7WQ3N8V4M2X6C5B0LB1',
    name: '수자원순환연구실',
    university: null,
    department: null,
    principalInvestigator: null,
    researchField: null,
    introduction: null,
    defaultVisibility: '열림',
  } as unknown as Awaited<ReturnType<LabSource['read']>>;
  return {
    async read() {
      return lab;
    },
    async update(changes) {
      return { ...lab, ...changes } as typeof lab;
    },
  };
}

async function openLabEdit() {
  render(
    <SessionProvider account={account({ permissions: { '연구실 설정': true } as never })}>
      <LabInfoPanel source={labSource()} />
    </SessionProvider>,
  );
  await screen.findByText('연구실 정보');
  await click(await screen.findByRole('button', { name: '정보 편집' }));
  return screen.getByLabelText('데이터 공개 범위') as HTMLSelectElement;
}

describe('㈎ §5-16 — 연구실 기본 공개 범위는 계약 3값이다', () => {
  it('셀렉트 옵션이 **정확히 3개**이고 `지정 공개` 를 고를 수 있다', async () => {
    // 대조군 명시 — 계약 `AccessState` 가 3값이라는 사실이 이 시험의 기대값이다.
    expect(ACCESS_STATES).toHaveLength(3);
    const sel = await openLabEdit();
    const options = within(sel).getAllByRole('option');
    expect(options).toHaveLength(3);
    expect(options.map((o) => (o as HTMLOptionElement).value)).toEqual([
      '열림',
      '잠김',
      '지정 공개',
    ]);
    // 사람이 보는 글자는 등록 화면과 **같은 표**를 읽는다(미결-1 ⓐ) — 두 벌이 아니다.
    expect(options.map((o) => o.textContent)).toEqual(ACCESS_STATES.map((s) => ACCESS_LABEL[s]));
    // 골라진다 — 옵션만 있고 값이 안 붙는 자리를 만들지 않는다.
    await change(sel, '지정 공개');
    expect(sel.value).toBe('지정 공개');
  });
});

// ═════════ ㈏ §5-31 · 등록 실패 — 400 문면 그대로 / 그 밖은 일반 문구 ═════════

const SERVER_400 = '기간의 종료는 시작보다 앞설 수 없다.';
const GENERIC = '데이터셋을 만들지 못했어요. 잠시 뒤 다시 시도해 주세요.';

function fakes(opts?: {
  onRegister?: () => never;
  capture?: (body: Record<string, unknown>) => void;
}): UploadSources {
  const status: Schemas['UploadStatus'] = {
    uploadId: UPLOAD_ID,
    files: [{ fileId: FILE_ID, fileName: FILE_NAME, kind: '본체', byteSize: 148_000_000 }],
    ready: true,
    renderable: true,
    metadataComplete: true,
    expiresAt: '2026-08-24T00:00:00Z',
    failure: null,
  } as Schemas['UploadStatus'];
  const upload: UploadSource = {
    async create(files) {
      return {
        uploadId: UPLOAD_ID,
        files: files.map((f) => ({
          fileId: FILE_ID,
          fileName: f.file.name,
          kind: f.kind,
          byteSize: f.file.size,
        })),
      };
    },
    async status() {
      return status;
    },
    async register(body) {
      if (opts?.onRegister) opts.onRegister();
      opts?.capture?.(body as unknown as Record<string, unknown>);
      return { datasetId: '01JYZ9K7WQ3N8V4M2X6C5B0DS1' };
    },
    async attachGrid() {
      return [];
    },
  };
  const preview: PreviewSource = {
    async palettes() {
      return [{ palette: 'viridis', label: '비리디스' }];
    },
    async createRender() {
      return { renderId: 'R1', status: '그리는 중', stage: '파일 읽는 중' } as never;
    },
    async getRender() {
      return { renderId: 'R1', status: '그리는 중', stage: '파일 읽는 중' } as never;
    },
  };
  const projects: ProjectSource = {
    async list() {
      return [];
    },
    async create(body) {
      return { projectId: '01JYZ9K7WQ3N8V4M2X6C5B0PR9', name: body.name, type: body.type };
    },
  };
  const lineage: LineageSource = {
    async suggestions() {
      return {
        degraded: false,
        scope: {
          labId: '01JYZ9K7WQ3N8V4M2X6C5B0LB1',
          labName: '수자원순환연구실',
          searchedCount: 0,
        },
        rawDataLikely: false,
        suggestions: [],
      } as LineageSuggestionResponse;
    },
    async candidates() {
      return [];
    },
  };
  return { upload, preview, projects, lineage };
}

function makeFile(name: string, size = 148_000_000) {
  const f = new File(['x'], name, { type: 'application/octet-stream' });
  Object.defineProperty(f, 'size', { value: size });
  return f;
}

async function openRegister(sources: UploadSources) {
  render(
    <MemoryRouter initialEntries={['/datasets']}>
      <SessionProvider account={account()}>
        <UploadEntry sources={sources} />
      </SessionProvider>
    </MemoryRouter>,
  );
  await click(screen.getByTestId('gnb-upload'));
  await screen.findByTestId('upload-modal');
  fireEvent.change(screen.getByTestId('up-drop-input'), {
    target: { files: [makeFile(FILE_NAME)] },
  });
  await act(async () => {});
  await screen.findByTestId('up-files');
  await click(await screen.findByTestId('reg-open'));
  await screen.findByTestId('reg-steps');
  await click(screen.getByRole('button', { name: /^② / }));
}

/** ② 에서 필수 칸을 채우고 ③ 까지 넘어가 `데이터셋 만들기` 를 누른다. */
async function submitRegister() {
  await change(screen.getByTestId('reg-summary'), '설명 한 줄');
  await click(screen.getByTestId('reg-next'));
  await click(screen.getByTestId('reg-done'));
}

describe('㈏ §5-31 — 등록 거절은 400 과 그 밖이 갈린다', () => {
  it('서버 400 이면 **서버 문면이 그대로** 뜬다 (일반 문구로 덮지 않는다)', async () => {
    await openRegister(
      fakes({
        onRegister() {
          throw new RegisterRejected(SERVER_400);
        },
      }),
    );
    await submitRegister();
    const err = await screen.findByTestId('reg-error');
    expect(err.textContent).toBe(SERVER_400);
    // ⛔ 종전 일반 문구가 **섞여 나오지 않는다** — 두 문장이 겹치면 고칠 칸이 다시 묻힌다.
    expect(err.textContent).not.toContain('잠시 뒤 다시 시도해 주세요');
  });

  it('그 밖의 실패(500)는 **종전 일반 문구** 그대로다 — 사람이 고칠 것이 없다', async () => {
    await openRegister(
      fakes({
        onRegister() {
          throw new Error('Internal Server Error');
        },
      }),
    );
    await submitRegister();
    const err = await screen.findByTestId('reg-error');
    expect(err.textContent).toBe(GENERIC);
    // 서버가 삼킨 내부 문자열이 사람에게 새어 나가지 않는다.
    expect(err.textContent).not.toContain('Internal Server Error');
  });

  it('`uploadSource.register` 가 400 봉투의 `message` 를 그대로 들어 올린다', async () => {
    const fetchStub = vi.fn(
      async () =>
        new Response(JSON.stringify({ message: SERVER_400 }), {
          status: 400,
          headers: { 'content-type': 'application/json' },
        }),
    );
    vi.stubGlobal('fetch', fetchStub);
    await expect(apiUploadSource().register({} as never)).rejects.toThrowError(RegisterRejected);
    expect(fetchStub).toHaveBeenCalledTimes(1);
    await expect(apiUploadSource().register({} as never)).rejects.toThrowError(SERVER_400);
  });
});

afterEach(() => {
  vi.unstubAllGlobals();
});

// ═══════════ ㈐ §5-14 · 기간은 달력 팝오버 하나로만 받는다 ═══════════

/** 인라인 기간 칸의 자취 — 걷힌 자리의 testid 전부. 팝오버 안쪽(`reg-period-pop-*`)과 갈린다. */
const INLINE_PERIOD_TESTIDS = [
  'reg-period-granularity',
  'reg-period-start',
  'reg-period-end',
  'reg-period-start-parts',
  'reg-period-end-parts',
];

describe('㈐ §5-14 — 기간 인라인 칸 0개 · 달력 팝오버 1개', () => {
  it('② 에 인라인 기간 칸이 **하나도** 없고 팝오버 버튼은 **하나**다', async () => {
    await openRegister(fakes());
    // 대조군 — 세는 대상이 5개라는 사실을 먼저 박는다(빈 목록 통과 방지).
    expect(INLINE_PERIOD_TESTIDS).toHaveLength(5);
    const inline = INLINE_PERIOD_TESTIDS.filter((id) => screen.queryByTestId(id) !== null);
    expect(inline).toEqual([]);
    expect(screen.getAllByTestId('reg-period-open')).toHaveLength(1);
    // 열기 전에는 팝오버 자체가 DOM 에 없다 — 「칸이 두 벌」이던 자리가 사라졌다.
    expect(screen.queryByTestId('reg-period-pop')).toBeNull();
  });

  it('팝오버가 여전히 `period.start`·`end`·`granularity` 를 **그대로** 싣는다', async () => {
    let sent: Record<string, unknown> | null = null;
    await openRegister(
      fakes({
        capture(body) {
          sent = body;
        },
      }),
    );
    await click(screen.getByTestId('reg-period-open'));
    await screen.findByTestId('reg-period-pop');
    await click(screen.getByTestId('reg-period-unit-일'));
    await change(screen.getByTestId('reg-period-pop-start-year'), '2020');
    await change(screen.getByTestId('reg-period-pop-start-month'), '05');
    await change(screen.getByTestId('reg-period-pop-start-day'), '01');
    await click(screen.getByTestId('reg-period-apply'));
    await submitRegister();
    // ⭑ ⟨PRD-40 판정 ⓐ⟩ 종료를 비우면 저장은 `period_end = period_start` 다 — 무변이다.
    expect(sent).not.toBeNull();
    expect(sent!.period).toEqual({
      start: '2020-05-01T00:00:00Z',
      end: '2020-05-01T00:00:00Z',
      granularity: '일',
    });
  });
});

// ═══════════ ㈑ §5-28 · Lv0 출처 안내는 사람 Lv 기준이다 ═══════════

function detailWith(patch: Record<string, unknown>): DatasetDetail {
  const base = Object.values(FIXTURE_DETAILS)[0];
  if (!base || !base.basicInfo) {
    throw new Error('픽스처가 비어 있다 — 대조군 없는 통과를 만들지 않는다.');
  }
  return {
    ...base,
    basicInfo: { ...base.basicInfo, ...patch },
  } as DatasetDetail;
}

async function mountDetail(detail: DatasetDetail) {
  const source: DetailSource = { get: () => Promise.resolve(detail) };
  render(
    <MemoryRouter initialEntries={[`/datasets/${detail.datasetId}`]}>
      <SessionProvider account={account()}>
        <Routes>
          <Route path="/datasets/:datasetId" element={<DatasetDetailPage source={source} />} />
        </Routes>
      </SessionProvider>
    </MemoryRouter>,
  );
  await screen.findByTestId('basic-info');
}

describe('㈑ §5-28 — Lv0 출처 안내의 기준은 사람 Lv 다', () => {
  it('사람 Lv0 ＋ 파생 Lv2 이고 두 칸이 비면 **안내가 뜬다** (종전에는 안 떴다)', async () => {
    await mountDetail(
      detailWith({
        processingLevelDerived: 2,
        processingLevelUserSet: 'Lv0',
        sourceUrl: null,
        sourceDownloadedOn: null,
      }),
    );
    const note = screen.getByTestId('ig-lv0-source-missing');
    expect(note.textContent).toBe(LV0_SOURCE_MISSING_NOTICE);
  });

  it('사람 Lv2 ＋ 파생 Lv0 이고 두 칸이 비면 **안내가 서지 않는다** (종전에는 떴다)', async () => {
    await mountDetail(
      detailWith({
        processingLevelDerived: 0,
        processingLevelUserSet: 'Lv2',
        sourceUrl: null,
        sourceDownloadedOn: null,
      }),
    );
    // 안내 자리가 정말 그려질 수 있는 화면인지 먼저 확인한다 — 빈 화면 통과 방지.
    expect(screen.getByTestId('ig-원천 표기')).toBeTruthy();
    expect(screen.queryByTestId('ig-lv0-source-missing')).toBeNull();
  });
});

// ═══════════ ㈒ §5-43 · 빈 상태 3문면은 권한과 무관하다 ═══════════

/** 빈 상태의 세 문장 — 정본은 `LineageSection` 이고 여기서는 **읽히는가**만 잰다. */
const EMPTY_SENTENCES = [
  '아직 채워지지 않은 계보예요',
  '업로드할 때 가공 전 데이터를 찾지 못해 모름으로 남겨 뒀어요.',
  '원자료(Lv0)라 부모가 없다면 그대로 두어도 괜찮아요.',
];

function emptyGraph(canEdit: boolean): LineageGraph {
  return {
    datasetId: SELF,
    lineageState: '기록 없음',
    lineageConfirmedAt: null,
    unknownParents: true,
    nodes: [
      {
        kind: '이 데이터',
        datasetId: SELF,
        name: 'nakdong_DEM_10m.tif',
        processingLevel: 2,
        verified: false,
        navigable: false,
        bodyAccessible: true,
        deletedAt: null,
      },
    ],
    edges: [],
    projectUseCount: 0,
    canEdit,
  } as LineageGraph;
}

function renderLineage(canEdit: boolean) {
  render(
    <MemoryRouter>
      <SessionProvider account={account()}>
        <LineageSection graph={emptyGraph(canEdit)} />
      </SessionProvider>
    </MemoryRouter>,
  );
}

describe('㈒ §5-43 — 빈 상태 3문면은 `canEdit` 과 무관하다', () => {
  it('`canEdit=false` 계정도 **3문면 전부**를 읽는다 (종전에는 2문면이었다)', () => {
    expect(EMPTY_SENTENCES).toHaveLength(3);
    renderLineage(false);
    const empty = screen.getByTestId('lin-empty');
    const read = EMPTY_SENTENCES.filter((s) => empty.textContent?.includes(s));
    expect(read).toHaveLength(3);
    // ⛔ 가려지는 것은 **행동뿐**이다 — 버튼은 비활성이 아니라 부재다(P-12 관례).
    expect(screen.queryByTestId('lin-fill')).toBeNull();
  });

  it('`canEdit=true` 는 같은 3문면 ＋ `계보 채우기` 버튼이다', () => {
    renderLineage(true);
    const empty = screen.getByTestId('lin-empty');
    const read = EMPTY_SENTENCES.filter((s) => empty.textContent?.includes(s));
    expect(read).toHaveLength(3);
    expect(screen.getByTestId('lin-fill')).toBeTruthy();
  });
});
