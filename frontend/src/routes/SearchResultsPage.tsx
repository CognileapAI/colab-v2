// S-06 검색 결과 — **뒤진 범위를 먼저 밝히고**, 결과마다 근거를 한 줄로 붙인다.
//
// 이 화면이 지켜야 하는 것은 「검색이 어휘 검색이라는 사실을 화면이 말하는가」다
// (`S1-PLAN.md §6` 완료 정의 6 · `CLAUDE.md §3`). 그래서 —
//   · 범위 줄이 결과보다 **위이자 먼저**다 (0건이어도, 장애여도)
//   · 0건은 오류가 아니라 정직한 빈 상태이고 **억지 제안을 하지 않는다**
//   · `degraded` 는 감추지 않는다. 도는 척(가짜 스피너)도 하지 않는다
//   · 잠긴 데이터는 사라지지 않는다 (`P-13`·`P-34`)
import { useMemo } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { SearchHitCard } from '../components/search/SearchHitCard';
import { defaultSearchSource } from '../components/search/searchSource';
import { useSearch } from '../components/search/useSearch';
import type { AiSearchScope, SearchSource } from '../components/search/types';
import '../components/search/search.css';

function ScopeLine(props: { scope: AiSearchScope; found: number }) {
  const { scope, found } = props;
  return (
    <p className="scope" data-testid="search-scope">
      {scope.labName} 데이터 {scope.searchedCount}건을 뒤졌
      {found > 0 ? `고 ${found}건을 찾았어요.` : '지만 맞는 것이 없었어요.'}
    </p>
  );
}

export function SearchResultsPage(props: { source?: SearchSource } = {}) {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const query = params.get('q') ?? '';
  const source = useMemo(() => props.source ?? defaultSearchSource(), [props.source]);
  const state = useSearch(source, query);

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
          {/* 뒤진 범위가 먼저다 — 0건이어도, degraded 여도 이 줄이 맨 앞이다 */}
          <ScopeLine scope={state.results.scope} found={state.results.items.length} />

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
          ) : state.results.items.length === 0 ? (
            /* 0건은 200 이고 정상이다. **대신 뭘 볼래요? 를 지어내지 않는다.** */
            <div className="notice notice--empty" data-testid="search-empty">
              <p>
                {state.results.scope.labName} 데이터 {state.results.scope.searchedCount}건을 뒤졌지만
                맞는 것이 없었어요.
              </p>
              <p>
                이 검색은 데이터에 적혀 있는 낱말을 그대로 찾아요 — 「강수량」으로는 「강수」가 적힌
                데이터가 나오지 않아요. 적혀 있을 법한 말 그대로 다시 물어보세요.
              </p>
              <Link to="/datasets">데이터셋 카탈로그에서 조건으로 좁혀 보기</Link>
            </div>
          ) : (
            <ul className="hits" data-testid="search-results">
              {/* 순서를 다시 매기지 않는다 — 순위는 `tsvector` 가 정했고(`〈72〉`),
                  같은 질의·같은 DB 상태면 같은 순서가 나와야 평가셋이 회귀를 잡는다 */}
              {state.results.items.map((row) => (
                <SearchHitCard
                  key={row.datasetId}
                  row={row}
                  onOpen={(datasetId) => navigate(`/datasets/${datasetId}`)}
                />
              ))}
            </ul>
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
