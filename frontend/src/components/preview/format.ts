// 미리보기 범례의 **표시 규칙**.
//
// 왜 생겼나 (화면 검수 2026-09-03 #20): 범례가 `0.18798384070396423 ~ 0.27763089040915173` 로
// 부동소수를 **17자리 그대로** 찍고 있었다. 정본은 이 자리의 자릿수를 정하지 않았고, 기대는
// 「사람이 읽는 범례 값」이다 — 그래서 **읽을 수 있는 자릿수로 끊되 값을 지어내지 않는다.**
//
// 규칙 셋 — ⑴ 유효숫자 4자리에서 끊고 꼬리 0 은 지운다 ⑵ 정수는 정수로 둔다(없는 소수점을
// 만들지 않는다) ⑶ 사람이 못 읽는 크기(1e-4 미만 · 1e6 이상)는 **지수로 적는다** — 0 으로
// 뭉개면 「값이 아주 작다」가 「값이 없다」로 화면에서 바뀐다.
const SIGNIFICANT = 4;

export function legendValue(n: number): string {
  if (!Number.isFinite(n)) return '—';
  if (n === 0) return '0';
  const a = Math.abs(n);
  if (a >= 1e6 || a < 1e-4) return n.toExponential(2);
  return String(Number(n.toPrecision(SIGNIFICANT)));
}
