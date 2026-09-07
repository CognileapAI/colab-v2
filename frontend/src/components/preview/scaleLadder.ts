/**
 * **축척 사다리** — 「같은 데이터셋이 아니어도 같은 등급으로 보인다」의 한 자리
 * (축 ①-⑤ · R-C spec 「축척은 사다리다」 · 우려 항목 #1).
 *
 * 요구는 하나다 — **기본 배율을 화면 폭이 정하게 두지 않는다.** 지금까지는
 * `.pv-tile { width: 100% }` 라 데이터의 지리 폭이 100 km 이든 4,000 km 이든 화면에서는
 * 같은 크기로 보였다(intent ⑤ 「사이즈가 뒤죽박죽」). 그래서 **데이터 폭을 담는 가장 작은
 * 단**으로 스냅해 등급을 만든다.
 *
 * ⚠ **값을 다른 곳에 다시 적지 않는다.** 사다리 단은 이 파일 한 자리다(spec 「모듈 · 인터페이스」
 *   축자 「하드코드 재정의 금지」). 화면·훅·시험 전부 `SCALE_LADDER_KM` 을 읽는다.
 * ⚠ **경계를 지어내지 않는다** — `bounds` 없는 ②비지도형에는 이 사다리를 적용하지 않는다.
 *   그 판정은 부르는 쪽이 `bounds` 유무로 한다(`DR-9`).
 *
 * ── 단 값의 근거(레인 실측 · 2026-09-08) ────────────────────────────────
 * 실측 대상 = ⓐ `PREVIEW-IMPLEMENTATION §3.3` 4종 실측 bbox(실물 산출물) ＋ ⓑ 프론트·
 * viz-render 픽스처 `bounds` 전량. 중위도 폭(km) 분포는:
 *
 *   112.4(warp-gaps) · 113.0(HLS tif 실측) · 177.8 · 270.2 ×2 · 279.2 · 360.2 ·
 *   720.5 · 1,034.8(HSR bin 실측) · 2,061.7(GK2A nc 실측) · 4,166.4(MODIS hdf 실측)
 *
 * 후보 5단(100·300·1,000·3,000·10,000)을 그대로 쓰면 **실물 HSR 1,034.8 km 가 1,000 을
 * 3.5 % 넘겨 3,000 단으로 떨어진다** — 국내 레이더 산출물이 2.9 배 빈 틀에 놓인다.
 * 같은 이유로 112 km 대 두 건이 300 단(2.7 배), 360 km 가 1,000 단(2.8 배)으로 떨어진다.
 * 단을 실측 군집(≈110 · 180~360 · 700~1,035 · 2,060 · 4,170)의 **바로 위**에 놓아
 * 고치면 최악 채움비가 2.9 → 2.4 배로, 중앙값이 ≈1.4 배로 내려온다. 그래서 후보를
 * **150 · 400 · 1,200 · 3,000 · 10,000** 으로 확정한다(단 수 5 는 그대로 · 우려 #1 ⓐ 유지).
 * 1,200 단은 Ted 문면 「대한민국 ＋ 중국 우측 ＋ 일본 간사이」(≈1,000~1,300 km)와도 겹친다.
 */

/** 사다리 단 — km 단위 가로 폭. **오름차순이고 이 배열이 유일한 정의다.** */
export const SCALE_LADDER_KM = [150, 400, 1200, 3000, 10000] as const;

export type ScaleRungKm = (typeof SCALE_LADDER_KM)[number];

/**
 * 지구 반지름에서 오는 두 상수. `pvLonOf`/`pvLatOf` 가 쓰는 것과 **같은 평면 근사**다 —
 * 경도 1° 는 위도에 따라 줄고(`cos`), 위도 1° 는 줄지 않는다.
 */
export const KM_PER_DEG_LAT = 110.57;
export const KM_PER_DEG_LON_EQUATOR = 111.32;

export interface GeoBounds {
  west: number;
  south: number;
  east: number;
  north: number;
}

/** 경계 상자의 중위도. 폭을 재는 기준선이다. */
export function boundsMidLat(b: GeoBounds): number {
  return (b.south + b.north) / 2;
}

/** 경계 상자의 **가로 폭(km)** — 중위도에서 잰다. */
export function boundsWidthKm(b: GeoBounds): number {
  return (b.east - b.west) * KM_PER_DEG_LON_EQUATOR * Math.cos((boundsMidLat(b) * Math.PI) / 180);
}

/** 경계 상자의 **세로 폭(km)**. */
export function boundsHeightKm(b: GeoBounds): number {
  return (b.north - b.south) * KM_PER_DEG_LAT;
}

/**
 * **데이터 폭을 담는 가장 작은 단**을 고른다(spec 축자).
 *
 * - 가장 큰 단을 넘는 폭(전지구 등)은 **가장 큰 단**으로 답한다 — 없는 단을 만들지 않는다.
 * - 0 이하·유한하지 않은 값은 **가장 작은 단**으로 답한다(폭을 지어내지 않는다).
 */
export function snapWidthKm(dataWidthKm: number): number {
  const first = SCALE_LADDER_KM[0] as number;
  if (!Number.isFinite(dataWidthKm) || dataWidthKm <= 0) return first;
  for (const rung of SCALE_LADDER_KM) {
    if (dataWidthKm <= rung) return rung;
  }
  return SCALE_LADDER_KM[SCALE_LADDER_KM.length - 1] as number;
}

/**
 * 기본 배율 — **데이터 폭 ÷ 스냅된 단**.
 *
 * 화면(4:3 틀)이 스냅된 단만큼의 폭을 담고, 데이터는 그 안에서 제 몫만 차지한다.
 * 그래서 값은 언제나 `(0, 1]` 이다 — 1 이면 데이터가 틀을 꽉 채운다.
 */
export function baseScaleFor(b: GeoBounds): number {
  const w = boundsWidthKm(b);
  if (!Number.isFinite(w) || w <= 0) return 1;
  return Math.min(1, w / snapWidthKm(w));
}

/**
 * 「지금 어디를 보고 있는지」 표시를 세울 것인가 — **데이터가 틀의 작은 몫만 차지할 때**만.
 * 꽉 채우면 외곽선은 그림의 테두리와 겹쳐 아무 것도 알려 주지 않는다.
 */
export const OUTLINE_FILL_THRESHOLD = 0.9;

export function needsBoundsOutline(b: GeoBounds | undefined): boolean {
  return b !== undefined && baseScaleFor(b) < OUTLINE_FILL_THRESHOLD;
}
