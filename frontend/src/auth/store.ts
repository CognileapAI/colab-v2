// 세션 토큰의 **유일한 보관소**. 다른 화면은 이 파일을 거치지 않고 토큰을 읽지 않는다
// (`PLAN-SoT §9 〈90〉-㉮` — 인증 세부를 한 모듈 안에 가둔다).
//
// 어디에 두는가 — `localStorage`. 무상태 서명 세션(`〈90〉-㉯`)이라 서버가 쿠키를 심을 자리가
// 없고, FE 는 정적 배포다(`frontend/README`). 새로고침으로 로그인이 풀리면 사람이 화면을
// 못 쓰므로 세션 스토리지가 아니라 로컬 스토리지를 쓴다.
//
// ⚠ **되돌림 비용이 낮은 선택이다.** 보관 위치를 쿠키로 옮기려면 이 파일과 `client.ts` 의
// 미들웨어만 바뀐다 — 화면은 `useAuth()` 밖을 모른다.

const KEY = 'colab.session.token';

type Listener = () => void;
const listeners = new Set<Listener>();

// jsdom·프라이빗 모드처럼 저장소 접근 자체가 던지는 환경이 있다. 던지면 **로그인 안 된 것**으로
// 본다 — fail-closed. 조용히 통과시키지 않는다.
function safeGet(): string | null {
  try {
    return window.localStorage.getItem(KEY);
  } catch {
    return null;
  }
}

let cached: string | null = safeGet();

export function getToken(): string | null {
  return cached;
}

export function setToken(token: string): void {
  cached = token;
  try {
    window.localStorage.setItem(KEY, token);
  } catch {
    /* 저장이 안 되면 이 탭 안에서만 산다. 그 사실을 거짓말로 덮지 않는다. */
  }
  listeners.forEach((l) => l());
}

/** 로그아웃의 실체 — 화면이 토큰을 버린다 (`〈90〉-㉳`). */
export function clearToken(): void {
  cached = null;
  try {
    window.localStorage.removeItem(KEY);
  } catch {
    /* 위와 같다 */
  }
  listeners.forEach((l) => l());
}

export function subscribe(listener: Listener): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}
