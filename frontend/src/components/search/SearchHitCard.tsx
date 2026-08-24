// 결과 카드 한 장 = 카탈로그 행 그대로 + AI 가 보탠 둘(관련도 막대 · 근거 한 줄).
//
// **잠긴 데이터도 이 카드로 선다** (`P-13`·`P-34`) — 이름은 보이고 본체만 막힌다.
// **관련도는 막대의 길이로만 산다** — 퍼센트·등급 텍스트를 만들면 그 자리가 확신도 숫자가 된다
// (`CLAUDE.md §3` — 확신도에 숫자 필드가 없다).
import type { SearchResultRow } from './types';

function day(ts: string): string {
  return ts.slice(0, 10);
}

export function SearchHitCard(props: { row: SearchResultRow; onOpen(datasetId: string): void }) {
  const { row } = props;
  const locked = !row.bodyAccessible;
  // 0..1 을 막대 길이로만 옮긴다. 이 수가 글자로 서는 자리는 화면 어디에도 없다.
  const width = `${Math.round(Math.min(1, Math.max(0, row.relevanceBar)) * 100)}%`;

  return (
    <li className={`hit${locked ? ' is-locked' : ''}`} data-testid="search-hit">
      <div className="hit-head">
        {locked && (
          <span className="lock" aria-label="잠긴 데이터">
            🔒
          </span>
        )}
        <button
          type="button"
          className="hit-name"
          data-testid="hit-name"
          onClick={() => props.onOpen(row.datasetId)}
        >
          {row.name}
        </button>
        {row.fileCount >= 2 && <span className="chip chip--neutral">조각 {row.fileCount}</span>}
        {locked && <span className="chip chip--warning">잠김</span>}
      </div>

      {/* 관련도 막대 — `role` 도 `aria-valuenow` 도 두지 않는다. 숫자를 보조기술에도 읽히지 않는다.
          순서가 이미 관련도이고, 막대는 강도만 거든다 (`fe-core.yaml SearchResultRow.relevanceBar`). */}
      <div className="relbar" data-testid="relevance-bar" aria-hidden="true">
        <span style={{ width }} />
      </div>

      <p className="hit-why" data-testid="search-rationale">
        {row.rationale}
      </p>

      <div className="hit-meta">
        <span className={`lvl lvl-${row.processingLevel}`}>Lv{row.processingLevel}</span>
        {row.topic && <span className="chip chip--neutral">{row.topic}</span>}
        {/* 잠긴 행에서 「누구에게 요청할지」가 더 필요하다 (`Policy_데이터_찾기 §5`) */}
        <span className="who">{row.uploader.name}</span>
        <span className="when">{day(row.lastModifiedAt)}</span>
        <span className="lin">{row.lineageState}</span>
      </div>
    </li>
  );
}
