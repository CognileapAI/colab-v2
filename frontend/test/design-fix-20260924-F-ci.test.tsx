/**
 * design-fix 20260924 · CI 경합 수정 레인 F-ci (`S-DESIGN-FIX-20260924.md` 「CI 경합 수정 레인 F-ci」).
 *
 * 경합 = 「미리보기 그리기」(`up-preview-draw`)는 `uploadId` 만 있으면 첫 렌더부터 누를 수 있는데
 * 팔레트는 `source.palettes()` 가 끝나야 채워지고, 그 전의 클릭은 `draw()` 첫 줄에서 **조용히** 버려진다.
 * PR #141 CI 두 시도(`thumb-nudge-20260905` 17 · `preview-slot-4x3`)가 둘 다 `idle` 로 멈춘 자리다.
 *
 * 오라클
 *  ① 팔레트가 오기 전에는 버튼이 비활성이다 · 그 사이 클릭은 그리기를 시작하지 않는다
 *  ② 팔레트가 오면 활성이 되고, 누르면 그 팔레트로 그린다
 *  ③ 팔레트가 클릭 시도보다 늦게 와도(강제 지연) 활성화를 기다려 누르면 그려진다
 *  ④ 팔레트를 못 받거나 빈 목록이면 버튼은 비활성이되 **기존 오류·안내 문면**이 이유를 말한다
 *  ⑤ 같은 `draw()` 를 부르는 「짝 파일 없이 그려 보기」(`up-preview-without-grid`)도 ①·②·④ 와 같다
 *     (수정 라운드 · Fable advisor ② 요구)
 */
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { PreviewPanel } from '../src/components/upload/PreviewPanel';
import type { PaletteOption, PreviewSource, RenderJob } from '../src/components/upload/types';
import { clickPreviewDrawWhenReady } from './helpers/previewDraw';

const UPLOAD_ID = '01JYZ9K7WQ3N8V4M2X6C5B0UP1';
const PALETTES: PaletteOption[] = [{ palette: 'viridis', label: '비리디스' }] as PaletteOption[];
const DONE = {
  renderId: '01JYZ9K7WQ3N8V4M2X6C5B0RE1',
  status: '완료',
  result: {
    imageUrl: 'https://viz.example/p/map.png',
    legend: { palette: 'viridis', classes: [{ color: '#440154', min: 0, max: 5 }] },
  },
} as unknown as RenderJob;

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((ok, fail) => {
    resolve = ok;
    reject = fail;
  });
  return { promise, resolve, reject };
}

function source(palettes: () => Promise<PaletteOption[]>) {
  return {
    palettes: vi.fn(palettes),
    createRender: vi.fn(async () => DONE),
    getRender: vi.fn(async () => DONE),
  };
}

function mount(src: ReturnType<typeof source>, hasReferenceGrid = true) {
  return render(
    <PreviewPanel
      source={src as unknown as PreviewSource}
      uploadId={UPLOAD_ID}
      hasReferenceGrid={hasReferenceGrid}
    />,
  );
}

describe('F-ci ① 팔레트 준비 전 「미리보기 그리기」는 비활성이다', () => {
  it('팔레트가 오기 전 버튼은 disabled 이고, 그 사이 클릭은 그리기를 시작하지 않는다', async () => {
    const pal = deferred<PaletteOption[]>();
    const src = source(() => pal.promise);
    mount(src);

    const draw = await screen.findByTestId('up-preview-draw');
    expect(draw).toBeDisabled();

    fireEvent.click(draw);
    await act(async () => {});
    expect(src.createRender).not.toHaveBeenCalled();
    expect(screen.getByTestId('up-preview-slot').getAttribute('data-preview-slot-state')).toBe('idle');
  });

  it('팔레트가 오면 활성이 되고, 누르면 그 팔레트로 그린다', async () => {
    const pal = deferred<PaletteOption[]>();
    const src = source(() => pal.promise);
    mount(src);
    expect(await screen.findByTestId('up-preview-draw')).toBeDisabled();

    await act(async () => {
      pal.resolve(PALETTES);
    });
    await waitFor(() => expect(screen.getByTestId('up-preview-draw')).toBeEnabled());

    await clickPreviewDrawWhenReady();
    await waitFor(() => expect(src.createRender).toHaveBeenCalledTimes(1));
    expect(src.createRender).toHaveBeenLastCalledWith(
      expect.objectContaining({ style: expect.objectContaining({ palette: 'viridis' }) }),
    );
    await waitFor(() => expect(screen.getByTestId('up-preview-image')).toBeTruthy());
  });
});

