// 대시보드의 화면 상태. **구획마다 따로 싣고 따로 실패한다** (`Policy_홈_대시보드 §9`) —
// 데이터 맵이 안 와도 할 일 함은 뜬다. 한 덩어리로 묶으면 하나가 죽을 때 홈이 통째로 죽는다.
import { useCallback, useEffect, useState } from 'react';
import {
  GroupHidden,
  type Activity,
  type AccessRequest,
  type DashboardSource,
  type DashboardSummary,
  type DataMap,
  type LineageTodo,
  type VerificationRequest,
} from './types';

/** 한 구획의 적재 상태. `hidden` 은 **권한이 없어 그룹이 통째로 없는 것**이다 (`§6`). */
export type Slot<T> =
  | { kind: '적재 중' }
  | { kind: '있음'; value: T }
  | { kind: '없음' }
  | { kind: '실패'; message: string };

export type DashboardState = {
  summary: Slot<DashboardSummary>;
  dataMap: Slot<DataMap>;
  activities: Slot<Activity[]>;
  lineageTodo: Slot<LineageTodo[]>;
  verifications: Slot<VerificationRequest[]>;
  accessRequests: Slot<AccessRequest[]>;
  /** 다시 불러오기 — §9 「할 일 함을 불러오지 못했어요」의 복구 버튼이 부른다. */
  reload: () => void;
};

function useSlot<T>(load: (() => Promise<T>) | null, deps: unknown[]): Slot<T> {
  const [slot, setSlot] = useState<Slot<T>>({ kind: '적재 중' });
  useEffect(() => {
    if (load === null) return;
    let alive = true;
    load()
      .then((value) => alive && setSlot({ kind: '있음', value }))
      .catch((e: unknown) => {
        if (!alive) return;
        // 403 은 실패가 아니다 — 그 그룹이 없는 것이다 (`§6`).
        if (e instanceof GroupHidden) setSlot({ kind: '없음' });
        else setSlot({ kind: '실패', message: e instanceof Error ? e.message : '불러오지 못했어요.' });
      });
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  return slot;
}

export function useDashboard(source: DashboardSource): DashboardState {
  const [nonce, setNonce] = useState(0);
  const reload = useCallback(() => setNonce((n) => n + 1), []);
  return {
    summary: useSlot(() => source.summary(), [source, nonce]),
    dataMap: useSlot(() => source.dataMap(), [source, nonce]),
    activities: useSlot(() => source.activities(), [source, nonce]),
    lineageTodo: useSlot(() => source.lineageTodo(), [source, nonce]),
    verifications: useSlot(() => source.pendingVerifications(), [source, nonce]),
    accessRequests: useSlot(() => source.pendingAccessRequests(), [source, nonce]),
    reload,
  };
}
