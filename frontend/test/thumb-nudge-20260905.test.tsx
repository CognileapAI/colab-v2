/**
 * WU-A10 · 썸네일 넛지 (PRD-20 · `R-A-3-frontend.md §2`).
 *
 * 수용 기준 두 줄이 오라클이다.
 *  · ② 단계 진입 → 썸네일과 **교체 안내 문구가 읽힌다**
 *  · 썸네일 클릭 → **파일 선택기가 열린다**
 *
 * ⛔ 저장 경로는 이 WU 밖이다(별건 `WU-C2`). 고른 그림은 화면에서만 보이고
 *    `representative_file_id` 로 나가지 않는다 — 그 사실도 여기서 지킨다.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { PreviewPanel } from '../src/components/upload/PreviewPanel';
import type { PreviewSource } from '../src/components/upload/types';

const UPLOAD_ID = '01JYZ9K7WQ3N8V4M2X6C5B0UP1';

/** 넛지 문면 — 정본 문구다. 여기서 새로 짓지 않는다. */
const NUDGE = '눌러서 다른 그림으로 바꿀 수 있어요';

function source(): PreviewSource {
  return {
    async palettes() {
      return [{ palette: 'viridis', label: '비리디스' }];
    },
    async createRender() {
      throw new Error('이 시험은 그리지 않는다');
    },
    async getRender() {
      throw new Error('이 시험은 그리지 않는다');
    },
  } as unknown as PreviewSource;
}

async function mount() {
  const view = render(
    <PreviewPanel source={source()} uploadId={UPLOAD_ID} hasReferenceGrid={false} />,
  );
  await screen.findByTestId('up-preview-draw');
  return view;
}

describe('WU-A10 대표 그림(썸네일) 넛지', () => {
  it('② 단계에 들어오면 썸네일 자리와 교체 안내가 함께 읽힌다', async () => {
    await mount();
    expect(await screen.findByTestId('up-thumb-block')).toBeTruthy();
    expect(screen.getByTestId('up-thumb-pick')).toBeTruthy();
    expect(screen.getByTestId('up-thumb-nudge').textContent).toContain(NUDGE);
  });

  it('썸네일을 누르면 파일 선택기가 열린다', async () => {
    await mount();
    const input = screen.getByTestId('up-thumb-input') as HTMLInputElement;
    expect(input.type).toBe('file');
    expect(input.accept).toBe('image/*');
    const click = vi.spyOn(input, 'click');

    fireEvent.click(screen.getByTestId('up-thumb-pick'));

    expect(click).toHaveBeenCalledTimes(1);
  });

  it('고른 그림은 화면에서만 바뀐다 — 저장 경로를 만들지 않는다', async () => {
    const url = vi.fn(() => 'blob:local/thumb');
    vi.stubGlobal('URL', { ...URL, createObjectURL: url, revokeObjectURL: vi.fn() });
    await mount();
    const input = screen.getByTestId('up-thumb-input') as HTMLInputElement;

    const file = new File([new Uint8Array([1, 2, 3])], 'cover.png', { type: 'image/png' });
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() =>
      expect(screen.getByTestId('up-thumb-img').getAttribute('src')).toBe('blob:local/thumb'),
    );
    expect(url).toHaveBeenCalledTimes(1);
    vi.unstubAllGlobals();
  });
});
