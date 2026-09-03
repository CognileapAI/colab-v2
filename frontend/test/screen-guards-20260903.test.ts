/**
 * 화면 소결함 둘 — 구간 수 빈 칸 · 「오늘」의 경계 (`CODE-REVIEW-20260903` 부록).
 *
 * **red 를 먼저 봤다.**
 *  · `Number('')` 이 0 이라 구간 수 칸을 비우면 계약 밖(3~9)의 0 이 다음 그리기에 실렸다.
 *  · `relativeTime` 이 지금에서 24시간을 빼는 창이라 **어제 23시가 오늘 아침에 「오늘」**이었다.
 */
import { describe, expect, it } from 'vitest';
import { classCountOf } from '../src/components/upload/PreviewPanel';
import { relativeTime } from '../src/components/dashboard/visits';

describe('구간 수 — 빈 칸은 0 이 아니다', () => {
  it('빈 칸·공백·숫자가 아닌 것은 기본값 6 이다', () => {
    expect(classCountOf('')).toBe(6);
    expect(classCountOf('   ')).toBe(6);
    expect(classCountOf('여섯')).toBe(6);
    // 계약 `RenderStyle.classCount` 는 3~9 다 — 0 은 어느 갈래로도 나가면 안 된다.
    expect(classCountOf('')).not.toBe(0);
  });

  it('고른 값은 그대로 읽는다', () => {
    expect(classCountOf('3')).toBe(3);
    expect(classCountOf('9')).toBe(9);
  });
});

describe('「오늘」은 24시간이 아니라 달력 날짜다', () => {
  // 지역 시간으로 만든다 — 이 함수가 재는 것이 **보는 사람의 달력**이기 때문이다.
  const at = (y: number, m: number, d: number, h: number) => new Date(y, m - 1, d, h);
  const iso = (y: number, m: number, d: number, h: number) => at(y, m, d, h).toISOString();

  it('어제 23시에 연 것은 오늘 아침에 「어제」다', () => {
    // 24시간 창으로 세면 차가 9시간이라 「오늘」이 나왔다 — 그것이 고친 결함이다.
    expect(relativeTime(iso(2026, 9, 2, 23), at(2026, 9, 3, 8))).toBe('어제');
  });

  it('같은 날 0시 5분에 연 것은 그날 밤 23시에도 「오늘」이다', () => {
    expect(relativeTime(iso(2026, 9, 3, 0), at(2026, 9, 3, 23))).toBe('오늘');
  });

  it('날짜 수만큼 센다 — 시각이 아니라 날이 단위다', () => {
    expect(relativeTime(iso(2026, 8, 31, 22), at(2026, 9, 3, 1))).toBe('3일 전');
    expect(relativeTime(iso(2026, 9, 1, 1), at(2026, 9, 3, 22))).toBe('2일 전');
  });

  it('앞날은 「오늘」로 접는다 — 음수 날짜를 지어내지 않는다', () => {
    expect(relativeTime(iso(2026, 9, 4, 1), at(2026, 9, 3, 22))).toBe('오늘');
  });
});
