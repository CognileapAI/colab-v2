/**
 * #120 미리보기를 지도식 뷰포트로 — **도구 층 고정 · 그림 중앙 정렬 · 커서 고정점 확대**.
 *
 * 오라클 = `dev-package/prd/specs/2026-09-18-issue-120-preview-map-viewport.md` 「시험 결정」
 *          ⑴~⑺ (승인 intent `dev-package/intent/2026-09-18-issue-120-preview-map-viewport.md`).
 *
 * ⚠ **jsdom 은 레이아웃을 계산하지 않는다** — 배치 판정은 두 갈래로 세운다.
 *   ㈎ DOM 관계(`contains` · `parentElement`) ㈏ CSS 원문 계측(주석 제거 뒤 존재 단언).
 *   선례 = `preview-layout-20260912.test.tsx` 의 `block()` 도우미.
 * ⚠ **내용 상자는 시험이 심는다** — `.pv-layers` 의 `offsetWidth/offsetHeight` 를
 *   `Object.defineProperty` 로 준다(뷰포트 `clientWidth` 를 주던 것과 같은 방식).
 *   대조군(내용 = 뷰포트)과 실험군(내용 ≠ 뷰포트)을 **쌍**으로 둬 새 인자가 실제로
 *   결과를 바꿈을 보인다(우려 5 · green-by-skip 방지).
 * ⚠ 화면 글자를 새로 만들지 않는다 — 기대 문자열은 전부 이미 있는 정본 문면이다.
 */
// @ts-expect-error — 타입 선언 없이 런타임만 쓴다(`preview-layout-20260912` 와 같은 규율).
import { readFileSync } from 'node:fs';
// @ts-expect-error — 같은 이유.
import { resolve } from 'node:path';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { DatasetPreviewSection } from '../src/components/datasetpreview/DatasetPreviewSection';
import { PreviewPanel } from '../src/components/upload/PreviewPanel';
import { UnregisteredPreviewPage } from '../src/routes/UnregisteredPreviewPage';
import { PREVIEW_ROUTE_PATH, previewPath } from '../src/components/preview/handoff';
import { centeredPanFor } from '../src/components/preview/useZoomPan';
import type { DatasetPreviewSource, ValueLookupResult } from '../src/components/datasetpreview/types';
import type { PreviewSource as UnregisteredSource, RenderJob } from '../src/components/preview/types';
import type { PreviewSource as UploadSource } from '../src/components/upload/types';
import { drawDatasetPreviewWhenReady, withDatasetPreviewFixture } from './datasetPreviewTest';

declare const process: { cwd(): string };

const DATASET_ID = '0000000000000000000000DS12';
const UPLOAD_ID = '01JYZ9K7WQ3N8V4M2X6C5B0UP2';
const RENDER_ID = '01JYZ9K7WQ3N8V4M2X6C5B0RE2';
const WAIT = { timeout: 5000 };

/**
 * 폭이 가장 큰 단을 넘는 경계 — **기본 배율이 정확히 1** 이다(`baseScaleFor = min(1, w/snap)`).
 * 축척 사다리를 이 시험의 변수에서 뺀다. 이번 이슈가 바꾸는 것은 배율이 아니라 자리다.
 */
const WIDE = { west: -90, south: -10, east: 90, north: 10 };

const LEGEND = {
  palette: 'viridis',
  unit: 'mm',
  variable: 'rainfall',
  classes: [{ color: '#440154', min: 0, max: 5 }],
};

function doneJob(bounds: typeof WIDE | undefined = WIDE): RenderJob {
  return {
    renderId: RENDER_ID,
    status: '완료',
    result: {
      imageUrl: 'https://viz.example/d/map.png',
      legend: LEGEND,
      ...(bounds ? { bounds } : {}),
    },
  } as unknown as RenderJob;
}

const HIT: ValueLookupResult = {
  available: true, value: 12.5, unit: 'mm', variable: '강우량',
  exactness: '원본과 같은 칸',
  cell: { row: 2, col: 3, center: { lat: 0, lon: 0 }, sizeDegrees: 0.25 },
  unavailableReason: null,
} as unknown as ValueLookupResult;

/* ── 화면 세 곳을 세우는 이음매 (기존 시험과 같은 방식) ─────────────────────── */

