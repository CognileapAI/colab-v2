import './src/shell/styles';
import auditTileUrl from './audit-tile.svg?url';
// Local visual fixtures. No production API request or persistent write is allowed.
import { useState } from 'react';
import { createRoot } from 'react-dom/client';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { SessionProvider } from './src/permission/session';
import { account, professor, researcher } from './test/factories';
import { ParentPicker } from './src/components/lineage/ParentPicker';
import { Gnb } from './src/shell/Gnb';
import { ProjectDetailPage } from './src/routes/ProjectDetailPage';
import { NotFoundPage } from './src/routes/NotFoundPage';
import { SearchResultsPage } from './src/routes/SearchResultsPage';
import { SearchUnavailable, type SearchSource } from './src/components/search/types';
import { UnregisteredPreviewPage } from './src/routes/UnregisteredPreviewPage';
import { PreviewGone, type PreviewSource, type RenderJob } from './src/components/preview/types';
import { MemberPermissionGrid } from './src/components/members/MemberPermissionGrid';
import { LabPage } from './src/routes/LabPage';
import { LabInfoModal } from './src/components/dashboard/LabInfoModal';
import { GroupHidden, type DashboardSource } from './src/components/dashboard/types';
import { DatasetsPage } from './src/routes/DatasetsPage';
import { fixtureCatalogSource, FIXTURE_ROWS } from './src/components/catalog/fixture';
import { ProjectsPage } from './src/routes/ProjectsPage';
import { ProjectFormModal } from './src/components/project/ProjectFormModal';
import { ProjectCloseModal } from './src/components/project/ProjectCloseModal';
import { fixtureProjectSource, FIXTURE_PROJECTS } from './src/components/project/fixture';
import { LabSettingsPage } from './src/routes/LabSettingsPage';
import { LoginPage } from './src/auth/LoginPage';
import { DatasetDetailPage } from './src/routes/DatasetDetailPage';
import { fixtureDetailSource, FIXTURE_DETAILS } from './src/components/detail/fixture';
import { fixtureLineageSource } from './src/components/lineage/graphFixture';
import { AccessRequestPanel } from './src/components/approval/AccessRequestPanel';
import { VerificationAction } from './src/components/approval/VerificationAction';
import type { ApprovalSource } from './src/components/approval/types';

// Fallback ports show explicit fixture failure instead of contacting any backend.
window.fetch = async () => new Response(JSON.stringify({message: '시각 검수용 응답: 이 기능의 서버 호출은 차단됩니다.'}), {status: 503, headers: {'Content-Type': 'application/json'}});
const blocked = async (): Promise<never> => { throw new Error('시각 검수: 저장하지 않습니다.'); };
const approval: ApprovalSource = { requestAccess: blocked, requestVerification: blocked, approveVerification: blocked, cancelVerification: blocked };
const DS1 = '01JYZ9K7WQ3N8V4M2X6C5B0DS1';
const DS2 = '01JYZ9K7WQ3N8V4M2X6C5B0DS2';
const PRJ = '01JYZ9K7WQ3N8V4M2X6C5B0PR1';

