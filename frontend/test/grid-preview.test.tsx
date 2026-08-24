/**
 * S-04 미리보기 3층 소비 + HSR 격자 업로드 흐름 — `S1-PLAN-REFOUND §E` 대비 시험.
 *
 * 오라클
 *  · `dev-package/sessions/S1-PLAN-REFOUND.md §E.2` — 상태 11개와 **한국어 확정안**
 *  · 같은 문서 `§E.3` — 검증 사다리 6단과 거절 사유
 *  · 같은 문서 `§D.4` — 잠정/확정 공통 색 범위
 *  · `PLAN-SoT §9-〈74〉·〈75〉·〈83〉·〈85〉` — 미리보기 3층 · 격자 전제 · `bounds` 는 지도형에만
 *
 * **화면 글자를 여기서 새로 만들지 않는다** — §E.2 표의 문구를 그대로 기대한다.
 * 원칙 하나가 이 파일 전체를 관통한다: **그릴 수 없는 것과 등록할 수 없는 것은 다르다.**
 */
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { PreviewPanel } from '../src/components/upload/PreviewPanel';
import type { PreviewSource, RenderJob } from '../src/components/upload/types';
import { GRID_COPY, gridState } from '../src/components/upload/gridFlow';

const RENDER_ID = '01JYZ9K7WQ3N8V4M2X6C5B0RE1';
const UPLOAD_ID = '01JYZ9K7WQ3N8V4M2X6C5B0UP1';

const LEGEND = { palette: 'viridis', classes: [{ color: '#440154', min: 0, max: 5 }] };

/** ②비지도형 — `imageUrl` 하나. **경계가 없는 것이 정상이다**(`〈85〉`). */
const DONE_VALUES: RenderJob = {
  renderId: RENDER_ID,
  status: '완료',
  result: {
    imageUrl: 'https://viz.example/p/detail.png',
    legend: LEGEND,
    precisionBadge: '격자 없음 — 지도형 보류',
    colorRangeStage: '잠정',
  },
} as unknown as RenderJob;

/** ③지도형 — 이미지 + 사이드카 + 월드파일 + 경계. */
const DONE_MAP: RenderJob = {
  renderId: RENDER_ID,
  status: '완료',
  result: {
    imageUrl: 'https://viz.example/p/map.png',
    sidecarUrl: 'https://viz.example/p/map.json',
    worldFileUrl: 'https://viz.example/p/map.pgw',
    bounds: { west: 127, south: 34, east: 130, north: 38 },
    legend: LEGEND,
    precisionBadge: '동봉 격자 적용',
    colorRangeStage: '잠정',
  },
} as unknown as RenderJob;

function failed(code: string, detail: string, withSalvage = true): RenderJob {
  return {
    renderId: RENDER_ID,
    status: '실패',
    failure: {
      code,
      message: '위경도를 담은 짝 파일이 없어요.',
      details: {
        detail,
        ...(withSalvage
          ? {
              thumbnailUrl: 'https://viz.example/p/thumb.webp',
              valuePreviewUrl: 'https://viz.example/p/detail.png',
              precisionBadge: '격자 없음 — 지도형 보류',
              colorRangeStage: '잠정',
            }
          : {}),
      },
    },
  } as unknown as RenderJob;
}

function source(jobs: RenderJob[]): PreviewSource {
  let i = 0;
  return {
    async palettes() {
      return [{ palette: 'viridis', label: '비리디스' }];
    },
    async createRender() {
      // 실서버와 같은 순서다 — 접수는 `그리는 중` 으로 오고 결과는 조회로 온다
      return { renderId: RENDER_ID, status: '그리는 중', stage: '파일 읽는 중' } as RenderJob;
    },
    async getRender() {
      const j = jobs[Math.min(i, jobs.length - 1)];
      i += 1;
      return j as RenderJob;
    },
  };
}

async function draw(over: Partial<Parameters<typeof PreviewPanel>[0]> = {}, jobs = [DONE_VALUES]) {
  render(
    <PreviewPanel
      source={over.source ?? source(jobs)}
      uploadId={UPLOAD_ID}
      hasReferenceGrid={over.hasReferenceGrid ?? false}
      grid={over.grid}
    />,
  );
  fireEvent.click(await screen.findByTestId('up-preview-draw'));
  await act(async () => {});
}

