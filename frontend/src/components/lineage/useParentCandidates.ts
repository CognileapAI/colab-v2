import { useCallback, useEffect, useRef, useState } from 'react';
import type { DatasetRow, LineageSource } from './types';

/** A failed lookup is not an empty result. Only the latest lookup may update the picker. */
export function useParentCandidates(source: Pick<LineageSource, 'candidates'>) {
  const [candidates, setCandidates] = useState<DatasetRow[] | null>(null);
  const [candidateError, setCandidateError] = useState<string | null>(null);
  const generation = useRef(0);
  useEffect(() => () => { generation.current += 1; }, [source]);
  const loadCandidates = useCallback((level: number | null) => {
    const current = ++generation.current;
    setCandidates(null);
    setCandidateError(null);
    void source.candidates(level).then(rows => {
      if (current === generation.current) setCandidates(rows);
    }).catch(() => {
      if (current === generation.current) setCandidateError('연구실 데이터 목록을 읽지 못했어요. 다시 시도해 주세요.');
    });
  }, [source]);
  return { candidates, candidateError, loadCandidates };
}
