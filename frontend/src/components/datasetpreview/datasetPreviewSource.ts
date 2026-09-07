// 데이터셋 상세 미리보기를 채우는 출처. **중계 3 op 만 부른다** —
// `listPalettes`(`GET /preview-palettes`) · `createPreviewRender`(`POST /previews`) ·
// `getPreviewRender`(`GET /previews/{renderId}`). 타일만은 중계를 거치지 않는다
// (`getRenderTile` 은 core-api 를 통과하지 않는 유일한 경로 — `core-viz.yaml` 상단 주석).
//
// **여기에 픽스처 폴백을 두지 않는다.** 상세 헤더·계보와 다른 점이고 의도한 차이다 —
// 가짜 지도를 그리면 사람이 그 그림을 보고 **재사용을 판단한다**(정본 §1.2 「재사용 판단」).
// 그릴 수 없으면 그릴 수 없다고 말하는 것이 이 구역의 일이다 (정본 §8·§9).
import { api } from '../../api/client';
import {
  NotRenderableError,
  PreviewGone,
  PreviewUnavailable,
  type RenderJob,
} from '../preview/types';
import type {
  DatasetPreviewSource,
  DatasetRenderInput,
  PaletteOption,
  ScreenshotRequest,
  ValueLookupResult,
} from './types';
import {
  RenderTooLarge,
  TOO_LARGE_MESSAGE,
  isRenderTooLarge,
  pieceOfDatasetFile,
  type PreviewPiece,
  type TargetDescription,
} from '../preview/pick';

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

/** 정본 §8 「그리는 서버에 연결 못 함」 행 축자. 여기서 새 한국어를 만들지 않는다. */
export const UNAVAILABLE_MESSAGE = '지금 미리보기를 만들 수 없어요. 잠시 뒤 다시 시도해 주세요.';

