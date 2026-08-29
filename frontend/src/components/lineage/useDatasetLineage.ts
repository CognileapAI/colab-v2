// 계보 한 건을 읽어 오는 상태 기계. 상태는 셋뿐이다 — 읽는 중 · 그린다 · 못 읽음.
//
// **못 읽음을 「빈 계보」로 접지 않는다.** 접으면 관계가 있는 데이터를 없다고 말한다.
import { useEffect, useState } from 'react';
import type { LineageGraph, LineageGraphSource } from './graphTypes';

export type LineageGraphState =
  | { status: 'loading' }
  | { status: 'ready'; graph: LineageGraph }
  | { status: 'unavailable' };

export function useDatasetLineage(
  source: LineageGraphSource,
  datasetId: string,
  reloadToken: number = 0,
): LineageGraphState {
  const [state, setState] = useState<LineageGraphState>({ status: 'loading' });

  useEffect(() => {
    let alive = true;
    setState({ status: 'loading' });
    source
      .get(datasetId)
      .then((graph) => alive && setState({ status: 'ready', graph }))
      .catch(() => alive && setState({ status: 'unavailable' }));
    return () => {
      alive = false;
    };
  }, [source, datasetId, reloadToken]);

  return state;
}
