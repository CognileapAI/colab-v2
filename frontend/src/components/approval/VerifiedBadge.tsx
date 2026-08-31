// Verified 배지 — **표시 전용이고 누르는 곳이 아니다** (`Policy_승인_처리 §1.5` · §8).
//
// `placeholders/VerifiedBadgeSlot.tsx` 가 P0 부터 잡아 둔 자리를 WU-P6 이 채운 것이다.
// 자리 컴포넌트를 지우지 않고 **이것으로 갈아 끼운다** — 자리의 근거(P0 §3 「미리 비워 둘 자리」)는
// 그대로 유효하고, 바뀐 것은 그 자리에 무엇이 들어가는가뿐이다.
//
// ⚠ **버튼도 링크도 아니다.** 배지는 카탈로그·검색·프로젝트·홈에 똑같이 반복되는 상태 표시라,
// 한 곳에서 눌리기 시작하면 나머지도 눌릴 것처럼 보이고 오조작이 생긴다 (§1.3-4).
// 승인 취소의 진입점은 상세 헤더의 `⋯` 더보기 하나뿐이다.
//
// ⚠ **미승인에 회색 배지를 두지 않는다.** 배지는 1종이고(§4 용어 정의) 없으면 없는 것이다 —
// 「미승인 배지」를 만들면 배지가 2종이 된다.
export function VerifiedBadge(props: { verified: boolean }) {
  if (!props.verified) return null;
  return (
    <span className="chip chip--verified" data-slot="verified-badge" title="교수가 품질을 보증했어요">
      Verified
    </span>
  );
}
