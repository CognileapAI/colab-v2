// 검색 한 번의 상태 기계. 상태가 넷이고 넷째를 지어내지 않는다.
//
// `unavailable` 이 `ready(0건)` 과 **다른 상태로 서 있는 것**이 이 파일의 요점이다 —
// 하나로 합치면 「검색이 죽었다」가 「없다」로 둔갑한다.
import { useEffect, useRef, useState } from 'react';
import { SearchUnavailable, type SearchResults, type SearchSource } from './types';

export type SearchState =
  | { status: 'loading' }
  | { status: 'ready'; results: SearchResults }
  | { status: 'unavailable' };

/**
 * ⭑ **⟨16차 해제 · `〈298〉`⟩ `verifiedOnly` 가 질의의 일부다.** 걸름이 서버로 갔으므로
 * 토글은 **상태가 아니라 질의**이고, 바뀌면 다시 묻는다.
 */
export function useSearch(source: SearchSource, query: string,
                          verifiedOnly = false): SearchState {
  const [state, setState] = useState<SearchState>({ status: 'loading' });
  //: 지금 화면에 그려져 있는 결과가 어느 질문의 것인가.
  const shown = useRef<string | null>(null);

  useEffect(() => {
    let alive = true;
    // **같은 질문에서 토글만 바뀐 것이면 이미 그린 결과를 지우지 않는다** — 지우면
    // 결과 헤드가 통째로 사라져 **토글 자신이 화면에서 없어진다**(다시 끌 수가 없다).
    // 질문이 바뀐 것이면 그때는 지운다 — 다른 질문의 결과를 남겨 두면 화면이 거짓말을 한다.
    if (shown.current !== query) setState({ status: 'loading' });
    source
      .search({ query, ...(verifiedOnly ? { verified: true } : {}) })
      .then((results) => {
        if (!alive) return;
        shown.current = query;
        setState({ status: 'ready', results });
      })
      .catch((e) => {
        if (!alive) return;
        // 어떤 실패든 결과를 지어내지 않는다. `SearchUnavailable` 이 아닌 것도
        // 「모른다」이지 「없다」가 아니므로 같은 자리로 보낸다.
        void (e instanceof SearchUnavailable);
        shown.current = null;
        setState({ status: 'unavailable' });
      });
    return () => {
      alive = false;
    };
  }, [source, query, verifiedOnly]);

  return state;
}
