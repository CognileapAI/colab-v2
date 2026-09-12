import { useEffect,useRef,useState } from 'react';
import { api } from '../api/client';
import { useAccount } from '../permission/session';
import '../auth/login.css';
import { validNewPassword } from '../auth/passwordRules';
import { useWorkProtection } from '../auth/useWorkProtection';
export function AccountAdminPage(){
 const account=useAccount(); const [options,setOptions]=useState<{labs:{labId:string;name:string}[];roles:('교수'|'연구원')[]}>();
 const [message,setMessage]=useState<string|null>(null);
 const [busy,setBusy]=useState(false);
 const [dirty,setDirty]=useState(false);
 const formRef=useRef<HTMLFormElement|null>(null);
 useWorkProtection('account-admin',{dirty,inFlight:busy,discard:()=>{formRef.current?.reset();setDirty(false);}});
 useEffect(()=>{if(account?.canManageServiceAccounts)void api.GET('/admin/account-options').then(({data})=>data&&setOptions(data));},[account]);
 if(!account?.canManageServiceAccounts)return <main><h1>계정 관리</h1><p>서비스 운영자만 사용할 수 있어요.</p></main>;
 return <main className="login"><section className="login-card account-card"><span className="login-brand">Co-Lab</span><h1 className="login-title">서비스 계정 추가</h1><p className="login-lead">기존 연구실과 역할을 지정하고 초기 비밀번호를 사용자에게 전달하세요.</p>
 <form ref={formRef} className="account-form" onInput={()=>setDirty(true)} onSubmit={async e=>{e.preventDefault();if(busy)return;setMessage(null);const form=e.currentTarget;const f=new FormData(form);
  const initialPassword=String(f.get('initialPassword'));
  if(!validNewPassword(initialPassword)){setMessage('초기 비밀번호는 10~512자로 입력해 주세요.');return;}
  setBusy(true);try{
   const {data,error}=await api.POST('/admin/accounts',{body:{email:String(f.get('email')),name:String(f.get('name')),labId:String(f.get('labId')),role:String(f.get('role')) as '교수'|'연구원',initialPassword}});
   setMessage(data?data.email+' 계정을 추가했어요.':(error?.message??'계정을 추가하지 못했어요.'));if(data){form.reset();setDirty(false);}
  }catch{setMessage('서버에 연결하지 못했어요. 계정이 추가됐는지 확인한 뒤 다시 시도해 주세요.');}finally{setBusy(false);}}}>
 <label className="login-label">이름<input className="login-input" name="name" required/></label><label className="login-label">이메일<input className="login-input" name="email" type="email" required/></label>
 <label className="login-label">연구실<select className="login-input" name="labId" required>{options?.labs.map(l=><option key={l.labId} value={l.labId}>{l.name}</option>)}</select></label>
 <label className="login-label">역할<select className="login-input" name="role" required>{options?.roles.map(r=><option key={r}>{r}</option>)}</select></label>
 <label className="login-label">초기 비밀번호<input className="login-input" name="initialPassword" aria-describedby="initial-password-help" type="password" required/></label>
 <p id="initial-password-help" className="login-label">10~512자로 입력하세요. 영문·숫자·특수문자 조합은 필수가 아니에요. 사용자는 첫 로그인 때 비밀번호를 변경해야 해요.</p>
 <button className="login-submit" type="submit" disabled={busy}>{busy?'추가하는 중…':'계정 추가'}</button></form>{message?<p className="account-status" role="status">{message}</p>:null}</section></main>;
}
