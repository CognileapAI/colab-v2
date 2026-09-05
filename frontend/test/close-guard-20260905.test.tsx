// WU-A9 · PRD-14 · 미결-15 ⓐ — 종료 확인 **조건**을 고친다. 문면은 종전 그대로다.
//
// 오라클 = `dev-package/prd/rounds/R-A-3-frontend.md` §2 WU-A9 수용 기준.
// 종전 조건 = 「등록 단계가 열려 있다」. 새 조건 = 「**사람이 입력한 값이 하나라도 있다**」.
// 판정 대상 = ①②③ 의 사람 입력 필드 전부 ＋ 확정된 계보 부모 건수.
// 자동으로 채워진 값(파일명에서 만든 이름 초안 · 확장자 · 용량 · 읽기 전용 가공 단계)은 **세지 않는다**.
// 계약·서버·DB 변경 0.
import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';

import { SessionProvider } from '../src/permission/session';
import { UploadEntry } from '../src/components/upload/UploadEntry';
import type {
  LineageStepContext,
  PreviewSource,
  ProjectSource,
  UploadSource,
  UploadSources,
} from '../src/components/upload/types';
import type { LineageSource, LineageSuggestionResponse } from '../src/components/lineage/types';
import type { CurrentAccount, Schemas } from '../src/api/client';

/** 종전 문면 — 이 문자열이 바뀌면 미결-15 ⓐ 위반이다 (PRD-34 는 §4 범위 밖). */
const CONFIRM_BODY = '확인한 계보와 입력한 내용이 사라져요. 데이터셋은 만들어지지 않아요.';

const UPLOAD_ID = '01JYZ9K7WQ3N8V4M2X6C5B0UP1';
const FILE_ID = '01JYZ9K7WQ3N8V4M2X6C5B0FI1';
const PROJECT_ID = '01JYZ9K7WQ3N8V4M2X6C5B0PR1';
const NDVI_ID = '01JYZ9K7WQ3N8V4M2X6C5B0PA1';
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

