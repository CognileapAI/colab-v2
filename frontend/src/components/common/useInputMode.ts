/**
 * **입력 방식 훅** (spec S-DEVICE-WIDTH-INPUT-20260926 「입력 방식 훅(새 공용 모듈)」).
 *
 * 터치 기기 = `(pointer: coarse)` 가 참인 기기(`docs/design-system.md` 버튼 행의 「터치가 주 입력인
 * 기기」와 같은 뜻). 판별할 수 없으면(매체 질의 없음 · jsdom) 마우스로 본다.
 * ⚠ TSX 안의 입력 매체 조건 문자열은 **이 모듈 한 곳에만** 둔다 — 디자인 검사 게이트는 TSX 를
 *   보지 않으므로 이 한 곳을 vitest 가 고정한다(`device-width-input-20260926-L1`).
 */
import { useSyncExternalStore } from 'react';

export type InputMode = 'touch' | 'mouse';

const TOUCH_QUERY = '(pointer: coarse)';

function query(): MediaQueryList | undefined {
  return typeof window.matchMedia === 'function' ? window.matchMedia(TOUCH_QUERY) : undefined;
}

function subscribe(onChange: () => void): () => void {
  const list = query();
  list?.addEventListener?.('change', onChange);
  return () => list?.removeEventListener?.('change', onChange);
}

function snapshot(): InputMode {
  return query()?.matches ? 'touch' : 'mouse';
}

export function useInputMode(): InputMode {
  return useSyncExternalStore(subscribe, snapshot, () => 'mouse');
}
