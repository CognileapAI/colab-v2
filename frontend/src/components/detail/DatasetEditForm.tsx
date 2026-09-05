// 상세 수정 폼 — **필드 표(`editFields.ts`)를 훑어 그린다.**
//
// ⭑ **골격이다.** 칸이 늘어도 이 파일은 안 바뀐다 — `TEXT_FIELDS` 에 한 줄이 늘 뿐이다
//   (WU-A4 설명 3줄·필수 배지 · WU-A6 관측 간격·기간 최소 단위 · R-B WU-B3 분류·유형…).
//
// ⛔ **`주제`(`topic`)는 이 폼에 없다** — 표시는 헤더 칩에 남고 편집 진입이 없다.
//    R-B 가 그 축을 `분류` 로 갈아치우므로, 그 사이 사람이 고친 값은 이관 대조를 흐린다.
import { useState } from 'react';
import {
  GRANULARITIES,
  GRANULARITY_LABEL,
  INTERVAL_LABEL,
  INTERVAL_UNITS,
  PERIOD_LABEL,
  TEXT_FIELDS,
  draftError,
  toDraft,
  type DatasetEditDraft,
} from './editFields';
import type { DatasetDetail } from './types';

const SAVE_FAILED = '수정한 내용을 저장하지 못했어요.';

export function DatasetEditForm(props: {
  detail: DatasetDetail;
  onSave: (draft: DatasetEditDraft) => Promise<void>;
  onCancel: () => void;
}) {
  // **한 번만** 뜬다 — 저장 중 낙관값이 `detail` 을 바꿔도 사람이 적던 값을 덮지 않는다.
  const [draft, setDraft] = useState<DatasetEditDraft>(() => toDraft(props.detail));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function set<K extends keyof DatasetEditDraft>(key: K, value: string) {
    setDraft((d) => ({ ...d, [key]: value }));
  }

  async function submit() {
    // 비울 수 없는 칸은 **보내기 전에** 막는다 — 서버와 같은 문구를 쓴다(`ERR-001`).
    const invalid = draftError(draft);
    if (invalid) {
      setError(invalid);
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await props.onSave(draft);
    } catch (e) {
      setError(e instanceof Error ? e.message : SAVE_FAILED);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="dt-edit" data-testid="detail-edit-form">
      <div className="de-grid">
        {TEXT_FIELDS.map((f) => (
          <label className="de-row" key={f.key}>
            <span className="de-k">
              {f.label}
              {/* ⭑ ⟨19차 · PRD-15⟩ 비울 수 없는 칸은 라벨이 그렇게 말한다. */}
              {f.required ? <span className="de-req">필수</span> : null}
            </span>
            {f.multiline ? (
              <textarea
                className="de-v"
                data-testid={`edit-${f.key}`}
                value={draft[f.key]}
                rows={3}
                onChange={(e) => set(f.key, e.target.value)}
              />
            ) : (
              <input
                className="de-v"
                type="text"
                data-testid={`edit-${f.key}`}
                value={draft[f.key]}
                onChange={(e) => set(f.key, e.target.value)}
              />
            )}
          </label>
        ))}
        {/* 기간은 **두 칸이 한 값**이다 (`DataPeriod`). 끝을 비우면 무기한이다. */}
        <div className="de-row" data-testid="edit-period">
          <span className="de-k">{PERIOD_LABEL}</span>
          <span className="de-v de-period">
            {/* ⭑ ⟨19차 해제 · PRD-18⟩ 최소 단위는 **기간 입력 앞**에 선다.
                `''`(미지정)이 기본이고 그때 표기는 종전 그대로다 — 재선택을 강제하지 않는다. */}
            <select
              aria-label={GRANULARITY_LABEL}
              data-testid="edit-period-granularity"
              value={draft.periodGranularity}
              onChange={(e) => set('periodGranularity', e.target.value)}
            >
              <option value="">최소 단위 미지정</option>
              {GRANULARITIES.map((g) => (
                <option key={g} value={g}>
                  {g}
                </option>
              ))}
            </select>
            <input
              type="date"
              aria-label="기간 시작"
              data-testid="edit-period-start"
              value={draft.periodStart}
              onChange={(e) => set('periodStart', e.target.value)}
            />
            <span className="de-tilde">~</span>
            <input
              type="date"
              aria-label="기간 끝"
              data-testid="edit-period-end"
              value={draft.periodEnd}
              onChange={(e) => set('periodEnd', e.target.value)}
            />
          </span>
        </div>
        {/* ⭑ ⟨19차 해제 · PRD-17⟩ 관측 간격도 **두 칸이 한 값**이다 — 기간과 같은 모양으로 선다.
            ⛔ 화면이 반쪽을 막지 않는다 — 400 의 문구는 서버 봉투 하나가 갖는다. */}
        <div className="de-row" data-testid="edit-interval">
          <span className="de-k">{INTERVAL_LABEL}</span>
          <span className="de-v de-period">
            <input
              type="text"
              inputMode="numeric"
              aria-label="관측 간격 수치"
              data-testid="edit-interval-value"
              value={draft.intervalValue}
              onChange={(e) => set('intervalValue', e.target.value)}
            />
            <select
              aria-label="관측 간격 단위"
              data-testid="edit-interval-unit"
              value={draft.intervalUnit}
              onChange={(e) => set('intervalUnit', e.target.value)}
            >
              <option value="">단위</option>
              {INTERVAL_UNITS.map((u) => (
                <option key={u} value={u}>
                  {u}
                </option>
              ))}
            </select>
          </span>
        </div>
      </div>

      {error ? (
        <p className="de-err" role="alert" data-testid="detail-edit-error">
          {error}
        </p>
      ) : null}

      <div className="de-act">
        <button
          type="button"
          className="btn btn-primary"
          data-testid="detail-edit-save"
          disabled={busy}
          onClick={submit}
        >
          저장
        </button>
        <button
          type="button"
          className="btn btn-secondary"
          data-testid="detail-edit-cancel"
          disabled={busy}
          onClick={props.onCancel}
        >
          취소
        </button>
      </div>
    </div>
  );
}
