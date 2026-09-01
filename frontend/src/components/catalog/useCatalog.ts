// 카탈로그의 화면 상태. 조건·정렬은 여기 한 곳에만 산다 (표 헤더가 유일한 조작 자리이므로).
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type {
  CatalogColumn,
  CatalogFilters,
  CatalogList,
  CatalogQuery,
  CatalogSource,
  FacetSet,
  FacetValue,
  SortOrder,
} from './types';
import { DEFAULT_SORT } from './types';

export type CatalogState = {
  query: CatalogQuery;
  list: CatalogList | null;
  facets: FacetSet | null;
  /** 조건이 하나도 없을 때의 전체 건수. 첫 조회에서 기억한다 */
  baseTotal: number | null;
  error: string | null;
  hasConditions: boolean;
  setSort: (column: CatalogColumn, order: SortOrder) => void;
  toggleValue: (column: CatalogColumn, value: FacetValue) => void;
  clearColumn: (column: CatalogColumn) => void;
  clearAll: () => void;
};

/**
 * 처음 걸고 들어오는 조건. **데이터 맵의 막대가 이 자리로 온다** — 「막대는 전부 눌려 그
 * 조건이 걸린 카탈로그로 간다」(`Policy_홈_대시보드 §8` 축자 · WU-P7). 조건 없이 열면
 * 맵에서 누른 묶음과 카탈로그가 다른 것을 보여줘 두 화면이 서로 다른 연구실이 된다.
 *
 * ⚠ 조건의 **조작 자리는 여전히 표 헤더 하나뿐이다** — 이 값은 첫 상태일 뿐이고
 * 조건 툴바를 새로 만들지 않는다 (`Policy_데이터_찾기 §1.3-9`).
 */
export function useCatalog(source: CatalogSource, initialFilters: CatalogFilters = {}): CatalogState {
  const [query, setQuery] = useState<CatalogQuery>({ sort: DEFAULT_SORT, filters: initialFilters });
  const [list, setList] = useState<CatalogList | null>(null);
  const [facets, setFacets] = useState<FacetSet | null>(null);
  const [error, setError] = useState<string | null>(null);
  const baseTotal = useRef<number | null>(null);

  const hasConditions = useMemo(
    () => Object.values(query.filters).some((v) => v && v.length > 0),
    [query.filters],
  );

  useEffect(() => {
    let alive = true;
    Promise.all([source.list(query), source.facets(query)])
      .then(([l, f]) => {
        if (!alive) return;
        if (baseTotal.current === null && !hasConditions) baseTotal.current = l.totalCount;
        setList(l);
        setFacets(f);
        setError(null);
      })
      .catch((e: unknown) => {
        if (alive) setError(e instanceof Error ? e.message : '목록을 불러오지 못했어요.');
      });
    return () => {
      alive = false;
    };
  }, [source, query, hasConditions]);

  const setSort = useCallback((column: CatalogColumn, order: SortOrder) => {
    setQuery((q) => ({ ...q, sort: { column, order } }));
  }, []);

  /** 한 열에서 값을 여러 개 고른다 (`Policy_데이터_찾기 §5`). 다시 누르면 그 값만 풀린다 */
  const toggleValue = useCallback((column: CatalogColumn, value: FacetValue) => {
    setQuery((q) => {
      const picked = q.filters[column] ?? [];
      const next = picked.some((v) => v === value)
        ? picked.filter((v) => v !== value)
        : [...picked, value];
      const filters = { ...q.filters };
      if (next.length === 0) delete filters[column];
      else filters[column] = next;
      return { ...q, filters };
    });
  }, []);

  const clearColumn = useCallback((column: CatalogColumn) => {
    setQuery((q) => {
      const filters = { ...q.filters };
      delete filters[column];
      return { ...q, filters };
    });
  }, []);

  const clearAll = useCallback(() => setQuery((q) => ({ ...q, filters: {} })), []);

  return {
    query,
    list,
    facets,
    baseTotal: baseTotal.current,
    error,
    hasConditions,
    setSort,
    toggleValue,
    clearColumn,
    clearAll,
  };
}
