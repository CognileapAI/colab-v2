/**
 * S-05 데이터셋 상세 — **미리보기(시각화) 구역** 정본 대비 시험 (WU-P3).
 *
 * 오라클 = `E-03_데이터셋_상세/documents/Policy_데이터셋_상세.md` 축자.
 *  · `§1.3-1` 「한 페이지 스크롤이다. 탭으로 콘텐츠를 숨기지 않는다」
 *  · `§1.3-5` 「시각화는 한 번에 값 하나만 그린다. 보기는 전원, 편집은 권한자다」
 *  · `§3.2`   「편집 컨트롤(지도 표현·값 선택·팔레트·구간·스크린샷·계보 수정)이 화면에 없다」
 *  · `§5`     「시각화 구간 수 ｜ — ｜ 3~9 단계. 기본 6」
 *  · `§8` 지도 표현 「**무엇으로 그릴지는 사람이 고르지 않는다**」
 *  · `§8`     「**미리보기는 서버가 그린다** … 시간이 걸리므로 **단계를 말해야 한다**
 *              (파일 읽기 → 그리기 → 범례). 한 덩어리 "로딩 중"으로 두면 멈춘 것인지
 *              진행 중인지 구분되지 않는다」
 *  · `§8` 「미리보기를 그릴 수 없을 때」 표 — 형식 불가 · 서버 연결 못 함 · 조각 일부 못 읽음
 *
 * **화면 글자를 여기서 새로 만들지 않는다** — 정본·서버가 준 문구를 그대로 기대한다.
 * 범위 밖(이 시험이 단언하지 않는 것) — 팔레트 선택 재렌더(`V-1`) · 값 조회(`V-2`) ·
 * 확대(정본 근거 0건) · 겹쳐 보기 · 스크린샷 버튼(FE 도달 계약 표면 부재).
 */
import { render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { DatasetDetailPage } from '../src/routes/DatasetDetailPage';
import { fixtureDetailSource } from '../src/components/detail/fixture';
import { NotRenderableError, PreviewUnavailable } from '../src/components/preview/types';
import type { RenderJob } from '../src/components/preview/types';
import type { DatasetPreviewSource } from '../src/components/datasetpreview/types';

const OPEN_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA1'; // 낙동강 유역 강우 (2025) — 목업 기본 장면
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
  result: { imageUrl: 'https://viz.example/d/map.png', legend: LEGEND },
} as unknown as RenderJob;

/**
 * 그리는 중 — **계약 `RenderStage` 값 그대로**(`파일 읽는 중`). 정본 §8 의 3단
 * (파일 읽기 → 그리기 → 범례)을 계약이 이 세 값으로 못 박았다. 화면이 다시 쓰지 않는다.
 */
const DRAWING: RenderJob = {
  renderId: RENDER_ID,
  status: '그리는 중',
  stage: '파일 읽는 중',
} as unknown as RenderJob;

