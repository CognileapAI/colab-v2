// 픽스처 — 서버 op 이 아직 501 을 낼 동안 화면을 세워 두는 자리.
// **값은 정본 목업 `mockups/프로젝트_260817.html` 의 `PROJ` 다섯 건 그대로다.** 새 데이터를
// 지어내지 않는다. 서버가 붙으면 `apiProjectSource` 가 그대로 들어오고 이 파일은 시험에서만 쓰인다.
//
// **목업에서 계약으로 옮기며 값을 고른 자리 셋** (그대로 옮길 수 없어 적어 둔다) —
//  ① 목업의 `g`(부모 수)는 계보 **상태 4값**이 아니다. `null → 기록 없음` · `0 → 원천`
//     (부모가 없고 원천 표기가 있다) · `>0 → 확정` 으로 옮겼다. 서버의 판정식과 같은 뜻이다.
//  ② 목업의 `t`("2025-06~09")는 표시 문자열이고 계약 `DataPeriod` 는 date-time 두 개다.
//     달의 첫날·끝날로 폈다 — **픽스처 저작이지 측정값이 아니다.**
//  ③ 목업에는 잠긴 소속 데이터셋이 한 건도 없다. **없는 것을 지어내지 않는다** — 잠김 표시의
//     시험은 `test/project.test.tsx` 가 자기 출처를 세워서 한다.
import type { ProjectDatasetRow, ProjectDetail, ProjectRow, ProjectSource } from './types';
import { ProjectGone } from './types';

type Seed = { g: number | null; v: boolean; period: [string, string] | null; slices?: number };

function ds(name: string, level: number, seed: Seed): ProjectDatasetRow {
  return {
    datasetId: name,
    name,
    fileCount: seed.slices ?? 1,
    processingLevel: level,
    period: seed.period === null ? null : { start: seed.period[0], end: seed.period[1] },
    lineageState: seed.g === null ? '기록 없음' : seed.g === 0 ? '원천' : '확정',
    verified: seed.v,
    accessState: '열림',
    bodyAccessible: true,
    // 목업의 소속 데이터셋 표에는 **활용 의미 문장 열이 없다** (§5 표 구성 6열).
    // 그 문장을 읽는 자리는 데이터셋 상세의 `활용 프로젝트` 다 (E-03).
    usageNote: null,
  };
}

const Y = (year: number) => [`${year}-01-01T00:00:00Z`, `${year}-12-31T00:00:00Z`] as [string, string];

