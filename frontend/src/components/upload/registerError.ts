// 등록 오류의 **단계 범위** (X-9 · 진단 `dev-package/reports/R-D/upload-step3-overlap-20260908.md` §2-(c)).
//
// 종전 = `registerError` 가 문자열 하나였고 렌더 자리(`RegisterArea.tsx` 의 `reg-error`)가
// 단계 분기 **바깥**이라, ② 에서 난 거절 문면이 ③ 에서도 그대로 서 있었다. 사람은 ③ 을 보며
// ② 의 칸을 고치라는 말을 읽는다 — 고칠 칸이 화면에 없다.
//
// 지금 = 문면과 **그것을 낳은 단계**를 함께 들고, 그 단계에서만 낸다.
//  - `step: null` = 단계와 무관한 파일·접수 오류(업로드 소실 · 접수 끊김 · 격자 후주입).
//    이것은 어느 단계에서도 보이고 단계 이동으로 지워지지 않는다 — 고칠 자리가 단계가 아니다.
import type { Step } from './RegisterArea';

/** 문면 하나와 그것이 속한 단계. `step: null` 이면 단계에 매이지 않는다. */
export type RegisterErrorAt = { step: Step | null; message: string } | null;

/** 지금 서 있는 단계에서 낼 문면 — 남의 단계 것이면 내지 않는다. */
export function messageForStep(err: RegisterErrorAt, step: Step): string | null {
  if (!err) return null;
  return err.step === null || err.step === step ? err.message : null;
}

/** 단계를 옮길 때 남길 것 — 자기 단계로 옮겨 가는 문면과 단계 무관 오류만 남는다. */
export function clearedOnStepChange(err: RegisterErrorAt, next: Step): RegisterErrorAt {
  if (!err) return null;
  return err.step === null || err.step === next ? err : null;
}
