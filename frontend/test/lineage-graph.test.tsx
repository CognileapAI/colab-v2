/**
 * S-05 계보 그래프 (WU-P3) — 정본 대비 시험.
 * 오라클 = `E-03_데이터셋_상세/documents/Policy_데이터셋_상세.md` (v2.2) §1-2 · §2 · §3.2 · §5 · §8 · §9
 *          와 그 목업 `mockups/데이터셋_상세_260817.html` (문구·라벨의 정본).
 *
 * **빈 집합 위에서 통과하지 않는다.** 모든 단언은 대상이 1건 이상임을 먼저 재거나,
 * 「비어 있는 것」자체를 기대값으로 명시한다 (green-by-skip 방지 · `CLAUDE.md §4`).
 */
import { render, screen, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { DatasetDetailPage } from '../src/routes/DatasetDetailPage';
import { fixtureDetailSource, FIXTURE_DETAILS } from '../src/components/detail/fixture';
import type { DetailSource } from '../src/components/detail/types';
import {
  FIXTURE_LINEAGE,
  fixtureLineageSource,
} from '../src/components/lineage/graphFixture';
import type { LineageGraph, LineageGraphSource } from '../src/components/lineage/graphTypes';

const OPEN_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA1'; // 목업 기본 장면 — 원천 2 · 가공 전 1 · 파생 1
const UNKNOWN_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA3'; // 기록 없음 (nakdong_DEM_10m.tif)
const LOCKED_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA5';
const PARENT_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA6'; // ERA5_precip_2025_Lv1.grib
const CHILD_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA7'; // nakdong_flood_index_2025_Lv3.nc

const 호랑이 = { accountId: '01JYZ9K7WQ3N8V4M2X6C5B0U01', name: '호랑이' };

function renderDetail(
  datasetId: string,
  lineage: LineageGraphSource = fixtureLineageSource(),
  detail: DetailSource = fixtureDetailSource(),
) {
  return render(
    <MemoryRouter initialEntries={[`/datasets/${datasetId}`]}>
      <Routes>
        <Route
          path="/datasets/:datasetId"
          element={<DatasetDetailPage source={detail} lineageSource={lineage} />}
        />
        <Route path="/datasets" element={<div>카탈로그</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

/** 한 건짜리 출처 — 시험이 그리려는 그래프를 그대로 준다. */
function only(graph: LineageGraph): LineageGraphSource {
  return { async get() { return graph; } };
}

async function settleLineage() {
  return screen.findByTestId('lineage-section');
}

const BASE = FIXTURE_LINEAGE[OPEN_ID]!;

describe('§8 계보 그래프 — 항상 표시하고 가로축은 데이터만 세운다', () => {
  it('그래프가 서고, 축은 원천 → 가공 전 → 이 데이터 → 파생 순이다', async () => {
    renderDetail(OPEN_ID);
    await settleLineage();
    const cols = screen.getAllByTestId('lin-col');
    expect(cols.length).toBeGreaterThan(0); // 대상 집합이 비지 않았음을 먼저 못박는다
    // §8 이 정한 것은 **순서**다. 「빈 칸도 자리를 지킨다」는 규정이 아니다 —
    // 그래서 개수가 아니라 오름차순을 잰다 (버그 3·5·7).
    const order = cols.map((c) => Number(c.getAttribute('data-col')));
    expect(order).toEqual([...order].sort((a, b) => a - b));
    expect(new Set(order).size).toBe(order.length);
    // 이 픽스처는 네 종류가 다 있어 네 칸이 다 선다
    expect(order).toEqual([0, 1, 2, 3]);
  });

  it('노드는 전부 데이터고 프로젝트 노드를 세우지 않는다 (§1-2)', async () => {
    renderDetail(OPEN_ID);
    await settleLineage();
    const nodes = screen.getAllByTestId('lin-node');
    expect(nodes.length).toBe(BASE.nodes.length);
    expect(nodes.length).toBeGreaterThan(0);
    const kinds = new Set(nodes.map((n) => n.getAttribute('data-kind')));
    for (const k of kinds) {
      expect(['원천', '가공 전', '이 데이터', '파생', '묘비']).toContain(k);
    }
    // 프로젝트는 배지로만 알린다 — 그래프 안에 프로젝트 노드가 없다
    expect(screen.getAllByTestId('lin-node').filter((n) => n.dataset.kind === '프로젝트')).toHaveLength(0);
  });

  it('`이 데이터`는 굵은 테두리로 구분된다', async () => {
    renderDetail(OPEN_ID);
    await settleLineage();
    const self = screen.getAllByTestId('lin-node').filter((n) => n.dataset.kind === '이 데이터');
    expect(self).toHaveLength(1);
    expect(self[0]!.className).toContain('is-self');
  });

  it('원천 노드는 점선 표기다', async () => {
    renderDetail(OPEN_ID);
    await settleLineage();
    const src = screen.getAllByTestId('lin-node').filter((n) => n.dataset.kind === '원천');
    expect(src.length).toBe(2);
    for (const n of src) expect(n.className).toContain('is-src');
  });

  it('화면을 넘으면 가로 스크롤한다 — 접거나 요약하지 않는다', async () => {
    renderDetail(OPEN_ID);
    await settleLineage();
    const g = screen.getByTestId('lin-graph');
    expect(g).toHaveAttribute('data-overflow', '가로 스크롤');
    // 접기·더 보기 같은 축약 컨트롤을 두지 않는다
    expect(within(g).queryByRole('button', { name: /더 보기|접기/ })).toBeNull();
  });

  it('가공 방식은 화살표 위 라벨이고 AI 경로에만 ✦ 를 붙인다', async () => {
    renderDetail(OPEN_ID);
    await settleLineage();
    const labels = screen.getAllByTestId('lin-method');
    const withMethod = BASE.edges.filter((e) => e.method !== null);
    expect(withMethod.length).toBeGreaterThan(0);
    expect(labels).toHaveLength(withMethod.length);
    expect(labels.map((l) => l.textContent)).toEqual(
      withMethod.map((e) => (e.origin === 'ai' ? `✦ ${e.method}` : e.method)),
    );
  });

  it('AI 가 아닌 관계의 라벨에는 ✦ 를 붙이지 않는다 (붉은 경로 픽스처)', async () => {
    const manual: LineageGraph = {
      ...BASE,
      edges: BASE.edges.map((e) => ({ ...e, origin: 'manual' as const })),
    };
    renderDetail(OPEN_ID, only(manual));
    await settleLineage();
    const labels = screen.getAllByTestId('lin-method');
    expect(labels.length).toBeGreaterThan(0);
    for (const l of labels) expect(l.textContent).not.toContain('✦');
  });
});

/** 렌더된 칸 번호 — 오름차순이 §8 의 축 순서다. */
function renderedCols(container: HTMLElement): number[] {
  return Array.from(container.querySelectorAll('[data-testid="lin-col"]')).map((c) =>
    Number(c.getAttribute('data-col')),
  );
}

/** 칸과 칸 사이 화살표. 노드 안의 `›`(`.arw`) 와 다른 클래스다. */
function arrowCount(container: HTMLElement): number {
  return container.querySelectorAll('.lin-arw').length;
}

const DERIVED_A = '01JYZ9K7WQ3N8V4M2X6C5B0AB1'; // 파생 Lv1

/** (a) 부모가 없는 루트 Lv0 — 자식만 있다. 원천·가공 전 칸이 비는 장면 (버그 5). */
const ROOT_WITH_CHILD: LineageGraph = {
  ...BASE,
  unknownParents: false,
  projectUseCount: 0,
  nodes: [
    { kind: '이 데이터', datasetId: OPEN_ID, name: 'nakdong_raw_2025_Lv0.nc', processingLevel: 0,
      verified: true, navigable: false, bodyAccessible: true, deletedAt: null },
    { kind: '파생', datasetId: DERIVED_A, name: 'nakdong_precip_2025_Lv1.nc', processingLevel: 1,
      verified: false, navigable: true, bodyAccessible: true, deletedAt: null },
  ],
  edges: [
    { childDatasetId: DERIVED_A, parentDatasetId: OPEN_ID, parentRole: '주입력',
      method: '임계값 초과일 집계', origin: 'manual', confirmedBy: 호랑이,
      confirmedAt: '2026-08-04T00:00:00Z' },
  ],
};

/** (b) 1-hop Lv0 → Lv1 이고 이 데이터가 잎이다. 파생 칸이 비는 장면 (버그 3). */
const LEAF_WITH_PARENT: LineageGraph = {
  ...BASE,
  unknownParents: false,
  projectUseCount: 0,
  nodes: [
    { kind: '가공 전', datasetId: PARENT_ID, name: 'ERA5_precip_2025_Lv0.grib', processingLevel: 0,
      verified: false, navigable: true, bodyAccessible: true, deletedAt: null },
    { kind: '이 데이터', datasetId: OPEN_ID, name: 'nakdong_precip_2025_Lv1.nc', processingLevel: 1,
      verified: true, navigable: false, bodyAccessible: true, deletedAt: null },
  ],
  edges: [
    { childDatasetId: OPEN_ID, parentDatasetId: PARENT_ID, parentRole: '주입력',
      method: '이중선형보간', origin: 'manual', confirmedBy: 호랑이,
      confirmedAt: '2026-08-05T00:00:00Z' },
  ],
};

/** (c) 원천 + 이 데이터 Lv0 + 파생 Lv1. 가공 전 칸이 비는 장면 (버그 7). */
const SOURCE_ROOT_CHILD: LineageGraph = {
  ...BASE,
  unknownParents: false,
  projectUseCount: 0,
  nodes: [
    { kind: '원천', datasetId: null, name: 'NMSC', processingLevel: null,
      verified: false, navigable: false, bodyAccessible: true, deletedAt: null },
    { kind: '이 데이터', datasetId: OPEN_ID, name: 'nakdong_raw_2025_Lv0.nc', processingLevel: 0,
      verified: true, navigable: false, bodyAccessible: true, deletedAt: null },
    { kind: '파생', datasetId: DERIVED_A, name: 'nakdong_precip_2025_Lv1.nc', processingLevel: 1,
      verified: false, navigable: true, bodyAccessible: true, deletedAt: null },
  ],
  edges: [
    { childDatasetId: DERIVED_A, parentDatasetId: OPEN_ID, parentRole: '주입력',
      method: '임계값 초과일 집계', origin: 'manual', confirmedBy: 호랑이,
      confirmedAt: '2026-08-04T00:00:00Z' },
  ],
};

/**
 * (c′) **같은 장면인데 서버가 원천 관계를 실은 판** (`BF-9` 완료 정의 ⑵).
 * 노드는 (c) 와 한 글자도 다르지 않고, `edges` 에 `parentDatasetId: null` 한 줄이 더 있다.
 * 계약이 이 모양을 이미 허용한다 — `LineageEdge.parentDatasetId` 산문 축자
 * 「원천 표기가 부모 자리인 관계는 데이터셋이 아니므로 null 이다」. **가공 방식은 없다.**
 */
const SOURCE_ROOT_CHILD_WITH_EDGE: LineageGraph = {
  ...SOURCE_ROOT_CHILD,
  edges: [
    ...SOURCE_ROOT_CHILD.edges,
    { childDatasetId: OPEN_ID, parentDatasetId: null, parentRole: '주입력', method: null,
      origin: 'manual', confirmedBy: 호랑이, confirmedAt: '2026-08-03T00:00:00Z' },
  ],
};

describe('§8 가로축 — 빈 칸도 고아 화살표도 두지 않는다 (버그 3·5·7)', () => {
  it('루트 Lv0 는 왼쪽에 빈 칸을 두지 않는다 — 이 데이터 · 파생만 선다 (버그 5)', async () => {
    const { container } = renderDetail(OPEN_ID, only(ROOT_WITH_CHILD));
    await settleLineage();
    expect(renderedCols(container)).toEqual([2, 3]);
    expect(arrowCount(container)).toBe(1);
  });

  it('잎 Lv1 은 오른쪽에 화살표를 두지 않는다 — 가공 전 · 이 데이터만 선다 (버그 3)', async () => {
    const { container } = renderDetail(OPEN_ID, only(LEAF_WITH_PARENT));
    await settleLineage();
    expect(renderedCols(container)).toEqual([1, 2]);
    expect(arrowCount(container)).toBe(1);
  });

  it('원천이 있고 가공 전이 없으면 원천 바로 옆에 이 데이터가 붙는다 (버그 7)', async () => {
    const { container } = renderDetail(OPEN_ID, only(SOURCE_ROOT_CHILD));
    await settleLineage();
    expect(renderedCols(container)).toEqual([0, 2, 3]);
    expect(arrowCount(container)).toBe(2);
    // 서버는 원천에 대응하는 edge 를 주지 않는다 — 라벨 없는 화살표 하나이지 빈 칸이 아니다
    const rails = container.querySelectorAll('.lin-rail');
    expect(rails).toHaveLength(2);
    expect(rails[0]!.querySelectorAll('[data-testid="lin-method"]')).toHaveLength(0);
    expect(rails[0]!.textContent).toContain('→');
  });

  it('원천 관계가 실려 와도 같은 그림이다 — 화살표 2 · 라벨 0 (BF-9 완료 정의 ⑵)', async () => {
    // **관계가 하나 늘었는데 그림은 그대로여야 한다.** 늘어난 관계에 `method` 가 없으므로
    // 레일에 라벨이 생기지 않고, 원천은 자기 칸(0)에 이미 서 있으므로 칸도 늘지 않는다.
    const before = renderDetail(OPEN_ID, only(SOURCE_ROOT_CHILD));
    await settleLineage();
    const shape = {
      cols: renderedCols(before.container),
      arrows: arrowCount(before.container),
      rails: before.container.querySelectorAll('.lin-rail').length,
      methods: before.container.querySelectorAll('[data-testid="lin-method"]').length,
      rows: before.container.querySelectorAll('[data-testid="lrow"]').length,
    };
    expect(shape).toEqual({ cols: [0, 2, 3], arrows: 2, rails: 2, methods: 1, rows: 3 });
    before.unmount();

    const { container } = renderDetail(OPEN_ID, only(SOURCE_ROOT_CHILD_WITH_EDGE));
    await settleLineage();
    expect({
      cols: renderedCols(container),
      arrows: arrowCount(container),
      rails: container.querySelectorAll('.lin-rail').length,
      methods: container.querySelectorAll('[data-testid="lin-method"]').length,
      rows: container.querySelectorAll('[data-testid="lrow"]').length,
    }).toEqual(shape);
    // 원천 행은 노드에서 오지 관계에서 오지 않는다 — **행이 겹쳐 생기지 않는다.**
    const srcRows = Array.from(container.querySelectorAll('[data-testid="lrow"]')).filter(
      (r) => (r as HTMLElement).dataset.stage === '원천',
    );
    expect(srcRows).toHaveLength(1);
  });

  it('기록 없음은 원천 관계 하나로 뒤집히지 않는다 (BF-9 완료 정의 ⑵)', async () => {
    // 「기록 없음」은 **가공 전 데이터를 모른다**는 뜻이다. 연구실 밖 출처 표기가 실려 왔다고
    // 빈 상태가 사라지면 edge 유무로 그림이 갈린다.
    const unknown: LineageGraph = {
      ...BASE,
      unknownParents: true,
      projectUseCount: 0,
      nodes: [
        { kind: '원천', datasetId: null, name: 'NMSC', processingLevel: null,
          verified: false, navigable: false, bodyAccessible: true, deletedAt: null },
        { kind: '이 데이터', datasetId: OPEN_ID, name: 'nakdong_raw_2025_Lv0.nc',
          processingLevel: 0, verified: true, navigable: false, bodyAccessible: true,
          deletedAt: null },
      ],
      edges: [],
    };
    const withEdge: LineageGraph = {
      ...unknown,
      edges: [
        { childDatasetId: OPEN_ID, parentDatasetId: null, parentRole: '주입력', method: null,
          origin: 'manual', confirmedBy: 호랑이, confirmedAt: '2026-08-03T00:00:00Z' },
      ],
    };
    for (const g of [unknown, withEdge]) {
      const { unmount } = renderDetail(OPEN_ID, only(g));
      await settleLineage();
      expect(screen.getByTestId('lin-empty')).toBeInTheDocument();
      unmount();
    }
  });

  it('렌더된 칸은 모두 노드를 하나 이상 담는다', async () => {
    for (const g of [ROOT_WITH_CHILD, LEAF_WITH_PARENT, SOURCE_ROOT_CHILD,
      SOURCE_ROOT_CHILD_WITH_EDGE, BASE]) {
      const { container, unmount } = renderDetail(OPEN_ID, only(g));
      await settleLineage();
      const cols = Array.from(container.querySelectorAll('[data-testid="lin-col"]'));
      expect(cols.length).toBeGreaterThan(0);
      for (const c of cols) {
        expect(c.querySelectorAll('[data-testid="lin-node"]').length).toBeGreaterThan(0);
      }
      unmount();
    }
  });

  it('화살표 개수는 언제나 렌더된 칸 수 − 1 이다', async () => {
    for (const g of [ROOT_WITH_CHILD, LEAF_WITH_PARENT, SOURCE_ROOT_CHILD,
      SOURCE_ROOT_CHILD_WITH_EDGE, BASE]) {
      const { container, unmount } = renderDetail(OPEN_ID, only(g));
      await settleLineage();
      const cols = renderedCols(container);
      expect(cols.length).toBeGreaterThan(0);
      expect(arrowCount(container)).toBe(cols.length - 1);
      expect(cols).toEqual([...cols].sort((a, b) => a - b));
      unmount();
    }
  });
});

describe('§8 계보 노드 이동', () => {
  it('데이터 노드(가공 전·파생)를 누르면 그 데이터셋 상세로 간다', async () => {
    renderDetail(OPEN_ID);
    await settleLineage();
    const movable = screen
      .getAllByTestId('lin-node')
      .filter((n) => n.dataset.kind === '가공 전' || n.dataset.kind === '파생');
    expect(movable.length).toBe(2);
    expect(movable.map((n) => n.getAttribute('href'))).toEqual([
      `/datasets/${PARENT_ID}`,
      `/datasets/${CHILD_ID}`,
    ]);
  });

  it('원천 노드는 이동하지 않고 hover 문구를 준다', async () => {
    renderDetail(OPEN_ID);
    await settleLineage();
    const src = screen.getAllByTestId('lin-node').filter((n) => n.dataset.kind === '원천');
    expect(src.length).toBe(2);
    for (const n of src) {
      expect(n.tagName).not.toBe('A');
      expect(n).toHaveAttribute('title', '연구실 밖 출처라 상세 화면이 없어요');
    }
  });

  it('잠긴 데이터 노드는 사라지지 않고 눌리면 잠긴 상세로 간다', async () => {
    const locked: LineageGraph = {
      ...BASE,
      nodes: BASE.nodes.map((n) =>
        n.datasetId === PARENT_ID ? { ...n, bodyAccessible: false } : n,
      ),
    };
    renderDetail(OPEN_ID, only(locked));
    await settleLineage();
    const node = screen
      .getAllByTestId('lin-node')
      .filter((n) => n.dataset.datasetId === PARENT_ID);
    expect(node).toHaveLength(1); // 사라지지 않는다
    expect(node[0]!).toHaveAttribute('href', `/datasets/${PARENT_ID}`);
  });

  it('묘비 노드는 남고 이름·가공 단계가 보이며 눌러도 이동하지 않는다', async () => {
    const tomb: LineageGraph = {
      ...BASE,
      nodes: BASE.nodes.map((n) =>
        n.datasetId === PARENT_ID
          ? { ...n, kind: '묘비' as const, navigable: false, deletedAt: '2026-08-09T00:00:00Z' }
          : n,
      ),
    };
    renderDetail(OPEN_ID, only(tomb));
    await settleLineage();
    const node = screen.getAllByTestId('lin-node').filter((n) => n.dataset.kind === '묘비');
    expect(node).toHaveLength(1);
    const t = node[0]!;
    expect(t.tagName).not.toBe('A');
    expect(t.textContent).toContain('ERA5_precip_2025_Lv1.grib');
    expect(t.textContent).toContain('Lv1');
    expect(t).toHaveAttribute('title', '지워진 데이터라 상세 화면이 없어요 · 2026-08-09');
    // 묘비의 화살표 라벨(가공 방식)도 그대로 보인다
    expect(screen.getAllByTestId('lin-method').map((l) => l.textContent).join(' ')).toContain(
      '유역 클리핑 · 유역 평균',
    );
    // 부모 자리의 묘비는 가공 전 칸(1열)에 선다
    expect(t.closest('[data-testid="lin-col"]')).toHaveAttribute('data-col', '1');
  });
});

describe('§8·§9 기록 없음 빈 상태 — 중립 톤', () => {
  it('관계 0건 + 기록 없음이면 그래프 대신 채우기 유도를 놓는다', async () => {
    const g = FIXTURE_LINEAGE[UNKNOWN_ID]!;
    expect(g.edges).toHaveLength(0); // 「관계가 없다」를 기대값으로 명시한다
    expect(g.unknownParents).toBe(true);
    renderDetail(UNKNOWN_ID);
    await settleLineage();
    expect(screen.queryByTestId('lin-graph')).toBeNull();
    const empty = screen.getByTestId('lin-empty');
    expect(within(empty).getByText('아직 채워지지 않은 계보예요')).toBeInTheDocument();
    // 경고가 아닌 중립 톤 — 위험·오류 어휘를 쓰지 않는다
    expect(empty.textContent).not.toMatch(/오류|실패|위험|잘못/);
  });

  it('관계가 붙어 있으면 기록 없음이 켜져 있어도 그래프를 그린다', async () => {
    const g: LineageGraph = { ...BASE, unknownParents: true };
    expect(g.edges.length).toBeGreaterThan(0);
    renderDetail(OPEN_ID, only(g));
    await settleLineage();
    expect(screen.getByTestId('lin-graph')).toBeInTheDocument();
    // §5 — 기록 없음 표시가 있으면 경고 칩
    expect(screen.getByTestId('lin-unknown-chip')).toHaveTextContent('기록 없음');
  });

  it('기록 없음이 아니면 경고 칩을 띄우지 않는다', async () => {
    expect(BASE.unknownParents).toBe(false);
    renderDetail(OPEN_ID);
    await settleLineage();
    expect(screen.queryByTestId('lin-unknown-chip')).toBeNull();
  });
});

describe('§8 계보 상세 행 — 경로 플래그와 확인 이력', () => {
  it('관계마다 한 행이고 파일명은 그 데이터셋 상세로 가는 링크다', async () => {
    renderDetail(OPEN_ID);
    await settleLineage();
    const rows = screen.getAllByTestId('lrow');
    expect(rows.length).toBeGreaterThan(0);
    const parentRow = rows.filter((r) => r.dataset.stage === '가공 전');
    expect(parentRow).toHaveLength(1);
    const link = within(parentRow[0]!).getByRole('link', {
      name: /ERA5_precip_2025_Lv1\.grib/,
    });
    expect(link).toHaveAttribute('href', `/datasets/${PARENT_ID}`);
  });

  it('행마다 경로 플래그와 확인자·확인일을 적는다', async () => {
    renderDetail(OPEN_ID);
    await settleLineage();
    const rows = screen
      .getAllByTestId('lrow')
      .filter((r) => r.dataset.stage === '가공 전' || r.dataset.stage === '파생');
    expect(rows.length).toBe(2);
    for (const r of rows) {
      expect(within(r).getByTestId('lin-flag')).toBeInTheDocument();
      expect(r.textContent).toMatch(/확인 .+ · \d{4}-\d{2}-\d{2}/);
    }
  });

  it('AI 경로의 플래그 문구는 `✦AI 제안 · 확인됨` 이다', async () => {
    renderDetail(OPEN_ID);
    await settleLineage();
    const ai = screen.getAllByTestId('lin-flag').filter((f) => f.dataset.origin === 'ai');
    expect(ai.length).toBe(2);
    for (const f of ai) expect(f.textContent).toBe('✦AI 제안 · 확인됨');
  });

  it('직접 연결의 플래그 문구는 `직접 연결` 이고 ✦ 가 없다', async () => {
    const manualGraph: LineageGraph = {
      ...BASE,
      edges: BASE.edges.map((e) => ({ ...e, origin: 'manual' as const })),
    };
    renderDetail(OPEN_ID, only(manualGraph));
    await settleLineage();
    const man = screen.getAllByTestId('lin-flag').filter((f) => f.dataset.origin === 'manual');
    expect(man.length).toBe(2);
    for (const f of man) expect(f.textContent).toBe('직접 연결');
  });

  it('파생 행은 읽기 전용이고 여기서 못 고친다고 알린다 (§3.2)', async () => {
    renderDetail(OPEN_ID);
    await settleLineage();
    const derived = screen.getAllByTestId('lrow').filter((r) => r.dataset.stage === '파생');
    expect(derived).toHaveLength(1);
    expect(derived[0]!.textContent).toContain('여기서는 못 고쳐요');
    expect(within(derived[0]!).queryByRole('button')).toBeNull();
  });

  it('원천 행은 이동 링크를 두지 않는다', async () => {
    renderDetail(OPEN_ID);
    await settleLineage();
    const src = screen.getAllByTestId('lrow').filter((r) => r.dataset.stage === '원천');
    expect(src).toHaveLength(1);
    expect(within(src[0]!).queryAllByRole('link')).toHaveLength(0);
    expect(src[0]!.textContent).toContain('연구실 밖 출처 표기라 열어 볼 상세 화면이 없어요');
  });
});

describe('§5·§8 활용 배지 — 노드가 아니라 표시다', () => {
  it('프로젝트 개수만 알리고 활용 섹션으로 점프한다', async () => {
    expect(BASE.projectUseCount).toBeGreaterThan(0);
    renderDetail(OPEN_ID);
    await settleLineage();
    const badge = screen.getByTestId('lin-usebadge');
    expect(badge.textContent).toContain(`활용 프로젝트 ${BASE.projectUseCount}건`);
    expect(badge).toHaveAttribute('href', '#sec-usage');
    // 노드가 아니다 — 노드 목록에 끼지 않는다
    expect(screen.getAllByTestId('lin-node')).not.toContain(badge);
  });

  it('0건이면 배지를 두지 않는다', async () => {
    const none: LineageGraph = { ...BASE, projectUseCount: 0 };
    renderDetail(OPEN_ID, only(none));
    await settleLineage();
    expect(screen.queryByTestId('lin-usebadge')).toBeNull();
  });
});

describe('§2·§3.2 확정 뒤 파일이 바뀌면 「이후 수정됨」', () => {
  it('확정일보다 마지막 수정이 나중이면 계보 구역 맨 위에 확정일·수정일을 나란히 놓는다', async () => {
    const d = FIXTURE_DETAILS[OPEN_ID]!;
    expect(d.lineageConfirmedAt).toBe('2026-07-30T00:00:00Z');
    expect(d.lastModifiedAt).toBe('2026-08-11T00:00:00Z');
    renderDetail(OPEN_ID);
    await settleLineage();
    const stale = screen.getByTestId('lin-stale');
    expect(stale.textContent).toContain('이후 수정됨');
    expect(stale.textContent).toContain('2026-07-30');
    expect(stale.textContent).toContain('2026-08-11');
    // 계보 구역의 맨 위다
    const section = screen.getByTestId('lineage-section');
    expect(section.querySelector('[data-testid="lin-stale"]')).toBe(stale);
    expect(stale.compareDocumentPosition(screen.getByTestId('lin-graph')) &
      Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it('확정 뒤 수정이 없으면 표시하지 않는다', async () => {
    const same = { ...FIXTURE_DETAILS[OPEN_ID]!, lastModifiedAt: '2026-07-30T00:00:00Z' };
    renderDetail(OPEN_ID, fixtureLineageSource(), { async get() { return same; } });
    await settleLineage();
    expect(screen.queryByTestId('lin-stale')).toBeNull();
  });
});

describe('§3.2·§6 보기 권한만 있는 사람에게는 편집 컨트롤이 없다', () => {
  it('canEdit 이 꺼지면 `계보 수정 · 추가` 가 화면에 없다', async () => {
    expect(BASE.canEdit).toBe(false);
    renderDetail(OPEN_ID);
    await settleLineage();
    expect(screen.queryByTestId('lin-edit')).toBeNull();
    expect(screen.queryByText('계보 수정 · 추가')).toBeNull();
  });

  it('canEdit 이 켜지면 E-04 검색 창을 여는 컨트롤이 선다', async () => {
    const editable: LineageGraph = { ...BASE, canEdit: true };
    renderDetail(OPEN_ID, only(editable));
    await settleLineage();
    const btn = screen.getByTestId('lin-edit');
    expect(btn).toHaveTextContent('계보 수정 · 추가');
  });

  it('빈 상태의 `계보 채우기` 도 같은 스위치로 갈린다', async () => {
    const g = FIXTURE_LINEAGE[UNKNOWN_ID]!;
    expect(g.canEdit).toBe(false);
    renderDetail(UNKNOWN_ID);
    await settleLineage();
    expect(screen.queryByText('계보 채우기')).toBeNull();

    renderDetail(UNKNOWN_ID, only({ ...g, canEdit: true }));
    expect(await screen.findByText('계보 채우기')).toBeInTheDocument();
  });
});

describe('§7 잠긴 상세 — 계보 섹션도 본문이라 나오지 않는다', () => {
  it('허용 목록 밖이면 계보 구역이 없다', async () => {
    expect(FIXTURE_DETAILS[LOCKED_ID]!.bodyAccessible).toBe(false);
    renderDetail(LOCKED_ID);
    await screen.findByTestId('locked-body-slot');
    expect(screen.queryByTestId('lineage-section')).toBeNull();
  });
});

describe('스키마가 주지 않는 값을 지어내지 않는다', () => {
  it('가공 방식이 null 인 관계는 화살표 라벨을 만들지 않는다', async () => {
    const nom: LineageGraph = { ...BASE, edges: BASE.edges.map((e) => ({ ...e, method: null })) };
    renderDetail(OPEN_ID, only(nom));
    await settleLineage();
    expect(screen.queryAllByTestId('lin-method')).toHaveLength(0);
    // 행은 그대로 서고 확인 이력은 남는다
    expect(screen.getAllByTestId('lrow').length).toBeGreaterThan(0);
  });

  it('가공 단계가 null 인 노드는 Lv 칩을 만들지 않는다', async () => {
    const noLv: LineageGraph = {
      ...BASE,
      nodes: BASE.nodes.map((n) => ({ ...n, processingLevel: null })),
    };
    renderDetail(OPEN_ID, only(noLv));
    await settleLineage();
    expect(screen.queryAllByTestId('lin-lv')).toHaveLength(0);
  });

  it('`processed` 경로는 정본이 문구를 주지 않아 플래그를 지어내지 않는다', async () => {
    const proc: LineageGraph = {
      ...BASE,
      edges: BASE.edges.map((e) => ({ ...e, origin: 'processed' as const })),
    };
    renderDetail(OPEN_ID, only(proc));
    await settleLineage();
    expect(screen.getAllByTestId('lrow').length).toBeGreaterThan(0);
    expect(screen.queryAllByTestId('lin-flag')).toHaveLength(0);
  });
});

describe('501 → 실서버 전환에 화면 코드가 바뀌지 않는다', () => {
  it('출처가 서버든 픽스처든 같은 컴포넌트가 같은 자리를 그린다', async () => {
    const fromServer: LineageGraph = {
      ...BASE,
      nodes: BASE.nodes.map((n) =>
        n.kind === '파생' ? { ...n, name: '서버가 내려준 파생 이름' } : n,
      ),
      projectUseCount: 5,
    };
    renderDetail(OPEN_ID, only(fromServer));
    await settleLineage();
    // 그래프 노드와 계보 상세 행이 **같은 값**을 쓴다 — 두 자리 모두에 선다
    expect(screen.getAllByText('서버가 내려준 파생 이름')).toHaveLength(2);
    expect(screen.getByTestId('lin-usebadge').textContent).toContain('활용 프로젝트 5건');
  });

  it('계보를 읽지 못하면 구역 자체를 그리지 않는다 — 빈 계보라고 말하지 않는다', async () => {
    const broken: LineageGraphSource = { async get() { throw new Error('boom'); } };
    renderDetail(OPEN_ID, broken);
    await screen.findByTestId('basic-info');
    expect(screen.queryByTestId('lineage-section')).toBeNull();
    expect(screen.queryByText('아직 채워지지 않은 계보예요')).toBeNull();
  });
});

describe('확인자 표기는 응답이 준 이름을 그대로 쓴다', () => {
  it('AccountRef 의 이름이 행에 그대로 실린다', async () => {
    const renamed: LineageGraph = {
      ...BASE,
      edges: BASE.edges.map((e) => ({ ...e, confirmedBy: 호랑이 })),
    };
    renderDetail(OPEN_ID, only(renamed));
    await settleLineage();
    const rows = screen.getAllByTestId('lrow').filter((r) => r.dataset.stage !== '원천'
      && r.dataset.stage !== '이 데이터');
    expect(rows.length).toBeGreaterThan(0);
    for (const r of rows) expect(r.textContent).toContain('확인 호랑이');
  });
});
