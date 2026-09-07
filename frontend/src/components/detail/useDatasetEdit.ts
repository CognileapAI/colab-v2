// 상세 수정의 상태 — **낙관적 갱신과 저장 왕복**만 맡는다 (WU-A3 · PRD-22).
//
// ⭑ **골격이다.** 여는 칸이 늘어도 이 파일은 안 바뀐다 — 늘어나는 것은 `editFields.ts` 의 표다.
//
// 왜 화면이 값을 손에 쥐는가 — 상세의 나머지 자리(격자 반영·승인)는 「서버에게 다시 묻는다」
// 규칙을 쓰지만, 수정은 **서버가 갱신된 상세를 200 으로 그대로 돌려준다**(`updateDataset`).
// 다시 묻는 왕복을 한 번 더 도는 대신 그 응답으로 갈아탄다 — 화면이 값을 지어내는 것이 아니라
// **서버가 준 값**으로 서는 것이라 두 규칙이 어긋나지 않는다.
import { useEffect, useState } from 'react';
import { loweringConfirmCopy } from '../common/accessState';
import {
  isValidSourceDownloadedOnShape,
  SOURCE_DOWNLOADED_ON_INVALID,
} from '../common/toastCopy';
import { applyDraft, draftError, toDraft, toPatch, type DatasetEditDraft } from './editFields';
import type { DatasetUpdateSource } from './updateSource';
import type { DatasetDetail } from './types';

/** 서버가 문장을 주지 않았을 때의 마지막 한 줄. 문구의 정본은 서버 봉투다. */
export const SAVE_FAILED = '수정한 내용을 저장하지 못했어요.';

export type DatasetEditState = {
  /** 화면이 그릴 상세 — 저장 뒤에는 서버가 돌려준 값, 저장 중에는 낙관값이다. */
  detail: DatasetDetail | null;
  editing: boolean;
  /**
   * ⭑ **⟨WU-A3R · PRD-22 각주 2⟩ 폼이 붙잡던 값이 여기로 올라왔다.**
   * `취소`/`저장` 이 **폼 밖**(다운로드가 있던 행)에 서므로, 두 자리가 같은 값을 봐야 한다.
   * 편집 중이 아니면 `null` 이다.
   */
  draft: DatasetEditDraft | null;
  saving: boolean;
  /** 보내기 전 판정(`ERR-001`)과 서버 봉투가 같은 자리에 선다. */
  error: string | null;
  /**
   * ⭑ **⟨advisor ② F1 · WU-B6⟩ 칸별 인라인 오류.** `내려받은 날` 형상 오류가 여기 선다 —
   * `error`(폼 아래 공통 자리)와 달리 **그 칸 아래**에 그려야 해서 따로 둔다.
   */
  fieldErrors: Partial<Record<keyof DatasetEditDraft, string>>;
  open(): void;
  cancel(): void;
  setField(key: keyof DatasetEditDraft, value: string): void;
  /**
   * ⭑ **⟨20차 해제 · PRD-11 · WU-B4⟩ 되묻는 문면.** `나만 보기` 로 **내리는** 변경이고
   * 지금 볼 수 있는 사람이 1명 이상일 때만 선다. `null` 이면 되묻지 않는다.
   */
  confirm: string | null;
  /** 되묻기에서 물러난다 — **편집을 닫지 않는다**(고른 값은 그대로 남는다). */
  dismissConfirm(): void;
  /** 실패하면 **낙관값을 되돌리고** 문구를 세운다 — 화면은 저장된 것처럼 남지 않는다. */
  submit(): Promise<void>;
};

