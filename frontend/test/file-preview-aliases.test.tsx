import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { FileDropCard } from '../src/components/upload/FileDropCard';

describe('실제 읽기 지원 별칭의 미리보기 안내', () => {
  it.each(['sample.tiff','sample.npy','sample.bin.gz','sample.nc4','sample.h5','sample.hdf5'])('%s를 미지원으로 안내하지 않는다', (name) => {
    render(<FileDropCard picked={[{ file:new File(['fixture'], name), kind:'본체' }]} onPick={() => {}} onKind={() => {}} />);
    expect(screen.getByTestId('up-previewable')).not.toHaveTextContent('지도로 못 그려요');
    expect(screen.getByTestId('up-previewable')).toHaveTextContent('파일 구조');
  });
});
