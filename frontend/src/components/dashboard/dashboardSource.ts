// 대시보드 일곱 조회의 실서버 배선. 경로·타입은 전부 생성물에서 온다 (`CLAUDE.md §3-6·§3-7`).
//
// **오류 문구를 화면이 지어내지 않는다** — 서버 봉투의 `message` 를 그대로 올린다
// (`components/approval/approvalSource.ts` 와 같은 규칙). 정본이 §9 에 화면 문구를 적어
// 둔 자리만 예외이고, 그 문구는 카드가 든다.
//
// **권한 403 은 오류가 아니다** — 「그 그룹이 통째로 없다」는 뜻이라 `GroupHidden` 으로 바꾼다
// (`Policy_홈_대시보드 §6`). 실패로 다루면 처리 권한이 없는 사람의 홈이 오류 화면이 된다.
import { api } from '../../api/client';
import { GroupHidden, type DashboardSource, type LineageTodo } from './types';

type Envelope = { message?: string } | undefined;

function fail(body: Envelope, fallback: string): never {
  throw new Error(body?.message || fallback);
}

/** 계보 확인이 필요한 두 상태. `§4` 용어 정의 축자 — 「확인 필요 + 기록 없음」이다. */
const UNSETTLED = ['확인 필요', '기록 없음'] as const;

export function apiDashboardSource(): DashboardSource {
  return {
    async summary() {
      const r = await api.GET('/dashboard/summary', {});
      if (!r.data) fail(r.error as Envelope, '요약 지표를 불러오지 못했어요.');
      return r.data;
    },
    async dataMap() {
      const r = await api.GET('/dashboard/data-map', {});
      // §9 「데이터 맵 집계를 불러오지 못함」의 문구는 카드가 든다 — 여기서는 실패만 알린다.
      if (!r.data) fail(r.error as Envelope, '연구실 데이터 분포를 지금 불러오지 못했어요.');
      return r.data;
    },
    async activities() {
      const r = await api.GET('/dashboard/activities', {});
      if (!r.data) fail(r.error as Envelope, '최근 활동을 불러오지 못했어요.');
      return r.data.items ?? [];
    },
    async lab() {
      const r = await api.GET('/lab', {});
      if (!r.data) fail(r.error as Envelope, '연구실 정보를 불러오지 못했어요.');
      return r.data;
    },
    async lineageTodo() {
      // **카탈로그와 같은 조건으로 묻는다** (`§5` 「묶는 기준은 카탈로그 필터와 같다」).
      // 전용 op 을 새로 열지 않는다 — 계약 개정 없이 되는 일을 계약 개정으로 하지 않는다.
      const r = await api.GET('/datasets', {
        params: { query: { lineageState: [...UNSETTLED] } },
      });
      if (!r.data) fail(r.error as Envelope, '처리할 일을 불러오지 못했어요.');
      return (r.data.items ?? []).map((row): LineageTodo => ({
        datasetId: row.datasetId, name: row.name, lineageState: row.lineageState,
      }));
    },
    async pendingVerifications() {
      const r = await api.GET('/verification-requests/pending', {});
      if (r.response.status === 403) throw new GroupHidden();
      if (!r.data) fail(r.error as Envelope, '처리할 일을 불러오지 못했어요.');
      return r.data.items ?? [];
    },
    async pendingAccessRequests() {
      const r = await api.GET('/access-requests/pending', {});
      if (r.response.status === 403) throw new GroupHidden();
      if (!r.data) fail(r.error as Envelope, '처리할 일을 불러오지 못했어요.');
      return r.data.items ?? [];
    },
    async approveAccessRequest(requestId) {
      const r = await api.POST('/access-requests/{requestId}/approval', {
        params: { path: { requestId } },
      });
      if (r.error || !r.response.ok) fail(r.error as Envelope, '승인하지 못했어요.');
    },
    async rejectAccessRequest(requestId, reason) {
      const r = await api.POST('/access-requests/{requestId}/rejection', {
        params: { path: { requestId } },
        body: { reason },
      });
      if (r.error || !r.response.ok) fail(r.error as Envelope, '거절하지 못했어요.');
    },
  };
}
