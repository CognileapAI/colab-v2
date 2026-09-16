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
 // 이동은 제출 응답 **뒤의** 상태 갱신에서 일어난다. fetch 가 불린 시점에 바로 재면
 // 아직 `/account-admin` 이라 간헐적으로 red 가 난다(실측 — 3회 중 1회).
 await waitFor(()=>expect(screen.getByTestId('location')).toHaveTextContent('/lab'));
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
test('서비스 운영자가 기존 연구실과 역할로 관리자를 등록한다',async()=>{
 // 화면이 목록도 함께 부르므로 **호출 순서가 아니라 경로**로 답한다.
 const fetch=vi.spyOn(globalThis,'fetch').mockImplementation(async input=>{
  const request=input as Request; const url=new URL(request.url);
  if(url.pathname.endsWith('/admin/account-options'))return json({labs:[{labId:LAB,name:'A 연구실'}],roles:['교수','연구원']});
  if(url.pathname.endsWith('/admin/accounts-v2')&&request.method==='GET')return json({accounts:[]});
  if(url.pathname.endsWith('/admin/accounts-v2')&&request.method==='POST')return json({accountId:'000000000000000000000000A2',email:'new@example.com',name:'새 사용자',labId:LAB,role:'교수'},201);
  return json({message:'모의하지 않은 경로'},500);
 });
 render(<SessionProvider account={{accountId:'00000000000000000000000AP1',name:'운영자',email:'op@example.com',role:'교수',permissions:{},labId:LAB,labName:'A 연구실',canManageServiceAccounts:true,mustChangePassword:false}}><AccountAdminPage/></SessionProvider>);
 fireEvent.click(screen.getByRole('tab',{name:'시스템 관리자 등록'}));
 const form=within(await screen.findByTestId('account-create'));
 await within(form.getByLabelText('연구실')).findByRole('option',{name:'A 연구실'});
 fireEvent.change(form.getByLabelText('연구실'),{target:{value:LAB}});
 fireEvent.change(form.getByLabelText('역할'),{target:{value:'교수'}});
 fireEvent.change(form.getByLabelText('이름'),{target:{value:'새 사용자'}});
 fireEvent.change(form.getByLabelText('이메일'),{target:{value:'new@example.com'}});
 fireEvent.change(form.getByLabelText('초기 비밀번호'),{target:{value:'initial-password'}});
 fireEvent.click(form.getByRole('button',{name:'시스템 관리자 등록'}));
 await screen.findByText('new@example.com 계정을 추가했어요.');
 const request=fetch.mock.calls.map(call=>call[0] as Request).find(call=>call.method==='POST')!;
 expect(JSON.parse(await request.clone().text())).toMatchObject({email:'new@example.com',labId:LAB,role:'교수',operator:true});
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
  if(url.pathname.endsWith('/admin/accounts-v2')&&request.method==='GET')return json({accounts:ACCOUNTS});
  if(url.pathname.endsWith('/password-reset'))return json({accountId:ACC_1,mustChangePassword:true});
  if(url.pathname.endsWith('/status'))return json({accountId:ACC_2,status:'active'});
  return json({message:'모의하지 않은 경로'},500);
 });
}
function renderAdmin(){return render(<SessionProvider account={OPERATOR}><AccountAdminPage/></SessionProvider>);}
const listUrls=(fetch:ReturnType<typeof routedFetch>)=>fetch.mock.calls
 .map(call=>new URL((call[0] as Request).url))
 .filter(url=>url.pathname.endsWith('/admin/accounts-v2')&&!url.pathname.includes('password'));

test('계정 관리 화면은 사용자 목록 탭만 기본으로 보여 준다',async()=>{
 routedFetch();
 renderAdmin();
 expect(await screen.findByRole('table',{name:'계정 목록'})).toBeInTheDocument();
 expect(screen.getByRole('tab',{name:'사용자 목록'})).toHaveAttribute('aria-selected','true');
 expect(screen.getByTestId('account-create')).not.toBeVisible();
});

