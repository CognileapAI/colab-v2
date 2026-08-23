// 표를 채우는 두 출처. 얼굴은 하나(`CatalogSource`)라 화면은 어느 쪽인지 모른다.
//
// **전환 방법** — 서버가 `listDatasets`·`listDatasetFacets` 를 구현해 501 을 그만 내면
// `defaultCatalogSource()` 가 그 응답을 그대로 쓴다. 화면·컴포넌트 코드는 한 줄도 바뀌지 않는다.
import { api } from '../../api/client';
import { fixtureCatalogSource } from './fixture';
import type { CatalogQuery, CatalogSource, DatasetRow, FacetSet, LineageState } from './types';

/** 아직 구현되지 않은 op (`PLAN-SoT §9-㊹` 501 두 종). */
class NotImplemented extends Error {}

function queryParams(q: CatalogQuery) {
  const f = q.filters;
  const verified = f['Verified'];
  return {
    sortColumn: q.sort.column,
    sortOrder: q.sort.order,
    ...(f['주제']?.length ? { topic: f['주제'].map(String) } : {}),
    ...(f['Level']?.length ? { processingLevel: f['Level'].map(Number) } : {}),
    ...(f['업로더']?.length ? { uploader: f['업로더'].map(String) } : {}),
    // 값은 계보 열 메뉴(=`LineageState` 넷)에서만 온다
    ...(f['계보']?.length ? { lineageState: f['계보'].map(String) as LineageState[] } : {}),
    // 계약의 Verified 조건은 불리언 하나다. 둘 다 고른 것은 조건이 없는 것과 같다
    ...(verified?.length === 1 ? { verified: verified[0] === true } : {}),
  };
}

export function apiCatalogSource(): CatalogSource {
  return {
    async list(q) {
      const r = await api.GET('/datasets', { params: { query: queryParams(q) } });
      if (r.response.status === 501) throw new NotImplemented();
      const body = r.data;
      if (!body) throw new Error('카탈로그 목록을 불러오지 못했어요.');
      return { items: body.items as DatasetRow[], totalCount: body.totalCount };
    },
    async facets(q) {
      const { sortColumn: _c, sortOrder: _o, ...rest } = queryParams(q);
      const r = await api.GET('/datasets/facets', { params: { query: rest } });
      if (r.response.status === 501) throw new NotImplemented();
      const body: FacetSet | undefined = r.data;
      if (!body) throw new Error('열 메뉴의 값별 건수를 불러오지 못했어요.');
      return body;
    },
  };
}

/**
 * 실서버를 먼저 부르고, 그 op 이 아직 501 이거나 닿지 않으면 픽스처로 그린다.
 * 폴백은 **읽기 전용 표 하나**에만 걸린다 — 쓰기 경로에는 두지 않는다.
 */
export function defaultCatalogSource(): CatalogSource {
  const live = apiCatalogSource();
  const stub = fixtureCatalogSource();
  return {
    async list(q) {
      try {
        return await live.list(q);
      } catch {
        return stub.list(q);
      }
    },
    async facets(q) {
      try {
        return await live.facets(q);
      } catch {
        return stub.facets(q);
      }
    },
  };
}
