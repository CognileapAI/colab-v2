import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, test, vi } from 'vitest';
import { MemoryRouter, useLocation } from 'react-router-dom';
import { PasswordChangePage } from '../src/auth/PasswordChangePage';
import { AccountAdminPage } from '../src/routes/AccountAdminPage';
import { SessionProvider } from '../src/permission/session';
import { getSession, setSession } from '../src/auth/store';
const LAB='0000000000000000000000000A';
beforeEach(()=>vi.restoreAllMocks());
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
 const fetch=vi.spyOn(globalThis,'fetch')
  .mockResolvedValueOnce(new Response(JSON.stringify({labs:[{labId:LAB,name:'A 연구실'}],roles:['교수','연구원']}),{status:200,headers:{'content-type':'application/json'}}))
  .mockResolvedValueOnce(new Response(JSON.stringify({accountId:'000000000000000000000000A2',email:'new@example.com',name:'새 사용자',labId:LAB,role:'교수'}),{status:201,headers:{'content-type':'application/json'}}));
 render(<SessionProvider account={{accountId:'00000000000000000000000AP1',name:'운영자',email:'op@example.com',role:'교수',permissions:{},labId:LAB,labName:'A 연구실',canManageServiceAccounts:true,mustChangePassword:false}}><AccountAdminPage/></SessionProvider>);
 await screen.findByRole('option',{name:'A 연구실'});
 fireEvent.change(screen.getByLabelText('이름'),{target:{value:'새 사용자'}});
 fireEvent.change(screen.getByLabelText('이메일'),{target:{value:'new@example.com'}});
 fireEvent.change(screen.getByLabelText('초기 비밀번호'),{target:{value:'initial-password'}});
 fireEvent.click(screen.getByRole('button',{name:'계정 추가'}));
 await screen.findByText('new@example.com 계정을 추가했어요.');
 const request=fetch.mock.calls[1]![0] as Request;
 expect(JSON.parse(await request.clone().text())).toMatchObject({email:'new@example.com',labId:LAB,role:'교수'});
 expect(screen.queryByText('initial-password')).not.toBeInTheDocument();
});
