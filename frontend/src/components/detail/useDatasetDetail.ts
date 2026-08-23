// 상세 한 건을 읽어 오는 상태 기계. 상태는 셋뿐이다 — 읽는 중 · 그린다 · 묘비.
import { useEffect, useState } from 'react';
import { DatasetGone, type DatasetDetail, type DetailSource } from './types';

export type DetailState =
  | { status: 'loading' }
  | { status: 'ready'; detail: DatasetDetail }
  | { status: 'gone' };

export function useDatasetDetail(source: DetailSource, datasetId: string): DetailState {
  const [state, setState] = useState<DetailState>({ status: 'loading' });

  useEffect(() => {
    let alive = true;
    setState({ status: 'loading' });
    source
      .get(datasetId)
      .then((detail) => alive && setState({ status: 'ready', detail }))
      .catch((e) => {
        if (!alive) return;
        // 묘비만 「지워졌다」고 말한다. 다른 실패를 여기로 흘려보내면 살아 있는 데이터를 지웠다고 한다
        setState(e instanceof DatasetGone ? { status: 'gone' } : { status: 'loading' });
      });
    return () => {
      alive = false;
    };
  }, [source, datasetId]);

  return state;
}
