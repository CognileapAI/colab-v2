// 픽스처용 조회 엔진. 서버가 `listDatasets`·`listDatasetFacets` 로 하는 일과 **같은 규칙**을 쓴다.
// 여기서 규칙을 새로 만들지 않는다 — 서버가 붙으면 이 파일은 쓰이지 않고 화면은 그대로다.
import { FILTERABLE, LINEAGE_ORDER } from './columns';
import type {
  CatalogColumn,
  CatalogFilters,
  CatalogList,
  CatalogQuery,
  DatasetRow,
  FacetSet,
  FacetValue,
} from './types';

/** 한 행에서 그 열이 갖는 조건값. 조건을 걸 수 있는 다섯 열만 답한다. */
export function cellValue(row: DatasetRow, column: CatalogColumn): FacetValue | null {
  switch (column) {
    case '주제':
      return row.topic;
    case 'Level':
      return row.processingLevel;
    case '업로더':
      return row.uploader.accountId;
    case '계보':
      return row.lineageState;
    case 'Verified':
      return row.verified;
    default:
      return null;
  }
}

function matches(row: DatasetRow, filters: CatalogFilters, except?: CatalogColumn): boolean {
  for (const column of FILTERABLE) {
    if (column === except) continue;
    const picked = filters[column];
    if (!picked || picked.length === 0) continue;
    const v = cellValue(row, column);
    if (!picked.some((p) => p === v)) return false;
  }
  return true;
}

function sortKey(row: DatasetRow, column: CatalogColumn): string | number {
  switch (column) {
    case '데이터셋':
      return row.name;
    case '주제':
      return row.topic ?? '';
    case 'Level':
      return row.processingLevel;
    case '프로젝트':
      return row.projects.representative?.name ?? '';
    case '업로더':
      return row.uploader.name;
    case '수정일':
      return row.lastModifiedAt;
    case '계보':
      return LINEAGE_ORDER.indexOf(row.lineageState);
    case 'Verified':
      return row.verified ? 1 : 0;
  }
}

export function runQuery(rows: DatasetRow[], query: CatalogQuery): CatalogList {
  const kept = rows.filter((r) => matches(r, query.filters));
  const dir = query.sort.order === '오름' ? 1 : -1;
  kept.sort((a, b) => {
    const x = sortKey(a, query.sort.column);
    const y = sortKey(b, query.sort.column);
    const r =
      typeof x === 'number' && typeof y === 'number' ? x - y : String(x).localeCompare(String(y), 'ko');
    return r * dir;
  });
  return { items: kept, totalCount: kept.length };
}

/**
 * 값별 건수. **다른 열에 걸린 조건을 먼저 적용한 뒤에 센다** (`Policy_데이터_찾기 §5` 값별 건수).
 * 0건인 값도 목록에서 빼지 않는다 — 화면이 흐리게 둔다.
 */
export function runFacets(rows: DatasetRow[], query: CatalogQuery): FacetSet {
  return {
    columns: FILTERABLE.map((column) => {
      const all: FacetValue[] = [];
      for (const row of rows) {
        const v = cellValue(row, column);
        if (v === null) continue;
        if (!all.some((x) => x === v)) all.push(v);
      }
      if (column === '계보') {
        all.sort((a, b) => LINEAGE_ORDER.indexOf(String(a)) - LINEAGE_ORDER.indexOf(String(b)));
      } else if (column === 'Verified') {
        all.sort((a, b) => Number(b) - Number(a));
      } else if (column === 'Level') {
        all.sort((a, b) => Number(a) - Number(b));
      } else if (column === '업로더') {
        const names = new Map(rows.map((r) => [r.uploader.accountId, r.uploader.name]));
        all.sort((a, b) =>
          String(names.get(String(a)) ?? a).localeCompare(String(names.get(String(b)) ?? b), 'ko'),
        );
      } else {
        all.sort((a, b) => String(a).localeCompare(String(b), 'ko'));
      }
      const base = rows.filter((r) => matches(r, query.filters, column));
      return {
        column,
        values: all.map((value) => ({
          value,
          count: base.filter((r) => cellValue(r, column) === value).length,
        })),
      };
    }),
  };
}