export function apiDatasetPreviewSource(datasetId: string): DatasetPreviewSource {
  return {
    async lookupValue(point: { lat: number; lon: number }): Promise<ValueLookupResult> {
      // **조각 식별자를 싣지 않는다** — 본체 조각은 원장이 안다(`〈294〉`).
      const r = await api.POST('/datasets/{datasetId}/value-lookup', {
        params: { path: { datasetId } },
        body: { point } as never,
      });
      // **「없다」는 200 으로 온다** — 여기서 값을 지어내지 않는다.
      if (!r.data) throw new PreviewUnavailable(messageOf(r.error, UNAVAILABLE_MESSAGE));
      return r.data as ValueLookupResult;
    },

    /** WU-C3 — 조각 목록. 「보기」를 누르는 목록과 **같은 op** 을 쓴다(새 경로 0). */
    async files(): Promise<PreviewPiece[]> {
      const r = await api.GET('/datasets/{datasetId}/files', {
        params: { path: { datasetId } },
      });
      if (!r.data) throw new PreviewUnavailable(messageOf(r.error, UNAVAILABLE_MESSAGE));
      return (r.data.items ?? []).map(pieceOfDatasetFile);
    },

    /** WU-C3 — 변수·시각 후보와 서버 기본값. **읽기 전용이다** — 렌더를 만들지 않는다. */
    async describe(): Promise<TargetDescription> {
      const r = await api.POST('/preview-target-descriptions', {
        body: { datasetId } as never,
      });
      if (isRenderTooLarge(r.response.status, r.error)) {
        throw new RenderTooLarge(messageOf(r.error, TOO_LARGE_MESSAGE));
      }
      if (!r.data) throw new PreviewUnavailable(messageOf(r.error, UNAVAILABLE_MESSAGE));
      return r.data as TargetDescription;
    },

    async palettes(): Promise<PaletteOption[]> {
      const r = await api.GET('/preview-palettes');
      // 503 = `RENDER_UNAVAILABLE`. **빈 배열로 접지 않는다** — 화면이 「팔레트가 없다」고
      // 말하는데 참인 것은 「물어보지 못했다」가 된다 (`〈87〉-㉯` 가 금지한 접기).
      if (!r.data) throw new PreviewUnavailable(messageOf(r.error, UNAVAILABLE_MESSAGE));
      return (r.data.items ?? []) as PaletteOption[];
    },

    async create(input: DatasetRenderInput): Promise<RenderJob> {
      const r = await api.POST('/previews', {
        body: {
          // **대상은 정확히 하나다** (`core-viz.yaml` RenderTarget). 등록된 데이터셋이다.
          // 고른 조각·값·시각은 **고른 것만** 실린다 — 생략은 「서버가 고른다」는 뜻이다.
          target: {
            datasetId: input.datasetId,
            ...(input.fileIds ? { fileIds: input.fileIds } : {}),
          },
          style: { palette: input.palette, classCount: input.classCount },
          ...(input.variable ? { variable: input.variable } : {}),
          ...(input.instant ? { instant: input.instant } : {}),
        } as never,
      });
      // WU-C3 — 413 은 **조각 하나로 다시 그릴 수 있다**는 사실이다. 「만들 수 없음」이 아니다.
      if (isRenderTooLarge(r.response.status, r.error)) {
        throw new RenderTooLarge(messageOf(r.error, TOO_LARGE_MESSAGE));
      }
      if (r.response.status === 404 || r.response.status === 410) throw new PreviewGone();
      if (r.response.status === 415) {
        throw new NotRenderableError(
          messageOf(r.error, '이 형식은 아직 지도로 못 그려요.'),
          renderableFormatsOf(r.error),
        );
      }
      if (!r.data) throw new PreviewUnavailable(messageOf(r.error, UNAVAILABLE_MESSAGE));
      return r.data as RenderJob;
    },

    async get(renderId: string): Promise<RenderJob> {
      const r = await api.GET('/previews/{renderId}', { params: { path: { renderId } } });
      if (r.response.status === 404 || r.response.status === 410) throw new PreviewGone();
      if (r.response.status === 415) {
        throw new NotRenderableError(
          messageOf(r.error, '이 형식은 아직 지도로 못 그려요.'),
          renderableFormatsOf(r.error),
        );
      }
      // **실패는 여기가 아니다** — `200 + failure` 로 온다. 비-200 을 실패 경로로 삼으면
      // 진짜 실패를 전부 놓친다 (`P2-viz-report §13`-④).
      if (!r.data) throw new PreviewUnavailable(messageOf(r.error, UNAVAILABLE_MESSAGE));
      return r.data as RenderJob;
    },

    async screenshot(request: ScreenshotRequest): Promise<Blob> {
      // **응답이 `image/png` 다** — 생성 클라이언트가 JSON 으로 읽지 않게 `parseAs` 를 준다.
      // 실패는 봉투(JSON)로 오고, **빈 이미지를 지어내지 않는다**(계약 503 설명 축자).
      const r = await api.POST('/preview-screenshots', {
        body: request as never,
        parseAs: 'blob',
      });
      if (!r.data) throw new PreviewUnavailable(messageOf(r.error, UNAVAILABLE_MESSAGE));
      return r.data as unknown as Blob;
    },

    async mapGeometry(sidecarUrl: string) {
      // **타일과 같은 결이다** — 산출물은 중계를 거치지 않는다(`core-viz.yaml` 상단 주석).
      // 못 읽으면 조용히 모른다고 답한다. **기본값을 지어내지 않는다**(조건 ⑷).
      try {
        const res = await fetch(sidecarUrl);
        if (!res.ok) return undefined;
        const doc: unknown = await res.json();
        if (typeof doc !== 'object' || doc === null) return undefined;
        const { width, height } = doc as { width?: unknown; height?: unknown };
        if (typeof width !== 'number' || typeof height !== 'number') return undefined;
        if (!(width > 0) || !(height > 0)) return undefined;
        return { width, height };
      } catch {
        return undefined;
      }
    },

    async probeTile(url: string) {
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
