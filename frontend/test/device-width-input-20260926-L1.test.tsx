/**
 * 휴대폰·패드 대응 20260926 — L1 지도 시범 (L1a 부분).
 *
 * 오라클 = `dev-package/prd/specs/S-DEVICE-WIDTH-INPUT-20260926.md` V2 · V4(구조) · V6 · V7(미리보기 CSS)
 *          · V8(미리보기 하한 삭제) · V11(맞춤 단추) · 「레인 확정」 L1a 줄(810 상수 · 넘침 2곳).
 * 새 seam = 지도 칸 폭 시험 도우미(`helpers/mapCellWidth.ts` · 가짜 `ResizeObserver`).
 * ⚠ jsdom 은 가림을 판정하지 못한다 — 여기서는 배치(어느 묶음 안에 무엇이 있나)와 누른 결과만
 *   잰다. 가림 0% 와 탭 도달의 근거는 캡처 수치와 실기기다(spec V4).
 * L1b 부분 = V5(끌기 축 속성 · CSS 대응) · V11(터치 탭 좌표 · 우려 7ⓐ) · V12 지도(입력 방식별 좌표 문구).
 *   jsdom 은 CSS 파일을 적용하지 않는다 — 계산된 `touch-action` 은 캡처 수치 · 브라우저가 재고,
 *   여기서는 끌기 축 속성 값과 원문 CSS 대응을 잰다.
 */
// @ts-expect-error — 타입 선언 없이 런타임만 쓴다(`preview-map-viewport-20260918` 와 같은 규율).
import { readFileSync, readdirSync, statSync } from 'node:fs';
// @ts-expect-error — 같은 이유.
import { join, resolve } from 'node:path';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { DatasetPreviewSection } from '../src/components/datasetpreview/DatasetPreviewSection';
import { PreviewPanel } from '../src/components/upload/PreviewPanel';
import { UnregisteredPreviewPage } from '../src/routes/UnregisteredPreviewPage';
import { PREVIEW_ROUTE_PATH, previewPath } from '../src/components/preview/handoff';
import { HUD_IDLE } from '../src/components/preview/PreviewPanels';
import { SessionProvider } from '../src/permission/session';
import type { CurrentAccount } from '../src/api/client';
import type { DatasetPreviewSource, ValueLookupResult } from '../src/components/datasetpreview/types';
import type { PreviewSource as UnregisteredSource, RenderJob } from '../src/components/preview/types';
import type { PreviewSource as UploadSource } from '../src/components/upload/types';
import { drawDatasetPreviewWhenReady, withDatasetPreviewFixture } from './datasetPreviewTest';
import { clickPreviewDrawWhenReady } from './helpers/previewDraw';
import { installMapCellWidth, stubPointer, type MapCellWidth } from './helpers/mapCellWidth';
import detailCss from '../src/components/detail/detail.css?raw';
import previewCss from '../src/components/preview/preview.css?raw';

declare const process: { cwd(): string };

/**
 * CSS 원문은 `?raw` 로 받는다 — `node:fs` 금지(`e01-apply-points.test.ts` 머리 주석 · 2026-09-02 배포 불가 사고).
 * vitest css 스텁은 허용 목록(`vite.config.ts` `test.css.include`) 밖 `?raw` 를 빈 문자열로 만든다 → 아래 「적재」 시험이 red.
 * 값 = [원문, 그 파일에 반드시 있는 선택자].
 */
const RAW_CSS: Record<string, readonly [string, string]> = {
  'src/components/preview/preview.css': [previewCss, '.pv-viewport'],
  'src/components/detail/detail.css': [detailCss, '.infogrid'],
};
const rawCss = (rel: string): string => {
  const hit = RAW_CSS[rel];
  if (!hit) throw new Error(`?raw 로 받지 않은 파일: ${rel}`);
  return hit[0];
};

describe('CSS 원문 적재 — `?raw` 가 비지 않고 알려진 선택자를 담는다(허용 목록 누락 = red)', () => {
  it.each(Object.entries(RAW_CSS))('%s', (rel, [css, known]) => {
    expect(css.length, rel).toBeGreaterThan(0);
    expect(css, rel).toContain(known);
  });
});

const DATASET_ID = '0000000000000000000000DS12';
const UPLOAD_ID = '01JYZ9K7WQ3N8V4M2X6C5B0UP2';
const RENDER_ID = '01JYZ9K7WQ3N8V4M2X6C5B0RE2';
const WAIT = { timeout: 5000 };
/** 기본 배율이 정확히 1 인 경계(#120 시험과 같은 값) — 맞춤 단추 결과를 배율 변화로 읽는다. */
const WIDE = { west: -90, south: -10, east: 90, north: 10 };
const LEGEND = {
  palette: 'viridis', unit: 'mm', variable: 'rainfall',
  classes: [{ color: '#440154', min: 0, max: 5 }],
};
const EDITOR = { permissions: { '업로드·편집': true } } as unknown as CurrentAccount;
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
    result: { imageUrl: 'https://viz.example/d/map.png', legend: LEGEND, bounds: WIDE },
  } as unknown as RenderJob;
}

let cell: MapCellWidth | undefined;
afterEach(() => {
  cell = undefined;
  vi.unstubAllGlobals();
});

