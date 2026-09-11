const KEY = 'colab.stage-durations.v1';
const MAX_SAMPLES = 20;

function samples(): Record<string, number[]> {
  try {
    const raw: unknown = JSON.parse(localStorage.getItem(KEY) ?? '{}');
    if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return {};
    return Object.fromEntries(Object.entries(raw).filter(([, value]) => Array.isArray(value))
      .map(([key, value]) => [key, (value as unknown[])
        .filter((n): n is number => typeof n === 'number' && Number.isFinite(n) && n > 0).slice(-MAX_SAMPLES)]));
  } catch { return {}; }
}

export function recordDuration(stage: string, milliseconds: number): void {
  if (!Number.isFinite(milliseconds) || milliseconds <= 0) return;
  const data = samples();
  data[stage] = [...(data[stage] ?? []), milliseconds].slice(-MAX_SAMPLES);
  try { localStorage.setItem(KEY, JSON.stringify(data)); } catch { /* 저장 불가면 다음 관측에서 다시 시작한다. */ }
}

export function durationMedian(stage: string): number | null {
  const values = (samples()[stage] ?? []).sort((a, b) => a - b);
  if (!values.length) return null;
  const middle = Math.floor(values.length / 2);
  return values.length % 2 ? values[middle]! : (values[middle - 1]! + values[middle]!) / 2;
}

export function progressRemaining(stage: string, fraction: number): number | null {
  const median = durationMedian(stage);
  if (median === null || !Number.isFinite(fraction)) return null;
  return median * (1 - Math.max(0, Math.min(1, fraction)));
}
