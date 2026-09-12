import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, expect, test, vi } from 'vitest';
import { MemoryRouter, useLocation } from 'react-router-dom';
import { PasswordChangePage } from '../src/auth/PasswordChangePage';
import { AccountAdminPage } from '../src/routes/AccountAdminPage';
import { SessionProvider } from '../src/permission/session';
import { getSession, setSession } from '../src/auth/store';
import { readDraft } from '../src/auth/draftVault';
const LAB='0000000000000000000000000A';
beforeEach(()=>vi.restoreAllMocks());
function json(body:unknown,status=200){return new Response(JSON.stringify(body),{status,headers:{'content-type':'application/json'}});}
function Location(){return <output data-testid="location">{useLocation().pathname}</output>;}
test('첫 로그인 사용자가 새 비밀번호를 제출하면 새 토큰을 저장하고 연구실로 이동한다',async()=>{
 setSession({token:'initial-token',sessionId:'00000000000000000000000S01',expiresAt:'2099-01-01T00:00:00Z',revocationToken:'revoke-cap'});
 const fetch=vi.spyOn(globalThis,'fetch').mockResolvedValue(new Response(JSON.stringify({token:'new-db-token',expiresAt:'2099-01-01T00:00:00Z',sessionId:'00000000000000000000000S01'}),{status:200,headers:{'content-type':'application/json'}}));
 render(<MemoryRouter initialEntries={['/account-admin']}><PasswordChangePage/><Location/></MemoryRouter>);
 fireEvent.change(screen.getByTestId('new-password'),{target:{value:'new-password-123'}});
 fireEvent.change(screen.getByTestId('confirm-password'),{target:{value:'new-password-123'}});
 fireEvent.click(screen.getByTestId('change-password'));
 await waitFor(()=>expect(fetch).toHaveBeenCalled());
 const passwordRequest=fetch.mock.calls[0]![0] as Request;
 expect(JSON.parse(await passwordRequest.clone().text())).toEqual({newPassword:'new-password-123'});
 expect(getSession()?.token).toBe('new-db-token');
 expect(getSession()?.revocationToken).toBe('revoke-cap');
 expect(screen.getByTestId('location')).toHaveTextContent('/lab');
});
test('새 비밀번호 확인이 다르면 제출하지 않는다',()=>{
 const fetch=vi.spyOn(globalThis,'fetch');
 render(<MemoryRouter><PasswordChangePage/></MemoryRouter>);
 fireEvent.change(screen.getByTestId('new-password'),{target:{value:'new-password-123'}});
 fireEvent.change(screen.getByTestId('confirm-password'),{target:{value:'different-password'}});
 expect(screen.getByTestId('change-password')).toBeDisabled();
 expect(fetch).not.toHaveBeenCalled();
});
test('비밀번호 변경 응답이 끊기면 자동 재전송 없이 결과 불명을 안내한다',async()=>{
 setSession({token:'initial-token',sessionId:'00000000000000000000000S01',expiresAt:'2099-01-01T00:00:00Z',revocationToken:'revoke-cap'});
 const fetch=vi.spyOn(globalThis,'fetch').mockRejectedValue(new TypeError('offline'));
 render(<MemoryRouter><PasswordChangePage/></MemoryRouter>);
 fireEvent.change(screen.getByTestId('new-password'),{target:{value:'new-password-123'}});
 fireEvent.change(screen.getByTestId('confirm-password'),{target:{value:'new-password-123'}});
 fireEvent.click(screen.getByTestId('change-password'));
 expect(await screen.findByRole('alert')).toHaveTextContent('변경 결과를 확인하지 못했어요');
 expect(fetch).toHaveBeenCalledTimes(1);
 expect(screen.getByTestId('change-password')).toBeEnabled();
});
test('서비스 운영자가 기존 연구실과 역할로 계정을 추가한다',async()=>{
 // 화면이 목록도 함께 부르므로 **호출 순서가 아니라 경로**로 답한다.
 const fetch=vi.spyOn(globalThis,'fetch').mockImplementation(async input=>{
  const request=input as Request; const url=new URL(request.url);
  if(url.pathname.endsWith('/admin/account-options'))return json({labs:[{labId:LAB,name:'A 연구실'}],roles:['교수','연구원']});
  if(url.pathname.endsWith('/admin/accounts')&&request.method==='GET')return json({accounts:[]});
  if(url.pathname.endsWith('/admin/accounts')&&request.method==='POST')return json({accountId:'000000000000000000000000A2',email:'new@example.com',name:'새 사용자',labId:LAB,role:'교수'},201);
  return json({message:'모의하지 않은 경로'},500);
 });
 render(<SessionProvider account={{accountId:'00000000000000000000000AP1',name:'운영자',email:'op@example.com',role:'교수',permissions:{},labId:LAB,labName:'A 연구실',canManageServiceAccounts:true,mustChangePassword:false}}><AccountAdminPage/></SessionProvider>);
 const form=within(await screen.findByTestId('account-create'));
 await within(form.getByLabelText('연구실')).findByRole('option',{name:'A 연구실'});
 fireEvent.change(form.getByLabelText('이름'),{target:{value:'새 사용자'}});
 fireEvent.change(form.getByLabelText('이메일'),{target:{value:'new@example.com'}});
 fireEvent.change(form.getByLabelText('초기 비밀번호'),{target:{value:'initial-password'}});
 fireEvent.click(form.getByRole('button',{name:'계정 추가'}));
 await screen.findByText('new@example.com 계정을 추가했어요.');
 const request=fetch.mock.calls.map(call=>call[0] as Request).find(call=>call.method==='POST')!;
 expect(JSON.parse(await request.clone().text())).toMatchObject({email:'new@example.com',labId:LAB,role:'교수'});
 expect(screen.queryByText('initial-password')).not.toBeInTheDocument();
});

