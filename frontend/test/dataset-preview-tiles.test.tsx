/**
 * S-05 데이터셋 상세 미리보기 — **지도 화면을 타일 방식으로** (WU-P3 · `#48` · Ted 판정 ⑩).
 *
 * 오라클 둘, **둘 다 정본과 계약이다 — 추정으로 쓰지 않는다.**
 *  · 정본 `E-03_데이터셋_상세/documents/Policy_데이터셋_상세.md` **v2.6** `§8`
 *    ─ `확대·이동` 행 축자 「**확대해도 렌더를 다시 걸지 않는다** — 이미 그린 결과 안에서
 *      **그 배율에 맞는 촘촘함으로 바꿔 끼운다**」 ← 타일이 하는 일 그 자체다
 *    ─ 「확대(줌) … 무엇이 되면 된 것인가」 **일곱 조건** (전부 충족해야 닫는다)
 *  · 계약 `contracts/seams/core-viz.yaml#RenderResult`
 *    ─ `tileUrlTemplate` = 「지도 위젯이 그대로 쓰는 타일 URL 틀(`{z}`·`{x}`·`{y}` 치환)」
 *    ─ `oneOf` 택일 · `dependentRequired: {tileUrlTemplate: [bounds]}`
 *
 * ⚠ **조건 ⑶ 을 정본 문면대로 판정한다.** 타일은 조각을 더 받으므로 요청 수는 늘어난다.
 * 정본이 금지한 것은 **렌더를 다시 거는 것**이고 판정도 「확대 조작 중 **새 렌더 작업 생성**
 * 0건」이다 — 즉 **사용자 조작이 서버 렌더를 다시 트리거하지 않는다**. 조각을 받아 오는
 * 것은 「이미 그린 결과 안에서」 일어나는 일이라 그 금지에 걸리지 않는다.
 *
 * ⚠ **재지 않은 것을 잰 것처럼 적지 않는다** — jsdom 이라 실제 그림 프레임은 여기서
 * 판정하지 않는다(그 축은 Ted 의 직접 확인 · `〈234〉`).
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { DatasetDetailPage } from '../src/routes/DatasetDetailPage';
import { fixtureDetailSource } from '../src/components/detail/fixture';
import type { RenderJob } from '../src/components/preview/types';
import type { DatasetPreviewSource } from '../src/components/datasetpreview/types';

const OPEN_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA1';
const RENDER_ID = '01JYZ9K7WQ3N8V4M2X6C5B0RE9';

/** `〈68〉` — 템플릿은 **불투명 문자열**이다. 질의부(서명)를 떼거나 다시 조립하지 않는다. */
const TEMPLATE =
  'https://viz.example/viz/v1/renders/R/tiles/{z}/{x}/{y}.png?exp=99&sig=abc';

const LEGEND = {
  palette: 'viridis',
  unit: 'mm',
  classes: [
    { color: '#440154', min: 0, max: 5 },
    { color: '#21918c', min: 5, max: 10 },
  ],
};

/** 서버가 실제로 내는 **타일 갈래** 결과 — `imageUrl` 이 없고 `tileUrlTemplate` 이 있다. */
const DONE: RenderJob = {
  renderId: RENDER_ID,
  status: '완료',
  result: {
    tileUrlTemplate: TEMPLATE,
    sidecarUrl: 'https://viz.example/p/map.json',
    worldFileUrl: 'https://viz.example/p/map.pgw',
    thumbnailUrl: 'https://viz.example/p/thumb.webp',
    valuePreviewUrl: 'https://viz.example/p/detail.png',
    legend: LEGEND,
    bounds: { west: 126, south: 34, east: 130, north: 38 },
  },
} as unknown as RenderJob;

/**
 * 원본 해상도는 **사이드카가 말한다** — ③지도형의 동반 JSON 이 `width`·`height` 를 담고
 * 그 URL 이 결과에 이미 실려 있다(`PREVIEW-IMPLEMENTATION §3.3` · 계약 `sidecarUrl`).
 * **화면이 지어내지 않는다**(조건 ⑷).
 */
