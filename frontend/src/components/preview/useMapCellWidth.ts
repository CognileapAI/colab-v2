/**
 * **지도 칸 폭 측정 훅** (spec S-DEVICE-WIDTH-INPUT-20260926 「미리보기 지도 시범」 · 2단계 Q2ⓐ).
 *
 * 지도 칸 = 미리보기 지도 구역(`section.pv-map`)의 가로 폭. 도구를 지도 위에 둘지(지금 배치 ·
 * #120) 지도 아래 블록으로 보낼지를 이 폭 하나로 정한다 — **입력 방식과 무관하다**(V6).
 *
 * - 첫 그리기 전 레이아웃에서 한 번 읽고, 이후 `ResizeObserver` 항목의 `contentRect.width` 로
 *   따라간다. 콜백 안에서 요소 크기를 다시 읽지 않는다.
 * - 폭이 0 이거나 `ResizeObserver` 가 없으면 「모름」이다. 「모름」은 지금 배치다.
 * - 상태는 배치 값(모름 · 위 · 아래)이라 경계를 넘을 때만 바뀐다 — 픽셀마다 다시 그리지 않는다.
 * - 경계 810 은 이 모듈이 내보낸다. 정본 표와 시험이 이 값을 읽는다.
 * 선례: 맨 위 메뉴의 `ResizeObserver`(존재 확인 가드 포함 · `shell/Gnb.tsx`).
 */
import { useCallback, useLayoutEffect, useState } from 'react';

/** 지도 칸이 이 값보다 좁으면 네 도구(범례 · 값 조회 · 좌표 표시 · 스크린샷)가 지도 아래로 간다. */
export const MAP_CELL_BOUNDARY = 810;

export type MapCellLayout = 'unknown' | 'over' | 'below';

function layoutFor(width: number): MapCellLayout {
  if (!(width > 0)) return 'unknown';
  return width < MAP_CELL_BOUNDARY ? 'below' : 'over';
}

export function useMapCellLayout(): [(el: HTMLElement | null) => void, MapCellLayout] {
  const [el, setEl] = useState<HTMLElement | null>(null);
  const [layout, setLayout] = useState<MapCellLayout>('unknown');
  const ref = useCallback((node: HTMLElement | null) => setEl(node), []);
  useLayoutEffect(() => {
    if (!el || typeof ResizeObserver === 'undefined') {
      setLayout('unknown');
      return;
    }
    // 첫 읽기는 border-box(`getBoundingClientRect`) · 관찰은 content-box(`contentRect`) — `.pv-map` 에 padding · border 가 없어 둘이 같다는 전제다.
    setLayout(layoutFor(el.getBoundingClientRect().width));
    const observer = new ResizeObserver((entries) => {
      const last = entries[entries.length - 1];
      if (last) setLayout(layoutFor(last.contentRect.width));
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, [el]);
  return [ref, layout];
}
