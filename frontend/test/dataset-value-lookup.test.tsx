/**
 * 값 조회 화면 (`V-2` · `PLAN-SoT §9 〈294〉` · 15차 동결 해제).
 *
 * 오라클 = 정본 `Policy_데이터셋_상세 §8 값 조회` ＋ 완료 정의 `〈254〉`.
 * 이 파일이 잠그는 것 —
 *  ⑴ 지도의 한 점을 누르면 **그 자리의 값**이 뜬다
 *  ⑵ **다시 그리지 않는다** — 누름 전후로 렌더 시작 호출이 늘지 않는다(음성)
 *  ⑷ 답하는 단위가 **한 칸**임을 화면이 말한다
 *  ⑸ 값이 없으면 **「없음」** — 0 으로 바꾸지 않는다(음성)
 *  ⑹ **좌표가 없는 자료에는 자리가 없다**(음성)
 *
 * ⚠ **좌표 계산은 따로 잰다.** 화면을 눌러 얻은 위경도가 틀리면 에러 없이 **다른 칸의
 * 값**이 나가는데, 그것이 이 기능에서 제일 나쁜 실패다. jsdom 은 실제 레이아웃을 하지
 * 않으므로 순수 함수(`pointFromViewport`)로 배율·이동까지 못 박는다.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { DatasetPreviewSection } from '../src/components/datasetpreview/DatasetPreviewSection';
import type { DatasetPreviewSource, ValueLookupResult } from '../src/components/datasetpreview/types';
import { pointFromViewport } from '../src/components/preview/PreviewPanels';
import type { RenderJob } from '../src/components/preview/types';

const RENDER_ID = '01ARZ3NDEKTSV4RRFFQ69G5FAV';
const DATASET_ID = '0000000000000000000000DSA1';
const BOUNDS = { west: 126, south: 36, east: 128, north: 38 };
const LEGEND = { unit: 'mm', classes: [{ min: 0, max: 1, color: '#eee' }] };

/** ③지도형 — 좌표가 있다. `bounds` 가 곧 「좌표 있는 자료」의 판정이다. */
const MAPPED = {
  renderId: RENDER_ID,
  status: '완료',
  result: { imageUrl: 'https://viz.example/d/map.png', bounds: BOUNDS, legend: LEGEND },
} as unknown as RenderJob;

/** ②비지도형 — 좌표가 없다. 완료지만 값 조회 자리가 서지 않는다. */
const UNMAPPED = {
  renderId: RENDER_ID,
  status: '완료',
  result: { imageUrl: 'https://viz.example/d/plot.png', legend: LEGEND },
} as unknown as RenderJob;

const HIT: ValueLookupResult = {
  available: true, value: 12.5, unit: 'mm', variable: '강우량',
  exactness: '원본과 같은 칸',
  cell: { row: 2, col: 3, center: { lat: 37.375, lon: 126.875 }, sizeDegrees: 0.25 },
  unavailableReason: null,
} as unknown as ValueLookupResult;

const EMPTY: ValueLookupResult = {
  available: false, value: null, unit: 'mm', variable: '강우량',
  exactness: '원본과 같은 칸',
  cell: { row: 2, col: 3, center: { lat: 37.375, lon: 126.875 }, sizeDegrees: 0.25 },
  unavailableReason: '값이 없는 칸이다',
} as unknown as ValueLookupResult;

function makeSource(job: RenderJob, lookup: ValueLookupResult): DatasetPreviewSource {
  return {
    palettes: vi.fn(async () => [{ palette: 'viridis' }]),
    create: vi.fn(async () => job),
    get: vi.fn(async () => job),
    probeTile: vi.fn(async () => 'ok' as const),
    mapGeometry: vi.fn(async () => undefined),
    screenshot: vi.fn(async () => new Blob()),
    lookupValue: vi.fn(async () => lookup),
  };
}

/** jsdom 은 레이아웃을 안 한다 — 뷰포트 크기를 시험이 명시적으로 준다. */
function sizeViewport(el: Element, width = 200, height = 200) {
  el.getBoundingClientRect = () =>
    ({ left: 0, top: 0, width, height, right: width, bottom: height, x: 0, y: 0,
       toJSON: () => ({}) }) as DOMRect;
}

async function mountMapped(source: DatasetPreviewSource) {
  render(<DatasetPreviewSection datasetId={DATASET_ID} source={source} pollMs={5} />);
  await waitFor(() => expect(screen.getByTestId('preview-map')).toBeTruthy());
  return screen.getByTestId('preview-viewport');
}

