import { render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { usePreviewRender } from '../src/components/preview/usePreviewRender';
import { PreviewUnavailable, type PreviewSource, type RenderJob } from '../src/components/preview/types';

const ID = '01JYZ9K7WQ3N8V4M2X6C5B0RE9';
const DONE = {
  renderId: ID,
  status: '완료',
  result: { imageUrl: '/preview.png', legend: { palette: 'viridis', classes: [] } },
} as unknown as RenderJob;

function Harness({ source }: { source: PreviewSource }) {
  const { state } = usePreviewRender({ source, renderId: ID, pollMs: 5 });
  return <div data-testid="phase">{state.phase}</div>;
}

function sourceWith(get: PreviewSource['get']): PreviewSource {
  return {
    get,
    create: vi.fn(),
    probeTile: vi.fn(async () => 'ok' as const),
  };
}

describe('미리보기 일시 503 재조회', () => {
  it('PreviewUnavailable 뒤에는 deadline 안에서 다시 조회해 실제 완료를 받는다', async () => {
    const get = vi.fn()
      .mockRejectedValueOnce(new PreviewUnavailable('잠시 연결할 수 없음'))
      .mockResolvedValueOnce(DONE);
    render(<Harness source={sourceWith(get)} />);

    await waitFor(() => expect(screen.getByTestId('phase').textContent).toBe('완료'));
    expect(get).toHaveBeenCalledTimes(2);
  });

  it('권한·유효성 계열 일반 오류는 재조회하지 않는다', async () => {
    const get = vi.fn().mockRejectedValue(new Error('forbidden'));
    render(<Harness source={sourceWith(get)} />);

    await waitFor(() => expect(screen.getByTestId('phase').textContent).toBe('만들 수 없음'));
    await new Promise((resolve) => setTimeout(resolve, 30));
    expect(get).toHaveBeenCalledTimes(1);
  });
});
