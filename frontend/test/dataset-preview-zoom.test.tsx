/**
 * S-05 데이터셋 상세 미리보기 — **확대(줌)** 정본 대비 시험 (WU-P3 · 화면 레인).
 *
 * 오라클 = `E-03_데이터셋_상세/documents/Policy_데이터셋_상세.md` **v2.5** 축자.
 *  · `§8` 「확대(줌) — 왜 넣는가, 무엇이 되면 된 것인가」의 **여섯 조건** (전부 충족해야 닫는다)
 *    ⑴ 미리보기가 그려진 뒤 지도를 **확대·축소·이동**할 수 있다
 *    ⑵ 확대·이동해도 **값·팔레트·구간 수 설정과 범례가 바뀌지 않는다**
 *    ⑶ 확대·이동이 **렌더를 다시 걸지 않는다** — 확대 조작 중 새 렌더 작업 생성 0건
 *    ⑷ **데이터가 가진 해상도가 한계다.** 한계에 닿으면 「원본 해상도까지 봤어요」를 알린다 ·
 *       **없는 값을 만들어 그리지 않는다**
 *    ⑸ 층이 둘 이상일 때 **확대·이동이 모든 층에 함께 적용된다**
 *    ⑹ **보기 권한만 있어도 확대된다** · **확대 상태는 저장하지 않는다**
 *  · `§8` `확대·이동` 행 「확대는 시각화 편집이 아니라 보기다」 · 「이미 그린 결과 안에서
 *    그 배율에 맞는 촘촘함으로 바꿔 끼운다」
 *
 * **화면 글자를 여기서 새로 만들지 않는다** — 정본 문구를 그대로 기대한다.
 * 범위 밖 — 팔레트 선택 재렌더(`V-1`) · 값 조회(`V-2`) · 겹쳐 보기 · 타일 서빙.
 */
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { DatasetDetailPage } from '../src/routes/DatasetDetailPage';
import { fixtureDetailSource } from '../src/components/detail/fixture';
import type { RenderJob } from '../src/components/preview/types';
import type { DatasetPreviewSource } from '../src/components/datasetpreview/types';

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

const DONE: RenderJob = {
  renderId: RENDER_ID,
  status: '완료',
  result: {
    imageUrl: 'https://viz.example/d/map.png',
    legend: LEGEND,
    bounds: { west: 126, south: 34, east: 130, north: 38 },
  },
} as unknown as RenderJob;

