/**
 * WU-C5 — **자립형 벡터 배경 지도** 시험 (축 ①-⑤b · POL-021 부분 반전).
 *
 * 오라클
 *  · R-C spec 「배경 = 자립형 Natural Earth 1:110m 해안선＋국경」 — 도시 없음 ·
 *    **외부 요청 0** · 파일 500KB 상한 · `bounds` 있는 결과에만.
 *  · 판정(intent `2026-09-08-preview-slot.md ⑤(b)`) — 타일 서버 0 · CDN 0 ·
 *    지도 라이브러리 0 · 한반도 고정 프레임 철회(다른 지역이 나올 수 있다).
 *
 * ⚠ **크기와 좌표를 이 파일에 다시 적지 않는다** — 상한 상수 하나만 두고 실제 파일을
 *   `fs.statSync` 로 잰다. 자산이 사라지면 `statSync` 가 먼저 던진다(green-by-skip 방지).
 */
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { statSync } from 'node:fs';
import { resolve } from 'node:path';
import { DatasetDetailPage } from '../src/routes/DatasetDetailPage';
import { fixtureDetailSource } from '../src/components/detail/fixture';
import type { RenderJob, RenderResult } from '../src/components/preview/types';
import type { DatasetPreviewSource } from '../src/components/datasetpreview/types';
import { basemapPathData } from '../src/components/preview/BasemapLayer';
import { lonFractionOf, latFractionOf } from '../src/components/preview/projection';
import { pvLonOf, pvLatOf } from '../src/components/preview/PreviewPanels';
import type { GeoBounds } from '../src/components/preview/scaleLadder';
import coastline from '../src/assets/basemap/ne_110m_coastline.json';
import boundaries from '../src/assets/basemap/ne_110m_admin_0_boundary_lines_land.json';

/** 판정 축자 「파일 상한 500KB」. 값은 **여기 한 자리**에만 산다. */
const SIZE_CAP_BYTES = 500 * 1024;

const ASSET_DIR = resolve(__dirname, '../src/assets/basemap');
const ASSETS = ['ne_110m_coastline.json', 'ne_110m_admin_0_boundary_lines_land.json'] as const;

const OPEN_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA1';
const RENDER_ID = '01JYZ9K7WQ3N8V4M2X6C5B0RE9';

/** 한반도를 담는 경계 — 「다른 지역이 나올 수도 있다」의 반대 극이 아니라, **잴 수 있는** 한 예다. */
const KOREA: GeoBounds = { west: 124, south: 33, east: 132, north: 39 };

const LEGEND = {
  palette: 'viridis',
  unit: 'mm',
  classes: [{ color: '#440154', min: 0, max: 5 }],
};

function makeSource(bounds?: GeoBounds): DatasetPreviewSource {
  const result: RenderResult = {
    imageUrl: 'https://viz.example/d/map.png',
    legend: LEGEND,
    ...(bounds ? { bounds } : {}),
  } as unknown as RenderResult;
  const job: RenderJob = { renderId: RENDER_ID, status: '완료', result } as unknown as RenderJob;
  return {
    palettes: vi.fn(async () => [{ palette: 'viridis' }]),
    create: vi.fn(async () => job),
    get: vi.fn(async () => job),
    probeTile: vi.fn(async () => 'ok' as const),
    mapGeometry: vi.fn(async () => undefined),
    lookupValue: vi.fn(async () => {
      throw new Error('이 시험은 값 조회를 부르지 않는다');
    }),
    screenshot: vi.fn(async () => new Blob([new Uint8Array([1])], { type: 'image/png' })),
  } as unknown as DatasetPreviewSource;
}

function renderDetail(previewSource: DatasetPreviewSource) {
  return render(
    <MemoryRouter initialEntries={[`/datasets/${OPEN_ID}`]}>
      <Routes>
        <Route
          path="/datasets/:datasetId"
          element={
            <DatasetDetailPage source={fixtureDetailSource()} previewSource={previewSource} />
          }
        />
      </Routes>
    </MemoryRouter>,
  );
}

afterEach(() => {
  vi.restoreAllMocks();
});

/* ── ⓐ 자산 — 레포 안에 있고, 상한 안이다 ───────────────────────────── */

describe('자산 — 자립형이라는 말은 파일이 레포에 있다는 뜻이다', () => {
  it('두 파일이 실제로 있고, 각각도 합계도 500KB 이하다', () => {
    let total = 0;
    for (const name of ASSETS) {
      // 없으면 `statSync` 가 던진다 — 「자산 없음」이 green 으로 새지 않는다.
      const size = statSync(resolve(ASSET_DIR, name)).size;
      expect(size).toBeGreaterThan(0);
      expect(size).toBeLessThanOrEqual(SIZE_CAP_BYTES);
      total += size;
    }
    expect(total).toBeLessThanOrEqual(SIZE_CAP_BYTES);
  });

  it('두 층 모두 선이 **한 줄 이상** 들어 있다 — 빈 껍데기가 아니다', () => {
    expect(coastline.features.length).toBeGreaterThanOrEqual(1);
    expect(boundaries.features.length).toBeGreaterThanOrEqual(1);
    expect(basemapPathData(coastline as never, KOREA).length).toBeGreaterThan(0);
    expect(basemapPathData(boundaries as never, KOREA).length).toBeGreaterThan(0);
  });

  it('도시 표기가 없다 — 점(Point) 기하가 한 건도 없다', () => {
    for (const fc of [coastline, boundaries]) {
      for (const f of fc.features) {
        expect(f.geometry.type).toMatch(/LineString$/);
      }
    }
  });
});

