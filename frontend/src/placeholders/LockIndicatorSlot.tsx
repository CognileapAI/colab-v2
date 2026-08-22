// 비워 둘 자리 ② — 잠긴 데이터 표시
// 어디에: 검색 카드 · 카탈로그 행 · 데이터셋 상세
// 채우는 곳: 에픽 E-06 (승인 처리) → **WU-P6**
// 근거: Policy_공통_기반 v1.4 §3 · PERMISSION-PRINCIPLES P-13
// 자물쇠·`잠김` 칩·`접근 요청` 버튼의 실물은 P6 이 채운다. 행은 절대 사라지지 않는다.
export function LockIndicatorSlot() {
  return <span data-slot="lock-indicator" data-fills-in="WU-P6" aria-hidden="true" />;
}
