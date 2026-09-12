// 로그인 화면. **회원가입이 아니다** — 계정은 개발자가 심는다 (P-17 · `PLAN-SoT §9 〈90〉`).
// 정본의 로그인 화면(A-01)은 구글 계정 하나로 못 박혀 있으나 P1 보류라 1차 범위 밖이고
// (`IA_사이트맵 §0` · `README_P1`), 여기 서는 것은 그 자리에 들어갈 **계정·비밀번호 어댑터**다
// (`PLAN-SoT §9 〈108〉`). 수단이 바뀌면 이 파일과 `store.ts` 만 바뀐다.
//
// ⚠ **정본은 비밀번호 로그인을 명시적으로 뺐다**(`PRD_계정과_연구실_소속 §5.2`). 어긋남을
// 감추지 않고 `〈108〉-㉮` 에 Ted 판정 사안으로 등재해 두었다.
import { useState } from 'react';
import { api } from '../api/client';
import { transitionTo } from './sessionCoordinator';
import { enqueueRevocation, flushLogoutQueue } from './logoutQueue';
import type { BrowserSession } from './store';
import { discardAccountWorkAcrossTabs, getCurrentAccountId, hasAccountWork } from './workGuard';
import {
  getLogoutQueueStatus,
  subscribeLogoutQueueStatus,
} from './logoutQueue';
import { useSyncExternalStore } from 'react';
import './login.css';
import { ThemeSwitcher } from '../shell/ThemeSwitcher';

export function LoginPage() {
  const logoutStatus = useSyncExternalStore(
    subscribeLogoutQueueStatus,
    getLogoutQueueStatus,
    getLogoutQueueStatus,
  );
  const [accountName, setAccountName] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!accountName.trim() || !password || busy) return;
    setBusy(true);
    setMessage(null);
    let candidate: BrowserSession | null = null;
    const retireCandidate = () => {
      if (!candidate) return;
      enqueueRevocation(candidate);
      candidate = null;
      void flushLogoutQueue();
    };
    // **가짜 진행을 만들지 않는다.** 실패는 실패로 보이고, 화면은 로그인 자리에 남는다
    // (정본 ERR-001 의 처리와 같은 모양 — `Validation_계정과_연구실_소속`).
    try {
      const { data, error, response } = await api.POST('/sessions', {
        body: { accountName: accountName.trim(), password },
      });
      if (data) {
        candidate = data;
        const verified = await api.GET('/me', {
          headers: { Authorization: 'Bearer ' + data.token },
        });
        if (!verified.data) {
          retireCandidate();
          setMessage('로그인 정보를 확인하지 못했어요. 잠시 뒤에 다시 시도해 주세요.');
          return;
        }
        const previousAccount = getCurrentAccountId();
        if (previousAccount && previousAccount !== verified.data.accountId && hasAccountWork(previousAccount)) {
          const discard = window.confirm(
            '다른 계정으로 로그인하면 작성 중인 작업을 버려야 해요. 작업을 버리고 로그인할까요?',
          );
          if (!discard) {
            retireCandidate();
            setMessage('작성 중인 작업을 유지했어요.');
            return;
          }
          const discarded = await discardAccountWorkAcrossTabs(previousAccount, false);
          if (!discarded) {
            retireCandidate();
            setMessage('다른 탭의 작업을 폐기하지 못했어요. 해당 탭을 확인한 뒤 다시 시도해 주세요.');
            return;
          }
        }
        const accepted = await transitionTo(data, verified.data.accountId);
        candidate = null;
        if (!accepted) {
          setMessage('다른 탭의 작업을 확인하지 못했어요. 해당 탭에서 작업을 끝내거나 취소한 뒤 다시 시도해 주세요.');
        }
        return;
      }
      if (response?.status === 401) {
        setMessage('계정 또는 비밀번호가 맞지 않아요. 비밀번호 변경 중 연결이 끊겼다면 기존 초기 비밀번호도 직접 시도해 보세요.');
        setPassword('');
        return;
      }
      if (response?.status === 429) {
        setMessage('로그인 시도가 너무 잦아요. 잠시 뒤에 다시 시도해 주세요.');
        return;
      }
      setMessage(error?.message ?? '로그인하지 못했어요. 잠시 뒤에 다시 시도해 주세요.');
    } catch {
      retireCandidate();
      setMessage('서버에 연결하지 못했어요. 잠시 뒤에 직접 다시 시도해 주세요.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="login">
      <div className="login-theme"><ThemeSwitcher /></div>
      <form className="login-card" onSubmit={submit}>
        <span className="login-brand">Co-Lab</span>
        <h1 className="login-title">로그인</h1>
        <p className="login-lead">
          운영자에게 받은 이메일과 초기 비밀번호를 넣어 주세요.
        </p>

        <label className="login-label" htmlFor="accountName">
          이메일
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
        {logoutStatus === 'server-unconfirmed' ? (
          <p className="login-error" role="status">이 브라우저에서는 로그아웃됐지만 서버 종료는 아직 확인 중이에요.</p>
        ) : null}
        {logoutStatus === 'storage-unavailable' ? (
          <p className="login-error" role="status">이 브라우저에서는 로그아웃됐습니다. 앱을 닫으면 서버 종료 재시도를 이어갈 수 없어요.</p>
        ) : null}
        {logoutStatus === 'manual-check' ? (
          <p className="login-error" role="status">서버 종료 요청을 확인하지 못했어요. 원래 로그인 시각부터 12시간 뒤에는 만료됩니다.</p>
        ) : null}
      </form>
    </main>
  );
}
