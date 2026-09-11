import { useEffect, useRef, useState } from 'react';
import { durationMedian, recordDuration } from './durationSamples';

/** 서버가 관측시킨 단계만 잰다. 실패·취소된 단계는 완료 표본에 넣지 않는다. */
export function useStageRemaining(runId: string | undefined, stage: string | undefined, status: string | undefined): number | null {
  const active = useRef<{ runId: string; stage: string; started: number } | null>(null);
  const [remaining, setRemaining] = useState<number | null>(null);
  useEffect(() => {
    const previous = active.current;
    if (previous && previous.runId === runId && (status === '완료' || (status === '그리는 중' && stage && stage !== previous.stage))) {
      recordDuration(previous.stage, performance.now() - previous.started);
    }
    active.current = null;
    setRemaining(null);
    if (!runId || !stage || status !== '그리는 중') return;
    const started = performance.now();
    active.current = { runId, stage, started };
    // 이번 단계가 끝나기 전에 저장된 표본만 이 요청의 추정에 쓴다.
    const median = durationMedian(stage);
    if (median === null) return;
    const update = () => setRemaining(Math.max(0, median - (performance.now() - started)));
    update();
    const timer = window.setInterval(update, 1000);
    return () => window.clearInterval(timer);
  }, [runId, stage, status]);
  return remaining;
}
