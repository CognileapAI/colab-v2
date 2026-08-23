// 테스트용 계정 — 타입은 생성물에서 온다. 형태를 손으로 다시 선언하지 않는다.
import type { CurrentAccount, PermissionSwitchSet } from '../src/api/client';

export const ALL_OFF: PermissionSwitchSet = {
  '업로드·편집': false,
  '프로젝트 생성': false,
  '승인 위임': false,
  '연구실 설정': false,
};

export function account(permissions: Partial<PermissionSwitchSet> = {}): CurrentAccount {
  return {
    accountId: '01JYZ9K7WQ3N8V4M2X6C5B0AHT',
    name: '호랑이',
    email: 'tiger@example.ac.kr',
    role: '연구원',
    permissions: { ...ALL_OFF, ...permissions } as PermissionSwitchSet,
    labId: '01JYZ9K7WQ3N8V4M2X6C5B0AHU',
    labName: '수자원순환연구실',
  };
}

// ── 구성원 · 권한 격자 (P1-fe-members) ───────────────────────────────────────
import type { Schemas } from '../src/api/client';

export type LabMember = Schemas['LabMember'];

/** 교수 행은 네 스위치가 켜진 채로 내려오고 편집 가능 열이 비어 있다 (P-5). */
export function professor(accountId: string, name: string): LabMember {
  return {
    accountId,
    name,
    email: `${accountId.toLowerCase()}@example.ac.kr`,
    role: '교수',
    permissions: {
      '업로드·편집': true,
      '프로젝트 생성': true,
      '승인 위임': true,
      '연구실 설정': true,
    },
    editablePermissions: [],
  };
}

/** editablePermissions 는 시험이 서버 역할로 채운다 — 화면이 계산하지 않는다 (P-31). */
export function researcher(
  accountId: string,
  name: string,
  permissions: Schemas['PermissionSwitchSet'],
): LabMember {
  return {
    accountId,
    name,
    email: `${accountId.toLowerCase()}@example.ac.kr`,
    role: '연구원',
    permissions,
    editablePermissions: [],
  };
}
