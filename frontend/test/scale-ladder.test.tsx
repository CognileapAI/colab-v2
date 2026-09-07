/**
 * WU-C4 — **축척 사다리 ＋ 세 화면 공유 확대/축소** 시험.
 *
 * 오라클
 *  · R-C spec 「축척은 사다리다」 축자 — 기본 배율 = `bounds` 중심 ＋ 표준 축척 사다리 스냅 ·
 *    `useZoomPan`/`.pv-zoom` 세 화면 공유 · 작은 유역은 외곽선 ＋ 더블클릭 맞춤.
 *  · 판정(intent `2026-09-08-preview-slot.md ⑤`) — 단 값은 **시스템 상수 한 자리** ·
 *    비지도형(`bounds` 없음)은 **현행**.
 *
 * ⚠ **사다리 값을 이 파일에 다시 적지 않는다** — `SCALE_LADDER_KM` 을 읽고 그 위에서 잰다.
 *   상수가 줄거나 늘면 첫 단언(길이 5)이 먼저 red 가 된다(green-by-skip 방지).
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { DatasetDetailPage } from '../src/routes/DatasetDetailPage';
import { fixtureDetailSource } from '../src/components/detail/fixture';
import { PreviewPanel } from '../src/components/upload/PreviewPanel';
import type { RenderJob, RenderResult } from '../src/components/preview/types';
import type { PreviewSource } from '../src/components/upload/types';
import type { DatasetPreviewSource } from '../src/components/datasetpreview/types';
import {
  KM_PER_DEG_LON_EQUATOR,
  SCALE_LADDER_KM,
  baseScaleFor,
  boundsWidthKm,
  snapWidthKm,
  type GeoBounds,
} from '../src/components/preview/scaleLadder';

const OPEN_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA1';
const RENDER_ID = '01JYZ9K7WQ3N8V4M2X6C5B0RE9';

const LEGEND = {
  palette: 'viridis',
  unit: 'mm',
  classes: [
    { color: '#440154', min: 0, max: 5 },
    { color: '#21918c', min: 5, max: 10 },
  ],
};

/** 중위도 36° 에서 **원하는 km 폭**을 갖는 경계 상자 하나. 폭만 정하고 높이는 고정한다. */
function boundsOfWidthKm(widthKm: number, midLat = 36): GeoBounds {
  const deg = widthKm / (KM_PER_DEG_LON_EQUATOR * Math.cos((midLat * Math.PI) / 180));
  return { west: 126, south: midLat - 1, east: 126 + deg, north: midLat + 1 };
}

function doneJob(bounds?: GeoBounds): RenderJob {
  const result: RenderResult = {
    imageUrl: 'https://viz.example/d/map.png',
    legend: LEGEND,
    ...(bounds ? { bounds } : {}),
  } as unknown as RenderResult;
  return { renderId: RENDER_ID, status: '완료', result } as unknown as RenderJob;
}

