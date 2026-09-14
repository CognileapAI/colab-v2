// ③ 계보 확정이 바깥 세계와 만나는 **얼굴 둘**.
//
// 타입은 전부 생성물에서 온다 — 여기서 계약 스키마를 다시 선언하지 않는다
// (`CLAUDE.md §3-6·§3-7`).
//
// **이 화면은 아무것도 저장하지 않는다.** 연결·지우기는 전부 클라이언트 상태이고,
// 사람이 고른 것만 `createDataset` 의 `lineageParents` 로 실린다
// (`CLAUDE.md §3-2` — D10 → D4 쓰기 경로가 없다 · `fe-core.yaml UploadLineageParent`).
import type { Schemas } from '../../api/client';

export type LineageSuggestionResponse = Schemas['LineageSuggestionResponse'];
export type LineageSuggestion = Schemas['LineageSuggestion'];
export type ParentCandidateSuggestion = Schemas['ParentCandidateSuggestion'];
export type ProcessingMethodSuggestion = Schemas['ProcessingMethodSuggestion'];
export type ParentRole = Schemas['ParentRole'];
export type LineageOrigin = Schemas['LineageOrigin'];
export type AiConfidence = Schemas['AiConfidence'];
export type DatasetRow = Schemas['DatasetRow'];
export type LineageCandidate = Schemas['LineageCandidate'];
export type LineageCandidatePage = Schemas['LineageCandidatePage'];
export type ParentCandidateRow = LineageCandidate | DatasetRow;
export type LineageCandidateQuery = {
  q?: string;
  category?: string;
  topic?: string;
  processingLevel?: number;
  periodStart?: string;
  periodEnd?: string;
  excludeDatasetId?: string;
  limit?: number;
  cursor?: string;
};
export type UploadLineageParent = Schemas['UploadLineageParent'];

/**
 * 부모 관계 한 건 — 화면 상태다. 저장되지 않았고, 확인해야만 등록 요청에 실린다.
 *
 * ⭑ **⟨WU-B5 · PRD-09⟩ 이 상태는 `LineageStep` 이 아니라 업로드 모달이 쥔다.**
 * 등록 카드가 단계마다 **언마운트**되므로(`RegisterArea` 의 `{step === 3 && …}`) ③ 안에
 * 두면 ① 로 갔다 오는 순간 연결이 통째로 사라진다 — PRD-09 축자 「사람이 한 연결을
 * 시스템이 되돌리지 않는다」가 그 자리에서 깨진다. 그래서 한 단계 위로 올렸다.
 */
export interface ParentCard {
  key: string;
  parentDatasetId: string;
  parentDatasetName: string;
  /** 제안에서 온 확신도. **사람이 수정하면 `null` 이 된다** — AI 행동이 아니게 되므로. */
  confidence: AiConfidence | null;
  rationale: string | null;
  origin: LineageOrigin;
  confirmed: boolean;
  /** 사람이 직접 적은 가공 방식 → 요청의 `method`. */
  method: string;
  /** 제안을 확인·수정한 가공 방식 → 요청의 `confirmedMethodText`. 둘 다 실으면 400 이다. */
  confirmedMethodText: string | null;
  /**
   * ⭑ **⟨개정 2026-09-14 · 기획서 rev2 목업 `.li-act`⟩ 쓰는 자리가 0건이다.**
   * ／ 종전 ~~`수정` 을 눌러 대상을 다시 고르는 중인가~~ — 카드의 버튼이 `지우기` 하나가
   * 되면서 `수정` 이 사라졌다. 대상을 바꾸는 길은 **지우고 다시 고르는 것**이다.
   * ⛔ 열쇠 자체는 남긴다(선택) — 기존 시험 fixture 가 이 이름으로 카드를 만든다.
   */
  picking?: boolean;
  /**
   * ⭑ **⟨신설 2026-09-14 · 목업 `.li-sub`⟩ 후보 줄이 들고 온 분류·기간.**
   * 연결 카드가 「무엇을 이었는지」를 되읽는 값이고, 모르면 그 자리를 세우지 않는다.
   */
  parentCategory?: string | null;
  parentPeriod?: { start: string; end: string | null } | null;
  /**
   * ⭑ **⟨WU-B5 · PRD-09⟩ 부모의 표시 Lv.** 사후 충돌(연결 뒤 자기 Lv 내림)을 재는 값이다.
   * `null` 이면 **모른다**는 뜻이고 그때는 충돌로 세지 않는다.
   * ⭑ **⟨WU-C9 · 21차 해제 ⑸ · 질의 23⟩ 제안도 이 값을 실어 온다**
   *   (`ParentCandidateSuggestion.parentProcessingLevel` · optional). 실려 오면 화면이
   *   서버 400 전에 충돌을 알리고, 없으면 후보 목록에서 대조될 때까지 비어 있다.
   *   **없는 값을 0 으로 채우지 않는다** — 그러면 모든 제안이 Lv0 으로 읽힌다.
   */
  parentLevel: number | null;
}

