// 상세 수정 폼 — **필드 표(`editFields.ts`)를 훑어 그린다.**
//
// ⭑ **골격이다.** 칸이 늘어도 이 파일은 안 바뀐다 — `TEXT_FIELDS` 에 한 줄이 늘 뿐이다
//   (WU-A4 설명 3줄·필수 배지 · WU-A6 관측 간격·기간 최소 단위 · R-B WU-B3 분류·유형…).
//
// ⛔ **`주제`(`topic`)는 이 폼에 없다** — 표시는 헤더 칩에 남고 편집 진입이 없다.
//    R-B 가 그 축을 `분류` 로 갈아치우므로, 그 사이 사람이 고친 값은 이관 대조를 흐린다.
import {
  ACCESS_LABEL,
  ACCESS_NOTE,
  ACCESS_STATES,
  type AccessState,
} from '../common/accessState';
import {
  GRANULARITIES,
  GRANULARITY_LABEL,
  INTERVAL_LABEL,
  INTERVAL_UNITS,
  PERIOD_LABEL,
  TEXT_FIELDS,
  type DatasetEditDraft,
} from './editFields';

/**
 * ⭑ **⟨WU-A3R · PRD-22 각주 2⟩ `취소`/`저장` 은 폼 밖 — 다운로드가 있던 행에 선다.**
 *
 * 그래서 값·저장 중·문구는 `useDatasetEdit` 이 쥐고, 이 폼은 **그 값을 그리기만** 한다.
 * 두 자리가 각자 상태를 들면 편집 중 화면과 버튼이 갈린다.
 */
export function DatasetEditForm(props: {
  draft: DatasetEditDraft;
  error: string | null;
  onField: (key: keyof DatasetEditDraft, value: string) => void;
}) {
  const draft = props.draft;
  const error = props.error;
  const set = props.onField;

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
        {/* ⭑ **⟨20차 해제 · PRD-11 · WU-B4⟩ 공개 범위 — 셀렉트 한 칸.**
            `나만 보기` 로 내리는 것은 **되돌릴 수 없는 결과**(허용 줄 전부 만료)를 만들어
            `useDatasetEdit` 이 저장 전에 되묻는다. 이 폼은 값을 고르기만 한다 —
            되묻는 문면은 저장 자리(`취소`/`저장` 이 서는 행)에 선다. */}
        <div className="de-row" data-testid="edit-access-state">
          <span className="de-k">공개 범위</span>
          <span className="de-v">
            <select
              aria-label="공개 범위"
              data-testid="edit-access-state-select"
              value={draft.accessState}
              onChange={(e) => set('accessState', e.target.value as AccessState)}
            >
              {ACCESS_STATES.map((v) => (
                <option key={v} value={v}>
                  {ACCESS_LABEL[v]}
                </option>
              ))}
            </select>
            <span className="de-note muted"> {ACCESS_NOTE[draft.accessState]}</span>
          </span>
        </div>
      </div>

      {error ? (
        <p className="de-err" role="alert" data-testid="detail-edit-error">
          {error}
        </p>
      ) : null}
    </div>
  );
}

/**
 * ⭑ **⟨WU-A3R⟩ 편집 중 행동 두 개.** 다운로드가 서 있던 자리에 그대로 선다 —
 * 편집 중에 다운로드는 DOM 에서 사라지고(P-12 와 같은 관례) 이 둘이 그 자리를 받는다.
 */
export function DatasetEditActions(props: {
  saving: boolean;
  onSave: () => void;
  onCancel: () => void;
  /**
   * ⭑ **⟨20차 해제 · PRD-11 · WU-B4⟩ `나만 보기` 로 내릴 때의 되묻는 문면.**
   * `null` 이면 되묻지 않는다 — 끊길 사람이 없거나 내리는 변경이 아니다.
   * 판정은 `useDatasetEdit` 이 한다(값과 `activeGrantCount` 를 둘 다 쥔 자리다).
   */
  confirm?: string | null;
  onConfirm?: () => void;
  /** 되묻는 문면에서 물러난다 — **편집을 닫지 않는다**(고른 값은 그대로 남는다). */
  onConfirmCancel?: () => void;
}) {
  if (props.confirm) {
    return (
      <div className="de-act de-confirm" data-testid="detail-edit-confirm" role="alertdialog">
        <p className="de-confirm-msg">{props.confirm}</p>
        <button
          type="button"
          className="btn btn-primary"
          data-testid="detail-edit-confirm-ok"
          disabled={props.saving}
          onClick={props.onConfirm}
        >
          확인
        </button>
        <button
          type="button"
          className="btn btn-secondary"
          data-testid="detail-edit-confirm-cancel"
          disabled={props.saving}
          onClick={props.onConfirmCancel ?? props.onCancel}
        >
          취소
        </button>
      </div>
    );
  }
  return (
    <div className="de-act" data-testid="detail-edit-actions">
      <button
        type="button"
        className="btn btn-primary"
        data-testid="detail-edit-save"
        disabled={props.saving}
        onClick={props.onSave}
      >
        저장
      </button>
      <button
        type="button"
        className="btn btn-secondary"
        data-testid="detail-edit-cancel"
        disabled={props.saving}
        onClick={props.onCancel}
      >
        취소
      </button>
    </div>
  );
}