// ───────────────────────────────────────────────────────────────────────────
describe('§D.4·〈85〉 미리보기 3층 — 좌표 없는 ②는 **완료**이지 실패가 아니다', () => {
  it('②비지도형: 이미지 한 장을 그리고 배지를 말한다. 오류 자리를 쓰지 않는다', async () => {
    await draw({}, [DONE_VALUES]);
    const img = await screen.findByTestId('up-preview-image', undefined, { timeout: 4000 });
    expect(img.getAttribute('src')).toBe('https://viz.example/p/detail.png');
    expect(screen.getByTestId('up-preview-badge')).toHaveTextContent('격자 없음 — 지도형 보류');
    expect(screen.getByTestId('up-preview-layer')).toHaveTextContent('값 미리보기');
    expect(screen.queryByTestId('up-preview-error')).toBeNull();
  });

  it('③지도형: 경계·사이드카가 함께 오면 지도형으로 말한다', async () => {
    await draw({}, [DONE_MAP]);
    const img = await screen.findByTestId('up-preview-image', undefined, { timeout: 4000 });
    expect(img.getAttribute('src')).toBe('https://viz.example/p/map.png');
    expect(screen.getByTestId('up-preview-layer')).toHaveTextContent('지도형');
    expect(screen.getByTestId('up-preview-badge')).toHaveTextContent('동봉 격자 적용');
  });

  it('①썸네일 — 진짜 실패라도 이미 구운 값 미리보기와 썸네일을 감추지 않는다', async () => {
    await draw({}, [failed('MAP_BOUNDS_IMPLAUSIBLE', '경계가 상식 밖이다')]);
    const salvage = await screen.findByTestId('up-preview-salvage', undefined, { timeout: 4000 });
    expect(salvage.querySelector('[data-testid="up-preview-thumb"]')?.getAttribute('src')).toBe(
      'https://viz.example/p/thumb.webp',
    );
    expect(salvage.querySelector('[data-testid="up-preview-image"]')?.getAttribute('src')).toBe(
      'https://viz.example/p/detail.png',
    );
  });

  it('화면에 ①②③ 같은 번호를 쓰지 않는다', async () => {
    await draw({}, [DONE_VALUES]);
    await screen.findByTestId('up-preview-image', undefined, { timeout: 4000 });
    expect(screen.getByTestId('up-preview').textContent).not.toMatch(/[①②③④⑤⑥⑦⑧⑨⑩⑪]/);
  });
});

describe('§D.4 잠정 색 범위 — 조용히 바꾸지 않는다', () => {
  it('잠정이면 등록 전에 미리 알린다', async () => {
    await draw({}, [DONE_VALUES]);
    await screen.findByTestId('up-preview-image', undefined, { timeout: 4000 });
    expect(screen.getByTestId('up-preview-colorstage')).toHaveTextContent('잠정');
    expect(screen.getByTestId('up-preview-colorstage')).toHaveTextContent(
      '등록하면 색이 달라질 수 있습니다',
    );
  });

  it('확정으로 바뀌면 그 사실을 한 번 말한다', async () => {
    const CONFIRMED = {
      renderId: RENDER_ID,
      status: '완료',
      result: {
        imageUrl: 'https://viz.example/p/detail2.png',
        legend: { palette: 'viridis', classes: [{ color: '#440154', min: 0, max: 9 }] },
        precisionBadge: '격자 없음 — 지도형 보류',
        colorRangeStage: '확정',
      },
    } as unknown as RenderJob;
    await draw({}, [DONE_VALUES, CONFIRMED]);
    await screen.findByTestId('up-preview-image', undefined, { timeout: 4000 });
    // 다시 그리면 확정 범위가 온다 — 그때 **한 번** 말한다
    fireEvent.click(screen.getByTestId('up-preview-draw'));
    await waitFor(
      () => expect(screen.getByTestId('up-preview-colorstage')).toHaveTextContent('확정'),
      { timeout: 4000 },
    );
    expect(screen.getByTestId('up-preview-colorstage')).toHaveTextContent('색 범위가 달라졌습니다');
  });
});

