// 상세 수정의 **필드 표** — 이 화면이 여는 칸이 무엇인지가 여기 한 곳에 있다 (WU-A3 · PRD-22).
//
// ⭑ **골격이다.** 뒤에 오는 WU 는 화면을 다시 짜지 않고 **이 표에 줄을 더한다** —
//   `R-A-2` WU-A4(설명 3줄·필수 배지) · `R-A-1` WU-A6(관측 간격·기간 최소 단위) ·
//   R-B WU-B3(분류·유형·공개 범위…). 줄을 더할 자리는 셋뿐이다:
//     ⑴ `TEXT_FIELDS` 에 한 줄 ⑵ `DatasetEditDraft` 에 열쇠 하나 ⑶ 값이 `basicInfo` 쪽이면
//        `applyDraft` 의 그 갈래에 한 줄. 폼(`DatasetEditForm`)은 표를 훑어 그리므로 안 고친다.
//
// ⛔ **지금 여는 칸은 `DatasetUpdate` 가 이미 받는 것뿐이다** — 이름 · 설명 · 원천 표기 ·
//    좌표계 · 기간 (`contracts/seams/fe-core.yaml:2794`). 계약에 없는 칸을 미리 그리면
//    같은 화면을 두 번 만들게 된다.
// ⛔ **`topic` 은 이 표에 없다.** R-B PRD-01 이 그 축을 `category` 로 갈아치우므로 곧 지울
//    칸을 만들 이유가 없고, 그 사이 사람이 고친 값이 이관 대조를 흐린다. 표시는 남고 읽기 전용이다.
import type { components } from '../../generated/fe-core';
import type { DatasetDetail } from './types';

export type DatasetUpdate = components['schemas']['DatasetUpdate'];
export type DataPeriod = components['schemas']['DataPeriod'];

/** 폼이 붙잡는 값. **전부 문자열이다** — 빈 문자열이 「비웠다」이고 계약의 `null` 로 번역된다. */
export type DatasetEditDraft = {
  name: string;
  summary: string;
  sourceLabel: string;
  crs: string;
  /** 기간은 두 칸이 한 값이다 (`DataPeriod`). 날짜 칸이라 `YYYY-MM-DD` 다. */
  periodStart: string;
  periodEnd: string;
};

/** 한 줄로 서는 자유 입력 칸. 라벨은 `Policy_데이터셋_상세 §5` 기본 정보 칸 이름 그대로다. */
export type TextFieldSpec = {
  key: 'name' | 'summary' | 'sourceLabel' | 'crs';
  label: string;
  /** 여러 줄 입력인가. 설명은 긴 글이라 `textarea` 다. */
  multiline?: boolean;
  /** 비울 수 없는 칸인가. 지금은 이름 하나다. */
  required?: boolean;
};

export const TEXT_FIELDS: readonly TextFieldSpec[] = [
  { key: 'name', label: '이름', required: true },
  { key: 'summary', label: '설명', multiline: true },
  { key: 'sourceLabel', label: '원천 표기' },
  { key: 'crs', label: '좌표계' },
];

/** 기간 칸의 라벨 — 두 칸이 한 값이라 표에서 따로 선다. */
export const PERIOD_LABEL = '기간';

/** `null` 은 **빈 칸**으로 연다 — 없는 값을 지어내지 않는다 (기존 행이 이 창구로 채워진다). */
function orBlank(v: string | null | undefined): string {
  return v ?? '';
}

/** 시각값 → 날짜 칸. 저장은 시각값 그대로다 (미결-18 — 화면이 조립한다). */
function toDateInput(v: string | null | undefined): string {
  return v ? v.slice(0, 10) : '';
}

/** 날짜 칸 → 시각값. 자정 UTC 로 세운다 — 화면이 고른 값이고 계약은 `date-time` 이다. */
function toTimestamp(v: string): string {
  return `${v}T00:00:00Z`;
}

export function toDraft(detail: DatasetDetail): DatasetEditDraft {
  const b = detail.basicInfo;
  return {
    name: detail.name,
    summary: orBlank(detail.summary),
    sourceLabel: orBlank(b?.sourceLabel),
    crs: orBlank(b?.crs),
    periodStart: toDateInput(b?.period?.start),
    periodEnd: toDateInput(b?.period?.end),
  };
}

/** 이름은 비울 수 없다 — 서버 `ERR-001` 과 **같은 문구**를 쓴다 (두 곳이 갈라지지 않게). */
export const EMPTY_NAME_MESSAGE = '데이터셋 이름을 적어 주세요.';

export function draftError(draft: DatasetEditDraft): string | null {
  if (draft.name.trim().length === 0) return EMPTY_NAME_MESSAGE;
  return null;
}

function periodOf(draft: DatasetEditDraft): DataPeriod | null {
  if (!draft.periodStart) return null;
  return {
    start: toTimestamp(draft.periodStart),
    end: draft.periodEnd ? toTimestamp(draft.periodEnd) : null,
  };
}

function samePeriod(a: DataPeriod | null, b: DataPeriod | null): boolean {
  if (!a || !b) return !a && !b;
  return a.start === b.start && (a.end ?? null) === (b.end ?? null);
}

/**
 * **바뀐 칸만** 담는다 — 계약 축자 「보내지 않은 열쇠는 안 건드린다. `null` 을 명시적으로
 * 보내는 것은 **비우라는 뜻**이고, 열쇠를 생략한 것은 **그대로 두라는 뜻**이다. 둘이 다르다」.
 * 그래서 빈 칸은 **생략이 아니라 `null`** 로 나간다.
 */
export function toPatch(detail: DatasetDetail, draft: DatasetEditDraft): DatasetUpdate {
  const before = toDraft(detail);
  const patch: DatasetUpdate = {};
  if (draft.name !== before.name) patch.name = draft.name.trim();
  for (const f of TEXT_FIELDS) {
    if (f.key === 'name') continue;
    if (draft[f.key] === before[f.key]) continue;
    const next = draft[f.key].trim();
    patch[f.key] = next.length > 0 ? next : null;
  }
  const nextPeriod = periodOf(draft);
  if (!samePeriod(nextPeriod, periodOf(before))) patch.period = nextPeriod;
  return patch;
}

/**
 * **낙관적 갱신** — 응답을 기다리지 않고 화면을 먼저 바꾼다. 서버가 200 으로 돌려준 상세가
 * 오면 그것이 이기고(왕복), 실패하면 이 값을 버리고 종전으로 되돌린다.
 * ⚠ 파생값(`processingLevel`·`lastModifiedAt`·계보)은 **건드리지 않는다** — 사람이 적은 칸만이다.
 */
export function applyDraft(detail: DatasetDetail, draft: DatasetEditDraft): DatasetDetail {
  const blank = (v: string) => (v.trim().length > 0 ? v.trim() : null);
  return {
    ...detail,
    name: draft.name.trim(),
    summary: blank(draft.summary),
    basicInfo: detail.basicInfo
      ? {
          ...detail.basicInfo,
          sourceLabel: blank(draft.sourceLabel),
          crs: blank(draft.crs),
          period: periodOf(draft),
        }
      : null,
  };
}
