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
      // ⭑ **⟨WU-A7R · PRD-42⟩ 서버가 적어 보낸 거절 문면을 그대로 올린다.** 이름 중복은
      // 400 ＋ 축자 문면으로 오고, 화면이 그것을 띄운다 — 같은 문장을 화면에서 다시 지으면
      // 서버와 두 얼굴이 된다. 문면이 없을 때만 종전 일반 문장으로 떨어진다.
      if (!r.data) {
        const message = (r.error as { message?: unknown } | undefined)?.message;
        throw new Error(typeof message === 'string' && message ? message
                                                               : '프로젝트를 만들지 못했어요.');
      }
      // 유형은 화면이 표의 유형 열에 쓴다 (`WU-A7R`). 응답에 없으면 보낸 값을 그대로 쓴다.
      return { projectId: r.data.projectId, name: r.data.name, type: r.data.type ?? body.type };
    },
  };
}