function detailSource(over: Partial<DatasetPreviewSource> = {}): DatasetPreviewSource {
  return withDatasetPreviewFixture({
    palettes: vi.fn(async () => [{ palette: 'viridis' }]),
    create: vi.fn(async () => doneJob()),
    get: vi.fn(async () => doneJob()),
    probeTile: vi.fn(async () => 'ok' as const),
    mapGeometry: vi.fn(async () => undefined),
    screenshot: vi.fn(async () => new Blob()),
    lookupValue: vi.fn(async () => HIT),
    ...over,
  } as unknown as DatasetPreviewSource);
}

async function mountDetail(source: DatasetPreviewSource) {
  render(<DatasetPreviewSection datasetId={DATASET_ID} source={source} pollMs={5} />);
  drawDatasetPreviewWhenReady();
  await waitFor(() => expect(screen.getByTestId('preview-map')).toBeTruthy(), WAIT);
  return screen.getByTestId('preview-viewport');
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
  const source = uploadSource();
  render(<PreviewPanel source={source} uploadId={UPLOAD_ID} hasReferenceGrid />);
  const draw = await screen.findByTestId('up-preview-draw');
  await waitFor(() => expect(screen.getByTestId('up-style-palette')).toBeTruthy(), WAIT);
  fireEvent.click(draw);
  return screen.findByTestId('up-preview-viewport');
}

function unregisteredSource(): UnregisteredSource {
  return {
    get: vi.fn(async () => doneJob()),
    create: vi.fn(async () => doneJob()),
    probeTile: vi.fn(async () => 'ok' as const),
  } as unknown as UnregisteredSource;
}

async function mountUnregistered() {
  const path = previewPath(UPLOAD_ID, RENDER_ID);
  render(
    <MemoryRouter
      initialEntries={[{ pathname: path.split('?')[0]!, search: path.split('?')[1] ?? '' }]}
    >
      <Routes>
        <Route
          path={PREVIEW_ROUTE_PATH}
          element={<UnregisteredPreviewPage source={unregisteredSource()} pollMs={1} />}
        />
      </Routes>
    </MemoryRouter>,
  );
  await screen.findByTestId('preview-map', {}, WAIT);
  return screen.getByTestId('preview-viewport');
}

/* ── 상자 심기 ────────────────────────────────────────────────────────────── */

/** jsdom 은 레이아웃을 안 한다 — 뷰포트 상자를 시험이 명시적으로 준다. */
function sizeViewport(el: Element, width: number, height: number) {
  Object.defineProperty(el, 'clientWidth', { value: width, configurable: true });
  Object.defineProperty(el, 'clientHeight', { value: height, configurable: true });
  el.getBoundingClientRect = () =>
    ({ left: 0, top: 0, width, height, right: width, bottom: height, x: 0, y: 0,
       toJSON: () => ({}) }) as DOMRect;
}

/** 내용 상자(층 묶음의 배치 크기) 를 심는다 — 그림의 가로세로비가 뷰포트와 다른 경우. */
function sizeContent(el: Element, width: number, height: number) {
  Object.defineProperty(el, 'offsetWidth', { value: width, configurable: true });
  Object.defineProperty(el, 'offsetHeight', { value: height, configurable: true });
}

/** `transform: translate(Xpx, Ypx) scale(S)` 원문에서 세 수를 읽는다. */
function transformOf(layers: HTMLElement): { x: number; y: number; scale: number } {
  const t = layers.style.getPropertyValue('--pv-layers-transform');
  const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([-\d.]+)\)/.exec(t);
  expect(m, `transform 원문을 읽지 못했다: ${t}`).toBeTruthy();
  return { x: Number(m![1]), y: Number(m![2]), scale: Number(m![3]) };
}

/** 한계 배율을 심고 `load` 를 알린다 — 없는 한계를 지어내지 않는다(정본 §8 조건 ⑷). */
function learnNativeWidth(viewport: HTMLElement, naturalPx: number) {
  const img = viewport.querySelector('img') as HTMLImageElement;
  Object.defineProperty(img, 'naturalWidth', { value: naturalPx, configurable: true });
  Object.defineProperty(img, 'naturalHeight', { value: naturalPx, configurable: true });
  fireEvent.load(img);
}

/* ── CSS 원문 계측 ────────────────────────────────────────────────────────── */

