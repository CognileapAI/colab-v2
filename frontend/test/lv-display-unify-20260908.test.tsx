/**
 * WU-C9 · Lv 표시 **사람 값 우선 통일** (R-B §5 판정 27·41 ＋ 23·24 · 21차 해제 ⑵⑸).
 *
 * 오라클 = `dev-package/prd/rounds/R-C-1-contract-db.md` 「### WU-C9 수용 기준」 축자 —
 *   ① 사람 값 ≠ 파생값 픽스처에서 **네 자리**(카탈로그 · 상세 · 계보 그래프 노드 ·
 *      프로젝트 소속 데이터셋 표)의 표시 Lv 가 **같다**.
 *   ⭑ **⟨개정 2026-09-14 · 기획자 9/13 피드백 「반쪽 AI 제거」 · Ted 재판정 대기 · 판정문 ㉮⟩
 *     수용 기준 ②③ 을 재던 블록을 걷었다.**
 *     ／ 종전 ~~② 제안에 `parentProcessingLevel` 이 실려 오면 화면 충돌 경고가 **서버 400
 *     전에** 뜬다 ／ ③ 그 열쇠가 **없으면** 종전대로 조용하다~~ — 등록 ③ 에서 **제안을
 *     부르는 자리가 사라져** 제안이 실어 오는 부모 Lv 자체가 없다.
 *     ⚠ **충돌 경고 규칙은 남아 있다** — 사람이 이어 붙인 부모의 Lv 로 같은 판정을 하고,
 *     그 자리는 `upload.test.tsx` ③ 계보 확정 블록과 서버 `test_lv_parent_rules.py` 다.
 *     ⛔ **판정의 정본은 여전히 서버 400 이다.**
 *
 * ⛔ **빈 집합 위에서 통과하지 않는다** — 자리 수를 먼저 세고(4) 그 다음에 값을 견준다.
 * ⚠ 서버는 두 값을 **나란히** 내려보낼 뿐이고(`d3_catalog.level_pair`) 고르는 것은
 *   화면이다(`common/processingLevel.ts` 한 자리). 파생값을 덮어 쓰면 계약 파괴(㉯)다.
 */
import { render, screen, waitFor, within } from '@testing-library/react';
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

