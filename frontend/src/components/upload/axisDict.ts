// 분류 3축 값 사전 — PRD-01·02·03 원문 표를 **축자로** 옮긴 것이다 (rev1 `AXIS_DEF` 일치).
//
// 지키는 것
//  - **한 곳이다.** PRD-04(정의·예시 한 줄)와 PRD-33(설명 칸 힌트·유형 참고 줄)이 같은
//    사전을 읽는다. 두 벌을 두면 한쪽만 고쳐지는 날이 오고 그날 다른 한쪽이 조용히 틀린다.
//  - **저장값은 국문 단일이다**(미결-13 ⓐ). 영문 병기는 표시층뿐이고 CHECK·필터·색인은 국문만 안다.
//  - **15값 전부에 정의·예시·부가 문구가 있다.** 빈 값 0 이 수용 기준이다.
//  - ⛔ 유형↔가공 단계 조합 검증을 만들지 않는다(미결-14 ⓐ) — 세 축은 서로 독립이다.

/** 축 값 하나 — 저장값·영문 병기·정의·예시·부가 문구. */
export interface AxisValue {
  /** 저장값(국문 단일). 셀렉트의 `value` 이자 계약에 실리는 값이다. */
  readonly value: string;
  /** 영문 병기 — **표시만**이다. `기상·기후 인자 (Meteorological & Climatic Factors)`. */
  readonly en: string;
  /** 화면 라벨. 가공 단계만 저장값과 다르다(`Lv2` ↔ `Lv2 · 도출된 2차 산출물`). */
  readonly label: string;
  /** PRD 표의 `설명` / `정의 · 설명` 열. */
  readonly def: string;
  /** PRD 표의 `대표 인자 예시` / `대표 예시` / `데이터 예시` 열. */
  readonly example: string;
  /**
   * 부가 문구 — 축마다 읽는 열이 다르다.
   *  - 분류 = `메타데이터 항목` · 유형 = `특이사항 및 주의점` · 가공 단계 = `메타데이터 필수 항목`.
   */
  readonly extra: string;
}

/** 국문＋영문 병기 표기 (PRD-02 원문 축자 형식) — `재분석자료 (Reanalysis Data)`. */
export function bilingual(v: AxisValue): string {
  return `${v.label} (${v.en})`;
}

/** 분류(Data Category) 5값 — PRD-01 원문 축자. */
export const CATEGORIES: readonly AxisValue[] = [
  {
    value: '수문 인자',
    en: 'Hydrological Factors',
    label: '수문 인자',
    def: '유역 내 수문 순환과 직접적으로 관련 인자',
    example: '유량, 수위, 적설량',
    extra: '유역코드, 관측 해상도',
  },
  {
    value: '기상·기후 인자',
    en: 'Meteorological & Climatic Factors',
    label: '기상·기후 인자',
    def: '기상 조건 및 기후변동성과 관련 자료',
    example: '강수량, 기온',
    extra: '공간 해상도, 시간 간격',
  },
  {
    value: '식생·탄소 인자',
    en: 'Vegetation & Carbon Factors',
    label: '식생·탄소 인자',
    def: '생태계 반응, 생물활동, 탄소 순환과 관련 요소',
    example: 'NDVI, GPP',
    extra: '위성플랫폼, 연산 방식',
  },
  {
    value: '사회·경제 인자',
    en: 'Socio-Economic Factors',
    label: '사회·경제 인자',
    def: '인간 활동 및 사회적 구조와 관련 지표',
    example: '인구밀도, 토지이용',
    extra: '통계 출처, 행정구역 단위',
  },
  {
    value: '환경 인자',
    en: 'Environmental Factors',
    label: '환경 인자',
    def: '물, 공기, 토양 등의 환경 상태와 직접 관련 요소',
    example: '대기오염농도, 토양오염지수',
    extra: '측정 기준, 샘플링 위치',
  },
] as const;

