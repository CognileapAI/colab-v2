// 공통 토스트 **한 개** — PRD-43.
//
// 종전에는 토스트 체계가 없었고 인라인 `.warn`/`.err` 만 있었다. 그래서 같은 성격의 안내가
// 화면마다 다른 모양으로 서고, 어떤 것은 **사라지지 않은 채** 남았다.
//
// 수용 기준 축자(PRD-43) — 「화면 위에 한 줄이 뜨고 **스스로 사라지며 포커스를 뺏지 않는다**」.
//
// **포커스를 뺏지 않는다**의 뜻:
//   · `role="status"` ＋ `aria-live="polite"` — 읽는 사람이 하던 일을 끊지 않고 뒤에 읽힌다.
//     `alert`/`assertive` 는 읽던 문장을 자른다. 안내는 경보가 아니다.
//   · `tabindex` 를 달지 않는다 — 탭 순서에 끼어들면 사라진 뒤 포커스가 허공에 남는다.
//   · 스스로 `focus()` 를 부르지 않는다. 부르는 쪽도 자동 포커스를 넣지 않는다.
//
// ⛔ 문면을 여기 적지 않는다 — 문면의 자리는 `toastCopy.ts` 하나다.
import { useEffect, useState } from 'react';

import './toast.css';

/**
 * 떠 있는 시간. 한 줄을 읽는 데 드는 시간보다 길고, 다음 동작을 막지 않을 만큼 짧다.
 * 시험이 이 값을 읽어 시계를 돌린다 — 숫자를 시험에 다시 적으면 두 벌이 된다.
 */
export const TOAST_DISMISS_MS = 4000;

export function Toast(props: {
  message: string;
  /** 시험이 잡는 손잡이. 자리마다 다른 값을 준다 (`LoadFailure` 선례). */
  testId?: string;
  /** 사라짐까지의 시간. 기본값을 바꿀 이유가 없으면 넘기지 않는다. */
  dismissMs?: number;
  /** 사라진 뒤 부르는 쪽의 상태도 함께 내리고 싶을 때. */
  onDismiss?: () => void;
}) {
  const { message, dismissMs = TOAST_DISMISS_MS, onDismiss } = props;
  const [shown, setShown] = useState(true);

  // **문면이 바뀌면 시계가 다시 선다.** 다시 세우지 않으면 뒤에 온 안내가 앞 안내의
  // 남은 시간만큼만 서 있다 — 마지막 안내일수록 짧게 보이는 뒤집힌 규칙이 된다.
  useEffect(() => {
    setShown(true);
    const timer = setTimeout(() => {
      setShown(false);
      onDismiss?.();
    }, dismissMs);
    return () => clearTimeout(timer);
  }, [message, dismissMs, onDismiss]);

  if (!shown) return null;

  return (
    <p
      className="toast"
      role="status"
      aria-live="polite"
      {...(props.testId ? { 'data-testid': props.testId } : {})}
    >
      {message}
    </p>
  );
}
