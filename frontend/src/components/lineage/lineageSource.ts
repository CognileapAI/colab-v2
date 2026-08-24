// ③ 계보 확정의 실서버 구현 — 읽기 2 op 뿐이다.
//
// **쓰기 op 이 여기 없는 것이 설계다.** 확인된 관계는 `createDataset` 의 `lineageParents` 로만
// 저장된다 (`CLAUDE.md §3-2` — D10 → D4 쓰기 경로가 존재하지 않는다).
// `addLineageParent`·`removeLineageParent`·`confirmLineage` 는 **이미 등록된 데이터셋**의
// 상세 화면 op 이라 업로드 모달에는 부를 자리가 없다 — 여기서는 `datasetId` 자체가 아직 없다.
import { api } from '../../api/client';
import type { DatasetRow, LineageSource, LineageSuggestionResponse } from './types';

export function apiLineageSource(): LineageSource {
  return {
    async suggestions(uploadId, q): Promise<LineageSuggestionResponse> {
      const r = await api.GET('/uploads/{uploadId}/lineage-suggestions', {
        params: {
          path: { uploadId },
          // 빈 값은 **보내지 않는다** — 「아직 안 골랐다」와 「빈 문자열」이 갈려야 한다.
          query: {
            ...(q.datasetNameDraft ? { datasetNameDraft: q.datasetNameDraft } : {}),
            ...(q.subject ? { subject: q.subject } : {}),
          },
        },
      });
      if (!r.data) throw new Error('계보 제안을 읽지 못했어요.');
      return r.data;
    },

    async candidates(): Promise<DatasetRow[]> {
      const r = await api.GET('/datasets', {});
      if (!r.data) throw new Error('연구실 데이터 목록을 읽지 못했어요.');
      return r.data.items ?? [];
    },
  };
}