test('시스템 관리자 등록 탭은 목록을 숨기고 무소속 관리자 요청을 보낸다',async()=>{
 const fetch=operatorFetch();
 renderAdmin();
 fireEvent.click(screen.getByRole('tab',{name:'시스템 관리자 등록'}));
 const form=within(await screen.findByTestId('account-create'));
 expect(screen.getByRole('table',{name:'계정 목록',hidden:true})).not.toBeVisible();
 fireEvent.change(form.getByLabelText('이름'),{target:{value:'무소속 관리자'}});
 fireEvent.change(form.getByLabelText('이메일'),{target:{value:'admin@example.com'}});
 fireEvent.change(form.getByLabelText('초기 비밀번호'),{target:{value:'initial-password'}});
 fireEvent.click(form.getByRole('button',{name:'시스템 관리자 등록'}));
 await waitFor(()=>expect(fetch.mock.calls.some(call=>(call[0] as Request).method==='POST')).toBe(true));
 const request=fetch.mock.calls.map(call=>call[0] as Request)
  .find(call=>call.method==='POST'&&call.url.endsWith('/admin/accounts-v2'))!;
 expect(JSON.parse(await request.clone().text())).toEqual({
  email:'admin@example.com',name:'무소속 관리자',initialPassword:'initial-password',operator:true,
 });
});

test('관리자 선택을 끄면 기존 일반 사용자 등록 요청을 유지한다',async()=>{
 const fetch=operatorFetch();
 renderAdmin();
 fireEvent.click(screen.getByRole('tab',{name:'시스템 관리자 등록'}));
 const form=within(screen.getByTestId('account-create'));
 await within(form.getByLabelText('연구실')).findByRole('option',{name:'A 연구실'});
 fireEvent.click(form.getByLabelText('시스템 관리자로 등록'));
 fireEvent.change(form.getByLabelText('이름'),{target:{value:'일반 사용자'}});
 fireEvent.change(form.getByLabelText('이메일'),{target:{value:'user@example.com'}});
 fireEvent.change(form.getByLabelText('연구실'),{target:{value:LAB}});
 fireEvent.change(form.getByLabelText('역할'),{target:{value:'연구원'}});
 fireEvent.change(form.getByLabelText('초기 비밀번호'),{target:{value:'initial-password'}});
 fireEvent.click(form.getByRole('button',{name:'사용자 등록'}));
 await waitFor(()=>expect(fetch.mock.calls.some(call=>(call[0] as Request).method==='POST')).toBe(true));
 const request=fetch.mock.calls.map(call=>call[0] as Request)
  .find(call=>call.method==='POST'&&call.url.endsWith('/admin/accounts-v2'))!;
 expect(JSON.parse(await request.clone().text())).toEqual({
  email:'user@example.com',name:'일반 사용자',labId:LAB,role:'연구원',initialPassword:'initial-password',
 });
});

test('관리자 소속은 연구실과 역할 중 하나만 고르면 보내지 않는다',async()=>{
 const fetch=operatorFetch();
 renderAdmin();
 fireEvent.click(screen.getByRole('tab',{name:'시스템 관리자 등록'}));
 const form=within(screen.getByTestId('account-create'));
 await within(form.getByLabelText('역할')).findByRole('option',{name:'교수 관리자'});
 fireEvent.change(form.getByLabelText('이름'),{target:{value:'부분 소속'}});
 fireEvent.change(form.getByLabelText('이메일'),{target:{value:'partial@example.com'}});
 fireEvent.change(form.getByLabelText('역할'),{target:{value:'교수'}});
 fireEvent.change(form.getByLabelText('초기 비밀번호'),{target:{value:'initial-password'}});
 fireEvent.submit(form.getByRole('button',{name:'시스템 관리자 등록'}).closest('form')!);
 expect(await screen.findByRole('status')).toHaveTextContent('연구실과 역할을 함께');
 expect(fetch.mock.calls.filter(call=>(call[0] as Request).method==='POST')).toHaveLength(0);
});

