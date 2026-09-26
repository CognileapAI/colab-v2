// 시각 검수 픽스처 — 업로드 미리보기 원천(`audit-design.tsx` 의 `upload-preview-expand` 장면 전용).
// 운영 진입점(`src/main.tsx`)에서 닿으면 안 된다: `frontend-fixture-reach` 가 `/fixture.ts` 도달을 red 로 판정한다.
//
// spec `dev-package/prd/specs/S-DEVICE-WIDTH-INPUT-20260926.md` 「새 장면 · 업로드 미리보기 확장보기」 원천 조건:
// 팔레트 정확히 3개(3개가 아니면 경고가 그려진다) · 그리기 요청이 첫 조회에 완료 · 결과 그림은 상세 장면과 같은 래스터 1장.
// 타이머 없음. 파일 · 변수 · 범례는 상세 원천과 같은 값을 쓴다.
import { FIXTURE_PREVIEW_FILE_ID, FIXTURE_PREVIEW_FILE_PATH, FIXTURE_PREVIEW_PALETTES, FIXTURE_PREVIEW_VARIABLE, fixturePreviewJobs } from '../datasetpreview/fixture';
import type { TargetDescription } from '../preview/pick';
import type { PreviewSource } from './types';

export const FIXTURE_UPLOAD_ID = '01JYZ9K7WQ3N8V4M2X6C5B0UP1';

export function fixtureUploadPreviewSource(imageUrl: string, uploadId = FIXTURE_UPLOAD_ID): PreviewSource {
  const jobs = fixturePreviewJobs({ uploadId }, imageUrl);
  return {
    palettes: async () => FIXTURE_PREVIEW_PALETTES,
    createRender: async () => jobs.drawing,
    getRender: async () => jobs.done,
    files: async () => [{ fileId: FIXTURE_PREVIEW_FILE_ID, fileName: FIXTURE_PREVIEW_FILE_PATH, renderable: true }],
    describe: async () => ({
      variables: [FIXTURE_PREVIEW_VARIABLE], instants: null, default: { variable: FIXTURE_PREVIEW_VARIABLE },
    }) as TargetDescription,
  };
}
