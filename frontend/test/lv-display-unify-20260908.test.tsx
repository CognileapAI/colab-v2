/**
 * WU-C9 · Lv 표시 **사람 값 우선 통일** (R-B §5 판정 27·41 ＋ 23·24 · 21차 해제 ⑵⑸).
 *
 * 오라클 = `dev-package/prd/rounds/R-C-1-contract-db.md` 「### WU-C9 수용 기준」 축자 —
 *   ① 사람 값 ≠ 파생값 픽스처에서 **네 자리**(카탈로그 · 상세 · 계보 그래프 노드 ·
 *      프로젝트 소속 데이터셋 표)의 표시 Lv 가 **같다**.
 *   ② 제안에 `parentProcessingLevel` 이 실려 오면 화면 충돌 경고가 **서버 400 전에** 뜬다.
 *   ③ 그 열쇠가 **없으면** 종전대로 조용하다 — 지어내지 않고 서버 400 이 판정한다.
 *
 * ⛔ **빈 집합 위에서 통과하지 않는다** — 자리 수를 먼저 세고(4) 그 다음에 값을 견준다.
 * ⚠ 서버는 두 값을 **나란히** 내려보낼 뿐이고(`d3_catalog.level_pair`) 고르는 것은
 *   화면이다(`common/processingLevel.ts` 한 자리). 파생값을 덮어 쓰면 계약 파괴(㉯)다.
 */
import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

import { CatalogTable } from '../src/components/catalog/CatalogTable';
import { useCatalog } from '../src/components/catalog/useCatalog';
import { FIXTURE_ROWS as FIXTURE_CATALOG_ROWS, fixtureCatalogSource } from '../src/components/catalog/fixture';
import type { DatasetRow as CatalogRow } from '../src/components/catalog/types';
import { DetailHeader } from '../src/components/detail/DetailHeader';
import { FIXTURE_DETAILS } from '../src/components/detail/fixture';
import type { DatasetDetail } from '../src/components/detail/types';
import type { ApprovalSource } from '../src/components/approval/types';
import { LineageSection } from '../src/components/lineage/LineageSection';
import { FIXTURE_LINEAGE } from '../src/components/lineage/graphFixture';
import type { LineageGraph } from '../src/components/lineage/graphTypes';
import { ProjectDatasetTable } from '../src/components/project/ProjectDatasetTable';
import type { ProjectDatasetRow } from '../src/components/project/types';
import { displayLevel } from '../src/components/common/processingLevel';

/** 한 데이터셋의 **한 가지 사실** — 사람이 고른 값과 계보 파생값이 **어긋난다**. */
const DS = '01JYZ9K7WQ3N8V4M2X6C5B0AA1';
const HUMAN = 'Lv3';
const HUMAN_N = 3;
const DERIVED = 1;
const SHOWN = `Lv${HUMAN_N}`;

const OPEN_ID = DS;

function stubApproval(): ApprovalSource {
  return {
    requestAccess: vi.fn(async () => {}),
    requestVerification: vi.fn(async () => {}),
    approveVerification: vi.fn(async () => {}),
    cancelVerification: vi.fn(async () => {}),
  };
}

/** ③ 프로젝트 소속 데이터셋 표 한 행 — 서버 `routes/project.py` 가 내는 모양 그대로. */
function projectRow(): ProjectDatasetRow {
  return {
    datasetId: DS,
    name: 'nakdong_precip_2025_Lv2.nc',
    fileCount: 1,
    // ⚠ 파생값이다 — 서버가 여기에 사람 값을 덮어 쓰지 않는다(21차 ⑵).
    processingLevel: DERIVED,
    processingLevelUserSet: HUMAN,
    period: null,
    lineageState: '확인 필요',
    verified: false,
    accessState: '열림',
    bodyAccessible: true,
  } as unknown as ProjectDatasetRow;
}