/* ── ⓑ 좌표계 — 배경과 커서 역산이 같은 사각형을 읽는다 ─────────────── */

describe('좌표 변환 — 정본은 한 자리다', () => {
  it('정투영과 커서 역산이 서로의 역이다 — 부산 앞바다 한 점으로 왕복', () => {
    // 부산 앞바다 (경도 129.05 · 위도 35.10) — KOREA 경계 **안**의 점이다.
    const lon = 129.05;
    const lat = 35.1;
    const fx = lonFractionOf(lon, KOREA);
    const fy = latFractionOf(lat, KOREA);
    expect(fx).toBeGreaterThan(0);
    expect(fx).toBeLessThan(1);
    expect(fy).toBeGreaterThan(0);
    expect(fy).toBeLessThan(1);
    // 틀 400×300 · 배율 1 · 이동 0 에서, 그 비율이 가리키는 픽셀을 역산하면 원래 값이다.
    const zoom = { scale: 1, x: 0, y: 0 };
    expect(pvLonOf(fx * 400, 400, KOREA, zoom)).toBeCloseTo(lon, 9);
    expect(pvLatOf(fy * 300, 300, KOREA, zoom)).toBeCloseTo(lat, 9);
  });

  it('경계 밖의 점은 0..1 밖으로 나간다 — 잘라서 가장자리로 답하지 않는다', () => {
    expect(lonFractionOf(KOREA.west - 10, KOREA)).toBeLessThan(0);
    expect(latFractionOf(KOREA.north + 10, KOREA)).toBeLessThan(0);
  });
});

/* ── ⓒ 화면 — 경계가 있을 때만 선다 ─────────────────────────────────── */

describe('배경 층 — `bounds` 있는 결과에만 선다', () => {
  it('지도형 결과에 배경 SVG 가 **정확히 1개**', async () => {
    renderDetail(makeSource(KOREA));
    await screen.findByTestId('preview-map');
    await waitFor(() => expect(screen.getAllByTestId('pv-basemap')).toHaveLength(1));
    // 해안선·국경 두 층이 각각 한 줄 이상 그려진다.
    expect(screen.getByTestId('pv-basemap-coastline').getAttribute('d')?.length).toBeGreaterThan(0);
    expect(screen.getByTestId('pv-basemap-boundary').getAttribute('d')?.length).toBeGreaterThan(0);
  });

  it('비지도형(경계 없음) 결과에는 **0개** — 없는 지도를 그리지 않는다', async () => {
    renderDetail(makeSource(undefined));
    await screen.findByTestId('preview-map');
    expect(screen.queryAllByTestId('pv-basemap')).toHaveLength(0);
  });

  it('C4 의 경계 외곽선이 배경 **위**에 남는다 — DOM 순서로 잰다', async () => {
    renderDetail(makeSource({ west: 126.9, south: 37.4, east: 127.1, north: 37.6 }));
    await screen.findByTestId('preview-map');
    const layers = await screen.findByTestId('preview-layers');
    const kids = Array.from(layers.children);
    const bg = kids.indexOf(screen.getByTestId('pv-basemap'));
    const outline = kids.indexOf(screen.getByTestId('preview-bounds-outline'));
    expect(bg).toBeGreaterThanOrEqual(0);
    expect(outline).toBeGreaterThan(bg);
  });
});

/* ── ⓓ 외부 요청 0 ──────────────────────────────────────────────────── */

describe('외부 요청 0 — POL-021 의 금지는 그대로 산다', () => {
  it('배경 자산을 가지러 나가는 요청이 0건이다 — `fetch` 도 `XMLHttpRequest` 도', async () => {
    // 감시만 하고 **가로채지 않는다** — 이 화면이 제 API 로 나가는 길(계보 등)은
    // 이 WU 의 소관이 아니고, 응답을 바꾸면 다른 WU 의 거동을 이 시험이 흔든다.
    const fetchSpy = vi.spyOn(globalThis, 'fetch');
    const xhrSpy = vi.spyOn(XMLHttpRequest.prototype, 'open');
    renderDetail(makeSource(KOREA));
    await screen.findByTestId('preview-map');
    await waitFor(() => expect(screen.getAllByTestId('pv-basemap')).toHaveLength(1));

    // ⓵ **배경 자산·타일 서버·외부 CDN 으로 나간 요청 0건.** 자산 이름이나 지도 낱말이
    //    URL 에 한 번이라도 보이면 그 순간 정적 import 가 아니게 된 것이다.
    const seen = fetchSpy.mock.calls.map((c) => String((c[0] as { url?: string })?.url ?? c[0]));
    const suspect = seen.filter((u) =>
      /basemap|geojson|natural[-_]?earth|ne_110m|tile|cdn|unpkg|jsdelivr|cloudflare/i.test(u),
    );
    expect(suspect).toEqual([]);
    // ⓶ 나간 요청은 전부 **이 앱 자신의 API** 다 — 바깥 출처가 하나도 없다.
    const foreign = seen.filter((u) => /^[a-z]+:\/\//i.test(u) && !u.startsWith('http://localhost'));
    expect(foreign).toEqual([]);
    // ⓷ XHR 은 아예 0건이다.
    expect(xhrSpy).toHaveBeenCalledTimes(0);
    expect(fetchSpy).toHaveBeenCalled();
  });
});