/** 주석은 걷어내고 읽는다 — 주석 속 선택자·값이 계측에 섞이지 않도록. */
const read = (rel: string): string =>
  String(readFileSync(resolve(process.cwd(), rel), 'utf8')).replace(/\/\*[\s\S]*?\*\//g, '');

const PREVIEW_CSS = read('src/components/preview/preview.css');
const UPLOAD_CSS = read('src/components/upload/upload.css');

/** 선택자 하나의 선언 블록(`{ … }`)을 원문에서 잘라낸다. 부재면 그 자리에서 실패한다. */
function block(css: string, selector: string): string {
  const at = css.indexOf(selector);
  expect(at, `선택자 부재: ${selector}`).toBeGreaterThan(-1);
  const open = css.indexOf('{', at);
  return css.slice(open + 1, css.indexOf('}', open));
}

/* ═══ ⑴ 도구 층이 뷰포트의 직계 자식이고 층 묶음의 형제다 — 네 화면 ═══════════ */

describe('⑴ 도구 층 — 네 화면에서 뷰포트 안 · 층 묶음 밖', () => {
  it('상세 — 확대 줄·범례·HUD·값 조회가 도구 층 자손이고 층 묶음 자손이 아니다', async () => {
    const viewport = await mountDetail(detailSource());
    const layers = screen.getByTestId('preview-layers');

    // **존재를 먼저 단언한다** — 조회 실패 0건을 통과로 세지 않는다.
    const zoomRow = screen.getByTestId('preview-zoom');
    const legend = viewport.querySelector('.pv-legend') as HTMLElement | null;
    const hud = screen.getByTestId('preview-cursor-hud');
    const valuePanel = screen.getByTestId('value-lookup');
    expect(legend, '범례가 뷰포트 안에 없다').toBeTruthy();

    const overlay = screen.getByTestId('preview-overlay');
    expect(overlay.parentElement).toBe(viewport);
    expect(overlay.previousElementSibling).toBe(layers);
    for (const tool of [zoomRow, legend!, hud, valuePanel]) {
      expect(overlay.contains(tool)).toBe(true);
      expect(layers.contains(tool)).toBe(false);
    }
  });

  it('업로드 인라인 — 확대 줄이 도구 층 자손이다', async () => {
    const viewport = await mountUpload();
    const zoomRow = await screen.findByTestId('up-preview-zoom');
    const overlay = screen.getByTestId('up-preview-overlay');
    expect(overlay.parentElement).toBe(viewport);
    expect(overlay.previousElementSibling).toBe(screen.getByTestId('up-preview-layers'));
    expect(overlay.contains(zoomRow)).toBe(true);
    expect(screen.getByTestId('up-preview-layers').contains(zoomRow)).toBe(false);
  });

  it('확장보기 — 확대 줄이 도구 층 자손이다', async () => {
    await mountUpload();
    await screen.findByTestId('up-preview-zoom');
    fireEvent.click(screen.getByTestId('pv-expand'));
    const viewport = await screen.findByTestId('pv-expand-viewport');
    const zoomRow = await screen.findByTestId('pv-expand-zoom');
    const overlay = screen.getByTestId('pv-expand-tools');
    expect(overlay.parentElement).toBe(viewport);
    expect(overlay.previousElementSibling).toBe(screen.getByTestId('pv-expand-layers'));
    expect(overlay.contains(zoomRow)).toBe(true);
  });

  it('등록 전 미리보기 — 확대 줄은 없고 범례·HUD 가 도구 층에 선다', async () => {
    const viewport = await mountUnregistered();
    const overlay = screen.getByTestId('preview-overlay');
    const legend = viewport.querySelector('.pv-legend') as HTMLElement | null;
    const hud = screen.getByTestId('preview-cursor-hud');
    expect(legend, '범례가 뷰포트 안에 없다').toBeTruthy();
    expect(overlay.parentElement).toBe(viewport);
    expect(overlay.contains(legend!)).toBe(true);
    expect(overlay.contains(hud)).toBe(true);
    // zoom 을 받지 않는 화면이라 확대 줄 자체가 없다 — 없는 조작을 세우지 않는다.
    expect(screen.queryByTestId('preview-zoom')).toBeNull();
  });
});

/* ═══ ⑵ 뷰포트 밖에는 아무 것도 남지 않는다 ═══════════════════════════════ */

describe('⑵ `.pv-mapcol` 에는 뷰포트만 · `.pv-map` 오른쪽 열이 없다', () => {
  it('상세 — 지도 열의 자식이 뷰포트 하나다', async () => {
    const viewport = await mountDetail(detailSource());
    const column = viewport.parentElement as HTMLElement;
    expect(column.className).toContain('pv-mapcol');
    expect(Array.from(column.children)).toEqual([viewport]);
  });

  it('상세 — 도구 층 밖에 선 범례가 없다', async () => {
    const viewport = await mountDetail(detailSource());
    const map = screen.getByTestId('preview-map');
    const legends = Array.from(map.querySelectorAll('.pv-legend'));
    expect(legends.length).toBe(1);
    const overlay = screen.getByTestId('preview-overlay');
    expect(overlay.contains(legends[0]!)).toBe(true);
    expect(viewport.contains(legends[0]!)).toBe(true);
  });
});

/* ═══ ⑶ 중앙 정렬 — 내용 상자 기준 두 축 ═══════════════════════════════════ */

describe('⑶ 중앙 정렬 — 순수 함수 `centeredPanFor`', () => {
  it('대조군 — 내용 = 뷰포트이면 종전과 같은 수를 낸다', () => {
    const pan = centeredPanFor({ scale: 0.5, x: 0, y: 0 }, { width: 1000, height: 800 });
    expect(pan.x).toBeCloseTo(250);
    expect(pan.y).toBeCloseTo(200);
  });

  it('실험군 — 내용 ≠ 뷰포트이면 두 축이 각자의 상자로 중앙에 선다', () => {
    const pan = centeredPanFor(
      { scale: 1, x: 0, y: 0 },
      { width: 1000, height: 800 },
      { width: 500, height: 1600 },
    );
    expect(pan.x).toBeCloseTo(250);
    // **내용이 뷰포트보다 큰 축도 중앙이다** — 종전 `(0,0)` 은 위 정렬이었다(우려 8).
    expect(pan.y).toBeCloseTo(-400);
  });

  it('실험군 — 이동값은 중앙 기준 편차라 0 이 곧 중앙이다', () => {
    const pan = centeredPanFor(
      { scale: 1, x: 100, y: 50 },
      { width: 1000, height: 800 },
      { width: 500, height: 1600 },
    );
    expect(pan.x).toBeCloseTo(350);
    expect(pan.y).toBeCloseTo(-350);
  });

  it('크기를 못 쟀으면 자리를 지어내지 않는다', () => {
    const pan = centeredPanFor({ scale: 0.5, x: 7, y: 9 }, undefined);
    expect(pan).toEqual({ x: 7, y: 9 });
  });
});

describe('⑶ 중앙 정렬 — 훅이 내용 상자를 실제로 읽는다', () => {
  it('세로가 긴 그림이 첫 표시에서 세로 중앙에 선다 · 드래그로 아래 가장자리까지 간다', async () => {
    const viewport = await mountDetail(detailSource());
    const layers = screen.getByTestId('preview-layers');
    sizeViewport(viewport, 512, 512);
    sizeContent(layers, 512, 1600);
    learnNativeWidth(viewport, 4096);

    await waitFor(() => expect(transformOf(layers).y).toBeCloseTo((512 - 1600) / 2), WAIT);
    expect(transformOf(layers).x).toBeCloseTo(0);

    // 배율 1 이상에서 아래 가장자리까지 끌어 볼 수 있다 — 범위는 내용 크기에서 온다.
    fireEvent.mouseDown(viewport, { clientX: 0, clientY: 0, button: 0 });
    fireEvent.mouseMove(window, { clientX: 0, clientY: -4000 });
    fireEvent.mouseUp(window, { clientX: 0, clientY: -4000 });
    expect(transformOf(layers).y).toBeCloseTo(512 - 1600);
  });

  it('「기본 배율로」가 넘치는 축도 중앙으로 되돌린다', async () => {
    const viewport = await mountDetail(detailSource());
    const layers = screen.getByTestId('preview-layers');
    sizeViewport(viewport, 512, 512);
    sizeContent(layers, 512, 1600);
    learnNativeWidth(viewport, 4096);

    fireEvent.mouseDown(viewport, { clientX: 0, clientY: 0, button: 0 });
    fireEvent.mouseMove(window, { clientX: 0, clientY: -4000 });
    fireEvent.mouseUp(window, { clientX: 0, clientY: -4000 });
    expect(transformOf(layers).y).toBeCloseTo(512 - 1600);

    fireEvent.click(screen.getByRole('button', { name: '기본 배율로' }));
    expect(transformOf(layers).y).toBeCloseTo((512 - 1600) / 2);
  });
});

/* ═══ ⑷ 휠 확대의 고정점은 커서다 ═════════════════════════════════════════ */

describe('⑷ 휠 확대 — 커서 아래 지점이 그 자리에 머문다', () => {
  it('확대 전후로 `(고정점 − 이동값) / 배율` 이 같다', async () => {
    const viewport = await mountDetail(detailSource());
    const layers = screen.getByTestId('preview-layers');
    sizeViewport(viewport, 512, 512);
    sizeContent(layers, 512, 512);
    learnNativeWidth(viewport, 4096);

    const ax = 128;
    const ay = 384;
    const before = transformOf(layers);
    const anchorBeforeX = (ax - before.x) / before.scale;
    const anchorBeforeY = (ay - before.y) / before.scale;

    fireEvent.wheel(viewport, { deltaY: -1, clientX: ax, clientY: ay });

    const after = transformOf(layers);
    expect(after.scale).toBe(before.scale * 2);
    expect((ax - after.x) / after.scale).toBeCloseTo(anchorBeforeX);
    expect((ay - after.y) / after.scale).toBeCloseTo(anchorBeforeY);
  });

  it('버튼 확대는 뷰포트 중심 고정점을 유지한다', async () => {
    const viewport = await mountDetail(detailSource());
    const layers = screen.getByTestId('preview-layers');
    sizeViewport(viewport, 512, 512);
    sizeContent(layers, 512, 512);
    learnNativeWidth(viewport, 4096);

    fireEvent.click(screen.getByRole('button', { name: '확대' }));
    const after = transformOf(layers);
    expect(after.scale).toBe(2);
    expect(after.x).toBeCloseTo(-256);
    expect(after.y).toBeCloseTo(-256);
  });

  it('도구 층 위의 휠은 그림을 확대하지 않는다', async () => {
    const viewport = await mountDetail(detailSource());
    const layers = screen.getByTestId('preview-layers');
    sizeViewport(viewport, 512, 512);
    sizeContent(layers, 512, 512);
    learnNativeWidth(viewport, 4096);

    // **먼저 확대 줄이 뷰포트 안에 있음을 단언한다** — 밖에 있으면 애초에 닿지 않아
    // 아래 음성 단언이 아무 것도 재지 않는다(green-by-skip 방지).
    const zoomRow = screen.getByTestId('preview-zoom');
    expect(viewport.contains(zoomRow)).toBe(true);

    const before = transformOf(layers);
    fireEvent.wheel(zoomRow, { deltaY: -1, clientX: 400, clientY: 400 });
    expect(transformOf(layers).scale).toBe(before.scale);
  });
});

/* ═══ ⑸ 역변환이 내용 상자를 쓴다 ═════════════════════════════════════════ */

describe('⑸ 값 조회 역변환 — 내용 상자 기준', () => {
  async function clickAt(content: { width: number; height: number }) {
    const source = detailSource();
    const viewport = await mountDetail(source);
    const layers = screen.getByTestId('preview-layers');
    sizeViewport(viewport, 1000, 800);
    sizeContent(layers, content.width, content.height);

    fireEvent.click(viewport, { clientX: 500, clientY: 500 });
    await waitFor(() => expect(source.lookupValue).toHaveBeenCalled(), WAIT);
    return vi.mocked(source.lookupValue!).mock.calls[0]![0];
  }

  it('대조군 — 내용 = 뷰포트이면 뷰포트 비율 그대로다', async () => {
    const point = await clickAt({ width: 1000, height: 800 });
    // fy = 500/800 = 0.625 → 위도 10 − 0.625 × 20 = −2.5
    expect(point.lat).toBeCloseTo(-2.5);
    expect(point.lon).toBeCloseTo(0);
  });

  it('실험군 — 내용이 뷰포트보다 낮으면 중앙 정렬분을 되돌린 값이 나간다', async () => {
    const point = await clickAt({ width: 1000, height: 400 });
    // 중앙 정렬 200px 을 뺀 fy = (500 − 200)/400 = 0.75 → 위도 10 − 0.75 × 20 = −5
    expect(point.lat).toBeCloseTo(-5);
    expect(point.lon).toBeCloseTo(0);
  });
});

/* ═══ ⑹ 도구 층 위의 조작은 그림에 닿지 않는다 ═════════════════════════════ */

describe('⑹ 도구 층의 이벤트 경계', () => {
  it('뷰포트 클릭은 값 조회를 일으키고(양성) 도구 층 클릭은 일으키지 않는다(음성)', async () => {
    const source = detailSource();
    const viewport = await mountDetail(source);
    const layers = screen.getByTestId('preview-layers');
    sizeViewport(viewport, 512, 512);
    sizeContent(layers, 512, 512);

    // 도구가 뷰포트 안에 있어야 이 음성 단언이 무언가를 잰다.
    const zoomRow = screen.getByTestId('preview-zoom');
    const valuePanel = screen.getByTestId('value-lookup');
    expect(viewport.contains(zoomRow)).toBe(true);
    expect(viewport.contains(valuePanel)).toBe(true);

    fireEvent.click(viewport, { clientX: 256, clientY: 256 });
    await waitFor(() => expect(source.lookupValue).toHaveBeenCalledTimes(1), WAIT);

    fireEvent.click(screen.getByRole('button', { name: '축소' }));
    fireEvent.click(valuePanel);
    expect(source.lookupValue).toHaveBeenCalledTimes(1);
  });

  it('도구 층 위 mousedown 은 드래그를 시작하지 않는다', async () => {
    const viewport = await mountDetail(detailSource());
    const layers = screen.getByTestId('preview-layers');
    sizeViewport(viewport, 512, 512);
    sizeContent(layers, 512, 1600);
    learnNativeWidth(viewport, 4096);

    const zoomRow = screen.getByTestId('preview-zoom');
    expect(viewport.contains(zoomRow)).toBe(true);

    const before = transformOf(layers);
    fireEvent.mouseDown(zoomRow, { clientX: 100, clientY: 100, button: 0 });
    fireEvent.mouseMove(window, { clientX: 100, clientY: -200 });
    fireEvent.mouseUp(window, { clientX: 100, clientY: -200 });
    expect(transformOf(layers).y).toBeCloseTo(before.y);
  });
});

/* ═══ ⑺ CSS 원문 계측 ═══════════════════════════════════════════════════ */

describe('⑺ CSS 원문 — 3층 구조와 도구 층 규칙', () => {
  it('뷰포트가 겹침의 기준 상자다', () => {
    expect(block(PREVIEW_CSS, '.pv-viewport {')).toContain('position: relative');
  });

  it('도구 층은 뷰포트를 덮되 빈 자리는 그림에 닿는다', () => {
    const overlay = block(PREVIEW_CSS, '.pv-overlay {');
    expect(overlay).toContain('position: absolute');
    expect(overlay).toContain('inset: 0');
    expect(overlay).toContain('pointer-events: none');
  });

  it('도구 요소만 포인터를 받고 불투명 표면 배경을 갖는다', () => {
    const tools = block(PREVIEW_CSS, '.pv-overlay .pv-zoom,');
    expect(tools).toContain('pointer-events: auto');
    expect(tools).toContain('background: var(--color-surface)');
    expect(tools).toContain('border: 1px solid var(--color-border)');
    expect(tools).toContain('border-radius: var(--radius-sm)');
  });

  it('지도 행이 여러 줄로 접히지 않는다 — 줄 높이가 그림 높이를 따라가지 않게', () => {
    const map = block(PREVIEW_CSS, '.pv-map {');
    expect(map).toContain('flex-wrap: nowrap');
    expect(map).not.toContain('flex-wrap: wrap');
  });

  it('지도 열이 틀의 가로도 받는다 — 뷰포트가 폭 0 으로 서지 않게', () => {
    // 도구가 도구 층으로 들어가 이 열의 자식이 뷰포트 하나뿐이고, 뷰포트 내용은 `width: 100%`
    // 라 스스로 폭을 만들지 못한다. 실화면에서 폭 0 으로 섰던 자리(레인 실측 2026-09-18).
    const column = block(PREVIEW_CSS, '.pv-frame .pv-mapcol {');
    expect(column).toContain('flex: 1 1 auto');
    expect(column).toContain('min-width: 0');
  });

  it('확장보기 뷰포트가 본문 높이를 받는다 — `.pvx-b` 가 스크롤되지 않게', () => {
    const vp = block(UPLOAD_CSS, '.pvx-b .pv-viewport {');
    expect(vp).toContain('flex: 1 1 auto');
    expect(vp).toContain('min-height: 0');
  });

  it('기존 단언은 그대로 선다 — 확대 줄의 줄바꿈 금지·「줄지 않음」', () => {
    const zoom = block(PREVIEW_CSS, '.pv-zoom {');
    expect(zoom).toContain('white-space: nowrap');
    expect(zoom).toContain('flex: none');
  });
});
