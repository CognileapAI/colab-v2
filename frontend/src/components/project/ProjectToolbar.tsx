// §8 필터 바 — 상태·유형·정렬 세 컨트롤과 보기 전환을 **목록 위 툴바 한 줄**에 모은다.
//
// 표만 있는 목록은 조건을 표 헤더에 두고, 카드/표 전환이 있는 목록은 툴바를 둔다 (§1.3-11).
// 이 화면은 두 보기를 오가므로 헤더에 넣으면 **카드 보기에서 조건을 걸 자리가 없어진다** —
// 데이터셋 목록(E-02)이 툴바를 걷어내고 헤더로 간 것과 갈리는 지점이다.
import { ALL, SORTS, type ProjectSort, type ProjectView, type StatusFilter, type TypeFilter } from './types';
import type { ProjectsState } from './useProjects';

const STATUSES: StatusFilter[] = ['진행 중', '닫힘', ALL];
const TYPES: TypeFilter[] = [ALL, '국가과제', '논문'];
const VIEWS: ProjectView[] = ['카드', '표'];

export function ProjectToolbar(props: { state: ProjectsState }) {
  const { state } = props;
  return (
    <div className="pj-toolbar" data-testid="project-toolbar">
      <label className="pj-ctl">
        <span>상태</span>
        <select
          aria-label="상태"
          value={state.query.status}
          onChange={(e) => state.setStatus(e.target.value as StatusFilter)}
        >
          {STATUSES.map((v) => (
            <option key={v} value={v}>
              {v}
            </option>
          ))}
        </select>
      </label>

      <label className="pj-ctl">
        <span>유형</span>
        <select
          aria-label="유형"
          value={state.query.type}
          onChange={(e) => state.setType(e.target.value as TypeFilter)}
        >
          {TYPES.map((v) => (
            <option key={v} value={v}>
              {v === ALL ? '유형 전체' : v}
            </option>
          ))}
        </select>
      </label>

      <label className="pj-ctl">
        <span>정렬</span>
        <select
          aria-label="정렬"
          value={state.query.sort}
          onChange={(e) => state.setSort(e.target.value as ProjectSort)}
        >
          {SORTS.map((v) => (
            <option key={v} value={v}>
              {v}
            </option>
          ))}
        </select>
      </label>

      {/* 보기 전환은 **조건을 건드리지 않는다** — 거른 결과와 정렬 순서가 그대로다 (§8) */}
      <div className="pj-views" role="radiogroup" aria-label="보기">
        {VIEWS.map((v) => (
          <button
            key={v}
            type="button"
            role="radio"
            aria-checked={state.view === v}
            aria-label={v}
            className={state.view === v ? 'on' : ''}
            onClick={() => state.setView(v)}
          >
            {v}
          </button>
        ))}
      </div>

      {/* 건수는 **아는 때에만** 그린다 — 못 불러온 자리의 「0건」은 실패를 「없음」으로
          바꿔 말한다. `useProjects` 가 그때 `totalCount` 를 `null` 로 둔다 (같은 한 벌의 판단). */}
      {state.totalCount !== null ? (
        <span className="pj-count">
          {state.totalCount}건
          {/* 숨김과 삭제가 헷갈리지 않게 (§8 숨은 닫힘 건수) */}
          {state.hiddenClosed > 0 ? ` · 닫힘 ${state.hiddenClosed}건은 숨겨져 있어요` : ''}
        </span>
      ) : null}
    </div>
  );
}
