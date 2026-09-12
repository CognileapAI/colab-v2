// 상세 계보 **수정 · 추가** 모달 (WU-B10 · PRD-31 · rev1 `H-46`).
//
// 지키는 것
//  - **등록 ③ 과 같은 찾기·연결 UI 를 쓴다** — `ParentPicker` 한 벌이고, 초과 후보의 사유도
//    같은 `parentOverReason` 이다. 사본을 뜨지 않는다(PRD-07·08·09 가 두 벌이 되지 않게).
//  - **`가공 방식` 은 새 칸이 아니다** — 이미 있는 `d4_lineage_edge.method` 를 여는 것이고,
//    등록 화면이 쓰는 열쇠(`ParentCard.method`)와 같은 이름으로 나간다.
//  - **새 op 을 만들지 않는다** — `addLineageParent` 하나를 부르고, 그 응답 그래프가 상세의
//    계보 구역을 그대로 갈아 끼운다(재조회 왕복 없이 · 화면이 값을 손으로 조립하지 않는다).
//  - **닫기는 한 곳이다**(A9R 규율) — Esc · 배경 · × 가 전부 `requestClose` 로 모인다.
//    열려 있는 동안 `data-esc-layer="계보 수정"` 표식을 **스스로 단다** — 업로드 모달과
//    같은 화면에 서게 되어도 그쪽 Esc 가 이 층을 먹지 않는다.
//  - **서버 400 이 최종 방어선**이다. 이 화면은 그 앞에서 초과 후보를 못 고르게 할 뿐이고,
//    거절 문구는 서버 봉투를 그대로 올린다 — 판정을 흉내 내지 않는다.
import { useCallback, useEffect, useRef, useState } from 'react';
import { useWorkProtection } from '../../auth/useWorkProtection';
import { ESC_LAYER_ATTR, useEscLayer } from '../upload/escLayer';
import { ParentPicker } from './ParentPicker';
import type { LineageGraph } from './graphTypes';
import type { LineageEditSource } from './lineageEditSource';
import type { LineageCandidateQuery, LineageSource, ParentCandidateRow } from './types';
import { useParentCandidates } from './useParentCandidates';
import './lineage.css';

/** 후보를 주는 얼굴 — 등록 ③ 이 쓰는 `LineageSource` 의 그 메서드다. */
export type ParentCandidateSource = Pick<LineageSource, 'candidates'>;

