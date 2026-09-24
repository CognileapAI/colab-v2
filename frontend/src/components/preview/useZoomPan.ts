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
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { baseScaleFor, needsBoundsOutline, snapWidthKm, boundsWidthKm, type GeoBounds } from './scaleLadder';
import { SETTLE_PX, VELOCITY_WINDOW_MS, capHandoffVelocity, projectedDistance, spring } from './spring';

/** 한 번 누를 때 들어가는 정도. 화면 조작의 단위이지 상한이 아니다. */
const STEP = 2;

/**
 * 끌기 시작 임계(px · 확정 값 4 · design-fix 20260924 #3). 누른 자리에서 이만큼을 **넘기 전에는**
 * 그림이 움직이지 않고, 넘는 순간 누른 자리 기준으로 따라붙어 그 뒤 1:1 이다. 임계 안에서 놓으면
 * 뒤이은 click(값 조회)은 그대로 살아 있다.
 */
const DRAG_THRESHOLD = 10;

export interface ZoomBoundsFraction {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
}

export interface UseZoomPanOptions {
  /**
   * ③지도형이 서버에서 받아 온 경계 네 값. **있을 때만 사다리가 선다** —
   * 없으면(②비지도형) 이 훅은 종전과 한 글자도 다르지 않게 움직인다(`DR-9`).
   */
  bounds?: GeoBounds | undefined;
}

