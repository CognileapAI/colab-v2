// `#40` — **분석에 실패한 업로드도 등록할 수 있어야 한다.**
//
// 오라클 = 정본 `Policy_업로드와_계보_확정:192` 「감지 실패·그릴 수 없음·헤더 못 읽음은
// 등록을 막지 않는다」. 서버는 이미 그 규칙을 지킨다 —
// `services/core-api/tests/test_dataset_registration.py`
// `test_a_failed_pipeline_does_not_block_registration` 가 실패 업로드의 등록을 201 로 잰다.
// 위반은 화면 쪽이다 — `UploadModal` 의 `다음 →` 비활성 식이 `status.failure` 를 차단 항으로 쥐고 있다.
//
// ⚠ 워커는 실패 시 `ready=False` 를 함께 쓴다
// (`services/pipeline-worker/src/colab_pipeline/domains/d5_ingestion.py` `_fail`).
// 따라서 「분석이 끝났다」는 `ready || failure` 로 읽어야 한다 — `failure` 항만 빼면 `ready:false`
// 가 그대로 막는다.
import { act, fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';

import { SessionProvider } from '../src/permission/session';
import { UploadEntry } from '../src/components/upload/UploadEntry';
import type {
  PreviewSource,
  ProjectSource,
  UploadSource,
  UploadSources,
} from '../src/components/upload/types';
import type { LineageSource, LineageSuggestionResponse } from '../src/components/lineage/types';
import type { CurrentAccount, Schemas } from '../src/api/client';

const UPLOAD_ID = '01JYZ9K7WQ3N8V4M2X6C5B0UP1';
const FILE_ID = '01JYZ9K7WQ3N8V4M2X6C5B0FI1';
const PROJECT_ID = '01JYZ9K7WQ3N8V4M2X6C5B0PR1';
const FILE_NAME = 'nakdong_precip_2025_Lv2.nc';

function account(): CurrentAccount {
  return {
    accountId: '01JYZ9K7WQ3N8V4M2X6C5B0AC1',
    name: '호랑이',
    email: 'tiger@example.ac.kr',
    role: '연구원',
    labId: '01JYZ9K7WQ3N8V4M2X6C5B0LB1',
    labName: '수자원순환연구실',
    permissions: { '업로드·편집': true } as CurrentAccount['permissions'],
  } as CurrentAccount;
}

/**
 * 워커가 실패로 끝낸 업로드의 상태 응답.
 * 값 형상은 생성 타입 `frontend/src/generated/fe-core.ts` `UploadStatus.failure`
 * (`{ reason: FailureReason } | null`)를 그대로 따른다 — 서버가 실제로 돌려주는 것도
 * `{"reason": …}` 하나다(`test_dataset_registration.py:271`).
 */
function failedStatus(): Schemas['UploadStatus'] {
  return {
    uploadId: UPLOAD_ID,
    files: [{ fileId: FILE_ID, fileName: FILE_NAME, kind: '본체', byteSize: 148_000_000 }],
    ready: false,
    renderable: false,
    metadataComplete: false,
    expiresAt: '2026-08-24T00:00:00Z',
    failure: { reason: '형식 인식 실패' },
  } as Schemas['UploadStatus'];
}

function fakes(): UploadSources {
  const status = failedStatus();
  const upload: UploadSource = {
    async create(files) {
      return {
        uploadId: UPLOAD_ID,
        files: files.map((f) => ({
          fileId: FILE_ID,
          fileName: f.file.name,
          kind: f.kind,
          byteSize: f.file.size,
        })),
      };
    },
    async status() {
      return status;
    },
    async register() {
      return { datasetId: '01JYZ9K7WQ3N8V4M2X6C5B0DS1' };
    },
    async attachGrid() {
      return [];
    },
  };
  const preview: PreviewSource = {
    async palettes() {
      return [{ palette: 'viridis', label: '비리디스' }];
    },
    async createRender() {
      return { renderId: 'R1', status: '그리는 중', stage: '파일 읽는 중' } as never;
    },
    async getRender() {
      return { renderId: 'R1', status: '그리는 중', stage: '파일 읽는 중' } as never;
    },
  };
  const projects: ProjectSource = {
    async list() {
      return [
        {
          projectId: PROJECT_ID,
          name: '낙동강 유역 홍수기 강우-유출 응답 분석',
          type: '국가과제',
          status: '진행 중',
          period: null,
          description: null,
          datasetCount: 0,
          verifiedCount: 0,
          unknownLineageCount: 0,
        } as Schemas['ProjectRow'],
      ];
    },
    async create(body) {
      return { projectId: '01JYZ9K7WQ3N8V4M2X6C5B0PR9', name: body.name, type: body.type };
    },
  };
  const lineage: LineageSource = {
    async suggestions() {
      return {
        degraded: false,
        scope: {
          labId: '01JYZ9K7WQ3N8V4M2X6C5B0LB1',
          labName: '수자원순환연구실',
          searchedCount: 0,
        },
        rawDataLikely: false,
        suggestions: [],
      } as LineageSuggestionResponse;
    },
    async candidates() {
      return [];
    },
  };
  return { upload, preview, projects, lineage };
}

function makeFile(name: string, size = 148_000_000) {
  const f = new File(['x'], name, { type: 'application/octet-stream' });
  Object.defineProperty(f, 'size', { value: size });
  return f;
}

async function click(el: Element | null) {
  fireEvent.click(el as HTMLElement);
  await act(async () => {});
}

/** 파일 1건을 올리고 워커가 실패로 끝낸 상태까지 간다. */
async function dropOntoFailedUpload() {
  render(
    <MemoryRouter initialEntries={['/datasets']}>
      <SessionProvider account={account()}>
        <UploadEntry sources={fakes()} />
      </SessionProvider>
    </MemoryRouter>,
  );
  await click(screen.getByTestId('gnb-upload'));
  await screen.findByTestId('upload-modal');
  fireEvent.change(screen.getByTestId('up-drop-input'), { target: { files: [makeFile(FILE_NAME)] } });
  await act(async () => {});
  await screen.findByTestId('up-files');
  await screen.findByTestId('up-analysis-failure');
}

describe('`#40` — 분석 실패는 등록을 막지 않는다', () => {
  it('실패한 업로드에서도 `다음 →` 을 누를 수 있다', async () => {
    await dropOntoFailedUpload();
    expect(screen.getByTestId('reg-open')).toBeEnabled();
  });

  it('실패 안내가 「지도로 못 그린다 · 등록은 된다」를 함께 말한다', async () => {
    await dropOntoFailedUpload();
    const banner = screen.getByTestId('up-analysis-failure');
    expect(banner).toHaveTextContent('형식 인식 실패');
    expect(banner).toHaveTextContent('등록은 됩니다');
  });

  it('`다음 →` 을 누르면 등록 단계가 열린다', async () => {
    await dropOntoFailedUpload();
    await click(screen.getByTestId('reg-open'));
    expect(await screen.findByTestId('reg-steps')).toBeInTheDocument();
    expect(screen.getByTestId('reg-area')).toBeInTheDocument();
  });
});
