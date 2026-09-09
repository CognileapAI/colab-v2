import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { DatasetPreviewSection } from '../src/components/datasetpreview/DatasetPreviewSection';
import type { DatasetPreviewSource } from '../src/components/datasetpreview/types';
import type { RenderJob } from '../src/components/preview/types';

function source(details: Record<string, unknown>): DatasetPreviewSource {
  const job = { renderId: 'render-one', status: '실패', failure: { code: 'GRID_MISSING', message: '위경도를 담은 짝 파일이 없어요.', details } } as RenderJob;
  return { palettes: async () => [{ palette: 'viridis' }], create: async () => job, get: async () => job,
    mapGeometry: vi.fn(async () => undefined), lookupValue: vi.fn(), probeTile: vi.fn(), screenshot: vi.fn() };
}

describe('상세에서 좌표 없는 값 그림 유지', () => {
  it('지도 실패 안내와 실제 값그림을 함께 표시하고 지도 조작은 제공하지 않는다', async () => {
    const s = source({ thumbnailUrl: '/thumb.webp', valuePreviewUrl: '/values.png', precisionBadge: '격자 없음 — 지도형 보류' });
    render(<DatasetPreviewSection datasetId="data-one" source={s} />);
    const img = await screen.findByRole('img', { name: '데이터 값 미리보기' });
    expect(img).toHaveAttribute('src', '/values.png');
    expect(screen.getByTestId('render-failure')).toHaveTextContent('짝 파일');
    expect(screen.getByRole('status')).toHaveTextContent('불러오는 중');
    fireEvent.load(img);
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
    expect(screen.getByTestId('dt-preview-slot')).toHaveAttribute('data-preview-slot-state', 'failed');
    expect(screen.queryByTestId('preview-cursor-hud')).not.toBeInTheDocument();
    expect(screen.queryByTestId('preview-zoom')).not.toBeInTheDocument();
    expect(screen.queryByTestId('preview-viewport')).not.toBeInTheDocument();
    fireEvent.click(img);
    expect(s.lookupValue).not.toHaveBeenCalled();
    expect(s.mapGeometry).not.toHaveBeenCalled();
  });
  it('썸네일만 남았으면 그것을 보여주고 이미지 오류 후 재시도한다', async () => {
    render(<DatasetPreviewSection datasetId="data-one" source={source({ thumbnailUrl: '/thumb.webp' })} />);
    const img = await screen.findByRole('img', { name: '데이터 썸네일' });
    expect(img).toHaveAttribute('src', '/thumb.webp');
    fireEvent.error(img);
    expect(screen.getByText('값 그림을 불러오지 못했어요.')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '그림 다시 불러오기' }));
    expect(screen.getByRole('status')).toHaveTextContent('불러오는 중');
    fireEvent.load(screen.getByRole('img', { name: '데이터 썸네일' }));
    expect(screen.queryByText('값 그림을 불러오지 못했어요.')).not.toBeInTheDocument();
  });
  it('실패 상세에 이미지 URL이 없으면 그림을 만들어 넣지 않는다', async () => {
    render(<DatasetPreviewSection datasetId="data-one" source={source({})} />);
    await screen.findByTestId('render-failure');
    expect(screen.queryByRole('img')).not.toBeInTheDocument();
  });
});
