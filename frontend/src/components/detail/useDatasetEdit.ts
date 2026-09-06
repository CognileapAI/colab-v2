// 상세 수정의 상태 — **낙관적 갱신과 저장 왕복**만 맡는다 (WU-A3 · PRD-22).
//
// ⭑ **골격이다.** 여는 칸이 늘어도 이 파일은 안 바뀐다 — 늘어나는 것은 `editFields.ts` 의 표다.
//
// 왜 화면이 값을 손에 쥐는가 — 상세의 나머지 자리(격자 반영·승인)는 「서버에게 다시 묻는다」
// 규칙을 쓰지만, 수정은 **서버가 갱신된 상세를 200 으로 그대로 돌려준다**(`updateDataset`).
// 다시 묻는 왕복을 한 번 더 도는 대신 그 응답으로 갈아탄다 — 화면이 값을 지어내는 것이 아니라
// **서버가 준 값**으로 서는 것이라 두 규칙이 어긋나지 않는다.
import { useEffect, useState } from 'react';
import { applyDraft, toPatch, type DatasetEditDraft } from './editFields';
import type { DatasetUpdateSource } from './updateSource';
import type { DatasetDetail } from './types';

export type DatasetEditState = {
  /** 화면이 그릴 상세 — 저장 뒤에는 서버가 돌려준 값, 저장 중에는 낙관값이다. */
  detail: DatasetDetail | null;
  editing: boolean;
  open(): void;
  cancel(): void;
  /** 실패하면 **낙관값을 되돌리고 다시 던진다** — 문구는 폼이 자기 자리에서 보인다. */
  save(draft: DatasetEditDraft): Promise<void>;
};

export function useDatasetEdit(
  source: DatasetUpdateSource,
  base: DatasetDetail | null,
): DatasetEditState {
  const [editing, setEditing] = useState(false);
  const [patched, setPatched] = useState<DatasetDetail | null>(null);

  // 서버를 **다시 읽었으면** 화면이 쥐고 있던 값을 버린다 — 새로 읽은 것이 정답이다.
  // `base` 는 다시 읽을 때만 다른 객체가 되므로 저장 직후에는 돌지 않는다.
  useEffect(() => {
    setPatched(null);
    setEditing(false);
  }, [base]);

  const detail = patched ?? base;

  return {
    detail,
    editing,
    open: () => setEditing(true),
    cancel: () => setEditing(false),
    async save(draft) {
      if (!detail) return;
      const patch = toPatch(detail, draft);
      const previous = patched;
      // ① 낙관 — 응답을 기다리지 않고 화면을 먼저 바꾼다
      setPatched(applyDraft(detail, draft));
      try {
        // ② 왕복 — 서버가 돌려준 상세가 이긴다
        const next = await source.update(detail.datasetId, patch);
        setPatched(next);
        setEditing(false);
      } catch (e) {
        // ③ 실패 — 되돌린다. 고친 화면을 남겨 두면 저장된 것처럼 보인다.
        setPatched(previous);
        throw e;
      }
    },
  };
}
