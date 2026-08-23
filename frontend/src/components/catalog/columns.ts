// 열 정의 — 이름·조건 가능 여부·표기는 `Policy_데이터_찾기 §5` 그대로다.
import type { CatalogColumn, FacetValue } from './types';

/** 8열. 순서와 글자를 바꾸지 않는다 (`CatalogColumn` enum 과 같은 순서). */
export const COLUMNS: CatalogColumn[] = [
  '데이터셋',
  '주제',
  'Level',
  '프로젝트',
  '업로더',
  '수정일',
  '계보',
  'Verified',
];

/** 조건을 걸 수 있는 열은 다섯이고, 나머지 열은 정렬만 갖는다 (`§5` 카탈로그 조건). */
export const FILTERABLE: CatalogColumn[] = ['주제', 'Level', '업로더', '계보', 'Verified'];

/** 계보 열의 값 차례. 정본이 적어 둔 네 표기 순서다 (`§5` 계보 열 표기). */
export const LINEAGE_ORDER = ['확정', '확인 필요', '기록 없음', '원천'];

export function isFilterable(column: CatalogColumn): boolean {
  return FILTERABLE.includes(column);
}

/**
 * 열 메뉴·칩 줄에 보이는 값 글자.
 * `업로더` 는 조건을 계정 ID 로 걸지만(계약 `FilterUploader`) 사람에게는 이름을 보인다 —
 * 이름은 지금 표에 실린 행에서 찾는다.
 */
export function valueLabel(
  column: CatalogColumn,
  value: FacetValue,
  uploaderNames: Map<string, string>,
): string {
  if (column === 'Level') return `Lv${value}`;
  if (column === 'Verified') return value === true ? 'Verified' : '승인 전';
  if (column === '업로더') return uploaderNames.get(String(value)) ?? String(value);
  return String(value);
}
