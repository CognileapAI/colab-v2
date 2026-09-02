// 카탈로그 표 — 8열 + 오른쪽 끝 빠른 작업 자리 (`Policy_데이터_찾기 §5`).
// 조건과 정렬은 **표 헤더에만** 있다. 조건 툴바도 좌측 패싯 사이드바도 두지 않는다 (§1.3-9).
// 잠긴 행은 사라지지 않는다 — 자물쇠와 `잠김` 칩이 붙을 뿐이다 (§8 · P-13).
import { useEffect, useState } from 'react';
import { API_BASE_URL } from '../../api/client';
import { downloadDataset } from '../../api/download';
import { COLUMNS, isFilterable } from './columns';
import { ColumnMenu } from './ColumnMenu';
import type { CatalogColumn, DatasetRow, FacetValue, SortOrder } from './types';
import type { CatalogState } from './useCatalog';

/** 수정일 칸은 날짜만 적는다 (목업 `2026-08-11`). */
function day(ts: string): string {
  return ts.slice(0, 10);
}

const EYE = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" aria-hidden="true">
    <path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7-10-7-10-7Z" />
    <circle cx="12" cy="12" r="3" />
  </svg>
);
const DL = (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.9"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
  >
    <path d="M12 3v12M7 11l5 5 5-5" />
    <path d="M4 20h16" />
  </svg>
);

function lineageTitle(row: DatasetRow): string | undefined {
  // 확정한 날과 바뀐 날은 마우스를 올렸을 때 알린다 (`§8` 계보 열). 칸 안에는 숫자를 넣지 않는다
  if (row.lineageState !== '확인 필요' || !row.lineageConfirmedAt) return undefined;
  return `${day(row.lineageConfirmedAt)} 에 확정했는데 ${day(row.lastModifiedAt)} 에 파일이 바뀌었어요`;
}

