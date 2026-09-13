// 가공 단계 Lv **표시 규칙 한 자리** (질의 27·41 · 21차 해제 ⑵ · WU-C9).
//
// 서버는 두 값을 **나란히** 내려보낸다 — 파생값 `processingLevel`(계보에서 계산) 과
// 사람이 고른 값 `processingLevelUserSet`(`Lv0`~`Lv3` 문자열). ⛔ 서버가 파생값 칸에
// 사람 값을 덮어 쓰지 않는다(기존 열쇠의 의미 변경 = 파괴 · `R-C.md ## 구현 결정` ⑵) —
// **고르는 것은 화면이고, 그 규칙이 이 파일 하나다.**
//
// ⛔ 이 규칙을 화면마다 다시 적지 않는다 — 카탈로그·상세·계보 그래프 노드·프로젝트 표
//    네 자리가 전부 여기를 부른다. 네 곳에 적으면 언젠가 한쪽만 고쳐지고, 같은
//    데이터셋이 화면마다 다른 Lv 로 보인다(질의 27·41 이 잰 현상 그대로다).

/** 가공 단계 4값 (`d3_dataset.processing_level_user_set` CHECK · 미결-7 ⓐ). */
export const LV_VALUES = [0, 1, 2, 3] as const;

/** `Lv2` 꼴 문자열을 정수로. 안 골랐으면 `null` 이다 — **화면이 값을 지어내지 않는다.** */
export function levelOf(userSet: string | null | undefined): number | null {
  if (!userSet || !userSet.startsWith('Lv')) return null;
  const n = Number(userSet.slice(2));
  return Number.isInteger(n) ? n : null;
}

/** `Lv2` 꼴 문자열 4값 — DB `CHECK (… IN ('Lv0','Lv1','Lv2','Lv3'))` 와 같은 집합이다. */
export const LV_CODES = LV_VALUES.map((n) => `Lv${n}`) as readonly string[];

/** 파생 계산의 상한 — 목록을 넓히면 여기가 따라 넓어진다 (미결-7 ⓐ). */
const LV_CAP = LV_VALUES[LV_VALUES.length - 1] as number;

/** 확정 부모 한 건이 말하는 것 — 확인 여부와 그 부모의 표시 Lv 뿐이다. */
export interface ParentLevelBearing {
  confirmed: boolean;
  parentLevel: number | null;
}

/**
 * ⭑ **⟨R-LTH-REVIEW-1 · spec §6 ㉱⟩ 확정 부모로 만드는 파생 Lv — 규칙 한 자리.**
 *
 * 주입력 부모 중 **최대 Lv ＋ 1**, 상한 `LV_CAP`.
 *  · 확정 부모 **0건** → `0`(`Lv0`). ⭑ ⟨개정 2026-09-14 · 카드 ⑩ ⓐ 축자 「부모 0건이면 Lv0 ·
 *    그 경우 등록 화면에도 경고가 선다」⟩ ／ 종전 ~~0건이면 `null`(Lv0 으로 바꾸지 않는다)~~ —
 *    서버 `level_view` 의 `processingLevelDerived`(부모 0이면 `0`)와 같은 값이다.
 *  · 부모 Lv 를 **하나라도 모름** → `null` — 모르는 값으로 미리보기를 만들지 않는다.
 *
 * ⚠ **판정이 아니다.** 등록 전에는 서버가 계산한 값이 없어 화면이 같은 식으로 미리 보여 줄
 *   뿐이고, 저장 뒤의 정본은 응답의 `processingLevelDerived` 다.
 * ⛔ 이 식을 화면마다 다시 적지 않는다 — 등록 ③ 미리보기와 ① 기본값이 같은 함수를 부른다.
 */
export function derivedLevelFromParents(
  parents: readonly ParentLevelBearing[],
): number | null {
  const known = parents.filter((p) => p.confirmed).map((p) => p.parentLevel);
  if (known.length === 0) return 0;
  if (known.some((v) => v === null)) return null;
  return Math.min(Math.max(...(known as number[])) + 1, LV_CAP);
}

/**
 * ⭑ **⟨R-LTH-REVIEW-1 · spec §6 ㉲⟩ 불일치 안내 한 줄 — 두 값 ＋ 각 값의 근거.**
 *
 * **상세 헤더(`dh-lv-mismatch`)와 등록 ③(`lin-lv-mismatch`)이 이 한 함수를 부른다** —
 * 두 곳에 문면을 적으면 언젠가 한쪽만 고쳐지고 같은 데이터셋이 화면마다 다른 말을 한다.
 *
 * ⛔ **차단이 아니다.** 이 줄이 뜬 상태로도 등록·저장이 성공한다(미결-2 ⓐ 「경고만」).
 */
// Ted 문면 확정 대기 · R-LTH-REVIEW-1
export function levelMismatchNotice(humanLevel: number, derivedLevel: number): string {
  return `고른 가공 단계는 Lv${humanLevel}이고, 연결한 데이터로 계산하면 Lv${derivedLevel}이에요(사람이 고른 값 / 주입력 부모 중 최대 Lv＋1 · 부모가 없으면 Lv0). 그대로 두어도 등록돼요.`;
}

/** 두 값을 나란히 든 것이면 무엇이든 — 계보 노드·프로젝트 표 행·카탈로그 행·상세. */
export interface LevelBearing {
  processingLevel?: number | null | undefined;
  processingLevelUserSet?: string | null | undefined;
}

/**
 * 화면에 그릴 Lv **하나**. **사람이 고른 값이 우선**이고, 안 골랐을 때만 파생값이
 * 대신한다. 둘 다 없으면 `null` 이고 부르는 쪽이 칩 자체를 그리지 않는다
 * (원천 표기 노드가 그렇다 — 데이터셋이 아니라 Lv 가 없다).
 *
 * ⚠ **불일치를 여기서 판정하지 않는다** — 어긋남은 경고이지 차단이 아니고
 *   (`processingLevelMismatch` · 미결-2 ⓐ), 그 문면은 상세 헤더가 쥔다.
 */
export function displayLevel(v: LevelBearing | null | undefined): number | null {
  if (!v) return null;
  const human = levelOf(v.processingLevelUserSet);
  if (human !== null) return human;
  return v.processingLevel ?? null;
}
