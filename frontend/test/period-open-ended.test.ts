/**
 * 끝이 없는 기간 = **무기한·진행 중** (계약 `DataPeriod.end`: `[string, "null"]` ·
 * 14차 해제 · Ted 판정 2026-09-02).
 *
 * ⚠ **`[미확인]` — 문면 무근거.** 화면 정본(UI 스펙 19)은 기간을 자유 입력 한 칸으로 적고
 * **열린 기간의 표기를 정하지 않았다.** 여기 문자열은 레포 안 선례를 따른 것이다 —
 * 상세 격자는 `~ 진행 중`, 소속 데이터셋 표는 같은 파일의 `projectPeriod` 가 이미 쓰는
 * **꼬리 물결**(`2025.03~`)이다. 스펙 문면이 정해지면 그것이 이긴다.
 */
import { describe, expect, it } from 'vitest';

import { EMPTY, formatPeriod } from '../src/components/detail/format';
import { dataPeriod } from '../src/components/project/format';

describe('무기한 기간 표기', () => {
  it('상세 기본 정보 — 끝이 없으면 진행 중이라고 말한다', () => {
    expect(formatPeriod({ start: '2025-06-01T00:00:00Z', end: null })).toBe('2025-06 ~ 진행 중');
  });

  it('상세 기본 정보 — 끝이 있으면 종전 표기가 그대로다 (회귀)', () => {
    expect(formatPeriod({ start: '2025-06-01T00:00:00Z', end: '2025-09-30T00:00:00Z' }))
      .toBe('2025-06 ~ 09');
    expect(formatPeriod(null)).toBe(EMPTY);
  });

  it('소속 데이터셋 표 — 끝이 없으면 꼬리 물결이다', () => {
    expect(dataPeriod({ start: '2025-06-01T00:00:00Z', end: null })).toBe('2025-06~');
  });

  it('소속 데이터셋 표 — 끝이 있으면 종전 표기가 그대로다 (회귀)', () => {
    expect(dataPeriod({ start: '2024-01-01T00:00:00Z', end: '2024-12-31T00:00:00Z' }))
      .toBe('2024 전체');
    expect(dataPeriod({ start: '2025-06-01T00:00:00Z', end: '2025-09-30T00:00:00Z' }))
      .toBe('2025-06~09');
    expect(dataPeriod(null)).toBe('—');
  });
});
