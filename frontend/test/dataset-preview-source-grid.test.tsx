/**
 * S-05 데이터셋 상세 미리보기 — **원본 격자 간격·크기 표기** (버그 13 · Ted 판정).
 *
 * Ted 요청 축자 「상세에서 원본 픽셀 크기를 알 수 있게 해 달라」. 상세는 이미 두 값을
 * 들고 있다 —
 *  · 격자 간격/해상도 = `DatasetBasicInfo.grid`(`fe-core.yaml` · 상세가 이미 읽어 온 값)
 *  · 원본 배열 크기 = ③지도형 사이드카의 `width`·`height`
 *    (`DatasetPreviewSource.mapGeometry` · 정본 v2.6 `§8` 조건 ⑷ 가 이미 확대 한계를
 *    재려고 쓰는 바로 그 값 — `dataset-preview-zoom.test.tsx`·`dataset-preview-tiles.test.tsx`
 *    참고).
 *
 * **새 API·계약을 만들지 않는다** — 둘 다 화면이 이미 받는 값을 머리에 옮겨 적을 뿐이다.
 * 어느 한쪽이 없으면 **그 조각만 뺀다** — 없는 값을 지어내지 않는다.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { DatasetDetailPage } from '../src/routes/DatasetDetailPage';
import { FIXTURE_DETAILS, fixtureDetailSource } from '../src/components/detail/fixture';
import type { RenderJob } from '../src/components/preview/types';
import type { DatasetPreviewSource } from '../src/components/datasetpreview/types';

const OPEN_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA1'; // 낙동강 유역 강우 (2025) · basicInfo.grid = '0.05° (~5km)'
const RENDER_ID = '01JYZ9K7WQ3N8V4M2X6C5B0RE9';

const LEGEND = {
  palette: 'viridis',
  unit: 'mm',
  classes: [{ color: '#440154', min: 0, max: 5 }],
};

/** 타일(③지도형) 갈래 — 등록된 데이터셋의 지도 화면은 이 갈래다(`〈238〉`). */
const TILED_DONE: RenderJob = {
  renderId: RENDER_ID,
  status: '완료',
  result: {
    tileUrlTemplate: 'https://viz.example/viz/v1/renders/R/tiles/{z}/{x}/{y}.png?exp=1&sig=a',
    sidecarUrl: 'https://viz.example/p/map.json',
    legend: LEGEND,
    bounds: { west: 126, south: 34, east: 130, north: 38 },
  },
} as unknown as RenderJob;

/**
 * ⭑ ⟨staging 실측 2026-09-04 · `PLAN-SoT §9 〈312〉`⟩ **이미지 갈래인데 ③지도형**.
 * 타일 갈래 스위치(`COLAB_VIZ_TILE_BRANCH`)는 **기본이 꺼짐**이고(`〈240〉` 판정 ⑬ ·
 * 「기본은 한 장」) staging 홈 env 에 선언이 없다 — 그래서 실제 화면이 받는 결과는
 * `imageUrl` ＋ `sidecarUrl` 이다. 계약도 그 모양을 허락한다: `sidecarUrl` 은
 * `tileUrlTemplate` 에 딸린 값이 아니라 **③지도형이면 실리는 값**이고
 * (`core-viz.yaml` `dependentRequired: sidecarUrl → bounds`), 굽는 쪽도 갈래와
 * 무관하게 싣는다(`jobs.py` — `map_image`·`geometry` 가 있으면 `sidecarUrl`).
 */
const IMAGE_MAP_DONE: RenderJob = {
  renderId: RENDER_ID,
  status: '완료',
  result: {
    imageUrl: 'https://viz.example/p/map.png',
    sidecarUrl: 'https://viz.example/p/map.json',
    worldFileUrl: 'https://viz.example/p/map.pgw',
    legend: LEGEND,
    bounds: { west: 126, south: 34, east: 130, north: 38 },
  },
} as unknown as RenderJob;

/** 이미지(②비지도형) 갈래 — 사이드카가 없어 `mapGeometry` 를 아예 묻지 않는다. */
const IMAGE_DONE: RenderJob = {
  renderId: RENDER_ID,
  status: '완료',
  result: { imageUrl: 'https://viz.example/d/map.png', legend: LEGEND },
} as unknown as RenderJob;

function makeSource(over: Partial<DatasetPreviewSource> = {}): DatasetPreviewSource {
  return {
    palettes: vi.fn(async () => [{ palette: 'viridis' }]),
    create: vi.fn(async () => TILED_DONE),
    get: vi.fn(async () => TILED_DONE),
    probeTile: vi.fn(async () => 'ok' as const),
    mapGeometry: vi.fn(async () => ({ width: 126, height: 128 })),
    lookupValue: vi.fn(async () => {
      throw new Error('이 시험은 값 조회를 부르지 않는다');
    }),
    screenshot: vi.fn(async () => new Blob([new Uint8Array([1])], { type: 'image/png' })),
    ...over,
  };
}

