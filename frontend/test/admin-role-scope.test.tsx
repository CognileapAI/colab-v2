import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import { DatasetPreviewSection } from '../src/components/datasetpreview/DatasetPreviewSection';
import { apiDatasetPreviewSource } from '../src/components/datasetpreview/datasetPreviewSource';
import type { DatasetPreviewSource } from '../src/components/datasetpreview/types';
import { ProjectFormModal } from '../src/components/project/ProjectFormModal';
import { SessionProvider } from '../src/permission/session';
import type { CurrentAccount } from '../src/api/client';
const account = { accountId:'admin', canManageServiceAccounts:true, labId:null } as CurrentAccount;
afterEach(() => vi.unstubAllGlobals());
it('변수 조회 거절을 안내하고 재시도하면 보기 가능', async () => {
 let attempts=0;
 const source = { files:async()=>[{fileId:'f',fileName:'a.nc',renderable:true}],palettes:async()=>[{palette:'viridis'}], describe:async()=>{if(++attempts===1)throw new Error('이 작업을 할 권한이 없어요.');return {variables:['v'],instants:null,default:{variable:'v',instant:null}};} } as unknown as DatasetPreviewSource;
 render(<DatasetPreviewSection datasetId="d" source={source}/>);
 expect(await screen.findByRole('alert')).toHaveTextContent('이 작업을 할 권한이 없어요.');
 fireEvent.click(screen.getByRole('button',{name:'다시 불러오기'}));
 await screen.findByRole('option',{name:'v'});
 expect(screen.getByTestId('dt-preview-draw')).not.toBeDisabled();
});
it('관리자 미리보기 팔레트와 후속 조회에 원자료 연구실 전달',async()=>{
 const requests:Request[]=[];
 vi.stubGlobal('fetch',async(r:Request)=>{requests.push(r);return new Response(JSON.stringify(r.url.includes('palettes')?{items:[]}:{renderId:'r',status:'그리는 중'}),{headers:{'Content-Type':'application/json'}});});
 const source=apiDatasetPreviewSource('d','lab-b');
 await source.palettes();await source.get('r');
 expect(requests.map(r=>r.headers.get('X-CoLAB-Target-Lab'))).toEqual(['lab-b','lab-b']);
});
it('관리자 프로젝트 생성은 대상 연구실 선택 필수',async()=>{
 vi.stubGlobal('fetch',async()=>new Response(JSON.stringify({labs:[{labId:'b',name:'연구실 B'}],roles:[]}),{headers:{'Content-Type':'application/json'}}));
 const submit=vi.fn(async()=>{});
 render(<SessionProvider account={account}><ProjectFormModal mode={{kind:'새 프로젝트'}} onSubmit={submit} onClose={()=>{}}/></SessionProvider>);
 fireEvent.change(screen.getByLabelText('이름'),{target:{value:'새 과제'}});
 fireEvent.click(screen.getByRole('button',{name:'만들기'}));
 expect(await screen.findByRole('alert')).toHaveTextContent('연구실');
 expect(submit).not.toHaveBeenCalled();
 fireEvent.change(await screen.findByLabelText('대상 연구실'),{target:{value:'b'}});
 fireEvent.click(screen.getByRole('button',{name:'만들기'}));
 expect(submit).toHaveBeenCalledWith(expect.objectContaining({name:'새 과제'}),'b');
});
it('업로드 미리보기 변수 조회 실패도 재시도 안내', async()=>{
 const { PreviewPanel } = await import('../src/components/upload/PreviewPanel');
 const source = {palettes:async()=>[{palette:'v'}],files:async()=>[],describe:async()=>{throw new Error('이 작업을 할 권한이 없어요.');}} as never;
 render(<PreviewPanel source={source} uploadId="up" hasReferenceGrid={false}/>);
 expect(await screen.findByText('이 작업을 할 권한이 없어요.')).toBeVisible();
 expect(screen.getByRole('button',{name:'다시 불러오기'})).toBeVisible();
});
it('업로드 생성과 프로젝트 빠른 생성에 선택 연구실 전달',async()=>{
 const { apiProjectSource }=await import('../src/components/upload/projectSource');
 const requests:Request[]=[];
 vi.stubGlobal('fetch',async(r:Request)=>{requests.push(r);return new Response(JSON.stringify({projectId:'p',name:'n',type:'논문',items:[]}),{headers:{'Content-Type':'application/json'}});});
 const source=apiProjectSource('lab-b');await source.list();await source.create({type:'논문',name:'n'});
 expect(requests.map(r=>r.headers.get('X-CoLAB-Target-Lab'))).toEqual(['lab-b','lab-b']);
});
it('연구실 설정은 관리자가 연구실을 고른 후 연다',async()=>{
 const {LabSettingsPage}=await import('../src/routes/LabSettingsPage');
 vi.stubGlobal('fetch',async()=>new Response(JSON.stringify({labs:[{labId:'b',name:'연구실 B'}],roles:[]}),{headers:{'Content-Type':'application/json'}}));
 render(<SessionProvider account={account}><LabSettingsPage/></SessionProvider>);
 expect(await screen.findByLabelText('대상 연구실')).toBeVisible();
});
it('교수 관리자 표시와 비공개 관리 접근 안내',async()=>{
 const {roleLabel}=await import('../src/components/members/permissions');
 const {accessNote}=await import('../src/components/common/accessState');
 expect(roleLabel({role:'교수'} as never)).toBe('교수 관리자');
 expect(accessNote('잠김')).toContain('시스템 관리자');
});
it.each([[403,'이 작업을 할 권한이 없어요.'],[404,'대상이 없거나 접근 권한이 없어요.']])('변수 조회 HTTP %s의 경계를 안내',async(status,message)=>{
 vi.stubGlobal('fetch',async()=>new Response(JSON.stringify({message:'internal detail'}),{status,headers:{'Content-Type':'application/json'}}));
 await expect(apiDatasetPreviewSource('d').describe!('f')).rejects.toThrow(message);
});
it('일반 사용자의 미리보기 후속 요청에는 관리자 연구실 헤더가 없다',async()=>{
 let header:string|null='unexpected';
 vi.stubGlobal('fetch',async(r:Request)=>{header=r.headers.get('X-CoLAB-Target-Lab');return new Response(JSON.stringify({renderId:'r',status:'그리는 중'}),{headers:{'Content-Type':'application/json'}});});
 await apiDatasetPreviewSource('d').get('r');expect(header).toBeNull();
});
it('기존 미등록 미리보기 URL도 서버 업로드 소속으로 후속 조회',async()=>{
 const {apiPreviewSource}=await import('../src/components/preview/previewSource');
 const requests:Request[]=[];
 vi.stubGlobal('fetch',async(r:Request)=>{requests.push(r);return new Response(JSON.stringify(r.url.includes('/uploads/')?{labId:'b',files:[]}:{renderId:'r',status:'그리는 중'}),{headers:{'Content-Type':'application/json'}});});
 await apiPreviewSource('u',true).get('r');
 expect(requests.at(-1)?.headers.get('X-CoLAB-Target-Lab')).toBe('b');
});
it.each(['get','files','describe','create','restore'] as const)('기존 미등록미리보기 %s 403은 권한안내로 구별', async(operation)=>{
 const {apiPreviewSource}=await import('../src/components/preview/previewSource');
 vi.stubGlobal('fetch',async()=>new Response(JSON.stringify({message:'internal authorization detail'}),{status:403,headers:{'Content-Type':'application/json'}}));
 const source=apiPreviewSource('u',operation==='restore');
 const request=operation==='get'||operation==='restore' ? source.get('r') : operation==='files' ? source.files!() : operation==='describe' ? source.describe!() : source.create({uploadId:'u',palette:'viridis',classCount:6,withoutReferenceGrid:false});
 await expect(request).rejects.toThrow('이 작업을 할 권한이 없어요.');
});
