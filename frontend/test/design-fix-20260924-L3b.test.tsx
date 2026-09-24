/**
 * design-fix 20260924 · L3b 미리보기 제스처 — #5 놓은 뒤 관성 ＋ 임계 감쇠 스프링(직접 구현).
 *
 * 오라클 = `dev-package/prd/specs/S-DESIGN-FIX-20260924.md` §4 「L3」 행 #5 · 확정 값 5 · 6.
 *  - 값 5 = 직접 구현(`components/preview/spring.ts` · 새 의존성 0).
 *  - 값 6 = damping 1.0 · response 0.4s · 놓을 때 속도 = 마지막 100ms 이동 기록의 평균 ·
 *    목표 = 현재 자리 ＋ (v / 1000)·0.998 / (1 − 0.998) 를 `clampView` 로 자른 자리 ·
 *    새로 누르기 · 휠 · 확대 단추 · 더블클릭이 오면 그 프레임 값에서 멈춤 · 동작 줄이기면 관성 0.
 * ⚠ L3a(#3) 시험 파일과 나눈 까닭 — 이 파일은 아직 없는 모듈(`spring.ts`)을 import 한다. 한 파일에
 *   두면 모듈 부재가 #3 단언 전부를 가린다(RED 이유가 섞인다).
 * ⚠ 시간은 가짜다 — 마운트(실시간 · 비동기 조회)를 끝낸 뒤 `requestAnimationFrame` ·
 *   `performance` 만 가짜로 돌린다. 그래서 이동 기록의 시각과 프레임이 결정적이다.
 */
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { DatasetPreviewSection } from '../src/components/datasetpreview/DatasetPreviewSection';
import { PreviewPanel } from '../src/components/upload/PreviewPanel';
import { SPRING_RESPONSE, spring } from '../src/components/preview/spring';
import type { DatasetPreviewSource } from '../src/components/datasetpreview/types';
import type { RenderJob } from '../src/components/preview/types';
import type { PreviewSource as UploadSource } from '../src/components/upload/types';
import { drawDatasetPreviewWhenReady, withDatasetPreviewFixture } from './datasetPreviewTest';

const DATASET_ID = '0000000000000000000000DS12';
const UPLOAD_ID = '01JYZ9K7WQ3N8V4M2X6C5B0UP2';
const RENDER_ID = '01JYZ9K7WQ3N8V4M2X6C5B0RE2';
const WAIT = { timeout: 5000 };
const WIDE = { west: -90, south: -10, east: 90, north: 10 };

/** 확정 값 6 — 투영 감속률. */
const DECEL = 0.998;
/** 세로 이동 범위 = ±(1600 − 512)/2. 첫 자리(편차 0)의 화면 y = −544. */
const HALF = (1600 - 512) / 2;
const Y0 = (512 - 1600) / 2;

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
    lookupValue: vi.fn(async () => undefined),
  } as unknown as DatasetPreviewSource);
}

async function mountDetail(source: DatasetPreviewSource = detailSource()) {
  render(<DatasetPreviewSection datasetId={DATASET_ID} source={source} pollMs={5} />);
  drawDatasetPreviewWhenReady();
  await waitFor(() => expect(screen.getByTestId('preview-map')).toBeTruthy(), WAIT);
  return { viewport: screen.getByTestId('preview-viewport'), layers: screen.getByTestId('preview-layers') };
}

function uploadSource(): UploadSource {
  return {
    palettes: vi.fn(async () => [{ palette: 'viridis', label: '비리디스' }]),
    createRender: vi.fn(async () => doneJob()),
    getRender: vi.fn(async () => doneJob()),
    files: vi.fn(async () => [
      { fileId: '01JYZ9K7WQ3N8V4M2X6C5B0F11', fileName: 'rain.nc', renderable: true },
    ]),
    describe: vi.fn(async () => ({
      variables: ['rainfall'], instants: null,
      default: { variable: 'rainfall', instant: null },
    })),
  } as unknown as UploadSource;
}