/** 정본 §3.1 의 예시 값 — 확정 71 · 원천 16 · 확인 필요 25 · 기록 없음 16, 지표 87 · 미확정 41. */
function fullSource(over: Partial<DashboardSource> = {}): DashboardSource {
  return {
    summary: async () => ({
      projectCount: 4,
      datasetCount: 128,
      lineageSettledCount: 87,
      lineageUnsettledCount: 41,
      verifiedCount: 33,
    }),
    dataMap: async () => ({
      totalCount: 128,
      byLineageState: [
        { value: '확정', count: 71 },
        { value: '원천', count: 16 },
        { value: '확인 필요', count: 25 },
        { value: '기록 없음', count: 16 },
      ],
      byTopic: [{ value: '강우·강수', count: 80 }, { value: '토지피복·LULC', count: 48 }],
    }),
    activities: async () => [
      {
        activityId: '01JYZ9K7WQ3N8V4M2X6C5B0AC1',
        actor: { accountId: '01JYZ9K7WQ3N8V4M2X6C5B0LI1', name: '사자' },
        action: '데이터셋 등록',
        target: { kind: '데이터셋', id: DS1, name: '낙동강 강우 원자료' },
        occurredAt: '2026-08-30T09:00:00Z',
      },
    ],
    lab: async () => ({
      labId: '01JYZ9K7WQ3N8V4M2X6C5B0AHU',
      name: '수자원순환연구실',
      university: 'A 대학교',
      department: '토목공학과',
      principalInvestigator: '사자 교수',
      researchField: '수문학',
      introduction: '수문 자료를 다룬다',
      defaultVisibility: '열림',
      memberCount: 7,
      openedAt: '2020-03-01T00:00:00Z',
    }),
    lineageTodo: async () => [
      { datasetId: DS1, name: '낙동강 강우 원자료', lineageState: '기록 없음' },
      { datasetId: DS2, name: '낙동강 강우 격자화', lineageState: '확인 필요' },
      { datasetId: PRJ, name: '한강 유출량', lineageState: '확인 필요' },
      { datasetId: 'x4', name: '금강 수질', lineageState: '확인 필요' },
    ],
    // 기본은 **권한 없음** — 승인 계열 두 그룹은 서버가 403 을 내는 것이 기본값이다.
    pendingVerifications: async () => {
      throw new GroupHidden();
    },
    pendingAccessRequests: async () => {
      throw new GroupHidden();
    },
    approveAccessRequest: async () => undefined,
    rejectAccessRequest: async () => undefined,
    ...over,
  };
}


