/**
 * S-05 미리보기 **확대·이동 반응 시간** 합격선 — 정본 `Policy_데이터셋_상세` v2.6 `§8`
 * 「확대(줌)」 조건 ⑺ 축자(`PLAN-SoT §9 〈233〉`).
 *
 * **여기서 재는 것** = 조작 이벤트가 들어온 순간부터 층 묶음의 변환이 반영된 순간까지의
 * **JS 처리 시간**이다. 확대는 렌더 재요청이 0건인 클라이언트 변환이므로(조건 ⑶ ·
 * `useZoomPan.ts`) 이 시간이 반응 시간의 전부를 이루는 부분이고, 그 위에 브라우저의
 * 합성(compositing)이 얹힌다.
 *
 * ⚠ **재지 않은 것을 잰 것처럼 적지 않는다** — 이 시험은 jsdom 에서 돌고 **화면 프레임을
 * 재지 않는다.** 실브라우저의 프레임 시간은 여기서 판정하지 않으며, 그 축은 Ted 의 직접
 * 확인(`〈234〉`)이 진다.
 *
 * 상한이 **넉넉한 이유**는 이 값이 「빠른가」를 재는 눈금이 아니라 **회귀를 잡는 자물쇠**이기
 * 때문이다 — 확대가 조용히 렌더 재요청이나 무거운 재계산을 타게 되면 여기서 수십 배로 튄다.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { DatasetDetailPage } from '../src/routes/DatasetDetailPage';
import { fixtureDetailSource } from '../src/components/detail/fixture';
import type { RenderJob } from '../src/components/preview/types';
import type { DatasetPreviewSource } from '../src/components/datasetpreview/types';

const OPEN_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA1';
const RENDER_ID = '01JYZ9K7WQ3N8V4M2X6C5B0RE9';

/** 합격선 — `PLAN-SoT §9 〈233〉`-㉯. 값의 정본은 정본 문서이고 여기는 그 집행이다. */
const 상한_밀리초 = 100;

const DONE: RenderJob = {
  renderId: RENDER_ID,
  status: '완료',
  result: {
    imageUrl: 'https://viz.example/d/map.png',
    legend: {
      palette: 'viridis',
      unit: 'mm',
      classes: [
        { color: '#440154', min: 0, max: 5 },
        { color: '#21918c', min: 5, max: 10 },
      ],
    },
    bounds: { west: 126, south: 34, east: 130, north: 38 },
  },
} as unknown as RenderJob;

function makeSource(): DatasetPreviewSource {
  return {
    palettes: vi.fn(async () => [{ palette: 'viridis' }]),
    create: vi.fn(async () => DONE),
    get: vi.fn(async () => DONE),
    probeTile: vi.fn(async () => 'ok' as const),
    // 이미지 갈래 시험이라 사이드카를 묻지 않는다 (`〈238〉`)
    mapGeometry: vi.fn(async () => undefined),
    // 값 조회는 이 시험의 관심 밖이다 — **자리는 채우되 값을 만들지 않는다**(`〈294〉`)
    lookupValue: vi.fn(async () => {
      throw new Error('이 시험은 값 조회를 부르지 않는다');
    }),
    screenshot: vi.fn(async () => new Blob([new Uint8Array([1])], { type: 'image/png' })),
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

/** 한계 배율은 데이터가 가진 해상도에서 온다. jsdom 은 못 재므로 시험이 값을 심는다. */
async function drawn() {
  await screen.findByTestId('preview-map');
  const viewport = screen.getByTestId('preview-viewport');
  Object.defineProperty(viewport, 'clientWidth', { value: 512, configurable: true });
  Object.defineProperty(viewport, 'clientHeight', { value: 512, configurable: true });
  const img = viewport.querySelector('img') as HTMLImageElement;
  Object.defineProperty(img, 'naturalWidth', { value: 4096, configurable: true });
  Object.defineProperty(img, 'naturalHeight', { value: 4096, configurable: true });
  fireEvent.load(img);
  return viewport;
}

function transformOf(): string {
  return screen.getByTestId('preview-layers').style.transform;
}

/** 최근접 순위법 — 표본이 적을 때 보간은 없는 정밀도를 지어낸다. */
function p95(sorted: number[]): number {
  return sorted[Math.max(1, Math.ceil(0.95 * sorted.length)) - 1] as number;
}

function 재본다(횟수: number, 한번: () => void): { p95: number; max: number } {
  const 표본: number[] = [];
  for (let i = 0; i < 횟수; i += 1) {
    const t0 = performance.now();
    한번();
    표본.push(performance.now() - t0);
  }
  표본.sort((a, b) => a - b);
  return { p95: p95(표본), max: 표본[표본.length - 1] as number };
}

describe('§8 확대 조건 ⑺ — 확대·이동 반응은 100 ms 이내다', () => {
  it('확대·축소 한 번의 처리 시간이 상한 안이다', async () => {
    renderDetail(makeSource());
    await drawn();
    const 확대 = screen.getByRole('button', { name: '확대' });
    const 축소 = screen.getByRole('button', { name: '축소' });
    let 짝수 = true;
    const 잰값 = 재본다(20, () => {
      fireEvent.click(짝수 ? 확대 : 축소);
      짝수 = !짝수;
      // 반영되지 않은 채로 시간만 재는 것을 막는다 — 변환 문자열을 실제로 읽는다.
      expect(transformOf()).toContain('scale(');
    });
    expect(잰값.p95).toBeLessThan(상한_밀리초);
    expect(잰값.max).toBeLessThan(상한_밀리초);
  });

  it('끌어 옮기기 한 걸음의 처리 시간이 상한 안이다', async () => {
    renderDetail(makeSource());
    const viewport = await drawn();
    fireEvent.click(screen.getByRole('button', { name: '확대' }));
    fireEvent.mouseDown(viewport, { clientX: 300, clientY: 300 });
    let x = 300;
    const 잰값 = 재본다(20, () => {
      x -= 3;
      fireEvent.mouseMove(window, { clientX: x, clientY: 300 });
      expect(transformOf()).toContain('translate(');
    });
    fireEvent.mouseUp(window);
    expect(잰값.p95).toBeLessThan(상한_밀리초);
    expect(잰값.max).toBeLessThan(상한_밀리초);
  });

  it('그 시간 안에 렌더 재요청이 0건이다 — 반응이 빠른 이유가 여기 있다', async () => {
    const source = makeSource();
    renderDetail(source);
    const viewport = await drawn();
    const 시작 = vi.mocked(source.create).mock.calls.length;
    for (let i = 0; i < 20; i += 1) {
      fireEvent.click(screen.getByRole('button', { name: '확대' }));
      fireEvent.wheel(viewport, { deltaY: 120, clientX: 100, clientY: 100 });
    }
    expect(vi.mocked(source.create).mock.calls.length - 시작).toBe(0);
    expect(vi.mocked(source.get).mock.calls.length).toBeLessThanOrEqual(1);
  });
});
