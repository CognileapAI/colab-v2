import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { SessionProvider } from '../src/permission/session';
import type { CurrentAccount } from '../src/api/client';
import { UploadModal } from '../src/components/upload/UploadModal';
import { PreviewPanel } from '../src/components/upload/PreviewPanel';
import type { PreviewSource, UploadSources } from '../src/components/upload/types';
import { UploadGone } from '../src/components/upload/types';

const ID = '01JYZ9K7WQ3N8V4M2X6C5B0UP1';
const drawing = { renderId: ID, status: '그리는 중', stage: '지도 그리는 중' };
const ready = { uploadId: ID, ready: true, renderable: true,
  metadataComplete: true, files: [], failure: null };

function startUpload(status: UploadSources['upload']['status']) {
  const create = vi.fn(async () => ({ uploadId: ID, files: [] }));
  const sources = { upload: { create, status }, preview: { palettes: async () => [] },
    projects: { list: async () => [] } } as unknown as UploadSources;
  const account = { accountId: ID, labId: ID, name: '검수', labName: '검수 연구실',
    permissions: { '업로드·편집': true } } as unknown as CurrentAccount;
  const view = render(<MemoryRouter><SessionProvider account={account}>
    <UploadModal sources={sources} onClose={() => {}} />
  </SessionProvider></MemoryRouter>);
  fireEvent.change(screen.getByTestId('up-drop-input'), {
    target: { files: [new File(['data'], 'sample.nc')] },
  });
  return { ...view, create };
}

describe('진행 상태 조회 실패 복구', () => {
  it('렌더 접수 응답을 기다리는 동안에도 진행 상태를 표시한다', async () => {
    const source = {
      palettes: async () => [{ palette: 'viridis', label: '비리디스' }],
      createRender: () => new Promise(() => {}),
    } as unknown as PreviewSource;
    render(<PreviewPanel source={source} uploadId={ID} hasReferenceGrid />);
    fireEvent.click(await screen.findByTestId('up-preview-draw'));
    expect(screen.getByTestId('up-preview-stage')).toHaveTextContent('미리보기 요청 중');
  });

  it('서버 렌더 완료 후 실제 이미지 로드까지 진행 안내를 유지한다', async () => {
    const source = {
      palettes: async () => [{ palette: 'viridis', label: '비리디스' }],
      createRender: async () => ({ renderId: ID, status: '완료',
        result: { imageUrl: '/preview.png' } }),
      getRender: () => new Promise(() => {}),
    } as unknown as PreviewSource;
    render(<PreviewPanel source={source} uploadId={ID} hasReferenceGrid />);
    fireEvent.click(await screen.findByTestId('up-preview-draw'));
    const img = await screen.findByTestId('up-preview-image');
    expect(screen.getByTestId('up-preview-image-loading')).toBeInTheDocument();
    fireEvent.load(img);
    expect(screen.queryByTestId('up-preview-image-loading')).toBeNull();
  });

  it('파일 추가 전송 중 이전 분석 완료 상태를 사용하지 않는다', async () => {
    const { create } = startUpload(vi.fn().mockResolvedValue(ready));
    await waitFor(() => expect(screen.getByTestId('up-analyze')).toHaveAttribute('data-stage', '3'));
    create.mockImplementationOnce(() => new Promise(() => {}));
    fireEvent.change(screen.getByTestId('up-drop-input'), {
      target: { files: [new File(['next'], 'second.nc')] },
    });
    await waitFor(() => expect(create).toHaveBeenCalledTimes(2));
    expect(screen.getByTestId('up-analyze')).toHaveAttribute('data-stage', '1');
  });
  it('렌더 조회 실패를 알린 뒤 그리는 중 표시를 끝낸다', async () => {
    const source = {
      palettes: async () => [{ palette: 'viridis', label: '비리디스' }],
      createRender: async () => drawing,
      getRender: async () => { throw new Error('temporary connection error'); },
    } as unknown as PreviewSource;
    render(<PreviewPanel source={source} uploadId={ID} hasReferenceGrid />);
    fireEvent.click(await screen.findByTestId('up-preview-draw'));
    await screen.findByTestId('up-preview-error');
    expect(screen.queryByTestId('up-preview-stage')).toBeNull();
    expect(screen.getByTestId('up-preview-draw')).toBeEnabled();
  });

  it('업로드 분석 조회가 한번 끊겨도 전송을 반복하지 않고 준비 상태를 다시 확인한다', async () => {
    const status = vi.fn()
      .mockRejectedValueOnce(new Error('temporary connection error'))
      .mockResolvedValue({ uploadId: ID, ready: true, renderable: true,
        metadataComplete: true, files: [], failure: null });
    const create = vi.fn(async () => ({ uploadId: ID, files: [] }));
    const sources = {
      upload: { create, status },
      preview: { palettes: async () => [] },
      projects: { list: async () => [] },
    } as unknown as UploadSources;
    const account = { accountId: ID, labId: ID, name: '검수', labName: '검수 연구실',
      permissions: { '업로드·편집': true } } as unknown as CurrentAccount;
    render(<MemoryRouter><SessionProvider account={account}>
      <UploadModal sources={sources} onClose={() => {}} />
    </SessionProvider></MemoryRouter>);
    fireEvent.change(screen.getByTestId('up-drop-input'), {
      target: { files: [new File(['data'], 'sample.nc')] },
    });
    await waitFor(() => expect(screen.getByTestId('up-analyze')).toHaveAttribute('data-stage', '3'),
      { timeout: 3000 });
    expect(create).toHaveBeenCalledTimes(1);
    expect(status).toHaveBeenCalledTimes(2);
  });

  it('반복 실패는 멈추고 수동 재시도로 분석 조회만 복구한다', async () => {
    const status = vi.fn().mockRejectedValue(new Error('offline'));
    const { create } = startUpload(status);
    await screen.findByTestId('up-status-retry', {}, { timeout: 4500 });
    expect(status).toHaveBeenCalledTimes(3);
    expect(screen.queryByTestId('up-analyze')).toBeNull();
    await act(async () => { await new Promise((resolve) => setTimeout(resolve, 1100)); });
    expect(status).toHaveBeenCalledTimes(3);
    status.mockResolvedValue(ready);
    fireEvent.click(screen.getByTestId('up-status-retry'));
    await waitFor(() => expect(screen.getByTestId('up-analyze')).toHaveAttribute('data-stage', '3'));
    expect(screen.queryByTestId('up-status-error')).toBeNull();
    expect(create).toHaveBeenCalledTimes(1);
  }, 10000);

  it('삭제된 업로드는 재조회하지 않고 다시 올리도록 안내한다', async () => {
    const status = vi.fn().mockRejectedValue(new UploadGone());
    startUpload(status);
    expect(await screen.findByTestId('up-status-error')).toHaveTextContent('다시 올려 주세요');
    expect(screen.queryByTestId('up-status-retry')).toBeNull();
    await act(async () => { await new Promise((resolve) => setTimeout(resolve, 1100)); });
    expect(status).toHaveBeenCalledTimes(1);
  });

  it('화면을 떠난 뒤 도착한 조회 실패는 재시도를 예약하지 않는다', async () => {
    let reject!: (reason: Error) => void;
    const status = vi.fn(() => new Promise<never>((_, fail) => { reject = fail; }));
    const view = startUpload(status);
    await waitFor(() => expect(status).toHaveBeenCalledTimes(1));
    view.unmount();
    await act(async () => {
      reject(new Error('late error'));
      await new Promise((resolve) => setTimeout(resolve, 1100));
    });
    expect(status).toHaveBeenCalledTimes(1);
  });
});