// ═══════════════ 운영자 백오피스 — 목록 · 재설정 · 비활성화 ═══════════════
const LAB_B='0000000000000000000000000B';
const ACC_1='000000000000000000000000A1';
const ACC_2='00000000000000000000000BP1';
const OPTIONS={labs:[{labId:LAB,name:'A 연구실'},{labId:LAB_B,name:'B 연구실'}],roles:['교수','연구원']};
const ACCOUNTS=[
 {accountId:ACC_1,email:'one@example.com',name:'한 사람',labId:LAB,labName:'A 연구실',role:'연구원',status:'active',lastLoginAt:'2026-09-11T02:03:04Z'},
 {accountId:ACC_2,email:'two@example.com',name:'두 사람',labId:LAB_B,labName:'B 연구실',role:'교수',status:'inactive',lastLoginAt:null},
];
const OPERATOR={accountId:'00000000000000000000000AP1',name:'운영자',email:'op@example.com',role:'교수' as const,permissions:{},labId:LAB,labName:'A 연구실',canManageServiceAccounts:true,mustChangePassword:false};

/** 호출 순서가 아니라 **경로**로 답한다 — 순서 의존 모의는 화면을 고칠 때마다 거짓으로 깨진다. */
function routedFetch(over?:(url:URL,request:Request)=>Response|undefined){
 return vi.spyOn(globalThis,'fetch').mockImplementation(async input=>{
  const request=input as Request; const url=new URL(request.url);
  const custom=over?.(url,request); if(custom)return custom;
  if(url.pathname.endsWith('/admin/account-options'))return json(OPTIONS);
  if(url.pathname.endsWith('/admin/accounts')&&request.method==='GET')return json({accounts:ACCOUNTS});
  if(url.pathname.endsWith('/password-reset'))return json({accountId:ACC_1,mustChangePassword:true});
  if(url.pathname.endsWith('/status'))return json({accountId:ACC_2,status:'active'});
  return json({message:'모의하지 않은 경로'},500);
 });
}
function renderAdmin(){return render(<SessionProvider account={OPERATOR}><AccountAdminPage/></SessionProvider>);}
const listUrls=(fetch:ReturnType<typeof routedFetch>)=>fetch.mock.calls
 .map(call=>new URL((call[0] as Request).url))
 .filter(url=>url.pathname.endsWith('/admin/accounts')&&!url.pathname.includes('password'));

test('운영자가 전 연구실 계정 목록을 여섯 열로 본다',async()=>{
 routedFetch();
 renderAdmin();
 const table=await screen.findByRole('table',{name:'계정 목록'});
 const headers=within(table).getAllByRole('columnheader').map(cell=>cell.textContent);
 expect(headers).toEqual(['이메일','이름','역할','연구실','상태','최근 로그인','']);
 const first=within(table).getByRole('row',{name:/one@example.com/});
 expect(first).toHaveTextContent('한 사람');
 expect(first).toHaveTextContent('연구원');
 expect(first).toHaveTextContent('A 연구실');
 expect(first).toHaveTextContent('2026-09-11');
 const second=within(table).getByRole('row',{name:/two@example.com/});
 expect(second).toHaveTextContent('B 연구실');
 expect(second).toHaveTextContent('기록 없음');
 expect(within(second).getByRole('button',{name:'재활성화'})).toBeInTheDocument();
 expect(within(first).getByRole('button',{name:'비활성화'})).toBeInTheDocument();
});