async function mountUpload() {
  render(<PreviewPanel source={uploadSource()} uploadId={UPLOAD_ID} hasReferenceGrid />);
  const draw = await screen.findByTestId('up-preview-draw');
  await waitFor(() => expect(screen.getByTestId('up-style-palette')).toBeTruthy(), WAIT);
  fireEvent.click(draw);
  const viewport = await screen.findByTestId('up-preview-viewport');
  return { viewport, layers: screen.getByTestId('up-preview-layers') };
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

/** 가짜 시간 — rAF · performance 만. setTimeout 은 실시간으로 둔다(마운트 뒤에 켠다). */
function fakeClock() {
  vi.useFakeTimers({ toFake: ['requestAnimationFrame', 'cancelAnimationFrame', 'performance'] });
}
const advance = (ms: number) => act(() => { vi.advanceTimersByTime(ms); });

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

/**
 * 느린 끌기 — 누름(0ms · y 300) → 10ms 311 → 20ms 312 → 30ms 313 → 30ms 놓기.
 * 마지막 100ms 이동 기록의 평균 = (313 − 300) / 30 px/ms. 목표는 이동 범위 안이다.
 */
function slowFling(viewport: HTMLElement) {
  fireEvent.pointerDown(viewport, { pointerId: 1, clientX: 300, clientY: 300, button: 0 });
  advance(10);
  fireEvent.pointerMove(window, { pointerId: 1, clientX: 300, clientY: 311 });
  advance(10);
  fireEvent.pointerMove(window, { pointerId: 1, clientX: 300, clientY: 312 });
  advance(10);
  fireEvent.pointerMove(window, { pointerId: 1, clientX: 300, clientY: 313 });
  fireEvent.pointerUp(window, { pointerId: 1, clientX: 300, clientY: 313 });
  return { released: 13, v: 13 / 30 };
}

/** 빠른 끌기 — 10ms 마다 20px. 투영 목표가 이동 범위를 넘어 `clampView` 가 자른다. */
function fastFling(viewport: HTMLElement) {
  fireEvent.pointerDown(viewport, { pointerId: 1, clientX: 300, clientY: 300, button: 0 });
  for (let i = 1; i <= 4; i += 1) {
    advance(10);
    fireEvent.pointerMove(window, { pointerId: 1, clientX: 300, clientY: 300 + 20 * i });
  }
  fireEvent.pointerUp(window, { pointerId: 1, clientX: 300, clientY: 380 });
  return { released: 80 };
}

/* ═══ 값 5 · 6 — 스프링 함수(순수) ════════════════════════════════════════ */

describe('#5 spring() — 임계 감쇠(damping 1.0) · response 0.4s', () => {
  it('response 는 확정 값 6(0.4s)이다', () => {
    expect(SPRING_RESPONSE).toBe(0.4);
  });

  it('t = 0 에서 위치 = 시작 · 속도 = 놓은 속도', () => {
    const s = spring(10, 200, 350, 0);
    expect(s.value).toBeCloseTo(10, 9);
    expect(s.velocity).toBeCloseTo(350, 9);
  });

  it('목표를 넘지 않는다 — 정지 출발 · 투영 속도 출발 모두', () => {
    const cases: Array<[number, number, number]> = [
      [0, 100, 0],
      [0, -100, 0],
      // 투영 목표 = 시작 + (v/1000)·0.998/(1−0.998) 일 때의 놓은 속도
      [0, (2000 / 1000) * DECEL / (1 - DECEL), 2000],
      [50, 50 + (-800 / 1000) * DECEL / (1 - DECEL), -800],
    ];
    for (const [from, to, v0] of cases) {
      const dir = Math.sign(to - from);
      for (let t = 0; t <= 3 * SPRING_RESPONSE; t += 0.001) {
        expect(dir * (spring(from, to, v0, t).value - to)).toBeLessThanOrEqual(1e-9);
      }
    }
  });

  it('response 의 3배 안에 목표 0.5px 안으로 선다', () => {
    const cases: Array<[number, number, number]> = [
      [0, 1000, 0],
      [0, (10000 / 1000) * DECEL / (1 - DECEL), 10000],
    ];
    for (const [from, to, v0] of cases) {
      expect(Math.abs(spring(from, to, v0, 3 * SPRING_RESPONSE).value - to)).toBeLessThan(0.5);
    }
  });
});

/* ═══ 동작 — 놓은 뒤 관성 · 경계 · 중단 · 동작 줄이기 ═════════════════════════ */

describe('#5 놓은 뒤 관성 — 속도를 이어받아 clampView(투영 목표)에 선다', () => {
  it('상세 — 놓은 뒤에도 같은 방향으로 이어지고 투영 목표에 정확히 선다', async () => {
    const { viewport, layers } = await mountDetail();
    prepare(viewport, layers);
    await waitFor(() => expect(yOf(layers)).toBeCloseTo(Y0), WAIT);
    fakeClock();
    const { released, v } = slowFling(viewport);
    expect(yOf(layers)).toBeCloseTo(Y0 + released);
    advance(16);
    expect(yOf(layers)).toBeGreaterThan(Y0 + released);
    advance(3 * SPRING_RESPONSE * 1000);
    const target = released + (v * DECEL) / (1 - DECEL);
    expect(target).toBeLessThan(HALF);
    expect(yOf(layers)).toBeCloseTo(Y0 + target, 3);
  });

  it('업로드 — 빠르게 끌고 놓으면 이동 범위 끝(clampView)에서 멈춘다', async () => {
    const { viewport, layers } = await mountUpload();
    prepare(viewport, layers);
    await waitFor(() => expect(yOf(layers)).toBeCloseTo(Y0), WAIT);
    fakeClock();
    const { released } = fastFling(viewport);
    expect(yOf(layers)).toBeCloseTo(Y0 + released);
    advance(16);
    expect(yOf(layers)).toBeGreaterThan(Y0 + released);
    advance(3 * SPRING_RESPONSE * 1000);
    expect(yOf(layers)).toBeCloseTo(Y0 + HALF, 3);
    // 경계를 넘어갔다 돌아오지 않는다 — 매 프레임 범위 안이다.
    advance(500);
    expect(yOf(layers)).toBeCloseTo(Y0 + HALF, 3);
  });

  it('관성이 끝나도 렌더를 다시 걸지 않는다(`dataset-preview-zoom-latency` 조건 유지)', async () => {
    const source = detailSource();
    const { viewport, layers } = await mountDetail(source);
    prepare(viewport, layers);
    await waitFor(() => expect(yOf(layers)).toBeCloseTo(Y0), WAIT);
    const created = vi.mocked(source.create).mock.calls.length;
    fakeClock();
    fastFling(viewport);
    advance(3 * SPRING_RESPONSE * 1000);
    expect(vi.mocked(source.create).mock.calls.length - created).toBe(0);
  });

  it('잠시 멈췄다 놓으면(마지막 100ms 이동 없음) 관성이 없다', async () => {
    const { viewport, layers } = await mountDetail();
    prepare(viewport, layers);
    await waitFor(() => expect(yOf(layers)).toBeCloseTo(Y0), WAIT);
    fakeClock();
    fireEvent.pointerDown(viewport, { pointerId: 1, clientX: 300, clientY: 300, button: 0 });
    advance(10);
    fireEvent.pointerMove(window, { pointerId: 1, clientX: 300, clientY: 340 });
    advance(150);
    fireEvent.pointerUp(window, { pointerId: 1, clientX: 300, clientY: 340 });
    advance(1000);
    expect(yOf(layers)).toBeCloseTo(Y0 + 40);
  });
});

describe('#5 관성 중단 — 그 프레임 값에서 멈추고 튀지 않는다', () => {
  const interrupts: Array<[string, (viewport: HTMLElement) => void]> = [
    ['새로 누르기(pointerDown)', (vp) => fireEvent.pointerDown(vp, { pointerId: 2, clientX: 200, clientY: 200, button: 0 })],
    ['휠', (vp) => fireEvent.wheel(vp, { deltaY: -120, clientX: 256, clientY: 256 })],
    ['확대 단추', () => fireEvent.click(screen.getByRole('button', { name: '확대' }))],
    ['축소 단추', () => fireEvent.click(screen.getByRole('button', { name: '축소' }))],
    ['기본 배율로 단추', () => fireEvent.click(screen.getByRole('button', { name: '기본 배율로' }))],
    ['더블클릭', (vp) => fireEvent.doubleClick(vp)],
  ];
  for (const [name, interrupt] of interrupts) {
    it(`${name} — 그 뒤 시간이 흘러도 변환이 그대로다`, async () => {
      const { viewport, layers } = await mountDetail();
      prepare(viewport, layers);
      await waitFor(() => expect(yOf(layers)).toBeCloseTo(Y0), WAIT);
      fakeClock();
      const { released } = fastFling(viewport);
      advance(32);
      const mid = yOf(layers);
      expect(mid).toBeGreaterThan(Y0 + released);
      expect(mid).toBeLessThan(Y0 + HALF);
      interrupt(viewport);
      const after = transformOf(layers);
      if (name.startsWith('새로 누르기')) expect(yOf(layers)).toBeCloseTo(mid, 9);
      advance(1000);
      expect(transformOf(layers)).toBe(after);
    });
  }
});

describe('#5 동작 줄이기 — 관성 0', () => {
  it('prefers-reduced-motion: reduce 가 참이면 놓은 자리에 선다', async () => {
    vi.stubGlobal('matchMedia', (q: string) => ({
      matches: q.includes('prefers-reduced-motion') && q.includes('reduce'),
      media: q, onchange: null,
      addEventListener: () => {}, removeEventListener: () => {},
      addListener: () => {}, removeListener: () => {}, dispatchEvent: () => false,
    }));
    const { viewport, layers } = await mountDetail();
    prepare(viewport, layers);
    await waitFor(() => expect(yOf(layers)).toBeCloseTo(Y0), WAIT);
    fakeClock();
    const { released } = fastFling(viewport);
    advance(1000);
    expect(yOf(layers)).toBeCloseTo(Y0 + released);
  });
});
