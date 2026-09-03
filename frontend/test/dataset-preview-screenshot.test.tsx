/**
 * S-05 데이터셋 상세 미리보기 — **스크린샷** 정본 대비 시험 (WU-P3 · 화면 레인).
 *
 * 오라클 = `Policy_데이터셋_상세` **v2.5** 축자.
 *  · `§8` 스크린샷 행 「지금 장면을 PNG로 저장. **설정을 저장하지 않으므로 남길 장면은 여기서
 *    뽑는다.** **확대한 자리와 배율도 "지금 장면"에 포함된다**」 · 권한 = **편집 권한자**
 *  · `§6`  「`업로드·편집` 켜짐 ｜ 시각화 편집·**스크린샷**·계보 수정」
 *  · `§3.2` 「편집 컨트롤(… 스크린샷 …)이 화면에 없다」 — 보기 전용에서는 자리째 없다
 *
 * 계약 = `fe-core.yaml#createPreviewScreenshot`(`POST /preview-screenshots`) ·
 * 요청 스키마는 `core-viz.yaml#ScreenshotRequest`(`layers[].renderId` · `viewport{width,height,bounds}`).
 * **계약을 고치지 않는다 · 생성물을 손대지 않는다.**
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { DatasetDetailPage } from '../src/routes/DatasetDetailPage';
import { fixtureDetailSource } from '../src/components/detail/fixture';
import { SessionProvider } from '../src/permission/session';
import { apiDatasetPreviewSource } from '../src/components/datasetpreview/datasetPreviewSource';
import type { CurrentAccount } from '../src/api/client';
import type { RenderJob } from '../src/components/preview/types';
import type { DatasetPreviewSource } from '../src/components/datasetpreview/types';

const OPEN_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA1';
const RENDER_ID = '01JYZ9K7WQ3N8V4M2X6C5B0RE9';

const LEGEND = {
  palette: 'viridis',
  unit: 'mm',
  classes: [{ color: '#440154', min: 0, max: 5 }],
};

const BOUNDS = { west: 126, south: 34, east: 130, north: 38 };

const DONE: RenderJob = {
  renderId: RENDER_ID,
  status: '완료',
  result: { imageUrl: 'https://viz.example/d/map.png', legend: LEGEND, bounds: BOUNDS },
} as unknown as RenderJob;

/** ②비지도형 — 좌표가 없는 결과도 **완료**다(`〈85〉`). 경계가 없는 것이 정상이다. */
const DONE_NO_BOUNDS: RenderJob = {
  renderId: RENDER_ID,
  status: '완료',
  result: { imageUrl: 'https://viz.example/d/plot.png', legend: LEGEND },
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
    screenshot: vi.fn(async () => new Blob([new Uint8Array([1, 2])], { type: 'image/png' })),
    ...over,
  };
}

function editorAccount(on: boolean): CurrentAccount {
  return { permissions: { '업로드·편집': on } } as unknown as CurrentAccount;
}

function renderDetail(previewSource: DatasetPreviewSource, account: CurrentAccount | null) {
  return render(
    <SessionProvider account={account}>
      <MemoryRouter initialEntries={[`/datasets/${OPEN_ID}`]}>
        <Routes>
          <Route
            path="/datasets/:datasetId"
            element={
              <DatasetDetailPage source={fixtureDetailSource()} previewSource={previewSource} />
            }
          />
        </Routes>
      </MemoryRouter>
    </SessionProvider>,
  );
}

/** 확대와 같은 자리에서 오는 값 — 그림의 원본 픽셀과 화면에 놓인 크기. */
function measure(naturalPx = 4096, boxPx = 512) {
  const viewport = screen.getByTestId('preview-viewport');
  Object.defineProperty(viewport, 'clientWidth', { value: boxPx, configurable: true });
  Object.defineProperty(viewport, 'clientHeight', { value: boxPx, configurable: true });
  const img = viewport.querySelector('img') as HTMLImageElement;
  Object.defineProperty(img, 'naturalWidth', { value: naturalPx, configurable: true });
  Object.defineProperty(img, 'naturalHeight', { value: naturalPx, configurable: true });
  fireEvent.load(img);
}

beforeEach(() => {
  Object.defineProperty(URL, 'createObjectURL', { value: vi.fn(() => 'blob:x'), configurable: true });
  Object.defineProperty(URL, 'revokeObjectURL', { value: vi.fn(), configurable: true });
});

afterEach(() => vi.restoreAllMocks());

