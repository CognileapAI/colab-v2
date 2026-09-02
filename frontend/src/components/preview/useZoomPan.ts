// 미리보기 **확대(줌)** — 정본 `Policy_데이터셋_상세 §8` 「확대(줌) — 왜 넣는가, 무엇이 되면
// 된 것인가」의 조건을 지키는 자리.
// ⭑ ⟨개정 2026-08-31⟩ 정본은 **v2.6 · 일곱 조건**이다(⑺ 반응 100 ms · `〈233〉`).
//   ／ 이전 표기 ~~v2.5 · 여섯 조건~~.
//
//  ⑵ **값·팔레트·구간 수 설정과 범례를 건드리지 않는다** — 이 훅은 렌더 요청에 손대지 않고
//     **이미 그린 결과 위의 변환**만 들고 있다. 범례는 확대되는 층 묶음 밖에 선다.
//  ⑶ **렌더를 다시 걸지 않는다** — 여기서 `create`·`get` 을 부르는 경로가 없다.
//  ⑷ **데이터가 가진 해상도가 한계다** — 한계 배율은 지어내지 않고 **원본이 실제로 가진
//     픽셀 수**와 화면에 놓인 크기의 비에서 온다. 재기 전에는 확대하지 않는다.
//     ⭑ ⟨2026-08-31 · `〈238〉`⟩ 그 픽셀 수의 출처가 **둘**이 됐다 — 이미지 갈래는 그림의
//     `naturalWidth`, **타일 갈래는 ③지도형 사이드카의 `width`**(`onNativeWidth`). 타일
//     표면에는 잴 그림 한 장이 없어서다. **어느 쪽도 지어내지 않는다.**
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
  /** 지금 재어 둔 화면 크기. 아직 못 쟀으면 `undefined` — 타일 모자이크가 이 값을 쓴다. */
  box: { width: number; height: number } | undefined;
  viewportRef: (el: HTMLDivElement | null) => void;
  onImageLoad: (e: { currentTarget: HTMLImageElement }) => void;
  /**
   * **원본 해상도를 그림이 아니라 밖에서 받는 자리** (조건 ⑷).
   * 타일 표면에는 「그림 한 장」이 없어 `naturalWidth` 를 잴 대상이 없다 — 대신
   * ③지도형의 사이드카가 담은 `width` 를 받는다(`PREVIEW-IMPLEMENTATION §3.3`).
   * **모르면 부르지 않는다** — 여기 기본값을 두면 한계를 지어내는 것이 된다.
   */
  onNativeWidth: (naturalWidth: number) => void;
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
  // 화면 크기는 **상태로도 들고 있어야 한다** — 타일 모자이크가 그 값으로 조각을 세우는데
  // ref 를 그때그때 읽으면 크기가 늦게 잡혀도 다시 그려지지 않는다.
  const [boxSize, setBoxSize] = useState<{ width: number; height: number } | undefined>();
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

  // ⭑ **휠은 네이티브 리스너로 건다 — React 의 `onWheel` 은 passive 다** (검수 #24).
  //   React 17+ 는 `wheel`·`touchmove`·`scroll` 을 루트에 **passive 로** 위임한다. 그래서
  //   위 `preventDefault()` 가 **아무 일도 하지 않았고**, 브라우저가 상세 화면에서
  //   `Unable to preventDefault inside passive event listener` 를 14건 찍고 있었다 —
  //   확대는 되는데 페이지도 같이 스크롤됐다. `{ passive: false }` 로 직접 걸어야 막힌다.
  //   ⚠ 이 자리를 다시 React 의 `onWheel` 로 되돌리면 그 순간 같은 결함이 돌아온다.
  const [node, setNode] = useState<HTMLDivElement | null>(null);
  useEffect(() => {
    if (!node) return;
    const handle = (e: WheelEvent) => onWheel(e);
    node.addEventListener('wheel', handle, { passive: false });
    return () => node.removeEventListener('wheel', handle);
  }, [node, onWheel]);

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

  // **원본 해상도는 한 번 알면 계속 유효하다** — 결과가 바뀌지 않는 한 다시 묻지 않는다.
  // 화면 크기 쪽은 바뀔 수 있으므로 둘을 갈라 들고, 크기가 바뀌면 한계를 다시 센다.
  const nativeWidth = useRef(0);

  const remeasure = useCallback(() => {
    const size = box();
    if (!size || !nativeWidth.current) return;
    setBoxSize((prev) =>
      prev && prev.width === size.width && prev.height === size.height ? prev : size,
    );
    setMaxScale(Math.max(1, nativeWidth.current / size.width));
    setMeasured(true);
  }, [box]);

  const learn = useCallback(
    (natural: number) => {
      if (!natural) return;
      nativeWidth.current = natural;
      remeasure();
    },
    [remeasure],
  );

  // 화면이 커지고 작아지면 **한계 배율도 달라진다** — 한계는 원본 픽셀 수와 화면에 놓인
  // 크기의 비이기 때문이다(조건 ⑷). 늘 같은 값으로 두면 한계를 지어내는 쪽이 된다.
  useEffect(() => {
    window.addEventListener('resize', remeasure);
    return () => window.removeEventListener('resize', remeasure);
  }, [remeasure]);

  const onImageLoad = useCallback(
    (e: { currentTarget: HTMLImageElement }) => learn(e.currentTarget.naturalWidth),
    [learn],
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
    box: boxSize,
    atLimit: measured && view.scale >= maxScale && (view.scale > 1 || blocked),
    viewportRef: (n) => {
      el.current = n;
      setNode(n);
    },
    onImageLoad,
    onNativeWidth: learn,
    onWheel,
    onMouseDown,
    zoomIn,
    zoomOut,
    reset,
    visibleFraction,
    viewportSize: box,
  };
}
