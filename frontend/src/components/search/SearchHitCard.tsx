// 결과 카드 한 장 = 카탈로그 행 그대로 + AI 가 보탠 둘(관련도 막대 · 근거 한 줄).
//
// **잠긴 데이터도 이 카드로 선다** (`P-13`·`P-34`) — 이름은 보이고 본체만 막힌다.
// **관련도는 막대의 길이로만 산다** — 퍼센트·등급 텍스트를 만들면 그 자리가 확신도 숫자가 된다
// (`CLAUDE.md §3` — 확신도에 숫자 필드가 없다).
// **`요약`·`기간` 문면을 여기서 다시 만들지 않는다** — 상세 기본 정보가 쓰는 것을 그대로
// 쓴다(`detail/format.ts`). 같은 값의 표기가 두 화면에서 갈리는 자리를 만들지 않는다.
// 특히 열린 기간(`~ 진행 중`)은 `〈283〉`(14차 해제)이 정한 성질이라 한 곳에만 있어야 한다.
import { formatPeriod, orEmpty } from '../detail/format';
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
    <li
      className={`hit${locked ? ' is-locked' : ''}${row.verified ? ' is-verified' : ''}`}
      data-testid="search-hit"
    >
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
        {/* 승인된 결과에만 배지가 선다 (정본 §8 「Verified 카드」 · 목업 `F-01` 391행).
            ⚠ **카탈로그의 `verified--pending` 취소선을 여기로 옮기지 않는다** — 그 표기는
            「칸을 비우지 않는다」가 이유이고(`〈282〉`-㉮ · `Policy §8 Verified 열`), 카드는
            애초에 칸이 아니라 배지 자리다. 정본이 카드에 요구한 것은 승인된 결과의 표시뿐이다. */}
        {row.verified && (
          <span className="verified" data-testid="hit-verified" aria-label="Verified">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" aria-hidden="true">
              <path d="M20 6L9 17l-5-5" />
            </svg>
            Verified
          </span>
        )}
        {locked && <span className="chip chip--warning">잠김</span>}
      </div>

      {/* 관련도 막대 — `role` 도 `aria-valuenow` 도 두지 않는다. 숫자를 보조기술에도 읽히지 않는다.
          순서가 이미 관련도이고, 막대는 강도만 거든다 (`fe-core.yaml SearchResultRow.relevanceBar`). */}
      <div className="relbar" data-testid="relevance-bar" aria-hidden="true">
        <span style={{ width }} />
      </div>

      {/* ⭑ **⟨16차 해제 · `〈298〉`⟩ 요약** — 정본 `§8 :120` 의 카드 구성에서 **관련도 막대와
          AI 근거 사이**다. **잠겨도 선다** (`P-13` — 이름·요약까지 노출).
          비면 지어내지 않고 빈 표시를 쓴다(상세 기본 정보와 같은 규칙). */}
      <p className="hit-summary" data-testid="hit-summary">
        {orEmpty(row.summary)}
      </p>

      <p className="hit-why" data-testid="search-rationale">
        {row.rationale}
      </p>

      <div className="hit-meta">
        {/* **정렬 이유를 카드가 말한다** (정본 §8 「Verified 카드」 축자 · §1.3-5 「올린 이유를
            카드에 문장으로 밝힌다」). 좌측 초록 룰은 `search.css` `.hit.is-verified` 가 그린다. */}
        {row.verified && (
          <span className="why-top" data-testid="hit-verified-why">
            ✓ 교수 승인이라 위로 올렸어요
          </span>
        )}
        <span className={`lvl lvl-${row.processingLevel}`}>Lv{row.processingLevel}</span>
        {row.topic && <span className="chip chip--neutral">{row.topic}</span>}
        {/* 잠긴 행에서 「누구에게 요청할지」가 더 필요하다 (`Policy_데이터_찾기 §5`) */}
        {/* ⭑ **⟨16차 해제 · `〈298〉`⟩ 기간.** ⚠ **잠긴 카드에는 두지 않는다** —
            정본 `§8` 「잠긴 결과 카드 … 기간·원천·소유 메타 줄은 두지 않는다」.
            서버가 값을 빼는 것이 아니라 **화면이 안 그리는 것**이다. */}
        {!locked && (
          <span className="span" data-testid="hit-period">
            {formatPeriod(row.period)}
          </span>
        )}
        <span className="who">{row.uploader.name}</span>
        <span className="when">{day(row.lastModifiedAt)}</span>
        <span className="lin">{row.lineageState}</span>
      </div>
    </li>
  );
}
