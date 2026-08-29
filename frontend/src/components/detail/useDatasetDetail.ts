// 상세 한 건을 읽어 오는 상태 기계. 상태는 셋뿐이다 — 읽는 중 · 그린다 · 묘비.
import { useEffect, useState } from 'react';
import { DatasetGone, type DatasetDetail, type DetailSource } from './types';

export type DetailState =
  | { status: 'loading' }
  | { status: 'ready'; detail: DatasetDetail }
  | { status: 'gone' };

/** 같은 데이터셋을 이미 그리고 있으면 그 상태를 지키고, 아니면 `읽는 중` 이다. */
function keepIfSame(s: DetailState, datasetId: string): DetailState {
  return s.status === 'ready' && s.detail.datasetId === datasetId ? s : { status: 'loading' };
}

/**
 * `reloadToken` — 값이 바뀌면 다시 읽는다. **화면이 서버 값을 손으로 고치지 않게** 하는 자리다
 * (격자를 반영한 뒤 `hasReferenceGridFile` 을 화면이 직접 true 로 바꾸면 서버가 거절해도 참으로 보인다).
 *
 * 같은 데이터셋을 **다시 묻는** 동안은 그리던 것을 지우지 않는다 — 비우면 펼쳐 둔 파일 목록이
 * 접히고 사람이 다시 눌러야 한다. 다른 데이터셋으로 옮길 때는 종전처럼 `읽는 중` 부터다.
 */
export function useDatasetDetail(source: DetailSource, datasetId: string,
                                 reloadToken: number = 0): DetailState {
  const [state, setState] = useState<DetailState>({ status: 'loading' });

  useEffect(() => {
    let alive = true;
    setState((s) => keepIfSame(s, datasetId));
    source
      .get(datasetId)
      .then((detail) => alive && setState({ status: 'ready', detail }))
      .catch((e) => {
        if (!alive) return;
        // 묘비만 「지워졌다」고 말한다. 다른 실패를 여기로 흘려보내면 살아 있는 데이터를 지웠다고 한다
        setState((s) => (e instanceof DatasetGone ? { status: 'gone' } : keepIfSame(s, datasetId)));
      });
    return () => {
      alive = false;
    };
  }, [source, datasetId, reloadToken]);

  return state;
}
