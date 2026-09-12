import { useState } from 'react';
import { api } from '../api/client';
import { getSession, getSessionEpoch, setSession } from './store';
import { logoutCurrent } from './sessionCoordinator';
import { validNewPassword } from './passwordRules';
import { useNavigate } from 'react-router-dom';
import './login.css';
export function PasswordChangePage() {
  const navigate=useNavigate();
  const [newPassword,setNew]=useState(''); const [confirm,setConfirm]=useState('');
  const [message,setMessage]=useState<string|null>(null); const [busy,setBusy]=useState(false);
  const [outcomeUnknown,setOutcomeUnknown]=useState(false);
  async function submit(event:React.FormEvent){event.preventDefault(); if(busy||!validNewPassword(newPassword)||newPassword!==confirm)return;
    const startedSession=getSession(); const startedEpoch=getSessionEpoch();
    if(!startedSession){setMessage('로그인 상태를 다시 확인해 주세요.');return;}
    setBusy(true);setMessage(null);setOutcomeUnknown(false);
    try {
      const {data,error}=await api.PUT('/me/password',{body:{newPassword}});
      if(data){
        const current=getSession();
        if(!current||current.sessionId!==startedSession.sessionId||
          current.token!==startedSession.token||getSessionEpoch()!==startedEpoch){
          setMessage('로그인 상태가 바뀌어 이전 변경 결과를 적용하지 않았어요.');return;
        }
        setSession({...data,revocationToken:current.revocationToken});
        navigate('/lab',{replace:true});return;
      }
      setMessage(error?.message??'비밀번호를 변경하지 못했어요.');
    } catch {
      setOutcomeUnknown(true);
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
    {confirm&&newPassword!==confirm?<p className="login-error" role="alert">비밀번호가 서로 달라요.</p>:null}
    <p id="new-password-help" className="login-label">10~512자로 입력하세요. 영문·숫자·특수문자 조합은 필수가 아니며, 초기 비밀번호와 달라야 해요.</p>
    <button className="login-submit" disabled={busy||!validNewPassword(newPassword)||newPassword!==confirm} data-testid="change-password">{busy?'변경하는 중…':'비밀번호 변경'}</button>
    {message?<p className="login-error" role="alert">{message}</p>:null}
    {outcomeUnknown?<button type="button" className="login-submit login-secondary" data-testid="password-relogin" onClick={()=>void logoutCurrent()}>다시 로그인</button>:null}
  </form></main>;
}
