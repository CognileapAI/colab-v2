/**
 * design-fix 20260924 · L3 미리보기 제스처 — #3 포인터 끌기(값 4 = 10px).
 *
 * 오라클 = `dev-package/prd/specs/S-DESIGN-FIX-20260924.md` §4 「L3」 행 #3 · 확정 값 4.
 *  - 마우스 이벤트 → 포인터 이벤트 ＋ `setPointerCapture` ＋ 시작 임계 10px(넘기 전 불변 ·
 *    넘는 순간 누른 자리 기준 1:1) · 끌기 성립 뒤 click(값 조회) 버림 · 임계 안의 click 은 조회.
 *  - 상세 미리보기 · 업로드 미리보기 둘 다 · pointerType mouse · touch · pen 같다.
 * ⚠ jsdom 29.1.1 은 PointerEvent 는 있고 `setPointerCapture` 는 없다(advisor ① F5) — 제품은
 *   optional-call 로 부르고, 호출 여부를 재는 이 시험만 스텁을 심는다.
 * ⚠ jsdom 은 레이아웃을 계산하지 않는다 — 뷰포트 · 내용 상자는 시험이 심는다
 *   (선례 `preview-map-viewport-20260918.test.tsx` 의 `sizeViewport` · `sizeContent`).
 */
// @ts-expect-error — 타입 선언 없이 런타임만 쓴다(`preview-map-viewport-20260918` 와 같은 규율).
import { readFileSync } from 'node:fs';
// @ts-expect-error — 같은 이유.
import { resolve } from 'node:path';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { DatasetPreviewSection } from '../src/components/datasetpreview/DatasetPreviewSection';
import { PreviewPanel } from '../src/components/upload/PreviewPanel';
import type { DatasetPreviewSource, ValueLookupResult } from '../src/components/datasetpreview/types';
import type { RenderJob } from '../src/components/preview/types';
import type { PreviewSource as UploadSource } from '../src/components/upload/types';
import { drawDatasetPreviewWhenReady, withDatasetPreviewFixture } from './datasetPreviewTest';

declare const process: { cwd(): string };

const DATASET_ID = '0000000000000000000000DS12';
const UPLOAD_ID = '01JYZ9K7WQ3N8V4M2X6C5B0UP2';
const RENDER_ID = '01JYZ9K7WQ3N8V4M2X6C5B0RE2';
const WAIT = { timeout: 5000 };

/** 기본 배율이 정확히 1 인 넓은 경계 — 축척 사다리를 이 시험의 변수에서 뺀다. */
const WIDE = { west: -90, south: -10, east: 90, north: 10 };

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

const HIT: ValueLookupResult = {
  available: true, value: 12.5, unit: 'mm', variable: '강우량',
  exactness: '원본과 같은 칸',
  cell: { row: 2, col: 3, center: { lat: 0, lon: 0 }, sizeDegrees: 0.25 },
  unavailableReason: null,
} as unknown as ValueLookupResult;

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

/** jsdom 은 레이아웃을 안 한다 — 뷰포트 상자를 시험이 준다. */
function sizeViewport(el: Element, width: number, height: number) {
  Object.defineProperty(el, 'clientWidth', { value: width, configurable: true });
  Object.defineProperty(el, 'clientHeight', { value: height, configurable: true });
  el.getBoundingClientRect = () =>
    ({ left: 0, top: 0, width, height, right: width, bottom: height, x: 0, y: 0,
       toJSON: () => ({}) }) as DOMRect;
}

/** 내용 상자 — 세로가 긴 그림이라 세로로 옮길 자리가 있다(±(1600 − 512)/2). */
function sizeContent(el: Element, width: number, height: number) {
  Object.defineProperty(el, 'offsetWidth', { value: width, configurable: true });
  Object.defineProperty(el, 'offsetHeight', { value: height, configurable: true });
}

function transformOf(layers: HTMLElement): { x: number; y: number; scale: number } {
  const t = layers.style.getPropertyValue('--pv-layers-transform');
  const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([-\d.]+)\)/.exec(t);
  expect(m, `transform 원문을 읽지 못했다: ${t}`).toBeTruthy();
  return { x: Number(m![1]), y: Number(m![2]), scale: Number(m![3]) };
}

/** 세로가 긴 내용(512 × 1600)을 512 × 512 뷰포트에 둔다 — 첫 자리 y = (512 − 1600)/2. */
function prepare(viewport: HTMLElement, layers: HTMLElement) {
  sizeViewport(viewport, 512, 512);
  sizeContent(layers, 512, 1600);
  // 크기를 심은 뒤 한 번 다시 그리게 한다(창 크기 변화와 같은 경로).
  const img = viewport.querySelector('img') as HTMLImageElement;
  Object.defineProperty(img, 'naturalWidth', { value: 4096, configurable: true });
  fireEvent.load(img);
}

const SCREENS = [
  ['상세 미리보기', mountDetail],
  ['업로드 미리보기', mountUpload],
] as const;

const POINTER_TYPES = ['mouse', 'touch', 'pen'] as const;

const tick = () => new Promise((r) => setTimeout(r, 30));

/* ═══ #3 — 시작 임계 10px · 누른 자리 기준 1:1 · 포인터 캡처 ═══════════════ */

