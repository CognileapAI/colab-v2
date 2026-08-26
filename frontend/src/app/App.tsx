import { AuthGate } from '../auth/AuthGate';
import { AppRoutes } from './routes';

/**
 * 인증은 `AuthGate` 한 곳에만 있다 (`PLAN-SoT §9 〈90〉-㉮`).
 * 권한 값의 유일한 원천은 여전히 `GET /me` 이고(P-6·P-7), 그 응답을 문지기가 읽어
 * `SessionProvider` 에 심는다 — 화면은 인증도 토큰도 알지 못한다.
 */
export function App() {
  return (
    <AuthGate>
      <AppRoutes />
    </AuthGate>
  );
}
