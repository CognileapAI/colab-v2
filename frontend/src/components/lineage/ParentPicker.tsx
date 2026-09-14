// 가공 전 데이터 **찾기·연결 UI** — 등록 ③ 과 상세 계보 모달이 **같은 한 벌**을 쓴다.
//
// ⭑ **⟨WU-B10 · PRD-31⟩ 이 파일은 새 화면이 아니라 `LineageStep` 안에 있던 `picker()` 를
//   그대로 들어올린 것이다.** 상세 모달이 사본을 만들면 PRD-07·08·09 의 규칙이 두 벌이 되고,
//   한쪽만 고쳐지는 날이 온다 — 그래서 옮기고 **양쪽이 이것을 부른다**.
//
// 여기가 지키는 것 (PRD-08 · WU-B5)
//  - **없는 것과 못 고르는 것은 다르다** — 초과 후보도 목록에 남고, 라디오만 비활성이며,
//    사유 한 줄이 읽힌다. 행 전체를 흐리게 만들지 않는다(`R-21` · `lineage.css`).
//  - **사유 문면은 이 파일 하나에 있다**(`parentOverReason`). 부르는 쪽이 다시 적지 않는다.
//
// ⭑ **⟨개정 2026-09-14 · 기획서 rev2 `#findModal` 축자⟩**
//   ／ 종전 ~~후보 줄 = 버튼 ＋ 파일명 전체 나열 · 필터 5칸(이름·분류·주제·가공 단계·기간 2)~~
//   ／ 종전 ~~필터는 검색어 하나 · 하단에 가공 방식 칸~~ (2026-09-14 중간본)
//  - **행은 라디오 단일 선택**이다(rev2 `#findList .frow` 축자). 누른 것이 곧 연결이 아니라,
//    **하단 고정 영역의 「이 데이터로 연결」이 확정**한다.
//  - **행이 적는 것은 이름 · 가공 단계 · 분류 · 기간 넷뿐**이다(기획자 「핵심 정보만」).
//    주제·원천 표기는 뺐다 — 고르는 판단에 쓰이지 않는 값이 줄 길이를 두 배로 만들었다.
//  - **파일은 대표 하나 ＋ 「외 N개」** 다. 전체 나열(`fileNames.join`)은 한 줄이 열 줄이 됐다.
//  - **필터는 목업 `.findbar` 의 네 칸**이다 — 이름·파일명 검색 · 분류 · 기간 · 가공 단계
//    (PRD-41 「네 조건은 AND」 · 가공 단계는 PRD-08). 네 값은 **한 질의로 함께** 서버로 가고,
//    목록은 고정 높이로 구른다.
//  - **가공 단계 칸의 항목은 자기 Lv 이하만**이다(목업 `buildFindLv()`). ⛔ 그 칸이 초과
//    후보를 **지우지는 않는다** — 초과 행은 목록에 남고 라디오만 비활성이다(PRD-08 무변).
//  - **하단 고정 영역** = 고른 후보 요약(이름·단계·분류) ＋ 취소／연결 **둘뿐**이다
//    (목업 `.modal-f`). ⛔ **가공 방식 칸을 여기 두지 않는다** — 그 칸은 팝업을 닫은 뒤
//    **연결 카드**에 있다(목업 `.li-act`).
//  ⚠ **하단 영역은 모달로 뜰 때(`onClose` 있음)만 선다.** 상세 계보 모달은 이 컴포넌트를
//    본문에 끼워 넣고 자기 바닥(`lin-fix-pick`)을 이미 갖고 있어, 여기서 또 그리면 두 벌이 된다.
import { useCallback, useEffect, useRef, useState } from 'react';
import { ESC_LAYER_ATTR, useEscLayer } from '../upload/escLayer';
import { CATEGORIES } from '../upload/axisDict';
import {
  LV_VALUES,
  displayLevel,
  type LineageCandidateQuery,
  type ParentCandidateRow,
} from './types';

/** 초과 후보의 사유 축자 (PRD-08 rev1). **두 화면이 이 한 함수를 쓴다.** */
export function parentOverReason(selfLv: number): string {
  return `이 데이터(Lv${selfLv})보다 높은 단계예요. 연결을 지우거나 분류에서 가공 단계를 올려 주세요.`;
}

