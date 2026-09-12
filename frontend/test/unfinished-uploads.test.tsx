/**
 * 오라클 — **메인 화면의 「올리다 만 것」 카드**.
 *
 * 업로드는 두 걸음이고(바이트 → 설정·등록), 미완결도 두 가지다. 지금까지 알림은
 * ⑴ **업로드 모달을 열어야만** 보였고 ⑵ **앞걸음(전송)만** 잡았다. 모달을 닫으면
 * 「올리다 만 것이 있다」는 사실 자체가 사라졌다.
 *
 * ⚠ 이 카드는 P7(할 일 함)의 자리가 아니다 — `TodoInboxSlot` 을 침범하지 않는다.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { SessionProvider } from '../src/permission/session';
import { UnfinishedUploads } from '../src/components/upload/UnfinishedUploads';
import { UploadEntry } from '../src/components/upload/UploadEntry';
import { OpenUploadContext } from '../src/components/upload/openUpload';
import { listPending, rememberPending } from '../src/components/upload/pendingStore';
import type { CurrentAccount } from '../src/api/client';
import type { LineageSource, LineageSuggestionResponse } from '../src/components/lineage/types';
import type {
  IncompleteTransferItem,
  PreviewSource,
  ProjectSource,
  UploadSource,
  UploadSources,
} from '../src/components/upload/types';

const LAB = '01JYZ9K7WQ3N8V4M2X6C5B0LB1';
const T1 = '01JYZ9K7WQ3N8V4M2X6C5B0TR1';
const U2 = '01JYZ9K7WQ3N8V4M2X6C5B0UP2';
const U3 = '01JYZ9K7WQ3N8V4M2X6C5B0UP3';

function account(): CurrentAccount {
  return { accountId: 'A1', name: '호랑이', email: 't@e.ac.kr', role: '연구원',
           labId: LAB, labName: '수자원순환연구실',
           permissions: { '업로드·편집': true } } as CurrentAccount;
}

const ITEM: IncompleteTransferItem = {
  uploadId: T1, sourceLabel: '기상 폴더', uploadedFiles: 3, plannedFiles: 8,
  uploadedBytes: 300, plannedBytes: 800, createdAt: 'x', expiresAt: 'y',
};

function source(over: Partial<UploadSource> = {}): UploadSource {
  return {
    create: vi.fn(), register: vi.fn(), attachGrid: vi.fn(),
    incomplete: async () => [],
    status: async () => { throw new Error('없음'); },
    ...over,
  } as unknown as UploadSource;
}

function draw(src: UploadSource, onOpen = vi.fn()) {
  render(
    <MemoryRouter>
      <SessionProvider account={account()}>
        <OpenUploadContext.Provider value={onOpen}>
          <UnfinishedUploads upload={src} />
        </OpenUploadContext.Provider>
      </SessionProvider>
    </MemoryRouter>,
  );
  return onOpen;
}

describe('메인 — 올리다 만 것', () => {
  it('미완결이 없으면 **카드를 아예 안 그린다** — 빈 카드를 두지 않는다', async () => {
    draw(source());
    await waitFor(() => expect(screen.queryByTestId('unfinished-uploads')).toBeNull());
  });

  it('파일이 덜 올라간 것과 등록만 남은 것을 **구분해서** 보여준다', async () => {
    rememberPending(LAB, U2);
    draw(source({
      incomplete: async () => [ITEM],
      status: async () => ({ uploadId: U2, files: [{ fileId: 'F', fileName: '비.nc', kind: '본체', byteSize: 1 }],
                             ready: true, renderable: null, metadataComplete: null,
                             expiresAt: 'z', failure: null }),
    }));
    const card = await screen.findByTestId('unfinished-uploads');
    expect(card).toHaveTextContent('기상 폴더');
    expect(card).toHaveTextContent('3/8');          // 파일 올리는 중
    expect(card).toHaveTextContent('등록만 남았어요');  // 설정 미완
  });

  it('**이미 등록한 것**은 서버가 말해 주는 대로 지운다 — 「등록만 남았어요」라고 거짓말하지 않는다', async () => {
    // 등록 직후 탭이 죽으면 브라우저 기억만 남는다. 그때 화면이 **끝난 일을 안 끝났다고**
    // 말했다. 서버가 `registered` 를 내리게 해(2026-09-02 동결 해제) 그 거짓을 닫았다.
    // ⚠ 카드가 **뜨는 상태**로 재 둔다(전송 1건). 빈 화면에서 「없음」을 재면 비동기가
    //    끝나기도 전에 통과한다 — 그건 오라클이 아니다.
    rememberPending(LAB, U3);
    draw(source({
      incomplete: async () => [ITEM],
      status: async () => ({ uploadId: U3, files: [{ fileId: 'F', fileName: '끝난.nc', kind: '본체', byteSize: 1 }],
                             ready: true, renderable: null, metadataComplete: null,
                             expiresAt: 'z', registered: true, failure: null }),
    }));
    const card = await screen.findByTestId('unfinished-uploads');
    expect(card).toHaveTextContent('기상 폴더');            // 전송은 그대로 있고
    await waitFor(() => expect(listPending(LAB)).not.toContain(U3));  // 등록된 것은 잊는다
    expect(card).not.toHaveTextContent('등록만 남았어요');  // 끝난 일을 안 끝났다고 하지 않는다
  });

  it('[이어서 올리기]가 모달을 **그 전송으로** 연다', async () => {
    const onOpen = draw(source({ incomplete: async () => [ITEM] }));
    (await screen.findByTestId(`unfinished-resume-${T1}`)).click();
    expect(onOpen).toHaveBeenCalledWith({ resumeUploadId: T1 });
  });
});

// ───────────────────────────────────────────────────────────────────────────
// `#33` ㉠ — 배너의 재개 요청이 **모달까지** 간다.
//
// 결함 = 메인 배너가 `openUpload({ resumeUploadId })` 로 값을 올려도 `UploadEntry` 가
// 그 값을 `UploadModal` 로 넘기지 않아 재개 무장(`resumeRef`·`resumeFromRef='banner'`)이
// 서지 않았다. 컨텍스트 스텁만 보는 시험은 이 결함을 통과시킨다 — 그래서 여기서는
// **진입 컴포넌트 실물**을 렌더하고 모달 안 배너의 무장 표시를 잰다.

/** 모달이 요구하는 나머지 세 출처 — 이 시험이 재는 것은 재개 무장뿐이라 최소만 답한다. */
function modalSources(upload: UploadSource): UploadSources {
  const preview: PreviewSource = {
    async palettes() { return [{ palette: 'viridis', label: '비리디스' }]; },
    async createRender() { return { renderId: 'R1', status: '그리는 중', stage: '파일 읽는 중' } as never; },
    async getRender() { return { renderId: 'R1', status: '그리는 중', stage: '파일 읽는 중' } as never; },
  };
  const projects: ProjectSource = {
    async list() { return []; },
    async create(body) { return { projectId: 'P9', name: body.name, type: body.type }; },
  };
  const lineage: LineageSource = {
    async suggestions() {
      return {
        degraded: false,
        scope: { labId: LAB, labName: '수자원순환연구실', searchedCount: 0 },
        rawDataLikely: false,
        suggestions: [],
      } as LineageSuggestionResponse;
    },
    async candidates() { return []; },
  };
  return { upload, preview, projects, lineage };
}

function drawEntry(upload: UploadSource, openRequest?: { seq: number; resumeUploadId?: string }) {
  return render(
    <MemoryRouter initialEntries={['/datasets']}>
      <SessionProvider account={account()}>
        <UploadEntry sources={modalSources(upload)} openRequest={openRequest} />
      </SessionProvider>
    </MemoryRouter>,
  );
}

describe('#33 ㉠ — 배너 재개 요청이 모달의 재개 무장까지 간다', () => {
  it('배너에서 「이어서 올리기」로 연 모달이 **그 전송으로 무장한 채** 뜬다', async () => {
    drawEntry(source({ incomplete: async () => [ITEM] }), { seq: 1, resumeUploadId: T1 });
    await screen.findByTestId('upload-modal');
    // 무장 표시는 신설하지 않는다 — 모달이 이미 가진 `is-armed` 와 재개 안내가 오라클이다.
    await waitFor(() => expect(screen.getByTestId(`up-resume-${T1}`)).toHaveClass('is-armed'));
    expect(screen.getByTestId('up-resume-hint')).toBeInTheDocument();
  });
});