export interface ZoomPan {
  scale: number;
  x: number;
  y: number;
  maxScale: number;
  /**
   * **기본 배율** — 축척 사다리가 정한 시작 자리(`scaleLadder.baseScaleFor`).
   * 경계가 없으면 `1` 이고, 그때 이 훅의 거동은 종전과 같다.
   */
  baseScale: number;
  /** 스냅된 사다리 단(km). 경계가 없으면 `undefined` — 없는 축척을 지어내지 않는다. */
  rungKm: number | undefined;
  /** 「지금 어디를 보고 있는지」 외곽선을 세울 것인가(작은 유역). */
  showBoundsOutline: boolean;
  /** 더블클릭 — **데이터 경계에 정확히 맞춘다**(여백 0). */
  fitToData: () => void;
  /** 데이터가 가진 해상도까지 들어왔는가. 재기 전에는 `false` — 모르는 것을 알린다고 하지 않는다. */
  atLimit: boolean;
  measured: boolean;
  /** 지금 재어 둔 화면 크기. 아직 못 쟀으면 `undefined` — 타일 모자이크가 이 값을 쓴다. */
  box: { width: number; height: number } | undefined;
  /**
   * ⭑ ⟨#120⟩ **중앙 기준 편차**로 들고 있는 이동값. `0` 이 곧 한가운데다.
   * 화면에 거는 `x`·`y` 는 여기에 중앙값을 더한 결과이고, 크기를 아직 못 잰 순간에도
   * 편차 0 은 「한가운데에 두려 한다」는 뜻으로 남는다.
   */
  panOffset: { x: number; y: number };
  viewportRef: (el: HTMLDivElement | null) => void;
  /**
   * ⭑ ⟨#120⟩ **층 묶음(`.pv-layers`)의 실제 배치 크기를 재는 자리.**
   * 층 묶음 높이는 그림의 가로세로비를 따르므로 뷰포트와 비율이 다르다 — 중앙 정렬·
   * 이동 범위·역변환·스크린샷 장면이 전부 이 상자를 써야 세로 중심이 맞는다.
   */
  layersRef: (el: HTMLElement | null) => void;
  /**
   * 층 묶음의 배치 크기. **두 치수 중 하나라도 0 이면 `undefined`** — jsdom·미측정·
   * 타일 갈래가 그 경우이고, 부르는 쪽이 뷰포트 상자로 대체한다(타일 갈래는 설계상
   * 내용 = 뷰포트다). **없는 크기를 지어내지 않는다.**
   */
  contentSize: () => { width: number; height: number } | undefined;
  onImageLoad: (e: { currentTarget: HTMLImageElement }) => void;
  /**
   * **원본 해상도를 그림이 아니라 밖에서 받는 자리** (조건 ⑷).
   * 타일 표면에는 「그림 한 장」이 없어 `naturalWidth` 를 잴 대상이 없다 — 대신
   * ③지도형의 사이드카가 담은 `width` 를 받는다(`PREVIEW-IMPLEMENTATION §3.3`).
   * **모르면 부르지 않는다** — 여기 기본값을 두면 한계를 지어내는 것이 된다.
   */
  onNativeWidth: (naturalWidth: number) => void;
  /**
   * ⭑ ⟨#120⟩ **휠 확대·축소의 고정점은 커서 아래 지점이다.** `clientX`·`clientY` 가 오면
   * 뷰포트 좌표로 바꿔 고정점으로 넘기고, 없으면(시험의 합성 이벤트) 종전대로 중심이다.
   * `target` 이 도구 층 안이면 아무 것도 하지 않는다 — 그 위에서는 페이지 스크롤이 자연스럽다.
   */
  onWheel: (e: {
    deltaY: number;
    clientX?: number;
    clientY?: number;
    target?: EventTarget | null;
    preventDefault?: () => void;
  }) => void;
  /**
   * 끌기 시작(포인터 · mouse · touch · pen 같은 경로). 캡처는 optional-call 이다 — 캡처가 없는
   * 환경(jsdom)에서도 이동·놓기는 창(window) 리스너가 받는다.
   */
  onPointerDown: (e: {
    clientX: number;
    clientY: number;
    button?: number;
    pointerId: number;
    currentTarget?: EventTarget | null;
  }) => void;
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

/**
 * **그림을 뷰포트 한가운데에 놓는다** (판정 축자 「`bounds` 중심」).
 *
 * ⭑ ⟨개정 2026-09-18 · `#120` intent⟩ 두 가지가 바뀌었다.
 *  ⑴ **내용 상자를 따로 받는다.** 종전은 「층 묶음 크기 = 뷰포트 크기」를 전제해
 *     `size × (1 − scale) / 2` 한 식으로 두 축을 계산했다. 층 묶음 높이는 그림의
 *     가로세로비를 따르므로 비율이 다르면 **세로 중심이 어긋난다**(이슈 첨부 1).
 *  ⑵ **`view.x`·`view.y` 는 중앙 기준 편차다.** 그래서 배율이 1 이상이어도, 내용이
 *     뷰포트보다 커도 중앙값을 함께 낸다 — 종전 `scale >= 1 → 손대지 않음` 은 세로가
 *     긴 그림을 **위 정렬**로 두었고 그것이 이슈의 그 화면이다(우려 8).
 *
 * `contentSize` 를 주지 않거나 두 치수 중 하나라도 0 이면 **뷰포트 상자로 대체**한다 —
 * 타일 갈래는 설계상 내용 = 뷰포트이고, 아직 못 잰 순간에는 종전과 같은 수가 나온다.
 * 뷰포트 크기를 모르면 그대로 둔다 — **없는 크기로 자리를 지어내지 않는다.**
 */
export function centeredPanFor(
  view: { scale: number; x: number; y: number },
  viewportSize: { width: number; height: number } | undefined,
  contentSize?: { width: number; height: number } | undefined,
): { x: number; y: number } {
  if (!viewportSize) return { x: view.x, y: view.y };
  const content =
    contentSize && contentSize.width > 0 && contentSize.height > 0 ? contentSize : viewportSize;
  return {
    x: (viewportSize.width - content.width * view.scale) / 2 + view.x,
    y: (viewportSize.height - content.height * view.scale) / 2 + view.y,
  };
}

export function useZoomPan(options?: UseZoomPanOptions): ZoomPan {
  const bounds = options?.bounds;
  // 경계 네 값은 **객체가 매번 새로 오더라도 같은 값이면 같은 축척**이어야 한다 —
  // 네 숫자로 기억을 건다.
  const west = bounds?.west;
  const south = bounds?.south;
  const east = bounds?.east;
  const north = bounds?.north;
  const geo = useMemo<GeoBounds | undefined>(
    () =>
      west === undefined || south === undefined || east === undefined || north === undefined
        ? undefined
        : { west, south, east, north },
    [west, south, east, north],
  );
  // **기본 배율은 화면 폭이 아니라 데이터가 정한다**(축 ①-⑤). 경계가 없으면 1 이고,
  // 그때 아래 모든 식은 종전과 같은 수를 낸다.
  const baseScale = useMemo(() => (geo ? baseScaleFor(geo) : 1), [geo]);
  const rungKm = useMemo(() => (geo ? snapWidthKm(boundsWidthKm(geo)) : undefined), [geo]);
  const showBoundsOutline = useMemo(() => needsBoundsOutline(geo), [geo]);

  const el = useRef<HTMLDivElement | null>(null);
  // ⭑ ⟨#120⟩ 층 묶음의 실제 배치 크기를 재는 손잡이. 없으면 내용 상자를 모른다.
  const layers = useRef<HTMLElement | null>(null);
  /** **이동값은 중앙 기준 편차다** — `0` 이 곧 한가운데다(`centeredPanFor`). */
  const [view, setView] = useState(() => ({ scale: 1, x: 0, y: 0 }));
  const [maxScale, setMaxScale] = useState(1);
  const [measured, setMeasured] = useState(false);
  const [blocked, setBlocked] = useState(false);
  // 화면 크기는 **상태로도 들고 있어야 한다** — 타일 모자이크가 그 값으로 조각을 세우는데
  // ref 를 그때그때 읽으면 크기가 늦게 잡혀도 다시 그려지지 않는다.
  const [boxSize, setBoxSize] = useState<{ width: number; height: number } | undefined>();
  /**
   * 누른 포인터 · 누른 자리(`sx`·`sy`) · 마지막 반영 자리(`x`·`y`) · 임계를 넘었는가 ·
   * 관성을 잡은 누름인가(`caught` — 그 탭 뒤의 click 은 값 조회가 아니다 · F-preview A35).
   */
  const drag = useRef<{
    id: number;
    sx: number;
    sy: number;
    x: number;
    y: number;
    active: boolean;
    caught: boolean;
  } | null>(null);
  /** 끌기가 성립한 뒤 따라오는 click 한 번을 버린다(값 조회가 끌기 끝에서 새지 않게). */
  const dragged = useRef(false);
  /** 이동 기록(시각 ms · 자리) — 놓을 때 마지막 100ms 의 평균 속도를 낸다(#5 · 값 6). */
  const samples = useRef<Array<{ t: number; x: number; y: number }>>([]);
  /** 놓은 뒤 관성 프레임 번호. 새 누르기 · 휠 · 확대 단추 · 더블클릭이 끊는다. */
  const inertia = useRef<number | null>(null);

  /** 관성을 **그 프레임 값에서** 멈춘다 — 자리를 다시 쓰지 않으므로 튀지 않는다. */
  const stopInertia = useCallback(() => {
    if (inertia.current === null) return;
    cancelAnimationFrame(inertia.current);
    inertia.current = null;
  }, []);
  useEffect(() => stopInertia, [stopInertia]);

  const box = useCallback(() => {
    const node = el.current;
    if (!node) return undefined;
    const width = node.clientWidth;
    const height = node.clientHeight;
    return width > 0 && height > 0 ? { width, height } : undefined;
  }, []);

  // ⭑ ⟨#120⟩ **내용 상자** — 층 묶음의 transform 이 걸리기 전 배치 크기다. 두 치수 중
  //   하나라도 0 이면 못 잰 것으로 보고 부르는 쪽이 뷰포트 상자로 대체한다(타일 갈래는
  //   `offsetWidth` 가 뷰포트 · `offsetHeight` 가 0 이고, 설계상 내용 = 뷰포트다).
  const contentSize = useCallback(() => {
    const node = layers.current;
    if (!node) return undefined;
    const width = node.offsetWidth;
    const height = node.offsetHeight;
    return width > 0 && height > 0 ? { width, height } : undefined;
  }, []);

  /** 중앙 정렬·이동 범위·역변환이 함께 쓰는 한 쌍. 내용을 못 재면 뷰포트로 대체한다. */
  const boxes = useCallback(() => {
    const viewport = box();
    if (!viewport) return undefined;
    return { viewport, content: contentSize() ?? viewport };
  }, [box, contentSize]);

  // 변환은 층 묶음의 왼쪽 위를 기준으로 건다(`transform-origin: 0 0`). 그림이 화면 밖으로
  // 빠져나가 빈 자리가 생기지 않게 이동 범위를 그림 안으로 가둔다.
  const clampView = useCallback(
    (next: { scale: number; x: number; y: number }) => {
      const sizes = boxes();
      if (!sizes) return { scale: next.scale, x: 0, y: 0 };
      // ⭑ ⟨개정 2026-09-18 · `#120`⟩ **시작 자리와 이동 범위를 가른다.** 이동값은
      //   중앙 기준 편차이므로 여기서 가두는 것은 「중앙에서 얼마나 벗어날 수 있는가」다.
      //   내용이 뷰포트보다 작거나 같은 축은 옮길 곳이 없어 편차 0(= 한가운데)에 고정되고,
      //   큰 축은 ±(내용 × 배율 − 뷰포트)/2 까지 간다 — 그 끝이 그림의 가장자리다.
      //   ／ 종전 표기 ~~`x: clamp(next.x, size.width * (1 - next.scale), 0)`~~ — 뷰포트
      //   크기 하나로 두 축을 계산해 세로가 긴 그림의 아래로 갈 수 없었다.
      const halfX = Math.max(0, (sizes.content.width * next.scale - sizes.viewport.width) / 2);
      const halfY = Math.max(0, (sizes.content.height * next.scale - sizes.viewport.height) / 2);
      return {
        scale: next.scale,
        x: clamp(next.x, -halfX, halfX),
        y: clamp(next.y, -halfY, halfY),
      };
    },
    [boxes],
  );

  const zoomTo = useCallback(
    (target: number, anchorX?: number, anchorY?: number) => {
      setView((cur) => {
        const sizes = boxes();
        const next = clamp(target, baseScale, maxScale);
        if (next === cur.scale) return cur;
        if (!sizes) return clampView({ scale: next, x: cur.x, y: cur.y });
        // 고정점 계산은 **화면에 실제로 걸린 이동값**(중앙값 + 편차) 위에서 해야 한다.
        const ax = anchorX ?? sizes.viewport.width / 2;
        const ay = anchorY ?? sizes.viewport.height / 2;
        const from = centeredPanFor(cur, sizes.viewport, sizes.content);
        const ratio = next / cur.scale;
        const toX = ax - (ax - from.x) * ratio;
        const toY = ay - (ay - from.y) * ratio;
        // 다시 편차로 돌려 놓는다 — 상태는 언제나 중앙 기준이다.
        const center = centeredPanFor({ scale: next, x: 0, y: 0 }, sizes.viewport, sizes.content);
        return clampView({ scale: next, x: toX - center.x, y: toY - center.y });
      });
    },
    [boxes, clampView, maxScale, baseScale],
  );

  // ⭑ ⟨#120⟩ 휠도 **버튼과 같은 한계·`blocked` 판정을 거친다** — 고정점만 다르다.
  //   휠 확대가 `atLimit` 를 지어내지 않게 판정 자리를 하나로 둔다.
  const stepIn = useCallback(
    (anchorX?: number, anchorY?: number) => {
      stopInertia();
      if (!measured || view.scale >= maxScale) {
        // 한계를 모르거나 한계에 닿았다. **없는 값을 만들어 그리지 않는다.**
        if (measured) setBlocked(true);
        return;
      }
      zoomTo(view.scale * STEP, anchorX, anchorY);
    },
    [measured, maxScale, view.scale, zoomTo, stopInertia],
  );

  const stepOut = useCallback(
    (anchorX?: number, anchorY?: number) => {
      stopInertia();
      setBlocked(false);
      zoomTo(view.scale / STEP, anchorX, anchorY);
    },
    [view.scale, zoomTo, stopInertia],
  );

  // ⚠ 버튼은 **인자 없이** 부른다 — `onClick={zoom.zoomIn}` 이 넘기는 클릭 이벤트가
  //   고정점 인자로 새어 들어가면 좌표를 지어내는 것이 된다.
  const zoomIn = useCallback(() => stepIn(), [stepIn]);

  const zoomOut = useCallback(() => stepOut(), [stepOut]);

  const reset = useCallback(() => {
    stopInertia();
    setBlocked(false);
    setView({ scale: baseScale, x: 0, y: 0 });
  }, [baseScale, stopInertia]);

  /**
   * **더블클릭 = 데이터에 맞춤**(판정 축자 「더블클릭으로 데이터에 맞춤」).
   * 여백 0 — 층 묶음의 좌표계에서 데이터 경계는 곧 틀 전체이므로 배율 1·이동 0 이다.
   * 경계가 없으면(②비지도형) 기본 배율과 같은 자리라 **아무 일도 하지 않는 것과 같다**.
   */
  const fitToData = useCallback(() => {
    stopInertia();
    setBlocked(false);
    setView({ scale: 1, x: 0, y: 0 });
  }, [stopInertia]);

  const onWheel = useCallback(
    (e: {
      deltaY: number;
      clientX?: number;
      clientY?: number;
      target?: EventTarget | null;
      preventDefault?: () => void;
    }) => {
      // ⭑ ⟨#120⟩ **도구 층 위에서는 그림을 건드리지 않는다.** 휠은 네이티브 리스너라
      //   React 의 `stopPropagation` 이 닿지 않으므로 target 으로 가른다. 여기서
      //   `preventDefault` 도 하지 않는다 — 그 위에서는 페이지 스크롤이 자연스럽다.
      const target = e.target;
      if (target instanceof Element && target.closest('.pv-overlay')) return;
      e.preventDefault?.();
      // 고정점은 **커서 아래 지점**이다. 좌표가 없으면(시험의 합성 이벤트) 종전대로 중심.
      let ax: number | undefined;
      let ay: number | undefined;
      const node = el.current;
      if (node && typeof e.clientX === 'number' && typeof e.clientY === 'number') {
        const rect = node.getBoundingClientRect();
        ax = e.clientX - rect.left;
        ay = e.clientY - rect.top;
      }
      if (e.deltaY < 0) stepIn(ax, ay);
      else stepOut(ax, ay);
    },
    [stepIn, stepOut],
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
    // 끌기 끝의 click 은 **캡처 단계에서** 멈춘다 — React 의 onClick(값 조회)은 루트 위임이라
    // 여기서 전파를 끊으면 닿지 않는다. 호출부마다 같은 검사를 흩지 않는다.
    // 도구 층(확대 줄 등)의 click 은 끌기의 끝이 아니다 — 건드리지 않는다.
    const swallow = (e: MouseEvent) => {
      if (!dragged.current) return;
      if (e.target instanceof Element && e.target.closest('.pv-overlay')) return;
      dragged.current = false;
      e.stopPropagation();
    };
    node.addEventListener('click', swallow, true);
    return () => {
      node.removeEventListener('wheel', handle);
      node.removeEventListener('click', swallow, true);
    };
  }, [node, onWheel]);

