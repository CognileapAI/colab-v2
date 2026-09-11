import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { GridUploadBlock } from '../src/components/upload/GridUploadBlock';

const SOURCE = '01JYZ9K7WQ3N8V4M2X6C5B0DS1';

describe('J-1~J-4 격자 편의 기능', () => {
  it('동일한 격자에는 불일치 경고를 표시하지 않는다', () => {
    render(<GridUploadBlock state={null} transfer={null}
      actions={{ onPickGrid: vi.fn(), onSkipGrid: vi.fn() }}
      options={{ candidates: [], mismatchWarning: { formatDiffers: false, hashDiffers: false, distanceMeters: 0, blocksRegistration: false } }} />);
    expect(screen.queryByTestId('up-grid-mismatch')).toBeNull();
    expect(screen.queryByText('이 파일은 좌표를 자체적으로 갖고 있지 않습니다.')).toBeNull();
  });
  it('기본 후보·예상 영역·비차단 불일치 경고를 서버 값 그대로 보이고 명시적으로 가져온다', () => {
    const reuse = vi.fn();
    render(
      <GridUploadBlock
        state={{ name: '좌표 없음' }}
        transfer={null}
        options={{
          bodyShape: [2, 3],
          currentGrid: {
            gridShape: [2, 3],
            gridDigest: 'new',
            formatSignature: 'float32:lat-lon',
            mapState: '지도 있음',
            expectedBounds: { west: 126, south: 34, east: 130, north: 38 },
          },
          candidates: [{
            datasetId: SOURCE,
            datasetName: '연구실 표준 격자',
            fileNames: ['lat.npy', 'lon.npy'],
            isDefault: true,
            gridShape: [2, 3],
            gridDigest: 'old',
            formatSignature: 'float64:lat-lon',
            mapState: '지도 있음',
          }],
          mismatchWarning: {
            formatDiffers: true,
            hashDiffers: true,
            distanceMeters: null,
            blocksRegistration: false,
          },
        }}
        actions={{ onPickGrid: vi.fn(), onSkipGrid: vi.fn(), onReuseGrid: reuse }}
      />,
    );

    expect(screen.getByText('연구실 기본 격자')).toBeInTheDocument();
    expect(screen.getByText(/연구실 표준 격자/)).toBeInTheDocument();
    expect(screen.getByTestId('up-grid-expected-bounds')).toHaveTextContent('126 · 34 · 130 · 38');
    expect(screen.getByTestId('up-grid-mismatch')).toHaveTextContent('거리 [미상]');
    expect(screen.getByTestId('up-grid-mismatch')).toHaveTextContent('등록을 막지 않아요');
    const button = screen.getByRole('button', { name: '연구실 표준 격자 가져오기' });
    expect(button).not.toBeDisabled();
    fireEvent.click(button);
    expect(reuse).toHaveBeenCalledWith(SOURCE);
  });
});
