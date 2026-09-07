// 표를 채우는 출처. **서버가 유일한 출처다.**
//
// ⭑ **2026-09-03 개정 — 픽스처 폴백을 걷었다** (`CODE-REVIEW-20260903` 9).
// 종전 기재 「실서버를 먼저 부르고 501 이거나 닿지 않으면 픽스처로 그린다」는 `listDatasets`·
// `listDatasetFacets` 가 아직 501 이던 동안의 기재였다. 지금 그 둘은 구현돼 있고
// (`not_implemented.py` 의 op 넷에 들어 있지 않다), 남아 있던 폴백은 501 이 아니라
// **401·500·네트워크 오류**를 픽스처 6행으로 덮고 있었다 — 카탈로그가 남의 연구실
// 메타데이터를 실데이터처럼 그리고, 세션이 만료돼도 로그인으로 돌아가지 않았다.
//
// 지금의 규칙 —
//   · 401 은 `api/client.ts` 의 응답 미들웨어가 토큰을 버려 `AuthGate` 로 넘긴다.
//   · 그 밖의 실패는 **못 읽었다고 말한다**(`useCatalog.error` → 화면의 다시 불러오기).
//   · 픽스처는 시험이 **손으로 꽂을 때만** 선다 (`fixtureCatalogSource()` 를 인자로).
import { api } from '../../api/client';
import type { CatalogQuery, CatalogSource, DatasetRow, FacetSet, LineageState } from './types';
import { UNSPECIFIED } from './axisFilters';

/**
 * ⭑ **⟨20차 해제 · PRD-05 · `WU-B7`⟩ 가공 단계 축과 `Level` 열이 같은 파라미터를 쓴다.**
 * 계약이 그 파라미터를 새로 만들지 말라고 했고(PRD-05 축자), 받는 형이 문자열인 이유는
 * 파수꼴 `미지정` 하나 때문이다 — 정수는 정수 글자 그대로 실린다(WU-B5 회귀).
 */
function levelParams(q: CatalogQuery): (number | '미지정')[] {
  const fromColumn = (q.filters['Level'] ?? []).map(Number);
  const fromAxis = q.axes['가공 단계'];
  // 축은 `Lv2` 라벨을 들고 있지만 파라미터는 **정수**다 — 파수꼴만 글자 그대로 간다.
  const axisValue: (number | '미지정')[] =
    fromAxis === undefined ? [] : [fromAxis === UNSPECIFIED ? UNSPECIFIED : Number(fromAxis.slice(2))];
  return [...fromColumn, ...axisValue];
}

/**
 * 화면 상태 → 계약 질의 파라미터. **export 인 이유는 시험이 이 대응을 직접 재기 위해서다** —
 * 축을 골랐는데 파라미터 이름이 갈리면 표는 조용히 전건을 그린다(0건이 아니라서 안 드러난다).
 */
export function queryParams(q: CatalogQuery) {
  const f = q.filters;
  const verified = f['Verified'];
  const levels = levelParams(q);
  return {
    sortColumn: q.sort.column,
    sortOrder: q.sort.order,
    ...(f['주제']?.length ? { topic: f['주제'].map(String) } : {}),
    ...(q.axes['분류'] ? { category: [q.axes['분류']] } : {}),
    ...(q.axes['유형'] ? { dataType: [q.axes['유형']] } : {}),
    ...(levels.length ? { processingLevel: levels } : {}),
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
      const body = r.data;
      if (!body) throw new Error('카탈로그 목록을 불러오지 못했어요.');
      return { items: body.items as DatasetRow[], totalCount: body.totalCount };
    },
    async facets(q) {
      const { sortColumn: _c, sortOrder: _o, ...rest } = queryParams(q);
      const r = await api.GET('/datasets/facets', { params: { query: rest } });
      const body: FacetSet | undefined = r.data;
      if (!body) throw new Error('열 메뉴의 값별 건수를 불러오지 못했어요.');
      return body;
    },
  };
}

/** 화면이 쓰는 출처. **대역이 없다** — 못 읽으면 못 읽었다고 말하는 것이 이 함수의 전부다. */
export function defaultCatalogSource(): CatalogSource {
  return apiCatalogSource();
}
