/**
 * 휴대폰·패드 대응 20260926 — L1 지도 시범 (L1a 부분).
 *
 * 오라클 = `dev-package/prd/specs/S-DEVICE-WIDTH-INPUT-20260926.md` V2 · V4(구조) · V6 · V7(미리보기 CSS)
 *          · V8(미리보기 하한 삭제) · V11(맞춤 단추) · 「레인 확정」 L1a 줄(810 상수 · 넘침 2곳).
 * 새 seam = 지도 칸 폭 시험 도우미(`helpers/mapCellWidth.ts` · 가짜 `ResizeObserver`).
 * ⚠ jsdom 은 가림을 판정하지 못한다 — 여기서는 배치(어느 묶음 안에 무엇이 있나)와 누른 결과만
 *   잰다. 가림 0% 와 탭 도달의 근거는 캡처 수치와 실기기다(spec V4).
 * ⚠ L1b 몫(끌기 축 `touch-action` · 터치 탭 좌표 · 터치 좌표 문구)은 이 파일에 아직 없다.
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

declare const process: { cwd(): string };

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

const read = (rel: string): string =>
  String(readFileSync(resolve(process.cwd(), rel), 'utf8')).replace(/\/\*[\s\S]*?\*\//g, '');
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
