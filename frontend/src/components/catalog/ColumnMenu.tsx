// 열 메뉴 — 위쪽 `정렬(오름/내림)`, 아래쪽 `값 목록(건수)` (`Policy_데이터_찾기 §8` 열 메뉴).
// 값을 고르는 동안 메뉴는 닫히지 않는다. 조건이 걸린 열에는 `이 열 조건 지우기` 가 생긴다.
import { isFilterable, menuValues, valueLabel } from './columns';
import type { CatalogColumn, CatalogSort, FacetSet, FacetValue, SortOrder } from './types';

export function ColumnMenu(props: {
  column: CatalogColumn;
  sort: CatalogSort;
  picked: FacetValue[];
  facets: FacetSet | null;
  uploaderNames: Map<string, string>;
  onSort: (column: CatalogColumn, order: SortOrder) => void;
  onToggle: (column: CatalogColumn, value: FacetValue) => void;
  onClearColumn: (column: CatalogColumn) => void;
}) {
  const { column, sort, picked } = props;
  const values = menuValues(
    column,
    props.facets?.columns.find((c) => c.column === column)?.values ?? [],
  );

  return (
    <div
      className="colmenu"
      role="menu"
      aria-label={`${column} 열 메뉴`}
      onClick={(e) => e.stopPropagation()}
    >
      <div className="cm-s">정렬</div>
      <button
        type="button"
        role="menuitem"
        className={`cm-i${sort.column === column && sort.order === '오름' ? ' on' : ''}`}
        onClick={() => props.onSort(column, '오름')}
      >
        오름차순
      </button>
      <button
        type="button"
        role="menuitem"
        className={`cm-i${sort.column === column && sort.order === '내림' ? ' on' : ''}`}
        onClick={() => props.onSort(column, '내림')}
      >
        내림차순
      </button>

      {isFilterable(column) && (
        <>
          <div className="cm-hr" />
          <div className="cm-s">{column}</div>
          {values.map((v) => {
            const on = picked.some((p) => p === v.value);
            // 눌러도 0건인 값은 감추지 않고 흐리게 둔다 (`§5` 값별 건수)
            const zero = v.count === 0 && !on;
            return (
              <button
                type="button"
                role="menuitemcheckbox"
                aria-checked={on}
                key={String(v.value)}
                className={`cm-i${on ? ' on' : ''}${zero ? ' is-zero' : ''}`}
                onClick={() => props.onToggle(column, v.value)}
              >
                <span className="cm-box" aria-hidden="true">
                  {on ? '✓' : ''}
                </span>
                <span className="cm-l">{valueLabel(column, v.value, props.uploaderNames)}</span>
                <span className="cm-n">({v.count})</span>
              </button>
            );
          })}
          {picked.length > 0 && (
            <>
              <div className="cm-hr" />
              <button
                type="button"
                role="menuitem"
                className="cm-clr"
                onClick={() => props.onClearColumn(column)}
              >
                이 열 조건 지우기
              </button>
            </>
          )}
        </>
      )}
    </div>
  );
}
