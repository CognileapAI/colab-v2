// ── 축 A: "권한 없음 → 숨김" (P-12) ─────────────────────────────────────────────
// 이 파일은 **권한 스위치**만 다룬다. 데이터 잠김(축 B)은 LockedContent.tsx 가 맡는다.
// 두 축을 한 메커니즘으로 합치지 않는다 — P-14.
//
// 비활성 버튼·경고 토스트를 만들지 않는다. 꺼진 것은 DOM 에서 사라진다.
// 규칙 본체(어느 행동이 어느 스위치인가)는 WU-P6 이 채운다. 여기서는 틀만 둔다.
import type { PermissionSwitch } from '../api/client';
import { useAccount } from './session';

/** 서버가 실어 준 스위치 값을 읽기만 한다. 역할에서 유도하지 않는다 (P-6). */
export function useHasPermission(name: PermissionSwitch): boolean {
  const account = useAccount();
  return account?.permissions?.[name] === true;
}

/** 스위치가 꺼져 있으면 아무것도 그리지 않는다 (P-12). */
export function PermissionGate(props: {
  requires: PermissionSwitch;
  children: React.ReactNode;
}) {
  return useHasPermission(props.requires) ? <>{props.children}</> : null;
}

/**
 * 스위치가 아니라 **서버가 건별로 판정해 내려준 값**(`actions.*` · `canEdit` · `canManage`)으로
 * 숨기는 자리. 화면이 조건을 임의로 정하지 않는다 (P-7).
 */
export function ActionGate(props: { allowed: boolean | undefined; children: React.ReactNode }) {
  return props.allowed === true ? <>{props.children}</> : null;
}