/** 도우미를 심는다. 끝에서 콜백이 실제로 불렸음을 단언하는 것은 각 시험의 몫이다. */
function width(px: number): MapCellWidth {
  cell = installMapCellWidth(px);
  return cell;
}

/* ── 화면 세 곳 ─────────────────────────────────────────────────────────── */

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
  render(
    <SessionProvider account={EDITOR}>
      <DatasetPreviewSection datasetId={DATASET_ID} source={source} pollMs={5} />
    </SessionProvider>,
  );
  drawDatasetPreviewWhenReady();
  await waitFor(() => expect(screen.getByTestId('preview-map')).toBeTruthy(), WAIT);
  return { source, viewport: screen.getByTestId('preview-viewport') };
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
  await waitFor(() => expect(screen.getByTestId('up-style-palette')).toBeTruthy(), WAIT);
  await clickPreviewDrawWhenReady();
  return screen.findByTestId('up-preview-viewport');
}

async function mountUnregistered() {
  const path = previewPath(UPLOAD_ID, RENDER_ID);
  const source = {
    get: vi.fn(async () => doneJob()),
    create: vi.fn(async () => doneJob()),
    probeTile: vi.fn(async () => 'ok' as const),
  } as unknown as UnregisteredSource;
  render(
    <MemoryRouter initialEntries={[{ pathname: path.split('?')[0]!, search: path.split('?')[1] ?? '' }]}>
      <Routes>
        <Route path={PREVIEW_ROUTE_PATH} element={<UnregisteredPreviewPage source={source} pollMs={1} />} />
      </Routes>
    </MemoryRouter>,
  );
  await screen.findByTestId('preview-map', {}, WAIT);
  return screen.getByTestId('preview-viewport');
}

/** 네 도구(범례 · 값 조회 · 좌표 표시 · 스크린샷)의 선택자. */
const FOUR = '.pv-legend, .pv-value, .pv-hud, .pv-shot';

function childClasses(el: Element): string[] {
  return Array.from(el.children).map((c) => c.className.split(' ')[0] ?? '');
}

/** jsdom 은 레이아웃을 안 한다 — 값 조회 역산이 쓰는 뷰포트 상자를 준다(#120 시험과 같은 방식). */
function sizeViewport(el: Element, w: number, h: number) {
  Object.defineProperty(el, 'clientWidth', { value: w, configurable: true });
  Object.defineProperty(el, 'clientHeight', { value: h, configurable: true });
  el.getBoundingClientRect = () =>
    ({ left: 0, top: 0, width: w, height: h, right: w, bottom: h, x: 0, y: 0, toJSON: () => ({}) }) as DOMRect;
}

/** 확대 한계를 알린다 — 재기 전에는 확대가 눌리지 않는다(정본 §8 조건 ⑷ · #120 시험과 같은 방식). */
function prepareZoom(viewport: HTMLElement) {
  sizeViewport(viewport, 512, 512);
  const img = viewport.querySelector('img') as HTMLImageElement;
  Object.defineProperty(img, 'naturalWidth', { value: 4096, configurable: true });
  Object.defineProperty(img, 'naturalHeight', { value: 4096, configurable: true });
  fireEvent.load(img);
}

function scaleOf(layersTestId: string): number {
  return Number(screen.getByTestId(layersTestId).getAttribute('data-zoom-scale'));
}

/* ── CSS 원문 ───────────────────────────────────────────────────────────── */