const previewParams = new URLSearchParams(location.search);
if (previewParams.get('design') === 'calm') {
  document.body.classList.add('design-preview');
  document.body.dataset.theme = previewParams.get('theme') === 'dark' ? 'dark' : 'light';
}
const scene = previewParams.get('scene') ?? 'catalog';
const full = previewParams.get('design') === 'full';
if (full) {
  document.body.classList.add('colab-ui');
  document.documentElement.dataset.design = 'calm';
  document.documentElement.dataset.theme = previewParams.get('theme') === 'dark' ? 'dark' : 'light';
  document.documentElement.dataset.themePreference = document.documentElement.dataset.theme;
}
const members = { list: async () => ({ok: true as const, items: [professor('p1', '사자 교수'), researcher('r1', '호랑이', {'업로드·편집': true, '프로젝트 생성': true}), researcher('r2', '표범', {})]}), save: blocked };
const searchSource: SearchSource = {search: async () => {
  if (scene === 'search-down') throw new SearchUnavailable();
  const items = scene === 'search-empty' ? [] : FIXTURE_ROWS.slice(0, 3).map(row => ({...row, summary: '강수 관측과 유역 분석을 위한 연구 자료', period: null, relevanceBar: 0.8, rationale: '이름과 주제에 검색어가 포함되어 있어요.'}));
  return {scope: {labId: 'lab', labName: '수자원순환연구실', searchedCount: 128}, isDataQuery: true, degraded: scene === 'search-degraded', items, totalCount: items.length, nextCursor: null};
}};
const previewJob: RenderJob = scene === 'preview-done' ? {renderId: 'render', status: '완료', result: {tileUrlTemplate: `${auditTileUrl}?z={z}&x={x}&y={y}`, bounds: {west:126.5,south:34.8,east:129.6,north:37.2}, legend: {palette:'viridis',variable:'rain',unit:'mm/h',classes:[{color:'#21918c',min:0,max:5}]}}} : {renderId: 'render', status: '실패', failure: {code: 'RENDER_FAILED', message: '파일을 그리지 못했어요.'}};
const previewSource: PreviewSource = { get: async () => {if (scene === 'preview-expired') throw new PreviewGone(); return previewJob;}, create: async () => previewJob, probeTile: async () => 'ok'};
const empty = scene === 'empty';
const source = fullSource(empty ? {
  summary: async () => ({projectCount: 0, datasetCount: 0, lineageSettledCount: 0, lineageUnsettledCount: 0, verifiedCount: 0}),
  dataMap: async () => ({totalCount: 0, byLineageState: [], byTopic: []}),
  activities: async () => [], lineageTodo: async () => [],
} : {});
function Scene() {
  const [open, setOpen] = useState(true);
  const close = () => setOpen(false);
  if (scene === 'lineage-picker') return <main className="lin">{open && <ParentPicker candidates={FIXTURE_ROWS} selfLv={2} levelFilter={null} onLevelFilterChange={() => {}} onPick={close} onClose={close} testId="audit-parent-picker" />}</main>;
  if (scene === 'not-found') return <NotFoundPage />;
  if (scene === 'members') return <main className="settings-page"><MemberPermissionGrid port={members} /></main>;
  if (scene.startsWith('search')) return <SearchResultsPage source={searchSource} />;
  if (scene.startsWith('preview')) return <Routes><Route path="/datasets/preview/:uploadId" element={<UnregisteredPreviewPage source={previewSource} />} /></Routes>;
  if (scene === 'project-detail') return <Routes><Route path="/projects/:projectId" element={<ProjectDetailPage source={fixtureProjectSource()} />} /></Routes>;
  if (scene === 'login') return <LoginPage />;
  if (scene === 'settings') return <LabSettingsPage port={members} labSource={{read: source.lab, update: blocked}} />;
  if (scene === 'lab' || scene === 'empty') return <LabPage source={source} />;
  if (scene === 'lab-dialog') return <><LabPage source={source} />{open && <LabInfoModal source={source} onClose={close} />}</>;
  if (scene === 'projects' || scene === 'project-table') return <ProjectsPage source={fixtureProjectSource()} />;
  if (scene === 'project-dialog' || scene === 'project-close') return <><ProjectsPage source={fixtureProjectSource()} />{open && (scene === 'project-close' ? <ProjectCloseModal detail={FIXTURE_PROJECTS[0]!} onConfirm={blocked} onClose={close} /> : <ProjectFormModal mode={{kind:'새 프로젝트'}} onSubmit={blocked} onClose={close} />)}</>;
  if (scene === 'access' || scene === 'pending') return <main className="detail-page" data-screen="S-05"><h1>잠긴 데이터셋</h1><AccessRequestPanel datasetId="fixture" canRequestAccess accessRequestPending={scene === 'pending'} source={approval} /></main>;
  if (scene === 'approval' || scene === 'approval-dialog') return <main className="detail-page" data-screen="S-05"><h1>승인된 데이터셋</h1><VerificationAction detail={{...Object.values(FIXTURE_DETAILS)[0]!, actions: {...Object.values(FIXTURE_DETAILS)[0]!.actions, canRequestVerification:false, canApproveVerification:false, canCancelVerification:true}}} source={approval} /></main>;
  if (scene === 'detail') return <Routes><Route path="/datasets/:datasetId" element={<DatasetDetailPage source={fixtureDetailSource()} lineageSource={fixtureLineageSource()} />} /></Routes>;
  return <Routes><Route path="/datasets" element={<DatasetsPage source={fixtureCatalogSource()} />} /><Route path="/datasets/:datasetId" element={<main data-screen="fixture-detail"><h1>데이터셋 상세 진입 확인</h1></main>} /></Routes>;
}
const entry = scene === 'detail' ? '/datasets/01JYZ9K7WQ3N8V4M2X6C5B0AA1' : scene === 'project-detail' ? `/projects/${FIXTURE_PROJECTS[0]!.projectId}` : scene.startsWith('search') ? '/datasets/search?q=강수' : scene.startsWith('preview') ? '/datasets/preview/upload?render=render' : scene.startsWith('project') ? '/projects' : scene === 'lab' || scene === 'empty' ? '/lab' : '/datasets';
createRoot(document.getElementById('root')!).render(<MemoryRouter initialEntries={[scene.startsWith('preview') ? {pathname:'/datasets/preview/upload',search:'?render=render',state:{preview:{uploadId:'upload',renderId:'render',withoutReferenceGrid:true,basicInfo:{byteSize:148000000,variable:'rain'},files:[{fileId:'file',fileName:'rain.nc',kind:'본체',byteSize:148000000}]}}} : entry]}><SessionProvider account={account({'연구실 설정':true,'프로젝트 생성':true,'업로드·편집': full || scene === 'detail'})}>{full && scene !== 'login' && <Gnb />}<Scene /></SessionProvider></MemoryRouter>);
