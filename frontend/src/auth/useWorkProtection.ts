import { useEffect, useRef } from 'react';
import { useAccount } from '../permission/session';
import { registerWork } from './workGuard';

type WorkProtection = {
  dirty: boolean;
  inFlight: boolean;
  discard?: () => void | Promise<void>;
  abort?: () => void;
};

/** 명시적 React 상태도 폼 DOM 바깥 변경까지 계정 전환 보호기에 등록한다. */
export function useWorkProtection(key: string, state: WorkProtection): void {
  const accountId = useAccount()?.accountId ?? null;
  const discard = useRef(state.discard);
  const abort = useRef(state.abort);
  discard.current = state.discard;
  abort.current = state.abort;

  useEffect(() => {
    if (!accountId || (!state.dirty && !state.inFlight)) return;
    return registerWork(key, {
      accountId,
      dirty: state.dirty,
      inFlight: state.inFlight,
      discard: () => discard.current?.(),
      abort: () => abort.current?.(),
    });
  }, [accountId, key, state.dirty, state.inFlight]);
}