describe('§E.2 격자 흐름 — 상태와 문구는 정본이 소유한다', () => {
  it('좌표 없음: 격자를 청하고, 건너뛰기가 함께 있다', async () => {
    await draw({ grid: { onPickGrid: vi.fn(), onSkipGrid: vi.fn() } }, [DONE_VALUES]);
    const block = await screen.findByTestId('up-grid-block', undefined, { timeout: 4000 });
    expect(block).toHaveTextContent('이 파일은 좌표를 자체적으로 갖고 있지 않습니다.');
    expect(block).toHaveTextContent('지도 위 위치를 보려면 위경도 격자 파일이 필요합니다.');
    expect(screen.getByTestId('up-grid-pick')).toBeEnabled();
    expect(screen.getByTestId('up-grid-skip')).toBeEnabled();
  });

  it('격자 파일을 고르면 바깥으로 넘긴다 — 화면이 축을 묻지 않는다', async () => {
    const onPick = vi.fn();
    await draw({ grid: { onPickGrid: onPick, onSkipGrid: vi.fn() } }, [DONE_VALUES]);
    await screen.findByTestId('up-grid-block', undefined, { timeout: 4000 });
    const input = screen.getByTestId('up-grid-input');
    fireEvent.change(input, { target: { files: [new File(['x'], 'Lat_HSR.npy')] } });
    await act(async () => {});
    expect(onPick).toHaveBeenCalled();
    expect(screen.queryByTestId('up-grid-axis')).toBeNull();
  });

  it('건너뜀: 지도 없이 등록한다고 말하고, 등록 경로를 막지 않는다', async () => {
    await draw({ grid: { skipped: true, onPickGrid: vi.fn(), onSkipGrid: vi.fn() } }, [
      DONE_VALUES,
    ]);
    const block = await screen.findByTestId('up-grid-block', undefined, { timeout: 4000 });
    expect(block).toHaveTextContent('지도 없이 등록합니다.');
    expect(block).toHaveTextContent('값 미리보기와 계보는 그대로 유지됩니다.');
  });

  it('전송 중: 크기 비례라 **여기만** 퍼센트가 정직하다', async () => {
    await draw(
      {
        grid: {
          transfer: { sentBytes: 13_281_474, totalBytes: 26_562_948 },
          onPickGrid: vi.fn(),
          onSkipGrid: vi.fn(),
        },
      },
      [DONE_VALUES],
    );
    const block = await screen.findByTestId('up-grid-block', undefined, { timeout: 4000 });
    expect(block).toHaveTextContent('격자 파일을 받는 중입니다.');
    expect(screen.getByTestId('up-grid-progress')).toHaveAttribute('value', '50');
  });

  it('확인 중: 판정은 이분법이라 퍼센트를 쓰지 않는다', async () => {
    await draw({ grid: { verifying: true, onPickGrid: vi.fn(), onSkipGrid: vi.fn() } }, [
      DONE_VALUES,
    ]);
    const block = await screen.findByTestId('up-grid-block', undefined, { timeout: 4000 });
    expect(block).toHaveTextContent('격자가 이 파일의 것인지 확인하는 중입니다.');
    expect(screen.queryByTestId('up-grid-progress')).toBeNull();
  });

  it('통과: 위치를 사람 눈으로 확인받는다', async () => {
    await draw({ grid: { onPickGrid: vi.fn(), onSkipGrid: vi.fn() } }, [DONE_MAP]);
    const block = await screen.findByTestId('up-grid-block', undefined, { timeout: 4000 });
    expect(block).toHaveTextContent('이 위치가 맞습니까?');
    expect(screen.getByTestId('up-grid-accept')).toBeEnabled();
  });
});