/** ④ 계보 그래프 — 「이 데이터」 노드만 이 데이터셋의 값으로 바꾼다. */
function graph(): LineageGraph {
  const base = FIXTURE_LINEAGE[OPEN_ID] as LineageGraph;
  return {
    ...base,
    canEdit: false,
    nodes: base.nodes.map((n) =>
      n.kind === '이 데이터'
        ? { ...n, processingLevel: DERIVED, processingLevelUserSet: HUMAN }
        : n,
    ),
  } as LineageGraph;
}

/**
 * ① 카탈로그 — 여기는 **서버가 이미 골라서 내려보내는 자리**다(`d3_catalog.level_view` ·
 * R-B · 계약 `DatasetRow.processingLevel` 산문 「사람 값이 `null` 인 행만 파생값으로 대신」).
 * 그래서 행에 실려 오는 값이 곧 사람 값이고, 화면은 같은 `displayLevel` 을 지날 뿐이다.
 */
function catalogRow(): CatalogRow {
  // 픽스처 6행 중 이 데이터셋의 행. **지어내지 않고 있는 행을 쓴다.**
  const base = FIXTURE_CATALOG_ROWS.find((r) => r.datasetId === DS) as CatalogRow;
  return { ...base, processingLevel: HUMAN_N } as CatalogRow;
}

function CatalogHarness(props: { rows: CatalogRow[] }) {
  const state = useCatalog(fixtureCatalogSource(props.rows));
  return (
    <CatalogTable
      state={state}
      uploaderNames={new Map()}
      onOpen={() => {}}
      onDownload={() => {}}
    />
  );
}

describe('WU-C9 ① 네 자리의 표시 Lv 가 같다 — 사람 값 우선', () => {
  it('사람 값 ≠ 파생값 픽스처에서 카탈로그·상세·계보 노드·프로젝트 표가 모두 Lv3 이다', async () => {
    const shown: string[] = [];

    // ㈎ 카탈로그
    const catalog = render(
      <MemoryRouter>
        <CatalogHarness rows={[catalogRow()]} />
      </MemoryRouter>,
    );
    await waitFor(() => expect(catalog.container.querySelector('.lvl')).toBeTruthy());
    const catalogLv = catalog.container.querySelector('.lvl');
    shown.push((catalogLv as HTMLElement).textContent as string);
    catalog.unmount();

    // ㈏ 상세 헤더
    const base = FIXTURE_DETAILS[OPEN_ID] as DatasetDetail;
    // ⚠ 상세도 카탈로그와 같다 — 서버가 `level_view` 로 **이미 고른** 표시값을 내린다.
    //    사람 값은 `basicInfo` 에 그대로 병존한다(불일치 안내가 그 값을 쓴다).
    const detail = {
      ...base,
      processingLevel: HUMAN_N,
      basicInfo: { ...(base.basicInfo ?? {}), processingLevelUserSet: HUMAN,
                   processingLevelDerived: DERIVED, processingLevelMismatch: true },
    } as unknown as DatasetDetail;
    const head = render(<DetailHeader detail={detail} approvalSource={stubApproval()} />);
    const headLv = head.container.querySelector('.dh-tags .lvl');
    expect(headLv).toBeTruthy();
    shown.push((headLv as HTMLElement).textContent as string);
    head.unmount();

    // ㈐ 계보 그래프 노드 (「이 데이터」)
    const lin = render(
      <MemoryRouter>
        <LineageSection graph={graph()} />
      </MemoryRouter>,
    );
    await screen.findByTestId('lineage-section');
    const selfNode = within(screen.getByTestId('lineage-section'))
      .getAllByTestId('lin-lv')
      .map((el) => el.textContent as string);
    expect(selfNode.length).toBeGreaterThan(0);
    // 「이 데이터」 노드가 그린 칩 — 그래프에서 이 데이터셋의 칸이다.
    const selfChip = lin.container.querySelector('.ln.is-self [data-testid="lin-lv"]')
      ?? lin.container.querySelector('[data-testid="lin-lv"]');
    shown.push(((selfChip as HTMLElement) ?? { textContent: '' }).textContent as string);
    lin.unmount();

    // ㈑ 프로젝트 소속 데이터셋 표
    const proj = render(<ProjectDatasetTable rows={[projectRow()]} canManage={false} onOpen={() => {}} onUnlink={async () => {}} />);
    const projLv = proj.container.querySelector('.lvl');
    expect(projLv).toBeTruthy();
    shown.push((projLv as HTMLElement).textContent as string);
    proj.unmount();

    // **자리 수를 먼저 센다** — 넷이 아니면 빈 집합 위에서 통과한 것이다.
    expect(shown).toHaveLength(4);
    expect(shown).toEqual([SHOWN, SHOWN, SHOWN, SHOWN]);
  });

  it('표시 규칙 함수는 한 자리다 — 사람 값이 없을 때만 파생값이 대신한다', () => {
    expect(displayLevel({ processingLevel: DERIVED, processingLevelUserSet: HUMAN })).toBe(HUMAN_N);
    expect(displayLevel({ processingLevel: DERIVED, processingLevelUserSet: null })).toBe(DERIVED);
    expect(displayLevel({ processingLevel: null, processingLevelUserSet: null })).toBe(null);
  });
});

