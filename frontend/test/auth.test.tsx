/**
 * FE 인증 모듈 (`PLAN-SoT §9 〈90〉` · WU-AUTH).
 *
 * **red 를 먼저 봤다** — `src/auth/` 가 없던 시점에 이 파일은 모듈 해석 실패로 red 였다.
 *
 * 여기서 증명하는 것 — 미인증이면 로그인 화면 · 로그인 성공이면 앱 · 실패는 정직한 표시 ·
 * 요청에 토큰이 자동으로 붙음 · 로그인 op 에는 안 붙음 · 401 이면 토큰을 버림 · 로그아웃.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { App } from '../src/app/App';
import { clearToken, getToken, setToken } from '../src/auth/store';
import { api } from '../src/api/client';
import { account } from './factories';

// 실제 토큰과 같은 모양(ASCII base64url) 이다 — 헤더 값은 ByteString 이라 한글이 들어갈 수 없다.
const TOKEN = 'v1.eyJzdWIiOiJBIn0.c2lnbmF0dXJl';

type Call = { url: string; auth: string | null; method: string };
let calls: Call[] = [];

function stubFetch(handler: (url: string) => Response) {
  vi.stubGlobal('fetch', (input: Request | string) => {
    const request = typeof input === 'string' ? new Request(input) : input;
    calls.push({
      url: new URL(request.url).pathname,
      auth: request.headers.get('Authorization'),
      method: request.method,
    });
    return Promise.resolve(handler(request.url));
  });
}

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

function renderApp() {
  return render(
    <MemoryRouter initialEntries={['/lab']}>
      <App />
    </MemoryRouter>,
  );
}

beforeEach(() => {
  calls = [];
  clearToken();
  // 매 시험이 자기 핸들러로 덮어쓴다. **fetch 를 원래대로 돌려놓지 않는다** —
  // 시험이 끝난 뒤 늦게 도착하는 effect 가 실제 네트워크를 부르면 그 실패는 원인을 못 찾는다.
  stubFetch(() => json(401, { code: 'UNAUTHORIZED', message: '기본 거부' }));
});

afterEach(() => {
  clearToken();
});

describe('문지기 — 인증 세부는 한 곳에만 있다', () => {
  it('토큰이 없으면 로그인 화면이고 GNB 가 없다', () => {
    stubFetch(() => json(401, { code: 'UNAUTHORIZED', message: '없다' }));
    renderApp();
    expect(screen.getByTestId('login-account-name')).toBeInTheDocument();
    // 로그인 전에는 상단 내비를 보이지 않는다 (정본 UI-006).
    expect(screen.queryByTestId('gnb-avatar')).toBeNull();
  });

  it('토큰이 없으면 /me 를 부르지 않는다', () => {
    stubFetch(() => json(401, { code: 'UNAUTHORIZED', message: '없다' }));
    renderApp();
    expect(calls.filter((c) => c.url.endsWith('/me'))).toHaveLength(0);
  });

  it('토큰이 있으면 /me 응답으로 앱을 그린다', async () => {
    setToken(TOKEN);
    stubFetch((url) =>
      url.endsWith('/me') ? json(200, account()) : json(200, {}),
    );
    renderApp();
    expect(await screen.findByTestId('gnb-avatar')).toBeInTheDocument();
  });

  it('/me 가 401 이면 토큰을 버리고 로그인 화면으로 돌아간다', async () => {
    setToken(TOKEN);
    stubFetch(() => json(401, { code: 'UNAUTHORIZED', message: '만료' }));
    renderApp();
    expect(await screen.findByTestId('login-account-name')).toBeInTheDocument();
    expect(getToken()).toBeNull();
  });
});

describe('요청 첨부 — 화면이 헤더를 손으로 붙이지 않는다', () => {
  it('토큰이 있으면 모든 요청에 Bearer 가 붙는다', async () => {
    setToken(TOKEN);
    stubFetch(() => json(200, account()));
    await api.GET('/me');
    expect(calls.at(-1)?.auth).toBe(`Bearer ${TOKEN}`);
  });

  it('로그인 op 에는 붙지 않는다 — 계약이 `security: []` 다', async () => {
    setToken(TOKEN);
    stubFetch(() => json(201, { token: 'x', expiresAt: '2026-08-27T00:00:00Z' }));
    await api.POST('/sessions', { body: { accountName: 'colab', password: 'x' } });
    expect(calls.at(-1)?.url).toBe('/api/v1/sessions');
    expect(calls.at(-1)?.auth).toBeNull();
  });

  it('토큰이 없으면 헤더를 만들어 내지 않는다', async () => {
    stubFetch(() => json(401, { code: 'UNAUTHORIZED', message: '없다' }));
    await api.GET('/me');
    expect(calls.at(-1)?.auth).toBeNull();
  });
});

describe('로그인 화면', () => {
  it('성공하면 토큰을 보관하고 앱으로 넘어간다', async () => {
    stubFetch((url) => {
      if (url.endsWith('/sessions')) {
        return json(201, { token: TOKEN, expiresAt: '2026-08-27T00:00:00Z' });
      }
      return json(200, account());
    });
    renderApp();
    // 새 의존성을 들이지 않는다 — 이미 있는 fireEvent 로 친다 (`test/catalog.test.tsx` 선례).
    fireEvent.change(screen.getByTestId('login-account-name'), { target: { value: 'colab' } });
    fireEvent.change(screen.getByTestId('login-password'), { target: { value: '시험-비밀번호' } });
    fireEvent.click(screen.getByTestId('login-submit'));
    await waitFor(() => expect(getToken()).toBe(TOKEN));
    expect(await screen.findByTestId('gnb-avatar')).toBeInTheDocument();
  });

  it('실패하면 로그인 자리에 남고 사유를 그대로 말한다 — 가짜 진행이 없다', async () => {
    stubFetch(() => json(401, { code: 'UNAUTHORIZED', message: '심어 둔 계정이 아니다.' }));
    renderApp();
    fireEvent.change(screen.getByTestId('login-account-name'), { target: { value: 'colab' } });
    fireEvent.change(screen.getByTestId('login-password'), { target: { value: '틀린-비밀번호' } });
    fireEvent.click(screen.getByTestId('login-submit'));
    expect(await screen.findByTestId('login-error')).toBeInTheDocument();
    expect(getToken()).toBeNull();
    expect(screen.getByTestId('login-account-name')).toBeInTheDocument();
  });

  it('빈 칸으로는 보낼 수 없다', () => {
    stubFetch(() => json(401, {}));
    renderApp();
    expect(screen.getByTestId('login-submit')).toBeDisabled();
    // 계정만 채워도 아직 못 보낸다 — 두 칸이 짝이다.
    fireEvent.change(screen.getByTestId('login-account-name'), { target: { value: 'colab' } });
    expect(screen.getByTestId('login-submit')).toBeDisabled();
  });

  it('실패해도 어느 칸이 틀렸는지 말하지 않는다 — 계정 존재가 새지 않는다', async () => {
    stubFetch(() => json(401, { code: 'UNAUTHORIZED', message: '심어 둔 계정이 아니다.' }));
    renderApp();
    fireEvent.change(screen.getByTestId('login-account-name'), { target: { value: '없는계정' } });
    fireEvent.change(screen.getByTestId('login-password'), { target: { value: '아무거나' } });
    fireEvent.click(screen.getByTestId('login-submit'));
    expect(await screen.findByTestId('login-error')).toHaveTextContent('계정 또는 비밀번호');
  });

  it('429 는 잠긴 것으로 말한다 — 틀린 것과 섞지 않는다', async () => {
    stubFetch(() => json(429, { code: 'TOO_MANY_ATTEMPTS', message: '너무 잦다' }));
    renderApp();
    fireEvent.change(screen.getByTestId('login-account-name'), { target: { value: 'colab' } });
    fireEvent.change(screen.getByTestId('login-password'), { target: { value: '아무거나' } });
    fireEvent.click(screen.getByTestId('login-submit'));
    expect(await screen.findByTestId('login-error')).toHaveTextContent('시도가 너무 잦아요');
  });

  it('비밀번호를 화면에 남기지 않는다 — 실패하면 칸을 비운다', async () => {
    stubFetch(() => json(401, { code: 'UNAUTHORIZED', message: '아니다' }));
    renderApp();
    fireEvent.change(screen.getByTestId('login-account-name'), { target: { value: 'colab' } });
    fireEvent.change(screen.getByTestId('login-password'), { target: { value: '틀린-비밀번호' } });
    fireEvent.click(screen.getByTestId('login-submit'));
    await screen.findByTestId('login-error');
    expect(screen.getByTestId('login-password')).toHaveValue('');
  });
});

describe('로그아웃', () => {
  it('endSession 을 부르고 토큰을 버린다', async () => {
    setToken(TOKEN);
    stubFetch((url) =>
      url.endsWith('/sessions/current') ? new Response(null, { status: 204 }) : json(200, account()),
    );
    renderApp();
    fireEvent.click(await screen.findByTestId('gnb-logout'));
    await waitFor(() => expect(getToken()).toBeNull());
    expect(calls.some((c) => c.method === 'DELETE' && c.url.endsWith('/sessions/current'))).toBe(
      true,
    );
    expect(await screen.findByTestId('login-account-name')).toBeInTheDocument();
  });
});