export function LineageFixModal(props: {
  datasetId: string;
  /** 기준 Lv — 그래프의 `이 데이터` 노드가 들고 있는 값이다. 모르면 `null`. */
  selfLv: number | null;
  candidateSource: ParentCandidateSource;
  editSource: LineageEditSource;
  /** 저장 성공 — 서버가 돌려준 **갱신된 그래프**가 그대로 올라간다. */
  onSaved: (graph: LineageGraph) => void;
  requestClose: () => void;
}) {
  const { candidateSource, editSource, requestClose } = props;
  const downOnBackdrop = useRef(false);
  const active = useRef(true);
  useEffect(() => { active.current = true; return () => { active.current = false; }; }, []);
  useEscLayer(useCallback(() => requestClose(), [requestClose]));

  const {
    candidates,
    candidateError,
    nextCursor,
    loadingMore,
    loadMoreError,
    loadCandidates: load,
    loadMore,
    retry,
  } = useParentCandidates(candidateSource);
  /** 찾기의 가공 단계 셀렉트. `null` = 전체 (PRD-08) — 등록 ③ 과 같은 규칙이다. */
  const [levelFilter, setLevelFilter] = useState<number | null>(null);
  const [picked, setPicked] = useState<ParentCandidateRow | null>(null);
  const [method, setMethod] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  useWorkProtection(`lineage-fix:${props.datasetId}`, {
    dirty: picked !== null || method !== '',
    inFlight: saving,
    discard: requestClose,
  });

  useEffect(() => {
    load({ excludeDatasetId: props.datasetId, limit: 25 });
  }, [load, props.datasetId]);

  function changeLevelFilter(next: number | null) {
    setLevelFilter(next);
  }

  function search(query: LineageCandidateQuery) {
    load({ ...query, excludeDatasetId: props.datasetId });
  }

  function save() {
    if (!picked || saving) return;
    setSaving(true);
    setError(null);
    void editSource
      .addParent(props.datasetId, {
        parentDatasetId: picked.datasetId,
        parentRole: '주입력',
        ...(method.trim() ? { method: method.trim() } : {}),
      })
      .then((graph) => {
        if (!active.current) return;
        props.onSaved(graph);
        requestClose();
      })
      .catch((e: unknown) => {
        // 서버 문구를 그대로 올린다 — 화면이 자기 판정 문구를 만들지 않는다.
        if (active.current) setError(e instanceof Error ? e.message : '계보를 고치지 못했어요.');
      })
      .finally(() => { if (active.current) setSaving(false); });
  }

  return (
    <div
      className="modal-back"
      data-testid="lin-fix-modal"
      {...{ [ESC_LAYER_ATTR]: '계보 수정' }}
      onMouseDown={(e) => {
        downOnBackdrop.current = e.target === e.currentTarget;
      }}
      onClick={(e) => {
        // 안쪽에서 눌러 배경에서 뗀 드래그로는 닫지 않는다 (A9R `downOnBackdrop`).
        if (e.target === e.currentTarget && downOnBackdrop.current) requestClose();
      }}
    >
      <div
        className="modal lin-fix"
        role="dialog"
        aria-modal="true"
        aria-label="계보 수정 · 추가"
        data-testid="lin-fix-body"
      >
        <div className="modal-h">
          <h3>계보 수정 · 추가</h3>
          <button
            type="button"
            className="x"
            data-testid="lin-fix-close"
            aria-label="계보 수정 닫기"
            onClick={requestClose}
          >
            ×
          </button>
        </div>
        <div className="modal-b">
          {/* 등록 ③ 과 **같은 컴포넌트**다 — 규칙이 한 자리에 있다 (PRD-07·08·09). */}
          <ParentPicker
            selfLv={props.selfLv}
            candidates={candidates}
            error={candidateError}
            onRetry={retry}
            levelFilter={levelFilter}
            onLevelFilterChange={changeLevelFilter}
            onSearch={search}
            nextCursor={nextCursor}
            loadingMore={loadingMore}
            loadMoreError={loadMoreError}
            onLoadMore={loadMore}
            onPick={(row) => setPicked(row)}
            testId="lin-fix-picker"
          />

          {picked ? (
            <div className="lin-fix-pick" data-testid="lin-fix-picked">
              <p>
                <b>{picked.name}</b> 를 가공 전 데이터로 잇습니다.
              </p>
              <label className="lin-fix-method-l" htmlFor="lin-fix-method">
                가공 방식
              </label>
              <input
                id="lin-fix-method"
                className="inp"
                data-testid="lin-fix-method"
                value={method}
                placeholder="예: 유역 클리핑 · 유역 평균"
                onChange={(e) => setMethod(e.target.value)}
              />
            </div>
          ) : (
            <p className="muted" data-testid="lin-fix-hint">
              이을 가공 전 데이터를 먼저 골라 주세요.
            </p>
          )}

          {error ? (
            <p className="de-err" role="alert" data-testid="lin-fix-error">
              {error}
            </p>
          ) : null}
        </div>
        <div className="modal-f">
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            data-testid="lin-fix-cancel"
            onClick={requestClose}
          >
            취소
          </button>
          <button
            type="button"
            className="btn btn-strong btn-sm"
            data-testid="lin-fix-save"
            disabled={!picked || saving}
            onClick={save}
          >
            {saving ? '잇는 중이에요…' : '연결 추가'}
          </button>
        </div>
      </div>
    </div>
  );
}