/** 유형(Data Type) 6값 — PRD-02 원문 축자. `extra` = `특이사항 및 주의점`. */
export const DATA_TYPES: readonly AxisValue[] = [
  {
    value: '지상관측자료',
    en: 'In-situ Observation',
    label: '지상관측자료',
    def: '지표면 또는 근처에서 센서를 통해 직접 측정하거나 원격 감지한 데이터',
    example: 'AWS 기온/강수, 수위/유량/적설',
    extra: '레이더도 지상 설치된 경우 포함, 포인트 또는 범위관측',
  },
  {
    value: '위성자료',
    en: 'Satellite-based Data',
    label: '위성자료',
    def: '인공위성에 탑재된 센서를 통해 원격탐사 방식으로 수집된 자료',
    example: 'MODIS NDVI, LST, GPM, Himawari',
    extra: '해상도, 궤도 정보 명시 필요',
  },
  {
    value: '재분석자료',
    en: 'Reanalysis Data',
    label: '재분석자료',
    def: '관측자료 + 수치모형을 동화한 격자 기반 통계-물리 결합 자료',
    example: 'ERA5, NCEP/NCAR, KMA LDAPS, KLAPS',
    extra: '시계열 일관성 우수, 시간 지연(latency) 존재',
  },
  {
    value: '수치모형자료',
    en: 'Numerical Model Output',
    label: '수치모형자료',
    def: '수치모델을 통해 특정 현상을 예측하거나 재현한 시뮬레이션 결과',
    example: 'WRF, SWAT, DSSAT',
    extra: '초기조건 및 설정 파라미터 기재 필요',
  },
  {
    value: '합성자료',
    en: 'Fused / Blended Data',
    label: '합성자료',
    def: '복수 자료를 융합하여 도출한 결과로, 관측 기반 또는 시뮬레이션 포함 가능',
    example: '레이더+위성 기반 강수 추정, NWP+위성 융합 예측',
    extra: '생성 방식, 융합 기법의 상세 설명 필요',
  },
  {
    value: '관측 기반 산출물',
    en: 'Derived Observation Products',
    label: '관측 기반 산출물',
    def: '관측자료를 활용하여 계산된 파생 인자',
    example: 'SPI, ET₀, NDVI 기반 생물계절지표',
    extra: 'Level 2와 밀접하게 연계됨',
  },
] as const;

/**
 * 가공단계(Lv) 4값 — PRD-03 원문 축자.
 *
 * ⚠ **저장값과 화면 라벨이 다른 유일한 축이다** — 저장은 `Lv0`~`Lv3`(DB CHECK 4값),
 *   화면은 `Lv2 · 도출된 2차 산출물`. `en` 은 병기할 영문이 표에 없어 라벨을 그대로 둔다.
 */
export const PROCESSING_LEVELS: readonly AxisValue[] = [
  {
    value: 'Lv0',
    en: 'Lv0',
    label: 'Lv0 · 원시 데이터',
    def: '원시 데이터',
    example: 'ERA5 원자료, 기상청 레이더 NetCDF',
    extra: '출처(Source URL), 다운로드 일자',
  },
  {
    value: 'Lv1',
    en: 'Lv1',
    label: 'Lv1 · 기초 전처리 완료 자료',
    def: '기초 전처리 완료 자료',
    example: 'NAN 보간, 좌표계 변환 등',
    extra: '보간방법, 좌표계 유형',
  },
  {
    value: 'Lv2',
    en: 'Lv2',
    label: 'Lv2 · 도출된 2차 산출물',
    def: '도출된 2차 산출물',
    example: 'SPI, PDSI, NDVI 변형',
    extra: '산출 방법(논문/수식)',
  },
  {
    value: 'Lv3',
    en: 'Lv3',
    label: 'Lv3 · 유형화 및 고차 분석 결과',
    def: '유형화 및 고차 분석 결과',
    example: '재해 유형별 군집화',
    extra: '유형화 기준, 클러스터 기반 리스크 매핑',
  },
] as const;

/** 기본 선택값 — rev1 `<option selected>` ＋ Policy `VAL-004`·`VAL-004b` 축자. */
export const DEFAULT_CATEGORY = '기상·기후 인자';
export const DEFAULT_DATA_TYPE = '재분석자료';
export const DEFAULT_PROCESSING_LEVEL = 'Lv2';

/** 세 축의 값 하나를 저장값으로 찾는다. 없는 값이면 `null` — 화면이 지어내지 않는다. */
export function findAxis(list: readonly AxisValue[], value: string): AxisValue | null {
  return list.find((v) => v.value === value) ?? null;
}
