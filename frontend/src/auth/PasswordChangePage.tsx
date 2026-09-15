import { useState } from 'react';
import { api } from '../api/client';
import { getSession, getSessionEpoch, setSession } from './store';
import { logoutCurrent } from './sessionCoordinator';
import { validNewPassword } from './passwordRules';
import { useNavigate } from 'react-router-dom';
import './login.css';
// 길이 규칙의 값은 `passwordRules.ts` 가 정한다. 화면은 그 값을 **한 곳**에서만 글로 옮긴다 —
// 안내문과 오류 문구가 서로 다른 숫자를 말하는 일이 생기지 않게 한다.
const lengthRule = '10~512자';
export function PasswordChangePage() {
  const navigate=useNavigate();
  const [newPassword,setNew]=useState(''); const [confirm,setConfirm]=useState('');
  const [message,setMessage]=useState<string|null>(null); const [busy,setBusy]=useState(false);
  // 다시 로그인할 자리가 필요한 상태 — 응답을 못 받은 경우와 서버가 거절한 경우 둘 다다.
  const [canRelogin,setCanRelogin]=useState(false);
  // 빈 칸은 아직 아무것도 틀리지 않은 상태다. 입력이 있는데 규칙에 못 미칠 때만 말한다.
  const tooShort=newPassword!==''&&!validNewPassword(newPassword);
  async function submit(event:React.FormEvent){event.preventDefault(); if(busy||!validNewPassword(newPassword)||newPassword!==confirm)return;
    const startedSession=getSession(); const startedEpoch=getSessionEpoch();
    if(!startedSession){setMessage('로그인 상태를 다시 확인해 주세요.');return;}
    setBusy(true);setMessage(null);setCanRelogin(false);
    try {
      const {data,error,response}=await api.PUT('/me/password',{body:{newPassword}});
      if(data){
        const current=getSession();
        if(!current||current.sessionId!==startedSession.sessionId||
          current.token!==startedSession.token||getSessionEpoch()!==startedEpoch){
          setMessage('로그인 상태가 바뀌어 이전 변경 결과를 적용하지 않았어요.');return;
        }
        setSession({...data,revocationToken:current.revocationToken});
        navigate('/lab',{replace:true});return;
      }
      // 서버가 거절했다. 종전에는 문구만 남고 이 화면에서 나갈 손잡이가 없었다.
      setMessage(error?.message??'비밀번호를 변경하지 못했어요.');
      setCanRelogin(true);
      // 401 은 세션이 이미 끝난 것이다 — 이 화면 자체가 로그인 화면으로 교체되므로 버튼을
      // 누를 자리가 남지 않는다. 저장소에 남은 세션을 여기서 그대로 정리한다.
      if(response?.status===401) void logoutCurrent();
    } catch {
      setCanRelogin(true);
      setMessage('변경 결과를 확인하지 못했어요. 자동으로 다시 보내지 않았습니다. 새 비밀번호로 먼저 로그인하고, 거절되면 기존 초기 비밀번호를 직접 시도해 주세요.');
    } finally { setBusy(false); }
  }
  return <main className="login"><form className="login-card" onSubmit={submit}>
    <span className="login-brand">Co-Lab</span><h1 className="login-title">비밀번호 변경</h1>
    <p className="login-lead">처음 로그인하셨습니다. 사용할 새 비밀번호로 바꿔 주세요.</p>
    <label className="login-label" htmlFor="new-password">새 비밀번호</label>
    <input id="new-password" aria-describedby="new-password-help" className="login-input" type="password" autoComplete="new-password" value={newPassword} onChange={e=>setNew(e.target.value)} data-testid="new-password"/>
    <label className="login-label login-label-spaced" htmlFor="confirm-password">새 비밀번호 확인</label>
    <input id="confirm-password" className="login-input" type="password" autoComplete="new-password" value={confirm} onChange={e=>setConfirm(e.target.value)} data-testid="confirm-password"/>
    {tooShort?<p className="login-error" role="alert" data-testid="new-password-rule-error">비밀번호는 {lengthRule}여야 해요.</p>:null}
    {confirm&&newPassword!==confirm?<p className="login-error" role="alert">비밀번호가 서로 달라요.</p>:null}
    <p id="new-password-help" className="login-label">{lengthRule}로 입력하세요. 영문·숫자·특수문자 조합은 필수가 아니며, 초기 비밀번호와 달라야 해요.</p>
    <button className="login-submit" disabled={busy||!validNewPassword(newPassword)||newPassword!==confirm} data-testid="change-password">{busy?'변경하는 중…':'비밀번호 변경'}</button>
    {message?<p className="login-error" role="alert">{message}</p>:null}
    {canRelogin?<button type="button" className="login-submit login-secondary" data-testid="password-relogin" onClick={()=>void logoutCurrent()}>다시 로그인</button>:null}
  </form></main>;
}