export const FIXTURE_PROJECTS: ProjectDetail[] = [
  {
    projectId: 'p1',
    name: '낙동강 유역 홍수기 강우-유출 응답 분석',
    type: '국가과제',
    status: '진행 중',
    period: { start: '2025-03', end: '2025-12' },
    description:
      '낙동강 유역의 2025년 홍수기(6~9월) 강우와 유출 관계를 분석하는 국가과제예요. 위성·재분석 강우를 유역 단위로 집계해 유출 응답 지연을 추정해요.',
    link: 'https://www.ntis.go.kr/project/2025-NRF-0413',
    canManage: true,
    datasets: [
      ds('nakdong_flood_index_2025_Lv3.nc', 3, { g: 3, v: false, period: ['2025-06-01T00:00:00Z', '2025-09-30T00:00:00Z'] }),
      ds('nakdong_precip_2025_Lv2.nc', 2, { g: 2, v: true, period: ['2025-06-01T00:00:00Z', '2025-09-30T00:00:00Z'], slices: 4 }),
      ds('nakdong_runoff_2025_Lv2.nc', 2, { g: 2, v: true, period: ['2025-06-01T00:00:00Z', '2025-09-30T00:00:00Z'] }),
      ds('nakdong_soil_2024_Lv2.nc', 2, { g: 1, v: false, period: Y(2024) }),
      ds('ERA5_precip_2025_Lv1.grib', 1, { g: 0, v: true, period: Y(2025) }),
      ds('ERA5_temp_2025_Lv1.grib', 1, { g: 0, v: false, period: Y(2025) }),
      ds('GK2A_rain_202506_Lv0.HDF5', 0, { g: 0, v: false, period: ['2025-06-01T00:00:00Z', '2025-06-30T00:00:00Z'] }),
      ds('GK2A_rain_202507_Lv0.HDF5', 0, { g: 0, v: false, period: ['2025-07-01T00:00:00Z', '2025-07-31T00:00:00Z'] }),
      ds('nakdong_basin_boundary_Lv1.shp', 1, { g: 0, v: true, period: Y(2024) }),
      ds('nakdong_station_obs_2025_Lv1.csv', 1, { g: null, v: false, period: ['2025-06-01T00:00:00Z', '2025-09-30T00:00:00Z'] }),
      ds('nakdong_dem_10m_Lv1.tif', 1, { g: 0, v: true, period: Y(2024) }),
      ds('nakdong_landuse_2023_Lv1.tif', 1, { g: null, v: false, period: Y(2023) }),
    ],
  },
  {
    projectId: 'p2',
    name: 'GK2A 위성 식생지수 시계열 구축',
    type: '논문',
    status: '진행 중',
    period: { start: '2024-06', end: '2025-02' },
    description:
      '천리안 2A 위성 자료로 식생지수 시계열을 만들어 가뭄 감시에 쓸 수 있는지 확인한 논문이에요.',
    link: 'https://doi.org/10.1234/colab.2025.0182',
    canManage: true,
    datasets: [
      ds('GK2A_NDVI_2025_Lv2.tif', 2, { g: 2, v: true, period: Y(2025) }),
      ds('GK2A_NDVI_2024_Lv2.tif', 2, { g: 2, v: true, period: Y(2024) }),
      ds('GK2A_LULC_2024_Lv1.tif', 1, { g: null, v: false, period: Y(2024) }),
      ds('GK2A_LST_2024_Lv1.tif', 1, { g: 1, v: true, period: Y(2024) }),
      ds('GK2A_refl_202406_Lv0.HDF5', 0, { g: 0, v: false, period: ['2024-06-01T00:00:00Z', '2024-06-30T00:00:00Z'], slices: 72 }),
      ds('GK2A_refl_202407_Lv0.HDF5', 0, { g: 0, v: false, period: ['2024-07-01T00:00:00Z', '2024-07-31T00:00:00Z'] }),
      ds('drought_index_2024_Lv3.nc', 3, { g: 3, v: false, period: Y(2024) }),
      ds('station_ndvi_val_2024_Lv1.csv', 1, { g: null, v: false, period: Y(2024) }),
    ],
  },
  {
    projectId: 'p3',
    name: '한강 상류 DEM 기반 유역 경계 재산정',
    type: '국가과제',
    status: '진행 중',
    period: { start: '2024-01', end: '2024-11' },
    description: '10미터 수치표고자료로 한강 상류 유역 경계를 다시 계산한 과제예요.',
    link: 'https://www.ntis.go.kr/project/2024-MOE-0771',
    canManage: true,
    datasets: [
      ds('hangang_DEM_5m_Lv1.tif', 1, { g: 0, v: true, period: Y(2024) }),
      ds('hangang_DEM_10m_Lv1.tif', 1, { g: 0, v: false, period: Y(2024) }),
      ds('hangang_basin_v2_Lv2.shp', 2, { g: 1, v: true, period: Y(2024) }),
      ds('hangang_flowdir_Lv2.tif', 2, { g: 1, v: false, period: Y(2024) }),
      ds('hangang_station_Lv0.csv', 0, { g: null, v: false, period: Y(2023) }),
    ],
  },
  {
    // **설명·연결 주소가 둘 다 빈 프로젝트다** — 카드의 「설명 적기 권유」와 상세의
    // 「주소 적기」 빈 상태가 이 한 건으로 그려진다 (§5 설명 · §8 연결 주소 빈 상태).
    projectId: 'p4',
    name: 'ERA5 재분석 강수 편의 보정 방법 비교',
    type: '논문',
    status: '진행 중',
    period: { start: '2025-01', end: '2025-06' },
    description: null,
    link: null,
    canManage: true,
    datasets: [
      ds('ERA5_precip_2025_Lv1.grib', 1, { g: 0, v: false, period: Y(2025) }),
      ds('ERA5_precip_bc_2025_Lv2.nc', 2, { g: 1, v: false, period: Y(2025) }),
      ds('station_precip_2025_Lv0.csv', 0, { g: null, v: false, period: Y(2025) }),
    ],
  },
  {
    projectId: 'p5',
    name: '금강 하굿둑 염분 확산 모의',
    type: '논문',
    status: '닫힘',
    period: { start: '2023-03', end: '2024-02' },
    description:
      '금강 하굿둑 운영에 따른 염분 확산을 모의한 논문이에요. 2024년에 게재를 마쳤어요.',
    link: 'https://doi.org/10.1234/colab.2024.0077',
    canManage: true,
    datasets: [
      ds('geum_salinity_2023_Lv2.nc', 2, { g: 1, v: false, period: Y(2023) }),
      ds('geum_tide_2023_Lv1.csv', 1, { g: 0, v: false, period: Y(2023) }),
    ],
  },
];

