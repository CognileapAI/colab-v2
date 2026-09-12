// ── 축 A: "권한 없음 → 숨김" (P-12) ─────────────────────────────────────────────
// 이 파일은 **권한 스위치**만 다룬다. 데이터 잠김(축 B)은 LockedContent.tsx 가 맡는다.
// 두 축을 한 메커니즘으로 합치지 않는다 — P-14.
//
// 비활성 버튼·경고 토스트를 만들지 않는다. 꺼진 것은 DOM 에서 사라진다.
// 규칙 본체(어느 행동이 어느 스위치인가)는 WU-P6 이 채운다. 여기서는 틀만 둔다.
import { createContext, useContext } from 'react';
import type { PermissionSwitch } from '../api/client';
import { useAccount } from './session';

/**
 * ⭑ **⟨신설 2026-09-13 · 승인 intent `2026-09-12-operator-designation.md`⟩ 읽기 전용 구역.**
 *
 * 축 A(권한 스위치)·축 B(데이터 잠김)와 **세 번째 축**이다 — 스위치는 켜져 있고 데이터도
 * 잠기지 않았는데 **그 행이 내 연구실 것이 아니라** 쓰기가 성립하지 않는 자리다. 관리자는
 * 모든 연구실을 읽고 쓰기는 소속 연구실 그대로이므로(같은 intent), 남의 연구실 화면에서는
 * 이 구역이 켜지고 쓰기 진입점이 **DOM 에서 사라진다**(P-12 — 비활성이 아니라 부재).
 *
 * ⚠ **방어선이 아니다.** 서버가 이미 403·404 로 거절하고
 * (`services/core-api/tests/test_operator_designation.py` ㈒), 이 구역은 **없는 길을 화면에
 * 그리지 않기 위한 것**이다. 화면을 고쳐 서버 판정을 대신하지 않는다.
 */
const ReadOnlyScope = createContext(false);

/** 이 구역 안의 쓰기 진입점을 전부 없앤다. `readOnly` 가 거짓이면 아무것도 바뀌지 않는다. */
export function ReadOnlyScopeProvider(props: { readOnly: boolean; children: React.ReactNode }) {
  return <ReadOnlyScope.Provider value={props.readOnly}>{props.children}</ReadOnlyScope.Provider>;
}

/** 읽기 전용 구역 안인가. 서버가 내려준 판정값과 **함께** 쓴다(둘 중 하나라도 꺼지면 숨긴다). */
export function useReadOnlyScope(): boolean {
  return useContext(ReadOnlyScope);
}

/** 서버가 실어 준 스위치 값을 읽기만 한다. 역할에서 유도하지 않는다 (P-6). */
export function useHasPermission(name: PermissionSwitch): boolean {
  const account = useAccount();
  const readOnly = useReadOnlyScope();
  return !readOnly && account?.permissions?.[name] === true;
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
 *
 * ⭑ **읽기 전용 구역 안에서는 서버 값이 참이어도 숨긴다.** 남의 연구실 데이터셋의 `다운로드`
 * 는 서버가 404 로 거절하고(`_EXPORT_TAIL` — 열람과 반출은 다른 일이다), `승인 요청`·
 * `접근 요청` 도 소속 연구실 밖에서는 서지 않는다. 서버 `actions` 가 아직 그 경계를 말하지
 * 않으므로(후속 항목) 여기서 **없는 길을 그리지 않는다**.
 */
export function ActionGate(props: { allowed: boolean | undefined; children: React.ReactNode }) {
  const readOnly = useReadOnlyScope();
  return !readOnly && props.allowed === true ? <>{props.children}</> : null;
}
