/**
 * WU-A12 — rev1 유지 항목 회귀 방어선 (PRD-39 · `R-A-4-verify.md` §A).
 *
 * 실측 13건 중 **`있음` 으로 판정된 5건**(#6 · #7 · #8 · #11 · #13)에 하나씩 건다.
 * 이 회차가 같은 화면(PRD-12·13·14·20·21·24·28)을 크게 고치므로, 방어선이 없으면
 * rev1 이 260825 에서 이어받은 행동이 고치는 중에 조용히 사라진다.
 *
 * ⛔ **이 시험은 고치지 않는다** — 지금 있는 것이 사라지면 red 가 되게만 한다.
 * **빈 집합 위에서 통과하지 않는다** — 모든 단언은 대상이 1건 이상임을 먼저 잰다
 * (green-by-skip 방지 · `CLAUDE.md §4`).
 *
 * 판정 근거는 세션 노트 `dev-package/sessions/p3-rev1-keep-audit-20260905.md` 의 13행 표다.
 */
import { fireEvent, render, screen, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { DatasetDetailPage } from '../src/routes/DatasetDetailPage';
import { fixtureDetailSource } from '../src/components/detail/fixture';
import { NotRenderableNotice } from '../src/components/preview/PreviewPanels';
import { LineageSection } from '../src/components/lineage/LineageSection';
import { FIXTURE_LINEAGE } from '../src/components/lineage/graphFixture';
import { BasicInfoGrid } from '../src/components/detail/BasicInfoGrid';
import { FileDropCard } from '../src/components/upload/FileDropCard';
import { formatFiles } from '../src/components/detail/format';
import type { DatasetPreviewSource } from '../src/components/datasetpreview/types';
import type { RenderJob } from '../src/components/preview/types';
import type { DatasetBasicInfo } from '../src/components/detail/types';
import type { FilesSource } from '../src/components/detail/filesSource';
import type { PickedFile } from '../src/components/upload/types';

const OPEN_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA1';

/* ──────────────────────────────────────────────────────────────────────────
 * #6 뷰어 휠 확대 · 끌어 이동 · `기본 배율로` 초기화
 *    rev1 근거 = `makePanZoom()` · `pvLatOf`/`pvLonOf`
 * ────────────────────────────────────────────────────────────────────────── */

const DONE: RenderJob = {
  renderId: '01JYZ9K7WQ3N8V4M2X6C5B0RE9',
  status: '완료',
  result: {
    imageUrl: 'https://viz.example/d/map.png',
    legend: {
      palette: 'viridis',
      unit: 'mm',
      classes: [
        { color: '#440154', min: 0, max: 5 },
        { color: '#21918c', min: 5, max: 10 },
      ],
    },
    bounds: { west: 126, south: 34, east: 130, north: 38 },
  },
} as unknown as RenderJob;

function previewSource(): DatasetPreviewSource {
  return {
    palettes: vi.fn(async () => [{ palette: 'viridis' }]),
    create: vi.fn(async () => DONE),
    get: vi.fn(async () => DONE),
    probeTile: vi.fn(async () => 'ok' as const),
    mapGeometry: vi.fn(async () => undefined),
    lookupValue: vi.fn(async () => {
      throw new Error('이 시험은 값 조회를 부르지 않는다');
    }),
    screenshot: vi.fn(async () => new Blob([new Uint8Array([1])], { type: 'image/png' })),
  } as unknown as DatasetPreviewSource;
}

/** jsdom 은 픽셀을 재지 않는다 — 한계 배율(4096/512 = 8)을 심고 `load` 를 알린다. */
async function drawnMap() {
  await screen.findByTestId('preview-map');
  const viewport = screen.getByTestId('preview-viewport');
  Object.defineProperty(viewport, 'clientWidth', { value: 512, configurable: true });
  Object.defineProperty(viewport, 'clientHeight', { value: 512, configurable: true });
  const img = viewport.querySelector('img') as HTMLImageElement;
  Object.defineProperty(img, 'naturalWidth', { value: 4096, configurable: true });
  Object.defineProperty(img, 'naturalHeight', { value: 4096, configurable: true });
  fireEvent.load(img);
  return viewport;
}

function scaleOf(): number {
  return Number(screen.getByTestId('preview-layers').getAttribute('data-zoom-scale'));
}

function renderDetailPreview() {
  return render(
    <MemoryRouter initialEntries={[`/datasets/${OPEN_ID}`]}>
      <Routes>
        <Route
          path="/datasets/:datasetId"
          element={
            <DatasetDetailPage source={fixtureDetailSource()} previewSource={previewSource()} />
          }
        />
      </Routes>
    </MemoryRouter>,
  );
}

describe('rev1 #6 — 뷰어 휠 확대 · 끌어 이동 · 초기화', () => {
  it('휠을 올리면 배율이 올라간다 (`makePanZoom` 의 휠 확대)', async () => {
    renderDetailPreview();
    const viewport = await drawnMap();
    expect(scaleOf()).toBe(1);
    fireEvent.wheel(viewport, { deltaY: -100, clientX: 256, clientY: 256 });
    expect(scaleOf()).toBeGreaterThan(1);
  });

  it('끌면 보는 자리가 움직인다 (`makePanZoom` 의 끌어 이동)', async () => {
    renderDetailPreview();
    const viewport = await drawnMap();
    fireEvent.click(screen.getByRole('button', { name: '확대' }));
    const before = screen.getByTestId('preview-layers').style.transform;
    expect(before).not.toBe('');
    fireEvent.mouseDown(viewport, { clientX: 300, clientY: 300 });
    fireEvent.mouseMove(window, { clientX: 240, clientY: 260 });
    fireEvent.mouseUp(window);
    expect(screen.getByTestId('preview-layers').style.transform).not.toBe(before);
  });

  it('`기본 배율로` 가 확대·이동을 한 번에 되돌린다 (rev1 `초기화`)', async () => {
    renderDetailPreview();
    await drawnMap();
    fireEvent.click(screen.getByRole('button', { name: '확대' }));
    expect(scaleOf()).toBeGreaterThan(1);
    fireEvent.click(screen.getByRole('button', { name: '기본 배율로' }));
    expect(scaleOf()).toBe(1);
  });
});

/* ──────────────────────────────────────────────────────────────────────────
 * #7 상세 미리보기 실패 문면 ＋ 그릴 수 있는 형식
 *    rev1 근거 = `이 형식은 아직 지도로 못 그려요` ＋ 지원 `bin · nc · tif · HDF`
 * ────────────────────────────────────────────────────────────────────────── */

describe('rev1 #7 — 그릴 수 없는 형식의 문면과 지원 형식 나열', () => {
  const FORMATS = ['bin', 'nc', 'tif', 'HDF'];

  it('실패 문면과 함께 **서버가 준** 지원 형식을 잇는다', () => {
    expect(FORMATS.length).toBeGreaterThan(0);
    render(
      <NotRenderableNotice
        message="이 형식은 아직 지도로 못 그려요."
        renderableFormats={FORMATS}
      />,
    );
    const box = screen.getByTestId('not-renderable');
    expect(box).toHaveTextContent('이 형식은 아직 지도로 못 그려요.');
    expect(box).toHaveTextContent('지금 그릴 수 있는 형식은 bin · nc · tif · HDF 예요.');
    // 못 그리는 것과 못 쓰는 것은 다르다 — 남은 길을 함께 말한다
    expect(box).toHaveTextContent('등록·계보 확정·다운로드는 그대로 할 수 있어요.');
  });

  it('형식 목록이 비면 **줄을 지어내지 않는다** — 문면만 남는다', () => {
    render(<NotRenderableNotice message="이 형식은 아직 지도로 못 그려요." renderableFormats={[]} />);
    expect(screen.getByTestId('not-renderable')).not.toHaveTextContent('지금 그릴 수 있는 형식은');
  });
});

/* ──────────────────────────────────────────────────────────────────────────
 * #8 계보 그래프 노드 이동 ＋ 원천 노드는 이동 없음
 *    rev1 근거 = `goDataset()` · `<title>연구실 밖 출처라 상세 화면이 없어요`
 * ────────────────────────────────────────────────────────────────────────── */

describe('rev1 #8 — 계보 노드 이동과 원천 노드의 이동 없음', () => {
  const GRAPH = FIXTURE_LINEAGE[OPEN_ID]!;

  function renderGraph() {
    return render(
      <MemoryRouter>
        <LineageSection graph={GRAPH} />
      </MemoryRouter>,
    );
  }

  it('이동 가능한 노드는 그 데이터셋 상세로 가는 링크다', () => {
    const navigable = GRAPH.nodes.filter((n) => n.navigable && n.datasetId);
    expect(navigable.length).toBeGreaterThan(0);
    renderGraph();
    const graph = screen.getByTestId('lin-graph');
    for (const n of navigable) {
      const node = within(graph)
        .getAllByTestId('lin-node')
        .find((el) => el.getAttribute('data-dataset-id') === n.datasetId);
      expect(node).toBeDefined();
      expect(node!.tagName).toBe('A');
      expect(node!.getAttribute('href')).toBe(`/datasets/${n.datasetId}`);
    }
  });

  it('원천 노드는 링크가 아니고 사유를 `title` 로 말한다', () => {
    const sources = GRAPH.nodes.filter((n) => n.kind === '원천');
    expect(sources.length).toBeGreaterThan(0);
    renderGraph();
    const nodes = within(screen.getByTestId('lin-graph'))
      .getAllByTestId('lin-node')
      .filter((el) => el.getAttribute('data-kind') === '원천');
    expect(nodes.length).toBe(sources.length);
    for (const el of nodes) {
      expect(el.tagName).not.toBe('A');
      expect(el.getAttribute('title')).toBe('연구실 밖 출처라 상세 화면이 없어요');
    }
  });
});

/* ──────────────────────────────────────────────────────────────────────────
 * #11 파일 목록 접힘 기본 ＋ 조각별 기간 없음
 *     rev1 근거 = `toggleFiles()`
 * ────────────────────────────────────────────────────────────────────────── */

const BASIC: DatasetBasicInfo = {
  variables: ['강수량'],
  crs: 'EPSG:4326',
  period: { start: '2025-06-01T00:00:00Z', end: '2025-09-30T00:00:00Z' },
  grid: '1 km',
  format: 'NetCDF',
  files: { count: 4, totalSizeBytes: 148 * 1024 ** 2 },
  sourceLabel: 'ERA5 재분석',
  owner: { accountId: '01JYZ9K7WQ3N8V4M2X6C5B0U01', name: '호랑이' },
  uploader: { accountId: '01JYZ9K7WQ3N8V4M2X6C5B0U01', name: '호랑이' },
} as unknown as DatasetBasicInfo;

const FILES = [
  { fileId: 'f1', fileName: 'part_202506.nc', kind: '본체', gridAxis: null },
  { fileId: 'f2', fileName: 'part_202507.nc', kind: '본체', gridAxis: null },
];

function filesSource(): { source: FilesSource; list: ReturnType<typeof vi.fn> } {
  const list = vi.fn(async () => FILES as never);
  return { source: { list } as unknown as FilesSource, list };
}

describe('rev1 #11 — 파일 목록은 접힘이 기본이고 조각별 기간을 달지 않는다', () => {
  it('열기 전에는 목록도 없고 조각 목록을 **부르지도 않는다**', () => {
    const { source, list } = filesSource();
    render(
      <BasicInfoGrid basicInfo={BASIC} fileName={null} datasetId={OPEN_ID} filesSource={source} />,
    );
    expect(screen.queryByTestId('file-list')).toBeNull();
    expect(list).not.toHaveBeenCalled();
    expect(screen.getByRole('button', { name: '보기' })).toBeInTheDocument();
  });

  it('`보기` 를 눌러야 펴지고, 조각 행에 기간 칸이 없다', async () => {
    const { source } = filesSource();
    render(
      <BasicInfoGrid basicInfo={BASIC} fileName={null} datasetId={OPEN_ID} filesSource={source} />,
    );
    fireEvent.click(screen.getByRole('button', { name: '보기' }));
    const list = await screen.findByTestId('file-list');
    const rows = within(list).getAllByRole('listitem');
    expect(rows.length).toBe(FILES.length);
    // 기간은 데이터셋 한 곳(기본 정보 `기간` 칸)에서만 말한다 — 조각마다 달지 않는다
    for (const row of rows) {
      expect(row.textContent ?? '').not.toMatch(/2025-\d{2}-\d{2}|기간/);
    }
    // 접었다 편 것이 아니라 **접힘이 기본**이었음을 되짚는다
    fireEvent.click(screen.getByRole('button', { name: '접기' }));
    expect(screen.queryByTestId('file-list')).toBeNull();
  });

  it('업로드 모달의 조각 묶음도 접힘이 기본이다', () => {
    const picked: PickedFile[] = [1, 2, 3].map((i) => ({
      file: new File([new Uint8Array(1024)], `part_${i}.nc`),
      kind: '본체' as const,
    }));
    render(<FileDropCard picked={picked} onPick={() => {}} onKind={() => {}} />);
    expect(screen.getByTestId('up-bundle')).toBeInTheDocument();
    expect(screen.queryByTestId('up-slices')).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: `조각 ${picked.length}개 모두 보기` }));
    expect(screen.getByTestId('up-slices')).toBeInTheDocument();
  });
});

