// 미리보기 **확대(줌)** — 정본 `Policy_데이터셋_상세 §8` 「확대(줌) — 왜 넣는가, 무엇이 되면
// 된 것인가」(v2.5 · `PLAN-SoT §9 〈232〉`)의 여섯 조건을 지키는 자리.
//
//  ⑵ **값·팔레트·구간 수 설정과 범례를 건드리지 않는다** — 이 훅은 렌더 요청에 손대지 않고
//     **이미 그린 결과 위의 변환**만 들고 있다. 범례는 확대되는 층 묶음 밖에 선다.
//  ⑶ **렌더를 다시 걸지 않는다** — 여기서 `create`·`get` 을 부르는 경로가 없다.
//  ⑷ **데이터가 가진 해상도가 한계다** — 한계 배율은 지어내지 않고 **그림이 실제로 가진
//     픽셀 수**(`naturalWidth`)와 화면에 놓인 크기의 비에서 온다. 재기 전에는 확대하지 않는다.
//  ⑸ **모든 층에 함께** — 변환은 층 묶음 하나에 걸리고 층마다 걸리지 않는다.
//  ⑹ **저장하지 않는다** — 상태는 이 훅의 메모리뿐이다. 저장소를 쓰지 않는다.
//
// **속도·상한의 수치를 정하지 않는다**(정본 §8 말미) — 배율 한계는 데이터에서 오는 값이고,
// 여기 상수로 박힌 것은 사람이 한 번에 얼마나 들어가는가(`STEP`) 하나다.
import { useCallback, useEffect, useRef, useState } from 'react';

/** 한 번 누를 때 들어가는 정도. 화면 조작의 단위이지 상한이 아니다. */
const STEP = 2;

export interface ZoomBoundsFraction {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
}

export interface ZoomPan {
  scale: number;
  x: number;
  y: number;
  maxScale: number;
  /** 데이터가 가진 해상도까지 들어왔는가. 재기 전에는 `false` — 모르는 것을 알린다고 하지 않는다. */
  atLimit: boolean;
  measured: boolean;
  viewportRef: (el: HTMLDivElement | null) => void;
  onImageLoad: (e: { currentTarget: HTMLImageElement }) => void;
  onWheel: (e: { deltaY: number; preventDefault?: () => void }) => void;
  onMouseDown: (e: { clientX: number; clientY: number; button?: number }) => void;
  zoomIn: () => void;
  zoomOut: () => void;
  reset: () => void;
  /** 지금 보고 있는 자리 — 그림 전체를 1 로 본 비율. 스크린샷의 「지금 장면」이 여기서 온다. */
  visibleFraction: () => ZoomBoundsFraction;
  /** 지도 위젯이 지금 보여주는 화면 크기(픽셀). 못 재면 `undefined`. */
  viewportSize: () => { width: number; height: number } | undefined;
}

function clamp(v: number, lo: number, hi: number): number {
  return v < lo ? lo : v > hi ? hi : v;
}