// ═══ ② · ③ 등록 ③ 충돌 판정 — 제안이 실어 온 부모 Lv (질의 23 · 21차 ⑸) ═══
//
// 판정의 **정본은 서버 400** 이다(`test_lv_parent_rules.py`). 화면이 하는 일은 그 400 이
// 오기 전에 같은 사실을 미리 말해 주는 것뿐이고, **값이 없으면 아무 말도 하지 않는다.**
import { SessionProvider } from '../src/permission/session';
import { UploadEntry } from '../src/components/upload/UploadEntry';
import type {
  DatasetRow as LineageCandidateRow,
  LineageSource,
  LineageSuggestionResponse,
} from '../src/components/lineage/types';
import type { PreviewSource, ProjectSource, UploadSource, UploadSources } from '../src/components/upload/types';
import type { CurrentAccount, Schemas } from '../src/api/client';

const UPLOAD_ID = '01JYZ9K7WQ3N8V4M2X6C5B0UP1';
const FILE_ID = '01JYZ9K7WQ3N8V4M2X6C5B0FI1';
const SUGG_ID = '01JYZ9K7WQ3N8V4M2X6C5B0SG1';
const PARENT_ID = '01JYZ9K7WQ3N8V4M2X6C5B0D02';

function account(): CurrentAccount {
  return {
    accountId: '01JYZ9K7WQ3N8V4M2X6C5B0AC1',
    name: '호랑이',
    email: 'tiger@example.ac.kr',
    role: '연구원',
    labId: '01JYZ9K7WQ3N8V4M2X6C5B0LB1',
    labName: '수자원순환연구실',
    permissions: {
      '업로드·편집': true,
      '프로젝트 생성': true,
      '승인 위임': false,
      '연구실 설정': false,
    } as Record<Schemas['PermissionSwitch'], boolean>,
  } as unknown as CurrentAccount;
}

/** 제안 한 장 — `parentProcessingLevel` 을 **실을 수도, 안 실을 수도** 있다. */
function suggestionResponse(withLevel: boolean): LineageSuggestionResponse {
  return {
    degraded: false,
    scope: { labId: 'l', labName: '수자원순환연구실', searchedCount: 3 },
    rawDataLikely: false,
    suggestions: [
      {
        suggestionId: SUGG_ID,
        kind: '가공 전 데이터',
        confidence: '높음',
        rationale: '파일명이 같은 유역·같은 기간을 가리켜요',
        parentDatasetId: PARENT_ID,
        parentDatasetName: '집계 강우',
        suggestedParentRole: '주입력',
        // ⭑ ⟨21차 ⑸⟩ **모르면 열쇠 자체를 만들지 않는다** — `null` 을 싣지 않는다.
        ...(withLevel ? { parentProcessingLevel: 2 } : {}),
      },
    ],
  } as unknown as LineageSuggestionResponse;
}

