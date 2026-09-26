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
//
// ⭑ 휴대폰·패드 대응 20260926 L3a(V9 · 부록 C 6) — 터치 기기에서만 배지가 **뜻을 펼치는 설명 단추**다.
// 승인 동작으로 가는 자리가 아니다(누르면 아래 문장만 보인다). 마우스는 표시 전용 배지와 `title` 그대로다.
import './approval.css';
import { TouchOrMouse } from '../common/TouchNote';
import { useInputMode } from '../common/useInputMode';

/** 마우스 올림 설명과 터치에서 누르면 보이는 설명이 같은 문장이다(「새 문구안」 14행 확정). */
const VERIFIED_MEANING = '교수가 품질을 보증했어요';

export function VerifiedBadge(props: { verified: boolean }) {
  const mouse = useInputMode() === 'mouse';
  if (!props.verified) return null;
  return (
    <TouchOrMouse mouse={mouse} note={VERIFIED_MEANING}>
      <span className="chip chip--verified" data-slot="verified-badge" title={mouse ? VERIFIED_MEANING : undefined}>
        Verified
      </span>
    </TouchOrMouse>
  );
}
