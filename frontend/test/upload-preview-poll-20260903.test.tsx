/**
 * 업로드 미리보기 폴링 취소 (`CODE-REVIEW-20260903` 부록 · `upload/PreviewPanel.tsx`).
 *
 * **red 를 먼저 봤다.** 종전 `poll` 은 `clearTimeout` 만 있고 **이미 날아간 조회**를 버릴
 * 방법이 없었다 — 그래서
 *  ⑴ 다시 그리기를 눌러도 옛 렌더의 늦은 응답이 새 렌더의 화면을 덮었고,
 *  ⑵ 화면이 사라진 뒤 도착한 응답이 `그리는 중` 이면 **폴링이 다시 예약**돼 계속 돌았다.
 *
 * ⚠ **중복 제거는 여기서 하지 않는다** — `preview/usePreviewRender` 와의 통합은 유보
 * 항목이다(`CODE-REVIEW-20260903-PLAN §4`). 이 파일은 취소만 잠근다.
 *
 * 이 파일은 `upload.test.tsx`(동시 편집 중인 핫 파일)를 건드리지 않으려고 따로 세웠다.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { PreviewPanel } from '../src/components/upload/PreviewPanel';
import type { PreviewSource, RenderJob } from '../src/components/upload/types';

const UPLOAD_ID = '01JYZ9K7WQ3N8V4M2X6C5B0UP1';
const OLD_ID = '01JYZ9K7WQ3N8V4M2X6C5B0RE1';
const NEW_ID = '01JYZ9K7WQ3N8V4M2X6C5B0RE2';
const LEGEND = { palette: 'viridis', classes: [{ color: '#440154', min: 0, max: 5 }] };

function drawing(renderId: string): RenderJob {
  return { renderId, status: '그리는 중', stage: '지도 그리는 중' } as unknown as RenderJob;
}

function done(renderId: string, badge: string): RenderJob {
  return {
    renderId,
    status: '완료',
    result: {
      imageUrl: `https://viz.example/p/${renderId}.png`,
      legend: LEGEND,
      precisionBadge: badge,
    },
  } as unknown as RenderJob;
}

function deferred<T>() {
  let settle!: (value: T) => void;
  const promise = new Promise<T>((resolve) => {
    settle = resolve;
  });
  return { promise, settle };
}

/** `pollMs` 는 250 이라 대기는 넉넉히 준다 — 느린 호스트에서 흔들리지 않게. */
const WAIT = { timeout: 5000 };

describe('업로드 미리보기 — 옛 폴링이 새 화면을 덮지 않는다', () => {
  it('다시 그리면 옛 렌더의 늦은 응답을 버린다', async () => {
    const late = deferred<RenderJob>();
    let created = 0;
    const source: PreviewSource = {
      palettes: vi.fn(async () => [{ palette: 'viridis', label: '비리디스' }]),
      createRender: vi.fn(async () => drawing(created++ === 0 ? OLD_ID : NEW_ID)),
      getRender: vi.fn((renderId: string) =>
        renderId === OLD_ID ? late.promise : Promise.resolve(done(NEW_ID, '새 렌더')),
      ),
    } as unknown as PreviewSource;

    render(<PreviewPanel source={source} uploadId={UPLOAD_ID} hasReferenceGrid />);
    const draw = await screen.findByTestId('up-preview-draw');

    fireEvent.click(draw); // ① 옛 렌더 — 조회가 붙잡혀 돌아오지 않는다
    await waitFor(() => expect(source.getRender).toHaveBeenCalledWith(OLD_ID), WAIT);

    fireEvent.click(draw); // ② 새 렌더 — 먼저 끝난다
    await waitFor(
      () => expect(screen.getByTestId('up-preview-badge').textContent).toBe('새 렌더'),
      WAIT,
    );

    // 이제 ① 이 완료로 도착한다. **새 화면을 덮으면 안 된다.**
    late.settle(done(OLD_ID, '옛 렌더'));
    await new Promise((r) => setTimeout(r, 50));
    expect(screen.getByTestId('up-preview-badge').textContent).toBe('새 렌더');
    expect(screen.queryByText('옛 렌더')).toBeNull();
  });

  it('화면이 사라진 뒤 도착한 응답은 폴링을 다시 예약하지 않는다', async () => {
    const late = deferred<RenderJob>();
    const source: PreviewSource = {
      palettes: vi.fn(async () => [{ palette: 'viridis', label: '비리디스' }]),
      createRender: vi.fn(async () => drawing(OLD_ID)),
      getRender: vi.fn(() => late.promise),
    } as unknown as PreviewSource;

    const view = render(<PreviewPanel source={source} uploadId={UPLOAD_ID} hasReferenceGrid />);
    fireEvent.click(await screen.findByTestId('up-preview-draw'));
    await waitFor(() => expect(source.getRender).toHaveBeenCalledTimes(1), WAIT);

    view.unmount();
    // 떠난 뒤에 `그리는 중` 이 도착한다 — 종전에는 여기서 다음 조회가 **또** 예약됐다.
    late.settle(drawing(OLD_ID));
    await new Promise((r) => setTimeout(r, 400));

    expect(source.getRender).toHaveBeenCalledTimes(1);
  });
});
