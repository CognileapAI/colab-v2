// WU-A13 · PRD-32 확장자 혼합 규칙 — 놓는 순간의 **선별** 규칙이다.
//
// rev1 `H-37` 축자 · Policy `VAL-002` · 시험 `TC-W-001b`.
// 가장 먼저 놓인 파일의 확장자만 남기고 나머지를 뺀다. 비교는 **소문자 기준**이다.
import { useState } from 'react';
import { describe, expect, it } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';

import { FileDropCard } from '../src/components/upload/FileDropCard';
import type { FileKind, PickedFile } from '../src/components/upload/types';

const TOAST = '확장자가 다른 파일은 뺐어요. 한 번에 한 종류만 묶어요';

/** 실제 모달과 같은 결선 — 놓으면 `picked` 에 쌓인다 (`UploadModal.pick`). */
function Harness() {
  const [picked, setPicked] = useState<PickedFile[]>([]);
  return (
    <FileDropCard
      picked={picked}
      onPick={(files) =>
        setPicked((cur) => [...cur, ...files.map((file) => ({ file, kind: '본체' as FileKind }))])
      }
      onKind={() => {}}
    />
  );
}

function drop(names: string[]) {
  const input = screen.getByTestId('up-drop-input') as HTMLInputElement;
  fireEvent.change(input, {
    target: { files: names.map((n) => new File([new Uint8Array(8)], n)) },
  });
}

describe('WU-A13 — 확장자 혼합은 놓는 순간 걸러진다', () => {
  it('`.nc` 3개와 `.tif` 1개를 놓으면 `.nc` 3개만 남고 토스트 축자가 뜬다', () => {
    render(<Harness />);
    drop(['a.nc', 'b.nc', 'c.tif', 'd.nc']);

    // 조각 묶음 요약을 펴서 남은 목록을 직접 센다
    fireEvent.click(screen.getByRole('button', { name: '조각 3개 모두 보기' }));
    const rows = Array.from(screen.getByTestId('up-slices').querySelectorAll('.fn')).map(
      (el) => el.textContent ?? '',
    );
    expect(rows).toEqual(['a.nc', 'b.nc', 'd.nc']);
    expect(rows.some((n) => n.endsWith('.tif'))).toBe(false);

    expect(screen.getByTestId('up-ext-toast')).toHaveTextContent(TOAST);
  });

  it('`.NC` 와 `.nc` 는 같은 종류다 — 둘 다 남고 토스트가 없다', () => {
    render(<Harness />);
    drop(['A.NC', 'b.nc']);

    fireEvent.click(screen.getByRole('button', { name: '조각 2개 모두 보기' }));
    const rows = Array.from(screen.getByTestId('up-slices').querySelectorAll('.fn')).map(
      (el) => el.textContent ?? '',
    );
    expect(rows).toEqual(['A.NC', 'b.nc']);
    expect(screen.queryByTestId('up-ext-toast')).toBeNull();
  });

  it('한 종류만 놓으면 토스트가 뜨지 않는다', () => {
    render(<Harness />);
    drop(['a.nc', 'b.nc', 'c.nc']);
    expect(screen.getByTestId('up-bundle')).toHaveTextContent('조각 3');
    expect(screen.queryByTestId('up-ext-toast')).toBeNull();
  });

  it('먼저 놓은 것의 확장자가 기준이다 — 나중 놓기도 그 기준을 따른다', () => {
    render(<Harness />);
    drop(['first.tif']);
    expect(screen.queryByTestId('up-ext-toast')).toBeNull();

    drop(['later.nc', 'later.tif']);
    fireEvent.click(screen.getByRole('button', { name: '조각 2개 모두 보기' }));
    const rows = Array.from(screen.getByTestId('up-slices').querySelectorAll('.fn')).map(
      (el) => el.textContent ?? '',
    );
    expect(rows).toEqual(['first.tif', 'later.tif']);
    expect(screen.getByTestId('up-ext-toast')).toHaveTextContent(TOAST);
  });
});
