/**
 * 연구실 설정 > 구성원 · 권한 — 권한 스위치를 고치는 **유일한 자리**(P-18).
 * 오라클은 정본이다: `E-01 Policy_역할과_권한 v1.3` §1.3-2 · §3 · §4 · §6,
 * 문안은 `mockups/제품_260817.html` 의 S-07 `구성원 · 권한` 카드에서 한 자도 바꾸지 않고 가져왔다.
 */
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { LabSettingsPage } from '../src/routes/LabSettingsPage';
import type { MembersPort } from '../src/components/members/port';
import { PERMISSION_SWITCHES } from '../src/components/members/permissions';
import type { PermissionSwitch } from '../src/components/members/permissions';
import { professor, researcher } from './factories';

/** 목업 시나리오 그대로 — 교수 1 · 연구원 4. `호랑이` 는 두 위임을 다 받았다. */
function seed() {
  return [
    professor('01JYZ9K7WQ3N8V4M2X6C5B0AH1', '사자 교수'),
    researcher('01JYZ9K7WQ3N8V4M2X6C5B0AH2', '호랑이', {
      '업로드·편집': true,
      '프로젝트 생성': true,
      '승인 위임': true,
      '연구실 설정': true,
    }),
    researcher('01JYZ9K7WQ3N8V4M2X6C5B0AH3', '표범', {
      '업로드·편집': true,
      '프로젝트 생성': true,
      '승인 위임': false,
      '연구실 설정': false,
    }),
  ];
}

/** 교수 눈으로 본 격자 — 연구원 행의 네 열이 모두 편집 가능하다. */
function asProfessor(items = seed()) {
  return items.map((m) =>
    m.role === '교수' ? m : { ...m, editablePermissions: [...PERMISSION_SWITCHES] },
  );
}

/** `연구실 설정` 위임자 눈 — 서버가 두 열만 실어 준다 (P-31). */
function asDelegate(items = seed()) {
  return items.map((m) =>
    m.role === '교수'
      ? m
      : { ...m, editablePermissions: ['업로드·편집', '프로젝트 생성'] as PermissionSwitch[] },
  );
}

function portOf(items: ReturnType<typeof seed>, saved?: ReturnType<typeof seed>) {
  const save = vi.fn(async () => ({ ok: true as const, items: saved ?? items }));
  const port: MembersPort = {
    list: async () => ({ ok: true, items }),
    save,
  };
  return { port, save };
}

/** fireEvent 를 쓴다 — user-event 를 새로 들이지 않는다(의존성 추가에 근거가 없다). */
async function click(el: HTMLElement | null) {
  fireEvent.click(el as HTMLElement);
  // 저장 응답처럼 비동기 갱신이 걸린 클릭을 flush 한다
  await Promise.resolve();
}

async function openGrid(port: MembersPort) {
  render(<LabSettingsPage port={port} />);
  await click(screen.getByRole('tab', { name: '구성원 · 권한' }));
  await screen.findByRole('table');
}

const cell = (who: string, sw: string) =>
  screen.getByRole('checkbox', { name: `${who} · ${sw}` }) as HTMLInputElement;

describe('스위치는 정확히 네 개다 (P-3)', () => {
  it('열 이름이 정본 문자열 그대로이고 다섯 번째 열이 없다', async () => {
    await openGrid(portOf(asProfessor()).port);
    const head = within(screen.getByRole('table')).getAllByRole('columnheader');
    expect(head.map((h) => h.textContent)).toEqual([
      '구성원',
      '역할',
      '업로드·편집',
      '프로젝트 생성',
      '승인 위임',
      '연구실 설정',
    ]);
  });
});

