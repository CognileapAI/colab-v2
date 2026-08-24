// 표기 규칙. **값을 고치지 않는다** — 보이는 모양만 정한다.
import type { ProjectDatasetRow, ProjectRow } from './types';

/**
 * 프로젝트 기간 — 목업 표기 그대로다. 같은 해면 종료의 연도를 접고(`2025.03~12`),
 * 해가 다르면 둘 다 편다(`2024.06~2025.02`). **진행 중이면 종료가 비어 있다** (§5).
 */
export function projectPeriod(period: ProjectRow['period']): string {
  if (!period || (!period.start && !period.end)) return '';
  const start = period.start ? period.start.replace('-', '.') : '';
  if (!period.end) return `${start}~`;
  const sameYear = period.start?.slice(0, 4) === period.end.slice(0, 4);
  return `${start}~${sameYear ? period.end.slice(5, 7) : period.end.replace('-', '.')}`;
}

/**
 * 데이터가 다루는 기간. 한 해를 통째로 덮으면 `2024 전체`, 같은 해 안이면 `2025-06~09`,
 * 한 달이면 `2025-06` 이다 — 목업의 `t` 표기 그대로다.
 */
export function dataPeriod(period: ProjectDatasetRow['period']): string {
  if (!period) return '—';
  const [sy, sm] = [period.start.slice(0, 4), period.start.slice(5, 7)];
  const [ey, em] = [period.end.slice(0, 4), period.end.slice(5, 7)];
  if (sy !== ey) return `${sy}-${sm}~${ey}-${em}`;
  if (sm === '01' && em === '12') return `${sy} 전체`;
  return sm === em ? `${sy}-${sm}` : `${sy}-${sm}~${em}`;
}