function makeSource(over: Partial<DatasetPreviewSource> = {}): DatasetPreviewSource {
  return {
    palettes: vi.fn(async () => [{ palette: 'viridis' }]),
    create: vi.fn(async () => DONE),
    get: vi.fn(async () => DONE),
    probeTile: vi.fn(async () => 'ok' as const),
    screenshot: vi.fn(async () => new Blob([new Uint8Array([1])], { type: 'image/png' })),
    mapGeometry: vi.fn(async () => ({ width: 4096, height: 4096 })),
    ...over,
  };
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

/** jsdom 은 배치를 재지 않는다 — 화면 크기를 심고 사이드카가 도착하기를 기다린다. */
async function drawnMap(boxPx = 512) {
  await screen.findByTestId('preview-map');
  const viewport = screen.getByTestId('preview-viewport');
  Object.defineProperty(viewport, 'clientWidth', { value: boxPx, configurable: true });
  Object.defineProperty(viewport, 'clientHeight', { value: boxPx, configurable: true });
  // 크기를 심은 사실을 알린다 — 실화면은 배치가 끝나면 스스로 이 값을 갖는다
  fireEvent(window, new Event('resize'));
  // 원본 해상도 4096 / 화면 512 = **한계 배율 8**
  await waitFor(() => expect(maxScaleOf()).toBe(8));
  await waitFor(() => expect(levelOf()).not.toBeNaN());
  return viewport;
}

function layers() {
  return screen.getByTestId('preview-layers');
}
function scaleOf(): number {
  return Number(layers().getAttribute('data-zoom-scale'));
}
function maxScaleOf(): number {
  return Number(layers().getAttribute('data-zoom-max-scale'));
}
function levelOf(): number {
  return Number(layers().getAttribute('data-tile-level'));
}
function tiles(): HTMLImageElement[] {
  return screen.queryAllByTestId('preview-tile') as HTMLImageElement[];
}

describe('타일 전환 — 지도 표면이 단일 PNG 가 아니라 타일 조각이다', () => {
  it('결과의 `tileUrlTemplate` 로 조각을 세운다 — 치환은 `{z}`·`{x}`·`{y}` 셋뿐이다', async () => {
    renderDetail(makeSource());
    await drawnMap();
    const src = tiles().map((t) => t.getAttribute('src') ?? '');
    expect(src.length).toBeGreaterThan(0);
    for (const s of src) {
      expect(s).not.toContain('{');
      // 서명 질의부는 **한 글자도 건드리지 않는다**(`〈68〉`)
      expect(s).toContain('?exp=99&sig=abc');
      expect(s).toMatch(/\/tiles\/\d+\/\d+\/\d+\.png/);
    }
    // 단일 이미지 표면이 남아 있지 않다 — 갈아끼움이다
    expect(screen.queryByTestId('preview-single-image')).toBeNull();
  });

  it('타일 갈래임을 화면이 표시한다 — 템플릿은 그대로 들고 있다', async () => {
    renderDetail(makeSource());
    await drawnMap();
    expect(screen.getByTestId('preview-map').getAttribute('data-tile-template')).toBe(TEMPLATE);
  });
});

describe('§8 확대 조건 ⑴ — 그린 뒤 확대·축소·이동이 된다', () => {
  it('확대·축소가 배율을 올리고 되돌린다 — 기본 배율 아래로는 내려가지 않는다', async () => {
    renderDetail(makeSource());
    await drawnMap();
    fireEvent.click(screen.getByRole('button', { name: '확대' }));
    expect(scaleOf()).toBe(2);
    fireEvent.click(screen.getByRole('button', { name: '축소' }));
    expect(scaleOf()).toBe(1);
    fireEvent.click(screen.getByRole('button', { name: '축소' }));
    expect(scaleOf()).toBe(1);
  });

  it('끌어 옮기면 보는 자리가 움직인다', async () => {
    renderDetail(makeSource());
    const viewport = await drawnMap();
    fireEvent.click(screen.getByRole('button', { name: '확대' }));
    const before = layers().style.transform;
    fireEvent.mouseDown(viewport, { clientX: 300, clientY: 300 });
    fireEvent.mouseMove(window, { clientX: 260, clientY: 300 });
    fireEvent.mouseUp(window);
    // 확대 뒤 중심을 잡느라 이미 이동해 있다 — **움직인 만큼**을 본다
    expect(layers().style.transform).not.toBe(before);
    expect(layers().style.transform).toContain('translate(-296px, -256px)');
  });
});

describe('§8 확대 조건 ⑵ — 값·팔레트·구간 수 설정과 범례가 바뀌지 않는다', () => {
  it('확대 전후 범례가 같고, 범례는 확대되는 층 묶음 **밖**에 있다', async () => {
    renderDetail(makeSource());
    await drawnMap();
    const before = screen.getByLabelText('범례').textContent;
    fireEvent.click(screen.getByRole('button', { name: '확대' }));
    expect(screen.getByLabelText('범례').textContent).toBe(before);
    expect(layers().contains(screen.getByLabelText('범례'))).toBe(false);
  });
});

describe('§8 확대 조건 ⑶ — 확대 조작 중 새 렌더 작업 생성 0건', () => {
  it('조각을 더 받아도 **렌더**를 다시 걸지 않는다 — 사용자 조작이 서버 렌더를 트리거하지 않는다', async () => {
    const source = makeSource();
    renderDetail(source);
    const viewport = await drawnMap();
    const 시작 = vi.mocked(source.create).mock.calls.length;

    for (let i = 0; i < 6; i += 1) {
      fireEvent.click(screen.getByRole('button', { name: '확대' }));
      fireEvent.wheel(viewport, { deltaY: 120 });
    }
    fireEvent.click(screen.getByRole('button', { name: '기본 배율로' }));

    expect(vi.mocked(source.create).mock.calls.length - 시작).toBe(0);
    expect(vi.mocked(source.get).mock.calls.length).toBeLessThanOrEqual(1);
    // 원본 해상도도 다시 묻지 않는다 — 결과 한 건에 한 번이다
    expect(vi.mocked(source.mapGeometry).mock.calls.length).toBeLessThanOrEqual(1);
  });

  it('배율이 오르면 **더 촘촘한 레벨**의 조각으로 바꿔 끼운다 (정본 축자)', async () => {
    renderDetail(makeSource());
    await drawnMap();
    const base = levelOf();
    fireEvent.click(screen.getByRole('button', { name: '확대' }));
    expect(levelOf()).toBe(base + 1);
    fireEvent.click(screen.getByRole('button', { name: '확대' }));
    expect(levelOf()).toBe(base + 2);
    fireEvent.click(screen.getByRole('button', { name: '기본 배율로' }));
    expect(levelOf()).toBe(base);
  });
});

describe('§8 확대 조건 ⑷ — 데이터가 가진 해상도가 한계다', () => {
  it('한계 배율을 넘어 들어가지 않는다 — 없는 값을 만들어 그리지 않는다', async () => {
    renderDetail(makeSource());
    await drawnMap();
    for (let i = 0; i < 8; i += 1)
      fireEvent.click(screen.getByRole('button', { name: '확대' }));
    expect(scaleOf()).toBe(8);
  });

  it('한계에 닿으면 「원본 해상도까지 봤어요」를 알린다', async () => {
    renderDetail(makeSource());
    await drawnMap();
    expect(screen.queryByTestId('zoom-limit')).toBeNull();
    for (let i = 0; i < 8; i += 1)
      fireEvent.click(screen.getByRole('button', { name: '확대' }));
    expect(screen.getByTestId('zoom-limit').textContent).toContain('원본 해상도까지 봤어요');
  });

  it('원본 해상도를 아직 모르면 확대하지 않는다 — 한계를 지어내지 않는다', async () => {
    const 안옴 = new Promise<never>(() => {});
    renderDetail(makeSource({ mapGeometry: vi.fn(() => 안옴 as never) }));
    await screen.findByTestId('preview-map');
    const viewport = screen.getByTestId('preview-viewport');
    Object.defineProperty(viewport, 'clientWidth', { value: 512, configurable: true });
    Object.defineProperty(viewport, 'clientHeight', { value: 512, configurable: true });
    fireEvent(window, new Event('resize'));
    fireEvent.click(screen.getByRole('button', { name: '확대' }));
    expect(scaleOf()).toBe(1);
    expect(screen.queryByTestId('zoom-limit')).toBeNull();
    // 조각도 세우지 않는다 — 레벨을 지어내야 세울 수 있다
    expect(tiles()).toHaveLength(0);
  });
});

describe('§8 확대 조건 ⑸ — 확대·이동은 모든 층에 함께 적용된다', () => {
  it('배율은 조각마다가 아니라 **층 묶음 하나**에 걸린다', async () => {
    renderDetail(makeSource());
    await drawnMap();
    fireEvent.click(screen.getByRole('button', { name: '확대' }));
    expect(layers().style.transform).toContain('scale(2)');
    for (const t of tiles()) {
      expect(t.style.transform).toBe('');
      expect(layers().contains(t)).toBe(true);
    }
  });
});

describe('§8 확대 조건 ⑹ — 보기 권한만 있어도 확대되고, 확대 상태는 저장하지 않는다', () => {
  it('편집 권한이 없어도 확대 컨트롤이 서고 동작한다', async () => {
    renderDetail(makeSource());
    await drawnMap();
    expect(screen.queryByRole('button', { name: /스크린샷/ })).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: '확대' }));
    expect(scaleOf()).toBe(2);
  });

  it('화면을 떠났다 오면 기본 배율이다 — 어디에도 저장하지 않는다', async () => {
    const localSpy = vi.spyOn(Storage.prototype, 'setItem');
    const first = renderDetail(makeSource());
    await drawnMap();
    fireEvent.click(screen.getByRole('button', { name: '확대' }));
    expect(scaleOf()).toBe(2);
    first.unmount();
    renderDetail(makeSource());
    await drawnMap();
    await waitFor(() => expect(scaleOf()).toBe(1));
    expect(localSpy).not.toHaveBeenCalled();
    localSpy.mockRestore();
  });
});

