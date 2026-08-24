// 검색 한 번의 상태 기계. 상태가 넷이고 넷째를 지어내지 않는다.
//
// `unavailable` 이 `ready(0건)` 과 **다른 상태로 서 있는 것**이 이 파일의 요점이다 —
// 하나로 합치면 「검색이 죽었다」가 「없다」로 둔갑한다.
import { useEffect, useState } from 'react';
import { SearchUnavailable, type SearchResults, type SearchSource } from './types';

export type SearchState =
  | { status: 'loading' }
  | { status: 'ready'; results: SearchResults }
  | { status: 'unavailable' };

export function useSearch(source: SearchSource, query: string): SearchState {
  const [state, setState] = useState<SearchState>({ status: 'loading' });

  useEffect(() => {
    let alive = true;
    setState({ status: 'loading' });
    source
      .search({ query })
      .then((results) => alive && setState({ status: 'ready', results }))
      .catch((e) => {
        if (!alive) return;
        // 어떤 실패든 결과를 지어내지 않는다. `SearchUnavailable` 이 아닌 것도
        // 「모른다」이지 「없다」가 아니므로 같은 자리로 보낸다.
        void (e instanceof SearchUnavailable);
        setState({ status: 'unavailable' });
      });
    return () => {
      alive = false;
    };
  }, [source, query]);

  return state;
}
