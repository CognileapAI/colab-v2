// 비워 둘 자리 ① — Verified 배지
// 어디에: 데이터셋 상세 헤더 · 검색 카드 · 카탈로그 행
// 채우는 곳: 에픽 E-06 (승인 처리) → **WU-P6**
// 근거: Policy_공통_기반 v1.4 §3 「미리 비워 둘 자리」 · sessions/P0.md §2
// 여기서는 자리만 잡는다. 배지 모양·조건·교수용 체크 버튼은 P6 이 채운다.
export function VerifiedBadgeSlot() {
  return <span data-slot="verified-badge" data-fills-in="WU-P6" aria-hidden="true" />;
}
