// 지수 백오프 + 지터 ±30%. 500ms ×2, 최대 5회는 호출자 규칙이다.
// 근거: dev-package/PLAN-SoT.md §9 〈338〉 (전송 재시도는 파트 단위)

export const MAX_ATTEMPTS = 5;

export function backoffDelay(attempt: number, baseMs = 500): number {
  const base = baseMs * 2 ** attempt;
  const jitter = (Math.random() * 2 - 1) * 0.3; // ±30% — 동시 재시도의 떼몰림을 흩는다
  return base * (1 + jitter);
}

export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}
