import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { DatasetDetailPage } from '../src/routes/DatasetDetailPage';
import { FIXTURE_DETAILS } from '../src/components/detail/fixture';
import { fixtureLineageSource } from '../src/components/lineage/graphFixture';
import { SessionProvider } from '../src/permission/session';
import type { CurrentAccount } from '../src/api/client';
import type { DatasetDetail } from '../src/components/detail/types';
import { apiRepresentativeImageSource } from '../src/components/detail/representativeImageSource';
import { clearToken, setToken } from '../src/auth/store';

const ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA1';
const CUSTOM: DatasetDetail = {
  ...(FIXTURE_DETAILS[ID] as DatasetDetail),
  representativeImage: {
    custom: true,
    fileName: 'cover.png',
    contentType: 'image/png',
    sizeBytes: 5,
  },
};

const ACCOUNT = {
  accountId: '01JYZ9K7WQ3N8V4M2X6C5B0AC1',
  name: '호랑이',
  email: 'tiger@example.org',
  role: '연구원',
  labId: '01JYZ9K7WQ3N8V4M2X6C5B0LB1',
  labName: '수문연구실',
  permissions: { '업로드·편집': true, '프로젝트 생성': false, '승인 위임': false, '연구실 설정': false },
} as CurrentAccount;

afterEach(() => {
  clearToken();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

function previewSource() {
  return {
    palettes: async () => [],
    files: async () => [],
    create: async () => { throw new Error('unused'); },
    get: async () => { throw new Error('unused'); },
    probeTile: async () => 404,
    screenshot: async () => { throw new Error('unused'); },
    valueAt: async () => { throw new Error('unused'); },
  } as never;
}

function mount(
  representativeImageSource: unknown,
  detail: DatasetDetail = CUSTOM,
  account: CurrentAccount = ACCOUNT,
) {
  return render(
    <MemoryRouter initialEntries={[`/datasets/${ID}`]}>
      <SessionProvider account={account}>
        <Routes>
          <Route path="/datasets/:datasetId" element={
            <DatasetDetailPage
              source={{ get: async () => detail }}
              lineageSource={fixtureLineageSource()}
              previewSource={previewSource()}
              representativeImageSource={representativeImageSource as never}
            />
          } />
        </Routes>
      </SessionProvider>
    </MemoryRouter>,
  );
}

describe('상세 대표 그림', () => {
  it('Bearer 출처가 준 Blob을 object URL로 보이고 떠날 때 해제한다', async () => {
    const blob = new Blob(['cover'], { type: 'image/png' });
    const source = { get: vi.fn().mockResolvedValue(blob), put: vi.fn(), remove: vi.fn() };
    const create = vi.fn(() => 'blob:detail/cover');
    const revoke = vi.fn();
    vi.stubGlobal('URL', { ...URL, createObjectURL: create, revokeObjectURL: revoke });
    const view = mount(source);

    expect(await screen.findByRole('img', { name: '사용자 대표 그림' })).toHaveAttribute(
      'src', 'blob:detail/cover',
    );
    expect(source.get).toHaveBeenCalledWith(ID);
    view.unmount();
    expect(revoke).toHaveBeenCalledWith('blob:detail/cover');
    vi.unstubAllGlobals();
  });

  it('화면이 바뀐 뒤 도착한 Blob은 object URL을 만들지 않는다', async () => {
    let finish!: (blob: Blob) => void;
    const source = {
      get: vi.fn(() => new Promise<Blob>((resolve) => { finish = resolve; })),
      put: vi.fn(),
      remove: vi.fn(),
    };
    const create = vi.fn(() => 'blob:late');
    vi.stubGlobal('URL', { ...URL, createObjectURL: create, revokeObjectURL: vi.fn() });
    const view = mount(source);
    await screen.findByRole('heading', { name: CUSTOM.name });
    view.unmount();
    await act(async () => finish(new Blob(['late'], { type: 'image/png' })));
    expect(create).not.toHaveBeenCalled();
    vi.unstubAllGlobals();
  });

  it('교체 실패는 기존 그림과 고른 파일을 보존하고 같은 파일로 재시도한다', async () => {
    const file = new File(['new'], 'new.webp', { type: 'image/webp' });
    const source = {
      get: vi.fn().mockResolvedValue(new Blob(['old'], { type: 'image/png' })),
      put: vi.fn().mockRejectedValueOnce(new Error('저장 연결 실패')).mockResolvedValue({ custom: true }),
      remove: vi.fn(),
    };
    vi.stubGlobal('URL', { ...URL, createObjectURL: vi.fn(() => 'blob:detail/old'), revokeObjectURL: vi.fn() });
    mount(source);
    await screen.findByRole('img', { name: '사용자 대표 그림' });
    fireEvent.change(screen.getByTestId('detail-representative-input'), { target: { files: [file] } });
    fireEvent.click(screen.getByRole('button', { name: '대표 그림 저장' }));
    const section = await screen.findByTestId('detail-representative');
    expect(await within(section).findByRole('alert'))
      .toHaveTextContent('저장 연결 실패');
    expect(screen.getByRole('img', { name: '사용자 대표 그림' })).toHaveAttribute('src', 'blob:detail/old');

    fireEvent.click(screen.getByRole('button', { name: '대표 그림 다시 저장' }));
    await waitFor(() => expect(source.put).toHaveBeenCalledTimes(2));
    expect(source.put.mock.calls).toEqual([[ID, file], [ID, file]]);
    vi.unstubAllGlobals();
  });

  it('자동 그림 복귀는 DELETE 뒤 사용자 그림을 걷고 기존 자동 미리보기를 남긴다', async () => {
    const source = {
      get: vi.fn().mockResolvedValue(new Blob(['old'], { type: 'image/png' })),
      put: vi.fn(),
      remove: vi.fn().mockResolvedValue(undefined),
    };
    vi.stubGlobal('URL', { ...URL, createObjectURL: vi.fn(() => 'blob:detail/old'), revokeObjectURL: vi.fn() });
    mount(source);
    await screen.findByRole('img', { name: '사용자 대표 그림' });
    fireEvent.click(screen.getByRole('button', { name: '자동 그림 사용' }));
    await act(async () => {});
    expect(source.remove).toHaveBeenCalledWith(ID);
    expect(screen.queryByRole('img', { name: '사용자 대표 그림' })).toBeNull();
    expect(screen.getByTestId('detail-preview-anchor')).toBeInTheDocument();
    vi.unstubAllGlobals();
  });

  it('교체 성공으로 새 Blob이 오면 이전 object URL을 해제한다', async () => {
    const source = {
      get: vi.fn()
        .mockResolvedValueOnce(new Blob(['old'], { type: 'image/png' }))
        .mockResolvedValueOnce(new Blob(['new'], { type: 'image/webp' })),
      put: vi.fn().mockResolvedValue({ custom: true }),
      remove: vi.fn(),
    };
    const create = vi.fn()
      .mockReturnValueOnce('blob:detail/old')
      .mockReturnValueOnce('blob:detail/new');
    const revoke = vi.fn();
    vi.stubGlobal('URL', { ...URL, createObjectURL: create, revokeObjectURL: revoke });
    mount(source);
    await screen.findByRole('img', { name: '사용자 대표 그림' });
    fireEvent.change(screen.getByTestId('detail-representative-input'), {
      target: { files: [new File(['new'], 'new.webp', { type: 'image/webp' })] },
    });
    fireEvent.click(screen.getByRole('button', { name: '대표 그림 저장' }));
    await waitFor(() => expect(screen.getByRole('img', { name: '사용자 대표 그림' }))
      .toHaveAttribute('src', 'blob:detail/new'));
    expect(revoke).toHaveBeenCalledWith('blob:detail/old');
    vi.unstubAllGlobals();
  });

  it('PUT 성공 뒤 새 Blob 조회가 실패하면 재업로드하지 않고 다시 불러올 수 있다', async () => {
    const source = {
      get: vi.fn()
        .mockResolvedValueOnce(new Blob(['old'], { type: 'image/png' }))
        .mockRejectedValueOnce(new Error('새 그림 조회 실패'))
        .mockResolvedValueOnce(new Blob(['new'], { type: 'image/webp' })),
      put: vi.fn().mockResolvedValue({ custom: true }),
      remove: vi.fn(),
    };
    const create = vi.fn()
      .mockReturnValueOnce('blob:detail/old')
      .mockReturnValueOnce('blob:detail/new');
    vi.stubGlobal('URL', { ...URL, createObjectURL: create, revokeObjectURL: vi.fn() });
    mount(source);
    await screen.findByRole('img', { name: '사용자 대표 그림' });
    fireEvent.change(screen.getByTestId('detail-representative-input'), {
      target: { files: [new File(['new'], 'new.webp', { type: 'image/webp' })] },
    });
    fireEvent.click(screen.getByRole('button', { name: '대표 그림 저장' }));
    expect(await within(screen.getByTestId('detail-representative')).findByRole('alert'))
      .toHaveTextContent('저장했지만 새 그림을 불러오지 못했어요');
    expect(screen.getByRole('img', { name: '사용자 대표 그림' })).toHaveAttribute('src', 'blob:detail/old');

    fireEvent.click(screen.getByRole('button', { name: '대표 그림 다시 불러오기' }));
    await waitFor(() => expect(screen.getByRole('img', { name: '사용자 대표 그림' }))
      .toHaveAttribute('src', 'blob:detail/new'));
    expect(source.put).toHaveBeenCalledTimes(1);
    vi.unstubAllGlobals();
  });

  it('본문을 읽을 수 있어도 업로드·편집 권한이 없으면 쓰기 버튼을 그리지 않는다', async () => {
    const source = {
      get: vi.fn().mockResolvedValue(new Blob(['old'], { type: 'image/png' })),
      put: vi.fn(),
      remove: vi.fn(),
    };
    vi.stubGlobal('URL', {
      ...URL,
      createObjectURL: vi.fn(() => 'blob:detail/read-only'),
      revokeObjectURL: vi.fn(),
    });
    mount(source, CUSTOM, {
      ...ACCOUNT,
      permissions: { ...ACCOUNT.permissions, '업로드·편집': false },
    });
    expect(await screen.findByRole('img', { name: '사용자 대표 그림' }))
      .toHaveAttribute('src', 'blob:detail/read-only');
    expect(source.get).toHaveBeenCalledWith(ID);
    expect(screen.queryByTestId('detail-representative-input')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '자동 그림 사용' })).not.toBeInTheDocument();
    vi.unstubAllGlobals();
  });

  it('읽기 전용 사용자도 GET 실패를 다시 시도해 사용자 그림을 볼 수 있다', async () => {
    const source = {
      get: vi.fn()
        .mockRejectedValueOnce(new Error('그림 조회 실패'))
        .mockResolvedValueOnce(new Blob(['old'], { type: 'image/png' })),
      put: vi.fn(),
      remove: vi.fn(),
    };
    vi.stubGlobal('URL', {
      ...URL,
      createObjectURL: vi.fn(() => 'blob:detail/read-retry'),
      revokeObjectURL: vi.fn(),
    });
    mount(source, CUSTOM, {
      ...ACCOUNT,
      permissions: { ...ACCOUNT.permissions, '업로드·편집': false },
    });
    const section = await screen.findByTestId('detail-representative');
    expect(await within(section).findByRole('alert'))
      .toHaveTextContent('그림 조회 실패');
    expect(screen.queryByTestId('detail-representative-input')).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '대표 그림 다시 불러오기' }));
    expect(await screen.findByRole('img', { name: '사용자 대표 그림' }))
      .toHaveAttribute('src', 'blob:detail/read-retry');
    expect(source.get).toHaveBeenCalledTimes(2);
    vi.unstubAllGlobals();
  });

  it('실제 API 출처는 Bearer GET Blob과 multipart File PUT 및 DELETE를 사용한다', async () => {
    const calls: Request[] = [];
    setToken('representative-token');
    const append = vi.spyOn(FormData.prototype, 'append');
    const fetcher = vi.spyOn(globalThis, 'fetch').mockImplementation(async input => {
      const request = input as Request;
      calls.push(request);
      if (request.method === 'GET') {
        return new Response(new Uint8Array([1, 2, 3]), {
          status: 200,
          headers: { 'Content-Type': 'image/png' },
        });
      }
      if (request.method === 'PUT') {
        return new Response(JSON.stringify({
          custom: true,
          fileName: 'cover.webp',
          contentType: 'image/webp',
          sizeBytes: 3,
        }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      return new Response(null, { status: 204 });
    });
    try {
      const source = apiRepresentativeImageSource();
      const blob = await source.get(ID);
      const file = new File(['new'], 'cover.webp', { type: 'image/webp' });
      await source.put(ID, file);
      await source.remove(ID);

      expect(blob.type).toBe('image/png');
      expect(blob.size).toBe(3);
      expect(typeof blob.arrayBuffer).toBe('function');
      expect(calls.map(request => request.method)).toEqual(['GET', 'PUT', 'DELETE']);
      expect(calls.every(request => request.headers.get('authorization') === 'Bearer representative-token')).toBe(true);
      expect(calls[1]!.headers.get('content-type')).toContain('multipart/form-data');
      expect(append).toHaveBeenCalledWith('image', file, 'cover.webp');
    } finally {
      append.mockRestore();
      fetcher.mockRestore();
      clearToken();
    }
  });
});
