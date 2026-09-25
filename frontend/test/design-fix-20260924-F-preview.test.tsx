/**
 * design-fix 20260924 · 수정 레인 F-preview — 미리보기 끌기·관성의 수용 검토 결함 14건.
 *
 * 오라클 = `dev-package/prd/specs/S-DESIGN-FIX-20260924.md` 「통합 수정」 F-preview 행 · 확정 값 5·6.
 * 결함 원문 = `dev-package/sessions/design-fix-20260924-acceptance.md` A23–A41(F-preview 14건).
 *  - A23/A25/A33/A40 `pointercancel` = 관성 없이 끝냄 · 취소 좌표를 표본에서 제외.
 *  - A26/A31 목표가 잘리면 인계 속도 상한 |v0| ≤ ω·|x0| · 매 프레임 범위.
 *  - A24/A28/A34 관성 시작점 = 최신 값(렌더 전 이동 포함).
 *  - A27 끌기 중 두 번째 포인터 무시.
 *  - A29/A41 `clampView`·`baseScale` 변화(경계 · 화면 크기) 때 관성 정지.
 *  - A30 놓은 속도가 스프링으로 인계된다.
 *  - A35 관성 중 탭으로 멈추면 뒤이은 click 이 값 조회를 부르지 않는다.
 * ⚠ 시간은 가짜다 — 마운트 뒤 `requestAnimationFrame` · `performance` 만 가짜로 돌린다(L3b 와 같은 규율).
 */
import { act, fireEvent, render, renderHook, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { DatasetPreviewSection } from '../src/components/datasetpreview/DatasetPreviewSection';
import { capHandoffVelocity, projectedDistance, spring, SPRING_RESPONSE } from '../src/components/preview/spring';
import { baseScaleFor } from '../src/components/preview/scaleLadder';
import { useZoomPan } from '../src/components/preview/useZoomPan';
import type { DatasetPreviewSource, ValueLookupResult } from '../src/components/datasetpreview/types';
import type { RenderJob } from '../src/components/preview/types';
import { drawDatasetPreviewWhenReady, withDatasetPreviewFixture } from './datasetPreviewTest';

const DATASET_ID = '0000000000000000000000DS12';
const RENDER_ID = '01JYZ9K7WQ3N8V4M2X6C5B0RE2';
const WAIT = { timeout: 5000 };
/** 기본 배율 1 인 넓은 경계(L3b 와 같다). */
const WIDE = { west: -90, south: -10, east: 90, north: 10 };
/** 기본 배율이 1 보다 작은 경계(≈2,004 km → 3,000 단). */
const NARROW = { west: 0, south: -5, east: 18, north: 5 };

/** 세로 이동 범위 = ±(1600 − 512)/2. 첫 자리(편차 0)의 화면 y = −544. */
const HALF = (1600 - 512) / 2;
const Y0 = (512 - 1600) / 2;
const OMEGA = (2 * Math.PI) / SPRING_RESPONSE;

const HIT: ValueLookupResult = {
  available: true, value: 12.5, unit: 'mm', variable: '강우량',
  exactness: '원본과 같은 칸',
  cell: { row: 2, col: 3, center: { lat: 0, lon: 0 }, sizeDegrees: 0.25 },
  unavailableReason: null,
} as unknown as ValueLookupResult;

function doneJob(): RenderJob {
  return {
    renderId: RENDER_ID,
    status: '완료',
    result: {
      imageUrl: 'https://viz.example/d/map.png',
      legend: { palette: 'viridis', unit: 'mm', variable: 'rainfall', classes: [{ color: '#440154', min: 0, max: 5 }] },
      bounds: WIDE,
    },
  } as unknown as RenderJob;
}

function detailSource(): DatasetPreviewSource {
  return withDatasetPreviewFixture({
    palettes: vi.fn(async () => [{ palette: 'viridis' }]),
    create: vi.fn(async () => doneJob()),
    get: vi.fn(async () => doneJob()),
    probeTile: vi.fn(async () => 'ok' as const),
    mapGeometry: vi.fn(async () => undefined),
    screenshot: vi.fn(async () => new Blob()),
    lookupValue: vi.fn(async () => HIT),
  } as unknown as DatasetPreviewSource);
}

async function mountDetail(source: DatasetPreviewSource = detailSource()) {
  render(<DatasetPreviewSection datasetId={DATASET_ID} source={source} pollMs={5} />);
  drawDatasetPreviewWhenReady();
  await waitFor(() => expect(screen.getByTestId('preview-map')).toBeTruthy(), WAIT);
  const viewport = screen.getByTestId('preview-viewport');
  const layers = screen.getByTestId('preview-layers');
  prepare(viewport, layers);
  await waitFor(() => expect(yOf(layers)).toBeCloseTo(Y0), WAIT);
  return { viewport, layers };
}

function prepare(viewport: HTMLElement, layers: HTMLElement) {
  Object.defineProperty(viewport, 'clientWidth', { value: 512, configurable: true });
  Object.defineProperty(viewport, 'clientHeight', { value: 512, configurable: true });
  viewport.getBoundingClientRect = () =>
    ({ left: 0, top: 0, width: 512, height: 512, right: 512, bottom: 512, x: 0, y: 0,
       toJSON: () => ({}) }) as DOMRect;
  Object.defineProperty(layers, 'offsetWidth', { value: 512, configurable: true });
  Object.defineProperty(layers, 'offsetHeight', { value: 1600, configurable: true });
  const img = viewport.querySelector('img') as HTMLImageElement;
  Object.defineProperty(img, 'naturalWidth', { value: 4096, configurable: true });
  fireEvent.load(img);
}

function yOf(layers: HTMLElement): number {
  const t = layers.style.getPropertyValue('--pv-layers-transform');
  const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([-\d.]+)\)/.exec(t);
  expect(m, `transform 원문을 읽지 못했다: ${t}`).toBeTruthy();
  return Number(m![2]);
}