describe('교수 행은 켜진 채로 고정돼 끌 수 없다 (§3 · P-5)', () => {
  it('편집 모드에서도 교수 행 네 칸은 켜짐 + 편집 불가다', async () => {
    await openGrid(portOf(asProfessor()).port);
    await click(screen.getByRole('button', { name: '권한 편집' }));
    for (const sw of PERMISSION_SWITCHES) {
      const box = cell('사자 교수', sw);
      expect(box.checked).toBe(true);
      expect(box.disabled).toBe(true);
    }
  });
});

describe('재위임 금지는 서버가 말한다 — 화면은 editablePermissions 를 따른다 (P-31)', () => {
  it('위임자에게 두 열은 값은 보이되 편집 불가다 — 숨기지 않는다', async () => {
    await openGrid(portOf(asDelegate()).port);
    await click(screen.getByRole('button', { name: '권한 편집' }));
    expect(cell('표범', '업로드·편집').disabled).toBe(false);
    expect(cell('표범', '프로젝트 생성').disabled).toBe(false);
    const locked = cell('표범', '승인 위임');
    expect(locked).toBeInTheDocument();
    expect(locked.disabled).toBe(true);
    expect(cell('표범', '연구실 설정').disabled).toBe(true);
  });

  it('화면이 규칙을 스스로 계산하지 않는다 — 서버가 네 열을 주면 네 열이 열린다', async () => {
    await openGrid(portOf(asProfessor()).port);
    await click(screen.getByRole('button', { name: '권한 편집' }));
    expect(cell('표범', '승인 위임').disabled).toBe(false);
  });
});

