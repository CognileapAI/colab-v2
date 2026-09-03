// 검색을 채우는 곳 — `searchDatasets` (`POST /dataset-searches`) 하나다.
//
// **픽스처가 없다.** 다른 화면(카탈로그·상세·프로젝트)은 서버가 501 을 낼 때 픽스처로 그리지만,
// 검색은 그러면 안 된다 — 「연구실에 무엇이 있는가」를 묻는 자리에 지어낸 행을 내보내면
// 화면이 정확히 거짓말을 한다 (`CLAUDE.md §3` 정직한 빈 상태 · 억지 제안 금지).
// 닿지 않으면 `SearchUnavailable` 을 던지고, 화면은 **장애를 장애라고 말한다.**
import { api } from '../../api/client';
import { SearchUnavailable, type SearchResults, type SearchSource } from './types';

export function apiSearchSource(): SearchSource {
  return {
    async search({ query, limit, verified }) {
      let r;
      try {
        r = await api.POST('/dataset-searches', {
          // **켰을 때만 싣는다** — 계약의 `verified` 는 선택 칸이고 생략이 「거르지 않는다」다.
          // `false` 를 실어도 뜻은 같지만, 안 걸고 있는 요청이 조건을 단 것처럼 보이지 않게 둔다.
          body: { query, limit: limit ?? 20, ...(verified ? { verified: true } : {}) },
        });
      } catch (e) {
        // 그물 자체가 끊어졌다. 5xx 와 같은 취급이다.
        throw new SearchUnavailable(String(e));
      }
      // 501·5xx 는 「검색이 아직/지금 없다」다. 빈 결과로 바꾸지 않는다 —
      // 빈 결과는 「뒤졌는데 없다」는 뜻이라 사실이 달라진다.
      if (!r.response.ok || !r.data) {
        throw new SearchUnavailable(`검색에 닿지 못했다 (${r.response.status}).`);
      }
      return r.data as SearchResults;
    },
  };
}

export function defaultSearchSource(): SearchSource {
  return apiSearchSource();
}