export function CatalogTable(props: {
  state: CatalogState;
  uploaderNames: Map<string, string>;
  onOpen: (datasetId: string) => void;
}) {
  const { state } = props;
  const [openColumn, setOpenColumn] = useState<CatalogColumn | null>(null);
  // 내려받기가 실패하면 조용히 넘어가지 않는다 — 눌렀는데 아무 일도 안 일어나는 것이 제일 나쁘다.
  const [downloadError, setDownloadError] = useState<string | null>(null);

  // 바깥을 누르면 닫힌다. 열 이름·메뉴 안의 클릭은 stopPropagation 으로 삼킨다
  useEffect(() => {
    const close = () => setOpenColumn(null);
    document.addEventListener('click', close);
    return () => document.removeEventListener('click', close);
  }, []);

  function pick(column: CatalogColumn, order: SortOrder) {
    state.setSort(column, order);
    setOpenColumn(null);
  }
  function toggle(column: CatalogColumn, value: FacetValue) {
    state.toggleValue(column, value); // 메뉴는 열어 둔다 — 연달아 고를 수 있어야 한다
  }
  function clearColumn(column: CatalogColumn) {
    state.clearColumn(column);
    setOpenColumn(null);
  }

  const rows = state.list?.items ?? [];

  return (
    <div className="tblwrap" data-scroll="both">
      <table className="tbl catalog" aria-label="데이터셋 목록">
        <thead>
          <tr>
            {COLUMNS.map((column) => {
              const sorted = state.query.sort.column === column;
              const filtered = (state.query.filters[column] ?? []).length > 0;
              return (
                <th
                  key={column}
                  scope="col"
                  data-col={column}
                  aria-sort={
                    sorted
                      ? state.query.sort.order === '오름'
                        ? 'ascending'
                        : 'descending'
                      : 'none'
                  }
                  className={[
                    sorted ? 'is-sorted' : '',
                    sorted && state.query.sort.order === '오름' ? 'is-asc' : '',
                    filtered ? 'is-filtered' : '',
                  ]
                    .filter(Boolean)
                    .join(' ')}
                >
                  {/* 열 이름 자체가 버튼이다 (`§8` 표 헤더). 화살표·점은 CSS 표식이라 이름에 섞이지 않는다 */}
                  <button
                    type="button"
                    className="thf"
                    aria-haspopup="menu"
                    aria-expanded={openColumn === column}
                    onClick={(e) => {
                      e.stopPropagation();
                      setOpenColumn((c) => (c === column ? null : column));
                    }}
                  >
                    {column}
                  </button>
                  {openColumn === column && (
                    <ColumnMenu
                      column={column}
                      sort={state.query.sort}
                      picked={state.query.filters[column] ?? []}
                      facets={isFilterable(column) ? state.facets : null}
                      uploaderNames={props.uploaderNames}
                      onSort={pick}
                      onToggle={toggle}
                      onClearColumn={clearColumn}
                    />
                  )}
                </th>
              );
            })}
            <th scope="col" className="rowact" aria-label="빠른 작업" />
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 && state.hasConditions && (
            <tr>
              <td colSpan={9} className="empty">
                조건에 맞는 데이터가 없어요. 조건을 하나 풀어 보세요.
              </td>
            </tr>
          )}
          {rows.map((row) => (
            <tr
              key={row.datasetId}
              className={`clk${row.bodyAccessible ? '' : ' is-locked'}`}
              onClick={() => props.onOpen(row.datasetId)}
            >
              <td className="fname">
                {!row.bodyAccessible && (
                  <span className="lock" data-testid="lock-icon" aria-label="잠긴 데이터">
                    🔒
                  </span>
                )}
                {row.name}{' '}
                {/* 조각 묶음 — 잠긴 행에도 뜬다 (`PLAN-SoT §9-㊼`) */}
                {row.fileCount >= 2 && <span className="chip chip--neutral">조각 {row.fileCount}</span>}
              </td>
              <td>{row.topic ?? ''}</td>
              <td>
                <span className={`lvl lvl-${row.processingLevel}`}>Lv{row.processingLevel}</span>
              </td>
              <td className="muted" title={row.projects.names.join(' · ')}>
                {row.projects.representative?.name ?? ''}{' '}
                {row.projects.moreCount > 0 && (
                  <span className="chip chip--neutral">외 {row.projects.moreCount}</span>
                )}
              </td>
              <td className="who">{row.uploader.name}</td>
              <td className="mono">{day(row.lastModifiedAt)}</td>
              <td title={lineageTitle(row)}>
                <span className={`lin lin--${row.lineageState === '확정' ? 'done' : row.lineageState === '확인 필요' ? 'wait' : 'none'}`}>
                  {row.lineageState}
                </span>
              </td>
              <td>
                {row.verified ? (
                  <span className="verified" aria-label="Verified">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" aria-hidden="true">
                      <path d="M20 6L9 17l-5-5" />
                    </svg>
                  </span>
                ) : (
                  /* 승인 처리가 아직 도착하지 않은 행 — 글자를 취소선·회색·꺼진 조작 모양으로
                     둔다 (Ted 판정 2026-09-02). 비워 두면 「값이 없다」와 「아직 안 왔다」가
                     화면에서 갈리지 않는다. 취소선 규칙은 `catalog.css` `.verified--pending`. */
                  <span
                    className="verified verified--pending"
                    data-testid="verified-pending"
                    aria-disabled="true"
                    title="승인 처리가 아직 도착하지 않았다"
                  >
                    Verified
                  </span>
                )}
                {!row.bodyAccessible && <span className="chip chip--warning">잠김</span>}
              </td>
              {/* 빠른 작업은 잠긴 행에 두지 않는다. 접근 요청은 상세에서 한다 (`§8` 잠긴 카탈로그 행) */}
              <td className="rowact">
                {row.bodyAccessible && (
                  <div className="ra">
                    <button
                      type="button"
                      className="rab"
                      title="엿보기"
                      aria-label={`${row.name} 엿보기`}
                      onClick={(e) => {
                        e.stopPropagation();
                        props.onOpen(row.datasetId);
                      }}
                    >
                      {EYE}
                    </button>
                    {/* href 는 계약이 정한 실제 자리라 그대로 둔다. 다만 브라우저가 만드는
                        요청에는 세션 토큰이 안 붙어 401 이 나므로, 누르면 인증된 클라이언트로
                        받는다 (`api/download.ts`). */}
                    <a
                      className="rab"
                      title="다운로드"
                      aria-label={`${row.name} 다운로드`}
                      href={`${API_BASE_URL}/datasets/${row.datasetId}/download`}
                      onClick={(e) => {
                        e.stopPropagation();
                        e.preventDefault();
                        setDownloadError(null);
                        void downloadDataset(row.datasetId).catch(() => {
                          setDownloadError(`${row.name} 을(를) 내려받지 못했어요.`);
                        });
                      }}
                    >
                      {DL}
                    </a>
                  </div>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {downloadError && (
        <p className="dlerr" role="alert">
          {downloadError}
        </p>
      )}
    </div>
  );
}