/**
 * 파일 표기 — **대표 하나 ＋ 「외 N개」** (기획자 2026-09-13).
 * 1건이면 이름만이고, 0건이면 줄 자체를 세우지 않는다(`null`).
 */
export function candidateFilesLabel(fileNames: string[]): string | null {
  if (fileNames.length === 0) return null;
  const [head, ...rest] = fileNames;
  return rest.length === 0 ? head! : `${head} 외 ${rest.length}개`;
}

/**
 * 기간 한 줄 — 끝이 없으면 `계속`. 날짜만 쓴다(시각은 고르는 판단에 쓰이지 않는다).
 * ⭑ **연결 카드도 이 함수를 쓴다**(`LineageStep`) — 같은 값이 두 문면으로 갈리지 않게.
 */
export function parentPeriodLabel(
  period: { start: string; end: string | null } | null | undefined,
): string | null {
  if (!period) return null;
  return `${period.start.slice(0, 10)} ~ ${period.end?.slice(0, 10) ?? '계속'}`;
}

/**
 * 기간 셀렉트의 항목 — **후보가 실제로 가진 연도**만 세운다(목업 `.findbar` 의 `2025`·`2024`).
 * ⛔ 없는 연도를 지어내지 않는다. 고른 연도는 결과가 줄어도 목록에 남는다(되돌릴 길).
 */
function candidateYears(rows: ParentCandidateRow[] | null, picked: string): string[] {
  const years = new Set<string>();
  for (const row of rows ?? []) {
    const period = 'period' in row ? row.period : null;
    if (period?.start) years.add(period.start.slice(0, 4));
  }
  if (picked) years.add(picked);
  return [...years].sort().reverse();
}

