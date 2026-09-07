/**
 * advisor ② F1 (WU-B6) — 내려받은 날 형상 오류를 화면이 인라인으로 막는다.
 *
 * 오라클 = `dev-package/jobs/18e71f5e/tmp/advisor2-b6.md` F1 ㈀ 축자 —
 *   등록 `submit()` 직전과 수정 폼 저장 직전에 형상이 틀리면 **전송하지 않고**
 *   해당 칸 아래에 서버 400 과 같은 문구 `내려받은 날은 날짜(YYYY-MM-DD)다.` 를 보인다.
 *
 * ⛔ 서버 400 이 화면에 닿지 않아 일반 실패 문구(「데이터셋을 만들지 못했어요…」)로
 *    덮이던 경로의 회귀 시험이다 — 재시도로 해소되지 않는 원인을 재시도하라고
 *    안내하던 막다른 길을 여기서 닫는다.
 *
 * 모든 단언은 **대상 건수를 먼저 잰다** — 빈 집합 통과(green-by-skip)를 막는다.
 */
import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { SessionProvider } from '../src/permission/session';
import { UploadEntry } from '../src/components/upload/UploadEntry';
import { LV0 } from '../src/components/upload/RegisterArea';
import { SOURCE_DOWNLOADED_ON_INVALID } from '../src/components/common/toastCopy';
import { DatasetDetailPage } from '../src/routes/DatasetDetailPage';
import { FIXTURE_DETAILS } from '../src/components/detail/fixture';
import type { DatasetDetail, DetailSource } from '../src/components/detail/types';
import type { DatasetUpdateSource } from '../src/components/detail/updateSource';
import type {
  LineageSource,
  LineageSuggestionResponse,
} from '../src/components/lineage/types';
import type {
  PreviewSource,
  ProjectSource,
  UploadSource,
  UploadSources,
} from '../src/components/upload/types';
import type { CurrentAccount, Schemas } from '../src/api/client';

const UPLOAD_ID = '01JYZ9K7WQ3N8V4M2X6C5B0UP1';
const FILE_ID = '01JYZ9K7WQ3N8V4M2X6C5B0FI1';
const DATASET_ID = '01JYZ9K7WQ3N8V4M2X6C5B0DS1';

function account(): CurrentAccount {
  return {
    accountId: '01JYZ9K7WQ3N8V4M2X6C5B0AC1',
    name: '호랑이',
    email: 'tiger@example.ac.kr',
    role: '연구원',
    labId: '01JYZ9K7WQ3N8V4M2X6C5B0LB1',
    labName: '수자원순환연구실',
    permissions: {
      '업로드·편집': true,
      '프로젝트 생성': true,
      '승인 위임': false,
      '연구실 설정': false,
    } as Record<Schemas['PermissionSwitch'], boolean>,
  } as unknown as CurrentAccount;
}

interface Calls {
  registered: Record<string, unknown>[];
}

function fakes() {
  const calls: Calls = { registered: [] };
  const upload: UploadSource = {
    async create() {
      return {
        uploadId: UPLOAD_ID,
        files: [
          {
            fileId: FILE_ID,
            fileName: 'nakdong_precip_2025_Lv2.nc',
            kind: '본체',
            byteSize: 349_000,
            createdAt: '2026-09-07T00:00:00Z',
          },
        ],
      } as never;
    },
    async status() {
      return {
        uploadId: UPLOAD_ID,
        ready: true,
        failure: null,
        metadataComplete: true,
        files: [
          {
            fileId: FILE_ID,
            fileName: 'nakdong_precip_2025_Lv2.nc',
            kind: '본체',
            byteSize: 349_000,
            createdAt: '2026-09-07T00:00:00Z',
          },
        ],
      } as never;
    },
    async register(body: Record<string, unknown>) {
      calls.registered.push(body as unknown as Record<string, unknown>);
      return { datasetId: DATASET_ID } as never;
    },
    async attachGrid() {
      return [] as never;
    },
  } as unknown as UploadSource;
  const preview: PreviewSource = {
    async palettes() {
      return [{ palette: 'viridis', label: '비리디스' }];
    },
    async createRender() {
      return { renderId: 'r', state: '실패', failure: null } as never;
    },
    async getRender() {
      return { renderId: 'r', state: '실패', failure: null } as never;
    },
  } as unknown as PreviewSource;
  const projects: ProjectSource = {
    async list() {
      return [];
    },
    async create() {
      return { projectId: '01JYZ9K7WQ3N8V4M2X6C5B0PR9', name: 'x', type: '국가과제' } as never;
    },
  } as unknown as ProjectSource;
  const lineage: LineageSource = {
    async suggestions() {
      return {
        degraded: false,
        scope: { labId: 'l', labName: '수자원순환연구실', searchedCount: 0 },
        rawDataLikely: false,
        suggestions: [],
      } as unknown as LineageSuggestionResponse;
    },
    async candidates() {
      return [];
    },
  } as unknown as LineageSource;
  return { sources: { upload, preview, projects, lineage } as UploadSources, calls };
}

