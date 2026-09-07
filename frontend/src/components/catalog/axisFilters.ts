// 분류 3축 필터 바가 읽는 값 — PRD-05 · WU-B7.
//
// 지키는 것
//  - **값 사전은 한 곳이다** (`components/upload/axisDict.ts`). 등록 화면과 필터 바가 같은
//    사전을 읽는다 — 두 벌을 두면 한쪽만 넓어지는 날이 오고 그날 필터가 조용히 0건을 낸다.
//  - **첫 항목 글자는 rev1 축자**다: `분류 전체` · `유형 전체` · `가공 단계 전체`(PRD-05 축자).
//  - **파수꼴 `미지정` 이 축마다 하나씩** 선다 — 값이 NULL 인 행을 사람이 찾아낼 유일한
//    경로다(PRD-05 축자). 정본은 서버 상수(`catalog.py` `UNSPECIFIED`)이고 이것은 그 사본이다.
import { CATEGORIES, DATA_TYPES, PROCESSING_LEVELS } from '../upload/axisDict';
import type { AxisValue } from '../upload/axisDict';
import type { AxisName } from './types';

/** 값이 NULL 인 행을 고르는 파수꼴. 서버 `catalog.UNSPECIFIED` 와 **같은 글자**다. */
export const UNSPECIFIED = '미지정';

/** 축의 첫 항목 — 「조건 없음」이다. 글자를 바꾸지 않는다 (rev1 문면 · PRD-05 축자). */
export const AXIS_ALL_LABEL: Record<AxisName, string> = {
  분류: '분류 전체',
  유형: '유형 전체',
  '가공 단계': '가공 단계 전체',
};

const DICT: Record<AxisName, readonly AxisValue[]> = {
  분류: CATEGORIES,
  유형: DATA_TYPES,
  '가공 단계': PROCESSING_LEVELS,
};

/** 축 하나의 셀렉트 항목 — 고정 어휘 ＋ 파수꼴. **0건 값을 지우지 않는다** (`§5`). */
export function axisOptions(axis: AxisName): { value: string; label: string }[] {
  return [
    ...DICT[axis].map((v) => ({ value: v.value, label: v.label })),
    { value: UNSPECIFIED, label: UNSPECIFIED },
  ];
}

/**
 * 값이 없는 칸의 표기. **「모른다」를 빈 칸으로 두지 않는다** — 빈 칸은 「값이 없다」와
 * 갈리지 않고, 그 행이 재선택 대상이라는 사실이 화면에서 사라진다(PRD-05·06).
 */
export const UNSPECIFIED_CELL = UNSPECIFIED;

/**
 * 상세 3행의 수정 진입 유도 한 줄.
 * ⚠ **축자 문면이 라운드 파일·PRD 에 없다**(`[미상]`) — 형제 자리(`설명이 아직 없어요 —
 * 수정에서 채워 주세요.`)의 형식을 그대로 따랐다. 정본 문면이 오면 이 한 줄만 바꾼다.
 * ⛔ 재선택을 **강제하지 않는다** — 안내 한 줄이다(미결-3 ⓐ).
 */
export const AXIS_UNSET_NUDGE = '아직 안 골랐어요 — 수정에서 골라 주세요.';
