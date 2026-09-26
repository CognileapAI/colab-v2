// 시각 검수 픽스처 — 데이터셋 상세 미리보기 원천(`audit-design.tsx` 의 `detail-preview-map` 두 장면 전용).
// 운영 진입점(`src/main.tsx`)에서 닿으면 안 된다: `frontend-fixture-reach` 가 `/fixture.ts` 도달을 red 로 판정한다.
//
// spec `dev-package/prd/specs/S-DEVICE-WIDTH-INPUT-20260926.md` 「새 장면 · 상세 미리보기 지도」 원천 조건:
// 타이머 없음 · 파일 1개(경로 72자) · 변수 1개(38자 · 기본 변수) · 팔레트 정확히 3개(3개가 아니면 경고 문장이 그려진다) ·
// 만들기 = 그리는 중 → 첫 조회에 완료 · 범례 6구간 · 데이터셋 이름 80자 · 값 조회는 고정값.
// 그림은 저장소 래스터 1장(`frontend/audit-map.png` · 점검에서 390 가림 100% 를 잰 크기와 비율)이고, URL 은 진입 파일이
// 번들러로 받아 넘긴다 — 이 모듈은 자산을 들이지 않는다.
import type { RenderJob } from '../preview/types';
import type { PreviewPiece, TargetDescription } from '../preview/pick';
import type { DatasetPreviewSource, ValueLookupResult } from './types';

/** 긴 변수 이름(38자) — 끝의 밴드 번호가 자료를 가르는 정보다(사용자 스토리 4). */
export const FIXTURE_PREVIEW_VARIABLE = 'HLS.S30.T52SCE.2025361T022121.v2.0.B02';
/** 긴 파일 경로(72자). */
export const FIXTURE_PREVIEW_FILE_PATH = `HLS_S30/2025/12/27/T52SCE/B02/${FIXTURE_PREVIEW_VARIABLE}.tif`;
/** 긴 데이터셋 이름(80자) — 상세 머리 · 뒤로 링크. */
export const FIXTURE_PREVIEW_DATASET_NAME =
  'HLS S30 지표 반사도 B02 청색 밴드 · 낙동강 중류 T52SCE 타일 · 2025년 12월 27일 관측 원자료 (HLS v2.0 원본)';
export const FIXTURE_PREVIEW_FILE_ID = '01JYZ9K7WQ3N8V4M2X6C5B0PF1';
export const FIXTURE_PREVIEW_RENDER_ID = '01JYZ9K7WQ3N8V4M2X6C5B0PR9';
/** 라벨까지 있는 3종 — 상세(`label` 선택)와 업로드(`label` 필수) 두 포트가 함께 받는다. */
export const FIXTURE_PREVIEW_PALETTES: { palette: string; label: string }[] = [
  { palette: 'viridis', label: '비리디스' },
  { palette: 'magma', label: '마그마' },
  { palette: 'rdbu', label: '빨강-파랑' },
];
export const FIXTURE_PREVIEW_BOUNDS = { west: 126.79, south: 35.13, east: 128.02, north: 36.13 };
const BREAKS = [0.006706, 0.03836, 0.05512, 0.07249, 0.09617, 0.1397, 0.5432];
const COLORS = ['#440154', '#414487', '#2a788e', '#22a884', '#7ad151', '#fde725'];
export const FIXTURE_PREVIEW_LEGEND = {
  palette: 'viridis',
  variable: FIXTURE_PREVIEW_VARIABLE,
  classes: COLORS.map((color, i) => ({ color, min: BREAKS[i]!, max: BREAKS[i + 1]! })),
};
export const FIXTURE_PREVIEW_LOOKUP: ValueLookupResult = {
  available: true, value: 0.0412, unit: null, variable: FIXTURE_PREVIEW_VARIABLE, exactness: '원본과 같은 칸', cell: null,
};
const PIECE: PreviewPiece = { fileId: FIXTURE_PREVIEW_FILE_ID, fileName: FIXTURE_PREVIEW_FILE_PATH, renderable: true };
const DESCRIPTION: TargetDescription = {
  variables: [FIXTURE_PREVIEW_VARIABLE], instants: null, default: { variable: FIXTURE_PREVIEW_VARIABLE },
} as TargetDescription;

/** 만들기 응답(그리는 중)과 첫 조회 응답(완료)의 대상 — 상세는 `datasetId`, 업로드는 `uploadId`. */
export function fixturePreviewJobs(target: RenderJob['target'], imageUrl: string): { drawing: RenderJob; done: RenderJob } {
  return {
    drawing: { target, renderId: FIXTURE_PREVIEW_RENDER_ID, status: '그리는 중', stage: '지도 그리는 중' },
    done: {
      target, renderId: FIXTURE_PREVIEW_RENDER_ID, status: '완료',
      result: { imageUrl, sidecarUrl: '/audit-sidecar', bounds: FIXTURE_PREVIEW_BOUNDS, legend: FIXTURE_PREVIEW_LEGEND },
    } as RenderJob,
  };
}

/** 상세 미리보기 원천. 타이머를 쓰지 않는다 — 만들기는 「그리는 중」, 조회는 언제나 「완료」다. */
export function fixtureDatasetPreviewSource(imageUrl: string, datasetId = '01JYZ9K7WQ3N8V4M2X6C5B0AA1'): DatasetPreviewSource {
  const jobs = fixturePreviewJobs({ datasetId }, imageUrl);
  return {
    palettes: async () => FIXTURE_PREVIEW_PALETTES,
    files: async () => [PIECE],
    describe: async () => DESCRIPTION,
    create: async () => jobs.drawing,
    get: async () => jobs.done,
    probeTile: async () => 'ok',
    mapGeometry: async () => ({ width: 3660, height: 3660 }),
    screenshot: async () => { throw new Error('시각 검수: 스크린샷은 만들지 않습니다.'); },
    lookupValue: async () => FIXTURE_PREVIEW_LOOKUP,
  };
}
