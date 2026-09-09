// WU-A9R · PRD-34 · PRD-14 · PRD-44 · PRD-39 ⑭ —
// 닫기 문면 3종 ＋ 배경 클릭 닫기 ＋ 손댐 판정 2필드 ＋ Esc 우선순위.
//
// 오라클 = `dev-package/prd/rounds/R-A2.md` §2-④ 완료 조건.
// ⛔ 문면 축자는 rev2 원문(`10_적용전/업로드_계보_260905_rev2_이태헌.html` `closeUpload()`)에서
//    떴다. 시험이 문자열을 새로 짓지 않는다 — `toastCopy.ts` 상수와 대조한다.
import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';

import { SessionProvider } from '../src/permission/session';
import { UploadEntry } from '../src/components/upload/UploadEntry';
import * as copy from '../src/components/common/toastCopy';
import type {
  LineageStepContext,
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
const PARENT_ID = '01JYZ9K7WQ3N8V4M2X6C5B0PA1';
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

function makeFile(name: string, size = 148_000_000, type = 'application/octet-stream') {
  const f = new File(['x'], name, { type });
  Object.defineProperty(f, 'size', { value: size });
  return f;
}

async function click(el: Element | null) {
  fireEvent.click(el as HTMLElement);
  await act(async () => {});
}

/** 배경 클릭 = 배경에서 눌러 배경에서 뗀 것. 눌림 자리까지 재야 드래그와 갈린다 (F3). */
async function backdropClick() {
  const back = screen.getByTestId('upload-backdrop');
  fireEvent.mouseDown(back);
  fireEvent.click(back);
  await act(async () => {});
}

async function change(el: Element | null, value: string) {
  fireEvent.change(el as HTMLElement, { target: { value } });
  await act(async () => {});
}

async function pressEscape() {
  fireEvent.keyDown(document, { key: 'Escape' });
  await act(async () => {});
}

/** 파일 1건을 올리고 등록 단계까지 연 상태. 사람이 적은 값은 **아직 0** 이다. */
async function openRegisterWithFile(
  opts: { lineageStep?: (ctx: LineageStepContext) => React.ReactNode } = {},
) {
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
  // ⭑ ⟨WU-B3⟩ 등록 카드가 ① 분류에서 열린다 — 이 시험들이 재는 칸은 ② 메타데이터 입력에
  // 있으므로 표시기로 한 단계 옮겨 둔다. **재는 것은 그대로다**(단계 이름만 바뀌었다).
  await click(screen.getByRole('button', { name: /^② / }));
}

describe('PRD-34 — 닫기 문면 3종은 한 곳에서 온다', () => {
  it('상황별 문면이 rev2 축자 그대로다', () => {
    expect(copy.UPLOAD_CLOSE_TITLE).toBe('업로드를 닫을까요?');
    expect(copy.UPLOAD_CLOSE_KEEP).toBe('계속하기');
    expect(copy.UPLOAD_CLOSE_LEAVE).toBe('닫고 나가기');
    expect(copy.UPLOAD_CLOSE_FILE_ONLY).toBe(
      '올린 파일이 취소돼요. 원본 파일은 그대로라 다시 올리면 돼요.',
    );
    expect(copy.UPLOAD_CLOSE_INPUT_ONLY).toBe(
      '적은 내용이 사라지고, 데이터셋은 만들어지지 않아요. 원본 파일은 그대로예요.',
    );
    expect(copy.uploadCloseWithLineage(3)).toBe(
      '적은 내용과 연결한 계보 3건이 사라지고, 데이터셋은 만들어지지 않아요. 원본 파일은 그대로예요.',
    );
  });

  it('갈래가 셋이고 서로 다르다 — 판정 기준은 사람 입력 유무와 확정 계보 건수다', () => {
    const a = copy.uploadCloseMessage({ hasHumanInput: false, lineageCount: 0 });
    const b = copy.uploadCloseMessage({ hasHumanInput: true, lineageCount: 0 });
    const c = copy.uploadCloseMessage({ hasHumanInput: true, lineageCount: 3 });
    expect(a).toBe(copy.UPLOAD_CLOSE_FILE_ONLY);
    expect(b).toBe(copy.UPLOAD_CLOSE_INPUT_ONLY);
    expect(c).toBe(copy.uploadCloseWithLineage(3));
    expect(new Set([a, b, c]).size).toBe(3);
  });

  it('계보 건수는 보간값이다 — 고정 숫자가 아니다', () => {
    expect(copy.uploadCloseWithLineage(1)).toContain('계보 1건');
    expect(copy.uploadCloseWithLineage(12)).toContain('계보 12건');
    expect(copy.uploadCloseWithLineage(1)).not.toBe(copy.uploadCloseWithLineage(12));
  });
});

describe('PRD-34 — 화면이 그 문면을 그대로 그린다', () => {
  it('입력 있음 · 계보 0 → 「적은 내용이 사라지고 …」 · 버튼은 계속하기 · 닫고 나가기', async () => {
    await openRegisterWithFile();
    await change(screen.getByTestId('reg-summary'), '가');
    await click(screen.getByTestId('upload-close'));
    const confirm = await screen.findByTestId('upload-close-confirm');
    expect(confirm).toHaveTextContent(copy.UPLOAD_CLOSE_TITLE);
    expect(confirm).toHaveTextContent(copy.UPLOAD_CLOSE_INPUT_ONLY);
    expect(within(confirm).getByRole('button', { name: copy.UPLOAD_CLOSE_KEEP })).toBeInTheDocument();
    expect(within(confirm).getByRole('button', { name: copy.UPLOAD_CLOSE_LEAVE })).toBeInTheDocument();
    expect(within(confirm).queryByRole('button', { name: '계속 작성' })).toBeNull();
  });

  it('입력 있음 · 계보 3건 → 문면에 `3` 이 보간된다', async () => {
    let ctx: LineageStepContext | null = null;
    await openRegisterWithFile({
      lineageStep: (c) => {
        ctx = c;
        return <div data-testid="fake-lineage">③ 자리</div>;
      },
    });
    await change(screen.getByTestId('reg-summary'), '가');
    await click(screen.getByRole('button', { name: /^③/ }));
    await screen.findByTestId('fake-lineage');
    await act(async () => {
      ctx!.onLineageParentsChange([
        { parentDatasetId: PARENT_ID, parentRole: '주입력' },
        { parentDatasetId: PARENT_ID, parentRole: '주입력' },
        { parentDatasetId: PARENT_ID, parentRole: '주입력' },
      ] as never);
    });
    await click(screen.getByTestId('upload-close'));
    const confirm = await screen.findByTestId('upload-close-confirm');
    expect(confirm).toHaveTextContent(copy.uploadCloseWithLineage(3));
  });

  it('「계속하기」는 확인만 닫는다 — 업로드는 그대로 남는다', async () => {
    await openRegisterWithFile();
    await change(screen.getByTestId('reg-summary'), '가');
    await click(screen.getByTestId('upload-close'));
    const confirm = await screen.findByTestId('upload-close-confirm');
    await click(within(confirm).getByRole('button', { name: copy.UPLOAD_CLOSE_KEEP }));
    expect(screen.queryByTestId('upload-close-confirm')).toBeNull();
    expect(screen.getByTestId('upload-modal')).toBeInTheDocument();
  });
});

describe('PRD-14 증분 — 손댐 판정 2필드', () => {
  it('③ 에서 프로젝트를 담으면 묻는다 — 담은 프로젝트 건수', async () => {
    await openRegisterWithFile();
    // ⭑ ⟨WU-B3⟩ 연관 프로젝트·논문 표는 ③ 연결 안으로 들어왔다(PRD-12).
    await click(screen.getByRole('button', { name: /^③/ }));
    await change(await screen.findByTestId('reg-proj-select'), PROJECT_ID);
    await click(screen.getByRole('button', { name: '+ 추가' }));
    await click(screen.getByTestId('upload-close'));
    expect(await screen.findByTestId('upload-close-confirm')).toBeInTheDocument();
  });

  it('대표 그림을 바꾸면 묻는다 — 대표 그림 교체 여부', async () => {
    await openRegisterWithFile();
    fireEvent.change(await screen.findByTestId('up-thumb-input'), {
      target: { files: [makeFile('thumb.png', 1024, 'image/png')] },
    });
    await act(async () => {});
    await click(screen.getByTestId('upload-close'));
    expect(await screen.findByTestId('upload-close-confirm')).toBeInTheDocument();
  });

  it('자동으로 채워진 값은 세지 않는다 — 파일만 올린 상태는 되묻지 않는다', async () => {
    await openRegisterWithFile();
    await click(screen.getByTestId('upload-close'));
    expect(screen.queryByTestId('upload-close-confirm')).toBeNull();
    expect(screen.queryByTestId('upload-modal')).toBeNull();
  });

  // F1 — 대표 그림 플래그는 파일과 함께 내린다. 파일을 빼면 그 그림도 함께 사라지므로
  // 플래그만 남으면 다시 올린 사람이 아무것도 안 적고도 되묻힌다.
  it('파일을 빼면 대표 그림 교체 표시도 내린다 — 재첨부 뒤 닫기는 되묻지 않는다', async () => {
    await openRegisterWithFile();
    fireEvent.change(await screen.findByTestId('up-thumb-input'), {
      target: { files: [makeFile('thumb.png', 1024, 'image/png')] },
    });
    await act(async () => {});
    await click(screen.getByRole('button', { name: '올린 파일 모두 빼기' }));
    fireEvent.change(screen.getByTestId('up-drop-input'), { target: { files: [makeFile(FILE_NAME)] } });
    await act(async () => {});
    await screen.findByTestId('up-files');
    await click(screen.getByTestId('upload-close'));
    expect(screen.queryByTestId('upload-close-confirm')).toBeNull();
    expect(screen.queryByTestId('upload-modal')).toBeNull();
  });

  // F2 — PRD-14 「사람 입력 필드 전부」. 관측 간격·최소 단위도 사람이 적은 값이다.
  it('관측 간격만 적어도 묻는다 — 사람 입력 필드 전부를 센다', async () => {
    await openRegisterWithFile();
    await change(screen.getByTestId('reg-interval-value'), '10');
    await click(screen.getByTestId('upload-close'));
    expect(await screen.findByTestId('upload-close-confirm')).toBeInTheDocument();
  });

  it('관측 간격 단위만 골라도 묻는다', async () => {
    await openRegisterWithFile();
    await change(screen.getByTestId('reg-interval-unit'), '분');
    await click(screen.getByTestId('upload-close'));
    expect(await screen.findByTestId('upload-close-confirm')).toBeInTheDocument();
  });
});

describe('PRD-44 — 배경 클릭', () => {
  it('입력이 있으면 배경 클릭이 닫기 확인을 그대로 탄다', async () => {
    await openRegisterWithFile();
    await change(screen.getByTestId('reg-summary'), '가');
    await backdropClick();
    const confirm = await screen.findByTestId('upload-close-confirm');
    expect(confirm).toHaveTextContent(copy.UPLOAD_CLOSE_INPUT_ONLY);
    expect(screen.getByTestId('upload-modal')).toBeInTheDocument();
  });

  it('아무것도 안 적었으면 배경 클릭이 되묻지 않고 닫는다', async () => {
    await openRegisterWithFile();
    await backdropClick();
    expect(screen.queryByTestId('upload-close-confirm')).toBeNull();
    expect(screen.queryByTestId('upload-modal')).toBeNull();
  });

  it('모달 내부 클릭은 닫지 않는다', async () => {
    await openRegisterWithFile();
    await change(screen.getByTestId('reg-summary'), '가');
    await click(screen.getByTestId('upload-modal'));
    expect(screen.queryByTestId('upload-close-confirm')).toBeNull();
    expect(screen.getByTestId('upload-modal')).toBeInTheDocument();
  });

  // F3 — 모달 안에서 누르고 배경에서 뗀 드래그는 click.target 이 배경이 된다(텍스트 선택).
  // 눌린 자리가 배경이 아니면 닫지 않는다.
  it('모달 안에서 눌러 배경에서 뗀 드래그는 닫지 않는다', async () => {
    await openRegisterWithFile();
    await change(screen.getByTestId('reg-summary'), '가');
    fireEvent.mouseDown(screen.getByTestId('upload-modal'));
    fireEvent.click(screen.getByTestId('upload-backdrop'));
    await act(async () => {});
    expect(screen.queryByTestId('upload-close-confirm')).toBeNull();
    expect(screen.getByTestId('upload-modal')).toBeInTheDocument();
  });
});

describe('PRD-39 ⑭ — Esc 우선순위', () => {
  it('닫기 확인이 떠 있으면 Esc 는 그것만 닫는다 — 업로드는 남는다', async () => {
    await openRegisterWithFile();
    await change(screen.getByTestId('reg-summary'), '가');
    await click(screen.getByTestId('upload-close'));
    await screen.findByTestId('upload-close-confirm');
    await pressEscape();
    expect(screen.queryByTestId('upload-close-confirm')).toBeNull();
    expect(screen.getByTestId('upload-modal')).toBeInTheDocument();
  });

  it('확인이 없으면 Esc 가 업로드 닫기를 청한다 — 입력이 있으면 확인이 뜬다', async () => {
    await openRegisterWithFile();
    await change(screen.getByTestId('reg-summary'), '가');
    await pressEscape();
    expect(await screen.findByTestId('upload-close-confirm')).toBeInTheDocument();
  });

  it('위에 있는 층(확장보기·찾기·계보 수정)이 열려 있으면 업로드는 Esc 를 먹지 않는다', async () => {
    await openRegisterWithFile();
    await change(screen.getByTestId('reg-summary'), '가');
    // 위 세 층은 스스로를 `data-esc-layer` 로 표시한다 (`ESC_LAYER_ATTR`).
    const layer = document.createElement('div');
    layer.setAttribute('data-esc-layer', '찾기');
    document.body.appendChild(layer);
    await pressEscape();
    expect(screen.queryByTestId('upload-close-confirm')).toBeNull();
    expect(screen.getByTestId('upload-modal')).toBeInTheDocument();
    layer.remove();
  });
});