export function ParentPicker(props: {
  /** 기준 Lv. `null` 이면 기준값이 없어 아무 후보도 초과로 세지 않는다. */
  selfLv: number | null;
  error?: string | null;
  onRetry?: () => void;
  onClose?: () => void;
  /** `null` = 읽는 중. 빈 배열은 **정직한 빈 상태**다. */
  candidates: ParentCandidateRow[] | null;
  /**
   * 가공 단계 셀렉트가 쥔 값. `null` = 전체. 거르는 것은 **서버 질의 파라미터**이고
   * ⛔ 자기 Lv 로 자동으로 걸지 않는다 — 초과 후보도 내려와야 「보이되 못 고름」이 그려진다.
   */
  levelFilter: number | null;
  onLevelFilterChange: (next: number | null) => void;
  onSearch?: (query: LineageCandidateQuery) => void;
  nextCursor?: string | null;
  loadingMore?: boolean;
  loadMoreError?: string | null;
  onLoadMore?: () => void;
  /** 고른 후보 한 건. ⭑ ⟨개정 2026-09-14⟩ 가공 방식은 **연결 카드**가 받는다. */
  onPick: (row: ParentCandidateRow) => void;
  /** 부르는 자리마다 다른 손잡이 — 등록 ③ 은 `lin-picker`, 상세 모달은 `lin-fix-picker`. */
  testId: string;
}) {
  const { selfLv, candidates, levelFilter } = props;
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('');
  const [year, setYear] = useState('');
  const [selected, setSelected] = useState<ParentCandidateRow | null>(null);
  const body = useRef<HTMLDivElement>(null);
  const downOnBackdrop = useRef(false);
  const selectedLv = selected ? displayLevel(selected) : null;
  const valid =
    selected &&
    (candidates ?? []).some((row) => row.datasetId === selected.datasetId) &&
    (selfLv === null || selectedLv === null || selectedLv <= selfLv);
  /** 목업 `.findbar` 네 칸이 **한 질의**로 나간다(PRD-41 「네 조건은 AND」). */
  function search(
    next: Partial<{ q: string; category: string; year: string; processingLevel: number | null }>,
  ) {
    const values = { q: query, category, year, processingLevel: levelFilter, ...next };
    setSelected(null);
    props.onSearch?.({
      ...(values.q.trim() ? { q: values.q.trim() } : {}),
      ...(values.category ? { category: values.category } : {}),
      // 연도 한 칸이 구간 두 값으로 펼쳐진다. UTC 하루 경계 변환은 `lineageSource` 몫이다.
      ...(values.year
        ? { periodStart: `${values.year}-01-01`, periodEnd: `${values.year}-12-31` }
        : {}),
      ...(values.processingLevel !== null ? { processingLevel: values.processingLevel } : {}),
      limit: 25,
    });
  }
  /** 가공 단계 항목 상한 = 자기 Lv (목업 `buildFindLv()`). 기준값이 없으면 목록 전체다. */
  const lvCap = selfLv ?? (LV_VALUES[LV_VALUES.length - 1] as number);
  const lvAllLabel = selfLv === null
    ? '가공 단계 전체'
    : `연결 가능 전체 · ${selfLv === 0 ? 'Lv0' : `Lv0~Lv${selfLv}`}`;
  const years = candidateYears(candidates, year);
  useEscLayer(useCallback(() => { props.onClose?.(); }, [props.onClose]));
  useEffect(() => {
    if (!props.onClose) return;
    const previous = document.activeElement as HTMLElement | null;
    body.current?.querySelector<HTMLInputElement>('input')?.focus();
    return () => { previous?.focus(); };
  }, []);
  const content = (
    <div className="lin-picker" data-testid={props.testId}>
      {/* ⭑ **⟨PRD-08 · PRD-41 · rev2 `.findbar`⟩ 네 칸 — 이름 검색 · 분류 · 기간 · 가공 단계.** */}
      <div className="lin-findbar">
        <label>
          <span>이름·파일명</span>
          <input
            className="inp"
            type="search"
            aria-label="데이터셋 이름 또는 파일명 검색"
            placeholder="이름 또는 파일명으로 찾아요"
            value={query}
            onChange={(event) => { setQuery(event.target.value); search({ q: event.target.value }); }}
          />
        </label>
        <label>
          <span>분류</span>
          <select
            className="sel"
            data-testid="lin-cat-filter"
            aria-label="분류"
            value={category}
            onChange={(event) => { setCategory(event.target.value); search({ category: event.target.value }); }}
          >
            <option value="">분류 전체</option>
            {CATEGORIES.map((item) => (
              <option key={item.value} value={item.value}>{item.label}</option>
            ))}
          </select>
        </label>
        <label>
          <span>기간</span>
          <select
            className="sel"
            data-testid="lin-period-filter"
            aria-label="기간"
            value={year}
            onChange={(event) => { setYear(event.target.value); search({ year: event.target.value }); }}
          >
            <option value="">기간 전체</option>
            {years.map((value) => <option key={value} value={value}>{value}</option>)}
          </select>
        </label>
        <label>
          <span>가공 단계</span>
          <select
            className="sel"
            data-testid="lin-lv-filter"
            aria-label="가공 단계"
            value={levelFilter === null ? '' : String(levelFilter)}
            onChange={(event) => {
              const next = event.target.value === '' ? null : Number(event.target.value);
              props.onLevelFilterChange(next);
              search({ processingLevel: next });
            }}
          >
            <option value="">{lvAllLabel}</option>
            {LV_VALUES.filter((value) => value <= lvCap).map((value) => (
              <option key={value} value={value}>Lv{value}</option>
            ))}
          </select>
        </label>
      </div>
      {props.error ? <div role="alert"><p>{props.error}</p><button type="button" className="btn btn-secondary" onClick={props.onRetry}>다시 시도</button></div> : candidates === null ? (
        <p className="muted">연구실 데이터를 읽는 중이에요…</p>
      ) : candidates.length === 0 ? (
        <p className="muted">{query || category || year || levelFilter !== null
          ? '검색 조건에 맞는 데이터가 없어요. 조건을 바꿔 주세요.'
          : '고를 수 있는 연구실 데이터가 아직 없어요.'}</p>
      ) : (
        <ul className="lin-cand-list">
          {candidates.map((row) => {
            // **없는 것과 못 고르는 것은 다르다** — 초과 행도 목록에 남고 사유가 읽힌다.
            // ⭑ ⟨WU-C9⟩ 후보 줄도 같은 표시 규칙을 지난다.
            const lv = displayLevel(row);
            const over = selfLv !== null && lv !== null && lv > selfLv;
            const picked = selected?.datasetId === row.datasetId;
            const files = 'fileNames' in row ? candidateFilesLabel(row.fileNames) : null;
            return (
              <li
                key={row.datasetId}
                data-testid={`lin-row-${row.datasetId}`}
                className={[over ? 'is-over' : null, picked ? 'is-picked' : null].filter(Boolean).join(' ') || undefined}
              >
                <label className="lin-cand">
                  <input
                    type="radio"
                    name={`${props.testId}-parent`}
                    data-testid={`lin-pick-${row.datasetId}`}
                    disabled={over}
                    checked={picked}
                    onChange={() => {
                      setSelected(row);
                      // 상세 계보 모달은 자기 바닥에서 확정한다 — 고르는 즉시 알린다.
                      if (!props.onClose) props.onPick(row);
                    }}
                  />
                  <span className="lin-cand-b">
                    <span className="lin-cand-h">
                      <span className="lin-name">{row.name}</span>
                      {lv !== null && <span className="lin-lv">Lv{lv}</span>}
                    </span>
                    <span className="lin-candidate-info">{[
                      'category' in row ? row.category : null,
                      'period' in row ? parentPeriodLabel(row.period) : null,
                    ].filter(Boolean).join(' · ')}</span>
                    {files ? (
                      <span className="lin-candidate-files" data-testid={`lin-files-${row.datasetId}`}>{files}</span>
                    ) : null}
                  </span>
                </label>
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
      {props.loadMoreError ? (
        <div data-testid="lin-load-more-error" role="alert">
          <p>{props.loadMoreError}</p>
          <button type="button" className="btn btn-secondary btn-sm" onClick={props.onLoadMore}>다음 결과 다시 보기</button>
        </div>
      ) : props.nextCursor ? (
        <button type="button" className="btn btn-secondary btn-sm" disabled={props.loadingMore} onClick={props.onLoadMore}>
          {props.loadingMore ? '다음 결과를 읽는 중이에요…' : '다음 결과 보기'}
        </button>
      ) : null}
    </div>
  );
  if (!props.onClose) return content;
  return <div className="modal-back lin-find-back" {...{ [ESC_LAYER_ATTR]: '가공 전 데이터 찾기' }} onMouseDown={event => { downOnBackdrop.current = event.target === event.currentTarget; }} onClick={event => { if (event.target === event.currentTarget && downOnBackdrop.current) props.onClose?.(); }}>
    <div className="modal lin-find" role="dialog" aria-modal="true" aria-label="가공 전 데이터 직접 찾기" ref={body} onKeyDown={event => {
      if (event.key !== 'Tab') return;
      const focusable = body.current?.querySelectorAll<HTMLElement>('button:not(:disabled), input:not(:disabled), select');
      if (!focusable?.length) return;
      const first = focusable[0]; const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
    }}>
      <div className="modal-h"><h3>가공 전 데이터 직접 찾기</h3><button type="button" className="x" aria-label="찾기 닫기" onClick={props.onClose}>×</button></div>
      <div className="modal-b">{content}</div>
      {/* ⭑ **하단 고정 영역**(목업 `.modal-f`) — 고른 것을 되읽어 주고 취소／연결 둘뿐이다.
          ⛔ **가공 방식 칸을 여기 두지 않는다** — 고른 뒤 팝업을 닫고 **연결 카드**에서 적는다. */}
      <div className="modal-f lin-find-f">
        <p className="lin-find-sum" data-testid="lin-find-summary">
          {selected
            ? [selected.name, selectedLv !== null ? `Lv${selectedLv}` : null,
               'category' in selected ? selected.category : null].filter(Boolean).join(' · ')
            : '후보를 고르세요'}
        </p>
        <div className="lin-find-btns">
          <button type="button" className="btn btn-secondary" onClick={props.onClose}>취소</button>
          <button type="button" className="btn btn-primary" disabled={!valid || !!props.error} onClick={() => {
            if (!valid || !selected) return;
            props.onPick(selected);
          }}>이 데이터로 연결</button>
        </div>
      </div>
    </div>
  </div>;
}