describe('실시간 저장이 아니다 — 편집 → 저장 → 확인 모달 (§3 · P-19)', () => {
  it('확인 모달의 저장을 누르기 전에는 요청이 한 번도 나가지 않는다', async () => {
    const { port, save } = portOf(asProfessor());
    await openGrid(port);
    await click(screen.getByRole('button', { name: '권한 편집' }));
    await click(cell('표범', '승인 위임'));
    expect(save).not.toHaveBeenCalled();
    await click(screen.getByRole('button', { name: '저장' }));
    expect(save).not.toHaveBeenCalled();
    expect(screen.getByRole('dialog', { name: '권한을 이렇게 바꿀까요?' })).toBeInTheDocument();
    await click(within(screen.getByRole('dialog')).getByRole('button', { name: '저장' }));
    expect(save).toHaveBeenCalledTimes(1);
  });

  it('한 요청에 바뀐 칸만 모아 싣는다 — 손대지 않은 스위치는 키가 없다', async () => {
    const { port, save } = portOf(asProfessor());
    await openGrid(port);
    await click(screen.getByRole('button', { name: '권한 편집' }));
    await click(cell('표범', '승인 위임'));
    await click(cell('호랑이', '업로드·편집'));
    await click(screen.getByRole('button', { name: '저장' }));
    await click(within(screen.getByRole('dialog')).getByRole('button', { name: '저장' }));
    expect(save).toHaveBeenCalledWith({
      items: [
        { accountId: '01JYZ9K7WQ3N8V4M2X6C5B0AH2', changes: { '업로드·편집': false } },
        { accountId: '01JYZ9K7WQ3N8V4M2X6C5B0AH3', changes: { '승인 위임': true } },
      ],
    });
  });

  it('켰다가 되돌린 칸은 변경이 아니다 — 요청에 실리지 않는다', async () => {
    const { port, save } = portOf(asProfessor());
    await openGrid(port);
    await click(screen.getByRole('button', { name: '권한 편집' }));
    await click(cell('표범', '승인 위임'));
    await click(cell('표범', '승인 위임'));
    await click(screen.getByRole('button', { name: '저장' }));
    expect(screen.queryByRole('dialog')).toBeNull();
    expect(save).not.toHaveBeenCalled();
    expect(screen.getByText('바뀐 권한이 없어요')).toBeInTheDocument();
  });

  it('확인 모달의 취소는 편집 모드를 유지한다 — 저장만 물린 것이다 (P-20)', async () => {
    const { port, save } = portOf(asProfessor());
    await openGrid(port);
    await click(screen.getByRole('button', { name: '권한 편집' }));
    await click(cell('표범', '승인 위임'));
    await click(screen.getByRole('button', { name: '저장' }));
    await click(within(screen.getByRole('dialog')).getByRole('button', { name: '취소' }));
    expect(screen.queryByRole('dialog')).toBeNull();
    expect(save).not.toHaveBeenCalled();
    expect(cell('표범', '승인 위임').disabled).toBe(false);
    expect(cell('표범', '승인 위임').checked).toBe(true);
  });

  it('편집 취소는 원래 값으로 되돌린다 (§3)', async () => {
    await openGrid(portOf(asProfessor()).port);
    await click(screen.getByRole('button', { name: '권한 편집' }));
    await click(cell('표범', '승인 위임'));
    await click(screen.getByRole('button', { name: '취소' }));
    expect(cell('표범', '승인 위임').checked).toBe(false);
    expect(cell('표범', '승인 위임').disabled).toBe(true);
    expect(screen.getByRole('button', { name: '권한 편집' })).toBeInTheDocument();
  });

  it('편집 중에는 바뀐 칸에 표식만 남는다 — 토스트를 띄우지 않는다 (P-20)', async () => {
    await openGrid(portOf(asProfessor()).port);
    await click(screen.getByRole('button', { name: '권한 편집' }));
    await click(cell('표범', '승인 위임'));
    expect(cell('표범', '승인 위임').closest('td')).toHaveClass('is-chg');
    expect(cell('표범', '업로드·편집').closest('td')).not.toHaveClass('is-chg');
    expect(screen.queryByTestId('members-toast')).toBeNull();
  });

  it('저장 응답이 곧 새 화면이다 — 서버가 돌려준 목록으로 다시 그린다', async () => {
    const after = asProfessor().map((m) =>
      m.name === '표범'
        ? { ...m, permissions: { ...m.permissions, '승인 위임': true, '업로드·편집': false } }
        : m,
    );
    const { port } = portOf(asProfessor(), after);
    await openGrid(port);
    await click(screen.getByRole('button', { name: '권한 편집' }));
    await click(cell('표범', '승인 위임'));
    await click(screen.getByRole('button', { name: '저장' }));
    await click(within(screen.getByRole('dialog')).getByRole('button', { name: '저장' }));
    await waitFor(() => expect(cell('표범', '업로드·편집').checked).toBe(false));
    expect(cell('표범', '승인 위임').checked).toBe(true);
    expect(screen.getByRole('button', { name: '권한 편집' })).toBeInTheDocument();
  });
});

describe('역할 표기는 받은 위임을 함께 적는다 (§6 · P-23)', () => {
  it('두 위임을 다 받은 연구원은 `연구원 · 승인·설정 위임`', async () => {
    await openGrid(portOf(asProfessor()).port);
    expect(screen.getByText('연구원 · 승인·설정 위임')).toBeInTheDocument();
    expect(screen.getAllByText('연구원').length).toBe(1);
    expect(screen.getByText('교수')).toBeInTheDocument();
  });
});

describe('막힌 것은 서버가 말한다 (P-11)', () => {
  it('403 이면 서버 문안을 그대로 보이고 화면이 스스로 문장을 만들지 않는다', async () => {
    const port: MembersPort = {
      list: async () => ({ ok: true, items: asDelegate() }),
      save: async () => ({ ok: false, message: '위임은 재위임되지 않아요' }),
    };
    await openGrid(port);
    await click(screen.getByRole('button', { name: '권한 편집' }));
    await click(cell('표범', '업로드·편집'));
    await click(screen.getByRole('button', { name: '저장' }));
    await click(within(screen.getByRole('dialog')).getByRole('button', { name: '저장' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('위임은 재위임되지 않아요');
    expect(cell('표범', '업로드·편집').disabled).toBe(false);
  });
});
