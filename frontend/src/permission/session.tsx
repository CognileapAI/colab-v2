// 현재 사용자 = GET /me 가 내려준 값 그대로. 화면이 역할로 권한을 재계산하지 않는다 (P-6·P-7).
import { createContext, useContext } from 'react';
import type { CurrentAccount } from '../api/client';

const SessionContext = createContext<CurrentAccount | null>(null);

export function SessionProvider(props: {
  account: CurrentAccount | null;
  children: React.ReactNode;
}) {
  return (
    <SessionContext.Provider value={props.account}>{props.children}</SessionContext.Provider>
  );
}

/** 아직 /me 응답이 없으면 null. 없는 동안 권한은 전부 꺼진 것으로 본다(fail-closed). */
export function useAccount(): CurrentAccount | null {
  return useContext(SessionContext);
}
