import { useEffect, useState } from 'react';
import { api, type CurrentAccount } from '../api/client';
import { SessionProvider } from '../permission/session';
import { AppRoutes } from './routes';

/**
 * 권한 값의 유일한 원천은 GET /me 다 (P-6·P-7).
 * 응답이 오기 전에는 account 가 null 이고, 그동안 모든 스위치는 꺼진 것으로 본다 — fail-closed.
 */
export function App() {
  const [account, setAccount] = useState<CurrentAccount | null>(null);

  useEffect(() => {
    let alive = true;
    void api.GET('/me').then(({ data }) => {
      if (alive && data) setAccount(data);
    });
    return () => {
      alive = false;
    };
  }, []);

  return (
    <SessionProvider account={account}>
      <AppRoutes />
    </SessionProvider>
  );
}
