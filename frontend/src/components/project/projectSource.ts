// 목록·상세를 채우는 두 출처. 얼굴은 하나(`ProjectSource`)라 화면은 어느 쪽인지 모른다.
//
// **전환 방법** — 서버가 `listProjects`·`getProject` 를 구현해 501 을 그만 내면
// `defaultProjectSource()` 가 그 응답을 그대로 쓴다. 화면·컴포넌트 코드는 한 줄도 바뀌지 않는다.
// (WU-P5 가 그 셋을 열었으므로 실서버 경로가 이제 살아 있다 — 픽스처는 서버가 없을 때의 자리다.)
import { api } from '../../api/client';
import { fixtureProjectSource } from './fixture';
import { ProjectGone, type ProjectDetail, type ProjectRow, type ProjectSource } from './types';

/** 아직 구현되지 않은 op (`PLAN-SoT §9-㊹` 501 두 종). */
class NotImplemented extends Error {}

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
      if (r.response.status === 501) throw new NotImplemented();
      const body = r.data;
      if (!body) throw new Error('프로젝트 목록을 불러오지 못했어요.');
      return { items: body.items as ProjectRow[], totalCount: body.totalCount };
    },
    async get(projectId) {
      const r = await api.GET('/projects/{projectId}', { params: { path: { projectId } } });
      // 남의 연구실과 지워진 것을 **같은 404** 로 받는다 (P-9·P-10). 501 과 섞지 않는다.
      if (r.response.status === 404) throw new ProjectGone();
      if (r.response.status === 501) throw new NotImplemented();
      const body = r.data;
      if (!body) throw new Error('프로젝트 상세를 불러오지 못했어요.');
      return body as ProjectDetail;
    },
  };
}

/**
 * 실서버를 먼저 부르고, 그 op 이 아직 501 이거나 닿지 않으면 픽스처로 그린다.
 * **404 는 폴백하지 않는다** — 없는 프로젝트를 픽스처로 되살리면 화면이 거짓말을 한다
 * (`detailSource.ts` 의 묘비 규칙과 같다).
 */
export function defaultProjectSource(): ProjectSource {
  const live = apiProjectSource();
  const stub = fixtureProjectSource();
  return {
    async list(query) {
      try {
        return await live.list(query);
      } catch {
        return stub.list(query);
      }
    },
    async get(projectId) {
      try {
        return await live.get(projectId);
      } catch (e) {
        if (e instanceof ProjectGone) throw e;
        return stub.get(projectId);
      }
    },
  };
}