function sourcesFor(withLevel: boolean): UploadSources {
  const files = [{ fileId: FILE_ID, fileName: 'nakdong_precip_2025_Lv1.nc', kind: '본체',
                   byteSize: 349_000, createdAt: '2026-09-08T00:00:00Z' }];
  const upload = {
    async create() { return { uploadId: UPLOAD_ID, files } as never; },
    async status() {
      return { uploadId: UPLOAD_ID, ready: true, failure: null, metadataComplete: true, files } as never;
    },
    async register() { return { datasetId: '01JYZ9K7WQ3N8V4M2X6C5B0DS1' } as never; },
    async attachGrid() { return [] as never; },
  } as unknown as UploadSource;
  const preview = {
    async palettes() { return [{ palette: 'viridis', label: '비리디스' }]; },
    async createRender() { return { renderId: 'r', state: '실패', failure: null } as never; },
    async getRender() { return { renderId: 'r', state: '실패', failure: null } as never; },
  } as unknown as PreviewSource;
  const projects = {
    async list() { return []; },
    async create() { return { projectId: '01JYZ9K7WQ3N8V4M2X6C5B0PR9', name: 'x', type: '국가과제' } as never; },
  } as unknown as ProjectSource;
  const lineage: LineageSource = {
    async suggestions() { return suggestionResponse(withLevel); },
    async candidates() { return [] as LineageCandidateRow[]; },
  };
  return { upload, preview, projects, lineage } as unknown as UploadSources;
}

async function click(el: Element | null) {
  fireEvent.click(el as HTMLElement);
  await act(async () => {});
}

/** ① 에서 자기 Lv 를 고르고 ③ 까지 간 뒤 **AI 제안을 부른다**. */
async function askInStepThree(withLevel: boolean) {
  render(
    <MemoryRouter initialEntries={['/datasets']}>
      <SessionProvider account={account()}>
        <UploadEntry sources={sourcesFor(withLevel)} />
      </SessionProvider>
    </MemoryRouter>,
  );
  await click(screen.getByTestId('gnb-upload'));
  await screen.findByTestId('upload-modal');
  const file = new File(['x'], 'nakdong_precip_2025_Lv1.nc', { type: 'application/octet-stream' });
  Object.defineProperty(file, 'size', { value: 349_000 });
  fireEvent.change(screen.getByTestId('up-drop-input'), { target: { files: [file] } });
  await act(async () => {});
  await screen.findByTestId('up-files');
  await click(await screen.findByTestId('reg-open'));
  await screen.findByTestId('reg-steps');
  // 자기 Lv = Lv1 · 제안이 실어 오는 부모 Lv = Lv2 → **초과**다.
  fireEvent.change(screen.getByTestId('reg-level'), { target: { value: 'Lv1' } });
  await act(async () => {});
  await click(screen.getByRole('button', { name: /^③/ }));
  await screen.findByTestId('lin-step');
  await click(screen.getByTestId('lin-ask'));
  await screen.findByTestId('lin-card');
}

describe('WU-C9 ② 제안의 `parentProcessingLevel` — 서버 400 전에 화면이 경고한다', () => {
  it('제안이 부모 Lv 를 실어 오고 자기 Lv 를 넘으면 `확인 필요` ＋ 충돌 안내가 뜬다', async () => {
    await askInStepThree(true);
    expect(screen.getByTestId('lin-need-check').textContent).toBe('확인 필요');
    expect(screen.getByTestId('lin-conflict-note').textContent).toContain('Lv1');
  });

  it('열쇠가 없으면 조용하다 — 지어내지 않고 서버 400 이 판정한다', async () => {
    await askInStepThree(false);
    // 카드는 그대로 선다(깨지지 않는다) — 경고만 없다.
    expect(screen.getAllByTestId('lin-card')).toHaveLength(1);
    expect(screen.queryByTestId('lin-need-check')).toBeNull();
    expect(screen.queryByTestId('lin-conflict-note')).toBeNull();
  });
});