test('등록 탭에 입력한 값은 목록 탭을 다녀와도 유지된다',()=>{
 operatorFetch();
 renderAdmin();
 fireEvent.click(screen.getByRole('tab',{name:'시스템 관리자 등록'}));
 fireEvent.change(screen.getByLabelText('이름'),{target:{value:'작성 중 관리자'}});
 fireEvent.click(screen.getByRole('tab',{name:'사용자 목록'}));
 fireEvent.click(screen.getByRole('tab',{name:'시스템 관리자 등록'}));
 expect(screen.getByLabelText('이름')).toHaveValue('작성 중 관리자');
});

test('운영자가 전 연구실 계정 목록을 일곱 열로 본다',async()=>{
 routedFetch();
 renderAdmin();
 const table=await screen.findByRole('table',{name:'계정 목록'});
 const headers=within(table).getAllByRole('columnheader').map(cell=>cell.textContent);
 // 「관리자」 열은 행 토글의 현재 상태다 (승인 intent 2026-09-12 운영자 지정).
 expect(headers).toEqual(['이메일','이름','역할','연구실','상태','시스템 관리자','최근 로그인','']);
 // 표 틀은 목록 응답보다 먼저 나타난다. 실제 계정 행이 도착한 뒤 검증한다.
 const first=await within(table).findByRole('row',{name:/one@example.com/});
 expect(first).toHaveTextContent('한 사람');
 expect(first).toHaveTextContent('연구원');
 expect(first).toHaveTextContent('A 연구실');
 expect(first).toHaveTextContent('2026-09-11');
 const second=await within(table).findByRole('row',{name:/two@example.com/});
 expect(second).toHaveTextContent('B 연구실');
 expect(second).toHaveTextContent('기록 없음');
 expect(within(second).getByRole('button',{name:'재활성화'})).toBeInTheDocument();
 expect(within(first).getByRole('button',{name:'비활성화'})).toBeInTheDocument();
});

