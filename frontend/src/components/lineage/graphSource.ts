// 계보 그래프를 채우는 출처. **서버가 유일한 출처다.**
//
// ⭑ **2026-09-03 개정 — 픽스처 폴백을 걷었다** (`CODE-REVIEW-20260903` 9).
// 종전 폴백은 core 가 `getDatasetLineage` 를 아직 라우팅하지 않던 동안의 것이었다. 그 자리는
// 열렸고, 남아 있던 폴백은 **남의 계보를 이 데이터셋의 계보로** 그리고 있었다 — 계보는
// 「이 데이터가 어디서 왔는가」라 틀린 그림이 빈 그림보다 나쁘다.
//
// 지금의 규칙 — 401 은 `api/client.ts` 가 `AuthGate` 로 넘기고, 그 밖의 실패는
// `unavailable` 이다. 화면은 그 자리에 **못 읽었다는 사실과 다시 불러오기**만 세운다.
import { api } from '../../api/client';
import type { LineageGraphSource } from './graphTypes';

export function apiLineageGraphSource(): LineageGraphSource {
  return {
    async get(datasetId) {
      const r = await api.GET('/datasets/{datasetId}/lineage', {
        params: { path: { datasetId } },
      });
      const body = r.data;
      if (!body) throw new Error('계보를 불러오지 못했어요.');
      return body;
    },
  };
}

/** 화면이 쓰는 출처. **대역이 없다** — 못 읽은 계보를 남의 계보로 채우지 않는다. */
export function defaultLineageSource(): LineageGraphSource {
  return apiLineageGraphSource();
}