test('목록 필터 네 가지가 서버 질의 인자로 전달된다',async()=>{
 const fetch=routedFetch();
 renderAdmin();
 await screen.findByRole('table',{name:'계정 목록'});
 const filters=screen.getByRole('group',{name:'계정 목록 필터'});
 fireEvent.change(within(filters).getByLabelText('연구실'),{target:{value:LAB_B}});
 await waitFor(()=>expect(listUrls(fetch).at(-1)!.searchParams.get('labId')).toBe(LAB_B));
 fireEvent.change(within(filters).getByLabelText('상태'),{target:{value:'inactive'}});
 await waitFor(()=>expect(listUrls(fetch).at(-1)!.searchParams.get('status')).toBe('inactive'));
 fireEvent.change(within(filters).getByLabelText('역할'),{target:{value:'교수'}});
 await waitFor(()=>expect(listUrls(fetch).at(-1)!.searchParams.get('role')).toBe('교수'));
 fireEvent.change(within(filters).getByLabelText('이메일'),{target:{value:'one'}});
 await waitFor(()=>expect(listUrls(fetch).at(-1)!.searchParams.get('email')).toBe('one'));
});

test('비밀번호 재설정은 값·확인이 같아야 보내고 원문을 화면에 남기지 않는다',async()=>{
 const fetch=routedFetch();
 renderAdmin();
 const table=await screen.findByRole('table',{name:'계정 목록'});
 fireEvent.click(within(within(table).getByRole('row',{name:/one@example.com/})).getByRole('button',{name:'비밀번호 재설정'}));
 const dialog=await screen.findByRole('dialog',{name:'비밀번호 재설정'});
 fireEvent.change(within(dialog).getByLabelText('새 초기 비밀번호'),{target:{value:'재설정-비밀번호-123'}});
 fireEvent.change(within(dialog).getByLabelText('새 초기 비밀번호 확인'),{target:{value:'다른-비밀번호-123'}});
 expect(within(dialog).getByRole('button',{name:'재설정'})).toBeDisabled();
 fireEvent.change(within(dialog).getByLabelText('새 초기 비밀번호 확인'),{target:{value:'재설정-비밀번호-123'}});
 fireEvent.click(within(dialog).getByRole('button',{name:'재설정'}));
 await waitFor(()=>expect(screen.queryByRole('dialog',{name:'비밀번호 재설정'})).toBeNull());
 const sent=fetch.mock.calls.map(call=>call[0] as Request).filter(request=>request.url.endsWith('/password-reset'));
 expect(sent).toHaveLength(1);
 expect(sent[0]!.url).toContain(`/admin/accounts/${ACC_1}/password-reset`);
 expect(JSON.parse(await sent[0]!.clone().text())).toEqual({newPassword:'재설정-비밀번호-123'});
 expect(document.body.textContent).not.toContain('재설정-비밀번호-123');
 expect(screen.queryByDisplayValue('재설정-비밀번호-123')).toBeNull();
 // 계정 전환 보관함에 남지 않는다 — 재설정 입력값은 보관 대상이 아니다(spec §4).
 expect(readDraft(OPERATOR.accountId,'account-admin')).toBeUndefined();
});

test('비활성화는 확인 대화상자를 거쳐야 보낸다',async()=>{
 const fetch=routedFetch();
 renderAdmin();
 const table=await screen.findByRole('table',{name:'계정 목록'});
 fireEvent.click(within(within(table).getByRole('row',{name:/one@example.com/})).getByRole('button',{name:'비활성화'}));
 const dialog=await screen.findByRole('dialog',{name:'계정 비활성화'});
 fireEvent.click(within(dialog).getByRole('button',{name:'그대로 두기'}));
 await waitFor(()=>expect(screen.queryByRole('dialog',{name:'계정 비활성화'})).toBeNull());
 expect(fetch.mock.calls.filter(call=>(call[0] as Request).url.endsWith('/status'))).toHaveLength(0);
 fireEvent.click(within(within(table).getByRole('row',{name:/one@example.com/})).getByRole('button',{name:'비활성화'}));
 fireEvent.click(within(await screen.findByRole('dialog',{name:'계정 비활성화'})).getByRole('button',{name:'비활성화'}));
 await waitFor(()=>expect(fetch.mock.calls.filter(call=>(call[0] as Request).url.endsWith('/status'))).toHaveLength(1));
 const sent=fetch.mock.calls.map(call=>call[0] as Request).find(request=>request.url.endsWith('/status'))!;
 expect(sent.url).toContain(`/admin/accounts/${ACC_1}/status`);
 expect(JSON.parse(await sent.clone().text())).toEqual({status:'inactive'});
});

test('비운영자에게는 목록도 서버 질의도 없다',async()=>{
 const fetch=routedFetch();
 render(<SessionProvider account={{...OPERATOR,canManageServiceAccounts:false}}><AccountAdminPage/></SessionProvider>);
 expect(await screen.findByText('서비스 운영자만 사용할 수 있어요.')).toBeInTheDocument();
 expect(screen.queryByRole('table',{name:'계정 목록'})).toBeNull();
 expect(fetch).not.toHaveBeenCalled();
});
