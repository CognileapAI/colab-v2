import { beforeEach, expect, it } from 'vitest';
import { durationMedian, recordDuration, progressRemaining } from '../src/components/preview/durationSamples';

beforeEach(() => localStorage.clear());

it('표본이 없으면 추정값이 없고 실제 완료 시간의 중앙값만 쓴다', () => {
  expect(durationMedian('전송')).toBeNull();
  expect(progressRemaining('전송', 0.5)).toBeNull();
  for (const ms of [1000, 2000, 100000]) recordDuration('전송', ms);
  expect(durationMedian('전송')).toBe(2000);
  expect(progressRemaining('전송', 0.25)).toBe(1500);
  recordDuration('전송', 4000);
  expect(durationMedian('전송')).toBe(3000);
  expect(durationMedian('지도 그리는 중')).toBeNull();
});

it('잘못된 관측치와 손상된 저장값은 추정 시간을 만들지 않는다', () => {
  for (const ms of [NaN, Infinity, -1, 0]) recordDuration('전송', ms);
  expect(durationMedian('전송')).toBeNull();
  localStorage.setItem('colab.stage-durations.v1', '{broken');
  expect(durationMedian('전송')).toBeNull();
});
