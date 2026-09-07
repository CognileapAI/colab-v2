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
