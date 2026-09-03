// 파일(조각) 목록을 읽는 곳 — 계약 `listDatasetFiles` (`fe-core.yaml` `/datasets/{datasetId}/files`).
//
// **`보기` 를 눌렀을 때만 부른다** (계약 요약 축자 · `Policy_데이터셋_상세 §5` 122행).
// 상세를 열 때마다 부르면 조각 수십~수백 건을 아무도 안 볼 때도 실어 나른다.
//
// 픽스처 대역을 두지 않는다 — 이 op 은 서버에 **이미 서 있다**
// (`routes/catalog.py` `listDatasetFiles`). 없는 값을 지어내 그리지 않는다.
import { api } from '../../api/client';
import type { components } from '../../generated/fe-core';

export type DatasetFile = components['schemas']['DatasetFile'];

export interface FilesSource {
  list(datasetId: string): Promise<DatasetFile[]>;
}

export function apiFilesSource(): FilesSource {
  return {
    async list(datasetId) {
      const r = await api.GET('/datasets/{datasetId}/files', {
        params: { path: { datasetId } },
      });
      // 403 은 잠김 + 허용 목록 밖이다 (P-34). 이 화면은 잠기면 본문째 안 그리므로
      // 여기 닿는 403 은 상태가 바뀐 것이고, 그때도 지어내지 않고 오류로 말한다.
      if (!r.data) throw new Error('파일 목록을 불러오지 못했어요.');
      return r.data.items ?? [];
    },
  };
}

export function defaultFilesSource(): FilesSource {
  return apiFilesSource();
}
