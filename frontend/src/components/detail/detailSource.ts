// 상세를 채우는 출처. **서버가 유일한 출처다.**
//
// ⭑ **2026-09-03 개정 — 픽스처 폴백을 걷었다** (`CODE-REVIEW-20260903` 9).
// 종전 폴백은 `getDataset` 이 501 이던 동안의 것이었다. 지금 그 op 은 구현돼 있고, 남아 있던
// 폴백은 **실존하는 데이터셋을 픽스처가 모르는 id 라는 이유로 `DatasetGone`** 으로 바꿔
// 「이 주소에는 화면이 없어요」를 그리고 있었다 (`fixture.ts` 의 모르는 id → `DatasetGone`).
//
// ⭑ **2026-09-03 개정 — 17차 해제(Ted 판정 ②)를 그 위에 얹었다.**
// 지금의 규칙 넷 — 410 은 **내 연구실 묘비**(`DatasetTombstone`) · 404 는 나머지 셋이 접힌
// 「없는 주소」(`DatasetGone`) · 401 은 `api/client.ts` 가 토큰을 버려 `AuthGate` 로 넘긴다 ·
// 그 밖의 실패는 **못 읽었다**(`useDatasetDetail` 의 `error`)고 말한다.
import { api } from '../../api/client';
import { DatasetGone, DatasetTombstone, type DetailSource } from './types';

export function apiDetailSource(): DetailSource {
  return {
    async get(datasetId) {
      const r = await api.GET('/datasets/{datasetId}', {
        params: { path: { datasetId } },
      });
      // ⭑ ⟨17차 해제 · Ted 판정 ②⟩ **두 코드는 다른 사실이다. 접지 않는다.**
      //   410 = 내 연구실 묘비 → `§9` 묘비 문구 · 404 = 나머지 셋 → `§2.4` 중립 문구.
      //   순서가 중요하다 — 410 을 404 뒤에 두는 실수는 안 나지만, 둘을 한 줄로 합치면
      //   화면이 영영 갈리지 못한다. 501 과도 섞지 않는다.
      if (r.response.status === 410) throw new DatasetTombstone();
      // 404 는 묘비가 아니라 「없는 주소」다 (`Policy_공통_기반 §2.4`)
      if (r.response.status === 404) throw new DatasetGone();
      const body = r.data;
      if (!body) throw new Error('데이터셋 상세를 불러오지 못했어요.');
      return body;
    },
  };
}

/**
 * 화면이 쓰는 출처. **대역이 없다** — 지워진 것(410)도, 없는 주소(404)도, 못 읽은 것도
 * 각자 그대로 말한다. 픽스처로 되살리면 화면이 거짓말을 한다.
 */
export function defaultDetailSource(): DetailSource {
  return apiDetailSource();
}
