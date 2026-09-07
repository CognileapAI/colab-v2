import { useEffect } from 'react';

// ⭑ ⟨advisor ② · F7⟩ Esc 층 표식의 **한 자리**.
//
// 이 상수가 `UploadModal.tsx` 에 있던 동안 `UploadModal → PreviewPanel →
// PreviewExpandOverlay → UploadModal` 순환 import 가 섰다. 런타임은 함수 본문 참조라
// 무해했으나 번들러의 평가 순서에 기대는 상태였다. 상수 하나를 잎으로 내려 끊는다.
//
// 규율(PRD-39 ⑭ · A9R) — **위에 뜬 층이 자기 표식을 스스로 단다.** 업로드 모달은 층
// 목록을 갖지 않고 이 표식이 하나라도 떠 있으면 Esc 를 먹지 않는다. 표식을 단 층은
// **자기 닫기 함수 한 곳**으로 스스로 닫는다 — 위 층의 Esc 가 아래 층을 닫지 않는다.
export const ESC_LAYER_ATTR = 'data-esc-layer';

/** 문서 전역 Esc 한 건을 듣는다. 층이 열려 있는 동안만 건다(닫히면 해제된다). */
export function useEscLayer(onEscape: () => void): void {
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key !== 'Escape') return;
      e.preventDefault();
      // ⚠ 아래 층(업로드 모달)은 `ESC_LAYER_ATTR` 이 DOM 에 떠 있으면 스스로 물러난다 —
      //    그 판정이 이 층의 표식 하나로 이미 서 있으므로 여기서 전파를 끊지 않는다.
      onEscape();
    }
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [onEscape]);
}
