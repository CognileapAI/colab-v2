// 로컬 시각 검수 전용 진입점. 실제 네트워크·저장 API를 사용하지 않는다.
import { createRoot } from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';
import { SessionProvider } from './src/permission/session';
import { UploadModal } from './src/components/upload/UploadModal';
import type { CurrentAccount } from './src/api/client';
import type { UploadSources } from './src/components/upload/types';
import 'pretendard/dist/web/variable/pretendardvariable-dynamic-subset.css';
import './src/shell/shell.css';
import './src/components/upload/upload.css';
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
  projects: { list: async () => [] },
} as unknown as UploadSources;
const account = { accountId: id, labId: id, name: '검수', labName: '수자원순환연구실',
  permissions: { '업로드·편집': true } } as unknown as CurrentAccount;
createRoot(document.getElementById('root')!).render(
  <MemoryRouter><SessionProvider account={account}>
    <UploadModal sources={sources} onClose={() => {}} />
  </SessionProvider></MemoryRouter>,
);
