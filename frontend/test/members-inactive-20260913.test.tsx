/**
 * 구성원 · 권한 표의 **비활성 계정** — 이태헌 1차 검증 `D-4`(카드 ④ ⓐ · 경계 ⓐ-1).
 *
 * 문제 = 계정 관리에서 「비활성」인 사람이 이 표에서는 현역과 똑같이 한 줄로 서고
 * 그 사람의 권한 스위치를 켜고 끌 수 있었다 — 두 화면이 같은 사람을 다르게 말했다.
 *
 * 규율은 바뀌지 않는다 — 화면은 **서버가 실어 준 `editablePermissions` 배열만** 읽고
 * (`permissions.ts` 앵커 `export function isEditable(` · P-31) 여기서 상태로 편집 가능을
 * 계산하지 않는다. 화면이 더하는 것은 **상태 칩과 잠금 이유 한 줄**이다.
 *
 * 대조군 = 같은 표의 활성 연구원 행(편집 가능). 대상 0건 통과를 가른다(spec §8-6 ⑶).
 * 서버 쪽 오라클은 `services/core-api/tests/test_lab_members.py` 가 따로 든다(§8-6 ⑹).
 */
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { MemberPermissionGrid } from '../src/components/members/MemberPermissionGrid';
import type { MembersPort } from '../src/components/members/port';
import { PERMISSION_SWITCHES } from '../src/components/members/permissions';
import type { LabMember } from '../src/components/members/permissions';
import { researcher } from './factories';

const ACTIVE_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AH2';
const INACTIVE_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AH3';

const SWITCHES_ON = {
  '업로드·편집': true,
  '프로젝트 생성': true,
  '승인 위임': false,
  '연구실 설정': false,
};

function seed(): LabMember[] {
  return [
    // 대조군 — 활성 연구원. 서버가 네 열을 편집 가능으로 실어 준다.
    {
      ...researcher(ACTIVE_ID, '호랑이', { ...SWITCHES_ON }),
      accountStatus: 'active',
      editablePermissions: [...PERMISSION_SWITCHES],
    },
    // 대상 — 비활성 계정. 서버가 편집 가능 열을 하나도 실어 주지 않는다.
    {
      ...researcher(INACTIVE_ID, '표범', { ...SWITCHES_ON }),
      accountStatus: 'inactive',
      editablePermissions: [],
    },
  ];
}

function portOf(items: LabMember[]) {
  const save = vi.fn(async () => ({ ok: true as const, items }));
  const port: MembersPort = { list: async () => ({ ok: true, items }), save };
  return { port, save };
}

/** fireEvent 를 쓴다 — user-event 를 새로 들이지 않는다(`members.test.tsx` 와 같은 규율). */
async function click(el: HTMLElement | null) {
  fireEvent.click(el as HTMLElement);
  await Promise.resolve();
}

async function openGrid(items = seed()) {
  const { port, save } = portOf(items);
  render(<MemberPermissionGrid port={port} />);
  await screen.findByRole('table');
  return { save };
}

const rowOf = (who: string) => screen.getByText(who).closest('tr') as HTMLElement;

const cell = (who: string, sw: string) =>
  screen.getByRole('checkbox', { name: `${who} · ${sw}` }) as HTMLInputElement;

describe('구성원 · 권한 — 비활성 계정', () => {
  it('비활성 계정 행에 「비활성」 칩이 선다 — 활성 행에는 없다(대조군)', async () => {
    await openGrid();

    expect(within(rowOf('표범')).getByText('비활성')).toBeTruthy();
    expect(within(rowOf('호랑이')).queryByText('비활성')).toBeNull();
  });

  it('편집 중에도 비활성 행의 스위치 넷이 전부 잠긴다 — 활성 행은 열린다(대조군)', async () => {
    await openGrid();
    await click(screen.getByRole('button', { name: '권한 편집' }));

    for (const sw of PERMISSION_SWITCHES) {
      expect(cell('표범', sw).disabled).toBe(true);
      expect(cell('호랑이', sw).disabled).toBe(false);
    }
  });

  it('잠금 이유를 화면이 말한다', async () => {
    await openGrid();
    await click(screen.getByRole('button', { name: '권한 편집' }));

    expect(screen.getByText('비활성 계정은 권한을 바꿀 수 없어요')).toBeTruthy();
  });

  it('활성 행만 저장 요청에 실린다 — 비활성 행은 요청 자체가 없다', async () => {
    const { save } = await openGrid();
    await click(screen.getByRole('button', { name: '권한 편집' }));
    await click(cell('호랑이', '승인 위임'));
    await click(screen.getByRole('button', { name: '저장' }));
    await click(within(screen.getByRole('dialog')).getByRole('button', { name: '저장' }));

    expect(save).toHaveBeenCalledWith({
      items: [{ accountId: ACTIVE_ID, changes: { '승인 위임': true } }],
    });
  });

  it('상태를 실어 주지 않는 서버 응답도 그대로 선다 — 열쇠는 선택이다', async () => {
    const items = seed().map(({ accountStatus: _drop, ...rest }) => rest as LabMember);
    render(<MemberPermissionGrid port={portOf(items).port} />);

    await waitFor(() => expect(screen.getByText('표범')).toBeTruthy());
    expect(screen.queryByText('비활성')).toBeNull();
  });
});
