// 공개 범위 3값의 **표기 한 자리** (PRD-11 · WU-B4 · 미결-1 ⓐ 확정 · rev1 축자).
//
// 저장값과 화면 표기가 **다르다** — 저장은 `열림`·`잠김`·`지정 공개` 이고 화면은
// `연구실 구성원 전체`·`나만 보기`·`지정한 사람만` 이다. 「열림/잠김」은 결정 용어라
// 코드·시험·문서가 붙어 있어 **지우지 않고**, 사람에게는 뜻이 드러나는 말로 보인다.
//
// ⛔ **이 표를 두 벌 만들지 않는다** — 등록 셀렉트 · 상세 헤더 칩 · 공개 범위 설명 ·
//    수정 폼이 전부 여기를 읽는다. 두 곳에 적으면 언젠가 한쪽만 고쳐진다.
// ⚠ **docx `D-4` 의 3값(전체 공개·조건부 공개·비공개)과 이름으로 짝짓지 않는다** —
//    기준축이 한 칸씩 어긋난다(PRD-11 대응표). 여기 3값의 기준축은 **연구실 내부**이고
//    연구실 밖 열람 상태는 구조적으로 없다(RLS 경계 무개방 · PRD-37 은 범위 밖).
import type { components } from '../../generated/fe-core';

export type AccessState = components['schemas']['AccessState'];

/** 저장값 3값. **정본은 DB CHECK 두 표**이고(`d2_dataset_access.state` ＋
 *  `d1_lab_profile.default_visibility`) 계약 `AccessState` 가 그 사본이다. */
export const ACCESS_STATES: readonly AccessState[] = ['열림', '잠김', '지정 공개'];

/** 기본 선택값 — 「기본 선택 = `연구실 구성원 전체`」(PRD-11 축자 · rev1 `<option selected>`). */
export const DEFAULT_ACCESS_STATE: AccessState = '열림';

/** 저장값 → 화면 표기. 문면은 rev1 셀렉트 축자 그대로다. */
export const ACCESS_LABEL: Record<AccessState, string> = {
  열림: '연구실 구성원 전체',
  잠김: '나만 보기',
  '지정 공개': '지정한 사람만',
};

/** 저장값 → 한 줄 설명. 값의 **범위**를 말한다(PRD-11 대응표 「뜻」 열 축자). */
export const ACCESS_NOTE: Record<AccessState, string> = {
  열림: '연구실 안 누구나 뷰·다운로드',
  잠김: '소유자만. 허용 목록이 비어 있다',
  '지정 공개': '허용 목록에 오른 사람만. 만료 = 승인일 + 6개월',
};

export function accessLabel(state: AccessState | null | undefined): string {
  return state ? (ACCESS_LABEL[state] ?? state) : ACCESS_LABEL[DEFAULT_ACCESS_STATE];
}

export function accessNote(state: AccessState | null | undefined): string {
  return state ? (ACCESS_NOTE[state] ?? '') : ACCESS_NOTE[DEFAULT_ACCESS_STATE];
}

/**
 * `나만 보기` 로 내릴 때 되묻는 문면 (PRD-11 상태 전이표 마지막 줄 축자).
 *
 * ⚠ **rev1·rev2 목업에 이 문장이 없다**(`grep '끊'` = rev1 0건 · rev2 1건이고 그 1건은
 *   무관한 산문이다). 그래서 정본은 PRD-11 의 이 한 줄이고, 지어내지 않았다.
 * ⚠ 수는 **지금 볼 수 있는 사람**(만료되지 않은 허용 줄)이다 — `DatasetDetail.activeGrantCount`.
 */
export function loweringConfirmCopy(activeGrantCount: number): string {
  return `지금 볼 수 있는 사람 ${activeGrantCount}명의 접근이 끊깁니다`;
}