function transformOf(layers: HTMLElement): string {
  return layers.style.getPropertyValue('--pv-layers-transform');
}

function fakeClock() {
  vi.useFakeTimers({ toFake: ['requestAnimationFrame', 'cancelAnimationFrame', 'performance'] });
}
const advance = (ms: number) => act(() => { vi.advanceTimersByTime(ms); });
const tick = () => new Promise((r) => setTimeout(r, 30));

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});

/** 빠른 끌기 — 10ms 마다 20px(L3b 와 같다). 놓은 편차 80. */
function fastFling(viewport: HTMLElement) {
  fireEvent.pointerDown(viewport, { pointerId: 1, clientX: 300, clientY: 300, button: 0 });
  for (let i = 1; i <= 4; i += 1) {
    advance(10);
    fireEvent.pointerMove(window, { pointerId: 1, clientX: 300, clientY: 300 + 20 * i });
  }
  fireEvent.pointerUp(window, { pointerId: 1, clientX: 300, clientY: 380 });
}

/* ═══ A23 · A25 · A33 · A40 — pointercancel 은 놓기가 아니다 ═══════════════════ */

describe('A23/A25/A33/A40 pointercancel — 관성 없이 끝내고 취소 좌표를 쓰지 않는다', () => {
  it('10px 넘게 끈 뒤 pointerCancel(0,0) — 변환이 그대로이고 시간이 흘러도 움직이지 않는다', async () => {
    const { viewport, layers } = await mountDetail();
    fakeClock();
    fireEvent.pointerDown(viewport, { pointerId: 1, clientX: 300, clientY: 300, button: 0 });
    for (let i = 1; i <= 4; i += 1) {
      advance(10);
      fireEvent.pointerMove(window, { pointerId: 1, clientX: 300, clientY: 300 + 20 * i });
    }
    const before = transformOf(layers);
    expect(yOf(layers)).toBeCloseTo(Y0 + 80);
    fireEvent.pointerCancel(window, { pointerId: 1, clientX: 0, clientY: 0 });
    expect(transformOf(layers)).toBe(before);
    advance(16);
    expect(transformOf(layers)).toBe(before);
    advance(1000);
    expect(transformOf(layers)).toBe(before);
  });

  it('취소 뒤 같은 포인터의 이동은 끌기가 아니다', async () => {
    const { viewport, layers } = await mountDetail();
    fakeClock();
    fireEvent.pointerDown(viewport, { pointerId: 1, clientX: 300, clientY: 300, button: 0 });
    advance(10);
    fireEvent.pointerMove(window, { pointerId: 1, clientX: 300, clientY: 340 });
    fireEvent.pointerCancel(window, { pointerId: 1, clientX: 0, clientY: 0 });
    const before = transformOf(layers);
    fireEvent.pointerMove(window, { pointerId: 1, clientX: 300, clientY: 400 });
    advance(1000);
    expect(transformOf(layers)).toBe(before);
  });
});

