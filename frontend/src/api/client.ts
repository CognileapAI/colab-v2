// core-api seam 클라이언트. 타입은 전부 생성물에서 온다 — 여기서 다시 선언하지 않는다.
// 근거: frontend/README.md(생성된 타입·클라이언트만 쓴다) · CLAUDE.md §3-7
import createClient from 'openapi-fetch';
import type { paths, components } from '../generated/fe-core';
import { clearToken, getToken } from '../auth/store';

// seam 의 servers[0].url. 계약이 정한 값이라 화면이 고르지 않는다.
export const API_BASE_URL = '/api/v1';

// 오리진을 붙여 **절대 URL** 로 넘긴다. 값은 여전히 계약의 것이고, 오리진은 지금 열려 있는
// 창의 것이다 — 계약에 환경 고정 URL 을 박지 않는다는 규칙(`fe-core.yaml` `colab-no-absolute-server-url`)
// 을 지키면서, 상대 경로를 못 받는 `Request` 구현(브라우저 밖) 위에서도 같은 코드가 돈다.
function resolvedBaseUrl(): string {
  const origin = typeof window === 'undefined' ? '' : window.location?.origin;
  return origin ? new URL(API_BASE_URL, origin).toString() : API_BASE_URL;
}

export const api = createClient<paths>({
  baseUrl: resolvedBaseUrl(),
  // `fetch` 를 **부를 때** 찾는다. 기본값은 모듈이 처음 읽히는 순간의 `globalThis.fetch` 를
  // 붙잡아 두는데, 그러면 나중에 창이 그것을 바꿔도(시험 대역 포함) 이 클라이언트만 옛것을 쓴다.
  fetch: (request) => globalThis.fetch(request),
});

// 인증 첨부는 **여기 한 줄이 전부**다 (`PLAN-SoT §9 〈90〉-㉮`). 화면이 헤더를 손으로 붙이지
// 않는다 — 붙이는 자리가 여럿이면 하나가 빠진 것을 아무도 못 본다.
//
// 로그인 op(`POST /sessions`)만 예외다. 계약이 그 op 에만 `security: []` 를 적었고,
// 아직 토큰이 없는 자리라 붙일 것도 없다.
api.use({
  onRequest({ request }) {
    if (new URL(request.url).pathname.endsWith('/sessions')) return request;
    const token = getToken();
    if (token) request.headers.set('Authorization', `Bearer ${token}`);
    return request;
  },
});

// 세션 만료를 알아채는 자리도 **여기 하나**다(첨부와 같은 이유). 서버가 401 을 내면 토큰을
// 버리고, 그 사실은 `auth/store` 의 구독자 — 곧 `AuthGate` — 에게 그대로 간다. `AuthGate` 가
// `/me` 401 에 하던 일과 **같은 신호**라 새 통로를 만들지 않는다.
//
// 왜 화면이 아니라 여기인가 — 401 을 화면마다 따로 알아채면 하나가 빠졌을 때 그 화면만
// 만료된 세션으로 계속 그려진다. 실제로 카탈로그·상세·프로젝트·계보는 401 을 픽스처로
// 덮어 「로그인으로 돌아가지 않는」 화면을 만들고 있었다 (`CODE-REVIEW-20260903` 9).
//
// 로그인 op(`POST /sessions`)은 제외한다 — 거기서의 401 은 「자격이 틀렸다」이지 만료가
// 아니고, 버릴 토큰도 없다. 그 문구는 `LoginPage` 가 자기 자리에서 말한다.
api.use({
  onResponse({ request, response }) {
    if (response.status !== 401) return;
    if (new URL(request.url).pathname.endsWith('/sessions')) return;
    clearToken();
  },
});

export type Schemas = components['schemas'];
export type CurrentAccount = Schemas['CurrentAccount'];
export type PermissionSwitch = Schemas['PermissionSwitch'];
export type PermissionSwitchSet = Schemas['PermissionSwitchSet'];
