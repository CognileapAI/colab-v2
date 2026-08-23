// 상세를 채우는 두 출처. 얼굴은 하나(`DetailSource`)라 화면은 어느 쪽인지 모른다.
//
// **전환 방법** — 서버가 `getDataset` 을 구현해 501 을 그만 내면 `defaultDetailSource()` 가
// 그 응답을 그대로 쓴다. 화면·컴포넌트 코드는 한 줄도 바뀌지 않는다.
import { api } from '../../api/client';
import { fixtureDetailSource } from './fixture';
import { DatasetGone, type DetailSource } from './types';

/** 아직 구현되지 않은 op (`PLAN-SoT §9-㊹` 501 두 종). */
class NotImplemented extends Error {}

export function apiDetailSource(): DetailSource {
  return {
    async get(datasetId) {
      const r = await api.GET('/datasets/{datasetId}', {
        params: { path: { datasetId } },
      });
      // 묘비는 상세 화면이 없다 (`Policy_데이터셋_상세 §7`). 501 과 섞지 않는다
      if (r.response.status === 404) throw new DatasetGone();
      if (r.response.status === 501) throw new NotImplemented();
      const body = r.data;
      if (!body) throw new Error('데이터셋 상세를 불러오지 못했어요.');
      return body;
    },
  };
}

/**
 * 실서버를 먼저 부르고, 그 op 이 아직 501 이거나 닿지 않으면 픽스처로 그린다.
 * **묘비(404)는 폴백하지 않는다** — 지워진 데이터를 픽스처로 되살리면 화면이 거짓말을 한다.
 */
export function defaultDetailSource(): DetailSource {
  const live = apiDetailSource();
  const stub = fixtureDetailSource();
  return {
    async get(datasetId) {
      try {
        return await live.get(datasetId);
      } catch (e) {
        if (e instanceof DatasetGone) throw e;
        return stub.get(datasetId);
      }
    },
  };
}