test('목록 필터 네 가지가 서버 질의 인자로 전달된다',async()=>{
 let releaseOptions!:()=>void;
 const optionsResponse=new Response(new ReadableStream({start(controller){
  releaseOptions=()=>{controller.enqueue(new TextEncoder().encode(JSON.stringify(OPTIONS)));controller.close();};
 }}),{headers:{'content-type':'application/json'}});
 const fetch=routedFetch(url=>url.pathname.endsWith('/admin/account-options')?optionsResponse:undefined);
 renderAdmin();
 await screen.findByRole('table',{name:'계정 목록'});
 const filters=screen.getByRole('group',{name:'계정 목록 필터'});
 // 표가 먼저 보이고 선택지 응답이 나중에 도착하는 순서를 보장한다.
 expect(within(filters).queryByRole('option',{name:'B 연구실'})).toBeNull();
 releaseOptions();
 await within(within(filters).getByLabelText('연구실')).findByRole('option',{name:'B 연구실'});
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
 fireEvent.click(within(await within(table).findByRole('row',{name:/one@example.com/})).getByRole('button',{name:'비밀번호 재설정'}));
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
 fireEvent.click(within(await within(table).findByRole('row',{name:/one@example.com/})).getByRole('button',{name:'비활성화'}));
 const dialog=await screen.findByRole('dialog',{name:'계정 비활성화'});
 fireEvent.click(within(dialog).getByRole('button',{name:'그대로 두기'}));
 await waitFor(()=>expect(screen.queryByRole('dialog',{name:'계정 비활성화'})).toBeNull());
 expect(fetch.mock.calls.filter(call=>(call[0] as Request).url.endsWith('/status'))).toHaveLength(0);
 fireEvent.click(within(await within(table).findByRole('row',{name:/one@example.com/})).getByRole('button',{name:'비활성화'}));
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

// ═══════════════ 시스템 관리자 지정·해제 ＋ 전 연구실 보기 ═══════════════
// 승인 intent = dev-package/intent/2026-09-12-operator-designation.md
const ACCOUNTS_WITH_OPERATOR=[
 {accountId:ACC_1,email:'one@example.com',name:'한 사람',labId:LAB,labName:'A 연구실',role:'연구원',status:'active',lastLoginAt:'2026-09-11T02:03:04Z',operator:false},
 {accountId:ACC_2,email:'two@example.com',name:'두 사람',labId:LAB_B,labName:'B 연구실',role:'교수',status:'inactive',lastLoginAt:null,operator:true},
 {accountId:OPERATOR.accountId,email:'op@example.com',name:'운영자',labId:LAB,labName:'A 연구실',role:'교수',status:'active',lastLoginAt:null,operator:true},
];
function operatorFetch(onOperator?:(request:Request)=>Response){
 return vi.spyOn(globalThis,'fetch').mockImplementation(async input=>{
  const request=input as Request; const url=new URL(request.url);
  if(url.pathname.endsWith('/admin/account-options'))return json(OPTIONS);
  if(url.pathname.endsWith('/operator'))return onOperator?onOperator(request):json({accountId:ACC_1,operator:true});
  if(url.pathname.endsWith('/admin/accounts-v2')&&request.method==='GET')return json({accounts:ACCOUNTS_WITH_OPERATOR});
  if(url.pathname.endsWith('/admin/accounts-v2')&&request.method==='POST')return json({accountId:ACC_1,email:'new@example.com',name:'새 사용자',labId:LAB,role:'교수'},201);
  return json({message:'모의하지 않은 경로'},500);
 });
}

test('행마다 관리자 토글이 있고 자기 자신은 누를 수 없다',async()=>{
 operatorFetch();
 renderAdmin();
 const table=await screen.findByRole('table',{name:'계정 목록'});
 const plain=await within(table).findByRole('row',{name:/one@example.com/});
 expect(within(plain).getByRole('button',{name:'시스템 관리자 지정'})).toBeEnabled();
 const boss=await within(table).findByRole('row',{name:/two@example.com/});
 expect(within(boss).getByRole('button',{name:'시스템 관리자 해제'})).toBeEnabled();
 const self=await within(table).findByRole('row',{name:/op@example.com/});
 expect(within(self).getByRole('button',{name:'시스템 관리자 해제'})).toBeDisabled();
});

test('시스템 관리자 지정은 확인 대화상자를 거쳐야 보낸다',async()=>{
 const fetch=operatorFetch();
 renderAdmin();
 const table=await screen.findByRole('table',{name:'계정 목록'});
 fireEvent.click(within(await within(table).findByRole('row',{name:/one@example.com/})).getByRole('button',{name:'시스템 관리자 지정'}));
 const dialog=await screen.findByRole('dialog',{name:'시스템 관리자 지정'});
 fireEvent.click(within(dialog).getByRole('button',{name:'그대로 두기'}));
 await waitFor(()=>expect(screen.queryByRole('dialog',{name:'시스템 관리자 지정'})).toBeNull());
 expect(fetch.mock.calls.filter(call=>(call[0] as Request).url.endsWith('/operator'))).toHaveLength(0);

 fireEvent.click(within(await within(table).findByRole('row',{name:/one@example.com/})).getByRole('button',{name:'시스템 관리자 지정'}));
 fireEvent.click(within(await screen.findByRole('dialog',{name:'시스템 관리자 지정'})).getByRole('button',{name:'시스템 관리자 지정'}));
 await waitFor(()=>expect(fetch.mock.calls.filter(call=>(call[0] as Request).url.endsWith('/operator'))).toHaveLength(1));
 const sent=fetch.mock.calls.map(call=>call[0] as Request).find(request=>request.url.endsWith('/operator'))!;
 expect(sent.url).toContain(`/admin/accounts/${ACC_1}/operator`);
 expect(JSON.parse(await sent.clone().text())).toEqual({operator:true});
});

test('마지막 시스템 관리자 해제 거절은 서버 문구 그대로 보인다',async()=>{
 operatorFetch(()=>json({code:'BAD_REQUEST',message:'마지막 관리자는 해제할 수 없다. 먼저 다른 관리자를 지정한다.'},400));
 renderAdmin();
 const table=await screen.findByRole('table',{name:'계정 목록'});
 fireEvent.click(within(await within(table).findByRole('row',{name:/two@example.com/})).getByRole('button',{name:'시스템 관리자 해제'}));
 fireEvent.click(within(await screen.findByRole('dialog',{name:'시스템 관리자 해제'})).getByRole('button',{name:'시스템 관리자 해제'}));
 expect(await screen.findByText('마지막 관리자는 해제할 수 없다. 먼저 다른 관리자를 지정한다.')).toBeInTheDocument();
});

// ═══════════════ 이태헌 1차 검증 4건 — 본문 영역 · 표 안내 · 자동완성 · 자기 줄 가드 ═══════════════
// 계획 = dev-package/prd/rounds/R-LTH-REVIEW-1.md Task 1 (spec §8-2 5~8)
test('운영자 화면이 본문 영역을 스스로 만들지 않는다',async()=>{
 routedFetch();
 const view=renderAdmin();
 await screen.findByRole('table',{name:'계정 목록'});
 expect(view.container.querySelectorAll('main')).toHaveLength(0);
 expect(screen.queryAllByRole('main')).toHaveLength(0);
});

test('비운영자 안내도 본문 영역을 새로 만들지 않는다',async()=>{
 routedFetch();
 const view=render(<SessionProvider account={{...OPERATOR,canManageServiceAccounts:false}}><AccountAdminPage/></SessionProvider>);
 expect(await screen.findByText('서비스 운영자만 사용할 수 있어요.')).toBeInTheDocument();
 expect(view.container.querySelectorAll('main')).toHaveLength(0);
});

test('계정 목록 표에 좌우 이동 안내와 키보드 초점을 받는 래퍼가 있다',async()=>{
 routedFetch();
 renderAdmin();
 const table=await screen.findByRole('table',{name:'계정 목록'});
 // 공용 패턴 = CatalogTable·ProjectTable·ProjectDatasetTable 과 같은 클래스·같은 축자.
 const wrap=screen.getByRole('region',{name:'계정 목록 표 스크롤'});
 expect(wrap).toHaveAttribute('tabindex','0');
 expect(wrap).toContainElement(table);
 const hint=document.querySelector('.table-scroll-hint');
 expect(hint).not.toBeNull();
 expect(hint).toHaveTextContent('표를 좌우로 밀면 나머지 항목과 작업을 볼 수 있어요.');
});

test('초기 비밀번호 칸을 비밀번호 관리 도구가 새 비밀번호로 읽는다',async()=>{
 routedFetch();
 renderAdmin();
 fireEvent.click(screen.getByRole('tab',{name:'시스템 관리자 등록'}));
 const form=within(await screen.findByTestId('account-create'));
 expect(form.getByLabelText('초기 비밀번호')).toHaveAttribute('autocomplete','new-password');
});

test('자기 줄 비활성화는 처음부터 눌리지 않고 이유가 화면에 적혀 있다',async()=>{
 operatorFetch();
 renderAdmin();
 const table=await screen.findByRole('table',{name:'계정 목록'});
 const self=await within(table).findByRole('row',{name:/op@example\.com/});
 expect(within(self).getByRole('button',{name:'비활성화'})).toBeDisabled();
 expect(within(self).getByText('자기 계정은 비활성화할 수 없어요')).toBeInTheDocument();
 // 대조군 — 남의 줄은 그대로 눌리고 이유 문면도 없다. 대상 0건 통과를 가른다(spec §8-6 ⑶).
 const other=await within(table).findByRole('row',{name:/one@example\.com/});
 expect(within(other).getByRole('button',{name:'비활성화'})).toBeEnabled();
 expect(within(other).queryByText('자기 계정은 비활성화할 수 없어요')).toBeNull();
});
