// 결과 카드 한 장 = 카탈로그 행 그대로 + AI 가 보탠 둘(관련도 막대 · 검색 근거 패널).
//
// **잠긴 데이터도 이 카드로 선다** (`P-13`·`P-34`) — 이름은 보이고 본체만 막힌다.
// **관련도는 막대의 길이로만 산다** — 퍼센트·등급 텍스트를 만들면 그 자리가 확신도 숫자가 된다
// (`CLAUDE.md §3` — 확신도에 숫자 필드가 없다).
// **`요약`·`기간` 문면을 여기서 다시 만들지 않는다** — 상세 기본 정보가 쓰는 것을 그대로
// 쓴다(`detail/format.ts`). 같은 값의 표기가 두 화면에서 갈리는 자리를 만들지 않는다.
// 특히 열린 기간(`~ 진행 중`)은 `〈283〉`(14차 해제)이 정한 성질이라 한 곳에만 있어야 한다.
import { formatPeriodWithInterval, orEmpty } from '../detail/format';
import type { SearchResultRow } from './types';

function day(ts: string): string {
  return ts.slice(0, 10);
}

type RationaleKind = NonNullable<SearchResultRow['rationaleFacts']>[number]['kind'];

/** 근거 종류의 화면 이름 — 내부 기법 이름(온톨로지·계보)을 쓰지 않는다 (intent Q7). */
const KIND_LABEL: Record<RationaleKind, string> = {
  term: '낱말 일치',
  concept: '관련 개념',
  linked: '연결된 자료',
  evidence: '파일 근거',
};

/**
 * 검색 근거 패널 — 요약(사람이 적은 값)과 **다른 요소·다른 면**이다
 * (intent `2026-09-25-search-rationale-separation.md` 트랙 A · 시안 A).
 * 맨 위 왼쪽 작은 태그 「✦ AI」 → 다음 줄에 2단계 목록(상위 = 근거 종류 · 하위 = 사실).
 * 순서는 서버가 정했다 — 다시 매기지 않는다. 사실 없는 종류는 그리지 않는다.
 * `rationaleFacts` 가 없는 응답(구 서버)은 `rationale` 한 줄을 같은 패널에 그린다.
 * 펼침·더보기는 두지 않는다 — 항목은 항상 전부 보인다.
 */
function RationalePanel(props: { row: SearchResultRow }) {
  const { row } = props;
  const facts = (row.rationaleFacts ?? []).filter((f) => f.items.length > 0);
  return (
    <div className="hit-rationale" data-testid="search-rationale-panel">
      <span className="hit-ai-tag" data-testid="search-rationale-tag">
        <span aria-hidden="true">✦</span> AI
      </span>
      {facts.length > 0 ? (
        <ul className="hit-facts" data-testid="search-rationale-facts">
          {facts.map((fact) => (
            <li key={fact.kind} className="hit-fact">
              <span className="hit-fact-kind" data-testid="search-rationale-kind">
                {KIND_LABEL[fact.kind]}
              </span>
              <ul className="hit-fact-items" data-testid="search-rationale-items">
                {fact.items.map((item, i) => (
                  <li key={i}>{item}</li>
                ))}
              </ul>
            </li>
          ))}
        </ul>
      ) : (
        <p className="hit-why" data-testid="search-rationale">
          {row.rationale}
        </p>
      )}
    </div>
  );
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
        {/* 운영자 범위(전 연구실) 결과에만 서버가 싣는다 — 같은 이름의 자료를 소속으로 가른다
            (intent `2026-09-25-operator-search-scope.md` Q2). 비운영자 응답에는 칸이 없어 안 선다. */}
        {row.labName && (
          <span className="chip chip--neutral" data-testid="hit-lab">
            {row.labName}
          </span>
        )}
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
        <span style={{ '--hit-relbar-w': width } as React.CSSProperties} />
      </div>

      {/* ⭑ **⟨16차 해제 · `〈298〉`⟩ 요약** — 정본 `§8 :120` 의 카드 구성에서 **관련도 막대와
          AI 근거 사이**다. **잠겨도 선다** (`P-13` — 이름·요약까지 노출).
          비면 지어내지 않고 빈 표시를 쓴다(상세 기본 정보와 같은 규칙). */}
      <p className="hit-summary" data-testid="hit-summary">
        {orEmpty(row.summary)}
      </p>

      <RationalePanel row={row} />

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
        {/* ⭑ **⟨19차 해제 · PRD-35⟩ 목록 카드는 상세와 **같은 함수**로 그린다** —
            세 자리가 같은 값을 다르게 적으면 같은 데이터가 세 얼굴을 갖는다.
            ⚠ `SearchResultRow` 는 관측 간격을 **싣지 않는다**(계약 축자 · 이 회차가 여는
            열쇠는 `DatasetCreate`·`DatasetUpdate`·`DatasetBasicInfo` 셋뿐이다). 그래서
            여기서 넘기는 값은 `undefined` 이고, **규칙이 같아 괄호가 안 그려진다** —
            카드가 상세와 다른 규칙을 쓰는 것이 아니라 **같은 규칙에 값이 없는 것**이다.
            카드가 간격을 보이려면 `SearchResultRow` 에 열쇠가 서야 하고 그것은 별건이다. */}
        {!locked && (
          <span className="span" data-testid="hit-period">
            {formatPeriodWithInterval(row.period, undefined)}
          </span>
        )}
        <span className="who">{row.uploader.name}</span>
        <span className="when">{day(row.lastModifiedAt)}</span>
        <span className="lin">{row.lineageState}</span>
      </div>
    </li>
  );
}
