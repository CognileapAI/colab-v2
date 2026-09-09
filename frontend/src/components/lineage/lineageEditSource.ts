// 상세 계보 쓰기 — 기존 추가·가공 방식 수정·관계 제거 계약을 재사용한다.
//
// ⛔ **새 op 을 만들지 않는다.** 계보 확정·수정 경로는 이미 서 있고(`routes/lineage.py` 의
//    `addLineageParent`·`removeLineageParent`·`confirmLineage`), 상세에서 오는 수정도 그
//    경로를 그대로 탄다. 계약·서버·스키마 변경이 이 WU 에 0건인 이유다.
//
// ⛔ **업로드 모달은 이 파일을 부르지 않는다** — 거기서는 `datasetId` 가 아직 없고, 확인된
//    관계는 `createDataset` 의 `lineageParents` 로만 저장된다(`lineageSource.ts` 머리말).
//
// 권한 게이트는 서버가 쥔다 — `업로드·편집` 스위치가 꺼져 있으면 403 이다
// (`services/core-api/tests/test_lineage_confirm.py::test_lineage_edits_need_the_upload_edit_switch`).
// 화면은 그 앞에서 진입점을 **감출** 뿐이고(`LineageGraph.canEdit`), 판정을 흉내 내지 않는다.
import { api } from '../../api/client';
import type { LineageGraph } from './graphTypes';
import type { ParentRole } from './types';

/** `ErrorEnvelope` 의 `message` 만 읽는다 — 화면이 상태 코드로 문구를 다시 짓지 않는다
 *  (`approvalSource.ts` `fail` · `datasetPreviewSource.ts` `messageOf` 와 같은 관례). */
function messageOf(body: unknown, fallback: string): string {
  if (typeof body === 'object' && body !== null) {
    const m = (body as { message?: unknown }).message;
    if (typeof m === 'string' && m.length > 0) return m;
  }
  return fallback;
}

export interface AddParentBody {
  parentDatasetId: string;
  parentRole: ParentRole;
  /** 이미 있는 `d4_lineage_edge.method` 칸이다 — 새 칸이 아니다(부록 A `H-50`). */
  method?: string;
}

export interface LineageEditSource {
  /** 200/201 응답 본문이 **갱신된 그래프**다 — 화면은 그것을 그대로 세운다. */
  addParent(datasetId: string, body: AddParentBody): Promise<LineageGraph>;
  updateMethod?(datasetId: string, parentDatasetId: string, method: string): Promise<LineageGraph>;
  removeParent?(datasetId: string, parentDatasetId: string): Promise<LineageGraph>;
}

export function apiLineageEditSource(): LineageEditSource {
  return {
    async updateMethod(datasetId, parentDatasetId, method) {
      const r = await api.PATCH('/datasets/{datasetId}/lineage/parents/{parentDatasetId}', {
        params: { path: { datasetId, parentDatasetId } }, body: { method: method.trim() || null },
      });
      if (!r.data) throw new Error(messageOf(r.error, '가공 방식을 저장하지 못했어요.'));
      return r.data;
    },
    async removeParent(datasetId, parentDatasetId) {
      const r = await api.DELETE('/datasets/{datasetId}/lineage/parents/{parentDatasetId}', {
        params: { path: { datasetId, parentDatasetId } },
      });
      if (!r.response.ok) throw new Error(messageOf(r.error, '연결을 제거하지 못했어요.'));
      const next = await api.GET('/datasets/{datasetId}/lineage', { params: { path: { datasetId } } });
      if (!next.data) throw new Error('연결을 제거했지만 계보를 다시 읽지 못했어요. 상세 화면을 새로고침해 주세요.');
      return next.data;
    },
    async addParent(datasetId, body) {
      const r = await api.POST('/datasets/{datasetId}/lineage/parents', {
        params: { path: { datasetId } },
        // 빈 가공 방식은 **보내지 않는다** — 「안 적었다」와 「빈 문자열」이 갈려야 한다.
        body: {
          parentDatasetId: body.parentDatasetId,
          parentRole: body.parentRole,
          ...(body.method ? { method: body.method } : {}),
        },
      });
      if (!r.data) throw new Error(messageOf(r.error, '계보를 고치지 못했어요.'));
      return r.data as LineageGraph;
    },
  };
}