function fakes(): UploadSources {
  const status: Schemas['UploadStatus'] = {
    uploadId: UPLOAD_ID,
    files: [{ fileId: FILE_ID, fileName: FILE_NAME, kind: '본체', byteSize: 148_000_000 }],
    ready: true,
    renderable: true,
    metadataComplete: true,
    expiresAt: '2026-08-24T00:00:00Z',
    failure: null,
  } as Schemas['UploadStatus'];

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

async function change(el: Element | null, value: string) {
  fireEvent.change(el as HTMLElement, { target: { value } });
  await act(async () => {});
}

/** 파일 1건을 올리고 등록 단계까지 연 상태. 사람이 적은 값은 **아직 0** 이다. */
async function openRegisterWithFile(opts: {
  lineageStep?: (ctx: LineageStepContext) => React.ReactNode;
} = {}) {
  const sources = fakes();
  render(
    <MemoryRouter initialEntries={['/datasets']}>
      <SessionProvider account={account()}>
        <UploadEntry sources={sources} lineageStep={opts.lineageStep} />
      </SessionProvider>
    </MemoryRouter>,
  );
  await click(screen.getByTestId('gnb-upload'));
  await screen.findByTestId('upload-modal');
  fireEvent.change(screen.getByTestId('up-drop-input'), { target: { files: [makeFile(FILE_NAME)] } });
  await act(async () => {});
  await screen.findByTestId('up-files');
  await click(await screen.findByTestId('reg-open'));
  await screen.findByTestId('reg-steps');
}

describe('WU-A9 — 종료 확인은 사람이 입력한 값이 있을 때만 묻는다', () => {
  it('파일만 올리고 아무것도 안 적으면 되묻지 않고 닫힌다', async () => {
    await openRegisterWithFile();
    await click(screen.getByTestId('upload-close'));
    expect(screen.queryByTestId('upload-close-confirm')).toBeNull();
    expect(screen.queryByTestId('upload-modal')).toBeNull();
  });

  it('파일명에서 자동으로 만든 이름 초안은 입력으로 세지 않는다', async () => {
    await openRegisterWithFile();
    // 자동 초안이 실제로 칸에 들어 있다 — 그런데도 묻지 않는 것이 이 시험의 값이다.
    expect(screen.getByTestId('reg-name')).toHaveValue('nakdong_precip_2025_Lv2');
    await click(screen.getByTestId('upload-close'));
    expect(screen.queryByTestId('upload-modal')).toBeNull();
  });

  it('설명을 한 글자 적으면 확인 모달이 뜬다 — 문면은 종전 그대로다', async () => {
    await openRegisterWithFile();
    await change(screen.getByTestId('reg-summary'), '가');
    await click(screen.getByTestId('upload-close'));
    const confirm = await screen.findByTestId('upload-close-confirm');
    expect(confirm).toHaveTextContent(CONFIRM_BODY);
    expect(within(confirm).getByRole('button', { name: '계속 작성' })).toBeInTheDocument();
    expect(within(confirm).getByRole('button', { name: '닫고 나가기' })).toBeInTheDocument();
    expect(screen.getByTestId('upload-modal')).toBeInTheDocument();
  });

  it('이름 초안을 사람이 한 글자라도 고치면 묻는다', async () => {
    await openRegisterWithFile();
    await change(screen.getByTestId('reg-name'), '낙동강 강수 2025');
    await click(screen.getByTestId('upload-close'));
    expect(await screen.findByTestId('upload-close-confirm')).toBeInTheDocument();
  });

  it('좌표계·변수·기간·원천 표기도 사람 입력이다 — 한 칸만 적어도 묻는다', async () => {
    await openRegisterWithFile();
    await change(screen.getByTestId('reg-crs'), 'E');
    await click(screen.getByTestId('upload-close'));
    expect(await screen.findByTestId('upload-close-confirm')).toBeInTheDocument();
  });

  it('계보 부모를 1건 확정하면 묻는다', async () => {
    let ctx: LineageStepContext | null = null;
    await openRegisterWithFile({
      lineageStep: (c) => {
        ctx = c;
        return <div data-testid="fake-lineage">③ 자리</div>;
      },
    });
    await click(screen.getByRole('button', { name: /^③/ }));
    await screen.findByTestId('fake-lineage');
    await act(async () => {
      ctx!.onLineageParentsChange([{ parentDatasetId: NDVI_ID, parentRole: '주입력' } as never]);
    });
    await click(screen.getByTestId('upload-close'));
    expect(await screen.findByTestId('upload-close-confirm')).toBeInTheDocument();
  });

  it('계보 부모가 0건으로 돌아오면 다시 묻지 않는다 — 확정 건수가 판정 대상이다', async () => {
    let ctx: LineageStepContext | null = null;
    await openRegisterWithFile({
      lineageStep: (c) => {
        ctx = c;
        return <div data-testid="fake-lineage">③ 자리</div>;
      },
    });
    await click(screen.getByRole('button', { name: /^③/ }));
    await screen.findByTestId('fake-lineage');
    await act(async () => {
      ctx!.onLineageParentsChange([{ parentDatasetId: NDVI_ID, parentRole: '주입력' } as never]);
    });
    await act(async () => {
      ctx!.onLineageParentsChange([]);
    });
    await click(screen.getByTestId('upload-close'));
    expect(screen.queryByTestId('upload-close-confirm')).toBeNull();
    expect(screen.queryByTestId('upload-modal')).toBeNull();
  });

  it('② 에서 프로젝트를 담으면 묻는다', async () => {
    await openRegisterWithFile();
    await click(screen.getByRole('button', { name: /^②/ }));
    await change(await screen.findByTestId('reg-proj-select'), PROJECT_ID);
    await click(screen.getByRole('button', { name: '+ 추가' }));
    await click(screen.getByTestId('upload-close'));
    expect(await screen.findByTestId('upload-close-confirm')).toBeInTheDocument();
  });
});
