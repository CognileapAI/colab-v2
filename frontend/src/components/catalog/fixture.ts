// 픽스처 — 서버 op 이 아직 501 을 낼 동안 화면을 세워 두는 자리.
// **값은 정본 목업 `mockups/데이터_찾기_260817.html` 의 카탈로그 6행 그대로다.** 새 데이터를 지어내지 않는다.
// 서버가 붙으면 `apiCatalogSource` 가 그대로 들어오고 이 파일은 시험에서만 쓰인다.
import { runFacets, runQuery } from './localEngine';
import type { CatalogSource, DatasetRow } from './types';

export const FIXTURE_ROWS: DatasetRow[] = [
  {
    datasetId: '01JYZ9K7WQ3N8V4M2X6C5B0AA1',
    name: 'nakdong_precip_2025_Lv2.nc',
    fileCount: 4,
    topic: '강우·강수',
    processingLevel: 2,
    projects: {
      representative: { projectId: '01JYZ9K7WQ3N8V4M2X6C5B0P01', name: '홍수기 강우-유출 분석' },
      moreCount: 1,
      names: ['홍수기 강우-유출 분석', 'ERA5 강수 편의 보정 비교'],
    },
    uploader: { accountId: '01JYZ9K7WQ3N8V4M2X6C5B0U01', name: '호랑이' },
    lastModifiedAt: '2026-08-11T00:00:00Z',
    lineageState: '확인 필요',
    lineageConfirmedAt: '2026-07-30T00:00:00Z',
    verified: true,
    accessState: '열림',
    bodyAccessible: true,
  },
  {
    datasetId: '01JYZ9K7WQ3N8V4M2X6C5B0AA2',
    name: 'GK2A_rain_202506_Lv0.HDF5',
    fileCount: 72,
    topic: '강우·강수',
    processingLevel: 0,
    projects: {
      representative: { projectId: '01JYZ9K7WQ3N8V4M2X6C5B0P01', name: '홍수기 강우-유출 분석' },
      moreCount: 0,
      names: ['홍수기 강우-유출 분석'],
    },
    uploader: { accountId: '01JYZ9K7WQ3N8V4M2X6C5B0U02', name: '표범' },
    lastModifiedAt: '2026-07-01T00:00:00Z',
    lineageState: '원천',
    lineageConfirmedAt: null,
    verified: false,
    accessState: '열림',
    bodyAccessible: true,
  },
  {
    datasetId: '01JYZ9K7WQ3N8V4M2X6C5B0AA3',
    name: 'nakdong_DEM_10m.tif',
    fileCount: 1,
    topic: '지형·DEM',
    processingLevel: 1,
    projects: {
      representative: { projectId: '01JYZ9K7WQ3N8V4M2X6C5B0P02', name: '유역 경계 재산정' },
      moreCount: 0,
      names: ['유역 경계 재산정'],
    },
    uploader: { accountId: '01JYZ9K7WQ3N8V4M2X6C5B0U03', name: '강아지' },
    lastModifiedAt: '2026-06-11T00:00:00Z',
    lineageState: '기록 없음',
    lineageConfirmedAt: null,
    verified: false,
    accessState: '열림',
    bodyAccessible: true,
  },
  {
    datasetId: '01JYZ9K7WQ3N8V4M2X6C5B0AA4',
    name: 'GK2A_NDVI_2025_Lv2.tif',
    fileCount: 1,
    topic: '식생·NDVI',
    processingLevel: 2,
    projects: {
      representative: { projectId: '01JYZ9K7WQ3N8V4M2X6C5B0P03', name: '식생지수 시계열 구축' },
      moreCount: 0,
      names: ['식생지수 시계열 구축'],
    },
    uploader: { accountId: '01JYZ9K7WQ3N8V4M2X6C5B0U02', name: '표범' },
    lastModifiedAt: '2026-05-02T00:00:00Z',
    lineageState: '확정',
    lineageConfirmedAt: '2026-05-02T00:00:00Z',
    verified: true,
    accessState: '열림',
    bodyAccessible: true,
  },
  {
    // 잠긴 행 — 표에서 사라지지 않는다. 조각 칩은 잠긴 행에도 뜬다 (`PLAN-SoT §9-㊼`)
    datasetId: '01JYZ9K7WQ3N8V4M2X6C5B0AA5',
    name: 'nakdong_runoff_2025_Lv2.nc',
    fileCount: 3,
    // 주제 = NULL. 4값(`〈55〉` · `㊸-④-2`)에 유출을 담을 값이 없다 —
    // 억지로 가까운 값에 배정하면 검색·분류가 조용히 틀린다. 미분류로 둔다.
    topic: null,
    processingLevel: 2,
    projects: {
      representative: { projectId: '01JYZ9K7WQ3N8V4M2X6C5B0P01', name: '홍수기 강우-유출 분석' },
      moreCount: 0,
      names: ['홍수기 강우-유출 분석'],
    },
    uploader: { accountId: '01JYZ9K7WQ3N8V4M2X6C5B0U04', name: '토끼' },
    lastModifiedAt: '2026-04-18T00:00:00Z',
    lineageState: '확정',
    lineageConfirmedAt: '2026-04-18T00:00:00Z',
    verified: false,
    accessState: '잠김',
    bodyAccessible: false,
  },
  {
    datasetId: '01JYZ9K7WQ3N8V4M2X6C5B0AA6',
    name: 'ERA5_precip_2025_Lv1.grib',
    fileCount: 1,
    topic: '강우·강수',
    processingLevel: 1,
    projects: {
      representative: { projectId: '01JYZ9K7WQ3N8V4M2X6C5B0P01', name: '홍수기 강우-유출 분석' },
      moreCount: 0,
      names: ['홍수기 강우-유출 분석'],
    },
    uploader: { accountId: '01JYZ9K7WQ3N8V4M2X6C5B0U01', name: '호랑이' },
    lastModifiedAt: '2025-10-02T00:00:00Z',
    lineageState: '확인 필요',
    lineageConfirmedAt: '2025-09-01T00:00:00Z',
    verified: false,
    accessState: '열림',
    bodyAccessible: true,
  },
];

export function fixtureCatalogSource(rows: DatasetRow[] = FIXTURE_ROWS): CatalogSource {
  return {
    list: async (q) => runQuery(rows, q),
    facets: async (q) => runFacets(rows, q),
  };
}
