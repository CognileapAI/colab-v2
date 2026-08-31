// 승인 처리(WU-P6)가 부르는 네 동작. **화면은 어느 쪽이 붙었는지 모른다** —
// 실서버와 시험 대역이 같은 얼굴을 쓴다 (`components/detail/types.ts` 의 `DetailSource` 와 같은 무늬).
//
// **판정은 하나도 여기 없다.** 누가 무엇을 할 수 있는지는 서버가 `DatasetDetail.actions` 로
// 내려주고 화면은 그것만 본다 (P-7). 이 얼굴은 「누르면 무엇을 부르나」만 정한다.
export interface ApprovalSource {
  /** 접근 요청 보내기. 사유는 0~300자 **선택**이라 `null` 이 정상값이다 (`Policy_승인_처리 §5`). */
  requestAccess(datasetId: string, reason: string | null): Promise<void>;
  /** Verified 승인 요청 — 올린 사람·소유자가 상세 헤더에서 직접 누른다 (§1.2). */
  requestVerification(datasetId: string): Promise<void>;
  /** Verified 승인 — 교수만 (§1.2 · P-22). */
  approveVerification(datasetId: string): Promise<void>;
  /** Verified 승인 취소 — 교수만. 취소 사유는 0~120자 **선택** (§5). */
  cancelVerification(datasetId: string, reason: string | null): Promise<void>;
}