export function useZoomPan(): ZoomPan {
  const el = useRef<HTMLDivElement | null>(null);
  const [view, setView] = useState({ scale: 1, x: 0, y: 0 });
  const [maxScale, setMaxScale] = useState(1);
  const [measured, setMeasured] = useState(false);
  const [blocked, setBlocked] = useState(false);
  const drag = useRef<{ x: number; y: number } | null>(null);

  const box = useCallback(() => {
    const node = el.current;
    if (!node) return undefined;
    const width = node.clientWidth;
    const height = node.clientHeight;
    return width > 0 && height > 0 ? { width, height } : undefined;
  }, []);

  // 변환은 층 묶음의 왼쪽 위를 기준으로 건다(`transform-origin: 0 0`). 그림이 화면 밖으로
  // 빠져나가 빈 자리가 생기지 않게 이동 범위를 그림 안으로 가둔다.
  const clampView = useCallback(
    (next: { scale: number; x: number; y: number }) => {
      const size = box();
      if (!size) return { scale: next.scale, x: 0, y: 0 };
      return {
        scale: next.scale,
        x: clamp(next.x, size.width * (1 - next.scale), 0),
        y: clamp(next.y, size.height * (1 - next.scale), 0),
      };
    },
    [box],
  );

  const zoomTo = useCallback(
    (target: number, anchorX?: number, anchorY?: number) => {
      setView((cur) => {
        const size = box();
        const next = clamp(target, 1, maxScale);
        if (next === cur.scale) return cur;
        const ax = anchorX ?? (size ? size.width / 2 : 0);
        const ay = anchorY ?? (size ? size.height / 2 : 0);
        const ratio = next / cur.scale;
        return clampView({ scale: next, x: ax - (ax - cur.x) * ratio, y: ay - (ay - cur.y) * ratio });
      });
    },
    [box, clampView, maxScale],
  );

  const zoomIn = useCallback(() => {
    if (!measured || view.scale >= maxScale) {
      // 한계를 모르거나 한계에 닿았다. **없는 값을 만들어 그리지 않는다.**
      if (measured) setBlocked(true);
      return;
    }
    zoomTo(view.scale * STEP);
  }, [measured, maxScale, view.scale, zoomTo]);

  const zoomOut = useCallback(() => {
    setBlocked(false);
    zoomTo(view.scale / STEP);
  }, [view.scale, zoomTo]);

  const reset = useCallback(() => {
    setBlocked(false);
    setView({ scale: 1, x: 0, y: 0 });
  }, []);

  const onWheel = useCallback(
    (e: { deltaY: number; preventDefault?: () => void }) => {
      e.preventDefault?.();
      if (e.deltaY < 0) zoomIn();
      else zoomOut();
    },
    [zoomIn, zoomOut],
  );

  const onMouseDown = useCallback(
    (e: { clientX: number; clientY: number; button?: number }) => {
      if (e.button !== undefined && e.button !== 0) return;
      drag.current = { x: e.clientX, y: e.clientY };
    },
    [],
  );

  useEffect(() => {
    function move(e: MouseEvent) {
      const from = drag.current;
      if (!from) return;
      drag.current = { x: e.clientX, y: e.clientY };
      setView((cur) => clampView({ ...cur, x: cur.x + (e.clientX - from.x), y: cur.y + (e.clientY - from.y) }));
    }
    function up() {
      drag.current = null;
    }
    window.addEventListener('mousemove', move);
    window.addEventListener('mouseup', up);
    return () => {
      window.removeEventListener('mousemove', move);
      window.removeEventListener('mouseup', up);
    };
  }, [clampView]);

  const onImageLoad = useCallback(
    (e: { currentTarget: HTMLImageElement }) => {
      const size = box();
      const natural = e.currentTarget.naturalWidth;
      if (!size || !natural) return;
      setMaxScale(Math.max(1, natural / size.width));
      setMeasured(true);
    },
    [box],
  );

  const visibleFraction = useCallback((): ZoomBoundsFraction => {
    const size = box();
    if (!size) return { x0: 0, y0: 0, x1: 1, y1: 1 };
    const w = size.width * view.scale;
    const h = size.height * view.scale;
    return {
      x0: clamp(-view.x / w, 0, 1),
      y0: clamp(-view.y / h, 0, 1),
      x1: clamp((size.width - view.x) / w, 0, 1),
      y1: clamp((size.height - view.y) / h, 0, 1),
    };
  }, [box, view]);

  return {
    scale: view.scale,
    x: view.x,
    y: view.y,
    maxScale,
    measured,
    atLimit: measured && view.scale >= maxScale && (view.scale > 1 || blocked),
    viewportRef: (node) => {
      el.current = node;
    },
    onImageLoad,
    onWheel,
    onMouseDown,
    zoomIn,
    zoomOut,
    reset,
    visibleFraction,
    viewportSize: box,
  };
}
