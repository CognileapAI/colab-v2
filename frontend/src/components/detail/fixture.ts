// 픽스처 — 서버의 `getDataset` 이 아직 501 을 낼 동안 화면을 세워 두는 자리.
// **값은 정본 목업에서 그대로 온다.** 새 데이터를 지어내지 않는다.
//   · 헤더·기본 정보 = `E-03_데이터셋_상세/mockups/데이터셋_상세_260817.html`
//       (기본 장면 = AA1 · D-03 잠긴 상세 = AA5)
//   · 나머지 네 건 = `E-02_데이터_찾기/mockups/데이터_찾기_260817.html` 의 카탈로그 6행.
//     그 목업이 주지 않는 값(구성·좌표계·기간·격자·원천 표기·용량)은 **null·0 으로 비운다** —
//     화면은 그 자리에 `—` 를 적는다. 없는 값을 지어내지 않는다 (`P1.md §5-2`).
// 서버가 붙으면 `apiDetailSource` 가 그대로 들어오고 이 파일은 시험에서만 쓰인다.
import { DatasetGone, type DatasetDetail, type DetailSource } from './types';

const 호랑이 = { accountId: '01JYZ9K7WQ3N8V4M2X6C5B0U01', name: '호랑이' };
const 표범 = { accountId: '01JYZ9K7WQ3N8V4M2X6C5B0U02', name: '표범' };
const 강아지 = { accountId: '01JYZ9K7WQ3N8V4M2X6C5B0U03', name: '강아지' };

const NO_VERIFICATION = {
  verified: false,
  approver: null,
  approvedAt: null,
  cancelledBy: null,
  cancelledAt: null,
  cancellationReason: null,
} satisfies DatasetDetail['verification'];

/** 상단(헤더·기본 정보)은 아무 행동도 열지 않는다. 액션의 판정은 전부 서버가 한다 (P-7). */
const NO_ACTIONS = {
  canRequestVerification: false,
  canApproveVerification: false,
  canCancelVerification: false,
  canEditLineage: false,
  canDelete: false,
  canDownload: false,
  canRequestAccess: false,
} satisfies DatasetDetail['actions'];

/** 목업 카탈로그 행만 아는 데이터셋 — 상세 목업이 없어 기본 정보 대부분이 빈 값이다. */
function fromCatalogRowOnly(row: {
  datasetId: string;
  name: string;
  topic: string;
  processingLevel: number;
  lineageState: DatasetDetail['lineageState'];
  lineageConfirmedAt: string | null;
  fileCount: number;
  uploader: { accountId: string; name: string };
  uploadedAt: string;
  lastModifiedAt: string;
  verified: boolean;
}): DatasetDetail {
  return {
    datasetId: row.datasetId,
    name: row.name,
    fileName: row.name,
    summary: null,
    topic: row.topic,
    processingLevel: row.processingLevel,
    lineageState: row.lineageState,
    verification: { ...NO_VERIFICATION, verified: row.verified },
    accessState: '열림',
    bodyAccessible: true,
    accessRequestPending: false,
    uploadedAt: row.uploadedAt,
    lastModifiedAt: row.lastModifiedAt,
    lineageConfirmedAt: row.lineageConfirmedAt,
    basicInfo: {
      variables: [],
      crs: null,
      period: null,
      grid: null,
      format: null,
      files: { count: row.fileCount, totalSizeBytes: 0, hasReferenceGridFile: false },
      sourceLabel: null,
      owner: row.uploader,
      uploader: row.uploader,
    },
    projects: [],
    actions: NO_ACTIONS,
  };
}