const read = (rel: string): string => rawCss(rel).replace(/\/\*[\s\S]*?\*\//g, '');
const PREVIEW_CSS = read('src/components/preview/preview.css');
const DETAIL_CSS = read('src/components/detail/detail.css');

/** 선택자 머리가 정확히 `head` 인 규칙 블록 전부(원문 순서). 없으면 빈 배열. */
function rulesOf(css: string, head: string): Array<{ at: number; body: string }> {
  const out: Array<{ at: number; body: string }> = [];
  const re = /([^{};]+)\{([^{}]*)\}/g;
  for (let m = re.exec(css); m; m = re.exec(css)) {
    if (m[1]!.trim().replace(/\s+/g, ' ') === head) out.push({ at: m.index, body: m[2]! });
  }
  return out;
}

/** `@media <조건> {` 블록 본문 전부(중괄호 짝을 센다). */
function mediaBodies(css: string, cond: string): string[] {
  const out: string[] = [];
  const head = `@media ${cond} {`;
  for (let at = css.indexOf(head); at > -1; at = css.indexOf(head, at + 1)) {
    let depth = 0;
    const open = at + head.length - 1;
    for (let i = open; i < css.length; i += 1) {
      if (css[i] === '{') depth += 1;
      else if (css[i] === '}' && --depth === 0) {
        out.push(css.slice(open + 1, i));
        break;
      }
    }
  }
  return out;
}

/* ═══ 810 경계 상수 ═════════════════════════════════════════════════════ */

describe('지도 칸 경계 810 — spec 「지도 · 그림 위 도구 원칙」 줄과 코드 상수', () => {
  it('spec 줄의 값과 지도 칸 폭 모듈이 내보내는 상수가 같다', async () => {
    const spec = String(
      readFileSync(resolve(process.cwd(), '../dev-package/prd/specs/S-DEVICE-WIDTH-INPUT-20260926.md'), 'utf8'),
    );
    const lines = spec.split('\n').filter((l: string) => /지도 · 그림 위 도구 원칙: 지도 경계 \d+/.test(l));
    expect(lines).toHaveLength(1);
    const specValue = Number(/지도 경계 (\d+)/.exec(lines[0]!)![1]);
    expect(specValue).toBe(810);
    // 모듈을 시험 안에서 불러 이 한 사례만 모듈 부재로 실패하게 한다(파일 전체 적재 실패 방지).
    const modulePath = '../src/components/preview/useMapCellWidth';
    const mod = (await import(/* @vite-ignore */ modulePath)) as { MAP_CELL_BOUNDARY: number };
    expect(mod.MAP_CELL_BOUNDARY).toBe(specValue);
  });
});

/* ═══ V2 · V6 상세 — 지도 칸 폭에 따른 배치 ═════════════════════════════ */

describe('V2 · V6 상세 — 지도 칸 810 미만이면 네 도구가 아래 블록으로 간다(마우스 판별 상태)', () => {
  const cases: Array<[number, 'below' | 'over']> = [
    [332, 'below'], [730, 'below'], [809, 'below'], [810, 'over'], [1190, 'over'],
  ];
  it('도우미 폭 목록은 다섯 개다(332 · 730 · 1190 · 경계 809 · 810)', () => {
    expect(cases).toHaveLength(5);
  });
  for (const [px, want] of cases) {
    it(`지도 칸 ${px} → ${want === 'below' ? '아래 블록' : '지도 위'}`, async () => {
      stubPointer(false);
      const helper = width(px);
      const { viewport } = await mountDetail();
      expect(helper.calls()).toBeGreaterThanOrEqual(1);
      const overlay = screen.getByTestId('preview-overlay');
      expect(overlay.parentElement).toBe(viewport);
      expect(overlay.contains(screen.getByTestId('preview-zoom'))).toBe(true);
      expect(screen.queryByRole('button', { name: '데이터에 맞춤' })).toBeNull();
      if (want === 'below') {
        expect(overlay.querySelectorAll(FOUR)).toHaveLength(0);
        const below = screen.getByTestId('preview-below');
        // 자리: 아래 자리(지도 틀 바로 뒤 · 같은 틀 묶음 안) 안
        const place = below.parentElement!;
        expect(place.className).toBe('pv-frame-below');
        expect(place.parentElement?.className).toBe('pv-frame-wrap');
        expect(place.previousElementSibling).toBe(screen.getByTestId('dt-preview-slot'));
        // 순서: 좌표 → 값 조회 → 범례 → 스크린샷(우려 5 ⓐ)
        expect(childClasses(below)).toEqual(['pv-hud', 'pv-value', 'pv-legend', 'pv-shot']);
        expect(viewport.querySelectorAll(FOUR)).toHaveLength(0);
      } else {
        expect(screen.queryByTestId('preview-below')).toBeNull();
        expect(overlay.querySelectorAll(FOUR)).toHaveLength(4);
      }
    });
  }

  it('폭 0(모름)이면 지금 배치(#120) 그대로다', async () => {
    const helper = width(0);
    const { viewport } = await mountDetail();
    expect(helper.calls()).toBeGreaterThanOrEqual(1);
    expect(screen.queryByTestId('preview-below')).toBeNull();
    expect(viewport.querySelectorAll(FOUR)).toHaveLength(4);
  });

  it('도우미는 지도 구역에만 폭을 알린다 — 다른 관찰 대상에는 콜백이 없다', () => {
    const helper = width(332);
    const other = document.createElement('header');
    const seen: unknown[] = [];
    const ro = new ResizeObserver((entries) => seen.push(entries));
    ro.observe(other);
    expect(seen).toHaveLength(0);
    expect(helper.calls()).toBe(0);
    ro.disconnect();
  });
});

describe('V2 상세 — 아래 블록의 이벤트 경계와 값 결과', () => {
  it('아래 블록 안 누름 · 포인터 누름 · 마우스 이동은 조회 0회 · 배율 · 좌표 표시 불변', async () => {
    const helper = width(332);
    const { source } = await mountDetail();
    expect(helper.calls()).toBeGreaterThanOrEqual(1);
    const below = screen.getByTestId('preview-below');
    const hud = screen.getByTestId('preview-cursor-hud');
    const before = screen.getByTestId('preview-layers').getAttribute('style');
    expect(below.contains(hud)).toBe(true);
    for (const el of [below, hud, screen.getByTestId('value-lookup'), below.querySelector('.pv-legend')!]) {
      fireEvent.click(el, { clientX: 10, clientY: 10 });
      fireEvent.pointerDown(el, { clientX: 10, clientY: 10, button: 0 });
      fireEvent.pointerMove(window, { clientX: 10, clientY: -300 });
      fireEvent.pointerUp(window, { clientX: 10, clientY: -300 });
      fireEvent.mouseMove(el, { clientX: 20, clientY: 20 });
    }
    expect(source.lookupValue).toHaveBeenCalledTimes(0);
    expect(screen.getByTestId('preview-layers').getAttribute('style')).toBe(before);
    expect(hud.textContent).toBe(HUD_IDLE);
  });

  it('회귀 — 좁은 배치에서도 그림 누름은 조회 1회다', async () => {
    const helper = width(332);
    const { source, viewport } = await mountDetail();
    expect(helper.calls()).toBeGreaterThanOrEqual(1);
    sizeViewport(viewport, 512, 512);
    fireEvent.click(viewport, { clientX: 256, clientY: 256 });
    await waitFor(() => expect(source.lookupValue).toHaveBeenCalledTimes(1), WAIT);
  });

  it('1190 → 332 로 바꿔도 값 결과가 남고 값 조회 알림 영역은 1개다 · 범례는 한 곳', async () => {
    const helper = width(1190);
    const { viewport } = await mountDetail();
    sizeViewport(viewport, 512, 512);
    fireEvent.click(viewport, { clientX: 256, clientY: 256 });
    await screen.findByTestId('value-lookup-value', {}, WAIT);
    expect(screen.queryByTestId('preview-below')).toBeNull();

    helper.setWidth(332);
    expect(helper.calls()).toBeGreaterThanOrEqual(2);
    const below = screen.getByTestId('preview-below');
    expect(document.querySelectorAll('[data-testid=value-lookup][aria-live]')).toHaveLength(1);
    expect(below.contains(screen.getByTestId('value-lookup'))).toBe(true);
    expect(screen.getByTestId('value-lookup-value').textContent).toBe('12.5 mm');
    expect(screen.getAllByLabelText('범례')).toHaveLength(1);

    helper.setWidth(1190);
    expect(screen.queryByTestId('preview-below')).toBeNull();
    expect(screen.getByTestId('value-lookup-value').textContent).toBe('12.5 mm');
  });
});

/* ═══ V2 미등록 — 지도 구역 바로 뒤 형제 블록 ═══════════════════════════ */

describe('V2 미등록 미리보기 — 아래 블록은 지도 구역 바로 뒤 형제다', () => {
  it('지도 칸 332 → 좌표 · 범례가 지도 구역 뒤 블록에 · 도구 층은 비어 있다', async () => {
    const helper = width(332);
    const viewport = await mountUnregistered();
    expect(helper.calls()).toBeGreaterThanOrEqual(1);
    const map = screen.getByTestId('preview-map');
    const below = screen.getByTestId('preview-below');
    expect(map.nextElementSibling).toBe(below);
    expect(childClasses(below)).toEqual(['pv-hud', 'pv-legend']);
    const overlay = screen.getByTestId('preview-overlay');
    expect(overlay.parentElement).toBe(viewport);
    expect(overlay.children).toHaveLength(0);
  });

  it('지도 칸 1190 → 지금 배치', async () => {
    const helper = width(1190);
    const viewport = await mountUnregistered();
    expect(helper.calls()).toBeGreaterThanOrEqual(1);
    expect(screen.queryByTestId('preview-below')).toBeNull();
    expect(viewport.querySelectorAll('.pv-legend, .pv-hud')).toHaveLength(2);
  });
});

/* ═══ V4 구조 · V11 맞춤 단추 — 입력 방식 ═══════════════════════════════ */

describe('V4 · V11 터치 — 도구 층에는 확대 묶음과 맞춤 단추만 · 누르면 배율 1', () => {
  it('상세 332 터치 — 도구 층 안은 확대 묶음과 맞춤 단추뿐이다 · 누르면 배율이 1이 된다', async () => {
    const pointer = stubPointer(true);
    const helper = width(332);
    const { viewport } = await mountDetail();
    expect(helper.calls()).toBeGreaterThanOrEqual(1);
    expect(pointer.queries).toContain('(pointer: coarse)');
    prepareZoom(viewport);
    const overlay = screen.getByTestId('preview-overlay');
    expect(overlay.querySelectorAll(FOUR)).toHaveLength(0);
    const fit = screen.getByRole('button', { name: '데이터에 맞춤' });
    expect(overlay.contains(fit)).toBe(true);
    // 3단추 줄 밖 · 같은 모서리
    expect(screen.getByTestId('preview-zoom').contains(fit)).toBe(false);
    const corner = fit.closest('.pv-overlay-br');
    expect(corner?.contains(screen.getByTestId('preview-zoom'))).toBe(true);
    expect(new Set(childClasses(corner!))).toEqual(new Set(['pv-fit', 'pv-zoom']));
    // 순서: 맞춤 단추가 확대 줄 앞(모서리 위쪽) — 좁은 지도에서 확대 줄이 지도 가운데까지 올라가지 않게(L1a 결정)
    expect(childClasses(corner!)).toEqual(['pv-fit', 'pv-zoom']);

    fireEvent.click(screen.getByRole('button', { name: '확대' }));
    expect(scaleOf('preview-layers')).toBe(2);
    fireEvent.click(fit);
    expect(scaleOf('preview-layers')).toBe(1);
  });

  it('업로드 인라인 · 확장보기 터치 — 맞춤 단추가 도구 층에 있고 누르면 배율 1', async () => {
    stubPointer(true);
    const viewport = await mountUpload();
    await screen.findByTestId('up-preview-zoom');
    const inline = screen.getByTestId('up-preview-overlay');
    const fitInline = Array.from(inline.querySelectorAll('button')).find((b) => b.textContent === '데이터에 맞춤');
    expect(fitInline, '인라인 도구 층에 맞춤 단추가 없다').toBeTruthy();
    expect(viewport.contains(fitInline!)).toBe(true);
    prepareZoom(viewport);
    fireEvent.click(Array.from(inline.querySelectorAll('button')).find((b) => b.textContent === '확대')!);
    expect(scaleOf('up-preview-layers')).toBeGreaterThan(1);
    fireEvent.click(fitInline!);
    expect(scaleOf('up-preview-layers')).toBe(1);

    fireEvent.click(screen.getByTestId('pv-expand'));
    prepareZoom(await screen.findByTestId('pv-expand-viewport'));
    const tools = screen.getByTestId('pv-expand-tools');
    const fitExpand = Array.from(tools.querySelectorAll('button')).find((b) => b.textContent === '데이터에 맞춤');
    expect(fitExpand, '확장보기 도구 층에 맞춤 단추가 없다').toBeTruthy();
    fireEvent.click(Array.from(tools.querySelectorAll('button')).find((b) => b.textContent === '확대')!);
    expect(scaleOf('pv-expand-layers')).toBeGreaterThan(1);
    fireEvent.click(fitExpand!);
    expect(scaleOf('pv-expand-layers')).toBe(1);
  });

  it('마우스 판별 · 판별 불가(매체 질의 없음)에서는 맞춤 단추가 없다', async () => {
    const pointer = stubPointer(false);
    await mountDetail();
    expect(pointer.queries).toContain('(pointer: coarse)');
    expect(screen.queryByRole('button', { name: '데이터에 맞춤' })).toBeNull();
  });

  it('판별 불가(매체 질의 없음)는 마우스다', async () => {
    vi.stubGlobal('matchMedia', undefined);
    await mountDetail();
    expect(screen.getByTestId('preview-zoom')).toBeTruthy();
    expect(screen.queryByRole('button', { name: '데이터에 맞춤' })).toBeNull();
  });

  it('미등록(확대 없는 지도)에는 터치에서도 맞춤 단추가 없다', async () => {
    stubPointer(true);
    await mountUnregistered();
    expect(screen.getByTestId('preview-overlay')).toBeTruthy();
    expect(screen.queryByRole('button', { name: '데이터에 맞춤' })).toBeNull();
  });

  it('TSX 의 입력 매체 조건 문자열은 입력 방식 훅 한 곳에만 있다', () => {
    const hits: string[] = [];
    const walk = (dir: string) => {
      for (const name of readdirSync(dir) as string[]) {
        const p = join(dir, name);
        if (statSync(p).isDirectory()) walk(p);
        else if (/\.(tsx?|jsx?)$/.test(name) && /\((any-)?(pointer|hover)\s*:/.test(String(readFileSync(p, 'utf8'))))
          hits.push(p.slice(p.indexOf('src/')));
      }
    };
    walk(resolve(process.cwd(), 'src'));
    expect(hits).toEqual(['src/components/common/useInputMode.ts']);
  });
});

/* ═══ CSS — 맞춤 단추 · 아래 블록 · 터치 44 · 16 하한 · 넘침 ═══════════════ */

describe('CSS 원문 — L1a 새 규칙은 기존 고정 블록 뒤에 있다', () => {
  const toolsAt = PREVIEW_CSS.indexOf('.pv-overlay .pv-zoom,');

  it('맞춤 단추 감싸개가 도구 층 누름 받기 규칙과 확대 묶음과 같은 면 · 테두리 · 모서리 토큰을 갖는다', () => {
    const rules = rulesOf(PREVIEW_CSS, '.pv-overlay .pv-fit');
    expect(rules).toHaveLength(1);
    const { at, body } = rules[0]!;
    expect(toolsAt).toBeGreaterThan(-1);
    expect(at).toBeGreaterThan(toolsAt);
    expect(body).toContain('pointer-events: auto');
    expect(body).toContain('background: var(--color-surface)');
    expect(body).toContain('border: 1px solid var(--color-border)');
    expect(body).toContain('border-radius: var(--radius-sm)');
    expect(body).toContain('box-shadow: none');
  });

  it('아래 블록은 세로 묶음 · 여백 토큰 간격 · 자식 바깥 여백 0 · 도구 층과 같은 면 토큰 · 그림자 0', () => {
    const block = rulesOf(PREVIEW_CSS, '.pv-below');
    expect(block).toHaveLength(1);
    expect(block[0]!.at).toBeGreaterThan(toolsAt);
    expect(block[0]!.body).toContain('flex-direction: column');
    expect(block[0]!.body).toMatch(/gap: var\(--space-\d\)/);
    const kids = rulesOf(PREVIEW_CSS, '.pv-below > *');
    expect(kids).toHaveLength(1);
    expect(kids[0]!.body).toContain('margin: 0');
    const face = rulesOf(PREVIEW_CSS, '.pv-below :is(.pv-hud, .pv-value, .pv-legend, .pv-shot)');
    expect(face).toHaveLength(1);
    for (const d of ['background: var(--color-surface)', 'border: 1px solid var(--color-border)',
      'border-radius: var(--radius-sm)', 'box-shadow: none']) expect(face[0]!.body).toContain(d);
    // 미등록(틀 묶음 gap 이 없는 자리)에서도 지도 구역과 아래 블록 사이가 여백 토큰 한 칸이다
    const sibling = rulesOf(PREVIEW_CSS, '.pv-map + .pv-below');
    expect(sibling).toHaveLength(1);
    expect(sibling[0]!.body).toContain('margin-top: var(--space-2)');
    // 도구 층 전용 범례 최대 높이는 아래 블록에 걸지 않는다
    expect(PREVIEW_CSS).not.toMatch(/\.pv-below[^{]*\{[^}]*max-height/);
  });

  it('긴 이름 줄바꿈은 아래 블록 범위에만 · 지도 위 범례 규칙은 그대로', () => {
    const wrap = rulesOf(PREVIEW_CSS, '.pv-below :is(.pv-legend-row dd, .pv-value-body dd)');
    expect(wrap).toHaveLength(1);
    expect(wrap[0]!.body).toContain('overflow-wrap: anywhere');
    expect(wrap[0]!.body).toContain('min-width: 0');
    expect(rulesOf(PREVIEW_CSS, '.pv-overlay .pv-legend')[0]!.body).not.toContain('overflow-wrap');
  });

  it('아래 자리는 비어 있으면 그려지지 않는다(묶음 간격 8px 없음)', () => {
    const empty = rulesOf(PREVIEW_CSS, '.pv-frame-below:empty');
    expect(empty).toHaveLength(1);
    expect(empty[0]!.body).toContain('display: none');
  });

  it('부록 B 레인 L1 대상(3항목)이 터치 블록 하나에서 최소 높이 · 가로 44 토큰을 갖는다', () => {
    const targets = JSON.parse(
      String(readFileSync(resolve(process.cwd(), 'scripts/visual-baseline/targets.json'), 'utf8')),
    ).targets.filter((t: { lane: string }) => t.lane === 'L1') as Array<{ n: number; selector: string }>;
    expect(targets.map((t) => t.n)).toEqual([23, 29, 30]);
    const touch = mediaBodies(PREVIEW_CSS, '(pointer: coarse)');
    expect(touch).toHaveLength(1);
    expect(PREVIEW_CSS.indexOf('@media (pointer: coarse) {')).toBeGreaterThan(PREVIEW_CSS.indexOf('@media (max-width: 640px) {'));
    const rule = /([^{}]+)\{([^{}]*)\}/.exec(touch[0]!)!;
    const selectors = rule[1]!.split(',').map((s) => s.trim());
    for (const t of targets) {
      for (const sel of t.selector.split(',').map((s) => s.trim())) {
        expect(selectors, `터치 블록에 대상 ${t.n} 선택자 ${sel} 가 없다`).toContain(sel);
      }
    }
    expect(rule[2]).toContain('min-height: var(--control-height)');
    expect(rule[2]).toContain('min-width: var(--control-height)');
  });

  it('부록 G 미리보기 16px 하한(`.pv-control select`)이 지워졌고 640 블록의 나머지 규칙은 남는다', () => {
    const narrow = mediaBodies(PREVIEW_CSS, '(max-width: 640px)');
    expect(narrow).toHaveLength(1);
    expect(narrow[0]).not.toMatch(/font-size:\s*16px/);
    expect(narrow[0]).toContain('.pv-basic-grid { grid-template-columns: minmax(0, 1fr); }');
    expect(narrow[0]).toContain(':is(.pv-zoom, .pv-shot, .lin) button { min-height: 44px; }');
    expect(PREVIEW_CSS).not.toMatch(/font-size:\s*16px/);
  });

  it('새 지도 장면 넘침 2곳 — 파일 경로 두 줄이 줄바꿈한다(기존 블록 뒤)', () => {
    const target = rulesOf(PREVIEW_CSS, '.dt-preview > .pv-muted');
    expect(target).toHaveLength(1);
    expect(target[0]!.body).toContain('overflow-wrap: anywhere');
    const dh = rulesOf(DETAIL_CSS, '.detail-page .dh-file');
    expect(dh).toHaveLength(2);
    expect(dh[0]!.body).not.toContain('overflow-wrap');
    expect(dh[1]!.body.trim()).toBe('overflow-wrap: anywhere;');
  });
});

/* ═══ L1b · V5 끌기 축 — 끌 범위가 있는 축에서만 지도가 움직인다 ═══════════ */

/** 작은 유역 경계 — 기본 배율이 1 보다 작아 「데이터에 맞춤」(배율 1)이 확대가 된다. */
const SMALL = { west: 126, south: 36, east: 127, north: 37 };

function detailSourceWith(bounds: typeof WIDE): DatasetPreviewSource {
  const job = () =>
    ({ ...doneJob(), result: { ...doneJob().result, bounds } }) as unknown as RenderJob;
  return withDatasetPreviewFixture({
    palettes: vi.fn(async () => [{ palette: 'viridis' }]),
    create: vi.fn(async () => job()),
    get: vi.fn(async () => job()),
    probeTile: vi.fn(async () => 'ok' as const),
    mapGeometry: vi.fn(async () => undefined),
    screenshot: vi.fn(async () => new Blob()),
    lookupValue: vi.fn(async () => HIT),
  } as unknown as DatasetPreviewSource);
}

/** 내용 상자(층 묶음 배치 크기)를 심는다 — design-fix 20260924 L3 의 `sizeContent` 와 같은 방식. */
function sizeContent(el: Element, w: number, h: number) {
  Object.defineProperty(el, 'offsetWidth', { value: w, configurable: true });
  Object.defineProperty(el, 'offsetHeight', { value: h, configurable: true });
}

/** 뷰포트 512 × 512 · 내용 w × h 를 심고 그림 적재로 한 번 다시 그리게 한다(창 크기 변화와 같은 경로). */
function plant(viewport: HTMLElement, layers: HTMLElement, w: number, h: number) {
  sizeViewport(viewport, 512, 512);
  sizeContent(layers, w, h);
  const img = viewport.querySelector('img') as HTMLImageElement;
  Object.defineProperty(img, 'naturalWidth', { value: 4096, configurable: true });
  fireEvent.load(img);
}

const axisOf = (el: HTMLElement) => el.getAttribute('data-drag-axis');

describe('V5 끌기 축 — 상세 지도(기본 배율 · 끌 범위별 · 확대)', () => {
  const cases: Array<[string, number, number, string]> = [
    ['두 축 끌 범위 0', 512, 512, 'none'],
    ['세로만 끌 범위(세로로 긴 그림)', 512, 1600, 'y'],
    ['가로만 끌 범위', 1600, 512, 'x'],
    ['두 축 끌 범위', 1600, 1600, 'both'],
  ];
  it('사례 목록은 네 개다(없음 · 세로 · 가로 · 둘 다)', () => {
    expect(cases).toHaveLength(4);
  });
  for (const [name, w, h, want] of cases) {
    it(`기본 배율 · ${name} → ${want}`, async () => {
      const { viewport } = await mountDetail();
      plant(viewport, screen.getByTestId('preview-layers'), w, h);
      expect(scaleOf('preview-layers')).toBe(1);
      await waitFor(() => expect(axisOf(viewport)).toBe(want), WAIT);
    });
  }

  it('확대(배율 > 기본 배율) → 둘 다 · 기본 배율로 돌아오면 다시 없음', async () => {
    const { viewport } = await mountDetail();
    plant(viewport, screen.getByTestId('preview-layers'), 512, 512);
    await waitFor(() => expect(axisOf(viewport)).toBe('none'), WAIT);
    fireEvent.click(screen.getByRole('button', { name: '확대' }));
    expect(scaleOf('preview-layers')).toBe(2);
    expect(axisOf(viewport)).toBe('both');
    fireEvent.click(screen.getByRole('button', { name: '기본 배율로' }));
    expect(scaleOf('preview-layers')).toBe(1);
    expect(axisOf(viewport)).toBe('none');
  });

  it('「데이터에 맞춤」이 확대일 때(기본 배율 < 1) → 둘 다', async () => {
    stubPointer(true);
    const { viewport } = await mountDetail(detailSourceWith(SMALL));
    plant(viewport, screen.getByTestId('preview-layers'), 512, 512);
    const base = Number(screen.getByTestId('preview-layers').getAttribute('data-zoom-base-scale'));
    expect(base).toBeLessThan(1);
    await waitFor(() => expect(axisOf(viewport)).toBe('none'), WAIT);
    fireEvent.click(screen.getByRole('button', { name: '데이터에 맞춤' }));
    expect(scaleOf('preview-layers')).toBe(1);
    expect(axisOf(viewport)).toBe('both');
  });
});

describe('V5 끌기 축 — 업로드 인라인 · 확장보기에도 같은 속성 · 미등록에는 없다', () => {
  it('업로드 인라인 · 확장보기 — 세로로 긴 그림 기본 배율 → 세로', async () => {
    const viewport = await mountUpload();
    await screen.findByTestId('up-preview-zoom');
    plant(viewport, screen.getByTestId('up-preview-layers'), 512, 1600);
    await waitFor(() => expect(axisOf(viewport)).toBe('y'), WAIT);

    fireEvent.click(screen.getByTestId('pv-expand'));
    const expand = await screen.findByTestId('pv-expand-viewport');
    plant(expand, screen.getByTestId('pv-expand-layers'), 512, 1600);
    await waitFor(() => expect(axisOf(expand)).toBe('y'), WAIT);
  });

  it('미등록(확대 없는 지도) — 속성이 없다(페이지가 늘 스크롤)', async () => {
    stubPointer(true);
    const viewport = await mountUnregistered();
    expect(viewport.hasAttribute('data-drag-axis')).toBe(false);
  });
});

describe('V5 CSS 원문 — 뷰포트 기본값은 페이지 스크롤 · 축 속성마다 touch-action', () => {
  it('`.pv-viewport {` 첫 블록은 `touch-action: pan-x pan-y` 이고 `position: relative` 가 그대로 있다', () => {
    const first = rulesOf(PREVIEW_CSS, '.pv-viewport')[0];
    expect(first, '.pv-viewport 블록이 없다').toBeTruthy();
    expect(first!.body).toMatch(/touch-action:\s*pan-x pan-y;/);
    expect(first!.body).not.toMatch(/touch-action:\s*none/);
    expect(first!.body).toContain('position: relative');
  });

  const MAP: Array<[string, string]> = [
    ['none', 'pan-x pan-y'],
    ['y', 'pan-x'],
    ['x', 'pan-y'],
    ['both', 'none'],
  ];
  it('대응표는 네 줄이다(spec 「구현 결정」 끌기 축 표)', () => {
    expect(MAP).toHaveLength(4);
  });
  for (const [axis, action] of MAP) {
    it(`[data-drag-axis='${axis}'] → touch-action: ${action} · 기본 블록 뒤`, () => {
      const rules = rulesOf(PREVIEW_CSS, `.pv-viewport[data-drag-axis='${axis}']`);
      expect(rules).toHaveLength(1);
      expect(rules[0]!.at).toBeGreaterThan(PREVIEW_CSS.indexOf('.pv-viewport {'));
      expect(rules[0]!.body.trim()).toBe(`touch-action: ${action};`);
    });
  }
});

/* ═══ L1b · V11 터치 탭 좌표 · V12 지도 문구 ═══════════════════════════════ */

const TOUCH_IDLE = '지도를 누르면 그 자리 좌표를 보여 줘요';

/** 터치 탭 — 포인터 누름 · 놓기 ＋ click. 마우스 이동(`mousemove`)은 보내지 않는다. */
function tap(viewport: HTMLElement, x: number, y: number) {
  fireEvent.pointerDown(viewport, { pointerId: 7, pointerType: 'touch', clientX: x, clientY: y, button: 0 });
  fireEvent.pointerUp(window, { pointerId: 7, pointerType: 'touch', clientX: x, clientY: y });
  fireEvent.click(viewport, { clientX: x, clientY: y });
}

/** 512 × 512 뷰포트의 (128, 384) = 가로 1/4 · 세로 3/4 → WIDE 경계에서 경도 −45 · 위도 −5. */
const TAPPED = '역산값 · 위도 -5.0000 · 경도 -45.0000';

describe('V11 · 우려 7ⓐ 터치 탭 좌표 — 상세 · 미등록 둘 다', () => {
  it('상세 터치 — 탭한 점의 위도 · 경도가 좌표 표시에 나오고 값 조회도 1회 일어난다', async () => {
    stubPointer(true);
    const { source, viewport } = await mountDetail();
    sizeViewport(viewport, 512, 512);
    const hud = screen.getByTestId('preview-cursor-hud');
    expect(hud.textContent).toBe(TOUCH_IDLE);
    tap(viewport, 128, 384);
    expect(hud.textContent).toBe(TAPPED);
    await waitFor(() => expect(source.lookupValue).toHaveBeenCalledTimes(1), WAIT);
  });

  it('미등록 터치 — 탭한 점의 위도 · 경도가 좌표 표시에 나온다(값 조회 없음)', async () => {
    stubPointer(true);
    const viewport = await mountUnregistered();
    sizeViewport(viewport, 512, 512);
    const hud = screen.getByTestId('preview-cursor-hud');
    expect(hud.textContent).toBe(TOUCH_IDLE);
    tap(viewport, 128, 384);
    expect(hud.textContent).toBe(TAPPED);
    expect(viewport.hasAttribute('data-value-lookup')).toBe(false);
  });

  it('미등록 터치 — 경계 밖 탭은 좌표를 지어내지 않는다(「지도 밖」)', async () => {
    stubPointer(true);
    const viewport = await mountUnregistered();
    sizeViewport(viewport, 512, 512);
    tap(viewport, 600, 384);
    expect(screen.getByTestId('preview-cursor-hud').textContent).toBe('지도 밖');
  });

  it('마우스 — 누름만으로는 좌표 표시가 바뀌지 않는다(마우스 이동 표시 그대로)', async () => {
    stubPointer(false);
    const viewport = await mountUnregistered();
    sizeViewport(viewport, 512, 512);
    const hud = screen.getByTestId('preview-cursor-hud');
    fireEvent.click(viewport, { clientX: 128, clientY: 384 });
    expect(hud.textContent).toBe(HUD_IDLE);
    fireEvent.mouseMove(viewport, { clientX: 128, clientY: 384 });
    expect(hud.textContent).toBe(TAPPED);
  });
});

describe('V12 지도 문구 — 입력 방식 스텁 두 갈래', () => {
  it('터치 — 좌표 표시 대기 문구가 새 문구다(상세 · 미등록)', async () => {
    stubPointer(true);
    await mountDetail();
    expect(screen.getByTestId('preview-cursor-hud').textContent).toBe(TOUCH_IDLE);
  });

  it('미등록 터치도 같은 새 문구다', async () => {
    stubPointer(true);
    await mountUnregistered();
    expect(screen.getByTestId('preview-cursor-hud').textContent).toBe(TOUCH_IDLE);
  });

  it('마우스 · 판별 불가 — 기존 문구 그대로', async () => {
    const pointer = stubPointer(false);
    await mountDetail();
    expect(pointer.queries).toContain('(pointer: coarse)');
    expect(screen.getByTestId('preview-cursor-hud').textContent).toBe(HUD_IDLE);
    expect(HUD_IDLE).toBe('커서를 지도 위로');
  });

  it('새 터치 문구는 마우스 문구 상수 바로 옆의 이름 붙은 상수다', () => {
    const src = String(readFileSync(resolve(process.cwd(), 'src/components/preview/PreviewPanels.tsx'), 'utf8'));
    const idle = src.indexOf("export const HUD_IDLE = '커서를 지도 위로';");
    const touch = src.indexOf(`export const HUD_IDLE_TOUCH = '${TOUCH_IDLE}';`);
    expect(idle).toBeGreaterThan(-1);
    expect(touch).toBeGreaterThan(idle);
    expect(src.slice(idle, touch).split('\n').length).toBeLessThanOrEqual(4);
  });
});
