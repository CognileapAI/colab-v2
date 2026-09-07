/**
 * **미리보기 한 자리 좌표 변환** (WU-C5 · 축 ①-⑤b).
 *
 * 커서 역산(`pvLonOf`/`pvLatOf` · WU-C4 rev1)과 배경 벡터의 정투영(`BasemapLayer`)은
 * **같은 사각형 하나**를 읽어야 한다. 둘이 각자 계산하면 배경 해안선과 래스터가 한 픽셀씩
 * 어긋나고, 그 어긋남은 화면에서만 보이지 시험에서는 보이지 않는다.
 *
 * 그래서 정본은 아래 네 함수뿐이다 — 역산 두 개는 `PreviewPanels` 가 이것을 **감싼다**.
 * 층 묶음(`.pv-layers`)의 좌표계에서 **데이터 경계는 곧 층 전체**이므로, 여기 비율은
 * 배율·이동과 무관한 0..1 이고 화면 변환은 층에 걸린 `transform` 하나가 담당한다.
 */
import type { GeoBounds } from './scaleLadder';

/** 경계 안의 가로 비율 → 경도. */
export function lonAtFraction(fx: number, bounds: GeoBounds): number {
  return bounds.west + fx * (bounds.east - bounds.west);
}

/** 경계 안의 세로 비율 → 위도. 화면 위쪽이 북쪽이라 비율을 뒤집어 뺀다. */
export function latAtFraction(fy: number, bounds: GeoBounds): number {
  return bounds.north - fy * (bounds.north - bounds.south);
}

/** 경도 → 경계 안의 가로 비율. `lonAtFraction` 의 역이고, 0..1 로 자르지 않는다. */
export function lonFractionOf(lon: number, bounds: GeoBounds): number {
  const span = bounds.east - bounds.west;
  return span === 0 ? 0 : (lon - bounds.west) / span;
}

/** 위도 → 경계 안의 세로 비율. `latAtFraction` 의 역. */
export function latFractionOf(lat: number, bounds: GeoBounds): number {
  const span = bounds.north - bounds.south;
  return span === 0 ? 0 : (bounds.north - lat) / span;
}
