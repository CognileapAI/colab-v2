// 승인 처리 네 동작의 실서버 배선. 타입·경로는 전부 생성물에서 온다 (CLAUDE.md §3-6·§3-7).
//
// **오류 문구를 화면이 지어내지 않는다** — 서버 봉투의 `message` 를 그대로 올린다.
// 정본이 §9 에 문구를 적어 두었고(「이미 처리된 요청이에요」 등) 그 문장의 주인은 서버다.
// 화면이 상태 코드로 문구를 다시 지으면 두 곳이 갈라진다.
import { api } from '../../api/client';
import type { ApprovalSource } from './types';

type Envelope = { message?: string } | undefined;

function fail(body: Envelope, fallback: string): never {
  throw new Error(body?.message || fallback);
}

export function apiApprovalSource(): ApprovalSource {
  return {
    async requestAccess(datasetId, reason) {
      const r = await api.POST('/datasets/{datasetId}/access-requests', {
        params: { path: { datasetId } },
        // 사유가 없으면 **몸통을 비워 보낸다** — 빈 문자열을 보내면 「빈 사유를 적었다」가 된다.
        body: reason === null ? {} : { reason },
      });
      if (r.error || !r.response.ok) fail(r.error as Envelope, '접근 요청을 보내지 못했어요.');
    },
    async requestVerification(datasetId) {
      const r = await api.POST('/datasets/{datasetId}/verification-request', {
        params: { path: { datasetId } },
      });
      if (r.error || !r.response.ok) fail(r.error as Envelope, '승인 요청을 보내지 못했어요.');
    },
    async approveVerification(datasetId) {
      const r = await api.POST('/datasets/{datasetId}/verification', {
        params: { path: { datasetId } },
      });
      if (r.error || !r.response.ok) fail(r.error as Envelope, '승인하지 못했어요.');
    },
    async cancelVerification(datasetId, reason) {
      const r = await api.POST('/datasets/{datasetId}/verification-cancellation', {
        params: { path: { datasetId } },
        body: reason === null ? {} : { reason },
      });
      if (r.error || !r.response.ok) fail(r.error as Envelope, '승인을 취소하지 못했어요.');
    },
  };
}