export function useDatasetEdit(
  source: DatasetUpdateSource,
  base: DatasetDetail | null,
): DatasetEditState {
  const [editing, setEditing] = useState(false);
  const [patched, setPatched] = useState<DatasetDetail | null>(null);
  const [draft, setDraft] = useState<DatasetEditDraft | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<keyof DatasetEditDraft, string>>>(
    {},
  );
  const [confirm, setConfirm] = useState<string | null>(null);

  // 서버를 **다시 읽었으면** 화면이 쥐고 있던 값을 버린다 — 새로 읽은 것이 정답이다.
  // `base` 는 다시 읽을 때만 다른 객체가 되므로 저장 직후에는 돌지 않는다.
  useEffect(() => {
    setPatched(null);
    setEditing(false);
    setDraft(null);
    setError(null);
    setFieldErrors({});
    setSaving(false);
    setConfirm(null);
  }, [base]);

  const detail = patched ?? base;

  return {
    detail,
    editing,
    draft,
    saving,
    error,
    fieldErrors,
    confirm,
    dismissConfirm: () => setConfirm(null),
    open: () => {
      if (!detail) return;
      setDraft(toDraft(detail));
      setError(null);
      setFieldErrors({});
      setConfirm(null);
      setEditing(true);
    },
    cancel: () => {
      setEditing(false);
      setDraft(null);
      setError(null);
      setFieldErrors({});
      setConfirm(null);
    },
    setField: (key, value) => {
      setDraft((d) => (d ? { ...d, [key]: value } : d));
      // 고치는 순간 그 칸의 인라인 오류를 지운다 — 서버 문구처럼 값을 고쳐도 남지 않는다.
      setFieldErrors((f) => (f[key] ? { ...f, [key]: undefined } : f));
    },
    async submit() {
      if (!detail || !draft) return;
      // ⭑ ⟨advisor ② F1 · WU-B6⟩ 형상 오류는 **보내기 전에** 막는다 — 등록 `submit()` 과
      //   같은 규율. 칸이 비었으면(선택 입력) 넘어간다.
      const day = draft.sourceDownloadedOn.trim();
      if (day && !isValidSourceDownloadedOnShape(day)) {
        setFieldErrors((f) => ({ ...f, sourceDownloadedOn: SOURCE_DOWNLOADED_ON_INVALID }));
        return;
      }
      // 비울 수 없는 칸은 **보내기 전에** 막는다 — 서버와 같은 문구를 쓴다(`ERR-001`).
      const invalid = draftError(draft);
      if (invalid) {
        setError(invalid);
        return;
      }
      const patch = toPatch(detail, draft);
      // ⭑ **⟨20차 해제 · PRD-11 · WU-B4⟩ `나만 보기` 로 내리기 전에 되묻는다.**
      //
      // 그 변경은 **같은 트랜잭션에서 유효 허용 줄을 전부 만료**시킨다 — 저장 뒤에 되돌려도
      // 끊긴 사람이 자동으로 되돌아오지 않는다(다시 요청·승인을 밟아야 한다). 되돌릴 수
      // 없는 결과라 화면이 수를 보이고 한 번 묻는다.
      // ⚠ 끊길 사람이 0명이면 묻지 않는다 — 잃을 것이 없는데 되묻으면 그 확인은 반사가 된다.
      // ⚠ 판정이 여기 있는 이유 — 값(`patch.accessState`)과 수(`detail.activeGrantCount`)를
      //   둘 다 쥔 자리가 여기뿐이다. 폼은 값만, 서버는 수만 안다.
      if (patch.accessState === '잠김' && detail.activeGrantCount > 0 && confirm === null) {
        setConfirm(loweringConfirmCopy(detail.activeGrantCount));
        return;
      }
      setConfirm(null);
      const previous = patched;
      setSaving(true);
      setError(null);
      // ① 낙관 — 응답을 기다리지 않고 화면을 먼저 바꾼다
      setPatched(applyDraft(detail, draft));
      try {
        // ② 왕복 — 서버가 돌려준 상세가 이긴다. 헤더 칩·공개 범위 설명이 그 값으로 다시 선다.
        const next = await source.update(detail.datasetId, patch);
        setPatched(next);
        setEditing(false);
        setDraft(null);
      } catch (e) {
        // ③ 실패 — 되돌린다. 고친 화면을 남겨 두면 저장된 것처럼 보인다.
        setPatched(previous);
        setError(e instanceof Error ? e.message : SAVE_FAILED);
      } finally {
        setSaving(false);
      }
    },
  };
}