describe('#3 포인터 끌기 — 임계 10px(값 4)', () => {
  for (const [name, mount] of SCREENS) {
    for (const pointerType of POINTER_TYPES) {
      it(`${name} · ${pointerType} — 5px 은 불변 · 11px 에서 누른 자리 기준 11px 이동 · 캡처(1)`, async () => {
        const { viewport, layers } = await mount();
        prepare(viewport, layers);
        await waitFor(() => expect(transformOf(layers).y).toBeCloseTo((512 - 1600) / 2), WAIT);
        const capture = vi.fn();
        (viewport as unknown as { setPointerCapture: unknown }).setPointerCapture = capture;
        const before = transformOf(layers);

        fireEvent.pointerDown(viewport, { pointerId: 1, pointerType, clientX: 300, clientY: 300, button: 0 });
        expect(capture).toHaveBeenCalledWith(1);

        fireEvent.pointerMove(window, { pointerId: 1, pointerType, clientX: 300, clientY: 305 });
        expect(transformOf(layers)).toEqual(before);

        fireEvent.pointerMove(window, { pointerId: 1, pointerType, clientX: 300, clientY: 311 });
        expect(transformOf(layers).y).toBeCloseTo(before.y + 11);
        expect(transformOf(layers).x).toBeCloseTo(before.x);

        // 임계를 넘은 뒤에는 1:1 이다.
        fireEvent.pointerMove(window, { pointerId: 1, pointerType, clientX: 300, clientY: 331 });
        expect(transformOf(layers).y).toBeCloseTo(before.y + 31);
        fireEvent.pointerUp(window, { pointerId: 1, pointerType, clientX: 300, clientY: 331 });
      });
    }
  }

  it('캡처가 없는 환경(jsdom 기본)에서도 끌기가 선다 — optional-call', async () => {
    const { viewport, layers } = await mountDetail();
    prepare(viewport, layers);
    await waitFor(() => expect(transformOf(layers).y).toBeCloseTo((512 - 1600) / 2), WAIT);
    expect((viewport as unknown as { setPointerCapture?: unknown }).setPointerCapture).toBeUndefined();
    const before = transformOf(layers);
    fireEvent.pointerDown(viewport, { pointerId: 1, clientX: 300, clientY: 300, button: 0 });
    fireEvent.pointerMove(window, { pointerId: 1, clientX: 300, clientY: 320 });
    fireEvent.pointerUp(window, { pointerId: 1, clientX: 300, clientY: 320 });
    expect(transformOf(layers).y).toBeCloseTo(before.y + 20);
  });

  it('주 단추가 아니면 끌기를 시작하지 않는다', async () => {
    const { viewport, layers } = await mountDetail();
    prepare(viewport, layers);
    await waitFor(() => expect(transformOf(layers).y).toBeCloseTo((512 - 1600) / 2), WAIT);
    const before = transformOf(layers);
    fireEvent.pointerDown(viewport, { pointerId: 1, clientX: 300, clientY: 300, button: 2 });
    fireEvent.pointerMove(window, { pointerId: 1, clientX: 300, clientY: 340 });
    fireEvent.pointerUp(window, { pointerId: 1 });
    expect(transformOf(layers)).toEqual(before);
  });
});

/* ═══ #3 — 끌기 성립 뒤 click 은 값 조회를 부르지 않는다 ═════════════════════ */

describe('#3 끌기 뒤 click 버림 — 임계 안의 click 은 조회한다', () => {
  it('11px 끌고 놓은 뒤의 click 은 값 조회 0 · 이어서 4px 안의 click 은 조회 1', async () => {
    const source = detailSource();
    const { viewport, layers } = await mountDetail(source);
    prepare(viewport, layers);

    fireEvent.pointerDown(viewport, { pointerId: 1, clientX: 256, clientY: 256, button: 0 });
    fireEvent.pointerMove(window, { pointerId: 1, clientX: 256, clientY: 267 });
    // 멈췄다 놓는다(마지막 100ms 이동 없음 → 관성 0). 관성이 돌면 다음 탭은 「관성을 잡는 탭」이라
    // 조회하지 않는다(F-preview A35) — 이 시험의 둘째 탭은 평소 탭이어야 한다.
    await new Promise((r) => setTimeout(r, 150));
    fireEvent.pointerUp(window, { pointerId: 1, clientX: 256, clientY: 267 });
    fireEvent.click(viewport, { clientX: 256, clientY: 267 });
    await tick();
    expect(source.lookupValue).toHaveBeenCalledTimes(0);

    fireEvent.pointerDown(viewport, { pointerId: 1, clientX: 256, clientY: 256, button: 0 });
    fireEvent.pointerMove(window, { pointerId: 1, clientX: 256, clientY: 260 });
    fireEvent.pointerUp(window, { pointerId: 1, clientX: 256, clientY: 260 });
    fireEvent.click(viewport, { clientX: 256, clientY: 260 });
    await waitFor(() => expect(source.lookupValue).toHaveBeenCalledTimes(1), WAIT);
  });
});

/* ═══ #3 — 공개 인터페이스 onMouseDown → onPointerDown ════════════════════════ */

/** 주석을 걷고 읽는다 — 주석 속 이름이 계측에 섞이지 않도록. */
const code = (rel: string): string =>
  String(readFileSync(resolve(process.cwd(), rel), 'utf8'))
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .replace(/(^|[^:])\/\/.*$/gm, '$1');

describe('#3 공개 인터페이스 — onMouseDown 0 · onPointerDown', () => {
  const files = [
    'src/components/preview/useZoomPan.ts',
    'src/components/preview/PreviewPanels.tsx',
    'src/components/preview/PreviewOverlay.tsx',
    'src/components/upload/PreviewPanel.tsx',
  ];
  for (const f of files) {
    it(`${f} 에 onMouseDown 이 없고 onPointerDown 이 있다`, () => {
      const src = code(f);
      expect(src).not.toMatch(/onMouseDown/);
      expect(src).toMatch(/onPointerDown/);
    });
  }

  it('캡처는 optional-call 로 부른다(advisor ① F5)', () => {
    expect(code('src/components/preview/useZoomPan.ts')).toMatch(/setPointerCapture\?\.\(/);
  });
});