describe('F-ci ③ 팔레트가 클릭 시도보다 늦게 와도 그려진다 (강제 지연 재현)', () => {
  it('버튼이 서자마자 누르려 해도 활성화를 기다려 누르므로 그림이 선다', async () => {
    // 진단 재현(`zz-forced-late`)과 같은 모양 — 팔레트 확정이 클릭 시도 뒤 20ms 에 도착한다.
    const src = source(async () => {
      await new Promise((r) => setTimeout(r, 20));
      return PALETTES;
    });
    mount(src);

    await clickPreviewDrawWhenReady();
    // 대기 한도는 기본값이다 — 버려진 클릭은 한도를 늘려도 그려지지 않는다(원인은 한도가 아니다).
    await waitFor(() => expect(screen.getByTestId('up-preview-image')).toBeTruthy());
    expect(src.createRender).toHaveBeenCalledTimes(1);
  });
});

describe('F-ci ④ 팔레트를 못 받으면 비활성이되 이유가 화면에 있다 (기존 문면)', () => {
  it('팔레트 조회가 실패하면 버튼은 비활성이고 기존 오류 문면이 선다', async () => {
    const src = source(async () => {
      throw new Error('palettes unavailable');
    });
    mount(src);

    const err = await screen.findByTestId('up-preview-error');
    expect(err.textContent).toContain('지금 미리보기를 만들 수 없어요.');
    expect(screen.getByTestId('up-preview-draw')).toBeDisabled();
  });

  it('팔레트 목록이 비어 있으면 버튼은 비활성이고 기존 팔레트 안내가 선다', async () => {
    const src = source(async () => []);
    mount(src);

    const issue = await screen.findByTestId('up-palette-issue');
    expect(issue.textContent).toContain('팔레트 목록이 예상한 3종과 달라요.');
    expect(screen.getByTestId('up-preview-draw')).toBeDisabled();
  });
});

describe('F-ci ⑤ 「짝 파일 없이 그려 보기」도 팔레트 준비 전 비활성이다 (같은 draw() 경로)', () => {
  const WITHOUT_GRID = 'up-preview-without-grid';

  it('팔레트가 오기 전 disabled 이고, 그 사이 클릭은 그리기를 시작하지 않는다', async () => {
    const pal = deferred<PaletteOption[]>();
    const src = source(() => pal.promise);
    mount(src, false);

    const btn = await screen.findByTestId(WITHOUT_GRID);
    expect(btn).toBeDisabled();

    fireEvent.click(btn);
    await act(async () => {});
    expect(src.createRender).not.toHaveBeenCalled();
  });

  it('팔레트 조회가 실패하면 disabled 이고 기존 오류 문면이 선다', async () => {
    const src = source(async () => {
      throw new Error('palettes unavailable');
    });
    mount(src, false);

    const err = await screen.findByTestId('up-preview-error');
    expect(err.textContent).toContain('지금 미리보기를 만들 수 없어요.');
    expect(screen.getByTestId(WITHOUT_GRID)).toBeDisabled();
  });

  it('팔레트가 오면 활성이 되고, 누르면 withoutReferenceGrid: true 로 그린다', async () => {
    const pal = deferred<PaletteOption[]>();
    const src = source(() => pal.promise);
    mount(src, false);
    expect(await screen.findByTestId(WITHOUT_GRID)).toBeDisabled();

    await act(async () => {
      pal.resolve(PALETTES);
    });
    await waitFor(() => expect(screen.getByTestId(WITHOUT_GRID)).toBeEnabled());

    await clickPreviewDrawWhenReady({ testId: WITHOUT_GRID });
    await waitFor(() => expect(src.createRender).toHaveBeenCalledTimes(1));
    expect(src.createRender).toHaveBeenLastCalledWith(
      expect.objectContaining({
        withoutReferenceGrid: true,
        style: expect.objectContaining({ palette: 'viridis' }),
      }),
    );
  });
});
