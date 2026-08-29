// 계보 그래프 픽스처 — core 가 `getDatasetLineage` 를 라우팅할 동안 화면을 세워 두는 자리.
// **값은 정본 목업에서 그대로 온다.** 새 계보를 지어내지 않는다.
//   · 기본 장면 = `E-03_데이터셋_상세/mockups/데이터셋_상세_260817.html` 의 계보 그래프
//     (원천 `ERA5 재분석`·`GK2A 위성` → 가공 전 `ERA5_precip_2025_Lv1.grib`
//      → 이 데이터 `nakdong_precip_2025_Lv2.nc` → 파생 `nakdong_flood_index_2025_Lv3.nc`)
//   · 기록 없음 장면 = 같은 목업의 `linEmpty` 상태 (`nakdong_DEM_10m.tif`)
// 목업이 주지 않는 값(가공 방식·확인 이력 없는 자리)은 null 로 비운다.
import type { LineageGraph, LineageGraphSource } from './graphTypes';

const 호랑이 = { accountId: '01JYZ9K7WQ3N8V4M2X6C5B0U01', name: '호랑이' };
const 강아지 = { accountId: '01JYZ9K7WQ3N8V4M2X6C5B0U03', name: '강아지' };

const SELF = '01JYZ9K7WQ3N8V4M2X6C5B0AA1'; // nakdong_precip_2025_Lv2.nc
const PARENT = '01JYZ9K7WQ3N8V4M2X6C5B0AA6'; // ERA5_precip_2025_Lv1.grib
/** 목업의 파생 데이터. 카탈로그 6행에는 없어 상세 픽스처에도 없다 — 그래프에만 있는 노드다. */
const CHILD = '01JYZ9K7WQ3N8V4M2X6C5B0AA7'; // nakdong_flood_index_2025_Lv3.nc
const UNKNOWN = '01JYZ9K7WQ3N8V4M2X6C5B0AA3'; // nakdong_DEM_10m.tif

export const FIXTURE_LINEAGE: Record<string, LineageGraph> = {
  [SELF]: {
    datasetId: SELF,
    lineageState: '확인 필요',
    lineageConfirmedAt: '2026-07-30T00:00:00Z',
    unknownParents: false,
    nodes: [
      // 원천은 연구실 데이터셋이 아니라 표기다 — `datasetId` 가 null 이고 이동하지 않는다
      { kind: '원천', datasetId: null, name: 'ERA5 재분석', processingLevel: 0,
        verified: false, navigable: false, bodyAccessible: true, deletedAt: null },
      { kind: '원천', datasetId: null, name: 'GK2A 위성', processingLevel: 0,
        verified: false, navigable: false, bodyAccessible: true, deletedAt: null },
      { kind: '가공 전', datasetId: PARENT, name: 'ERA5_precip_2025_Lv1.grib',
        processingLevel: 1, verified: false, navigable: true, bodyAccessible: true,
        deletedAt: null },
      { kind: '이 데이터', datasetId: SELF, name: 'nakdong_precip_2025_Lv2.nc',
        processingLevel: 2, verified: true, navigable: false, bodyAccessible: true,
        deletedAt: null },
      { kind: '파생', datasetId: CHILD, name: 'nakdong_flood_index_2025_Lv3.nc',
        processingLevel: 3, verified: false, navigable: true, bodyAccessible: true,
        deletedAt: null },
    ],
    edges: [
      // 원천 → 가공 전 두 줄. 목업은 이 두 화살표에 가공 방식 라벨을 붙이지 않았다
      { childDatasetId: PARENT, parentDatasetId: null, parentRole: '주입력', method: null,
        origin: 'manual', confirmedBy: 호랑이, confirmedAt: '2026-08-05T00:00:00Z' },
      { childDatasetId: PARENT, parentDatasetId: null, parentRole: '보조입력', method: null,
        origin: 'manual', confirmedBy: 호랑이, confirmedAt: '2026-08-05T00:00:00Z' },
      { childDatasetId: SELF, parentDatasetId: PARENT, parentRole: '주입력',
        method: '유역 클리핑 · 유역 평균', origin: 'ai', confirmedBy: 호랑이,
        confirmedAt: '2026-08-05T00:00:00Z' },
      { childDatasetId: CHILD, parentDatasetId: SELF, parentRole: '주입력',
        method: '임계값 초과일 집계', origin: 'ai', confirmedBy: 강아지,
        confirmedAt: '2026-08-04T00:00:00Z' },
    ],
    projectUseCount: 2, // 목업 `활용 프로젝트 2건 ›`
    canEdit: false, // 목업 기본 장면은 보기 전용이다
  },

  [UNKNOWN]: {
    datasetId: UNKNOWN,
    lineageState: '기록 없음',
    lineageConfirmedAt: null,
    unknownParents: true,
    nodes: [
      { kind: '이 데이터', datasetId: UNKNOWN, name: 'nakdong_DEM_10m.tif', processingLevel: 1,
        verified: false, navigable: false, bodyAccessible: true, deletedAt: null },
    ],
    edges: [],
    projectUseCount: 0,
    canEdit: false,
  },
};

export function fixtureLineageSource(
  graphs: Record<string, LineageGraph> = FIXTURE_LINEAGE,
): LineageGraphSource {
  return {
    async get(datasetId) {
      const found = graphs[datasetId];
      // 모르는 데이터셋의 계보를 지어내지 않는다 — 부르는 쪽이 구역을 세우지 않는다
      if (!found) throw new Error('계보 픽스처가 없어요.');
      return found;
    },
  };
}
