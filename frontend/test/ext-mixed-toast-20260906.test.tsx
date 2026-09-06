// WU-A13R · PRD-32 ＋ PRD-43 — 확장자 혼합 안내가 **공통 토스트를 탄다**.
//
// PRD-43 축자 — 「이미 요구로 서 있는 토스트 축자 2건은 여기 다시 적지 않는다 … **같은
// 컴포넌트를 쓴다**」. 종전 자리는 인라인 `<p class="up-toast">` 였고 **스스로 사라지지
// 않았다**. 선별 규칙 자체(`keepOneExtension`)는 WU-A13 그대로이고, 여기서 재는 것은
// 「그 안내가 공통 토스트로 뜨는가」 하나다 — 선별 회귀는 `ext-mixed-20260905.test.tsx`.
import { useState } from 'react';
import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { TOAST_DISMISS_MS } from '../src/components/common/Toast';
import { FileDropCard, MIXED_EXTENSION_NOTICE } from '../src/components/upload/FileDropCard';
import type { FileKind, PickedFile } from '../src/components/upload/types';

afterEach(() => {
  vi.useRealTimers();
});

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

describe('WU-A13R — 확장자 혼합 안내는 공통 토스트다', () => {
  it('공손한 알림 구역으로 뜬다 — `role="status"` · `aria-live="polite"`', () => {
    render(<Harness />);
    drop(['a.nc', 'b.tif']);
    const el = screen.getByTestId('up-ext-toast');
    expect(el).toHaveTextContent(MIXED_EXTENSION_NOTICE);
    expect(el).toHaveAttribute('role', 'status');
    expect(el).toHaveAttribute('aria-live', 'polite');
  });

  it('스스로 사라진다 — 종전 인라인 안내는 남아 있었다', () => {
    vi.useFakeTimers();
    render(<Harness />);
    drop(['a.nc', 'b.tif']);
    expect(screen.getByTestId('up-ext-toast')).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(TOAST_DISMISS_MS + 10);
    });
    expect(screen.queryByTestId('up-ext-toast')).toBeNull();
  });

  it('포커스를 뺏지 않는다 — 놓기 인풋에서 포커스가 옮겨 가지 않는다', () => {
    render(<Harness />);
    const input = screen.getByTestId('up-drop-input') as HTMLInputElement;
    input.focus();
    drop(['a.nc', 'b.tif']);
    expect(document.activeElement).toBe(input);
    expect(screen.getByTestId('up-ext-toast')).not.toHaveAttribute('tabindex');
  });
});