/** 지표 타일 세 칸은 소속 데이터셋에서 **세어서** 나온다 — 두 곳에 적으면 갈라진다. */
export function rowOf(detail: ProjectDetail): ProjectRow {
  return {
    projectId: detail.projectId,
    name: detail.name,
    type: detail.type,
    status: detail.status,
    period: detail.period,
    description: detail.description,
    datasetCount: detail.datasets.length,
    verifiedCount: detail.datasets.filter((d) => d.verified).length,
    unknownLineageCount: detail.datasets.filter((d) => d.lineageState === '기록 없음').length,
  };
}

export const FIXTURE_ROWS: ProjectRow[] = FIXTURE_PROJECTS.map(rowOf);

export function fixtureProjectSource(): ProjectSource {
  return {
    async list(query) {
      const items = FIXTURE_ROWS.filter(
        (r) =>
          (query.status === '전체' || r.status === query.status) &&
          (query.type === '전체' || r.type === query.type),
      );
      return { items: sortRows(items, query.sort), totalCount: items.length };
    },
    async get(projectId) {
      const found = FIXTURE_PROJECTS.find((p) => p.projectId === projectId);
      if (!found) throw new ProjectGone();
      return found;
    },
    // ── 쓰기 다섯 — **부르면 죽는다.** ───────────────────────────────────────
    //
    // 픽스처는 서버가 없을 때 **읽을 화면을 세우는 자리**이고, 쓰기를 흉내 내면
    // 저장되지 않은 것을 저장됐다고 말한다. 화면 시험은 자기 출처를 세워서 한다
    // (`test/project.test.tsx` — 잠긴 데이터셋 시험이 이미 그 무늬다).
    async create() {
      throw new Error('픽스처는 쓰기를 흉내 내지 않는다.');
    },
    async update() {
      throw new Error('픽스처는 쓰기를 흉내 내지 않는다.');
    },
    async setStatus() {
      throw new Error('픽스처는 쓰기를 흉내 내지 않는다.');
    },
    async remove() {
      throw new Error('픽스처는 쓰기를 흉내 내지 않는다.');
    },
    async unlink() {
      throw new Error('픽스처는 쓰기를 흉내 내지 않는다.');
    },
  };
}

/**
 * **빈 기간은 언제나 뒤로 간다.** 없는 값을 최댓값·최솟값으로 취급하면 정렬을 바꿀 때마다
 * 같은 프로젝트가 맨 앞과 맨 뒤를 오간다. 서버(`routes/project.py::_sort_rows`)와 같은 규칙이다.
 */
export function sortRows(rows: ProjectRow[], sort: string): ProjectRow[] {
  if (sort === '데이터셋 많은 순') {
    return [...rows].sort((a, b) => b.datasetCount - a.datasetCount || a.name.localeCompare(b.name));
  }
  const key = sort === '최근 종료 순' ? 'end' : 'start';
  const ascending = sort === '먼저 시작한 순';
  const dated = rows.filter((r) => r.period?.[key]);
  const undated = rows.filter((r) => !r.period?.[key]);
  dated.sort((a, b) => {
    const x = String(a.period?.[key]);
    const y = String(b.period?.[key]);
    return ascending ? x.localeCompare(y) : y.localeCompare(x);
  });
  return [...dated, ...undated.sort((a, b) => a.name.localeCompare(b.name))];
}
