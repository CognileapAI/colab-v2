// 로그인 화면. **회원가입이 아니다** — 계정은 개발자가 심는다 (P-17 · `PLAN-SoT §9 〈90〉`).
// 정본의 로그인 화면(A-01)은 구글 계정 하나로 못 박혀 있으나 P1 보류라 1차 범위 밖이고
// (`IA_사이트맵 §0` · `README_P1`), 여기 서는 것은 그 자리에 들어갈 **계정·비밀번호 어댑터**다
// (`PLAN-SoT §9 〈108〉`). 수단이 바뀌면 이 파일과 `store.ts` 만 바뀐다.
//
// ⚠ **정본은 비밀번호 로그인을 명시적으로 뺐다**(`PRD_계정과_연구실_소속 §5.2`). 어긋남을
// 감추지 않고 `〈108〉-㉮` 에 Ted 판정 사안으로 등재해 두었다.
import { useState } from 'react';
import { api } from '../api/client';
import { setToken } from './store';
import './login.css';

export function LoginPage() {
  const [accountName, setAccountName] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!accountName.trim() || !password || busy) return;
    setBusy(true);
    setMessage(null);
    // **가짜 진행을 만들지 않는다.** 실패는 실패로 보이고, 화면은 로그인 자리에 남는다
    // (정본 ERR-001 의 처리와 같은 모양 — `Validation_계정과_연구실_소속`).
    const { data, error, response } = await api.POST('/sessions', {
      body: { accountName: accountName.trim(), password },
    });
    setBusy(false);
    if (data) {
      setToken(data.token);
      return;
    }
    // **어느 칸이 틀렸는지 말하지 않는다** — 계정의 존재 여부가 화면으로 새지 않게 (`〈108〉-㉮`).
    if (response?.status === 401) {
      setMessage('계정 또는 비밀번호가 맞지 않아요.');
      setPassword('');
      return;
    }
    if (response?.status === 429) {
      setMessage('로그인 시도가 너무 잦아요. 잠시 뒤에 다시 시도해 주세요.');
      return;
    }
    setMessage(error?.message ?? '로그인하지 못했어요. 잠시 뒤에 다시 시도해 주세요.');
  }

  return (
    <main className="login">
      <form className="login-card" onSubmit={submit}>
        <span className="login-brand">Co-Lab</span>
        <h1 className="login-title">로그인</h1>
        <p className="login-lead">
          계정은 개발자가 만들어 드려요. 받으신 계정과 비밀번호를 넣어 주세요.
        </p>

        <label className="login-label" htmlFor="accountName">
          계정
        </label>
        <input
          id="accountName"
          className="login-input"
          type="text"
          autoComplete="username"
          value={accountName}
          onChange={(e) => setAccountName(e.target.value)}
          data-testid="login-account-name"
        />

        <label className="login-label login-label-spaced" htmlFor="password">
          비밀번호
        </label>
        <input
          id="password"
          className="login-input"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          data-testid="login-password"
        />

        <button
          type="submit"
          className="login-submit"
          disabled={busy || !accountName.trim() || !password}
          data-testid="login-submit"
        >
          {busy ? '확인하는 중…' : '들어가기'}
        </button>

        {message ? (
          <p className="login-error" role="alert" data-testid="login-error">
            {message}
          </p>
        ) : null}
      </form>
    </main>
  );
}