  const onPointerDown = useCallback(
    (e: {
      clientX: number;
      clientY: number;
      button?: number;
      pointerId: number;
      currentTarget?: EventTarget | null;
    }) => {
      if (e.button !== undefined && e.button !== 0) return;
      // 끌기 중 다른 포인터(두 번째 손가락)의 누름은 무시한다 — 첫 포인터가 끝날 때까지(A27).
      if (drag.current && drag.current.id !== e.pointerId) return;
      // 관성 중의 누름은 관성을 잡는 탭이다 — 놓은 뒤 click 을 값 조회로 넘기지 않는다(A35).
      const caught = inertia.current !== null;
      stopInertia();
      dragged.current = false;
      drag.current = {
        id: e.pointerId,
        sx: e.clientX,
        sy: e.clientY,
        x: e.clientX,
        y: e.clientY,
        active: false,
        caught,
      };
      samples.current = [{ t: performance.now(), x: e.clientX, y: e.clientY }];
      // 캡처가 있으면 뷰포트 밖으로 나가도 이동이 이어진다. 없으면(jsdom) 창 리스너가 받는다.
      (e.currentTarget as Element | null | undefined)?.setPointerCapture?.(e.pointerId);
    },
    [stopInertia],
  );

  useEffect(() => {
    function move(e: PointerEvent) {
      const from = drag.current;
      if (!from || e.pointerId !== from.id) return;
      const now = performance.now();
      samples.current = samples.current.filter((p) => now - p.t <= VELOCITY_WINDOW_MS);
      samples.current.push({ t: now, x: e.clientX, y: e.clientY });
      if (!from.active) {
        // 임계를 **넘기 전에는** 움직이지 않는다. 넘는 순간 누른 자리 기준으로 붙는다
        // (`from.x`·`from.y` 가 아직 누른 자리이므로 첫 반영이 곧 누른 자리부터의 전량이다).
        if (Math.hypot(e.clientX - from.sx, e.clientY - from.sy) <= DRAG_THRESHOLD) return;
        from.active = true;
      }
      const dx = e.clientX - from.x;
      const dy = e.clientY - from.y;
      from.x = e.clientX;
      from.y = e.clientY;
      setView((cur) => clampView({ ...cur, x: cur.x + dx, y: cur.y + dy }));
    }
    function up(e: PointerEvent) {
      const from = drag.current;
      if (!from || e.pointerId !== from.id) return;
      dragged.current = from.active || from.caught;
      drag.current = null;
      if (!from.active) return;
      // 놓을 때 속도 = 마지막 100ms 이동 기록의 평균(px/s · 확정 값 6). 기록이 한 점뿐이면
      // (잠시 멈췄다 놓음) 속도 0 — 관성 없이 그 자리에 선다.
      const now = performance.now();
      const recent = [...samples.current, { t: now, x: e.clientX, y: e.clientY }].filter(
        (p) => now - p.t <= VELOCITY_WINDOW_MS,
      );
      samples.current = [];
      const first = recent[0];
      const last = recent[recent.length - 1];
      if (!first || !last || last.t <= first.t) return;
      // 「동작 줄이기」면 관성 없이 놓은 자리에 선다.
      if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return;
      const vx = ((last.x - first.x) / (last.t - first.t)) * 1000;
      const vy = ((last.y - first.y) / (last.t - first.t)) * 1000;
      // 목표 = 투영 자리를 이동 범위로 자른 값. 스프링이 놓은 속도를 이어받아 그리로 간다.
      // 출발 자리는 **첫 프레임의 갱신 함수가 받은 최신 값(`cur`)** 이다 — 렌더 시점의 값을 쓰면
      // 아직 커밋되지 않은 마지막 이동이 빠져 한 걸음 뒤에서 출발한다(A24/A28/A34).
      // 목표가 잘렸으면 인계 속도를 |v0| ≤ ω·|x0| 로 줄여 끝에서 넘쳤다 잘리지 않게 한다(A26).
      const t0 = now;
      let launch: {
        x: number;
        y: number;
        goal: { x: number; y: number };
        vx: number;
        vy: number;
      } | null = null;
      let settled = false;
      const frame = () => {
        if (settled) {
          inertia.current = null;
          return;
        }
        const t = (performance.now() - t0) / 1000;
        setView((cur) => {
          // 갱신 함수는 멱등이어야 한다 — StrictMode(DEV)는 몰아 처리하는 갱신을 두 번 부르고
          // 첫 결과를 버린다. 멈춘 뒤의 호출도 앞 프레임 값이 아니라 목표를 돌려준다(FP-1).
          // `settled` 는 rAF 루프의 멈춤 판단에만 쓴다.
          if (settled && launch) return clampView({ ...cur, x: launch.goal.x, y: launch.goal.y });
          if (!launch) {
            const goal = clampView({
              scale: cur.scale,
              x: cur.x + projectedDistance(vx),
              y: cur.y + projectedDistance(vy),
            });
            launch = {
              x: cur.x,
              y: cur.y,
              goal,
              vx: capHandoffVelocity(vx, cur.x - goal.x),
              vy: capHandoffVelocity(vy, cur.y - goal.y),
            };
          }
          const { goal } = launch;
          const sx = spring(launch.x, goal.x, launch.vx, t).value;
          const sy = spring(launch.y, goal.y, launch.vy, t).value;
          const done = Math.abs(sx - goal.x) < SETTLE_PX && Math.abs(sy - goal.y) < SETTLE_PX;
          if (done) settled = true;
          return clampView({ ...cur, x: done ? goal.x : sx, y: done ? goal.y : sy });
        });
        // 갱신 함수가 렌더까지 미뤄지면 `settled` 는 다음 프레임에 읽힌다 — 빈 프레임 하나가 더 돈다.
        inertia.current = settled ? null : requestAnimationFrame(frame);
      };
      inertia.current = requestAnimationFrame(frame);
    }
    // pointercancel 은 놓기가 아니다 — 관성 없이 끝내고 취소 이벤트의 좌표는 표본에 넣지 않는다
    // (A23/A25/A33). 취소 뒤에는 click 이 오지 않으므로 버릴 click 도 없다.
    function cancel(e: PointerEvent) {
      const from = drag.current;
      if (!from || e.pointerId !== from.id) return;
      drag.current = null;
      samples.current = [];
      dragged.current = false;
    }
    window.addEventListener('pointermove', move);
    window.addEventListener('pointerup', up);
    window.addEventListener('pointercancel', cancel);
    return () => {
      window.removeEventListener('pointermove', move);
      window.removeEventListener('pointerup', up);
      window.removeEventListener('pointercancel', cancel);
      // 도는 관성 프레임은 놓을 때의 `clampView` 를 쥐고 있다 — 리스너를 새로 걸 때 멈춘다(A41).
      stopInertia();
    };
  }, [clampView, stopInertia]);

