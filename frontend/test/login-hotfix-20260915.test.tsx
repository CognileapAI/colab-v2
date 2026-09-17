/**
 * 출시 직전 핫픽스 — 로그인·비밀번호 변경 화면의 막다른 자리 3건.
 *
 * ① 변경 화면이 서버 오류를 받으면 사람이 할 수 있는 일이 없었다(문구만 남고 손잡이 없음).
 * ② 새 비밀번호가 짧으면 버튼만 꺼지고 왜 꺼졌는지 말하지 않았다.
 * ③ 로그인 429 는 「잠시 뒤」라고만 해서 얼마나 기다릴지 알 수 없었다.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { App } from '../src/app/App';
import { clearToken, getToken } from '../src/auth/store';
import { setToken } from './sessionFixture';
import { account } from './factories';

const TOKEN = 'v1.eyJzdWIiOiJBIn0.c2lnbmF0dXJl';
const SESSION_KEY = 'colab.browser-session.v1';
const LONG_ENOUGH = '새로운 비밀번호 열두자';

function json(status: number, body: unknown, headers: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', ...headers },
  });
}

function renderApp() {
  return render(
    <MemoryRouter initialEntries={['/lab']}>
      <App />
    </MemoryRouter>,
  );
}

/** 첫 비밀번호 변경 화면을 세운다 — `/me/password` 응답만 시험이 고른다. */
function stubPasswordChange(passwordResponse: () => Promise<Response>) {
  vi.stubGlobal('fetch', (input: Request | string) => {
    const request = typeof input === 'string' ? new Request(input) : input;
    const path = new URL(request.url).pathname;
    if (path.endsWith('/me/password')) return passwordResponse();
    if (path.endsWith('/me-v2')) {
      return Promise.resolve(json(200, { ...account(), mustChangePassword: true }));
    }
    return Promise.resolve(new Response(null, { status: 204 }));
  });
}

async function fillAndSubmit(value: string) {
  fireEvent.change(await screen.findByTestId('new-password'), { target: { value } });
  fireEvent.change(screen.getByTestId('confirm-password'), { target: { value } });
  fireEvent.click(screen.getByTestId('change-password'));
}

beforeEach(() => {
  clearToken();
  localStorage.clear();
});

describe('비밀번호 변경 — 서버가 오류를 주면 사람이 빠져나갈 수 있다', () => {
  it('오류 응답에도 다시 로그인 버튼이 있고, 누르면 토큰을 버리고 로그인 화면으로 간다', async () => {
    setToken(TOKEN);
    stubPasswordChange(() =>
      Promise.resolve(json(400, { code: 'SAME_AS_INITIAL', message: '초기 비밀번호와 같아요.' })),
    );
    renderApp();
    await fillAndSubmit(LONG_ENOUGH);

    // 서버 문구는 그대로 보인다.
    expect(await screen.findByText('초기 비밀번호와 같아요.')).toBeInTheDocument();
    // 종전에는 이 버튼이 네트워크 끊김(outcomeUnknown) 갈래에만 있었다.
    fireEvent.click(await screen.findByTestId('password-relogin'));

    expect(await screen.findByTestId('login-account-name')).toBeInTheDocument();
    await waitFor(() => expect(getToken()).toBeNull());
    expect(localStorage.getItem(SESSION_KEY)).toBeNull();
  });

  it('세션이 끝난 401 이면 남은 세션을 저장소에서 지우고 로그인 화면으로 보낸다', async () => {
    setToken(TOKEN);
    stubPasswordChange(() =>
      Promise.resolve(json(401, { code: 'UNAUTHORIZED', message: '세션이 끝났어요.' })),
    );
    renderApp();
    await fillAndSubmit(LONG_ENOUGH);

    // 종전에는 suspended 상태의 세션이 localStorage 에 그대로 남았다.
    await waitFor(() => expect(localStorage.getItem(SESSION_KEY)).toBeNull());
    expect(getToken()).toBeNull();
    // 세션이 정리된 뒤의 화면을 잰다 — 정리 전 잠깐 뜨는 덮개 로그인 폼이 아니다.
    expect(screen.getByTestId('login-account-name')).toBeInTheDocument();
    expect(screen.queryByTestId('new-password')).toBeNull();
  });
});

describe('비밀번호 변경 — 길이가 모자라면 그렇다고 말한다', () => {
  it('9자면 규칙 문구를 보이고 버튼은 꺼져 있다', async () => {
    setToken(TOKEN);
    stubPasswordChange(() => Promise.resolve(new Response(null, { status: 204 })));
    renderApp();
    fireEvent.change(await screen.findByTestId('new-password'), { target: { value: 'a'.repeat(9) } });

    const rule = await screen.findByTestId('new-password-rule-error');
    expect(rule).toHaveAttribute('role', 'alert');
    expect(rule).toHaveTextContent('10~512자');
    expect(screen.getByTestId('change-password')).toBeDisabled();
  });

  it('10자면 규칙 문구가 없다', async () => {
    setToken(TOKEN);
    stubPasswordChange(() => Promise.resolve(new Response(null, { status: 204 })));
    renderApp();
    fireEvent.change(await screen.findByTestId('new-password'), { target: { value: 'a'.repeat(10) } });

    expect(screen.queryByTestId('new-password-rule-error')).toBeNull();
  });

  it('빈 칸에는 규칙 문구를 띄우지 않는다 — 아직 아무것도 틀리지 않았다', async () => {
    setToken(TOKEN);
    stubPasswordChange(() => Promise.resolve(new Response(null, { status: 204 })));
    renderApp();
    await screen.findByTestId('new-password');

    expect(screen.queryByTestId('new-password-rule-error')).toBeNull();
  });
});

describe('로그인 429 — 얼마나 기다릴지 말한다', () => {
  async function loginOnce(response: Response) {
    vi.stubGlobal('fetch', (input: Request | string) => {
      const request = typeof input === 'string' ? new Request(input) : input;
      const path = new URL(request.url).pathname;
      if (path.endsWith('/sessions')) return Promise.resolve(response);
      return Promise.resolve(json(401, { code: 'UNAUTHORIZED', message: '없다' }));
    });
    renderApp();
    fireEvent.change(screen.getByTestId('login-account-name'), { target: { value: 'colab' } });
    fireEvent.change(screen.getByTestId('login-password'), { target: { value: '아무거나' } });
    fireEvent.click(screen.getByTestId('login-submit'));
    return screen.findByTestId('login-error');
  }

  it('Retry-After 헤더가 있으면 그 값을 분으로 올려 말한다', async () => {
    const error = await loginOnce(
      json(429, { code: 'TOO_MANY_ATTEMPTS', message: '너무 잦다' }, { 'Retry-After': '300' }),
    );
    expect(error).toHaveTextContent('5분 뒤');
    expect(error).toHaveTextContent('맞는 비밀번호도 거절돼요');
  });

  it('본문 retryAfterSeconds 도 읽고, 남은 초는 올림한다', async () => {
    const error = await loginOnce(
      json(429, { code: 'TOO_MANY_ATTEMPTS', message: '너무 잦다', retryAfterSeconds: 90 }),
    );
    expect(error).toHaveTextContent('2분 뒤');
  });

  it('서버가 대기 시간을 주지 않으면 기본 15분으로 말한다', async () => {
    const error = await loginOnce(json(429, { code: 'TOO_MANY_ATTEMPTS', message: '너무 잦다' }));
    expect(error).toHaveTextContent('15분 뒤');
  });
});