describe('§E.3 검증 사다리 — 무엇을 거절하고 무엇이라 말하는가', () => {
  it('형상 불일치: 두 형상을 숫자로 말한다', async () => {
    await draw({ grid: { onPickGrid: vi.fn(), onSkipGrid: vi.fn() } }, [
      failed(
        'REFERENCE_GRID_MISSING',
        '격자 형상이 데이터와 안 맞는다: 데이터 (2881, 2305) vs 격자 (1200, 1200)',
      ),
    ]);
    const block = await screen.findByTestId('up-grid-block', undefined, { timeout: 4000 });
    expect(block).toHaveTextContent('이 격자는 이 파일의 것이 아닙니다.');
    expect(block).toHaveTextContent('이 파일은 2881 × 2305 이고, 올리신 격자는 1200 × 1200 입니다.');
  });

  it('축 판별 실패: 사람에게 어느 쪽이 위도인지 **묻지 않는다**', async () => {
    await draw({ grid: { onPickGrid: vi.fn(), onSkipGrid: vi.fn() } }, [
      failed(
        'REFERENCE_GRID_MISSING',
        '축을 판별하지 못했다(A.npy / B.npy): 두 배열 모두 값이 ±90 안에 있어 위도와 경도를 구분할 수 없다 — 파일명으로 정하지 않는다',
      ),
    ]);
    const block = await screen.findByTestId('up-grid-block', undefined, { timeout: 4000 });
    expect(block).toHaveTextContent('어느 쪽이 위도이고 어느 쪽이 경도인지 판정하지 못했습니다.');
    expect(screen.queryByTestId('up-grid-axis')).toBeNull();
  });

  it('짝 불일치: 두 형상을 나란히 말한다', async () => {
    await draw({ grid: { onPickGrid: vi.fn(), onSkipGrid: vi.fn() } }, [
      failed('REFERENCE_GRID_MISSING', '위도/경도 형상 불일치(Lat + Lon): (2881, 2305) vs (2881, 1)'),
    ]);
    const block = await screen.findByTestId('up-grid-block', undefined, { timeout: 4000 });
    expect(block).toHaveTextContent('위도 파일과 경도 파일의 크기가 서로 다릅니다.');
    expect(block).toHaveTextContent('2881 × 2305 / 2881 × 1');
  });

  it('경계 위생 실패: 지도형만 만들지 않는다 — 값 미리보기는 남는다', async () => {
    await draw({ grid: { onPickGrid: vi.fn(), onSkipGrid: vi.fn() } }, [
      failed('MAP_BOUNDS_IMPLAUSIBLE', 'bbox 가 한반도 밖'),
    ]);
    const block = await screen.findByTestId('up-grid-block', undefined, { timeout: 4000 });
    expect(block).toHaveTextContent('결과 위치가 한반도 밖으로 나왔습니다');
    expect(screen.getByTestId('up-preview-salvage')).toBeInTheDocument();
  });

  it('렌더 서버 불가: 등록은 그대로 진행할 수 있다고 말한다', async () => {
    const dead: PreviewSource = {
      async palettes() {
        return [{ palette: 'viridis', label: '비리디스' }];
      },
      async createRender() {
        throw new Error('unreachable');
      },
      async getRender() {
        throw new Error('unreachable');
      },
    };
    await draw({ source: dead, grid: { onPickGrid: vi.fn(), onSkipGrid: vi.fn() } });
    const block = await screen.findByTestId('up-grid-block', undefined, { timeout: 4000 });
    expect(block).toHaveTextContent('미리보기를 만드는 서버에 닿지 못했습니다.');
    expect(block).toHaveTextContent('등록은 그대로 진행할 수 있습니다.');
  });
});

describe('§E.0-1 등록은 미리보기에 인질이 아니다 — 상태 기계 수준', () => {
  it('어떤 상태에서도 격자 블록이 등록을 막는 신호를 내지 않는다', () => {
    const cases = [
      { verifying: true },
      { transfer: { sentBytes: 1, totalBytes: 2 } },
      { skipped: true },
      { unreachable: true },
      { failure: { code: 'REFERENCE_GRID_MISSING', details: { detail: '축을 판별하지 못했다(a/b): 두 배열 모두 값이 ±90 안에 있어' } } },
      { failure: { code: 'MAP_BOUNDS_IMPLAUSIBLE', details: { detail: 'x' } } },
    ];
    for (const c of cases) {
      const s = gridState({ hasGrid: true, ...c } as never);
      expect(s).not.toBeNull();
      expect(GRID_COPY[s!.name].blocksRegistration).toBeFalsy();
    }
  });
});
