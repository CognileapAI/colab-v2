// ── 축 B: "데이터 잠김 → 노출 + 요청 자리" (P-13) ──────────────────────────────
// 이 파일은 **데이터 접근**만 다룬다. 권한 스위치(축 A)는 PermissionGate.tsx 가 맡는다 — P-14.
//
// 잠긴 데이터는 사라지지 않는다. 이름·요약은 그대로 보이고, 본체가 있던 자리가
// `접근 요청` 이 된다. 같이 숨기면 E-06 접근 요청 흐름 자체가 죽는다 (P-13·P-34).
// 서버도 같은 기준을 쓴다 — 목록·상세는 200 이고 `bodyAccessible: false` 만 다르다 (P-11).
import { LockIndicatorSlot } from '../placeholders/LockIndicatorSlot';

/**
 * `bodyAccessible` 는 서버가 내려주는 값이다. 화면이 계산하지 않는다.
 * - `header`  : 언제나 보인다 (이름·요약 등 메타)
 * - `children`: 본체. 닿을 수 있을 때만 그린다
 * - `request` : 본체 자리를 대신하는 `접근 요청` 자리 — 내용은 WU-P6 이 채운다
 */
export function LockedContent(props: {
  bodyAccessible: boolean;
  header: React.ReactNode;
  children: React.ReactNode;
  request?: React.ReactNode;
}) {
  return (
    <div data-locked={!props.bodyAccessible}>
      {props.header}
      {props.bodyAccessible ? (
        props.children
      ) : (
        <div data-testid="locked-body-slot">
          <LockIndicatorSlot />
          {props.request ?? null}
        </div>
      )}
    </div>
  );
}
