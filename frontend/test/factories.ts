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
