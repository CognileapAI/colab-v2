// 가공 전 데이터 **찾기·연결 UI** — 등록 ③ 과 상세 계보 모달이 **같은 한 벌**을 쓴다.
//
// ⭑ **⟨WU-B10 · PRD-31⟩ 이 파일은 새 화면이 아니라 `LineageStep` 안에 있던 `picker()` 를
//   그대로 들어올린 것이다.** 상세 모달이 사본을 만들면 PRD-07·08·09 의 규칙이 두 벌이 되고,
//   한쪽만 고쳐지는 날이 온다 — 그래서 옮기고 **양쪽이 이것을 부른다**.
//
// 여기가 지키는 것 (PRD-08 · WU-B5)
//  - **가공 단계 셀렉트가 거르는 자리는 서버 질의 파라미터**다. 자기 Lv 로 자동으로 걸지 않는다.
//  - **없는 것과 못 고르는 것은 다르다** — 초과 후보도 목록에 남고, 버튼만 비활성이며,
//    사유 한 줄이 읽힌다. 행 전체를 흐리게 만들지 않는다(`R-21` · `lineage.css`).
//  - **사유 문면은 이 파일 하나에 있다**(`parentOverReason`). 부르는 쪽이 다시 적지 않는다.
import { useCallback, useEffect, useRef, useState } from 'react';
import { ESC_LAYER_ATTR, useEscLayer } from '../upload/escLayer';
import { LV_VALUES, displayLevel, type DatasetRow } from './types';

/** 초과 후보의 사유 축자 (PRD-08 rev1). **두 화면이 이 한 함수를 쓴다.** */
export function parentOverReason(selfLv: number): string {
  return `이 데이터(Lv${selfLv})보다 높은 단계예요. 연결을 지우거나 분류에서 가공 단계를 올려 주세요.`;
}