function renderDetail(
  previewSource: DatasetPreviewSource,
  details: Record<string, (typeof FIXTURE_DETAILS)[string]> = FIXTURE_DETAILS,
) {
  return render(
    <MemoryRouter initialEntries={[`/datasets/${OPEN_ID}`]}>
      <Routes>
        <Route
          path="/datasets/:datasetId"
          element={
            <DatasetDetailPage
              source={fixtureDetailSource(details)}
              previewSource={previewSource}
            />
          }
        />
        <Route path="/datasets" element={<div>카탈로그</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('§8 — 미리보기 머리가 원본 격자 간격·크기를 말한다 (버그 13 · Ted 판정)', () => {
  it('격자 해상도와 원본 배열 크기를 함께 캡션으로 낸다', async () => {
    renderDetail(makeSource());
    await screen.findByTestId('preview-map');
    await waitFor(() =>
      expect(screen.getByTestId('preview-source-grid').textContent).toContain('0.05° (~5km)'),
    );
    expect(screen.getByTestId('preview-source-grid').textContent).toContain('126 × 128');
  });

  it('원본 크기를 못 재면(②비지도형) 격자 해상도만 낸다 — 없는 값을 지어내지 않는다', async () => {
    const source = makeSource({ create: vi.fn(async () => IMAGE_DONE), get: vi.fn(async () => IMAGE_DONE) });
    renderDetail(source);
    await screen.findByTestId('preview-map');
    expect(screen.getByTestId('preview-source-grid').textContent).toContain('0.05° (~5km)');
    expect(screen.getByTestId('preview-source-grid').textContent).not.toContain('×');
    expect(source.mapGeometry).not.toHaveBeenCalled();
  });

  it('타일 갈래가 꺼져 있어도(이미지 ＋ 사이드카) 원본 배열 크기가 캡션에 선다', async () => {
    // staging 실측 결함 — 캡션이 `격자 …` 까지만 나오고 「· W × H」 가 3 데이터셋 전부 빠졌다.
    // 원인은 자료가 아니라 **화면이 사이드카를 타일 갈래에서만 물었다**는 것이다.
    const source = makeSource({
      create: vi.fn(async () => IMAGE_MAP_DONE),
      get: vi.fn(async () => IMAGE_MAP_DONE),
      mapGeometry: vi.fn(async () => ({ width: 821, height: 1024 })),
    });
    renderDetail(source);
    await screen.findByTestId('preview-map');
    await waitFor(() =>
      expect(screen.getByTestId('preview-source-grid').textContent).toContain('821 × 1024'),
    );
    expect(screen.getByTestId('preview-source-grid').textContent).toContain('0.05° (~5km)');
    expect(source.mapGeometry).toHaveBeenCalledWith('https://viz.example/p/map.json');
  });

  it('격자 해상도가 없어도(GK-2A) 원본 배열 크기만으로 캡션이 선다', async () => {
    // staging 실측 — GK-2A 는 `basicInfo.grid` 가 없어 **캡션 자리가 통째로 빠졌다**.
    // 사이드카가 말하는 크기가 있으면 그 조각만으로 캡션이 서야 한다(Ted Q2).
    const noGrid = {
      ...FIXTURE_DETAILS,
      [OPEN_ID]: {
        ...FIXTURE_DETAILS[OPEN_ID]!,
        basicInfo: { ...FIXTURE_DETAILS[OPEN_ID]!.basicInfo!, grid: null },
      },
    };
    const source = makeSource({
      create: vi.fn(async () => IMAGE_MAP_DONE),
      get: vi.fn(async () => IMAGE_MAP_DONE),
      mapGeometry: vi.fn(async () => ({ width: 821, height: 1024 })),
    });
    renderDetail(source, noGrid);
    await screen.findByTestId('preview-map');
    await waitFor(() =>
      expect(screen.getByTestId('preview-source-grid').textContent).toBe('821 × 1024'),
    );
  });

  it('격자 해상도도 원본 크기도 없으면 자리째 없다', async () => {
    const noGrid = {
      ...FIXTURE_DETAILS,
      [OPEN_ID]: {
        ...FIXTURE_DETAILS[OPEN_ID]!,
        basicInfo: { ...FIXTURE_DETAILS[OPEN_ID]!.basicInfo!, grid: null },
      },
    };
    const source = makeSource({ create: vi.fn(async () => IMAGE_DONE), get: vi.fn(async () => IMAGE_DONE) });
    renderDetail(source, noGrid);
    await screen.findByTestId('preview-map');
    expect(screen.queryByTestId('preview-source-grid')).toBeNull();
  });
});
