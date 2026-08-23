// 화면과 seam 사이의 얇은 자리. **타입은 전부 생성물에서 온다** — 여기서 형태를 다시 선언하지 않는다.
//
// 왜 포트를 두는가: `listLabMembers` · `saveLabMemberPermissions` 는 아직 501 을 낼 수 있다.
// 화면은 계약 타입에만 기대고, 실물이 붙으면 `livePort` 만 그대로 쓰면 된다 — 화면은 고치지 않는다.
import { api } from '../../api/client';
import type { Schemas } from '../../api/client';
import type { LabMember } from './permissions';

export type PortResult =
  | { ok: true; items: LabMember[] }
  /** 실패 문안은 **서버 ErrorEnvelope.message 그대로**다. 화면이 문장을 만들지 않는다 (P-11). */
  | { ok: false; message: string };

export interface MembersPort {
  list(): Promise<PortResult>;
  save(request: Schemas['PermissionSaveRequest']): Promise<PortResult>;
}

function unwrap(
  data: { items?: LabMember[] } | undefined,
  error: Schemas['ErrorEnvelope'] | undefined,
): PortResult {
  if (error) return { ok: false, message: error.message };
  return { ok: true, items: data?.items ?? [] };
}

/** 생성된 클라이언트만 쓴다. 경로·메서드를 손으로 적지 않는다. */
export const livePort: MembersPort = {
  async list() {
    const { data, error } = await api.GET('/lab/members');
    return unwrap(data, error as Schemas['ErrorEnvelope'] | undefined);
  },
  async save(request) {
    const { data, error } = await api.PUT('/lab/members/permissions', { body: request });
    return unwrap(data, error as Schemas['ErrorEnvelope'] | undefined);
  },
};
