// 미리보기를 채우는 출처. **중계 2 op 만 부른다** (`createPreviewRender`·`getPreviewRender`).
// 타일만은 중계를 거치지 않는다 — `getRenderTile` 은 core-api 를 통과하지 않는 유일한 경로다
// (`core-viz.yaml` 상단 주석 · `〈63〉-㉮`).
//
// **여기에 픽스처 폴백을 두지 않는다.** 카탈로그·상세와 다른 점이고, 의도한 차이다 —
// 등록 전 파일의 미리보기를 가짜로 그리면 **사람이 그 그림을 보고 등록을 판단한다.**
// 그릴 수 없으면 그릴 수 없다고 말하는 것이 이 화면의 일이다 (정본 §9).
import { api } from '../../api/client';
import {
  NotRenderableError,
  PreviewGone,
  PreviewUnavailable,
  type PreviewSource,
  type RenderJob,
  type RerenderInput,
} from './types';

/** `ErrorEnvelope.details` 는 자유 객체다. 생성 타입을 고치지 않고 여기서 좁혀 읽는다. */
function renderableFormatsOf(body: unknown): string[] {
  if (typeof body !== 'object' || body === null) return [];
  const details = (body as { details?: unknown }).details;
  if (typeof details !== 'object' || details === null) return [];
  const list = (details as { renderableFormats?: unknown }).renderableFormats;
  return Array.isArray(list) ? list.filter((v): v is string => typeof v === 'string') : [];
}

function messageOf(body: unknown, fallback: string): string {
  if (typeof body === 'object' && body !== null) {
    const m = (body as { message?: unknown }).message;
    if (typeof m === 'string' && m.length > 0) return m;
  }
  return fallback;
}

export function apiPreviewSource(): PreviewSource {
  return {
    async get(renderId) {
      const r = await api.GET('/previews/{renderId}', { params: { path: { renderId } } });
      // 수명이 지나면 **없는 것으로 답한다** (`〈67〉`-ⓐ 규칙 ③ — 404 의 정본 근거)
      if (r.response.status === 404 || r.response.status === 410) throw new PreviewGone();
      if (r.response.status === 415) {
        throw new NotRenderableError(
          messageOf(r.error, '이 형식은 아직 지도로 못 그려요.'),
          renderableFormatsOf(r.error),
        );
      }
      if (r.response.status === 503) {
        throw new PreviewUnavailable(
          messageOf(r.error, '지금 미리보기를 만들 수 없어요. 잠시 뒤 다시 시도해 주세요.'),
        );
      }
      // **실패는 여기가 아니다** — `200 + failure` 로 온다. 비-200 을 실패 경로로 삼으면
      // 진짜 실패를 전부 놓친다 (`P2-viz-report §13`-④)
      if (!r.data) throw new PreviewUnavailable('지금 미리보기를 만들 수 없어요. 잠시 뒤 다시 시도해 주세요.');
      return r.data as RenderJob;
    },

    async create(input: RerenderInput) {
      const r = await api.POST('/previews', {
        body: {
          target: { uploadId: input.uploadId },
          style: { palette: input.palette, classCount: input.classCount },
          withoutReferenceGrid: input.withoutReferenceGrid,
        } as never,
      });
      if (r.response.status === 404 || r.response.status === 410) throw new PreviewGone();
      if (r.response.status === 415) {
        throw new NotRenderableError(
          messageOf(r.error, '이 형식은 아직 지도로 못 그려요.'),
          renderableFormatsOf(r.error),
        );
      }
      if (!r.data) {
        throw new PreviewUnavailable(
          messageOf(r.error, '지금 미리보기를 만들 수 없어요. 잠시 뒤 다시 시도해 주세요.'),
        );
      }
      return r.data as RenderJob;
    },

    async probeTile(url) {
      // 만료된 렌더의 타일은 **410 이 아니라 401** 로 보인다 — 서명이 결과 수명과 함께 죽고
      // 인증이 조회보다 먼저 평가되기 때문이다 (`P2-viz-report` 부록 `A-1` 끝).
      // 이 화면은 그것을 **만료**로 말한다. 「권한이 없다」로 말하면 사람이 로그인을 의심한다.
      try {
        const res = await fetch(url, { method: 'GET' });
        return res.status === 401 || res.status === 403 || res.status === 410 ? 'expired' : 'ok';
      } catch {
        // 네트워크가 끊긴 것과 만료는 다른 사실이다. 만료로 단정하지 않는다
        return 'ok';
      }
    },
  };
}