  // **원본 해상도는 한 번 알면 계속 유효하다** — 결과가 바뀌지 않는 한 다시 묻지 않는다.
  // 화면 크기 쪽은 바뀔 수 있으므로 둘을 갈라 들고, 크기가 바뀌면 한계를 다시 센다.
  const nativeWidth = useRef(0);

  const remeasure = useCallback(() => {
    // 화면 크기·한계 배율이 바뀌면 이동 범위도 바뀐다 — 놓을 때의 목표로 가던 관성을 멈춘다(A41).
    stopInertia();
    const size = box();
    if (!size || !nativeWidth.current) return;
    setBoxSize((prev) =>
      prev && prev.width === size.width && prev.height === size.height ? prev : size,
    );
    // 한계는 여전히 **원본 픽셀 수 ÷ 화면 폭**이다(조건 ⑷ · 수치 하드코드 0).
    // ⚠ **사다리는 바닥만 내린다** — 천장(1 = 데이터가 틀을 꽉 채우는 자리)은 손대지 않는다.
    //   여기를 `baseScale` 로 내리면 「데이터에 맞춤」보다 덜 들어간 곳이 한계가 된다.
    setMaxScale(Math.max(1, nativeWidth.current / size.width));
    setMeasured(true);
  }, [box, stopInertia]);

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

