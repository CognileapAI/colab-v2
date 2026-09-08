// 기간의 **최소 단위**와 그 단위가 여는 입력 칸 (PRD-18 · 미결-18 ⓐ · `M-7`).
//
// **저장은 바뀌지 않는다** — 계약 `DataPeriod` 는 종전대로 `date-time` 두 칸이고,
// 이 모듈은 **화면이 그 시각값을 조립·해체하는 규칙**만 갖는다. 미결-18 ⓐ 축자 =
// 「기간은 시각값 저장 유지, 화면이 최소 단위 셀렉트 ＋ Start/End 를 조립한다」.
//
// ⛔ **`Date` 를 쓰지 않는다.** 보는 사람의 시간대가 날짜를 하루 밀 수 있고, 그러면 같은
//    데이터가 사람마다 다른 기간을 갖는다. 조립도 해체도 **문자열 자리**로만 한다.

/** 단위 6값. **정본은 DB CHECK** (`d3_dataset_autometa.period_granularity`) 다. */
export const GRANULARITIES = ['년', '월', '일', '시', '분', '초'] as const;
export type Granularity = (typeof GRANULARITIES)[number];

/** 한 자리(칸) 하나. `key` 는 testid·`id` 의 접미사이기도 하다. */
export type PartSpec = {
  key: 'year' | 'month' | 'day' | 'hour' | 'minute' | 'second';
  label: (typeof GRANULARITIES)[number];
  /** 비워 둔 하위 자리를 저장 시 채우는 값 (아래 `assemble` 산문). */
  fill: string;
  /** 자릿수 — `2025` 는 넷, 나머지는 둘이다. */
  width: 2 | 4;
};

/**
 * 자리표. **순서가 곧 「연 → 초」의 계층**이고, 고른 단위까지 잘라 쓴다.
 *
 * `fill` — **비운 하위 자리는 0 으로 채운다**(PRD-18 축자). 다만 **월·일에는 0 이 없다** —
 * `2025-00-00` 은 시각이 아니다. 그래서 그 둘의 「가장 낮은 값」은 `01` 이고, 0 이 뜻하는
 * 「그 자리를 안 정했다」를 시각값으로 옮기면 그것이 된다. 시·분·초는 그대로 `00` 이다.
 */
export const PARTS: readonly PartSpec[] = [
  { key: 'year', label: '년', fill: '', width: 4 },
  { key: 'month', label: '월', fill: '01', width: 2 },
  { key: 'day', label: '일', fill: '01', width: 2 },
  { key: 'hour', label: '시', fill: '00', width: 2 },
  { key: 'minute', label: '분', fill: '00', width: 2 },
  { key: 'second', label: '초', fill: '00', width: 2 },
];

export type PeriodParts = Record<PartSpec['key'], string>;

export const EMPTY_PARTS: PeriodParts = {
  year: '', month: '', day: '', hour: '', minute: '', second: '',
};

/**
 * 고른 단위가 **여는 칸**. `분` 이면 `연·월·일·시·분` 다섯이다 (PRD-18 수용 기준 축자).
 * 단위를 안 골랐으면 **한 칸도 안 연다** — 그때 화면은 종전 날짜 칸 두 개를 그대로 쓴다.
 */
export function partsFor(granularity: string): readonly PartSpec[] {
  const at = GRANULARITIES.indexOf(granularity as Granularity);
  return at < 0 ? [] : PARTS.slice(0, at + 1);
}

function pad(value: string, width: number): string {
  return value.padStart(width, '0').slice(-width);
}

/**
 * 칸들 → `date-time` 하나. **연이 비면 기간이 없는 것**이다 — 연 없는 월은 시각이 아니다.
 * 열린 칸 중 비운 것과 안 연 하위 자리는 모두 `fill` 로 채운다.
 */
export function assemble(parts: PeriodParts, granularity: string): string | null {
  if (!parts.year.trim()) return null;
  const open = new Set(partsFor(granularity).map((p) => p.key));
  const value = (spec: PartSpec): string => {
    const raw = open.has(spec.key) ? parts[spec.key].trim() : '';
    return pad(raw || spec.fill, spec.width);
  };
  const [y, mo, d, h, mi, s] = PARTS.map(value);
  return `${y}-${mo}-${d}T${h}:${mi}:${s}Z`;
}

/**
 * 기간 역전의 **문면 정본은 서버**다 — `services/core-api/…/app/routes/catalog.py` 축자.
 * 화면이 새 문장을 지으면 같은 거절이 두 얼굴이 된다(WU-A4 가 세운 규율 그대로).
 */
export const PERIOD_INVERTED_MESSAGE = '기간의 종료는 시작보다 앞설 수 없다.';

/**
 * `YYYY-MM-DD` 도 `YYYY-MM-DDTHH:MM:SSZ` 도 같은 자리로 편다.
 * ⚠ **시간대 표기는 붙지 않는다** — 이 화면의 시각값은 `assemble` 이 만든 UTC(`Z`) 하나뿐이라
 *   서버가 경계한 「표기가 다른 두 값의 문자열 비교」가 여기서는 성립하지 않는다.
 */
function flatten(value: string): string {
  const bare = value.trim().replace(/Z$/, '');
  return bare.length <= 10 ? `${bare}T00:00:00` : bare;
}

/**
 * 종료가 시작보다 앞서는가 — 서버 400 과 **같은 판정**을 화면이 먼저 한다.
 * 한쪽이 비면 다투지 않는다(종료는 비울 수 있다 · PRD-40 판정 ⓐ). 시작=끝은 역전이 아니다.
 * ⛔ 서버 검사를 걷지 않는다 — 화면은 **먼저** 알릴 뿐이고 정본은 그대로 서버다.
 */
export function isPeriodInverted(
  start: string | null | undefined,
  end: string | null | undefined,
): boolean {
  if (!start?.trim() || !end?.trim()) return false;
  return flatten(end) < flatten(start);
}

/** `date-time` → 칸들. 되읽기(수정 화면)와 시험이 쓴다. */
export function disassemble(iso: string | null | undefined): PeriodParts {
  if (!iso) return { ...EMPTY_PARTS };
  return {
    year: iso.slice(0, 4),
    month: iso.slice(5, 7),
    day: iso.slice(8, 10),
    hour: iso.slice(11, 13),
    minute: iso.slice(14, 16),
    second: iso.slice(17, 19),
  };
}
