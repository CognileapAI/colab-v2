// 기본 정보 칸의 표시 규칙. 값이 없으면 지어내지 않고 비운 표시를 쓴다.
import type { DatasetBasicInfo } from './types';

/** 정본이 값을 주지 않은 칸. 빈 칸을 지우면 아홉 칸 격자가 깨지고 「없다」는 사실도 사라진다. */
export const EMPTY = '—';

/**
 * ⭑ **⟨19차 해제 · PRD-17⟩ 관측 간격을 안 적은 행의 안내 한 줄.**
 *
 * 빈 칸으로 두면 「모른다」와 「간격이 없다」가 화면에서 갈리지 않는다. 문구는 **한 자리**에
 * 있다 — 두 벌을 두면 한쪽만 고쳐지는 날이 온다. ⛔ 재선택을 강제하지 않는다.
 */
export const INTERVAL_MISSING_NOTICE = '관측 간격 미기재';

/**
 * 기간 = 데이터가 다루는 시간 범위 (`§4` 용어). 목업 표기는 `2025-06 ~ 09` 다 —
 * 해가 같으면 뒤쪽 해를 다시 적지 않는다.
 *
 * **끝이 없으면 무기한이다** (`DataPeriod.end`: `[string, "null"]` · 14차 해제).
 * 빈 칸으로 두면 「기간을 모른다」와 「아직 안 끝났다」가 화면에서 갈리지 않는다.
 * ⚠ **`[미확인]`** — 화면 정본은 열린 기간의 문면을 정하지 않았다. `~ 진행 중` 은
 * 레포 안에서 고른 값이고, 스펙 문면이 정해지면 그것이 이긴다.
 */
export function formatPeriod(p: DatasetBasicInfo['period']): string {
  if (!p) return EMPTY;
  // ⭑ **⟨advisor ② · F4 · PRD-40⟩ 한 시점이면 한 값으로 적는다.**
  // 종료를 비운 행은 저장이 `period_end = period_start` 다(`UploadModal.humanMetadata`).
  // 그대로 범위 규칙에 태우면 `2020-06-01 00:00 ~ 00:00` 이 되어, 화면이 있지도 않은
  // 「범위」를 말한다. 괄호 병기(`formatPeriodWithInterval`)는 이 값 뒤에 그대로 붙는다.
  if (p.end && p.start === p.end) {
    return p.granularity ? cut(p.start, p.granularity) : p.start.slice(0, 10);
  }
  // ⭑ **⟨19차 해제 · PRD-18⟩ 최소 단위가 있으면 그 자리까지 적는다.**
  // `null` 이면 아래 종전 규칙 그대로다 — 기존 전 행이 그 상태이고 **재선택이 없다.**
  if (p.granularity) return formatPeriodByUnit(p.start, p.end ?? null, p.granularity);
  const s = p.start.slice(0, 7);
  if (!p.end) return `${s} ~ 진행 중`;
  const e = p.end.slice(0, 7);
  return s.slice(0, 4) === e.slice(0, 4) ? `${s} ~ ${e.slice(5, 7)}` : `${s} ~ ${e}`;
}

/**
 * 최소 단위별로 시각값을 **어디까지 적는가** (PRD-18 · `M-7`).
 *
 * 저장은 종전대로 `date-time` 하나이고(미결-18 ⓐ), 이 표가 그 값을 **되돌려 읽는 열쇠**다.
 * 단위를 모르면 `2025-06-01T00:00:00Z` 가 「6월 1일」인지 「6월 1일 0시 0분」인지 갈리지 않는다.
 *
 * 자리 = ISO 문자열의 **글자 수**다 (`2025-06-01T00:00:00Z`).
 * ⚠ **`Date` 로 파싱하지 않는다** — 보는 사람의 시간대가 날짜를 하루 밀 수 있고, 그러면
 *   같은 데이터가 사람마다 다른 기간을 갖게 된다. 종전 규칙(`slice(0, 7)`)도 같은 이유였다.
 */
const UNIT_CUT: Record<string, number> = { 년: 4, 월: 7, 일: 10, 시: 13, 분: 16, 초: 19 };

function cut(iso: string, unit: string): string {
  const n = UNIT_CUT[unit] ?? 16;
  // `T` 는 저장의 문법이고 화면의 문법이 아니다 — 사람이 읽는 자리에서는 공백이다.
  return iso.slice(0, n).replace('T', ' ');
}

function formatPeriodByUnit(start: string, end: string | null, unit: string): string {
  // ⭑ ⟨advisor ② · F4⟩ 한 시점 규칙은 「같은 날」 생략보다 **먼저** 걸린다 — 순서가 뒤집히면
  //   `2020-06-01 00:00 ~ 00:00` 이 다시 나온다. `formatPeriod` 가 이미 걸렀지만, 이 함수를
  //   직접 부르는 자리가 생겨도 같은 값을 내도록 여기서도 첫 분기다.
  if (end && start === end) return cut(start, unit);
  const s = cut(start, unit);
  if (!end) return `${s} ~ 진행 중`;
  const e = cut(end, unit);
  // **같은 날이면 날짜를 다시 적지 않는다** — 목업 축자 `2020-05-01 00:00 ~ 03:00`.
  // 종전 규칙이 「해가 같으면 해를 다시 안 적는다」였던 것과 같은 종류의 생략이다.
  if (s.length > 10 && e.length > 10 && s.slice(0, 10) === e.slice(0, 10)) {
    return `${s} ~ ${e.slice(11)}`;
  }
  // ⭑ **⟨WU-A13R · PRD-43 `D-07`⟩ 단위 `월` 에서 해가 겹치면 뒤의 해를 줄인다** —
  // 수용 기준 축자 「기간 `2025-06-01 ~ 2025-09-30` · 단위 `월` 이면 `2025-06 ~ 09`」.
  // ⚠ **`월` 에서만 줄인다.** 단위 `일` 은 PRD-18 수용 기준이 끝을 통째로 적게 하고
  // (`2025-06-01 ~ 2025-06-30` · `test/interval-period-20260906.test.tsx:311`), 그 시험이
  // 이 규칙의 경계다. 단위를 안 적은 종전 행은 위 `formatPeriod` 가 같은 생략을 이미 한다.
  if (unit === '월' && s.slice(0, 4) === e.slice(0, 4)) return `${s} ~ ${e.slice(5, 7)}`;
  return s === e ? s : `${s} ~ ${e}`;
}