describe('값 조회 — 지도의 한 점', () => {
  it('⑴ 한 점을 누르면 그 자리의 값이 뜬다 · ⑷ 답하는 단위를 함께 말한다', async () => {
    const source = makeSource(MAPPED, HIT);
    const viewport = await mountMapped(source);
    sizeViewport(viewport);

    // 누르기 전에는 「고르기 전」 안내뿐이다 — 값이 미리 떠 있지 않다.
    expect(screen.getByTestId('value-lookup').textContent).toContain('한 점을 누르면');

    fireEvent.click(viewport, { clientX: 100, clientY: 100 });

    await waitFor(() => expect(screen.getByTestId('value-lookup-value')).toBeTruthy());
    expect(screen.getByTestId('value-lookup-value').textContent).toBe('12.5 mm');
    // ⑷ — 「원본 해상도 이상은 약속하지 않는다」가 값과 같은 자리에 있다.
    expect(screen.getByTestId('value-lookup-exactness').textContent).toBe('한 칸 · 원본과 같은 칸');
    // 서버에 나간 것이 **화면 한가운데의 지도 좌표**다.
    expect(source.lookupValue).toHaveBeenCalledWith({ lat: 37, lon: 127 });
  });

  it('⑸ 값이 없는 칸은 0 이 아니라 「없음」이다', async () => {
    const source = makeSource(MAPPED, EMPTY);
    const viewport = await mountMapped(source);
    sizeViewport(viewport);

    fireEvent.click(viewport, { clientX: 10, clientY: 10 });

    await waitFor(() => expect(screen.getByTestId('value-lookup-value')).toBeTruthy());
    expect(screen.getByTestId('value-lookup-value').textContent).toBe('없음');
    expect(screen.getByTestId('value-lookup-value').textContent).not.toContain('0');
    expect(screen.getByTestId('value-lookup-reason').textContent).toBe('값이 없는 칸이다');
  });

  it('⑵ 값 조회가 렌더를 다시 시작하지 않는다', async () => {
    const source = makeSource(MAPPED, HIT);
    const viewport = await mountMapped(source);
    sizeViewport(viewport);
    const before = (source.create as ReturnType<typeof vi.fn>).mock.calls.length;

    fireEvent.click(viewport, { clientX: 100, clientY: 100 });
    await waitFor(() => expect(screen.getByTestId('value-lookup-value')).toBeTruthy());

    expect((source.create as ReturnType<typeof vi.fn>).mock.calls.length).toBe(before);
  });

  it('⑹ 좌표가 없는 자료에는 조회 자리가 없다', async () => {
    const source = makeSource(UNMAPPED, HIT);
    render(<DatasetPreviewSection datasetId={DATASET_ID} source={source} pollMs={5} />);
    await waitFor(() => expect(screen.getByTestId('preview-map')).toBeTruthy());

    expect(screen.queryByTestId('value-lookup')).toBeNull();
    expect(screen.getByTestId('preview-viewport').getAttribute('data-value-lookup')).toBeNull();
  });
});

describe('화면의 한 점 → 지도 좌표', () => {
  const box = { width: 200, height: 200 };

  it('배율 1 에서 화면 비율이 경계 안의 비율이다', () => {
    expect(pointFromViewport({ x: 100, y: 100 }, box, BOUNDS, { scale: 1, x: 0, y: 0 }))
      .toEqual({ lat: 37, lon: 127 });
    expect(pointFromViewport({ x: 0, y: 0 }, box, BOUNDS, { scale: 1, x: 0, y: 0 }))
      .toEqual({ lat: 38, lon: 126 });
  });

  it('확대·이동을 되돌린 뒤에 비율을 낸다 — 빼먹으면 다른 칸의 값이 나간다', () => {
    // 2배로 키우고 (20,20) 만큼 민 상태에서 화면 (120,120) 을 눌렀다
    // ⟹ 층 좌표 (50,50) ⟹ 비율 0.25 ⟹ 경도 126.5 · 위도 37.5
    expect(pointFromViewport({ x: 120, y: 120 }, box, BOUNDS, { scale: 2, x: 20, y: 20 }))
      .toEqual({ lat: 37.5, lon: 126.5 });
    // 배율을 무시했다면 (0.6, 0.6) → 경도 127.2 가 나온다 — 같지 않아야 한다.
    expect(pointFromViewport({ x: 120, y: 120 }, box, BOUNDS, { scale: 2, x: 20, y: 20 }))
      .not.toEqual({ lat: 36.8, lon: 127.2 });
  });

  it('경계 밖을 누르면 좌표를 지어내지 않는다', () => {
    expect(pointFromViewport({ x: -5, y: 100 }, box, BOUNDS, { scale: 1, x: 0, y: 0 }))
      .toBeUndefined();
    expect(pointFromViewport({ x: 100, y: 400 }, box, BOUNDS, { scale: 1, x: 0, y: 0 }))
      .toBeUndefined();
  });
});
