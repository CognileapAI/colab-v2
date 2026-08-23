// ② 소속 프로젝트 지정이 읽고 쓰는 두 op.
// 빠른 생성은 **유형·이름 두 칸만** 받는다 (`Policy §5` — 설명·기간·연결 주소는 받지 않는다).
import { api } from '../../api/client';
import { NotImplemented, type ProjectCreate, type ProjectSource } from './types';

export function apiProjectSource(): ProjectSource {
  return {
    async list() {
      const r = await api.GET('/projects', { params: { query: {} } });
      if (r.response.status === 501) throw new NotImplemented();
      return r.data?.items ?? [];
    },

    async create(body: ProjectCreate) {
      const r = await api.POST('/projects', { body });
      if (r.response.status === 501) throw new NotImplemented();
      if (!r.data) throw new Error('프로젝트를 만들지 못했어요.');
      return { projectId: r.data.projectId, name: r.data.name };
    },
  };
}