function makeSource(over: Partial<DatasetPreviewSource> = {}): DatasetPreviewSource {
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

/**
 * **한계 배율은 데이터가 가진 해상도에서 온다** — 그림의 원본 픽셀 수와 화면에 놓인 크기의 비다.
 * jsdom 은 두 값을 재지 않으므로 시험이 실물 대신 값을 심고 `load` 를 알린다.
 * 여기서 심는 4096 / 512 = **한계 배율 8**.
 */
function measure(naturalPx = 4096, boxPx = 512) {
  const viewport = screen.getByTestId('preview-viewport');
  Object.defineProperty(viewport, 'clientWidth', { value: boxPx, configurable: true });
  Object.defineProperty(viewport, 'clientHeight', { value: boxPx, configurable: true });
  const img = viewport.querySelector('img') as HTMLImageElement;
  Object.defineProperty(img, 'naturalWidth', { value: naturalPx, configurable: true });
  Object.defineProperty(img, 'naturalHeight', { value: naturalPx, configurable: true });
  fireEvent.load(img);
  return { viewport, img };
}

function scaleOf(): number {
  return Number(screen.getByTestId('preview-layers').getAttribute('data-zoom-scale'));
}

async function drawnMap() {
  await screen.findByTestId('preview-map');
  return measure();
}

describe('§8 확대 조건 ⑴ — 그린 뒤 확대·축소·이동이 된다', () => {
  it('확대 버튼이 배율을 올린다', async () => {
    renderDetail(makeSource());
    await drawnMap();
    expect(scaleOf()).toBe(1);
    fireEvent.click(screen.getByRole('button', { name: '확대' }));
    expect(scaleOf()).toBe(2);
  });

  it('축소 버튼이 배율을 되돌린다 — 기본 배율 아래로는 내려가지 않는다', async () => {
    renderDetail(makeSource());
    await drawnMap();
    fireEvent.click(screen.getByRole('button', { name: '확대' }));
    fireEvent.click(screen.getByRole('button', { name: '축소' }));
    expect(scaleOf()).toBe(1);
    fireEvent.click(screen.getByRole('button', { name: '축소' }));
    expect(scaleOf()).toBe(1);
  });

  it('끌어 옮기면 보는 자리가 움직인다', async () => {
    renderDetail(makeSource());
    const { viewport } = await drawnMap();
    fireEvent.click(screen.getByRole('button', { name: '확대' }));
    const before = screen.getByTestId('preview-layers').style.transform;
    fireEvent.mouseDown(viewport, { clientX: 300, clientY: 300 });
    fireEvent.mouseMove(window, { clientX: 240, clientY: 260 });
    fireEvent.mouseUp(window);
    expect(screen.getByTestId('preview-layers').style.transform).not.toBe(before);
  });
});

describe('§8 확대 조건 ⑵ — 값·팔레트·구간 수 설정과 범례가 바뀌지 않는다', () => {
  it('확대 전후 범례가 같다', async () => {
    renderDetail(makeSource());
    await drawnMap();
    const legend = within(screen.getByTestId('preview-map')).getByLabelText('범례');
    const before = legend.textContent;
    fireEvent.click(screen.getByRole('button', { name: '확대' }));
    fireEvent.click(screen.getByRole('button', { name: '확대' }));
    expect(
      within(screen.getByTestId('preview-map')).getByLabelText('범례').textContent,
    ).toBe(before);
    expect(legend.textContent).toContain('0 ~ 5 mm');
  });

  it('범례는 확대되는 층 묶음 **밖**에 있다 — 그림과 함께 커지지 않는다', async () => {
    renderDetail(makeSource());
    await drawnMap();
    const layers = screen.getByTestId('preview-layers');
    expect(within(layers).queryByLabelText('범례')).toBeNull();
  });

  it('팔레트·구간 수 설정이 확대로 다시 요청되지 않는다', async () => {
    const source = makeSource();
    renderDetail(source);
    await drawnMap();
    fireEvent.click(screen.getByRole('button', { name: '확대' }));
    expect(vi.mocked(source.create).mock.calls).toHaveLength(1);
    expect(vi.mocked(source.create).mock.calls[0]?.[0].classCount).toBe(6);
    expect(vi.mocked(source.create).mock.calls[0]?.[0].palette).toBe('viridis');
  });
});

describe('§8 확대 조건 ⑶ — 확대 조작 중 새 렌더 작업 생성 0건', () => {
  it('확대·축소·이동·되돌리기를 해도 렌더를 다시 걸지 않는다', async () => {
    const source = makeSource();
    renderDetail(source);
    const { viewport } = await drawnMap();
    const started = vi.mocked(source.create).mock.calls.length;
    fireEvent.click(screen.getByRole('button', { name: '확대' }));
    fireEvent.click(screen.getByRole('button', { name: '확대' }));
    fireEvent.wheel(viewport, { deltaY: -120, clientX: 100, clientY: 100 });
    fireEvent.mouseDown(viewport, { clientX: 300, clientY: 300 });
    fireEvent.mouseMove(window, { clientX: 200, clientY: 200 });
    fireEvent.mouseUp(window);
    fireEvent.click(screen.getByRole('button', { name: '축소' }));
    fireEvent.click(screen.getByRole('button', { name: '기본 배율로' }));
    expect(vi.mocked(source.create).mock.calls.length - started).toBe(0);
  });
});

describe('§8 확대 조건 ⑷ — 데이터가 가진 해상도가 한계다', () => {
  it('한계 배율을 넘어 들어가지 않는다 — 없는 값을 만들어 그리지 않는다', async () => {
    renderDetail(makeSource());
    await drawnMap(); // 한계 배율 8
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

  it('그림의 해상도를 아직 모르면 확대하지 않는다 — 한계를 지어내지 않는다', async () => {
    renderDetail(makeSource());
    await screen.findByTestId('preview-map');
    fireEvent.click(screen.getByRole('button', { name: '확대' }));
    expect(scaleOf()).toBe(1);
  });
});

describe('§8 확대 조건 ⑸ — 확대·이동은 모든 층에 함께 적용된다', () => {
  it('배율은 층마다가 아니라 **층 묶음 하나**에 걸린다', async () => {
    renderDetail(makeSource());
    const { img } = await drawnMap();
    fireEvent.click(screen.getByRole('button', { name: '확대' }));
    const layers = screen.getByTestId('preview-layers');
    expect(layers.style.transform).toContain('scale(2)');
    // 층(그림) 자신은 배율을 갖지 않는다 — 층마다 따로 확대하지 않는다
    expect(img.style.transform).toBe('');
    expect(layers.contains(img)).toBe(true);
  });
});

describe('§8 확대 조건 ⑹ — 보기 권한만 있어도 확대되고, 확대 상태는 저장하지 않는다', () => {
  it('편집 권한이 없어도 확대 컨트롤이 서고 동작한다 (편집 컨트롤과 함께 숨지 않는다)', async () => {
    renderDetail(makeSource());
    await drawnMap();
    // 권한 스위치가 하나도 켜지지 않은 세션이다 — 스크린샷(편집 컨트롤)은 없다
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
    // ⭑ **WU-P7 이 이 단언을 좁혔다.** 종전은 「`setItem` 이 한 번도 안 불린다」였는데,
    //   그 뒤 상세 화면이 **「내가 열어 본 것」을 브라우저에 적는다**(`Policy_홈_대시보드 §10` ·
    //   `components/dashboard/visits.ts`). 확대 상태를 저장하지 않는다는 **이 시험의 규칙은
    //   그대로 지켜지고**, 넓게 잡혀 있던 단언만 그 규칙의 크기로 줄인다 — 확대 관련 키가
    //   하나도 안 써지는 것을 본다. 넓은 단언을 지우는 것이 아니라 대상을 명시하는 것이다.
    const keys = localSpy.mock.calls.map((call) => String(call[0]));
    expect(keys.filter((k) => /zoom|scale|확대/i.test(k))).toEqual([]);
    expect(keys.every((k) => k === 'colab.v2.visits')).toBe(true);
    localSpy.mockRestore();
  });
});
