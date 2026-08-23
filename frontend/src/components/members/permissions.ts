// 권한 스위치 4종과 역할 표기 — 값의 정본은 `E-01 Policy_역할과_권한 v1.3` 이다.
// 라벨은 정본 문자열 그대로이며 번역·축약·재배열하지 않는다.
import type { Schemas } from '../../api/client';

export type PermissionSwitch = Schemas['PermissionSwitch'];
export type PermissionSwitchSet = Schemas['PermissionSwitchSet'];
export type LabMember = Schemas['LabMember'];

/**
 * **정확히 네 개다** (§1.3-2 · P-3). 다섯 번째를 만들지 않는다.
 * 순서는 정본 §2 표 · 목업 `구성원 권한 표` 헤더와 같다.
 * 기본값(앞의 둘 켜짐 / 위임 성격인 뒤의 둘 꺼짐)은 계약
 * `common.json#PermissionSwitchSet.default` 가 갖는다 — 여기서 다시 적지 않는다.
 */
export const PERMISSION_SWITCHES = [
  '업로드·편집',
  '프로젝트 생성',
  '승인 위임',
  '연구실 설정',
] as const satisfies readonly PermissionSwitch[];

/** 표의 앞 두 열. 목업 헤더 그대로. */
export const MEMBER_COLUMNS = ['구성원', '역할'] as const;

/**
 * 역할 표기 — 역할과 **받은 위임을 함께** 적는다 (§6 · P-23).
 * 정본이 값을 준 것은 두 위임을 다 받은 연구원 하나뿐이다: `연구원 · 승인·설정 위임`.
 * 한쪽만 받은 연구원의 합성 표기는 **정본에 없어 만들지 않는다** — 역할만 적는다.
 * [정본 무근거] 한쪽 위임만 받은 연구원의 표기.
 */
export function roleLabel(member: LabMember): string {
  if (member.role === '교수') return '교수';
  const both = member.permissions['승인 위임'] === true && member.permissions['연구실 설정'] === true;
  return both ? '연구원 · 승인·설정 위임' : '연구원';
}

/** 이 요청자가 이 칸을 고칠 수 있는가 — **서버가 실어 준 배열만** 읽는다 (P-31). */
export function isEditable(member: LabMember, sw: PermissionSwitch): boolean {
  return member.editablePermissions.includes(sw);
}

export type Draft = Record<string, PermissionSwitchSet>;

export function draftOf(members: readonly LabMember[]): Draft {
  return Object.fromEntries(members.map((m) => [m.accountId, { ...m.permissions }]));
}

/**
 * 바꾼 칸만 모은다 — 손대지 않은 스위치는 키가 없다 (`PermissionSaveRequest.changes`).
 * 켰다가 되돌린 칸은 변경이 아니다.
 */
export function diffOf(
  members: readonly LabMember[],
  draft: Draft,
): Schemas['PermissionSaveRequest']['items'] {
  const items: Schemas['PermissionSaveRequest']['items'] = [];
  for (const m of members) {
    const changes: Record<string, boolean> = {};
    for (const sw of PERMISSION_SWITCHES) {
      const next = draft[m.accountId]?.[sw];
      if (next !== undefined && next !== m.permissions[sw]) changes[sw] = next;
    }
    if (Object.keys(changes).length > 0) items.push({ accountId: m.accountId, changes });
  }
  return items;
}
