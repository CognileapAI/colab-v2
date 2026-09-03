// S-01 검색 히어로 · S-06 검색 결과의 화면 상태 타입.
// 응답 모양은 전부 계약 생성물에서 온다 — 여기서 다시 선언하지 않는다 (`CLAUDE.md §3-6·§3-7`).
import type { components } from '../../generated/fe-core';

type S = components['schemas'];

export type SearchResultRow = S['SearchResultRow'];
/**
 * `ListEnvelope.items` 가 `unknown[]` 이라 교차형이 `unknown` 으로 무너진다 —
 * **모양을 다시 선언하는 것이 아니라** 생성물의 그 한 칸만 좁힌다(`Omit` 은 파생이다).
 */
export type SearchResults = Omit<S['SearchResults'], 'items'> & { items: SearchResultRow[] };
export type AiSearchScope = S['AiSearchScope'];

/** 검색 질문은 1~200자다 (`SearchQuery.query`). 화면이 이 값을 두 곳에서 정하지 않는다. */
export const MAX_QUERY_LENGTH = 200;

/**
 * 검색에 **닿지 못했다.** 0건과 다른 사건이다 —
 * 0건은 정상 응답이고(`§1.3-7`), 이것은 「검색이 지금 없다」이다.
 * 이 둘을 같은 화면으로 그리면 화면이 거짓말을 한다.
 */
export class SearchUnavailable extends Error {}

/**
 * ⭑ **⟨16차 해제 · `〈298〉`⟩ `verified` 가 실린다.** `Verified만 보기` 걸름은 **서버가**
 * 진다 — 화면이 받은 쪽을 거르면 `limit` **한 쪽 안에서만** 걸러져 이어보기 뒤쪽의 승인
 * 결과가 켜도 오지 않았다(`〈295〉`-㉲-ⓑ 가 적어 둔 한계).
 * **생략은 「거르지 않는다」다** — `false` 를 굳이 싣지 않는다.
 */
export type SearchRequest = { query: string; limit?: number; verified?: boolean };

/**
 * 결과를 채우는 곳. 실서버(`searchDatasets`) 하나뿐이다 —
 * **픽스처 폴백을 두지 않는다.** 검색은 「무엇이 실제로 있는가」를 답하는 자리라
 * 지어낸 행을 섞으면 그 답이 거짓이 된다 (`CLAUDE.md §3` — 못 찾으면 정직한 빈 상태).
 */
export interface SearchSource {
  search(request: SearchRequest): Promise<SearchResults>;
}
