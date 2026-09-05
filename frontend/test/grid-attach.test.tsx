/**
 * S-05 「기준 격자 추가」 — 격자 후주입의 화면 절반.
 *
 * 오라클 = Ted 2026-08-25 판정(사용자 관점 우선). 사람에게 「격자를 나중에 붙이는 행위」는
 * **파일 업로드**이므로 새 화면 개념을 만들지 않는다 — 진입점 하나 + **S-04 업로드 모달 재사용**.
 * 그래서 이 시험이 확인하는 것은 「새 화면이 없다」와 「끝의 한 걸음만 다르다」다.
 *
 * fireEvent 를 쓴다 — user-event 를 새로 들이지 않는다(집 관례).
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { SessionProvider } from '../src/permission/session';
import { GridAttachEntry } from '../src/components/upload/GridAttachEntry';
import { GridAxisTaken, NoResolvedGrid, UploadGone } from '../src/components/upload/types';
import type {
  DatasetFile,
  PreviewSource,
  ProjectSource,
  UploadSource,
  UploadSources,
} from '../src/components/upload/types';
import type { LineageSource } from '../src/components/lineage/types';
import type { CurrentAccount, Schemas } from '../src/api/client';

const UPLOAD_ID = '01JYZ9K7WQ3N8V4M2X6C5B0UP1';
const FILE_ID = '01JYZ9K7WQ3N8V4M2X6C5B0FI1';
const FILE_ID2 = '01JYZ9K7WQ3N8V4M2X6C5B0FI2';
const DATASET_ID = '01JYZ9K7WQ3N8V4M2X6C5B0DS1';

type Perm = Partial<Record<Schemas['PermissionSwitch'], boolean>>;

function account(perm: Perm): CurrentAccount {
  return {
    accountId: '01JYZ9K7WQ3N8V4M2X6C5B0AC1',
    name: '호랑이',
    email: 'tiger@example.ac.kr',
    role: '연구원',
    labId: '01JYZ9K7WQ3N8V4M2X6C5B0LB1',
    labName: '수자원순환연구실',
    permissions: perm as CurrentAccount['permissions'],
  } as CurrentAccount;
}

function fakes(over: { ready?: boolean; attachThrows?: unknown } = {}) {
  const calls = {
    created: [] as { name: string; kind: string }[],
    attached: [] as { datasetId: string; uploadId: string }[],
  };
  const status: Schemas['UploadStatus'] = {
    uploadId: UPLOAD_ID,
    files: [
      {
        fileId: FILE_ID,
        fileName: 'lat.npy',
        kind: '기준 격자 파일',
        byteSize: 1024,
        gridAxis: { carriesLat: true, carriesLon: false },
      },
    ],
    gridRejections: [],
    ready: over.ready ?? true,
    renderable: false,
    metadataComplete: false,
    expiresAt: '2026-08-26T00:00:00Z',
    failure: null,
  };
  const upload: UploadSource = {
    async create(files) {
      for (const f of files) calls.created.push({ name: f.file.name, kind: f.kind });
      return {
        uploadId: UPLOAD_ID,
        files: files.map((f, i) => ({
          fileId: i === 0 ? FILE_ID : FILE_ID2,
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
      throw new Error('후주입 모드는 등록 전환을 부르지 않는다.');
    },
    async attachGrid(datasetId, uploadId) {
      calls.attached.push({ datasetId, uploadId });
      if (over.attachThrows) throw over.attachThrows;
      const items: DatasetFile[] = [
        {
          fileId: FILE_ID,
          fileName: 'lat.npy',
          kind: '기준 격자 파일',
          byteSize: 4,
          createdAt: '2026-08-29T00:00:00Z',
          gridAxis: { carriesLat: true, carriesLon: false },
        },
      ];
      return items;
    },
  };
  const preview: PreviewSource = {
    async palettes() {
      return [{ palette: 'viridis', label: '비리디스' }];
    },
    async createRender() {
      throw new Error('부르지 않는다');
    },
    async getRender() {
      throw new Error('부르지 않는다');
    },
  };
  const projects: ProjectSource = {
    async list() {
      return [];
    },
    async create() {
      throw new Error('부르지 않는다');
    },
  };
  const lineage = {
    async suggestions() {
      throw new Error('부르지 않는다');
    },
    async candidates() {
      return [];
    },
  } as unknown as LineageSource;
  return { calls, sources: { upload, preview, projects, lineage } as UploadSources };
}

async function click(el: Element | null) {
  fireEvent.click(el as HTMLElement);
  await act(async () => {});
}

function mount(sources: UploadSources, perm?: Perm, onAttached?: () => void) {
  return render(
    <MemoryRouter initialEntries={[`/datasets/${DATASET_ID}`]}>
      <SessionProvider account={account(perm ?? { '업로드·편집': true })}>
        <GridAttachEntry
          datasetId={DATASET_ID}
          datasetName="강우 1 km"
          onAttached={onAttached}
          sources={sources}
        />
      </SessionProvider>
    </MemoryRouter>,
  );
}

async function openAttachModal(sources: UploadSources) {
  mount(sources);
  await click(screen.getByTestId('grid-attach-open'));
  await screen.findByTestId('upload-modal');
}

async function dropGrid(name = 'lat.npy') {
  const input = screen.getByTestId('up-drop-input');
  fireEvent.change(input, { target: { files: [new File(['x'], name)] } });
  await act(async () => {});
  await screen.findByTestId('up-files');
}

// ───────────────────────────────────────────────────────────────────────────
describe('진입점 — 데이터셋 상세에 버튼 하나', () => {
  it('`업로드·편집` 이 꺼지면 버튼이 **숨는다** — 비활성이 아니다 (`P-12`)', () => {
    const { sources } = fakes();
    mount(sources, { '업로드·편집': false });
    expect(screen.queryByTestId('grid-attach-open')).toBeNull();
  });

  it('버튼이 여는 것은 **업로드 모달 그대로**다 — 새 화면 개념이 없다', async () => {
    const { sources } = fakes();
    await openAttachModal(sources);
    const modal = screen.getByTestId('upload-modal');
    expect(modal).toHaveAttribute('role', 'dialog');
    expect(modal).toHaveAttribute('data-mode', 'grid-attach');
    // 라우트를 만들지 않는다 — 모달이다.
    expect(window.location.pathname).not.toContain('grid');
  });

  it('후주입 모드에서는 **등록 게이트가 없다** — 데이터셋을 만드는 화면이 아니다', async () => {
    const { sources } = fakes();
    await openAttachModal(sources);
    await dropGrid();
    expect(screen.queryByTestId('reg-gate')).toBeNull();
    expect(screen.queryByTestId('reg-open')).toBeNull();
    expect(screen.getByTestId('grid-attach-gate')).toBeTruthy();
  });
});

describe('접수 — 파일 종류 기본값이 격자다', () => {
  it('놓은 파일이 `기준 격자 파일` 로 접수된다 — 사람이 격자를 붙이러 왔다', async () => {
    const { calls, sources } = fakes();
    await openAttachModal(sources);
    await dropGrid();
    expect(calls.created).toEqual([{ name: 'lat.npy', kind: '기준 격자 파일' }]);
  });

  it('판별 사다리·11 상태를 그리는 미리보기 패널이 **같은 코드**로 선다', async () => {
    const { sources } = fakes();
    await openAttachModal(sources);
    await dropGrid();
    expect(screen.getByTestId('up-preview')).toBeTruthy();
  });
});

describe('확정 — 끝의 한 걸음만 다르다', () => {
  it('판별이 끝나기 전에는 반영 버튼을 누를 수 없다', async () => {
    const { sources } = fakes({ ready: false });
    await openAttachModal(sources);
    await dropGrid();
    expect(screen.getByTestId('grid-attach-confirm')).toBeDisabled();
  });

  it('반영은 **`datasetId` 와 `uploadId` 를 한 요청으로** 보낸다 — 짝은 화면이 들고 있었다', async () => {
    const { calls, sources } = fakes();
    await openAttachModal(sources);
    await dropGrid();
    await click(screen.getByTestId('grid-attach-confirm'));
    expect(calls.attached).toEqual([{ datasetId: DATASET_ID, uploadId: UPLOAD_ID }]);
  });

  it('반영이 끝나면 모달이 닫히고 상세를 **서버에게 다시 묻는다**', async () => {
    const { sources } = fakes();
    let reloaded = 0;
    mount(sources, undefined, () => {
      reloaded += 1;
    });
    await click(screen.getByTestId('grid-attach-open'));
    await screen.findByTestId('upload-modal');
    await dropGrid();
    await click(screen.getByTestId('grid-attach-confirm'));
    expect(reloaded).toBe(1);
    expect(screen.queryByTestId('upload-modal')).toBeNull();
  });
});

describe('거절 — 서버가 판정하고 화면은 그 문장을 그대로 보여 준다', () => {
  it('그 축의 격자가 이미 있으면 (`〈58〉` 상한) 그 이유를 말한다', async () => {
    const { sources } = fakes({ attachThrows: new GridAxisTaken() });
    await openAttachModal(sources);
    await dropGrid();
    await click(screen.getByTestId('grid-attach-confirm'));
    expect(screen.getByTestId('grid-attach-error')).toHaveTextContent('이미 있어요');
  });

  it('축을 못 정한 격자는 반영할 것이 없다고 말한다 (`〈66〉`)', async () => {
    const { sources } = fakes({ attachThrows: new NoResolvedGrid() });
    await openAttachModal(sources);
    await dropGrid();
    await click(screen.getByTestId('grid-attach-confirm'));
    expect(screen.getByTestId('grid-attach-error')).toHaveTextContent('위도·경도를 정하지 못했어요');
  });

  it('확정 전에 업로드가 회수됐으면 (`〈67〉`) 다시 올리라고 말한다', async () => {
    const { sources } = fakes({ attachThrows: new UploadGone() });
    await openAttachModal(sources);
    await dropGrid();
    await click(screen.getByTestId('grid-attach-confirm'));
    expect(screen.getByTestId('grid-attach-error')).toHaveTextContent('더 이상 없어요');
  });

  it('거절돼도 **모달이 닫히지 않는다** — 사람이 고쳐서 다시 누른다', async () => {
    const { sources } = fakes({ attachThrows: new GridAxisTaken() });
    await openAttachModal(sources);
    await dropGrid();
    await click(screen.getByTestId('grid-attach-confirm'));
    expect(screen.getByTestId('upload-modal')).toBeTruthy();
  });
});