function makeSource(bounds?: GeoBounds): DatasetPreviewSource {
  const job = doneJob(bounds);
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

function scaleOf(testId = 'preview-layers'): number {
  return Number(screen.getByTestId(testId).getAttribute('data-zoom-scale'));
}

/* ── ⓐ 상수 한 자리 ──────────────────────────────────────────────────── */

describe('축척 사다리 — 단 값은 시스템 상수 한 자리다', () => {
  it('사다리는 5단이고 오름차순이다 — 길이가 바뀌면 아래 시험이 먼저 red 가 된다', () => {
    expect(SCALE_LADDER_KM).toHaveLength(5);
    const asc = [...SCALE_LADDER_KM].sort((a, b) => a - b);
    expect([...SCALE_LADDER_KM]).toEqual(asc);
    expect(new Set(SCALE_LADDER_KM).size).toBe(5);
  });

  it('각 단마다 — 바로 아래 폭은 그 단으로, 바로 위 폭은 다음 단으로 스냅한다', () => {
    SCALE_LADDER_KM.forEach((rung, i) => {
      // 「담는 가장 작은 단」 — 단 값 자신과 그 바로 아래는 이 단이다.
      expect(snapWidthKm(rung)).toBe(rung);
      expect(snapWidthKm(rung - 0.5)).toBe(rung);
      const next = SCALE_LADDER_KM[i + 1];
      // 마지막 단을 넘는 폭은 **가장 큰 단**으로 답한다 — 없는 단을 만들지 않는다.
      expect(snapWidthKm(rung + 0.5)).toBe(next ?? rung);
    });
  });

  it('가장 큰 단을 크게 넘는 폭(전지구)도 가장 큰 단이다', () => {
    const top = SCALE_LADDER_KM[SCALE_LADDER_KM.length - 1] as number;
    expect(snapWidthKm(top * 100)).toBe(top);
  });

  it('폭을 지어내지 않는다 — 0·음수·NaN 은 가장 작은 단이다', () => {
    const first = SCALE_LADDER_KM[0] as number;
    expect(snapWidthKm(0)).toBe(first);
    expect(snapWidthKm(-1)).toBe(first);
    expect(snapWidthKm(Number.NaN)).toBe(first);
  });

  it('폭은 중위도에서 잰다 — 같은 경도 폭이라도 위도가 높으면 좁다(`cos(midLat)`)', () => {
    const low = boundsWidthKm({ west: 126, south: 0, east: 130, north: 2 });
    const high = boundsWidthKm({ west: 126, south: 59, east: 130, north: 61 });
    expect(high).toBeLessThan(low);
  });
});

/* ── ⓑ 기본 배율 = 사다리 ÷ 틀 ──────────────────────────────────────── */

describe('기본 배율 — 데이터 폭 ÷ 스냅된 단', () => {
  it('실측 픽스처(HSR bin · 폭 ≈1,035 km)의 초기 배율이 사다리 산식과 같다', async () => {
    const hsr: GeoBounds = {
      west: 121.883864,
      south: 31.13964,
      east: 133.558007,
      north: 43.303245,
    };
    renderDetail(makeSource(hsr));
    await screen.findByTestId('preview-map');
    const expected = boundsWidthKm(hsr) / snapWidthKm(boundsWidthKm(hsr));
    await waitFor(() => expect(scaleOf()).toBeCloseTo(expected, 6));
    expect(
      Number(screen.getByTestId('preview-layers').getAttribute('data-scale-rung-km')),
    ).toBe(snapWidthKm(boundsWidthKm(hsr)));
  });

  it('단을 거의 꽉 채우는 폭은 배율 ≈1 이다 — 등급이 같으면 크기도 같다', async () => {
    // 단 값 **바로 아래**를 쓴다 — 단 값 자신은 부동소수 오차 한 번에 다음 단으로 넘어간다
    // (그 경계 자체는 위 `snapWidthKm` 단언이 정확히 잰다).
    const b = boundsOfWidthKm((SCALE_LADDER_KM[1] as number) - 1);
    expect(baseScaleFor(b)).toBeCloseTo(1, 2);
    renderDetail(makeSource(b));
    await screen.findByTestId('preview-map');
    await waitFor(() => expect(scaleOf()).toBeCloseTo(baseScaleFor(b), 6));
  });

  it('②비지도형(`bounds` 없음)은 현행 그대로 — 기본 배율 1 · 사다리 표식 없음', async () => {
    renderDetail(makeSource());
    await screen.findByTestId('preview-map');
    expect(scaleOf()).toBe(1);
    expect(
      screen.getByTestId('preview-layers').getAttribute('data-scale-rung-km'),
    ).toBeNull();
    expect(screen.queryByTestId('preview-bounds-outline')).toBeNull();
  });
});

/* ── ⓒ 더블클릭 = 데이터에 맞춤 ─────────────────────────────────────── */

describe('더블클릭 — 데이터 경계에 맞춘다(여백 0)', () => {
  it('작은 유역에서 더블클릭하면 배율이 1(데이터가 틀을 꽉 채움)로 간다', async () => {
    const small = boundsOfWidthKm((SCALE_LADDER_KM[0] as number) * 0.6);
    renderDetail(makeSource(small));
    await screen.findByTestId('preview-map');
    await waitFor(() => expect(scaleOf()).toBeLessThan(1));
    fireEvent.doubleClick(screen.getByTestId('preview-viewport'));
    expect(scaleOf()).toBeCloseTo(1, 6);
  });

  it('「기본 배율로」는 사다리 자리로 되돌린다 — 맞춤과 기본은 다른 자리다', async () => {
    const small = boundsOfWidthKm((SCALE_LADDER_KM[0] as number) * 0.6);
    renderDetail(makeSource(small));
    await screen.findByTestId('preview-map');
    fireEvent.doubleClick(screen.getByTestId('preview-viewport'));
    expect(scaleOf()).toBeCloseTo(1, 6);
    fireEvent.click(screen.getByRole('button', { name: '기본 배율로' }));
    await waitFor(() => expect(scaleOf()).toBeCloseTo(baseScaleFor(small), 6));
  });
});

/* ── ⓓ 외곽선 = 「지금 어디를 보고 있는지」 ──────────────────────────── */

describe('경계 외곽선 — 작은 유역에만 선다', () => {
  it('데이터가 틀의 작은 몫만 차지하면 외곽선이 있다', async () => {
    renderDetail(makeSource(boundsOfWidthKm((SCALE_LADDER_KM[0] as number) * 0.6)));
    await screen.findByTestId('preview-map');
    await waitFor(() => expect(screen.getByTestId('preview-bounds-outline')).toBeTruthy());
  });

  it('데이터가 틀을 채우면 외곽선이 없다 — 그림 테두리와 겹쳐 아무 것도 알리지 않는다', async () => {
    renderDetail(makeSource(boundsOfWidthKm((SCALE_LADDER_KM[1] as number) - 1)));
    await screen.findByTestId('preview-map');
    expect(screen.queryByTestId('preview-bounds-outline')).toBeNull();
  });

  it('외곽선은 **확대되는 층 묶음 안**에 있다 — 그림과 함께 움직인다(조건 ⑸)', async () => {
    renderDetail(makeSource(boundsOfWidthKm((SCALE_LADDER_KM[0] as number) * 0.6)));
    await screen.findByTestId('preview-map');
    const outline = await screen.findByTestId('preview-bounds-outline');
    expect(screen.getByTestId('preview-layers').contains(outline)).toBe(true);
  });
});

/* ── ⓔ 세 화면이 같은 버튼을 쓴다 ───────────────────────────────────── */

const UPLOAD_RESULT: RenderResult = {
  imageUrl: 'https://viz.example/u/map.png',
  legend: LEGEND,
  bounds: boundsOfWidthKm(600),
} as unknown as RenderResult;

function uploadSource(): PreviewSource {
  const job = { renderId: RENDER_ID, status: '완료', result: UPLOAD_RESULT } as unknown as RenderJob;
  return {
    palettes: vi.fn(async () => [{ palette: 'viridis', label: 'viridis' }]),
    createRender: vi.fn(async () => job),
    getRender: vi.fn(async () => job),
  } as unknown as PreviewSource;
}

function renderUpload() {
  return render(<PreviewPanel uploadId="up-1" source={uploadSource()} hasReferenceGrid />);
}

describe('세 화면 공유 — 같은 `.pv-zoom` 버튼 세 개', () => {
  it('상세 — 확대·축소·기본 배율로 세 버튼', async () => {
    renderDetail(makeSource(boundsOfWidthKm(600)));
    await screen.findByTestId('preview-map');
    const group = screen.getByTestId('preview-zoom');
    expect(group.querySelectorAll('button')).toHaveLength(3);
    expect(group.className).toContain('pv-zoom');
  });

  it('업로드 — 같은 마크업의 버튼 세 개', async () => {
    renderUpload();
    fireEvent.click(await screen.findByRole('button', { name: /미리보기 그리기/ }));
    const group = await screen.findByTestId('up-preview-zoom');
    expect(group.querySelectorAll('button')).toHaveLength(3);
    expect(group.className).toContain('pv-zoom');
  });

  it('확장보기 — 같은 마크업의 버튼 세 개 · 층 규칙(`data-esc-layer`)은 그대로다', async () => {
    renderUpload();
    fireEvent.click(await screen.findByRole('button', { name: /미리보기 그리기/ }));
    await screen.findByTestId('up-preview-zoom');
    fireEvent.click(screen.getByTestId('pv-expand'));
    const overlay = await screen.findByTestId('pv-expand-overlay');
    expect(overlay.getAttribute('data-esc-layer')).toBe('확장보기');
    const group = await screen.findByTestId('pv-expand-zoom');
    expect(group.querySelectorAll('button')).toHaveLength(3);
    expect(group.className).toContain('pv-zoom');
  });
});
