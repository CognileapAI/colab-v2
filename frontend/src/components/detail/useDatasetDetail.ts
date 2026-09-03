// 상세 한 건을 읽어 오는 상태 기계. 상태는 넷 — 읽는 중 · 그린다 · 묘비 · 못 읽음.
//
// ⭑ **2026-09-03 개정** (`CODE-REVIEW-20260903` 9) — 종전에는 묘비가 아닌 실패를 전부
// `loading` 으로 되돌려 **영원한 빈 화면**을 만들었다(픽스처 폴백이 그 자리를 가려 잘 안
// 보였다). 「읽는 중」과 「못 읽었다」는 사람이 할 일이 다르다 — 기다릴 것인가 다시 부를 것인가.
import { useEffect, useState } from 'react';
import { DatasetGone, type DatasetDetail, type DetailSource } from './types';

export type DetailState =
  | { status: 'loading' }
  | { status: 'ready'; detail: DatasetDetail }
  | { status: 'gone' }
  | { status: 'error' };

/**
 * `reloadToken` — 값이 바뀌면 다시 읽는다. **화면이 서버 값을 손으로 고치지 않게** 하는 자리다
 * (격자를 반영한 뒤 `hasReferenceGridFile` 을 화면이 직접 true 로 바꾸면 서버가 거절해도 참으로 보인다).
 */
export function useDatasetDetail(source: DetailSource, datasetId: string,
                                 reloadToken: number = 0): DetailState {
  const [state, setState] = useState<DetailState>({ status: 'loading' });

  useEffect(() => {
    let alive = true;
    setState({ status: 'loading' });
    source
      .get(datasetId)
      .then((detail) => alive && setState({ status: 'ready', detail }))
      .catch((e) => {
        if (!alive) return;
        // 묘비만 「지워졌다」고 말한다. 다른 실패를 여기로 흘려보내면 살아 있는 데이터를
        // 지웠다고 한다 — 그래서 그 나머지는 「못 읽었다」로 따로 선다.
        setState(e instanceof DatasetGone ? { status: 'gone' } : { status: 'error' });
      });
    return () => {
      alive = false;
    };
  }, [source, datasetId, reloadToken]);

  return state;
}
