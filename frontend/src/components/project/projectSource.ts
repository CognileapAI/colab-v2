// 목록·상세를 채우는 출처. **서버가 유일한 출처다.**
//
// ⭑ **2026-09-03 개정 — 픽스처 폴백을 걷었다** (`CODE-REVIEW-20260903` 9).
// 종전 폴백은 `listProjects`·`getProject` 가 501 이던 동안의 것이고, WU-P5 가 그 셋을
// 열었으므로 남아 있던 폴백은 501 이 아니라 **401·500·네트워크 오류**를 덮고 있었다.
//
// 지금의 규칙 — 404 는 그대로 `ProjectGone`, 401 은 `api/client.ts` 가 `AuthGate` 로 넘기고,
// 그 밖의 실패는 **못 읽었다**고 말한다 (`useProjects`·`useProject` 의 실패 상태).
import { api } from '../../api/client';
import {
  ProjectGone,
  ProjectHasDatasets,
  type ProjectCreate,
  type ProjectDetail,
  type ProjectRow,
  type ProjectSource,
  type ProjectStatus,
  type ProjectUpdate,
} from './types';

export function apiProjectSource(): ProjectSource {
  return {
    async list(query) {
      const r = await api.GET('/projects', {
        params: {
          query: {
            // 「전체」는 **조건을 빼는 것**이다 — 계약에 그런 값이 없다.
            ...(query.status === '전체' ? {} : { status: query.status }),
            ...(query.type === '전체' ? {} : { type: query.type }),
            sort: query.sort,
          },
        },
      });
      const body = r.data;
      if (!body) throw new Error('프로젝트 목록을 불러오지 못했어요.');
      return { items: body.items as ProjectRow[], totalCount: body.totalCount };
    },
    async get(projectId) {
      const r = await api.GET('/projects/{projectId}', { params: { path: { projectId } } });
      // 남의 연구실과 지워진 것을 **같은 404** 로 받는다 (P-9·P-10).
      if (r.response.status === 404) throw new ProjectGone();
      const body = r.data;
      if (!body) throw new Error('프로젝트 상세를 불러오지 못했어요.');
      return body as ProjectDetail;
    },

    // ── 쓰기 다섯 (F-03·F-04·F-05 · 삭제 · 소속 해제) ───────────────────────
    //
    // **폴백하지 않는다.** 픽스처로 성공을 흉내 내는 순간 **저장되지 않은 것을 저장됐다고**
    // 말하게 된다. 2026-09-03 부터는 읽기도 같다 — 이 파일에 픽스처가 없다.
    async create(input: ProjectCreate) {
      const r = await api.POST('/projects', { body: input });
      if (!r.data) throw new Error('프로젝트를 만들지 못했어요.');
      return r.data as ProjectDetail;
    },
    async update(projectId, input: ProjectUpdate) {
      const r = await api.PATCH('/projects/{projectId}', {
        params: { path: { projectId } },
        body: input,
      });
      if (r.response.status === 404) throw new ProjectGone();
      if (!r.data) throw new Error('프로젝트를 고치지 못했어요.');
      return r.data as ProjectDetail;
    },
    async setStatus(projectId, status: ProjectStatus) {
      const r = await api.PUT('/projects/{projectId}/status', {
        params: { path: { projectId } },
        body: { status },
      });
      if (r.response.status === 404) throw new ProjectGone();
      if (!r.data) throw new Error('프로젝트 상태를 바꾸지 못했어요.');
      return r.data as ProjectDetail;
    },
    async remove(projectId) {
      const r = await api.DELETE('/projects/{projectId}', {
        params: { path: { projectId } },
      });
      // **409 를 삼키지 않는다** — 소속 데이터셋이 있다는 사실을 화면이 그대로 말한다.
      if (r.response.status === 409) throw new ProjectHasDatasets();
      if (r.response.status === 404) throw new ProjectGone();
      if (r.response.status !== 204) throw new Error('프로젝트를 지우지 못했어요.');
    },
    async unlink(projectId, datasetId) {
      const r = await api.DELETE('/projects/{projectId}/datasets/{datasetId}', {
        params: { path: { projectId, datasetId } },
      });
      if (r.response.status === 404) throw new ProjectGone();
      if (r.response.status !== 204) throw new Error('소속을 해제하지 못했어요.');
    },
  };
}

/** 화면이 쓰는 출처. **대역이 없다** — 읽기 둘도 쓰기 다섯과 같은 규칙을 따른다. */
export function defaultProjectSource(): ProjectSource {
  return apiProjectSource();
}
