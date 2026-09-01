// S-01 연구실 대시보드(WU-P7)가 부르는 것들. 값 타입은 전부 계약 생성물에서 온다 —
// 여기서 다시 선언하지 않는다 (`CLAUDE.md §3-6·§3-7`).
//
// **판정은 하나도 여기 없다.** 어느 그룹이 보이는지는 서버가 정한다 — 할 일 함의 승인 계열
// 두 목록은 권한이 없으면 **403** 이고(계약 `listPendingAccessRequests` ·
// `listPendingVerificationRequests`), 화면은 그 403 을 「그룹이 통째로 없다」로 읽는다
// (`Policy_홈_대시보드 §6` 축자 「처리할 수 없는 그룹은 통째로 없다」 · P-7).
// 역할로 유도하지 않는다 — 화면이 역할을 보고 그리면 서버와 두 곳에서 갈라진다 (P-6).
import type { components } from '../../generated/fe-core';

type S = components['schemas'];

export type DashboardSummary = S['DashboardSummary'];
export type DataMap = S['DataMap'];
export type Activity = S['Activity'];
export type Lab = S['Lab'];
export type AccessRequest = S['AccessRequest'];
export type VerificationRequest = S['VerificationRequest'];
export type LineageState = S['LineageState'];

/** 계보 확인 그룹 한 줄 — 데이터 이름과 **왜 확인해야 하는지** (`§5` 할 일 함 항목). */
export type LineageTodo = {
  datasetId: string;
  name: string;
  /** `확인 필요` 인가 `기록 없음` 인가. 이유 문장은 이 값에서 나온다 — 화면이 지어내지 않는다. */
  lineageState: LineageState;
};

/**
 * 권한이 없어 **그룹이 통째로 없는** 경우. 서버의 403 을 그대로 옮긴 값이고,
 * 화면은 이것을 「빈 그룹」과 구별한다 — 빈 그룹으로 남기면 처리 권한이 있는 줄 알고
 * 기다리게 된다 (`§6` 축자).
 */
export class GroupHidden extends Error {}

/**
 * 대시보드를 채우는 곳. 실서버와 시험 대역이 **같은 얼굴**을 쓴다
 * (`components/detail/types.ts` 의 `DetailSource` 와 같은 무늬).
 */
export interface DashboardSource {
  summary(): Promise<DashboardSummary>;
  dataMap(): Promise<DataMap>;
  /** 최근 활동 — **연구실 활동만**. 내 열람은 서버에 없다 (`§10`). */
  activities(): Promise<Activity[]>;
  /** 연구실 정보 읽기 — **전 구성원**이 읽는다 (`§6`). */
  lab(): Promise<Lab>;
  /** 계보 확인 그룹 — 전 구성원. `확인 필요` + `기록 없음` 이다 (`§4` 용어 정의). */
  lineageTodo(): Promise<LineageTodo[]>;
  /** Verified 검토 대기 — 교수만. 권한이 없으면 `GroupHidden` 을 던진다. */
  pendingVerifications(): Promise<VerificationRequest[]>;
  /** 받은 접근 요청 — 교수·`승인 위임` 연구원. 권한이 없으면 `GroupHidden` 을 던진다. */
  pendingAccessRequests(): Promise<AccessRequest[]>;
  /**
   * 접근 요청 처리 — **P6 이 연 op 을 그대로 부른다** (`approveAccessRequest` ·
   * `rejectAccessRequest`). 홈은 **버튼의 자리**를 주고 처리 규칙은 E-06 이 정한다
   * (`Policy_홈_대시보드 §5.2` · §8 「처리 버튼을 그 자리에 둔다」).
   * 거절 사유는 **1~300자 필수**이고 요청자에게 그대로 전달된다 (`Policy_승인_처리 §5` · P-26).
   */
  approveAccessRequest(requestId: string): Promise<void>;
  rejectAccessRequest(requestId: string, reason: string): Promise<void>;
}