/**
 * 관측 간격 한 덩이 — `10분` (PRD-17). **두 칸이 한 값**이라 반쪽이면 안 그린다.
 *
 * 계약이 표시 문자열을 싣지 않는다 — 조립은 여기서만 한다.
 */
export function formatInterval(
  interval: DatasetBasicInfo['observationInterval'] | undefined,
): string | null {
  if (!interval) return null;
  const { value, unit } = interval;
  if (value === null || value === undefined || !unit) return null;
  return `${value}${unit}`;
}

/**
 * **기간 표기의 정본 (PRD-35).** 기간을 보이는 **모든 자리**가 이 함수 하나를 쓴다 —
 * 상세 기본 정보 · 목록 카드 · 등록 미리보기. 세 자리가 같은 값을 다르게 적으면 같은
 * 데이터가 화면 사이에서 세 얼굴을 갖는다.
 *
 * 규칙 = 기간 뒤에 관측 간격을 **괄호로 병기**한다. 목업 축자
 * `2020-05-01 00:00 ~ 03:00 (10분)`.
 * ⛔ **관측 간격이 비면 괄호를 그리지 않는다** — 빈 괄호 `()` 는 「없다」가 아니라 잡음이다.
 */
export function formatPeriodWithInterval(
  period: DatasetBasicInfo['period'],
  interval: DatasetBasicInfo['observationInterval'] | undefined,
): string {
  const base = formatPeriod(period);
  const gap = formatInterval(interval);
  // 기간 자체가 없으면 빈 표시 하나다 — `— (10분)` 은 무엇의 간격인지 말하지 않는다.
  if (!gap || base === EMPTY) return base;
  return `${base} (${gap})`;
}

/** 단위 표기 — 목업이 쓰는 단위는 `MB` 다(`37 MB` · `148 MB`). */
function withUnit(bytes: number): string {
  const K = 1024;
  if (bytes >= K ** 3) return `${(bytes / K ** 3).toFixed(1)} GB`;
  if (bytes >= K ** 2) return `${Math.round(bytes / K ** 2)} MB`;
  if (bytes >= K) return `${Math.round(bytes / K)} KB`;
  return `${bytes} B`;
}

/** 용량 표기. 합계 자리 전용 — 0 은 「픽스처가 용량을 모르는 자리」라 `—` 다. */
export function formatBytes(bytes: number): string {
  if (bytes <= 0) return EMPTY; // 픽스처가 용량을 모르는 자리 — 0 B 라고 말하지 않는다
  return withUnit(bytes);
}

/**
 * 조각 **하나**의 크기. `null` = 모름 — `d3_file.size_bytes` 가 NULL 일 수 있고 그것은 0 과 다르다
 * (`〈339〉-(가)` 「모르는 값을 0 으로 적지 않는다」). `formatBytes` 의 「0 → `—`」 규칙과 **갈라 둔다**:
 * 여기서 0 은 진짜 0 B 다.
 */
export function formatFileSize(bytes: number | null): string {
  if (bytes === null) return '모름'; // [정본 무근거 · 〈339〉]
  return withUnit(bytes);
}

/**
 * `파일` 칸은 **조각 수와 용량 합계만** 말한다 (`§5`).
 * 파일이 한 건이면 파일명과 용량을 그대로 쓴다. 조각을 이 자리에 나열하지 않는다.
 */
export function formatFiles(files: DatasetBasicInfo['files'], fileName: string | null): string {
  const size = formatBytes(files.totalSizeBytes);
  if (files.count === 1) return fileName ? `${fileName} · ${size}` : size;
  return `조각 ${files.count}개 · 합계 ${size}`;
}

/**
 * 포맷 칸의 표기 — **확장자는 확장자로만 적는다** (PRD-21 · `P-10`·`R-09`).
 *
 * `.hdf` 하나가 서로 호환되지 않는 두 포맷을 가리키므로, 매직 넘버를 읽지 않는 한 단정할 수
 * 없다. 그래서 화면은 판별 결과 문자열(`format`)을 쓰지 않고 조각의 확장자를 `*.nc` 로 적는다.
 *
 * **퇴행 경로가 있다** — 확장자를 못 뽑은 기존 행은 `format` 을 그대로 보인다. 둘 다 없으면
 * 빈 표시다. 지어내지 않는다.
 *
 * ⚠ **조립은 이 함수 하나가 한다.** 상세·목록·등록이 같은 값을 다르게 적으면 화면 사이에서
 * 같은 데이터가 두 얼굴을 갖는다.
 */
export function formatExtension(
  fileExtension: string | null | undefined,
  format: string | null | undefined,
): string {
  if (fileExtension && fileExtension.length > 0) return `*.${fileExtension}`;
  return orEmpty(format);
}

export function orEmpty(v: string | null | undefined): string {
  return v && v.length > 0 ? v : EMPTY;
}
