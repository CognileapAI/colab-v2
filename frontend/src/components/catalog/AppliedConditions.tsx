// 적용된 조건 칩 줄 — 표 바로 위 한 곳. 조건이 없으면 **줄째로 사라진다** (`Policy_데이터_찾기 §8`).
import { valueLabel } from './columns';
import type { CatalogColumn, CatalogFilters, FacetValue } from './types';

export function AppliedConditions(props: {
  filters: CatalogFilters;
  uploaderNames: Map<string, string>;
  onToggle: (column: CatalogColumn, value: FacetValue) => void;
  onClearAll: () => void;
}) {
  const entries = Object.entries(props.filters) as [CatalogColumn, FacetValue[]][];
  const chips = entries.flatMap(([column, values]) =>
    (values ?? []).map((value) => ({ column, value })),
  );
  if (chips.length === 0) return null;

  return (
    <div className="fchips" data-testid="applied-conditions">
      <span className="fl">적용된 조건</span>
      {chips.map(({ column, value }) => {
        const label = valueLabel(column, value, props.uploaderNames);
        return (
          <span className="fc" key={`${column}:${String(value)}`}>
            <b>{column}</b> {label}{' '}
            <button
              type="button"
              aria-label={`${column} ${label} 조건 해제`}
              onClick={() => props.onToggle(column, value)}
            >
              ×
            </button>
          </span>
        );
      })}
      <button type="button" className="fall" onClick={props.onClearAll}>
        전체 해제
      </button>
    </div>
  );
}
