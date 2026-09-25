// 로컬 시각 검수 전용 진입점. 실제 네트워크·저장 API를 사용하지 않는다.
import './src/shell/styles';
import { createRoot } from 'react-dom/client';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { SessionProvider } from './src/permission/session';
import { DatasetDetailPage } from './src/routes/DatasetDetailPage';
import { fixtureDetailSource } from './src/components/detail/fixture';
import { fixtureLineageSource } from './src/components/lineage/graphFixture';
import { UploadModal } from './src/components/upload/UploadModal';
import { UploadEntry } from './src/components/upload/UploadEntry';
import { GridAttachEntry } from './src/components/upload/GridAttachEntry';
import type { CurrentAccount } from './src/api/client';
import type { UploadSources } from './src/components/upload/types';
const previewParams = new URLSearchParams(location.search);
document.body.classList.add('colab-ui');
document.documentElement.dataset.theme = previewParams.get('theme') === 'dark' ? 'dark' : 'light';
const id = '01JYZ9K7WQ3N8V4M2X6C5B0UP1';
let files: unknown[] = [];
const sources = {
  upload: {
    create: async (picked: {file: File; kind: string}[]) => {
      files = picked.map((p, i) => ({ fileId: `${id}${i}`, fileName: p.file.name,
        byteSize: p.file.size, kind: p.kind }));
      return { uploadId: id, files };
    },
    status: async () => ({ uploadId: id, files, ready: true, renderable: true,
      metadataComplete: true, failure: null }),
    register: async () => { throw new Error('시각 검수 전용: 저장하지 않습니다'); },
  },
  preview: {
    palettes: async () => [{ palette: 'viridis', label: '비리디스' }],
    createRender: async () => ({ renderId: id, status: '그리는 중', stage: '지도 그리는 중' }),
    getRender: async () => { throw new Error('시각 검수 전용 모의 오류'); },
  },
  projects: { list: async () => [{
    projectId: id,
    type: '국가과제',
    name: '긴 프로젝트 제목이 필터 너비를 넘어가더라도 선택 버튼을 밀어내지 않는지 확인하는 시각 검수용 과제',
  }] },
} as unknown as UploadSources;
// design-fix 후속 20260925 Q4 — `?register=ok` 일 때만 등록·반영이 성공하고, 모달을 실제 부모 두 입구
// (`UploadEntry` · `GridAttachEntry` · `useUploadModalPresence`)가 연다. 「등록 직후 0.3초 안에 닫고 다시 열기」를
// 로컬 실브라우저로 재는 자리다. 질의가 없으면 아래 기존 동작(등록 실패 · 빈 닫기) 그대로다. 서버 호출 0.
const registerOk = previewParams.get('register') === 'ok';
const okSources = {
  ...sources,
  upload: { ...sources.upload,
    register: async () => ({ datasetId: '01JYZ9K7WQ3N8V4M2X6C5B0DS1' }),
    attachGrid: async () => [] },
  lineage: {
    suggestions: async () => ({ degraded: false, scope: { labId: id, labName: '수자원순환연구실', searchedCount: 0 },
      rawDataLikely: false, suggestions: [] }),
    candidates: async () => [],
  },
} as unknown as UploadSources;
const account = { accountId: id, labId: id, name: '검수', labName: '수자원순환연구실',
  permissions: { '업로드·편집': true } } as unknown as CurrentAccount;
createRoot(document.getElementById('root')!).render(
  <MemoryRouter initialEntries={['/datasets/01JYZ9K7WQ3N8V4M2X6C5B0AA1']}><SessionProvider account={account}>
    {registerOk ? <main className="appmain" data-screen="audit-register-ok"><UploadEntry sources={okSources} /> <GridAttachEntry datasetId="01JYZ9K7WQ3N8V4M2X6C5B0AA1" datasetName="낙동강 강수" sources={okSources} /></main> : new URLSearchParams(location.search).get('scene') === 'detail' ? <Routes><Route path="/datasets/:datasetId" element={<DatasetDetailPage source={fixtureDetailSource()} lineageSource={fixtureLineageSource()} />} /></Routes> : <UploadModal sources={sources} onClose={() => {}} />}
  </SessionProvider></MemoryRouter>,
);