export const FIXTURE_DETAILS: Record<string, DatasetDetail> = {
  // ── 상세 목업 기본 장면 ──────────────────────────────────────────────────────
  '01JYZ9K7WQ3N8V4M2X6C5B0AA1': {
    datasetId: '01JYZ9K7WQ3N8V4M2X6C5B0AA1',
    name: '낙동강 유역 강우 (2025)',
    fileName: 'nakdong_precip_2025_Lv2.nc',
    summary: '유역 평균 강수량',
    topic: '강우·강수',
    processingLevel: 2,
    lineageState: '확인 필요',
    verification: { ...NO_VERIFICATION, verified: true },
    accessState: '열림',
    bodyAccessible: true,
    accessRequestPending: false,
    uploadedAt: '2026-07-30T00:00:00Z',
    lastModifiedAt: '2026-08-11T00:00:00Z',
    lineageConfirmedAt: '2026-07-30T00:00:00Z',
    basicInfo: {
      variables: ['시간별 격자 강수량 (tp, mm)'],
      crs: 'EPSG:5179',
      period: { start: '2025-06-01T00:00:00Z', end: '2025-09-30T00:00:00Z' },
      grid: '0.05° (~5km)',
      format: 'nc',
      // 목업: `파일 조각 4개 · 합계 148 MB` · `기준 격자 파일 없음`
      files: { count: 4, totalSizeBytes: 148 * 1024 * 1024, hasReferenceGridFile: false },
      sourceLabel: 'ERA5 재분석 · GK2A 위성',
      owner: 호랑이, // 목업: `소유·업로드 호랑이`
      uploader: 호랑이,
    },
    projects: [],
    actions: NO_ACTIONS,
  },

  // ── 상세 목업 D-03 잠긴 데이터 상세 ─────────────────────────────────────────
  // 잠기면 `basicInfo` 가 null 이다 — 기본 정보를 통째로 비운다 (`§7` · `PLAN-SoT §9-㊼-④`).
  '01JYZ9K7WQ3N8V4M2X6C5B0AA5': {
    datasetId: '01JYZ9K7WQ3N8V4M2X6C5B0AA5',
    name: '낙동강 유역 유출량 (2025)',
    fileName: 'nakdong_runoff_2025_Lv2.nc',
    summary: '강우와 짝이 되는 유출 결과',
    // 주제 = NULL. 4값(`〈55〉` · `㊸-④-2`)에 유출을 담을 값이 없다 —
    // 억지로 가까운 값에 배정하면 검색·분류가 조용히 틀린다. 미분류로 둔다.
    topic: null,
    processingLevel: 2,
    lineageState: '확정',
    verification: NO_VERIFICATION,
    accessState: '잠김',
    bodyAccessible: false,
    accessRequestPending: false,
    uploadedAt: '2026-04-18T00:00:00Z',
    lastModifiedAt: '2026-04-18T00:00:00Z',
    lineageConfirmedAt: '2026-04-18T00:00:00Z',
    basicInfo: null,
    projects: null,
    actions: NO_ACTIONS,
  },

  '01JYZ9K7WQ3N8V4M2X6C5B0AA2': fromCatalogRowOnly({
    datasetId: '01JYZ9K7WQ3N8V4M2X6C5B0AA2',
    name: 'GK2A_rain_202506_Lv0.HDF5',
    topic: '강우·강수',
    processingLevel: 0,
    lineageState: '원천',
    lineageConfirmedAt: null,
    fileCount: 72,
    uploader: 표범,
    uploadedAt: '2026-07-01T00:00:00Z',
    lastModifiedAt: '2026-07-01T00:00:00Z',
    verified: false,
  }),
  '01JYZ9K7WQ3N8V4M2X6C5B0AA3': fromCatalogRowOnly({
    datasetId: '01JYZ9K7WQ3N8V4M2X6C5B0AA3',
    name: 'nakdong_DEM_10m.tif',
    topic: '지형·DEM',
    processingLevel: 1,
    lineageState: '기록 없음',
    lineageConfirmedAt: null,
    fileCount: 1,
    uploader: 강아지,
    uploadedAt: '2026-06-11T00:00:00Z',
    lastModifiedAt: '2026-06-11T00:00:00Z',
    verified: false,
  }),
  '01JYZ9K7WQ3N8V4M2X6C5B0AA4': fromCatalogRowOnly({
    datasetId: '01JYZ9K7WQ3N8V4M2X6C5B0AA4',
    name: 'GK2A_NDVI_2025_Lv2.tif',
    topic: '식생·NDVI',
    processingLevel: 2,
    lineageState: '확정',
    lineageConfirmedAt: '2026-05-02T00:00:00Z',
    fileCount: 1,
    uploader: 표범,
    uploadedAt: '2026-05-02T00:00:00Z',
    lastModifiedAt: '2026-05-02T00:00:00Z',
    verified: true,
  }),
  '01JYZ9K7WQ3N8V4M2X6C5B0AA6': fromCatalogRowOnly({
    datasetId: '01JYZ9K7WQ3N8V4M2X6C5B0AA6',
    name: 'ERA5_precip_2025_Lv1.grib',
    topic: '강우·강수',
    processingLevel: 1,
    lineageState: '확인 필요',
    lineageConfirmedAt: '2025-09-01T00:00:00Z',
    fileCount: 1,
    uploader: 호랑이,
    uploadedAt: '2025-09-01T00:00:00Z',
    lastModifiedAt: '2025-10-02T00:00:00Z',
    verified: false,
  }),
};

export function fixtureDetailSource(
  details: Record<string, DatasetDetail> = FIXTURE_DETAILS,
): DetailSource {
  return {
    async get(datasetId) {
      const found = details[datasetId];
      if (!found) throw new DatasetGone();
      return found;
    },
  };
}