export function ParentPicker(props: {
  /** 기준 Lv. `null` 이면 기준값이 없어 아무 후보도 초과로 세지 않는다. */
  selfLv: number | null;
  error?: string | null;
  onRetry?: () => void;
  onClose?: () => void;
  /** `null` = 읽는 중. 빈 배열은 **정직한 빈 상태**다. */
  candidates: DatasetRow[] | null;
  levelFilter: number | null;
  onLevelFilterChange: (next: number | null) => void;
  onPick: (row: DatasetRow) => void;
  /** 부르는 자리마다 다른 손잡이 — 등록 ③ 은 `lin-picker`, 상세 모달은 `lin-fix-picker`. */
  testId: string;
}) {
  const { selfLv, candidates, levelFilter } = props;
  const [query, setQuery] = useState('');
  const [topic, setTopic] = useState('');
  const [selected, setSelected] = useState<DatasetRow | null>(null);
  const body = useRef<HTMLDivElement>(null);
  const downOnBackdrop = useRef(false);
  const topics = [...new Set((candidates ?? []).map(row => row.topic).filter(Boolean))];
  const filtered = (candidates ?? []).filter(row => row.name.toLocaleLowerCase().includes(query.trim().toLocaleLowerCase()) && (!topic || row.topic === topic));
  const valid = selected && filtered.some(row => row.datasetId === selected.datasetId) && (selfLv === null || displayLevel(selected) === null || displayLevel(selected)! <= selfLv);
  useEscLayer(useCallback(() => { props.onClose?.(); }, [props.onClose]));
  useEffect(() => {
    if (!props.onClose) return;
    const previous = document.activeElement as HTMLElement | null;
    body.current?.querySelector<HTMLInputElement>('input')?.focus();
    return () => { previous?.focus(); };
  }, []);
  const content = (
    <div className="lin-picker" data-testid={props.testId}>
      <div className="lin-findbar">
        <label><span>데이터셋 이름</span><input className="inp" type="search" aria-label="데이터셋 이름 검색" placeholder="데이터셋 이름으로 찾아요" value={query} onChange={event => setQuery(event.target.value)} /></label>
        <label><span>주제</span><select className="sel" aria-label="주제" value={topic} onChange={event => setTopic(event.target.value)}><option value="">주제 전체</option>{topics.map(value => <option key={value!} value={value!}>{value}</option>)}</select></label>
      {/* ⭑ **⟨PRD-08⟩ 가공 단계 셀렉트.** 거르는 것은 **서버 질의 파라미터**이고,
          자기 Lv 로 자동으로 걸지 않는다 — 초과 후보도 내려와야 아래 `is-over` 가
          「보이되 못 고름」을 그릴 수 있다. */}
      <label className="lin-lvfilter">
        <span>가공 단계</span>
        <select
          className="sel"
          data-testid="lin-lv-filter"
          value={levelFilter === null ? '' : String(levelFilter)}
          onChange={(e) =>
            props.onLevelFilterChange(e.target.value === '' ? null : Number(e.target.value))
          }
        >
          <option value="">전체</option>
          {LV_VALUES.map((v) => (
            <option key={v} value={v}>
              Lv{v}
            </option>
          ))}
        </select>
      </label>
      </div>
      {props.error ? <div role="alert"><p>{props.error}</p><button type="button" className="btn btn-secondary" onClick={props.onRetry}>다시 시도</button></div> : candidates === null ? (
        <p className="muted">연구실 데이터를 읽는 중이에요…</p>
      ) : filtered.length === 0 ? (
        <p className="muted">{query || topic ? '검색 조건에 맞는 데이터가 없어요. 조건을 바꿔 주세요.' : '고를 수 있는 연구실 데이터가 아직 없어요.'}</p>
      ) : (
        <ul>
          {filtered.map((row) => {
            // **없는 것과 못 고르는 것은 다르다** — 초과 행도 목록에 남고 사유가 읽힌다.
            // ⭑ ⟨WU-C9⟩ 후보 줄도 같은 표시 규칙을 지난다.
            const lv = displayLevel(row);
            const over = selfLv !== null && lv !== null && lv > selfLv;
            return (
              <li key={row.datasetId} className={over ? 'is-over' : undefined}>
                <button
                  type="button"
                  className="btn btn-ghost btn-sm"
                  data-testid={`lin-pick-${row.datasetId}`}
                  disabled={over}
                  aria-pressed={selected?.datasetId === row.datasetId}
                  onClick={() => { setSelected(row); if (!props.onClose) props.onPick(row); }}
                >
                  {row.name} {lv !== null && <span className="lin-lv">Lv{lv}</span>}
                </button>
                <p className="lin-candidate-info">{[row.topic, row.projects?.representative?.name, row.fileCount ? `파일 ${row.fileCount}개` : null, row.uploader?.name].filter(Boolean).join(' · ')}</p>
                {over && (
                  // 사유는 **살린다** — 행 전체를 흐리게 만들면 유일한 설명이 무너진다(`R-21`).
                  <p className="lin-over-why" data-testid={`lin-over-${row.datasetId}`}>
                    {parentOverReason(selfLv as number)}
                  </p>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
  if (!props.onClose) return content;
  return <div className="modal-back lin-find-back" {...{ [ESC_LAYER_ATTR]: '가공 전 데이터 찾기' }} onMouseDown={event => { downOnBackdrop.current = event.target === event.currentTarget; }} onClick={event => { if (event.target === event.currentTarget && downOnBackdrop.current) props.onClose?.(); }}>
    <div className="modal lin-find" role="dialog" aria-modal="true" aria-label="가공 전 데이터 직접 찾기" ref={body} onKeyDown={event => {
      if (event.key !== 'Tab') return;
      const focusable = body.current?.querySelectorAll<HTMLElement>('button:not(:disabled), input, select');
      if (!focusable?.length) return;
      const first = focusable[0]; const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
    }}>
      <div className="modal-h"><h3>가공 전 데이터 직접 찾기</h3><button type="button" className="x" aria-label="찾기 닫기" onClick={props.onClose}>×</button></div>
      <div className="modal-b">{content}</div>
      <div className="modal-f"><button type="button" className="btn btn-secondary" onClick={props.onClose}>취소</button><button type="button" className="btn btn-primary" disabled={!valid || !!props.error} onClick={() => { if (valid && selected) props.onPick(selected); }}>이 데이터로 연결</button></div>
    </div>
  </div>;
}
