// S-05 데이터셋 상세의 **미리보기(시각화) 구역** 포트 (WU-P3).
//
// **타입은 전부 생성물·기존 미리보기 모듈에서 온다** — 여기서 다시 선언하지 않는다
// (`CLAUDE.md §3-7`). 이 파일이 새로 만드는 것은 **대상이 다르다**는 사실 하나다:
// S-08 은 등록 전 업로드(`uploadId`)를 그리고, 이 구역은 **등록된 데이터셋**(`datasetId`)을
// 그린다. 계약은 둘 다 이미 받는다 (`core-viz.yaml` RenderTarget · `fe-core.yaml`
// `createPreviewRender` — 「대상은 `datasetId`(등록 후) 또는 `uploadId`(등록 전, S-08)
// 정확히 하나다」). **계약을 고치지 않았다.**
import type { Schemas } from '../../api/client';
import type { RenderJob } from '../preview/types';

/**
 * 스크린샷 요청 = **생성물의 `ScreenshotRequest` 그대로**다
 * (`fe-core.yaml#createPreviewScreenshot` → `core-viz.yaml#ScreenshotRequest`).
 * 여기서 다시 선언하지 않는다 (`CLAUDE.md §3-7`).
 */
export type ScreenshotRequest = Schemas['ScreenshotRequest'];

/** 팔레트 후보 한 건. 키는 viz-render 소유의 불투명 값이다 — 화면이 이름을 지어내지 않는다. */
export interface PaletteOption {
  palette: string;
}

/**
 * 렌더 시작 요청. **표현 종류(격자·경계·점)를 싣지 않는다** —
 * 「무엇으로 그릴지는 사람이 고르지 않는다」(`Policy_데이터셋_상세 §8` 지도 표현).
 */
export interface DatasetRenderInput {
  datasetId: string;
  palette: string;
  /** `Policy_데이터셋_상세 §5` — 3~9 단계. 기본 6. */
  classCount: number;
}

export interface DatasetPreviewSource {
  /** `RenderStyle.palette` 값의 유일한 출처. 못 받으면 렌더를 시작하지 않는다. */
  palettes(): Promise<PaletteOption[]>;
  /** 렌더 작업을 시작한다. 실패는 예외가 아니라 `status: 실패` 로도 온다. */
  create(input: DatasetRenderInput): Promise<RenderJob>;
  /** 렌더 작업 조회. **실패는 200 + `failure`** 라 여기서 예외가 되지 않는다. */
  get(renderId: string): Promise<RenderJob>;
  /** 타일 한 장을 찔러 본다. 401 = 서명 만료. */
  probeTile(url: string): Promise<'ok' | 'expired'>;
  /**
   * 지금 장면을 PNG 로 뽑는다 (`createPreviewScreenshot` 중계).
   * **그리는 일은 서버가 한다** — 화면은 층과 보고 있는 자리만 실어 보낸다.
   */
  screenshot(request: ScreenshotRequest): Promise<Blob>;
}