/* ═══ A26 · A31 — 목표가 잘리면 넘침 없이 선다 ═════════════════════════════════ */

describe('A26 capHandoffVelocity — |v0| ≤ ω·|x0|', () => {
  it('남은 거리가 v0/ω 안이면 속도를 ω·|x0| 로 줄이고 스프링이 목표를 넘지 않는다', () => {
    // 목표까지 50px · 놓은 속도 2000px/s — 50 < 2000/ω(≈127) 이라 그대로 두면 목표를 넘는다.
    const from = 0;
    const to = 50;
    const v = capHandoffVelocity(2000, from - to);
    expect(Math.abs(v)).toBeLessThanOrEqual(OMEGA * 50 + 1e-9);
    expect(v).toBeGreaterThan(0);
    for (let t = 0; t <= 3 * SPRING_RESPONSE; t += 0.001) {
      expect(spring(from, to, v, t).value - to).toBeLessThanOrEqual(1e-9);
    }
  });

  it('반대 방향 · 멀리 있는 목표 — 상한에 걸리지 않으면 속도를 바꾸지 않는다', () => {
    expect(capHandoffVelocity(-800, 1000)).toBe(-800);
    expect(capHandoffVelocity(2000, -(2000 / 1000) * 0.998 / 0.002)).toBe(2000);
  });

  it('남은 거리 0(이미 끝) — 인계 속도 0', () => {
    expect(capHandoffVelocity(2000, 0)).toBe(0);
  });
});

describe('A26/A31 목표가 잘린 관성 — 매 프레임 범위 안 · 끝에서 급정거하지 않는다', () => {
  it('끝까지 50px 남기고 2000px/s 로 놓으면 경계에 스며들 듯 선다', async () => {
    const { viewport, layers } = await mountDetail();
    fakeClock();
    fireEvent.pointerDown(viewport, { pointerId: 1, clientX: 300, clientY: 100, button: 0 });
    advance(200);
    fireEvent.pointerMove(window, { pointerId: 1, clientX: 300, clientY: 394 });
    for (let i = 1; i <= 10; i += 1) {
      advance(10);
      fireEvent.pointerMove(window, { pointerId: 1, clientX: 300, clientY: 394 + 20 * i });
    }
    fireEvent.pointerUp(window, { pointerId: 1, clientX: 300, clientY: 594 });
    expect(yOf(layers)).toBeCloseTo(Y0 + 494);
    const bound = Y0 + HALF;
    const ys: number[] = [yOf(layers)];
    for (let f = 0; f < 60; f += 1) {
      advance(16);
      const y = yOf(layers);
      // 매 프레임 범위 안이다.
      expect(y).toBeLessThanOrEqual(bound + 1e-9);
      ys.push(y);
    }
    const arrived = ys.findIndex((y) => Math.abs(y - bound) < 1e-9);
    expect(arrived).toBeGreaterThan(0);
    // 경계에 닿기 직전 프레임은 이미 1px 안이다 — 움직이던 채로 경계에서 잘리지 않았다.
    expect(bound - ys[arrived - 1]!).toBeLessThanOrEqual(1);
  });
});

/* ═══ A24 · A28 · A34 — 관성 시작점 = 최신 값 ══════════════════════════════════ */

describe('A24/A28/A34 관성 시작점 — 아직 그려지지 않은 마지막 이동도 포함한다', () => {
  it('마지막 pointermove 의 렌더 전에 pointerup 이 와도 투영 목표에 정확히 선다', async () => {
    vi.spyOn(console, 'error').mockImplementation(() => {});
    const { viewport, layers } = await mountDetail();
    fakeClock();
    fireEvent.pointerDown(viewport, { pointerId: 1, clientX: 300, clientY: 300, button: 0 });
    advance(16);
    fireEvent.pointerMove(window, { pointerId: 1, clientX: 300, clientY: 311 });
    advance(16);
    fireEvent.pointerMove(window, { pointerId: 1, clientX: 300, clientY: 312 });
    advance(16);
    // act 밖 — React 가 이 이동을 아직 커밋하지 않은 채로 놓기가 온다.
    window.dispatchEvent(new PointerEvent('pointermove', { pointerId: 1, clientX: 300, clientY: 313 }));
    window.dispatchEvent(new PointerEvent('pointerup', { pointerId: 1, clientX: 300, clientY: 313 }));
    advance(3 * SPRING_RESPONSE * 1000);
    const v = (13 / 48) * 1000;
    expect(yOf(layers)).toBeCloseTo(Y0 + 13 + projectedDistance(v), 3);
  });
});

