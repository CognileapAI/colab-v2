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
// 규칙 원문 — `vite.config.ts` 의 `test.css.include` 가 `?raw` id 를 허용해야 비지 않는다.
import shellCss from '../src/shell/shell.css?raw';
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

/**
 * 버그 2 (레인 C) 회귀 — `.gnb-settings` 에 `gap` 선언이 없어 아이콘과 「연구실 설정」 글자가
 * 붙어 보였다(bug02). 형제 버튼 `.gnb-upload`·`.avatar` 는 6px, `.labswitch` 는 7px를 갖는다.
 */
describe('버그 2 — 연구실 설정 버튼 아이콘 간격', () => {
  it('.gnb-settings 는 선언값 gap 이 6px 이상이다', () => {
    const acc = account({ '연구실 설정': true });
    renderAt('/lab', acc);
    const btn = screen.getByTestId('gnb-lab-settings');
    expect(btn.classList.contains('gnb-settings')).toBe(true);
    // jsdom 은 `gap` 을 계산값으로 내지 않는다(빈 문자열) — 선언은 규칙 원문으로 잰다.
    const rule = shellCss.match(/\.gnb-settings \{[^}]*\}/)?.[0] ?? '';
    const gap = parseFloat(rule.match(/\bgap:\s*([\d.]+)px/)?.[1] ?? 'NaN');
    expect(gap).toBeGreaterThanOrEqual(6);
  });
});

describe('관리자 전 연구실 보기 — 승인 intent 2026-09-12 운영자 지정', () => {
  it('관리자에게는 연구실 자리에 「전체 연구실」과 읽기 전용 표시가 선다', () => {
    renderAt('/lab', { ...account(), canManageServiceAccounts: true });
    const button = screen.getByTestId('lab-switcher');
    expect(button).toHaveTextContent('전체 연구실');
    expect(button.getAttribute('aria-label')).toContain('읽기 전용');
  });

  /**
   * 회귀 — 종전에는 「(읽기 전용)」이 `aria-label` 안에만 있어 **화면에는 `전체 연구실` 만**
   * 보였다(`dev-package/reports/r-login-backoffice/task8-realuse/results.md §1-7` 실측
   * 「(읽기 전용)」은 눈에 보이지 않는다). 범위 표기는 보조기술 전용 사실이 아니다.
   */
  it('「읽기 전용」이 **보이는 글자**로도 선다 — aria-label 안에만 있지 않다', () => {
    renderAt('/lab', { ...account(), canManageServiceAccounts: true });
    const label = screen.getByTestId('lab-switcher').querySelector('.ln-ro');
    expect(label).not.toBeNull();
    expect(label).toHaveTextContent('읽기 전용');
    // `aria-hidden` 으로 가려 두지 않는다 — 보이는 글자이자 읽히는 글자다.
    expect(label?.getAttribute('aria-hidden')).toBeNull();
  });

  it('관리자가 아니면 그 글자가 아예 없다', () => {
    renderAt('/lab', account());
    expect(screen.getByTestId('lab-switcher').querySelector('.ln-ro')).toBeNull();
  });

  it('관리자가 아니면 종전처럼 소속 연구실 이름만 선다', () => {
    renderAt('/lab', account());
    const button = screen.getByTestId('lab-switcher');
    expect(button).toHaveTextContent('수자원순환연구실');
    expect(button).not.toHaveTextContent('전체 연구실');
  });
});