  // **시작 자리는 사다리가 정한다.** 경계가 없으면(`baseScale === 1`) 아무 것도 하지
  // 않는다 — ②비지도형의 거동을 한 글자도 바꾸지 않기 위해서다.
  // 경계가 바뀌면(기본 배율 변화) 도는 관성을 먼저 멈춘다 — 멈추지 않으면 다음 프레임이
  // 옛 배율의 목표로 시작 자리를 덮는다(A29).
  useEffect(() => {
    stopInertia();
    if (baseScale >= 1) return;
    setView((cur) => (cur.scale === baseScale ? cur : { scale: baseScale, x: 0, y: 0 }));
  }, [baseScale, stopInertia]);

  const onImageLoad = useCallback(
    (e: { currentTarget: HTMLImageElement }) => learn(e.currentTarget.naturalWidth),
    [learn],
  );

  const visibleFraction = useCallback((): ZoomBoundsFraction => {
    const sizes = boxes();
    if (!sizes) return { x0: 0, y0: 0, x1: 1, y1: 1 };
    // ⭑ ⟨#120⟩ 「지금 장면」은 **화면에 실제로 그려진 자리**에서 센다 — 그림의 범위는
    //   내용 상자, 보이는 창은 뷰포트 상자다. 종전은 둘을 같은 것으로 보고 중앙 정렬분도
    //   빠뜨려, 중앙에 놓인 그림의 장면이 왼쪽 위로 치우쳐 나갔다.
    const at = centeredPanFor(view, sizes.viewport, sizes.content);
    const w = sizes.content.width * view.scale;
    const h = sizes.content.height * view.scale;
    return {
      x0: clamp(-at.x / w, 0, 1),
      y0: clamp(-at.y / h, 0, 1),
      x1: clamp((sizes.viewport.width - at.x) / w, 0, 1),
      y1: clamp((sizes.viewport.height - at.y) / h, 0, 1),
    };
  }, [boxes, view]);

