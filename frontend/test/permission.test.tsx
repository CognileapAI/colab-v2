/**
 * 권한 게이트 틀 — 두 축이 **서로 다른 처리**임을 회귀로 묶는다 (P-14).
 *   축 A: 권한 없음 → 숨김 (P-12)          — PermissionGate / ActionGate
 *   축 B: 데이터 잠김 → 노출 + 요청 자리 (P-13) — LockedContent
 */
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { AppRoutes } from '../src/app/routes';
import { SessionProvider } from '../src/permission/session';
import { PermissionGate, ActionGate } from '../src/permission/PermissionGate';
import { LockedContent } from '../src/permission/LockedContent';
import { account } from './factories';
import type { CurrentAccount } from '../src/api/client';

function withSession(acc: CurrentAccount | null, node: React.ReactNode) {
  return render(<SessionProvider account={acc}>{node}</SessionProvider>);
}

describe('축 A — 권한 없음은 숨긴다 (P-12)', () => {
  it('스위치가 꺼지면 DOM 에서 사라진다 — 비활성 버튼을 남기지 않는다', () => {
    withSession(
      account({ '업로드·편집': false }),
      <PermissionGate requires="업로드·편집">
        <button type="button">업로드</button>
      </PermissionGate>,
    );
    expect(screen.queryByRole('button')).toBeNull();
  });

  it('스위치가 켜지면 보인다', () => {
    withSession(
      account({ '업로드·편집': true }),
      <PermissionGate requires="업로드·편집">
        <button type="button">업로드</button>
      </PermissionGate>,
    );
    expect(screen.getByRole('button', { name: '업로드' })).toBeInTheDocument();
  });

  it('세션이 아직 없으면 전부 꺼진 것으로 본다 (fail-closed)', () => {
    withSession(
      null,
      <PermissionGate requires="업로드·편집">
        <button type="button">업로드</button>
      </PermissionGate>,
    );
    expect(screen.queryByRole('button')).toBeNull();
  });

  it('ActionGate 는 서버가 내려준 판정값만 읽는다 — 화면이 조건을 정하지 않는다 (P-7)', () => {
    const { rerender } = render(
      <ActionGate allowed={false}>
        <button type="button">삭제</button>
      </ActionGate>,
    );
    expect(screen.queryByRole('button')).toBeNull();
    rerender(
      <ActionGate allowed={true}>
        <button type="button">삭제</button>
      </ActionGate>,
    );
    expect(screen.getByRole('button', { name: '삭제' })).toBeInTheDocument();
  });

  it('GNB 우측 버튼은 스위치로 갈린다 — 꺼진 사람에겐 아예 없다', () => {
    const view = render(
      <MemoryRouter initialEntries={['/lab']}>
        <SessionProvider account={account()}>
          <AppRoutes />
        </SessionProvider>
      </MemoryRouter>,
    );
    expect(view.queryByTestId('gnb-upload')).toBeNull();
    expect(view.queryByTestId('gnb-lab-settings')).toBeNull();
    view.unmount();

    const view2 = render(
      <MemoryRouter initialEntries={['/lab']}>
        <SessionProvider account={account({ '업로드·편집': true, '연구실 설정': true })}>
          <AppRoutes />
        </SessionProvider>
      </MemoryRouter>,
    );
    expect(view2.getByTestId('gnb-upload')).toBeInTheDocument();
    expect(view2.getByTestId('gnb-lab-settings')).toBeInTheDocument();
  });
});

describe('축 B — 잠긴 데이터는 숨기지 않는다 (P-13)', () => {
  it('본체가 막혀도 이름·요약은 보이고 그 자리가 접근 요청이 된다', () => {
    render(
      <LockedContent
        bodyAccessible={false}
        header={<h1>낙동강 강우 2025</h1>}
        request={<button type="button">접근 요청</button>}
      >
        <div>본체</div>
      </LockedContent>,
    );
    expect(screen.getByRole('heading', { name: '낙동강 강우 2025' })).toBeInTheDocument();
    expect(screen.queryByText('본체')).toBeNull();
    expect(screen.getByRole('button', { name: '접근 요청' })).toBeInTheDocument();
    expect(screen.getByTestId('locked-body-slot')).toBeInTheDocument();
  });

  it('닿을 수 있으면 본체가 그대로 나오고 잠금 자리는 없다', () => {
    render(
      <LockedContent bodyAccessible={true} header={<h1>낙동강 강우 2025</h1>}>
        <div>본체</div>
      </LockedContent>,
    );
    expect(screen.getByText('본체')).toBeInTheDocument();
    expect(screen.queryByTestId('locked-body-slot')).toBeNull();
  });
});

describe('P-14 — 두 축을 섞지 않는다', () => {
  it('권한 스위치가 전부 꺼져 있어도 잠기지 않은 데이터는 그대로 보인다', () => {
    withSession(
      account(),
      <LockedContent bodyAccessible={true} header={<h1>이름</h1>}>
        <div>본체</div>
      </LockedContent>,
    );
    expect(screen.getByText('본체')).toBeInTheDocument();
  });

  it('권한 스위치가 전부 켜져 있어도 잠긴 데이터의 본체는 열리지 않는다', () => {
    withSession(
      account({ '업로드·편집': true, '프로젝트 생성': true, '승인 위임': true, '연구실 설정': true }),
      <LockedContent bodyAccessible={false} header={<h1>이름</h1>}>
        <div>본체</div>
      </LockedContent>,
    );
    expect(screen.queryByText('본체')).toBeNull();
    expect(screen.getByRole('heading', { name: '이름' })).toBeInTheDocument();
  });
});