describe('§6 · §3.2 — 스크린샷은 편집 권한자 컨트롤이다', () => {
  it('`업로드·편집` 이 켜져 있으면 버튼이 선다', async () => {
    renderDetail(makeSource(), editorAccount(true));
    await screen.findByTestId('preview-map');
    expect(screen.getByRole('button', { name: '스크린샷' })).toBeTruthy();
  });

  it('꺼져 있으면 자리째 없다 — 비활성 버튼을 두지 않는다', async () => {
    renderDetail(makeSource(), editorAccount(false));
    await screen.findByTestId('preview-map');
    expect(screen.queryByRole('button', { name: '스크린샷' })).toBeNull();
  });

  it('좌표가 없는 결과(②비지도형)에는 버튼을 세우지 않는다 — 계약이 요구하는 경계를 지어내지 않는다', async () => {
    const source = makeSource({
      create: vi.fn(async () => DONE_NO_BOUNDS),
      get: vi.fn(async () => DONE_NO_BOUNDS),
    });
    renderDetail(source, editorAccount(true));
    await screen.findByTestId('preview-map');
    expect(screen.queryByRole('button', { name: '스크린샷' })).toBeNull();
  });
});

describe('§8 — 지금 장면을 뽑는다', () => {
  it('이 렌더를 층으로, 화면 크기와 경계를 뷰포트로 실어 보낸다', async () => {
    const source = makeSource();
    renderDetail(source, editorAccount(true));
    await screen.findByTestId('preview-map');
    measure();
    fireEvent.click(screen.getByRole('button', { name: '스크린샷' }));
    await waitFor(() => expect(source.screenshot).toHaveBeenCalled());
    const req = vi.mocked(source.screenshot).mock.calls[0]?.[0];
    expect(req?.layers).toEqual([{ renderId: RENDER_ID, opacity: 1 }]);
    expect(req?.viewport.width).toBe(512);
    expect(req?.viewport.height).toBe(512);
    expect(req?.viewport.bounds).toEqual(BOUNDS);
  });

  it('**확대한 자리와 배율도 「지금 장면」에 포함된다** — 좁아진 경계로 나간다', async () => {
    const source = makeSource();
    renderDetail(source, editorAccount(true));
    await screen.findByTestId('preview-map');
    measure();
    fireEvent.click(screen.getByRole('button', { name: '확대' })); // 배율 2 · 가운데를 키운다
    fireEvent.click(screen.getByRole('button', { name: '스크린샷' }));
    await waitFor(() => expect(source.screenshot).toHaveBeenCalled());
    const b = vi.mocked(source.screenshot).mock.calls[0]?.[0].viewport.bounds;
    // 배율 2 로 가운데를 키워 봤다 — 네 변이 모두 안쪽으로 좁아진다
    expect(b?.west ?? 0).toBeGreaterThan(BOUNDS.west);
    expect(b?.east ?? 0).toBeLessThan(BOUNDS.east);
    expect(b?.south ?? 0).toBeGreaterThan(BOUNDS.south);
    expect(b?.north ?? 0).toBeLessThan(BOUNDS.north);
  });

  it('받은 PNG 를 그대로 내려 준다 — 화면이 그림을 다시 만들지 않는다', async () => {
    renderDetail(makeSource(), editorAccount(true));
    await screen.findByTestId('preview-map');
    measure();
    fireEvent.click(screen.getByRole('button', { name: '스크린샷' }));
    await waitFor(() => expect(URL.createObjectURL).toHaveBeenCalled());
  });

  it('그리는 서버에 못 닿으면 그 사실을 말한다 — 빈 이미지를 지어내지 않는다', async () => {
    const source = makeSource({
      screenshot: vi.fn(async () => {
        throw new Error('지금 미리보기를 만들 수 없어요. 잠시 뒤 다시 시도해 주세요.');
      }),
    });
    renderDetail(source, editorAccount(true));
    await screen.findByTestId('preview-map');
    measure();
    fireEvent.click(screen.getByRole('button', { name: '스크린샷' }));
    const box = await screen.findByTestId('screenshot-failure');
    expect(box.textContent).toContain('지금 미리보기를 만들 수 없어요.');
    expect(URL.createObjectURL).not.toHaveBeenCalled();
  });
});

describe('계약 — 중계 op `createPreviewScreenshot` 에 닿는다', () => {
  it('`POST /preview-screenshots` 를 부르고 PNG 본문을 그대로 돌려준다', async () => {
    const calls: Array<{ url: string; method: string }> = [];
    vi.stubGlobal('fetch', async (input: Request) => {
      calls.push({ url: input.url, method: input.method });
      // jsdom 의 `Blob` 은 `Response` 본문으로 그대로 들어가지 않는다 — 바이트로 준다
      return new Response(new Uint8Array([137, 80]), {
        status: 200,
        headers: { 'content-type': 'image/png' },
      });
    });
    const blob = await apiDatasetPreviewSource('0000000000000000000000DSA1').screenshot({
      layers: [{ renderId: RENDER_ID, opacity: 1 }],
      viewport: { width: 512, height: 512, bounds: BOUNDS },
    });
    expect(calls[0]?.url).toContain('/preview-screenshots');
    expect(calls[0]?.method).toBe('POST');
    expect(blob.size).toBe(2);
    vi.unstubAllGlobals();
  });
});