/* ──────────────────────────────────────────────────────────────────────────
 * #13 데이터셋 용량 = 조각 합계
 *     rev1 근거 = `totalSize()` · `POL-022`
 * ────────────────────────────────────────────────────────────────────────── */

describe('rev1 #13 — 용량은 조각의 합계다', () => {
  it('상세 `파일` 칸이 조각 수와 **합계** 용량을 함께 말한다', () => {
    expect(BASIC.files.count).toBeGreaterThan(1);
    expect(formatFiles(BASIC.files, null)).toBe('조각 4개 · 합계 148 MB');
  });

  it('업로드 조각 묶음의 용량이 조각 크기의 합이다 — 첫 조각 하나가 아니다', () => {
    const sizes = [1024 ** 2, 2 * 1024 ** 2, 3 * 1024 ** 2];
    const picked: PickedFile[] = sizes.map((n, i) => ({
      file: new File([new Uint8Array(n)], `part_${i}.nc`),
      kind: '본체' as const,
    }));
    render(<FileDropCard picked={picked} onPick={() => {}} onKind={() => {}} />);
    const bundle = screen.getByTestId('up-bundle');
    expect(bundle).toHaveTextContent('합계 6 MB');
    expect(bundle).not.toHaveTextContent('합계 1 MB');
  });
});