async function click(el: Element | null) {
  fireEvent.click(el as HTMLElement);
  await act(async () => {});
}

async function change(el: Element | null, value: string) {
  fireEvent.change(el as HTMLElement, { target: { value } });
  await act(async () => {});
}

function makeFile(name = 'nakdong_precip_2025_Lv2.nc') {
  const f = new File(['x'], name, { type: 'application/octet-stream' });
  Object.defineProperty(f, 'size', { value: 349_000 });
  return f;
}

async function openRegister(sources: UploadSources) {
  render(
    <MemoryRouter initialEntries={['/datasets']}>
      <SessionProvider account={account()}>
        <UploadEntry sources={sources} />
      </SessionProvider>
    </MemoryRouter>,
  );
  await click(screen.getByTestId('gnb-upload'));
  await screen.findByTestId('upload-modal');
  fireEvent.change(screen.getByTestId('up-drop-input'), { target: { files: [makeFile()] } });
  await act(async () => {});
  await screen.findByTestId('up-files');
  await click(await screen.findByTestId('reg-open'));
  await screen.findByTestId('reg-steps');
}

async function goStep(n: '①' | '②' | '③') {
  await click(screen.getByRole('button', { name: new RegExp(`^${n}`) }));
}

async function pickLevel(value: string) {
  await goStep('①');
  await change(screen.getByTestId('reg-level'), value);
}

describe('advisor ② F1 · WU-B6 — 등록 형상 인라인 선검사', () => {
  it('오타 입력 (`2026.08.20`) → `createDataset`(`register`) 미호출 ∧ 서버 문구가 칸 아래에 뜬다', async () => {
    const { sources, calls } = fakes();
    await openRegister(sources);
    await pickLevel(LV0);
    await goStep('②');
    await change(screen.getByTestId('reg-summary'), '시험용 설명 한 줄');
    await goStep('③');
    await change(screen.getByTestId('reg-source-downloaded-on'), '2026.08.20');
    await click(screen.getByTestId('reg-done'));

    expect(calls.registered).toHaveLength(0);
    const err = screen.getByTestId('reg-source-downloaded-on-error');
    expect(err.textContent).toBe(SOURCE_DOWNLOADED_ON_INVALID);
    expect(SOURCE_DOWNLOADED_ON_INVALID).toBe('내려받은 날은 날짜(YYYY-MM-DD)다.');
  });
});

const DETAIL_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA1';
const DETAIL_BASE = FIXTURE_DETAILS[DETAIL_ID] as DatasetDetail;

function deferredUpdateSource() {
  const calls: { datasetId: string }[] = [];
  const source: DatasetUpdateSource = {
    async update(datasetId) {
      calls.push({ datasetId });
      return { ...DETAIL_BASE };
    },
  };
  return { calls, source };
}

function mountDetail(updateSource: DatasetUpdateSource) {
  const source: DetailSource = { async get() { return DETAIL_BASE; } };
  return render(
    <MemoryRouter initialEntries={[`/datasets/${DETAIL_ID}`]}>
      <SessionProvider account={account()}>
        <Routes>
          <Route
            path="/datasets/:datasetId"
            element={<DatasetDetailPage source={source} updateSource={updateSource} />}
          />
          <Route path="/datasets" element={<div>카탈로그</div>} />
        </Routes>
      </SessionProvider>
    </MemoryRouter>,
  );
}

describe('advisor ② F1 · WU-B6 — 수정 폼 저장 형상 인라인 선검사', () => {
  it('오타 입력 (`8/20`) → PATCH 미호출 ∧ 서버 문구가 칸 아래에 뜬다', async () => {
    const { source, calls } = deferredUpdateSource();
    mountDetail(source);
    await screen.findByRole('heading', { level: 1, name: DETAIL_BASE.name });
    await act(async () => {});
    await click(await screen.findByTestId('detail-edit-open'));
    const form = await screen.findByTestId('detail-edit-form');

    await change(within(form).getByTestId('edit-sourceDownloadedOn'), '8/20');
    await click(screen.getByTestId('detail-edit-save'));

    expect(calls).toHaveLength(0);
    const err = within(form).getByTestId('edit-sourceDownloadedOn-error');
    expect(err.textContent).toBe(SOURCE_DOWNLOADED_ON_INVALID);
  });
});
