// S-02 프로젝트 목록 · S-02b 상세의 화면 상태 타입.
// 표기·값 집합은 전부 계약 생성물에서 온다 — 여기서 다시 선언하지 않는다 (CLAUDE.md §3-6·§3-7).
import type { components } from '../../generated/fe-core';

type S = components['schemas'];

export type ProjectRow = S['ProjectRow'];
export type ProjectDetail = S['ProjectDetail'];
export type ProjectDatasetRow = S['ProjectDatasetRow'];
export type ProjectSort = S['ProjectSort'];
// 두 값 집합은 `common.json` 의 것이고, 계약 행에서 **끌어다 쓴다** — 다시 적지 않는다.
export type ProjectStatus = ProjectRow['status'];
export type ProjectType = ProjectRow['type'];

/** 상태·유형 조건의 「전체」. **계약에는 없다** — 파라미터를 빼는 것이 「거르지 않는다」다. */
export const ALL = '전체' as const;

export type StatusFilter = ProjectStatus | typeof ALL;
export type TypeFilter = ProjectType | typeof ALL;

/** 카드와 표는 **같은 거른 결과**를 그린다. 필터·정렬은 한 벌뿐이다 (`Policy_프로젝트 §5`). */
export type ProjectView = '카드' | '표';

export type ProjectQuery = {
  status: StatusFilter;
  type: TypeFilter;
  sort: ProjectSort;
};

/**
 * 목록 기본값 — 상태 `진행 중` · 유형 전체 · 정렬 `최근 시작 순` (`§5` 목록 기본값).
 * **기본은 카드다** — 고를 때는 카드, 견줄 때는 표다 (§5).
 */
export const DEFAULT_QUERY: ProjectQuery = { status: '진행 중', type: ALL, sort: '최근 시작 순' };
export const DEFAULT_VIEW: ProjectView = '카드';

export const SORTS: ProjectSort[] = [
  '최근 시작 순',
  '먼저 시작한 순',
  '최근 종료 순',
  '데이터셋 많은 순',
];

export type ProjectList = { items: ProjectRow[]; totalCount: number };

/** 프로젝트가 없다 — 지워졌거나 남의 연구실이다. 계약은 둘을 같은 404 로 낸다 (P-9·P-10). */
export class ProjectGone extends Error {}

/**
 * 목록·상세를 채우는 곳. 실서버(`listProjects`·`getProject`)와 픽스처가 같은 얼굴을 쓴다.
 * `hiddenClosed` 는 **봉투에 없는 값**이라 여기서 두 번째 질의로 얻는다 — 상태만 `닫힘` 으로
 * 바꿔 부른 `totalCount` 다 (계약 `listProjects` 산문).
 */
export interface ProjectSource {
  list(query: ProjectQuery): Promise<ProjectList>;
  get(projectId: string): Promise<ProjectDetail>;
}
