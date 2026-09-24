// 미리보기 끌기를 놓은 뒤의 움직임 — **임계 감쇠(damping 1.0) 스프링**(design-fix 20260924 #5).
// 확정 값 5 = 새 의존성 없이 직접 구현 · 값 6 = response 0.4s · 투영 감속률 0.998.
// X·Y 를 따로 부른다. 시간은 초, 속도는 px/s 다.

/** 한 번 흔들림에 걸리는 시간(초 · 확정 값 6). ω = 2π / response. */
export const SPRING_RESPONSE = 0.4;

/** 투영 감속률(ms 당 · 확정 값 6). 놓은 속도로 미끄러질 거리 = (v / 1000)·r / (1 − r). */
export const DECELERATION = 0.998;

/** 놓을 때 속도를 재는 창(ms · 확정 값 6) — 이 안의 이동 기록 평균이 놓은 속도다. */
export const VELOCITY_WINDOW_MS = 100;

/** 목표에서 이만큼 안이면 멈춘 것으로 본다(px). */
export const SETTLE_PX = 0.5;

/** 놓은 속도(px/s)로 미끄러질 거리(px). */
export function projectedDistance(velocity: number): number {
  return ((velocity / 1000) * DECELERATION) / (1 - DECELERATION);
}

/**
 * 인계 속도 상한 `|v0| ≤ ω·|x0|`(design-fix 20260924 F-preview A26 · `x0 = from − to`).
 * damping 1.0 스프링은 `v0` 가 이 상한을 넘을 때만 목표를 한 번 지나친다. 목표가 `clampView` 로
 * 잘린 자리(이동 범위 끝)면 그 넘침이 「움직이던 채로 끝에서 잘림」으로 보이므로 속도를 줄인다.
 * 잘리지 않은 투영 목표는 `|x0| ≈ 0.5 s × |v0|` 라 상한(≈ 7.8·|v0|)에 걸리지 않는다.
 */
export function capHandoffVelocity(v0: number, x0: number, response: number = SPRING_RESPONSE): number {
  const limit = ((2 * Math.PI) / response) * Math.abs(x0);
  if (Math.abs(v0) <= limit) return v0;
  return limit === 0 ? 0 : Math.sign(v0) * limit;
}

/**
 * 닫힌 식`x(t) = to + (x0 + (v0 + ω·x0)·t)·e^(−ω·t)` · `x0 = from − to`.
 * t = 0 에서 위치 = `from` · 속도 = `v0`. damping 1.0 이라 진동하지 않는다.
 */
export function spring(
  from: number,
  to: number,
  v0: number,
  t: number,
  response: number = SPRING_RESPONSE,
): { value: number; velocity: number } {
  const w = (2 * Math.PI) / response;
  const x0 = from - to;
  const b = v0 + w * x0;
  const decay = Math.exp(-w * t);
  return { value: to + (x0 + b * t) * decay, velocity: (v0 - w * b * t) * decay };
}
