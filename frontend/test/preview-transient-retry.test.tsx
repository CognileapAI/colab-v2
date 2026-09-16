import { fireEvent, render, screen, waitFor } from '@testing-library/react';
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
  const { state, resume } = usePreviewRender({ source, renderId: ID, pollMs: 5 });
  return <><div data-testid="phase">{state.phase}</div><button onClick={resume}>resume</button></>;
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

  it('일반 조회 예외도 deadline 안에서는 같은 renderId를 재조회한다', async () => {
    const get = vi.fn().mockRejectedValueOnce(new SyntaxError('bad json')).mockResolvedValueOnce(DONE);
    const source = sourceWith(get);
    render(<Harness source={source} />);
    await waitFor(() => expect(screen.getByTestId('phase')).toHaveTextContent('완료'));
    expect(get).toHaveBeenCalledTimes(2);
    expect(source.create).not.toHaveBeenCalled();
  });

  it('deadline 뒤 결과 불명은 같은 renderId만 수동 재조회한다', async () => {
    vi.spyOn(Date, 'now').mockReturnValueOnce(0).mockReturnValue(31_000);
    const get = vi.fn().mockRejectedValueOnce(new PreviewUnavailable('unknown')).mockResolvedValueOnce(DONE);
    const source = sourceWith(get);
    render(<Harness source={source} />);
    await waitFor(() => expect(screen.getByTestId('phase')).toHaveTextContent('결과 불명'));
    expect(source.create).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'resume' }));
    await waitFor(() => expect(screen.getByTestId('phase')).toHaveTextContent('완료'));
    expect(get).toHaveBeenCalledTimes(2);
    expect(get).toHaveBeenNthCalledWith(1, ID);
    expect(get).toHaveBeenNthCalledWith(2, ID);
    expect(source.create).not.toHaveBeenCalled();
  });

  it('deadline 뒤 일반 예외도 새 create 없이 같은 renderId만 재개한다', async () => {
    vi.spyOn(Date, 'now').mockReturnValueOnce(0).mockReturnValue(31_000);
    const get = vi.fn().mockRejectedValueOnce(new Error('unknown response')).mockResolvedValueOnce(DONE);
    const source = sourceWith(get);
    render(<Harness source={source} />);
    await waitFor(() => expect(screen.getByTestId('phase')).toHaveTextContent('결과 불명'));
    fireEvent.click(screen.getByRole('button', { name: 'resume' }));
    await waitFor(() => expect(screen.getByTestId('phase')).toHaveTextContent('완료'));
    expect(get).toHaveBeenNthCalledWith(1, ID);
    expect(get).toHaveBeenNthCalledWith(2, ID);
    expect(source.create).not.toHaveBeenCalled();
  });
});
