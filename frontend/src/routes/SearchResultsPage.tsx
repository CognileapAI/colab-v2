// S-06 검색 결과 — **뒤진 범위를 먼저 밝히고**, 결과마다 근거를 한 줄로 붙인다.
//
// 이 화면이 지켜야 하는 것은 「검색이 어휘 검색이라는 사실을 화면이 말하는가」다
// (`S1-PLAN.md §6` 완료 정의 6 · `CLAUDE.md §3`). 그래서 —
//   · 범위 줄이 결과보다 **위이자 먼저**다 (0건이어도, 장애여도)
//   · 0건은 오류가 아니라 정직한 빈 상태이고 **억지 제안을 하지 않는다**
//   · `degraded` 는 감추지 않는다. 도는 척(가짜 스피너)도 하지 않는다
//   · 잠긴 데이터는 사라지지 않는다 (`P-13`·`P-34`)
import { useMemo, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { SearchHitCard } from '../components/search/SearchHitCard';
import { defaultSearchSource } from '../components/search/searchSource';
import { useSearch } from '../components/search/useSearch';
import type { AiSearchScope, SearchSource } from '../components/search/types';
import '../components/search/search.css';

function ScopeLine(props: { scope: AiSearchScope }) {
  const { scope } = props;
  return (
    <p className="scope" data-testid="search-scope">
      {/* ⚠ 0건일 때 **판정 문장을 여기서 말하지 않는다** — 목업 F-02 의 0건 상태가
          「…맞는 것이 없었어요」를 자기 안에 이미 담고 있어, 둘을 다 두면 같은 말이 화면에
          두 번 나온다(검수 #13 · 실물에서 연속 2회 출력). **범위·개수는 그대로 남는다** —
          정본 §3.3 「0건일 때 원인을 알 수 있다」가 요구하는 것은 이 줄이지 판정이 아니다.
          ⭑ **찾은 건수는 이 줄이 지지 않는다** (검수 #11 · 정본 §8) — 정본은 범위 표시줄과
          결과 헤드를 **다른 줄**로 적었고, 건수는 `Verified만 보기` 토글에 따라 갱신되어야
          하므로 토글과 같은 줄에 있어야 한다. */}
      {scope.labName} 데이터 {scope.searchedCount}건을 뒤졌어요.
    </p>
  );
}

/**
 * 결과 헤드 — **찾은 건수 · `Verified만 보기` 토글 · 정렬 기준**을 한 줄에
 * (정본 `Policy_데이터_찾기 §8` 「결과 헤드」·「Verified만 보기」 · 목업 `F-01` 383~387행).
 *
 * **정렬 선택 상자를 두지 않는다** — 순서를 고르는 조작은 카탈로그에만 있다(같은 행 축자).
 * 그래서 오른쪽 끝의 「Verified 우선 · 관련도 순」은 **고른 값이 아니라 고정 문구**다.
 *
 * ⭑ **2026-09-03 개정 (`〈298〉` · 16차 해제) — 걸름이 서버로 갔다.** 종전 기재
 * 「토글은 화면이 건다 … 서버 걸름은 계약 개정이 있어야 서는 자리」(`〈295〉`)는 **그때는
 * 참이었다**. 16차가 `SearchQuery.verified` 를 열었으므로 이제 토글은 **다시 묻는 조작**이고,
 * 화면은 받은 쪽을 다시 거르지 않는다. 그래야 이어보기 뒤쪽의 승인 결과도 온다
 * (`〈295〉`-㉲-ⓑ 가 ⚠ 로 적어 둔 「한 쪽 안에서만 거른다」가 닫힌다).
 */
function ResultHead(props: {
  found: number;
  verifiedOnly: boolean;
  onToggle(): void;
}) {
  const { found, verifiedOnly } = props;
  return (
    <div className="result-head" data-testid="search-result-head">
      <b>{found}건</b>을 찾았어요.
      <button
        type="button"
        className={`vfilter${verifiedOnly ? ' on' : ''}`}
        data-testid="verified-only"
        aria-pressed={verifiedOnly}
        onClick={props.onToggle}
      >
        <span className="vsw" aria-hidden="true" />
        Verified만 보기
      </button>
      <span className="sortby">Verified 우선 · 관련도 순</span>
    </div>
  );
}

export function SearchResultsPage(props: { source?: SearchSource } = {}) {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const query = params.get('q') ?? '';
  const source = useMemo(() => props.source ?? defaultSearchSource(), [props.source]);
  // `Verified만 보기` — **검색 전용**이다 (정본 §8). 카탈로그에서는 같은 일을 Verified 열의
  // 조건이 맡으므로 이 상태를 그쪽과 공유하지 않는다.
  const [verifiedOnly, setVerifiedOnly] = useState(false);
  // ⭑ **⟨16차 해제 · `〈298〉`⟩ 토글이 질의로 들어간다** — 걸름은 서버가 `limit` 앞에서 건다.
  const state = useSearch(source, query, verifiedOnly);
  // **받은 것을 다시 거르지 않는다.** 여기서 한 번 더 거르면 「서버가 걸렀나」를 아무도
  // 못 재고, 서버 걸름이 깨져도 화면이 그 사실을 덮는다.
  const shown = state.status === 'ready' ? state.results.items : [];

  return (
    <div className="search-page" data-screen="S-06">
      <div className="page-head">
        <h1>검색 결과</h1>
        <span className="q">‘{query}’</span>
      </div>

      {state.status === 'loading' && (
        <p className="loading" data-testid="search-loading">
          뒤지는 중이에요…
        </p>
      )}

      {/* 검색에 닿지 못했다. **0건이 아니다** — 「없다」고 말하지 않고 「지금 못 한다」고 말한다.
          그리고 카탈로그는 그대로 돈다 (`CLAUDE.md §3` — AI 없이도 v2 는 완결된 제품이다). */}
      {state.status === 'unavailable' && (
        <div className="notice notice--down" data-testid="search-unavailable">
          <p>
            검색이 지금 동작하지 않아요. 무엇이 있는지 못 뒤진 것이지, 없다는 뜻이 아니에요.
          </p>
          <Link to="/datasets">데이터셋 카탈로그에서 직접 찾기</Link>
        </div>
      )}

      {state.status === 'ready' && (
        <>
          {/* 뒤진 범위가 먼저다 — 0건이어도, degraded 여도 이 줄이 맨 앞이다 (정본 §3.3) */}
          <ScopeLine scope={state.results.scope} />

          {state.results.degraded && (
            <div className="notice notice--degraded" data-testid="search-degraded">
              질의 해석이 지금 동작하지 않아, 적어 주신 문장의 <b>낱말 그대로</b> 찾은 결과예요.
              찾은 것은 그대로 실제 결과이고, 놓친 것이 있을 수 있어요.
            </div>
          )}

          {!state.results.isDataQuery ? (
            <div className="notice" data-testid="search-not-data-query">
              <p>이 검색은 데이터를 찾는 질문에 답해요.</p>
              <p className="hint">
                예: 「한강 유역 강수 자료」 · 「2023년 위성 영상」 — 데이터에 적혀 있을 법한 말로
                물어보세요.
              </p>
            </div>
          ) : /* ⭑ **⟨16차 해제 · `〈298〉`⟩ 토글을 켠 채의 0건은 「못 찾았어요」가 아니다.**
                 뒤진 결과는 있고 승인된 것이 없을 뿐이라, 여기서 0건 상태로 갈아타면
                 **토글이 화면에서 사라져 다시 끌 수가 없다.** 그때는 아래 결과 헤드를
                 0건으로 그린다 (`Policy §8` 「건수 갱신」). */
            shown.length === 0 && !verifiedOnly ? (
            /* 0건은 200 이고 정상이다. **대신 뭘 볼래요? 를 지어내지 않는다.** */
            /* 0건 상태의 네 조각은 **목업 E-02 `F-02` 축자**다 (`데이터_찾기_260817.html`
               448~453행 · `Policy_데이터_찾기 §154행` 「"맞는 데이터를 못 찾았어요" + 뒤진
               범위·개수 + [단어를 바꿔 다시 찾기] [카탈로그에서 훑어보기] + 업로드 권유 한 줄」).
               막다른 길을 만들지 않는다 — 그리고 **대신 뭘 볼래요? 를 지어내지 않는다.** */
            <div className="notice notice--empty" data-testid="search-empty">
              <h2>맞는 데이터를 못 찾았어요</h2>
              <p>
                {state.results.scope.labName} 데이터 <b>{state.results.scope.searchedCount}개</b>를
                뒤졌지만 <b>‘{query}’</b>에 맞는 것이 없었어요.
              </p>
              <p className="hint">
                이 검색은 데이터에 적혀 있는 낱말을 그대로 찾아요 — 「강수량」으로는 「강수」가 적힌
                데이터가 나오지 않아요.
              </p>
              <div className="empty-acts">
                <button type="button" className="quiet" onClick={() => navigate('/')}>
                  단어를 바꿔 다시 찾기
                </button>
                <Link className="strong" to="/datasets">
                  카탈로그에서 훑어보기
                </Link>
              </div>
              <p className="muted">이 데이터를 갖고 계시면 업로드해 주세요.</p>
            </div>
          ) : (
            <>
              {/* 건수·토글·정렬 기준 한 줄. **0건 상태에는 두지 않는다** — 켜고 끌 것이 없다 */}
              <ResultHead
                found={shown.length}
                verifiedOnly={verifiedOnly}
                onToggle={() => setVerifiedOnly((v) => !v)}
              />
              <ul className="hits" data-testid="search-results">
              {/* 순서를 다시 매기지 않는다 — 순위는 `tsvector` 가 정했고(`〈72〉`),
                  같은 질의·같은 DB 상태면 같은 순서가 나와야 평가셋이 회귀를 잡는다 */}
                {shown.map((row) => (
                  <SearchHitCard
                    key={row.datasetId}
                    row={row}
                    onOpen={(datasetId) => navigate(`/datasets/${datasetId}`)}
                  />
                ))}
              </ul>
            </>
          )}
        </>
      )}

      <div className="crosslink">
        <span>뭐가 있는지부터 훑고 싶으면 카탈로그가 빨라요.</span>
        <Link to="/datasets">데이터셋으로</Link>
      </div>
    </div>
  );
}
