// 표기 규칙. **값을 고치지 않는다** — 보이는 모양만 정한다.
import type { ProjectDatasetRow, ProjectRow } from './types';

/**
 * 프로젝트 기간. 일자를 보존하고 같은 해의 종료는 연도만 접는다.
 */
export function projectPeriod(period: ProjectRow['period']): string {
  if (!period || (!period.start && !period.end)) return '';
  const start = period.start ? period.start.replaceAll('-', '.') : '';
  if (!period.end) return `${start}~`;
  const sameYear = period.start?.slice(0, 4) === period.end.slice(0, 4);
  return `${start}~${sameYear ? period.end.slice(5).replace('-', '.') : period.end.replaceAll('-', '.')}`;
}

/**
 * 데이터가 다루는 기간. 한 해를 통째로 덮으면 `2024 전체`, 같은 해 안이면 `2025-06~09`,
 * 한 달이면 `2025-06` 이다 — 목업의 `t` 표기 그대로다.
 */
export function dataPeriod(period: ProjectDatasetRow['period']): string {
  if (!period) return '—';
  // **끝이 없으면 무기한이다** (14차 해제). 표기는 바로 위 `projectPeriod` 와 같은
  // 꼬리 물결이다 — 한 표 안에서 「열려 있다」를 두 모양으로 그리지 않는다.
  if (!period.end) return `${period.start.slice(0, 4)}-${period.start.slice(5, 7)}~`;
  const [sy, sm] = [period.start.slice(0, 4), period.start.slice(5, 7)];
  const [ey, em] = [period.end.slice(0, 4), period.end.slice(5, 7)];
  if (sy !== ey) return `${sy}-${sm}~${ey}-${em}`;
  if (sm === '01' && em === '12') return `${sy} 전체`;
  return sm === em ? `${sy}-${sm}` : `${sy}-${sm}~${em}`;
}
