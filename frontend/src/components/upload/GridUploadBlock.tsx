// 「미리보기를 보려면 격자를 올리세요」 — `S1-PLAN-REFOUND §E` 의 화면.
//
// **새 화면을 만들지 않는다** — 이 블록은 `PreviewPanel` **안**에서 열린다(`§E.1-㈎`).
// 상태와 문구는 `gridFlow.ts` 가 소유하고, 이 파일은 그것을 그리기만 한다.
//
// ⚠ **격자는 매번 직접 올린다**(`§E.5`) — 재사용·추천·연구실 기본 격자가 여기 없는 것은
// 빠진 것이 아니라 **뺀 것**이다(편의 기능 후일 묶음 `§J`).
import type { GridStateResult } from './gridFlow';
import { fillBody, GRID_COPY } from './gridFlow';

export interface GridActions {
  onPickGrid(files: File[]): void;
  onSkipGrid(): void;
  /** 전송 취소. 없으면 취소 버튼을 세우지 않는다 — 못 하는 것을 있는 척하지 않는다. */
  onCancel?: () => void;
  /** 사람이 지도를 보고 「맞습니다」를 누른다 (사다리 6단 — 마지막 확인은 눈이다). */
  onAccept?: () => void;
  /**
   * 축 뒤집기. ⚠ **등록 전에는 부를 계약 경로가 없다** — `flipAxes` 는
   * `replaceDatasetGridFile`(등록된 데이터셋) 에만 있다. 그래서 이 자리는
   * **핸들러가 있을 때만** 버튼이 선다. 없는 길을 버튼으로 만들지 않는다.
   */
  onFlipAxes?: () => void;
}

function Progress(props: { transfer: { sentBytes: number; totalBytes: number } | null }) {
  const t = props.transfer;
  if (!t || t.totalBytes <= 0) {
    // **퍼센트를 지어내지 않는다** — 셀 수 없으면 세지 않는다 (`§D.7`)
    return <span className="spin" aria-hidden="true" />;
  }
  const pct = Math.min(100, Math.round((t.sentBytes / t.totalBytes) * 100));
  return (
    <progress className="gridbar" data-testid="up-grid-progress" max={100} value={pct}>
      {pct}%
    </progress>
  );
}

export function GridUploadBlock(props: {
  state: GridStateResult;
  actions: GridActions;
  transfer: { sentBytes: number; totalBytes: number } | null;
}) {
  const { state, actions } = props;
  const copy = GRID_COPY[state.name];
  const body = fillBody(state.name, state.shapes);
  const busy = copy.progress !== undefined;
  const rejected =
    state.name === '형상 불일치' || state.name === '축 판별 실패' || state.name === '짝 불일치';

  return (
    <div
      className="gridblock"
      data-testid="up-grid-block"
      data-grid-state={state.name}
      aria-live={busy ? 'polite' : 'off'}
      {...(busy ? { 'aria-busy': 'true' } : {})}
    >
      <p className="gb-t">{copy.title}</p>
      {body ? <p className="gb-b">{body}</p> : null}
      {/* 문장을 못 가른 거절은 **서버가 준 문장을 그대로** 보여 준다 — 지어내지 않는다 */}
      {!body && state.serverDetail ? (
        <p className="gb-b" data-testid="up-grid-detail">
          {state.serverDetail}
        </p>
      ) : null}

      {copy.progress === '퍼센트' ? <Progress transfer={props.transfer ?? null} /> : null}
      {copy.progress === '불확정' ? <span className="spin" aria-hidden="true" /> : null}

      <div className="gb-a">
        {/* 격자를 청하는 자리 — 좌표 없음 · 거절 뒤 다시 올리기 */}
        {(state.name === '좌표 없음' || rejected || state.name === '경계 위생 실패') && (
          <>
            <label className="btn btn-strong btn-sm" data-testid="up-grid-pick">
              {rejected || state.name === '경계 위생 실패' ? '다른 파일 올리기' : '격자 파일 올리기'}
              <input
                type="file"
                multiple
                className="hidden-input"
                data-testid="up-grid-input"
                onChange={(e) => actions.onPickGrid(Array.from(e.target.files ?? []))}
              />
            </label>
            {state.name === '좌표 없음' && (
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                data-testid="up-grid-skip"
                onClick={actions.onSkipGrid}
              >
                건너뛰기 — 나중에 올릴게요
              </button>
            )}
          </>
        )}

        {state.name === '격자 전송 중' && actions.onCancel && (
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            data-testid="up-grid-cancel"
            onClick={actions.onCancel}
          >
            취소
          </button>
        )}

        {state.name === '위치 확인' && (
          <>
            <button
              type="button"
              className="btn btn-strong btn-sm"
              data-testid="up-grid-accept"
              onClick={actions.onAccept}
            >
              맞습니다
            </button>
            {actions.onFlipAxes && (
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                data-testid="up-grid-flip"
                onClick={actions.onFlipAxes}
              >
                위도·경도 뒤집기
              </button>
            )}
          </>
        )}
      </div>
    </div>
  );
}
