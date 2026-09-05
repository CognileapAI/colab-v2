// 상세 수정의 실서버 배선 — 계약 op `updateDataset`(PATCH `/datasets/{datasetId}`).
// 타입·경로는 전부 생성물에서 온다 (CLAUDE.md §3-6·§3-7). 계약은 **이미 서 있고** 이 WU 는
// 프론트만 바꾼다 — `contracts/` 를 열지 않는다.
//
// **오류 문구를 화면이 지어내지 않는다** — 서버 봉투의 `message` 를 그대로 올린다
// (`approvalSource.ts` 와 같은 규칙). 상태 코드로 문구를 다시 지으면 두 곳이 갈라진다.
import { api } from '../../api/client';
import type { DatasetUpdate } from './editFields';
import type { DatasetDetail } from './types';

export interface DatasetUpdateSource {
  /** 200 으로 **갱신된 상세**가 돌아온다 — 화면은 그 값으로 갈아탄다(왕복). */
  update(datasetId: string, patch: DatasetUpdate): Promise<DatasetDetail>;
}

type Envelope = { message?: string } | undefined;

export function apiDatasetUpdateSource(): DatasetUpdateSource {
  return {
    async update(datasetId, patch) {
      const r = await api.PATCH('/datasets/{datasetId}', {
        params: { path: { datasetId } },
        body: patch,
      });
      if (r.error || !r.response.ok) {
        const body = r.error as Envelope;
        throw new Error(body?.message || '수정한 내용을 저장하지 못했어요.');
      }
      const body = r.data;
      if (!body) throw new Error('수정한 내용을 저장하지 못했어요.');
      return body;
    },
  };
}

export function defaultDatasetUpdateSource(): DatasetUpdateSource {
  return apiDatasetUpdateSource();
}
