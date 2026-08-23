// S-04 모달 → S-08 화면으로 넘기는 짐과 그 주소. **이어짐이 이 화면의 요점이다**
// (정본 §8.1 「업로드 모달에서 그린 미리보기를 그대로 이어서 보여준다」).
//
// **왜 주소에도 싣는가** — `renderId` 를 메모리(라우터 state)에만 두면 새로고침 한 번에
// 이어짐이 끊기고, 화면이 「없는 미리보기」를 그린다. 주소에 실으면 이어짐이 구조가 된다.
// 헤더에서 읽은 값(`basicInfo`)은 주소에 담지 않는다 — 주소는 식별자만 나른다.
import type { PreviewHandoff } from './types';

/** S-08 라우트. 주인 탭이 `데이터셋` 이라 `/datasets` 아래에 둔다 (`shell/nav.ts` `ownerTabOf`). */
export const PREVIEW_ROUTE_PATH = '/datasets/preview/:uploadId';

/** 렌더 식별자를 싣는 질의 이름. */
export const RENDER_QUERY_KEY = 'render';

/**
 * S-08 에서 `연구실에 등록 →` 을 눌렀을 때 목록 화면에 실어 보내는 state 키
 * (정본 §7.2 「모달을 다시 열고 등록 단계까지 펼친다」).
 * **모달은 `P2-fe-upload` 소유**라 이 화면은 열쇠만 건네고 열지 않는다.
 */
export const REGISTER_FROM_PREVIEW_STATE_KEY = 'openUploadForRegister';

/** 라우터 state 에 미리보기 짐을 담는 키. */
export const PREVIEW_STATE_KEY = 'preview';

export function previewPath(uploadId: string, renderId?: string): string {
  const base = `/datasets/preview/${encodeURIComponent(uploadId)}`;
  return renderId ? `${base}?${RENDER_QUERY_KEY}=${encodeURIComponent(renderId)}` : base;
}

/** S-04 모달이 쓰는 자리 — 짐과 주소를 한 번에 만든다. */
export function previewNavigation(handoff: PreviewHandoff): {
  to: string;
  state: Record<string, PreviewHandoff>;
} {
  return {
    to: previewPath(handoff.uploadId, handoff.renderId),
    state: { [PREVIEW_STATE_KEY]: handoff },
  };
}

/** 라우터 state 에서 짐을 꺼낸다. 없으면 null — **없는 것을 지어내지 않는다.** */
export function readPreviewHandoff(state: unknown): PreviewHandoff | null {
  if (typeof state !== 'object' || state === null) return null;
  const held = (state as Record<string, unknown>)[PREVIEW_STATE_KEY];
  if (typeof held !== 'object' || held === null) return null;
  const h = held as Partial<PreviewHandoff>;
  if (typeof h.uploadId !== 'string') return null;
  return {
    uploadId: h.uploadId,
    ...(typeof h.renderId === 'string' ? { renderId: h.renderId } : {}),
    ...(typeof h.withoutReferenceGrid === 'boolean'
      ? { withoutReferenceGrid: h.withoutReferenceGrid }
      : {}),
    basicInfo: h.basicInfo ?? {},
    files: h.files ?? [],
  };
}