/* ═══ A27 — 끌기 중 두 번째 포인터 ═════════════════════════════════════════════ */

describe('A27 끌기 중 두 번째 포인터 — 무시하고 첫 포인터의 끌기를 잇는다', () => {
  it('두 번째 손가락의 누름·이동·놓기는 변환을 바꾸지 않고, 첫 손가락 이동은 계속 반영된다', async () => {
    const { viewport, layers } = await mountDetail();
    fakeClock();
    fireEvent.pointerDown(viewport, { pointerId: 1, clientX: 300, clientY: 300, button: 0 });
    advance(10);
    fireEvent.pointerMove(window, { pointerId: 1, clientX: 300, clientY: 320 });
    expect(yOf(layers)).toBeCloseTo(Y0 + 20);
    fireEvent.pointerDown(viewport, { pointerId: 2, clientX: 100, clientY: 100, button: 0 });
    advance(10);
    fireEvent.pointerMove(window, { pointerId: 2, clientX: 100, clientY: 150 });
    expect(yOf(layers)).toBeCloseTo(Y0 + 20);
    fireEvent.pointerUp(window, { pointerId: 2, clientX: 100, clientY: 150 });
    advance(200);
    expect(yOf(layers)).toBeCloseTo(Y0 + 20);
    fireEvent.pointerMove(window, { pointerId: 1, clientX: 300, clientY: 330 });
    expect(yOf(layers)).toBeCloseTo(Y0 + 30);
  });
});

/* ═══ A29 · A41 — 경계 · 화면 크기가 바뀌면 관성을 멈춘다 ═══════════════════════ */

function mountHook(bounds: typeof WIDE, reactStrictMode = false) {
  const vp = document.createElement('div');
  Object.defineProperty(vp, 'clientWidth', { value: 512, configurable: true });
  Object.defineProperty(vp, 'clientHeight', { value: 512, configurable: true });
  const lay = document.createElement('div');
  Object.defineProperty(lay, 'offsetWidth', { value: 512, configurable: true });
  Object.defineProperty(lay, 'offsetHeight', { value: 1600, configurable: true });
  const hook = renderHook(({ b }) => useZoomPan({ bounds: b }), {
    initialProps: { b: bounds },
    reactStrictMode,
  });
  act(() => {
    hook.result.current.viewportRef(vp as HTMLDivElement);
    hook.result.current.layersRef(lay);
  });
  act(() => hook.result.current.onNativeWidth(4096));
  return { hook, vp };
}

function hookFling(hook: ReturnType<typeof mountHook>['hook']) {
  act(() => hook.result.current.onPointerDown({ pointerId: 1, clientX: 300, clientY: 300, button: 0 }));
  for (let i = 1; i <= 4; i += 1) {
    advance(10);
    fireEvent.pointerMove(window, { pointerId: 1, clientX: 300, clientY: 300 + 20 * i });
  }
  fireEvent.pointerUp(window, { pointerId: 1, clientX: 300, clientY: 380 });
  advance(32);
}

describe('A29/A41 관성 중 경계·크기 변화 — 관성을 멈춘다', () => {
  it('A29 baseScale 이 바뀌면 시작 자리(기본 배율 · 편차 0)가 다음 프레임에 덮이지 않는다', () => {
    const base = baseScaleFor(NARROW);
    expect(base).toBeGreaterThan(0.4);
    expect(base).toBeLessThan(1);
    fakeClock();
    const { hook } = mountHook(WIDE);
    hookFling(hook);
    expect(hook.result.current.panOffset.y).toBeGreaterThan(80);
    hook.rerender({ b: NARROW });
    expect(hook.result.current.scale).toBeCloseTo(base, 9);
    expect(hook.result.current.panOffset).toEqual({ x: 0, y: 0 });
    advance(1000);
    expect(hook.result.current.scale).toBeCloseTo(base, 9);
    expect(hook.result.current.panOffset).toEqual({ x: 0, y: 0 });
  });

  it('A41 화면 크기가 바뀌면(resize) 그 프레임 값에서 멈춘다', () => {
    fakeClock();
    const { hook, vp } = mountHook(WIDE);
    hookFling(hook);
    Object.defineProperty(vp, 'clientHeight', { value: 1024, configurable: true });
    act(() => { window.dispatchEvent(new Event('resize')); });
    const at = hook.result.current.panOffset.y;
    advance(1000);
    expect(hook.result.current.panOffset.y).toBe(at);
  });
});

