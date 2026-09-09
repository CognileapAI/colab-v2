import { useCallback, useEffect, useRef, useState } from 'react';
import type {
  LineageCandidateQuery,
  LineageSource,
  ParentCandidateRow,
} from './types';

/** A failed lookup is not an empty result. Only the latest lookup may update the picker. */
export function useParentCandidates(source: Pick<LineageSource, 'candidates'>) {
  const [candidates, setCandidates] = useState<ParentCandidateRow[] | null>(null);
  const [candidateError, setCandidateError] = useState<string | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loadingMore, setLoadingMore] = useState(false);
  const [loadMoreError, setLoadMoreError] = useState<string | null>(null);
  const generation = useRef(0);
  const latestQuery = useRef<LineageCandidateQuery>({});
  useEffect(() => () => { generation.current += 1; }, [source]);
  const loadCandidates = useCallback((input: LineageCandidateQuery | number | null = {}) => {
    const query = typeof input === 'number'
      ? { processingLevel: input }
      : input ?? {};
    latestQuery.current = query;
    const current = ++generation.current;
    setCandidates(null);
    setCandidateError(null);
    setNextCursor(null);
    setLoadingMore(false);
    setLoadMoreError(null);
    void source.candidates(query).then(result => {
      if (current !== generation.current) return;
      const page = Array.isArray(result) ? { items: result, nextCursor: null } : result;
      setCandidates([...new Map(page.items.map(row => [row.datasetId, row])).values()]);
      setNextCursor(page.nextCursor);
    }).catch(() => {
      if (current === generation.current) setCandidateError('연구실 데이터 목록을 읽지 못했어요. 다시 시도해 주세요.');
    });
  }, [source]);

  const loadMore = useCallback(() => {
    if (!nextCursor || loadingMore) return;
    const current = generation.current;
    const cursor = nextCursor;
    setLoadingMore(true);
    setLoadMoreError(null);
    void source.candidates({ ...latestQuery.current, cursor }).then(result => {
      if (current !== generation.current) return;
      const page = Array.isArray(result) ? { items: result, nextCursor: null } : result;
      setCandidates(previous => {
        const rows = [...(previous ?? []), ...page.items];
        return [...new Map(rows.map(row => [row.datasetId, row])).values()];
      });
      setNextCursor(page.nextCursor);
    }).catch(() => {
      if (current === generation.current) setLoadMoreError('다음 결과를 더 읽지 못했어요. 기존 결과는 그대로예요.');
    }).finally(() => {
      if (current === generation.current) setLoadingMore(false);
    });
  }, [source, nextCursor, loadingMore]);

  const retry = useCallback(() => loadCandidates(latestQuery.current), [loadCandidates]);
  return {
    candidates,
    candidateError,
    nextCursor,
    loadingMore,
    loadMoreError,
    loadCandidates,
    loadMore,
    retry,
  };
}
