// S-03 카탈로그의 화면 상태 타입.
// 표기·값 집합은 전부 계약 생성물에서 온다 — 여기서 다시 선언하지 않는다 (CLAUDE.md §3-6·§3-7).
import type { components } from '../../generated/fe-core';

type S = components['schemas'];

export type CatalogColumn = S['CatalogColumn'];
export type SortOrder = S['SortOrder'];
export type DatasetRow = S['DatasetRow'];
export type MapState = S['MapState'];
export type FacetSet = S['FacetSet'];
export type LineageState = S['LineageState'];

/** 열 메뉴에서 고른 값. 열에 따라 문자열·정수·불리언이다 (`FacetSet.values[].value` 와 같은 집합). */
export type FacetValue = string | number | boolean;

/** 열 조건. 열 메뉴가 유일한 조작 자리다 (`Policy_데이터_찾기 §1.3-9`). */
export type CatalogFilters = Partial<Record<CatalogColumn, FacetValue[]>>;

/**
 * ⭑ **⟨20차 해제 · PRD-05 · `WU-B7`⟩ 분류 3축.** 열이 아니라 **필터 바**의 축이다 —
 * 정렬 대상이 아니라서 `CatalogColumn` 에 넣지 않았고, 패싯도 `axes` 로 갈라져 온다.
 */
export type AxisName = '분류' | '유형' | '가공 단계';

/** 축 이름 셋. 화면의 순서이자 상세 3행의 순서다 (PRD-06 축자). */
export const AXES: AxisName[] = ['분류', '유형', '가공 단계'];

/**
 * 축마다 **한 값**이다 — 셀렉트 하나가 한 축을 맡는다(rev1 필터 바 문면).
 * 값이 없으면 그 축은 조건이 아니다(`분류 전체`).
 */
export type AxisFilters = Partial<Record<AxisName, string>>;

export type CatalogSort = { column: CatalogColumn; order: SortOrder };

export type CatalogQuery = { sort: CatalogSort; filters: CatalogFilters; axes: AxisFilters; mapState?: MapState };

/** 기본 정렬은 **수정일 최신순** (`Policy_데이터_찾기 §5` 기본 정렬). */
export const DEFAULT_SORT: CatalogSort = { column: '수정일', order: '내림' };

export type CatalogList = { items: DatasetRow[]; totalCount: number };

/**
 * 표를 채우는 곳. 실서버(`listDatasets`·`listDatasetFacets`)와 픽스처가 같은 얼굴을 쓴다 —
 * 서버가 501 을 그만 내면 화면 코드는 한 줄도 바뀌지 않는다.
 */
export interface CatalogSource {
  list(query: CatalogQuery): Promise<CatalogList>;
  facets(query: CatalogQuery): Promise<FacetSet>;
}
