// 목록·상세의 상태 기계.
//
// **필터·정렬은 한 벌뿐이다** — 카드와 표가 각자 거르면 곧 서로 다른 목록을 보여준다
// (`Policy_프로젝트 §5` 두 보기의 관계). 그래서 보기 전환은 조건을 **건드리지 않는다.**
import { useCallback, useEffect, useState } from 'react';
import {
  DEFAULT_QUERY,
  DEFAULT_VIEW,
  ProjectGone,
  type ProjectDetail,
  type ProjectQuery,
  type ProjectRow,
  type ProjectSource,
  type ProjectView,
  type StatusFilter,
  type TypeFilter,
} from './types';
import type { ProjectSort } from './types';

export type ProjectsState = {
  query: ProjectQuery;
  view: ProjectView;
  rows: ProjectRow[];
  totalCount: number;
  /** 숨은 닫힘 건수. **봉투에 필드를 만들지 않는다** — 상태만 `닫힘` 으로 바꿔 다시 세운 수다. */
  hiddenClosed: number;
  loading: boolean;
  /**
   * 못 불러왔다. **`rows.length === 0` 과 가른다** — 「조건에 맞는 프로젝트가 없어요」와
   * 「목록을 못 불러왔어요」는 사람이 할 일이 다르다 (`CODE-REVIEW-20260903` 9).
   */
  failed: boolean;
  /** 다시 불러오기 — 실패 자리의 손잡이가 부른다. 조건·보기는 그대로 둔다. */
  reload(): void;
  setStatus(value: StatusFilter): void;
  setType(value: TypeFilter): void;
  setSort(value: ProjectSort): void;
  setView(value: ProjectView): void;
};

export function useProjects(source: ProjectSource): ProjectsState {
  const [query, setQuery] = useState<ProjectQuery>(DEFAULT_QUERY);
  const [view, setView] = useState<ProjectView>(DEFAULT_VIEW);
  const [rows, setRows] = useState<ProjectRow[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [hiddenClosed, setHiddenClosed] = useState(0);
  const [loading, setLoading] = useState(true);
  const [failed, setFailed] = useState(false);
  const [nonce, setNonce] = useState(0);
  const reload = useCallback(() => setNonce((n) => n + 1), []);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setFailed(false);
    void (async () => {
      try {
        const list = await source.list(query);
        if (!alive) return;
        setRows(list.items);
        setTotalCount(list.totalCount);
        // 상태가 `진행 중` 일 때만 숨은 것이 있다. `전체`·`닫힘` 이면 숨긴 것이 없다.
        if (query.status !== '진행 중') {
          setHiddenClosed(0);
        } else {
          const closed = await source.list({ ...query, status: '닫힘' });
          if (alive) setHiddenClosed(closed.totalCount);
        }
        if (alive) setLoading(false);
      } catch {
        // **삼키지 않는다.** 종전에는 `catch` 가 아예 없어 목록 실패가 미처리 거절로 새고
        // 화면은 「조건에 맞는 프로젝트가 없어요」로 남았다 — 있는 프로젝트를 없다고 말한 것이다.
        if (!alive) return;
        setRows([]);
        setTotalCount(0);
        setHiddenClosed(0);
        setFailed(true);
        setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, [source, query, nonce]);

  const setStatus = useCallback((status: StatusFilter) => setQuery((q) => ({ ...q, status })), []);
  const setType = useCallback((type: TypeFilter) => setQuery((q) => ({ ...q, type })), []);
  const setSort = useCallback((sort: ProjectSort) => setQuery((q) => ({ ...q, sort })), []);

  return { query, view, rows, totalCount, hiddenClosed, loading, failed, reload,
           setStatus, setType, setSort, setView };
}

export type ProjectDetailState =
  | { status: 'loading' }
  | { status: 'ready'; detail: ProjectDetail }
  | { status: 'gone' }
  | { status: 'error' };

export function useProject(
  source: ProjectSource,
  projectId: string,
): ProjectDetailState & { reload(): void } {
  const [state, setState] = useState<ProjectDetailState>({ status: 'loading' });
  const [nonce, setNonce] = useState(0);
  const reload = useCallback(() => setNonce((n) => n + 1), []);

  useEffect(() => {
    let alive = true;
    setState({ status: 'loading' });
    source
      .get(projectId)
      .then((detail) => alive && setState({ status: 'ready', detail }))
      .catch((e) => {
        if (!alive) return;
        // 「없다」고 말하는 것은 404 뿐이다. 다른 실패를 여기로 흘리면 살아 있는 프로젝트를
        // 없다고 한다 (`useDatasetDetail` 의 묘비 규칙과 같다). 나머지는 「못 읽었다」다 —
        // `loading` 으로 되돌리면 영원한 빈 화면이 된다.
        setState(e instanceof ProjectGone ? { status: 'gone' } : { status: 'error' });
      });
    return () => {
      alive = false;
    };
  }, [source, projectId, nonce]);

  return { ...state, reload };
}
