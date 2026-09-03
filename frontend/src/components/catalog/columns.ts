// 열 정의 — 이름·조건 가능 여부·표기는 `Policy_데이터_찾기 §5` 그대로다.
import { TOPICS } from '../upload/types';
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

/**
 * 열 메뉴에 세울 값과 건수.
 *
 * ⭑ **`주제` 는 고정 4목록이다** — 값 집합이 표에 실린 행에서 나오지 않고
 * `Policy_업로드와_계보_확정 §5`(`〈55〉` DB CHECK)가 정한 넷으로 고정돼 있다.
 * 서버 패싯은 **지금 있는 값만** 세어 내려주므로, 그대로 그리면 아무도 아직 올리지 않은
 * 주제(예: `토지피복·LULC`)가 메뉴에서 통째로 사라진다 — 「그 주제가 없다」와
 * 「그 주제로 걸 수 없다」가 화면에서 갈리지 않는다 (QA 검수 #9).
 * **0건 값은 감추지 않고 흐리게 둔다** (`Policy_데이터_찾기 116행` 축자).
 *
 * 건수는 **서버가 준 값을 그대로 쓴다** — 화면이 세지 않는다. 서버가 말하지 않은 값만 0 이다.
 */
export function menuValues(
  column: CatalogColumn,
  values: { value: FacetValue; count: number }[],
): { value: FacetValue; count: number }[] {
  if (column !== '주제') return values;
  const counted = new Map(values.map((v) => [String(v.value), v.count]));
  return TOPICS.map((t) => ({ value: t as FacetValue, count: counted.get(t) ?? 0 }));
}

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