function makeSource(over: Partial<DatasetPreviewSource> = {}): DatasetPreviewSource {
  return {
    palettes: vi.fn(async () => [{ palette: 'viridis' }]),
    create: vi.fn(async () => DONE),
    get: vi.fn(async () => DONE),
    probeTile: vi.fn(async () => 'ok' as const),
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
        <Route path="/datasets" element={<div>카탈로그</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('§1.3-1 · §8 — 미리보기 구역은 상세 안에 선다', () => {
  it('상세 화면에 미리보기 구역이 있다', async () => {
    renderDetail(makeSource());
    expect(await screen.findByTestId('dataset-preview')).toBeTruthy();
  });

  it('탭으로 숨기지 않는다 — 미리보기를 여는 탭 버튼이 없다', async () => {
    renderDetail(makeSource());
    await screen.findByTestId('dataset-preview');
    expect(screen.queryByRole('tab')).toBeNull();
    expect(screen.queryByRole('tablist')).toBeNull();
  });
});

describe('§8 — 서버가 그린다. 대상은 이 데이터셋이다', () => {
  it('등록된 데이터셋을 대상으로 렌더를 시작한다 (`datasetId`)', async () => {
    const source = makeSource();
    renderDetail(source);
    await waitFor(() => expect(source.create).toHaveBeenCalled());
    expect(vi.mocked(source.create).mock.calls[0]?.[0].datasetId).toBe(OPEN_ID);
  });

  it('§5 — 구간 수 기본값은 6 이다', async () => {
    const source = makeSource();
    renderDetail(source);
    await waitFor(() => expect(source.create).toHaveBeenCalled());
    expect(vi.mocked(source.create).mock.calls[0]?.[0].classCount).toBe(6);
  });

  it('팔레트 이름을 화면이 지어내지 않는다 — 서버 목록의 값을 쓴다', async () => {
    const source = makeSource({ palettes: vi.fn(async () => [{ palette: 'magma' }]) });
    renderDetail(source);
    await waitFor(() => expect(source.create).toHaveBeenCalled());
    expect(vi.mocked(source.create).mock.calls[0]?.[0].palette).toBe('magma');
  });

  it('팔레트 목록이 비면 렌더를 시작하지 않는다 — 빈 값으로 부르지 않는다', async () => {
    const source = makeSource({ palettes: vi.fn(async () => []) });
    renderDetail(source);
    await screen.findByTestId('preview-unavailable');
    expect(source.create).not.toHaveBeenCalled();
  });

  it('§8 지도 표현 — 무엇으로 그릴지 고르는 자리를 두지 않는다', async () => {
    renderDetail(makeSource());
    const section = await screen.findByTestId('dataset-preview');
    expect(within(section).queryByText('격자')).toBeNull();
    expect(within(section).queryByText('경계')).toBeNull();
    expect(within(section).queryByText('점')).toBeNull();
  });
});

describe('§8 — 단계를 말한다. 한 덩어리 「로딩 중」으로 두지 않는다', () => {
  it('그리는 중에는 정본 3문구 중 지금 단계를 그대로 말한다', async () => {
    const source = makeSource({ create: vi.fn(async () => DRAWING), get: vi.fn(async () => DRAWING) });
    renderDetail(source);
    // 자리만 있고 글자가 없는 것은 「단계를 말한 것」이 아니다 — **글자가 뜰 때까지** 기다린다
    await waitFor(() =>
      expect(screen.getByTestId('render-stage').textContent).toContain('파일 읽는 중'),
    );
    expect(screen.queryByText(/로딩 중/)).toBeNull();
  });
});

describe('§8 — 완료되면 지도와 범례가 함께 선다', () => {
  it('지도가 뜬다', async () => {
    renderDetail(makeSource());
    expect(await screen.findByTestId('preview-map')).toBeTruthy();
  });

  it('범례가 서버가 준 구간 그대로 뜬다 — 화면이 구간을 다시 계산하지 않는다', async () => {
    renderDetail(makeSource());
    const map = await screen.findByTestId('preview-map');
    const legend = within(map).getByLabelText('범례');
    expect(legend.textContent).toContain('0 ~ 5 mm');
    expect(legend.textContent).toContain('5 ~ 10 mm');
  });
});

describe('§8 미리보기를 그릴 수 없을 때 — 실패는 종류대로 말한다', () => {
  it('그릴 수 없는 형식이면 **지금 그릴 수 있는 형식을 함께** 적는다', async () => {
    const source = makeSource({
      create: vi.fn(async () => {
        throw new NotRenderableError('이 형식은 아직 지도로 못 그려요.', [
          'NetCDF',
          'Binary',
          'HDF4',
          'GeoTIFF',
        ]);
      }),
    });
    renderDetail(source);
    const box = await screen.findByTestId('not-renderable');
    expect(box.textContent).toContain('이 형식은 아직 지도로 못 그려요.');
    expect(box.textContent).toContain('NetCDF');
    expect(box.textContent).toContain('GeoTIFF');
  });

  it('그리는 서버에 못 닿으면 정본 문구로 말한다 — 다운로드·계보는 그대로다', async () => {
    const source = makeSource({
      create: vi.fn(async () => {
        throw new PreviewUnavailable(
          '지금 미리보기를 만들 수 없어요. 잠시 뒤 다시 시도해 주세요.',
        );
      }),
    });
    renderDetail(source);
    const box = await screen.findByTestId('preview-unavailable');
    expect(box.textContent).toContain('지금 미리보기를 만들 수 없어요. 잠시 뒤 다시 시도해 주세요.');
    // 계보 구역은 살아 있다 — 그릴 수 없는 것과 읽을 수 없는 것은 다르다
    expect(screen.queryByTestId('dataset-preview')).toBeTruthy();
  });

  it('실패는 서버(정본)가 준 문구를 그대로 낸다', async () => {
    const failed = {
      renderId: RENDER_ID,
      status: '실패',
      failure: { code: 'RENDER_TIMEOUT', message: '그리는 데 너무 오래 걸려요. 조각 하나나 좁은 기간으로 다시 해 보세요' },
    } as unknown as RenderJob;
    const source = makeSource({ create: vi.fn(async () => failed), get: vi.fn(async () => failed) });
    renderDetail(source);
    const box = await screen.findByTestId('render-failure');
    expect(box.textContent).toContain('그리는 데 너무 오래 걸려요');
  });

  it('조각 일부를 못 읽은 것은 **실패가 아니다** — 읽은 조각으로 그리고 못 읽은 조각을 이름으로 밝힌다', async () => {
    const partial = {
      renderId: RENDER_ID,
      status: '완료',
      result: { imageUrl: 'https://viz.example/d/map.png', legend: LEGEND },
      partialFailure: {
        totalParts: 72,
        renderedParts: 69,
        missingParts: [
          { fileName: 'rain_20250701.nc', instant: '2025-07-01' },
          { fileName: 'rain_20250702.nc', instant: '2025-07-02' },
          { fileName: 'rain_20250703.nc', instant: '2025-07-03' },
        ],
      },
    } as unknown as RenderJob;
    const source = makeSource({ create: vi.fn(async () => partial), get: vi.fn(async () => partial) });
    renderDetail(source);
    const box = await screen.findByTestId('partial-failure');
    expect(box.textContent).toContain('조각 72개 중 3개를 읽지 못했어요. 읽은 69개로 그릴 수 있어요.');
    expect(box.textContent).toContain('rain_20250701.nc');
    // 지도는 그대로 그려진다
    expect(screen.getByTestId('preview-map')).toBeTruthy();
  });
});

describe('§1.3-5 · §3.2 · §6 — 보기는 전원, 편집은 권한자다', () => {
  it('보기 권한만이면 미리보기 편집 컨트롤이 화면에 **없다**', async () => {
    renderDetail(makeSource());
    const section = await screen.findByTestId('dataset-preview');
    // 정본 §3.2 가 이름으로 든 편집 컨트롤 넷 — 하나도 DOM 에 없다
    expect(within(section).queryByTestId('palette-control')).toBeNull();
    expect(within(section).queryByLabelText('구간 수')).toBeNull();
    expect(within(section).queryByRole('button', { name: /스크린샷/ })).toBeNull();
    expect(within(section).queryByRole('combobox')).toBeNull();
  });
});