  // **한가운데 놓기는 내보낼 때 한다** — 상태에 넣어 두면 화면 크기를 아직 못 잰 순간에
  // 0 으로 굳어 버리고, 그 뒤 크기를 알아도 다시 계산되지 않는다. 크기는 렌더마다 잰다.
  const pan = centeredPanFor(view, box(), contentSize());

  return {
    scale: view.scale,
    x: pan.x,
    y: pan.y,
    maxScale,
    baseScale,
    rungKm,
    showBoundsOutline,
    fitToData,
    measured,
    box: boxSize,
    // ⭑ ⟨버그 8⟩ **한계는 들어간 뒤에만 오는 것이 아니다.** 종전 조건은 `view.scale > 1 ||
    //   blocked` 를 요구해 **한 번이라도 확대했거나 눌러 본 뒤**에만 한계를 말했다. 그런데
    //   실제 산출물은 폭 808~821 px 이고 상세 뷰포트는 ≈ 820 px 이라 `maxScale` 이 1 로
    //   떨어진다 — 들어갈 자리가 애초에 없어 `view.scale` 이 1 을 넘을 수 없고, 그래서
    //   **세 버튼이 무동작인데 화면은 한마디도 하지 않았다.**
    //   한계 배율이 1 이면 **잰 그 순간이 곧 한계**다. 그 사실을 처음부터 세운다.
    //   ⚠ **한계 배율의 계산은 여기서 손대지 않는다** — 「데이터가 가진 해상도까지만」
    //   (조건 ⑷ · `PLAN-SoT §9 〈232〉`)은 정본 규칙이고 상한을 올리는 것은 정본 개정이다.
    atLimit:
      measured && view.scale >= maxScale && (view.scale > baseScale || blocked || maxScale <= baseScale),
    panOffset: { x: view.x, y: view.y },
    viewportRef: (n) => {
      el.current = n;
      setNode(n);
    },
    layersRef: (n) => {
      layers.current = n;
    },
    contentSize,
    onImageLoad,
    onNativeWidth: learn,
    onWheel,
    onPointerDown,
    zoomIn,
    zoomOut,
    reset,
    visibleFraction,
    viewportSize: box,
  };
}