/* ═══ FP-1 — StrictMode 이중 호출에도 관성은 목표에 정확히 선다 ═══════════════════ */

describe('FP-1 관성 갱신 함수는 멱등이다 — StrictMode(DEV 이중 호출)에서도 목표에 선다', () => {
  // 한 act 안에서 여러 프레임을 돌리면 갱신이 렌더 때 몰아서 처리된다(eager 아님).
  // StrictMode 는 그때 갱신 함수를 두 번 부르고 첫 결과를 버린다 — 멈춤 프레임의 둘째 호출이
  // 앞 프레임 값을 돌려주면 목표보다 SETTLE_PX 이상 모자란 자리에 선다.
  for (const reactStrictMode of [false, true]) {
    it(`reactStrictMode=${reactStrictMode} · 빠른 끌기 뒤 panOffset 이 잘린 투영 목표와 같다`, () => {
      fakeClock();
      const { hook } = mountHook(WIDE, reactStrictMode);
      hookFling(hook);
      advance(3000);
      const goal = Math.min(HALF, 80 + projectedDistance(2000));
      expect(goal).toBe(HALF);
      expect(hook.result.current.panOffset).toEqual({ x: 0, y: goal });
      advance(1000);
      expect(hook.result.current.panOffset).toEqual({ x: 0, y: goal });
    });
  }
});

/* ═══ A30 — 놓은 속도가 스프링으로 인계된다 ═════════════════════════════════════ */

describe('A30 속도 인계 — 첫 프레임 = spring(놓은 자리, 목표, v, t)', () => {
  it('16ms 마다 1px 씩 끌고 놓은 뒤 첫 프레임(16ms)의 자리가 놓은 속도 인계 값이다', async () => {
    const { viewport, layers } = await mountDetail();
    fakeClock();
    fireEvent.pointerDown(viewport, { pointerId: 1, clientX: 300, clientY: 300, button: 0 });
    advance(16);
    fireEvent.pointerMove(window, { pointerId: 1, clientX: 300, clientY: 311 });
    advance(16);
    fireEvent.pointerMove(window, { pointerId: 1, clientX: 300, clientY: 312 });
    advance(16);
    fireEvent.pointerMove(window, { pointerId: 1, clientX: 300, clientY: 313 });
    fireEvent.pointerUp(window, { pointerId: 1, clientX: 300, clientY: 313 });
    const v = (13 / 48) * 1000;
    const target = 13 + projectedDistance(v);
    expect(target).toBeLessThan(HALF);
    advance(16);
    const withV = spring(13, target, v, 0.016).value;
    const still = spring(13, target, 0, 0.016).value;
    expect(yOf(layers)).toBeCloseTo(Y0 + withV, 3);
    expect(withV - still).toBeGreaterThan(1);
  });
});

/* ═══ A35 — 관성 중 탭으로 멈추면 값 조회 안 함 ════════════════════════════════ */

describe('A35 관성을 잡는 탭 — 뒤이은 click 은 값 조회를 부르지 않는다', () => {
  it('관성 중 임계 안 누름·놓기 뒤 click 은 조회 0 · 그다음 평소 탭은 조회 1', async () => {
    const source = detailSource();
    const { viewport } = await mountDetail(source);
    fakeClock();
    fastFling(viewport);
    advance(32);
    fireEvent.pointerDown(viewport, { pointerId: 1, clientX: 256, clientY: 256, button: 0 });
    fireEvent.pointerUp(window, { pointerId: 1, clientX: 256, clientY: 256 });
    fireEvent.click(viewport, { clientX: 256, clientY: 256 });
    await tick();
    expect(source.lookupValue).toHaveBeenCalledTimes(0);

    fireEvent.pointerDown(viewport, { pointerId: 1, clientX: 256, clientY: 256, button: 0 });
    fireEvent.pointerUp(window, { pointerId: 1, clientX: 256, clientY: 256 });
    fireEvent.click(viewport, { clientX: 256, clientY: 256 });
    await waitFor(() => expect(source.lookupValue).toHaveBeenCalledTimes(1), WAIT);
  });
});
