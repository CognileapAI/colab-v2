// 로그인 화면. **회원가입이 아니다** — 계정은 개발자가 심는다 (P-17 · `PLAN-SoT §9 〈90〉`).
// 정본의 로그인 화면(A-01)은 구글 계정 하나로 못 박혀 있으나 P1 보류라 1차 범위 밖이고
// (`IA_사이트맵 §0` · `README_P1`), 여기 서는 것은 그 자리에 들어갈 **접속 코드 어댑터**다.
// 수단이 바뀌면 이 파일과 `store.ts` 만 바뀐다.
import { useState } from 'react';
import { api } from '../api/client';
import { setToken } from './store';
import './login.css';

export function LoginPage() {
  const [accessCode, setAccessCode] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!accessCode.trim() || busy) return;
    setBusy(true);
    setMessage(null);
    // **가짜 진행을 만들지 않는다.** 실패는 실패로 보이고, 화면은 로그인 자리에 남는다
    // (정본 ERR-001 의 처리와 같은 모양 — `Validation_계정과_연구실_소속`).
    const { data, error, response } = await api.POST('/sessions', {
      body: { accessCode: accessCode.trim() },
    });
    setBusy(false);
    if (data) {
      setToken(data.token);
      return;
    }
    setMessage(
      response?.status === 401
        ? '심어 둔 계정이 아니에요. 접속 코드를 다시 확인해 주세요.'
        : (error?.message ?? '로그인하지 못했어요. 잠시 뒤에 다시 시도해 주세요.'),
    );
  }

  return (
    <main className="login">
      <form className="login-card" onSubmit={submit}>
        <span className="login-brand">Co-Lab</span>
        <h1 className="login-title">로그인</h1>
        <p className="login-lead">
          계정은 개발자가 만들어 드려요. 받으신 접속 코드를 넣어 주세요.
        </p>

        <label className="login-label" htmlFor="accessCode">
          접속 코드
        </label>
        <input
          id="accessCode"
          className="login-input"
          type="password"
          autoComplete="off"
          value={accessCode}
          onChange={(e) => setAccessCode(e.target.value)}
          data-testid="login-access-code"
        />

        <button
          type="submit"
          className="login-submit"
          disabled={busy || !accessCode.trim()}
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
