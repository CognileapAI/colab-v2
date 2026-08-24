// ③ 계보 확정이 바깥 세계와 만나는 **얼굴 둘**.
//
// 타입은 전부 생성물에서 온다 — 여기서 계약 스키마를 다시 선언하지 않는다
// (`CLAUDE.md §3-6·§3-7`).
//
// **이 화면은 아무것도 저장하지 않는다.** 확인·수정·거절은 전부 클라이언트 상태이고,
// 사람이 확인한 것만 `createDataset` 의 `lineageParents` 로 실린다
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
export type UploadLineageParent = Schemas['UploadLineageParent'];

/** 부모 역할 2값 (`common.json#ParentRole`). 화면이 목록을 지어내지 않는다. */
export const PARENT_ROLES: ParentRole[] = ['주입력', '보조입력'];

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
   */
  candidates(): Promise<DatasetRow[]>;
}
