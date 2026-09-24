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
import { AccountAdminPage } from './src/routes/AccountAdminPage';
import { PasswordChangePage } from './src/auth/PasswordChangePage';
import type { Schemas } from './src/api/client';

// account-admin 장면이 부르는 두 경로만 로컬 응답을 준다(`api/client.ts` 가 호출 시점에 `globalThis.fetch` 를 찾는다).
const ADMIN_OPTIONS: Schemas['AccountOptions'] = {labs: [{labId: '01JYZ9K7WQ3N8V4M2X6C5B0AHU', name: '수자원순환연구실'}, {labId: '01JYZ9K7WQ3N8V4M2X6C5B0AHV', name: '기후예측연구실'}], roles: ['교수', '연구원']};
const ADMIN_ACCOUNTS: Schemas['ServiceAccountListV2'] = {accounts: [
  {accountId: '01JYZ9K7WQ3N8V4M2X6C5B0AD1', email: 'op@example.ac.kr', name: '운영자', labId: null, labName: null, role: null, status: 'active', lastLoginAt: '2026-09-20T09:00:00Z', operator: true},
  {accountId: '01JYZ9K7WQ3N8V4M2X6C5B0AD2', email: 'lion@example.ac.kr', name: '사자 교수', labId: '01JYZ9K7WQ3N8V4M2X6C5B0AHU', labName: '수자원순환연구실', role: '교수', status: 'active', lastLoginAt: '2026-09-19T01:30:00Z', operator: false},
  {accountId: '01JYZ9K7WQ3N8V4M2X6C5B0AD3', email: 'tiger@example.ac.kr', name: '호랑이', labId: '01JYZ9K7WQ3N8V4M2X6C5B0AHU', labName: '수자원순환연구실', role: '연구원', status: 'active', lastLoginAt: null, operator: false},
  {accountId: '01JYZ9K7WQ3N8V4M2X6C5B0AD4', email: 'a.very.long.researcher.mailbox.name.for.layout@hydrology.example.ac.kr', name: '표범', labId: '01JYZ9K7WQ3N8V4M2X6C5B0AHV', labName: '기후예측연구실', role: '연구원', status: 'active', lastLoginAt: '2026-09-02T12:00:00Z', operator: false},
  {accountId: '01JYZ9K7WQ3N8V4M2X6C5B0AD5', email: 'cheetah@example.ac.kr', name: '치타', labId: '01JYZ9K7WQ3N8V4M2X6C5B0AHV', labName: '기후예측연구실', role: '교수', status: 'inactive', lastLoginAt: '2026-08-11T08:00:00Z', operator: false},
]};
// Fallback ports show explicit fixture failure instead of contacting any backend.
globalThis.fetch = async (input: RequestInfo | URL) => {
  const path = new URL(input instanceof Request ? input.url : String(input), location.href).pathname;
  const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), {status, headers: {'Content-Type': 'application/json'}});
  if (scene === 'account-admin' && path.endsWith('/admin/accounts-v2')) return json(ADMIN_ACCOUNTS);
  if (scene === 'account-admin' && path.endsWith('/admin/account-options')) return json(ADMIN_OPTIONS);
  return json({message: '시각 검수용 응답: 이 기능의 서버 호출은 차단됩니다.'}, 503);
};
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
// design=calm: design-preview.html 의 「제안」 — GNB 없는 화면. 테마는 정본 다크 블록(`:root[data-theme="dark"]`)이
// 읽는 <html> 에 건다(P1 · 종전 body 의 data-theme 은 tokens.css 의 body.design-preview 별칭에 기댔다).
if (previewParams.get('design') === 'calm') {
  document.body.classList.add('design-preview');
  document.documentElement.dataset.theme = previewParams.get('theme') === 'dark' ? 'dark' : 'light';
}
const scene = previewParams.get('scene') ?? 'catalog';
const full = previewParams.get('design') === 'full';
if (full) {
  document.body.classList.add('colab-ui');
  document.documentElement.dataset.theme = previewParams.get('theme') === 'dark' ? 'dark' : 'light';
  document.documentElement.dataset.themePreference = document.documentElement.dataset.theme;
}
const members = { list: async () => ({ok: true as const, items: [professor('p1', '사자 교수'), researcher('r1', '호랑이', {'업로드·편집': true, '프로젝트 생성': true}), researcher('r2', '표범', {})]}), save: blocked };
const searchSource: SearchSource = {search: async () => {
  if (scene === 'search-down') throw new SearchUnavailable();
  const items = scene === 'search-empty' ? [] : FIXTURE_ROWS.slice(0, 3).map(row => ({...row, summary: '강수 관측과 유역 분석을 위한 연구 자료', period: null, relevanceBar: 0.8, rationale: '이름과 주제에 검색어가 포함되어 있어요.'}));
  return {scope: {labId: 'lab', labName: '수자원순환연구실', searchedCount: 128}, isDataQuery: true, degraded: scene === 'search-degraded', items, totalCount: items.length, nextCursor: null};
}};
const previewJob: RenderJob = scene === 'preview-done' ? {target: {uploadId: 'upload'}, renderId: 'render', status: '완료', result: {tileUrlTemplate: `${auditTileUrl}?z={z}&x={x}&y={y}`, bounds: {west:126.5,south:34.8,east:129.6,north:37.2}, legend: {palette:'viridis',variable:'rain',unit:'mm/h',classes:[{color:'#21918c',min:0,max:5}]}}} : {target: {uploadId: 'upload'}, renderId: 'render', status: '실패', failure: {code: 'RENDER_FAILED', message: '파일을 그리지 못했어요.'}};
const previewSource: PreviewSource = { get: async () => {if (scene === 'preview-expired') throw new PreviewGone(); return previewJob;}, create: async () => previewJob, probeTile: async () => 'ok'};
const empty = scene === 'empty';
const source = fullSource(empty ? {
  summary: async () => ({projectCount: 0, datasetCount: 0, lineageSettledCount: 0, lineageUnsettledCount: 0, verifiedCount: 0}),
  dataMap: async () => ({totalCount: 0, byLineageState: [], byTopic: []}),
  activities: async () => [], lineageTodo: async () => [],
} : {});
// scene=primitives — 프리미티브 갤러리(spec S-DESIGN-STRUCTURE-P5-20260924). 6계열 × 정적 상태(기본 · 수식자 · disabled)를
// primitives.css 클래스만으로 그린다. 제품 컴포넌트를 import 하지 않는다 — 이 장면은 프리미티브 CSS 만 보여 준다.
// hover·focus 는 정적 캡처가 재현하지 못해 그리지 않는다. `.modal-back` 은 화면 전체를 덮는 fixed 뒤판이라 빼고
// 대화상자 판(`.modal.modal--dialog`)만 제자리에 연 상태로 둔다(뒤판 모양은 lab-dialog·project-dialog 장면이 찍는다).
const GALLERY_ROWS = [
  {name: '낙동강 강우 원자료', kind: '원천', size: '148 MB'},
  {name: '낙동강 강우 격자화', kind: '가공', size: '96 MB'},
  {name: '한강 유출량', kind: '원천', size: '12 MB'},
];
function PrimitivesGallery() {
  return <main className="primitives-gallery" data-screen="primitives">
    <h1>프리미티브 갤러리</h1>
    <p>기본값 = <code>primitives.css</code> · 목록 = <code>primitives.txt</code> · 정적 상태만(hover·focus 없음).</p>
    <section data-family="btn" aria-labelledby="pg-btn">
      <h2 id="pg-btn">btn — 버튼</h2>
      <p>
        <button className="btn" type="button">.btn</button>{' '}
        <button className="btn btn-primary" type="button">.btn-primary</button>{' '}
        <button className="btn btn-secondary" type="button">.btn-secondary</button>{' '}
        <button className="btn btn-ghost" type="button">.btn-ghost</button>{' '}
        <button className="btn btn-danger" type="button">.btn-danger</button>{' '}
        <button className="btn btn-sm" type="button">.btn-sm</button>
      </p>
      <p>
        <button className="btn" type="button" disabled>.btn disabled</button>{' '}
        <button className="btn btn-primary" type="button" disabled>.btn-primary disabled</button>{' '}
        <button className="btn btn-secondary" type="button" disabled>.btn-secondary disabled</button>{' '}
        <button className="btn btn-ghost" type="button" disabled>.btn-ghost disabled</button>{' '}
        <button className="btn btn-danger" type="button" disabled>.btn-danger disabled</button>
      </p>
    </section>
    <section data-family="field" aria-labelledby="pg-field">
      <h2 id="pg-field">field — 입력·선택</h2>
      <p>
        <input className="inp" aria-label=".inp" defaultValue=".inp 값" />{' '}
        <input className="inp" aria-label=".inp 자리표시" placeholder=".inp 자리표시" />{' '}
        <input className="inp" aria-label=".inp disabled" defaultValue=".inp disabled" disabled />
      </p>
      <p>
        <select className="sel" aria-label=".sel" defaultValue="a"><option value="a">.sel 선택</option><option value="b">둘째</option></select>{' '}
        <select className="sel" aria-label=".sel disabled" defaultValue="a" disabled><option value="a">.sel disabled</option></select>
      </p>
    </section>
    <section data-family="chip" aria-labelledby="pg-chip">
      <h2 id="pg-chip">chip — 칩</h2>
      <p>
        <span className="chip">.chip</span>
        <span className="chip chip--off">.chip--off</span>
        <span className="chip chip--verified">.chip--verified</span>
        <span className="chip chip--lineage">.chip--lineage</span>
        <span className="chip chip--neutral">.chip--neutral</span>
        <span className="chip chip--warning">.chip--warning</span>
      </p>
    </section>
    <section data-family="card" aria-labelledby="pg-card">
      <h2 id="pg-card">card — 카드</h2>
      <div className="card">
        <div className="card-h"><h3>.card-h 제목</h3><button className="btn" type="button">동작</button></div>
        <div className="card-b">.card-b 본문 — 카드 몸의 여백과 글자를 본다.</div>
      </div>
    </section>
    <section data-family="table" aria-labelledby="pg-table">
      <h2 id="pg-table">table — 표</h2>
      <p className="table-scroll-hint">.table-scroll-hint — 좁은 화면에서 표를 좌우로 움직여 봅니다.</p>
      <div className="tblwrap">
        <table className="tbl">
          <thead><tr><th scope="col">.tbl 이름</th><th scope="col">종류</th><th scope="col">크기</th></tr></thead>
          <tbody>{GALLERY_ROWS.map(row => <tr key={row.name}><td>{row.name}</td><td>{row.kind}</td><td>{row.size}</td></tr>)}</tbody>
        </table>
      </div>
    </section>
    <section data-family="modal" aria-labelledby="pg-modal">
      <h2 id="pg-modal">modal — 대화상자</h2>
      <div className="modal modal--dialog" role="dialog" aria-labelledby="pg-modal-title">
        <div className="modal-h"><h3 id="pg-modal-title">.modal-h 제목</h3></div>
        <div className="modal-b">.modal-b 본문 — 열린 상태를 뒤판 없이 제자리에 둔다.</div>
        <div className="modal-f"><button className="btn btn-secondary" type="button">취소</button><button className="btn btn-primary" type="button">확인</button></div>
      </div>
    </section>
  </main>;
}
function Scene() {
  const [open, setOpen] = useState(true);
  const close = () => setOpen(false);
  if (scene === 'primitives') return <PrimitivesGallery />;
  if (scene === 'lineage-picker') return <main className="lin">{open && <ParentPicker candidates={FIXTURE_ROWS} selfLv={2} levelFilter={null} onLevelFilterChange={() => {}} onPick={close} onClose={close} testId="audit-parent-picker" />}</main>;
  if (scene === 'not-found') return <NotFoundPage />;
  if (scene === 'members') return <main className="settings-page"><MemberPermissionGrid port={members} /></main>;
  if (scene.startsWith('search')) return <SearchResultsPage source={searchSource} />;
  if (scene.startsWith('preview')) return <Routes><Route path="/datasets/preview/:uploadId" element={<UnregisteredPreviewPage source={previewSource} />} /></Routes>;
  if (scene === 'project-detail') return <Routes><Route path="/projects/:projectId" element={<ProjectDetailPage source={fixtureProjectSource()} />} /></Routes>;
  if (scene === 'login') return <LoginPage />;
  if (scene === 'password-change') return <PasswordChangePage />;
  if (scene === 'account-admin') return <main className="appmain"><AccountAdminPage /></main>;
  if (scene === 'settings') return <LabSettingsPage port={members} labSource={{read: source.lab, update: blocked}} />;
  if (scene === 'lab' || scene === 'empty' || scene === 'gnb-more') return <LabPage source={source} />;
  if (scene === 'lab-dialog') return <><LabPage source={source} />{open && <LabInfoModal source={source} onClose={close} />}</>;
  if (scene === 'projects' || scene === 'project-table') return <ProjectsPage source={fixtureProjectSource()} />;
  if (scene === 'project-dialog' || scene === 'project-close') return <><ProjectsPage source={fixtureProjectSource()} />{open && (scene === 'project-close' ? <ProjectCloseModal detail={FIXTURE_PROJECTS[0]!} onConfirm={blocked} onClose={close} /> : <ProjectFormModal mode={{kind:'새 프로젝트'}} onSubmit={blocked} onClose={close} />)}</>;
  if (scene === 'access' || scene === 'pending') return <main className="detail-page" data-screen="S-05"><h1>잠긴 데이터셋</h1><AccessRequestPanel datasetId="fixture" canRequestAccess accessRequestPending={scene === 'pending'} source={approval} /></main>;
  if (scene === 'approval' || scene === 'approval-dialog') return <main className="detail-page" data-screen="S-05"><h1>승인된 데이터셋</h1><VerificationAction detail={{...Object.values(FIXTURE_DETAILS)[0]!, actions: {...Object.values(FIXTURE_DETAILS)[0]!.actions, canRequestVerification:false, canApproveVerification:false, canCancelVerification:true}}} source={approval} /></main>;
  if (scene === 'detail') return <Routes><Route path="/datasets/:datasetId" element={<DatasetDetailPage source={fixtureDetailSource()} lineageSource={fixtureLineageSource()} />} /></Routes>;
  return <Routes><Route path="/datasets" element={<DatasetsPage source={fixtureCatalogSource()} />} /><Route path="/datasets/:datasetId" element={<main data-screen="fixture-detail"><h1>데이터셋 상세 진입 확인</h1></main>} /></Routes>;
}
// 계정 플래그 — `scripts/visual-baseline/scenes.json` 이 장면마다 `upload`·`labSettings`·`operator` 를 고정한다.
// 값이 없으면 종전 기본값(업로드 = full 또는 detail · 연구실 설정 켬 · 운영자 아님)을 쓴다.
const flag = (key: string, fallback: boolean) => previewParams.has(key) ? previewParams.get(key) === '1' : fallback;
const sessionAccount = {...account({'연구실 설정': flag('labSettings', true), '프로젝트 생성': true, '업로드·편집': flag('upload', full || scene === 'detail')}), ...(flag('operator', scene === 'account-admin') ? {canManageServiceAccounts: true} : {})};
// 제품에서 GNB 없이 단독 렌더되는 화면(`AuthGate`) · 프리미티브 갤러리(P5 · 제품 화면이 아니다).
const STANDALONE = ['login', 'password-change', 'primitives'];
const entry = scene === 'detail' ? '/datasets/01JYZ9K7WQ3N8V4M2X6C5B0AA1' : scene === 'project-detail' ? `/projects/${FIXTURE_PROJECTS[0]!.projectId}` : scene.startsWith('search') ? '/datasets/search?q=강수' : scene.startsWith('preview') ? '/datasets/preview/upload?render=render' : scene.startsWith('project') ? '/projects' : scene === 'lab' || scene === 'empty' || scene === 'gnb-more' ? '/lab' : scene === 'account-admin' ? '/account-admin' : '/datasets';
createRoot(document.getElementById('root')!).render(<MemoryRouter initialEntries={[scene.startsWith('preview') ? {pathname:'/datasets/preview/upload',search:'?render=render',state:{preview:{uploadId:'upload',renderId:'render',withoutReferenceGrid:true,basicInfo:{byteSize:148000000,variable:'rain'},files:[{fileId:'file',fileName:'rain.nc',kind:'본체',byteSize:148000000}]}}} : entry]}><SessionProvider account={sessionAccount}>{full && !STANDALONE.includes(scene) && <Gnb />}<Scene /></SessionProvider></MemoryRouter>);
