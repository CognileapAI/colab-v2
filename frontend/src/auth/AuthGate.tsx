// 인증 문지기 — **다른 화면은 인증을 알지 못한다** (`PLAN-SoT §9 〈90〉-㉮`).
//
// 네 상태가 있다.
//   ① 토큰 없음        → 로그인 화면
//   ② 토큰 있고 확인 중 → 빈 화면(가짜 진행을 그리지 않는다)
//   ③ 토큰이 안 통함    → 토큰을 버리고 ①
//   ④ 확인을 못 함      → 못 했다고 말하고 다시 시도 (2026-09-03 신설)
//
// 401 을 받고도 앱을 그리면, 사람은 화면이 비어 있는 이유를 자기 실수로 의심한다.
//
// ⭑ **2026-09-03 개정** (`CODE-REVIEW-20260903` 부록) — `/me` 에 `.catch` 가 없어 서버에
// 닿지 못하면 ② 가 **영구 빈 화면**이 되고 다시 시도할 손잡이도 없었다. 그 자리를 ④ 로 세운다.
// 401 은 여전히 ③ 이다 — 못 닿은 것과 안 통하는 것은 사람이 할 일이 다르다.
import { useCallback, useEffect, useState, useSyncExternalStore } from 'react';
import { api, type CurrentAccount } from '../api/client';
import { LoadFailure } from '../components/common/LoadFailure';
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
  const [unreachable, setUnreachable] = useState(false);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    if (!token) {
      setAccount(null);
      setUnreachable(false);
      return;
    }
    let alive = true;
    setUnreachable(false);
    void api
      .GET('/me')
      .then(({ data, response }) => {
        if (!alive) return;
        if (data) {
          setAccount(data);
          return;
        }
        // 만료·위조·심어 둔 계정이 사라진 경우 — 전부 「다시 로그인」이다.
        if (response?.status === 401) {
          clearToken();
          return;
        }
        // 401 이 아닌 실패(5xx 등)는 **로그인 문제가 아니다.** 토큰을 버리면 멀쩡한 세션이
        // 서버 장애 때문에 끊긴다 — 버리지 않고 다시 시도할 자리를 준다.
        setUnreachable(true);
      })
      .catch(() => {
        // 네트워크가 끊겼다. 종전에는 이 갈래가 없어 화면이 ② 로 영원히 멈췄다.
        if (alive) setUnreachable(true);
      });
    return () => {
      alive = false;
    };
  }, [token, attempt]);

  if (!token) return <LoginPage />;
  if (unreachable) {
    return (
      <LoadFailure
        message="로그인 상태를 확인하지 못했어요. 잠시 뒤 다시 시도해 주세요."
        onRetry={() => setAttempt((n) => n + 1)}
        testId="auth-unreachable"
        retryLabel="다시 시도"
        retryTestId="auth-retry"
      />
    );
  }
  if (!account) return <div data-testid="auth-pending" />;

  return <SessionProvider account={account}>{props.children}</SessionProvider>;
}