/**
 * ⭑ **⟨신설 2026-09-14 · 레인 A6 · 사용자 결정⟩ 계약 기본값 하나.**
 * ／ 종전 ~~`PARENT_ROLES` 2값 배열 — 카드의 셀렉트가 목록으로 그렸다~~ —
 * 목업 `.li-f` 에 그 셀렉트가 없다. **업로드 화면은 부모 역할을 묻지 않고** 이 값을
 * 고정해 싣는다(`common.json#ParentRole` 의 `default` 축자).
 * ⛔ **enum 2값 자체는 계약에 그대로 있다** — 고르는 자리가 **상세의 계보 수정**
 * (`LineageFixModal`)로만 남은 것이고, 계약·DB 는 무변이다.
 */
export const DEFAULT_PARENT_ROLE: ParentRole = '주입력';

export interface LineageSource {
  /**
   * `listUploadLineageSuggestions` — AI 제안 중계. **0건도 200 으로 온다.**
   * 확정 오퍼레이션이 아니다 — 여기서 저장되는 것은 없다.
   */
  suggestions(
    uploadId: string,
    q: { datasetNameDraft?: string; subject?: string },
  ): Promise<LineageSuggestionResponse>;
  /**
   * `직접 추가` 가 고를 후보 — 연구실 카탈로그(`listDatasets`).
   * **AI 와 무관한 경로다.** 제안이 0건이어도 사람은 여기로 계보를 세운다.
   *
   * ⭑ **⟨WU-B5 · PRD-08⟩ `level` 은 사람이 셀렉트에서 고른 조건**이고, 없으면 전부다.
   * ⛔ **자기 Lv 로 자동으로 걸지 않는다** — 초과 후보도 내려와야 화면이 「보이되 못 고름」
   *   을 그릴 수 있다(축자 「숨기지는 않는다. 없는 것과 못 고르는 것은 다르다」).
   */
  candidates(
    query?: LineageCandidateQuery | number | null,
  ): Promise<LineageCandidatePage | ParentCandidateRow[]>;
}

// ⭑ **⟨WU-C9 · 질의 27·41⟩ Lv 표시 규칙의 집은 `common/processingLevel.ts` 하나다.**
//    여기서 다시 선언하지 않고 **그대로 다시 내보낸다** — 종전 수입 경로
//    (`import { levelOf } from '../lineage/types'`)를 끊으면 네 자리가 각자 고쳐진다.
export {
  LV_VALUES,
  levelOf,
  displayLevel,
  // ⭑ ⟨R-LTH-REVIEW-1 · spec §6 ㉱·㉲⟩ 파생 미리보기 식과 불일치 문면도 같은 집이다.
  derivedLevelFromParents,
  levelMismatchNotice,
} from '../common/processingLevel';
export type { LevelBearing, ParentLevelBearing } from '../common/processingLevel';