describe('§8 확대 조건 ⑺ — 타일 표면에서도 반응이 100 ms 안이다', () => {
  /** 합격선 정본 = `Policy_데이터셋_상세` v2.6 `§8` 렌더 성능·상한 표. 여기는 집행이다. */
  const 상한_밀리초 = 100;

  function 재본다(횟수: number, 한번: () => void): { p95: number; max: number } {
    const 표본: number[] = [];
    for (let i = 0; i < 횟수; i += 1) {
      const t0 = performance.now();
      한번();
      표본.push(performance.now() - t0);
    }
    표본.sort((a, b) => a - b);
    // 최근접 순위법 — 표본이 적을 때 보간은 없는 정밀도를 지어낸다
    const 잰값 = {
      p95: 표본[Math.max(1, Math.ceil(0.95 * 표본.length)) - 1] as number,
      max: 표본[표본.length - 1] as number,
    };
    // **재고 나서 적기 위해 남긴다** — 회차 기록이 인용하는 수가 이 줄에서 온다
    console.log(`[타일 확대 반응] 표본 ${표본.length} · p95 ${잰값.p95.toFixed(3)} ms · 최대 ${잰값.max.toFixed(3)} ms`);
    return 잰값;
  }

  it('확대·축소 한 번의 처리 시간이 상한 안이다', async () => {
    renderDetail(makeSource());
    await drawnMap();
    const 확대 = screen.getByRole('button', { name: '확대' });
    const 축소 = screen.getByRole('button', { name: '축소' });
    let 짝수 = true;
    const 잰값 = 재본다(20, () => {
      fireEvent.click(짝수 ? 확대 : 축소);
      짝수 = !짝수;
      expect(layers().style.transform).toContain('scale(');
    });
    expect(잰값.p95).toBeLessThan(상한_밀리초);
    expect(잰값.max).toBeLessThan(상한_밀리초);
  });

  it('끌어 옮기기 한 걸음의 처리 시간이 상한 안이다', async () => {
    renderDetail(makeSource());
    const viewport = await drawnMap();
    fireEvent.click(screen.getByRole('button', { name: '확대' }));
    fireEvent.mouseDown(viewport, { clientX: 300, clientY: 300 });
    let x = 300;
    const 잰값 = 재본다(20, () => {
      x -= 3;
      fireEvent.mouseMove(window, { clientX: x, clientY: 300 });
      expect(layers().style.transform).toContain('translate(');
    });
    fireEvent.mouseUp(window);
    expect(잰값.p95).toBeLessThan(상한_밀리초);
    expect(잰값.max).toBeLessThan(상한_밀리초);
  });
});
