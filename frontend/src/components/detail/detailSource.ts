// 상세를 채우는 출처. **서버가 유일한 출처다.**
//
// ⭑ **2026-09-03 개정 — 픽스처 폴백을 걷었다** (`CODE-REVIEW-20260903` 9).
// 종전 폴백은 `getDataset` 이 501 이던 동안의 것이었다. 지금 그 op 은 구현돼 있고, 남아 있던
// 폴백은 **실존하는 데이터셋을 픽스처가 모르는 id 라는 이유로 `DatasetGone`** 으로 바꿔
// 「이 주소에는 화면이 없어요」를 그리고 있었다 (`fixture.ts` 의 모르는 id → `DatasetGone`).
//
// 지금의 규칙 — 404 는 그대로 묘비, 401 은 `api/client.ts` 가 `AuthGate` 로 넘긴다,
// 그 밖의 실패는 **못 읽었다**(`useDatasetDetail` 의 `error`)고 말한다.
import { api } from '../../api/client';
import { DatasetGone, type DetailSource } from './types';

export function apiDetailSource(): DetailSource {
  return {
    async get(datasetId) {
      const r = await api.GET('/datasets/{datasetId}', {
        params: { path: { datasetId } },
      });
      // 묘비는 상세 화면이 없다 (`Policy_데이터셋_상세 §7`)
      if (r.response.status === 404) throw new DatasetGone();
      const body = r.data;
      if (!body) throw new Error('데이터셋 상세를 불러오지 못했어요.');
      return body;
    },
  };
}

/** 화면이 쓰는 출처. **대역이 없다** — 지워진 것도, 못 읽은 것도 각자 그대로 말한다. */
export function defaultDetailSource(): DetailSource {
  return apiDetailSource();
}
