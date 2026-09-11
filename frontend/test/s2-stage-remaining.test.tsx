import { renderHook } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { durationMedian, recordDuration } from '../src/components/preview/durationSamples';
import { useStageRemaining } from '../src/components/preview/useStageRemaining';

beforeEach(() => localStorage.clear());
afterEach(() => vi.restoreAllMocks());

it('표본 없는 단계는 추정값이 없고 완료된 단계 표본은 다음 요청부터 쓴다', () => {
  const now = vi.spyOn(performance, 'now').mockReturnValue(100);
  const view = renderHook(({ id, stage, status }) => useStageRemaining(id, stage, status), {
    initialProps: { id: 'R1', stage: '파일 읽는 중', status: '그리는 중' },
  });
  expect(view.result.current).toBeNull();
  now.mockReturnValue(2100);
  view.rerender({ id: 'R1', stage: '지도 그리는 중', status: '그리는 중' });
  expect(durationMedian('파일 읽는 중')).toBe(2000);
  expect(view.result.current).toBeNull();
  now.mockReturnValue(5100);
  view.rerender({ id: 'R1', stage: '', status: '완료' });
  expect(durationMedian('지도 그리는 중')).toBe(3000);
  view.rerender({ id: 'R2', stage: '파일 읽는 중', status: '그리는 중' });
  expect(view.result.current).toBe(2000);
});

it('실패와 새 요청으로 취소된 단계는 완료 시간 표본에 넣지 않는다', () => {
  recordDuration('파일 읽는 중', 8000);
  const view = renderHook(({ id, status }) => useStageRemaining(id, '파일 읽는 중', status), {
    initialProps: { id: 'R1', status: '그리는 중' },
  });
  view.rerender({ id: 'R1', status: '실패' });
  expect(view.result.current).toBeNull();
  expect(durationMedian('파일 읽는 중')).toBe(8000);
  view.rerender({ id: 'R2', status: '그리는 중' });
  view.rerender({ id: 'R3', status: '그리는 중' });
  expect(durationMedian('파일 읽는 중')).toBe(8000);
});
