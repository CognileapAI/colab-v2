import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, expect, test, vi } from 'vitest';
import { MemoryRouter, useLocation } from 'react-router-dom';
import { PasswordChangePage } from '../src/auth/PasswordChangePage';
import { LoginPage } from '../src/auth/LoginPage';
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
// ⭑ ⟨개정 2026-09-17 · #84⟩ ／ 종전 ~~「기존 연구실과 역할로 **관리자**를 등록한다」~~ —
//    관리자를 체크하면 연구실·역할이 비활성·비움이 되므로 「관리자 ＋ 연구실·역할」 조합은
//    화면에서 더 이상 만들 수 없다(Ted 결정: 관리자는 연구실·역할 없음). 재는 사실은
//    그대로다 — **연구실·역할을 실은 생성 요청이 그 값으로 나간다.**
test('서비스 운영자가 기존 연구실과 역할로 사용자를 생성한다',async()=>{
 // 화면이 목록도 함께 부르므로 **호출 순서가 아니라 경로**로 답한다.
 const fetch=vi.spyOn(globalThis,'fetch').mockImplementation(async input=>{
  const request=input as Request; const url=new URL(request.url);
  if(url.pathname.endsWith('/admin/account-options'))return json({labs:[{labId:LAB,name:'A 연구실'}],roles:['교수','연구원']});
  if(url.pathname.endsWith('/admin/accounts-v2')&&request.method==='GET')return json({accounts:[]});
  if(url.pathname.endsWith('/admin/accounts-v2')&&request.method==='POST')return json({accountId:'000000000000000000000000A2',email:'new@example.com',name:'새 사용자',labId:LAB,role:'교수'},201);
  return json({message:'모의하지 않은 경로'},500);
 });
 render(<SessionProvider account={{accountId:'00000000000000000000000AP1',name:'운영자',email:'op@example.com',role:'교수',permissions:{},labId:LAB,labName:'A 연구실',canManageServiceAccounts:true,mustChangePassword:false}}><AccountAdminPage/></SessionProvider>);
 fireEvent.click(screen.getByRole('tab',{name:'사용자 생성'}));
 const form=within(await screen.findByTestId('account-create'));
 await within(form.getByLabelText('연구실')).findByRole('option',{name:'A 연구실'});
 fireEvent.change(form.getByLabelText('연구실'),{target:{value:LAB}});
 fireEvent.change(form.getByLabelText('역할'),{target:{value:'교수'}});
 fireEvent.change(form.getByLabelText('이름'),{target:{value:'새 사용자'}});
 fireEvent.change(form.getByLabelText('이메일'),{target:{value:'new@example.com'}});
 fireEvent.change(form.getByLabelText('초기 비밀번호'),{target:{value:'initial-password'}});
 fireEvent.click(form.getByRole('button',{name:'사용자 생성'}));
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

// ⭑ ⟨개정 2026-09-17 · #84⟩ 체크박스 기본값이 꺼짐이 됐다 — 관리자 요청을 보내려면
//    **명시로 체크한다.** ／ 종전 ~~기본 켜짐이라 아무 조작 없이 관리자가 됐다~~.
test('사용자 생성 탭은 목록을 숨기고 관리자를 체크하면 무소속 관리자 요청을 보낸다',async()=>{
 const fetch=operatorFetch();
 renderAdmin();
 fireEvent.click(screen.getByRole('tab',{name:'사용자 생성'}));
 const form=within(await screen.findByTestId('account-create'));
 expect(screen.getByRole('table',{name:'계정 목록',hidden:true})).not.toBeVisible();
 fireEvent.click(form.getByLabelText('시스템 관리자로 등록'));
 fireEvent.change(form.getByLabelText('이름'),{target:{value:'무소속 관리자'}});
 fireEvent.change(form.getByLabelText('이메일'),{target:{value:'admin@example.com'}});
 fireEvent.change(form.getByLabelText('초기 비밀번호'),{target:{value:'initial-password'}});
 fireEvent.click(form.getByRole('button',{name:'사용자 생성'}));
 await waitFor(()=>expect(fetch.mock.calls.some(call=>(call[0] as Request).method==='POST')).toBe(true));
 const request=fetch.mock.calls.map(call=>call[0] as Request)
  .find(call=>call.method==='POST'&&call.url.endsWith('/admin/accounts-v2'))!;
 expect(JSON.parse(await request.clone().text())).toEqual({
  email:'admin@example.com',name:'무소속 관리자',initialPassword:'initial-password',operator:true,
 });
});

// ⭑ ⟨개정 2026-09-17 · #84⟩ 기본값이 꺼짐이라 「끄는」 경로를 재려면 **먼저 켠다.**
//    켰다 끄면 연구실·역할이 **다시 활성**이 되어야 한다 — 비활성 전환의 되돌림 경로다.
test('관리자 선택을 켰다 끄면 연구실·역할이 다시 활성이 되고 일반 사용자 요청을 유지한다',async()=>{
 const fetch=operatorFetch();
 renderAdmin();
 fireEvent.click(screen.getByRole('tab',{name:'사용자 생성'}));
 const form=within(screen.getByTestId('account-create'));
 await within(form.getByLabelText('연구실')).findByRole('option',{name:'A 연구실'});
 fireEvent.click(form.getByLabelText('시스템 관리자로 등록'));
 expect(form.getByLabelText('연구실')).toBeDisabled();
 fireEvent.click(form.getByLabelText('시스템 관리자로 등록'));
 expect(form.getByLabelText('연구실')).toBeEnabled();
 expect(form.getByLabelText('역할')).toBeEnabled();
 fireEvent.change(form.getByLabelText('이름'),{target:{value:'일반 사용자'}});
 fireEvent.change(form.getByLabelText('이메일'),{target:{value:'user@example.com'}});
 fireEvent.change(form.getByLabelText('연구실'),{target:{value:LAB}});
 fireEvent.change(form.getByLabelText('역할'),{target:{value:'연구원'}});
 fireEvent.change(form.getByLabelText('초기 비밀번호'),{target:{value:'initial-password'}});
 fireEvent.click(form.getByRole('button',{name:'사용자 생성'}));
 await waitFor(()=>expect(fetch.mock.calls.some(call=>(call[0] as Request).method==='POST')).toBe(true));
 const request=fetch.mock.calls.map(call=>call[0] as Request)
  .find(call=>call.method==='POST'&&call.url.endsWith('/admin/accounts-v2'))!;
 expect(JSON.parse(await request.clone().text())).toEqual({
  email:'user@example.com',name:'일반 사용자',labId:LAB,role:'연구원',initialPassword:'initial-password',
 });
});

test('소속은 연구실과 역할 중 하나만 고르면 보내지 않는다',async()=>{
 const fetch=operatorFetch();
 renderAdmin();
 fireEvent.click(screen.getByRole('tab',{name:'사용자 생성'}));
 const form=within(screen.getByTestId('account-create'));
 await within(form.getByLabelText('역할')).findByRole('option',{name:'교수 관리자'});
 fireEvent.change(form.getByLabelText('이름'),{target:{value:'부분 소속'}});
 fireEvent.change(form.getByLabelText('이메일'),{target:{value:'partial@example.com'}});
 fireEvent.change(form.getByLabelText('역할'),{target:{value:'교수'}});
 fireEvent.change(form.getByLabelText('초기 비밀번호'),{target:{value:'initial-password'}});
 fireEvent.submit(form.getByRole('button',{name:'사용자 생성'}).closest('form')!);
 expect(await screen.findByRole('status')).toHaveTextContent('연구실과 역할을 함께');
 expect(fetch.mock.calls.filter(call=>(call[0] as Request).method==='POST')).toHaveLength(0);
});

test('생성 탭에 입력한 값은 목록 탭을 다녀와도 유지된다',()=>{
 operatorFetch();
 renderAdmin();
 fireEvent.click(screen.getByRole('tab',{name:'사용자 생성'}));
 fireEvent.change(screen.getByLabelText('이름'),{target:{value:'작성 중 관리자'}});
 fireEvent.click(screen.getByRole('tab',{name:'사용자 목록'}));
 fireEvent.click(screen.getByRole('tab',{name:'사용자 생성'}));
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
 fireEvent.click(screen.getByRole('tab',{name:'사용자 생성'}));
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

// ═══════════════ 계정 생성 폼 — 문면 · 순서 · 기본값 · 시험 식별자 ═══════════════
// 승인 intent = dev-package/intent/2026-09-17-issue-84-account-create-form.md (#84 · #54)
// ⚠ #84⑵(뷰포트 높이가 바뀌어도 제출 버튼이 세로로 움직이지 않는다)는 **여기서 재지 않는다** —
//   jsdom 에는 레이아웃 엔진이 없어 높이를 바꿔도 차이가 나지 않는다(green-by-skip).
//   그 판정은 `frontend-visual`/`agent-browser` 의 실화면 계측 몫이고, 아래 수식 클래스
//   존재 단언은 그 계측의 **대체가 아니다**.
const CREATE_FIELD_TESTIDS=['ac-name','ac-email','ac-lab','ac-role','ac-password','ac-operator','ac-submit'] as const;

test('#84 생성 탭·카드 제목·제출 버튼 문면이 모두 `사용자 생성` 이다',async()=>{
 operatorFetch();
 renderAdmin();
 fireEvent.click(screen.getByRole('tab',{name:'사용자 생성'}));
 const card=await screen.findByTestId('account-create');
 expect(within(card).getByRole('heading',{name:'사용자 생성'})).toBeInTheDocument();
 expect(within(card).getByRole('button',{name:'사용자 생성'})).toBeInTheDocument();
 // 관리자 여부로 제출 문면이 갈리지 않는다 — 한 화면에 세 이름이 섞이지 않는다.
 fireEvent.click(within(card).getByLabelText('시스템 관리자로 등록'));
 expect(within(card).getByRole('button',{name:'사용자 생성'})).toBeInTheDocument();
 expect(within(card).queryByRole('button',{name:'시스템 관리자 등록'})).toBeNull();
 expect(within(card).queryByRole('button',{name:'사용자 등록'})).toBeNull();
});

test('#84 관리자 여부 체크가 폼의 첫 요소이고 기본값은 꺼짐이다',async()=>{
 operatorFetch();
 renderAdmin();
 fireEvent.click(screen.getByRole('tab',{name:'사용자 생성'}));
 const card=await screen.findByTestId('account-create');
 const check=within(card).getByTestId('ac-operator') as HTMLInputElement;
 expect(check.checked).toBe(false);
 const form=check.closest('form')!;
 // **첫 요소**다 — 그 선택이 아래 칸을 채울 필요가 있는지를 결정하기 때문이다.
 expect(form.firstElementChild!.contains(check)).toBe(true);
 // 이름 칸보다 앞선다 — 「첫 자식」이 우연히 맞는 형태를 막는다.
 const name=within(card).getByTestId('ac-name');
 expect(check.compareDocumentPosition(name)&Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
});

test('#84 관리자 여부를 체크하면 연구실·역할이 비활성이 되고 값이 빈다',async()=>{
 operatorFetch();
 renderAdmin();
 fireEvent.click(screen.getByRole('tab',{name:'사용자 생성'}));
 const card=await screen.findByTestId('account-create');
 await within(within(card).getByTestId('ac-lab')).findByRole('option',{name:'A 연구실'});
 const lab=within(card).getByTestId('ac-lab') as HTMLSelectElement;
 const role=within(card).getByTestId('ac-role') as HTMLSelectElement;
 // ⑴ 체크 **전에는 활성**이고 값이 실제로 들어간다 — 양성·음성 쌍으로 잰다.
 expect(lab.disabled).toBe(false);
 expect(role.disabled).toBe(false);
 fireEvent.change(lab,{target:{value:LAB}});
 fireEvent.change(role,{target:{value:'연구원'}});
 expect(lab.value).toBe(LAB);
 expect(role.value).toBe('연구원');
 // ⑵ 체크하면 비활성이 되고 **값까지 비운다** — `disabled` 만으로는 화면에 값이 남는다.
 fireEvent.click(within(card).getByTestId('ac-operator'));
 expect(lab.disabled).toBe(true);
 expect(role.disabled).toBe(true);
 expect(lab.value).toBe('');
 expect(role.value).toBe('');
});

test('#84 초기 상태로 다섯 칸만 채워 제출하면 관리자 아님으로 생성 요청이 나간다',async()=>{
 const fetch=operatorFetch();
 renderAdmin();
 fireEvent.click(screen.getByRole('tab',{name:'사용자 생성'}));
 const card=await screen.findByTestId('account-create');
 await within(within(card).getByTestId('ac-lab')).findByRole('option',{name:'A 연구실'});
 // 관리자 체크는 **건드리지 않는다** — 아무 조작 없이 제출하면 일반 사용자여야 한다.
 fireEvent.change(within(card).getByTestId('ac-name'),{target:{value:'일반 사용자'}});
 fireEvent.change(within(card).getByTestId('ac-email'),{target:{value:'user@example.com'}});
 fireEvent.change(within(card).getByTestId('ac-lab'),{target:{value:LAB}});
 fireEvent.change(within(card).getByTestId('ac-role'),{target:{value:'연구원'}});
 fireEvent.change(within(card).getByTestId('ac-password'),{target:{value:'initial-password'}});
 fireEvent.click(within(card).getByTestId('ac-submit'));
 await waitFor(()=>expect(fetch.mock.calls.some(call=>(call[0] as Request).method==='POST')).toBe(true));
 const request=fetch.mock.calls.map(call=>call[0] as Request)
  .find(call=>call.method==='POST'&&call.url.endsWith('/admin/accounts-v2'))!;
 const body=JSON.parse(await request.clone().text());
 expect(body).toEqual({email:'user@example.com',name:'일반 사용자',labId:LAB,role:'연구원',initialPassword:'initial-password'});
 // 권한이 기본값이 되지 않는다 — 열쇠 자체가 없다.
 expect('operator' in body).toBe(false);
});

test('#54 생성 폼의 칸 일곱을 testid 로 각각 하나씩 짚을 수 있고 기존 구역 testid 도 산다',async()=>{
 operatorFetch();
 renderAdmin();
 fireEvent.click(screen.getByRole('tab',{name:'사용자 생성'}));
 const card=await screen.findByTestId('account-create');
 // 총계가 아니라 **목록을 돌며 각각 1건**을 센다.
 expect(CREATE_FIELD_TESTIDS).toHaveLength(7);
 for(const id of CREATE_FIELD_TESTIDS) expect(within(card).getAllByTestId(id)).toHaveLength(1);
 // 러너가 짚는 `name` 은 그대로 살아 있다 — testid 는 덧붙인 것이지 대체가 아니다.
 // (dev-package/tools/dev-seed/runner.py 가 `[data-testid="account-create"] input[name="…"]` 로 짚는다)
 const inputs=['name','email','initialPassword','operator'].map(n=>card.querySelector(`input[name="${n}"]`));
 expect(inputs.filter(Boolean)).toHaveLength(4);
 const selects=['labId','role'].map(n=>card.querySelector(`select[name="${n}"]`));
 expect(selects.filter(Boolean)).toHaveLength(2);
 expect(card.querySelector('button[type="submit"]')).toBeTruthy();
});

test('#84 계정 관리 화면 최상위에만 세로 배치 수식 클래스가 붙는다',async()=>{
 operatorFetch();
 const {container}=renderAdmin();
 await screen.findByTestId('account-create');
 const root=container.querySelector('.login')!;
 expect(root.classList.contains('account-admin')).toBe(true);
 // 공용 `.login` 은 그대로다 — 수식 클래스만 덧붙는다.
 expect(root.classList.contains('login')).toBe(true);
});

// ═══════════════ #121 — 잘린 값의 전체 문면 · 액션 셀 구조 ═══════════════
// 승인 근거 = dev-package/prd/specs/2026-09-18-issue-121-account-admin-gap-table.md
//             「시험 결정 ⑶⑷」 ＋ 「advisor ① A1」.
// ⚠ 열 폭·여백·고정 열은 **여기서 재지 않는다** — jsdom 에 배치 엔진이 없다(green-by-skip).
//   그 판정은 `dev-package/reports/issue-121/` 의 실브라우저 `get box` 계측 몫이다.
//   여기서는 생략 부호가 가린 값을 **읽을 수단이 실제로 붙어 있는지**만 잰다.
const LONG_EMAIL='jeongsuyeon.researcher.2026@example-institute-of-water-resources-research.org';
const ACCOUNTS_WITH_LONG_EMAIL=[
 {accountId:ACC_1,email:'one@example.com',name:'한 사람',labId:LAB,labName:'A 연구실',role:'연구원',status:'active',lastLoginAt:'2026-09-11T02:03:04Z',operator:false},
 {accountId:ACC_2,email:LONG_EMAIL,name:'정수연',labId:LAB_B,labName:'하천유역모델링연구실',role:'교수',status:'active',lastLoginAt:null,operator:false},
];
function longEmailFetch(){
 return routedFetch(url=>url.pathname.endsWith('/admin/accounts-v2')?json({accounts:ACCOUNTS_WITH_LONG_EMAIL}):undefined);
}

test('#121 자유 문자열 셀은 생략 부호에 가려도 `title` 로 전체 값을 읽는다',async()=>{
 longEmailFetch();
 renderAdmin();
 const table=await screen.findByRole('table',{name:'계정 목록'});
 // 짧은 값 — 생략 부호가 걸리지 않는 쪽도 같은 수단을 갖는다(green-by-skip 방지 쌍).
 const short=await within(table).findByRole('row',{name:/one@example\.com/});
 expect(within(short).getByText('one@example.com')).toHaveAttribute('title','one@example.com');
 expect(within(short).getByText('한 사람')).toHaveAttribute('title','한 사람');
 expect(within(short).getByText('A 연구실')).toHaveAttribute('title','A 연구실');
 // 60자 이상 — `title` 은 잘린 표시가 아니라 **원값** 이다.
 expect(LONG_EMAIL.length).toBeGreaterThanOrEqual(60);
 const long=await within(table).findByRole('row',{name:new RegExp(LONG_EMAIL.replace(/[.]/g,'\\.'))});
 const longCell=within(long).getByText(LONG_EMAIL);
 expect(longCell).toHaveAttribute('title',LONG_EMAIL);
 expect(longCell).toHaveClass('account-cell-text');
 expect(within(long).getByText('하천유역모델링연구실')).toHaveAttribute('title','하천유역모델링연구실');
});

test('#121 소속 없는 계정의 연구실 칸은 화면 문면과 `title` 이 같다',async()=>{
 routedFetch(url=>url.pathname.endsWith('/admin/accounts-v2')
  ?json({accounts:[{accountId:ACC_1,email:'solo@example.com',name:'무소속',labId:null,labName:null,role:null,status:'active',lastLoginAt:null,operator:true}]})
  :undefined);
 renderAdmin();
 const table=await screen.findByRole('table',{name:'계정 목록'});
 const row=await within(table).findByRole('row',{name:/solo@example\.com/});
 // 역할 칸도 같은 `없음` 을 그리므로 **열 자리**로 짚는다(4번째 = 연구실).
 const cells=row.querySelectorAll('td');
 const labCell=cells[3]!;
 expect(labCell).toHaveTextContent('없음');
 // 화면이 `없음` 을 그리면 `title` 도 `없음` 이다 — 빈 title 로 「읽을 수 없음」을 만들지 않는다.
 expect(labCell).toHaveAttribute('title','없음');
 // 역할 열은 값 집합이 짧아 폭이 고정이라 생략 부호 대상이 아니다 — `title` 을 달지 않는다.
 expect(cells[2]).toHaveTextContent('없음');
 expect(cells[2]).not.toHaveAttribute('title');
});

test('#121 A1 액션 `td` 는 table-cell 로 남고 버튼은 안쪽 div 가 담는다',async()=>{
 operatorFetch();
 renderAdmin();
 const table=await screen.findByRole('table',{name:'계정 목록'});
 const row=await within(table).findByRole('row',{name:/one@example\.com/});
 const cell=within(row).getByRole('button',{name:'비밀번호 재설정'}).closest('td')!;
 // 종전 ~~`<td className="account-row-actions">`~~ — `td` 자체에 flex 가 걸려 sticky 가 붙지 않았다.
 expect(cell).toHaveClass('account-row-actions-cell');
 expect(cell).not.toHaveClass('account-row-actions');
 const inner=cell.querySelector(':scope > div.account-row-actions')!;
 expect(inner).not.toBeNull();
 expect(inner.querySelectorAll(':scope > button')).toHaveLength(3);
});

test('#121 자기 줄 이유 문면은 화면에 남고 `title` 로도 전체를 읽는다',async()=>{
 operatorFetch();
 renderAdmin();
 const table=await screen.findByRole('table',{name:'계정 목록'});
 const self=await within(table).findByRole('row',{name:/op@example\.com/});
 const note=within(self).getByText('자기 계정은 비활성화할 수 없어요');
 expect(note).toHaveClass('account-row-note');
 expect(note).toHaveAttribute('title','자기 계정은 비활성화할 수 없어요');
 // note 는 액션 셀 안쪽 div 의 자식이다 — 셀 밖으로 내보내지 않는다.
 expect(note.parentElement).toHaveClass('account-row-actions');
});

test('#121 A2 목록 패널 래퍼에 폭 수식 클래스가 붙고 숨김은 그대로다',async()=>{
 operatorFetch();
 const {container}=renderAdmin();
 await screen.findByRole('table',{name:'계정 목록'});
 const panel=container.querySelector('.account-list-panel')!;
 expect(panel).not.toBeNull();
 expect(panel.querySelector('[data-testid="account-list"]')).not.toBeNull();
 // 목록 탭이 열린 상태 — 래퍼는 숨지 않는다.
 expect(panel).not.toHaveAttribute('hidden');
 // 생성 탭으로 옮기면 같은 래퍼가 `hidden` 을 되받는다(수식 클래스가 `display` 를 덮지 않는다).
 fireEvent.click(screen.getByRole('tab',{name:'사용자 생성'}));
 expect(container.querySelector('.account-list-panel')).toHaveAttribute('hidden');
});

test('#84 로그인·비밀번호 변경 화면에는 그 수식 클래스가 붙지 않는다',()=>{
 const pw=render(<MemoryRouter><PasswordChangePage/></MemoryRouter>);
 const pwRoot=pw.container.querySelector('.login')!;
 expect(pwRoot).toBeTruthy();
 expect(pwRoot.classList.contains('account-admin')).toBe(false);
 pw.unmount();
 const login=render(<MemoryRouter><LoginPage/></MemoryRouter>);
 const loginRoot=login.container.querySelector('.login')!;
 expect(loginRoot).toBeTruthy();
 expect(loginRoot.classList.contains('account-admin')).toBe(false);
});
