/**
 * 완료 판정 #7 (sessions/P0.md §5) 회귀 —
 *   ① GNB 첫 탭이 `연구실` 이다
 *   ② 비워 둘 자리 3곳이 렌더된다
 */
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { AppRoutes } from '../src/app/routes';
import { SessionProvider } from '../src/permission/session';
import { MAIN_NAV } from '../src/shell/nav';
import { account } from './factories';
import type { CurrentAccount } from '../src/api/client';

function renderAt(path: string, acc: CurrentAccount | null = account()) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <SessionProvider account={acc}>
        <AppRoutes />
      </SessionProvider>
    </MemoryRouter>,
  );
}

describe('완료 판정 #7 — GNB 첫 탭', () => {
  it('주 내비는 정본 순서 그대로 세 탭이고 첫 탭은 `연구실` 이다', () => {
    expect(MAIN_NAV.map((t) => t.label)).toEqual(['연구실', '프로젝트', '데이터셋']);
  });

  it('렌더된 GNB 의 첫 번째 탭 글자가 `연구실` 이다 (`홈` 이 아니다)', () => {
    renderAt('/lab');
    const tabs = screen.getByRole('navigation', { name: '주 내비' }).querySelectorAll('a');
    expect(tabs).toHaveLength(3);
    expect(tabs[0]).toHaveTextContent('연구실');
    expect(screen.queryByText('홈')).toBeNull();
  });

  it('GNB 하이라이트는 화면 주인 탭에 고정된다', () => {
    renderAt('/datasets');
    const tabs = screen.getByRole('navigation', { name: '주 내비' }).querySelectorAll('a');
    expect(tabs[0]).not.toHaveClass('is-active');
    expect(tabs[2]).toHaveClass('is-active');
  });
});

describe('완료 판정 #7 — 비워 둘 자리 3곳', () => {
  it('할 일 함 자리가 `연구실` 화면에 있다', () => {
    const { container } = renderAt('/lab');
    expect(container.querySelector('[data-slot="todo-inbox"]')).not.toBeNull();
  });

  it('Verified 배지 자리와 잠금 표시 자리가 카탈로그에 있다', () => {
    const { container } = renderAt('/datasets');
    expect(container.querySelector('[data-slot="verified-badge"]')).not.toBeNull();
    expect(container.querySelector('[data-slot="lock-indicator"]')).not.toBeNull();
  });
});
