// 비워 둘 자리 ③ — 할 일 함
// 어디에: `연구실` 화면(대시보드) 상단
// 채우는 곳: 에픽 E-06 (승인 처리) · E-07 (연구실 대시보드) → **WU-P6 · WU-P7**
// 근거: Policy_공통_기반 v1.4 §3 · IA_사이트맵 §4
// 그룹별 권한 노출(교수 Verified 검토 대기 · 받은 접근 요청)은 P6·P7 이 채운다.
export function TodoInboxSlot() {
  return <section data-slot="todo-inbox" data-fills-in="WU-P6,WU-P7" aria-hidden="true" />;
}
