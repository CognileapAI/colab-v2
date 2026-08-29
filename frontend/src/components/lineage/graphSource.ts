// 계보 그래프를 채우는 두 출처. 얼굴은 하나(`LineageGraphSource`)라 화면은 어느 쪽인지 모른다.
//
// **전환 방법** — core 가 `getDatasetLineage` 를 라우팅하는 순간 `defaultLineageSource()` 가
// 그 응답을 그대로 쓴다. 컴포넌트 코드는 바뀌지 않는다 (`detailSource.ts` 와 같은 패턴).
import { api } from '../../api/client';
import { fixtureLineageSource } from './graphFixture';
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

/**
 * 실서버를 먼저 부르고, 아직 닿지 않으면 픽스처로 그린다.
 * **읽지 못한 것을 「빈 계보」로 그리지 않는다** — 부르는 쪽이 구역 자체를 세우지 않는다.
 */
export function defaultLineageSource(): LineageGraphSource {
  const live = apiLineageGraphSource();
  const stub = fixtureLineageSource();
  return {
    async get(datasetId) {
      try {
        return await live.get(datasetId);
      } catch {
        return stub.get(datasetId);
      }
    },
  };
}
