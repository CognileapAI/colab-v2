// 인증 문지기 — **다른 화면은 인증을 알지 못한다** (`PLAN-SoT §9 〈90〉-㉮`).
//
// 세 상태만 있다.
//   ① 토큰 없음        → 로그인 화면
//   ② 토큰 있고 확인 중 → 빈 화면(가짜 진행을 그리지 않는다)
//   ③ 토큰이 안 통함    → 토큰을 버리고 ①
//
// 401 을 받고도 앱을 그리면, 사람은 화면이 비어 있는 이유를 자기 실수로 의심한다.
import { useCallback, useEffect, useState, useSyncExternalStore } from 'react';
import { api, type CurrentAccount } from '../api/client';
import { SessionProvider } from '../permission/session';
import { LoginPage } from './LoginPage';
import { clearToken, getToken, subscribe } from './store';

export function useToken(): string | null {
  return useSyncExternalStore(subscribe, getToken, getToken);
}

/** 로그아웃 — 서버 op 을 부르고, 결과와 무관하게 토큰을 버린다 (`〈90〉-㉳`). */
export function useLogout(): () => void {
  return useCallback(() => {
    void api.DELETE('/sessions/current').finally(() => clearToken());
  }, []);
}

export function AuthGate(props: { children: React.ReactNode }) {
  const token = useToken();
  const [account, setAccount] = useState<CurrentAccount | null>(null);

  useEffect(() => {
    if (!token) {
      setAccount(null);
      return;
    }
    let alive = true;
    void api.GET('/me').then(({ data, response }) => {
      if (!alive) return;
      if (data) {
        setAccount(data);
        return;
      }
      // 만료·위조·심어 둔 계정이 사라진 경우 — 전부 「다시 로그인」이다.
      if (response?.status === 401) clearToken();
    });
    return () => {
      alive = false;
    };
  }, [token]);

  if (!token) return <LoginPage />;
  if (!account) return <div data-testid="auth-pending" />;

  return <SessionProvider account={account}>{props.children}</SessionProvider>;
}
