import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { DatasetPreviewSection } from '../src/components/datasetpreview/DatasetPreviewSection';
import type { DatasetPreviewSource } from '../src/components/datasetpreview/types';
import type { RenderJob } from '../src/components/preview/types';

const FILE_A = '01JYZ9K7WQ3N8V4M2X6C5B0F01';
const FILE_B = '01JYZ9K7WQ3N8V4M2X6C5B0F02';
const RENDER_ID = '01JYZ9K7WQ3N8V4M2X6C5B0RE1';

function source(overrides: Partial<DatasetPreviewSource> = {}) {
  const done = {
    renderId: RENDER_ID, status: '완료',
    result: { imageUrl: 'https://viz.example/preview.png', legend: { palette: 'viridis', variable: 'rain', classes: [] } },
  } as unknown as RenderJob;
  return {
    palettes: vi.fn(async () => [{ palette: 'viridis' }]),
    files: vi.fn(async () => [
      { fileId: FILE_A, fileName: 'a.nc', renderable: true },
      { fileId: FILE_B, fileName: 'b.nc', renderable: true },
    ]),
    describe: vi.fn(async () => ({
      variables: ['rain', 'temperature'],
      instants: { count: 2, first: '2024-01-01T00:00:00Z', last: '2024-01-02T00:00:00Z' },
      default: { variable: 'rain', instant: '2024-01-01T00:00:00Z' },
    })),
    create: vi.fn(async () => done), get: vi.fn(async () => done),
    probeTile: vi.fn(async () => 'ok' as const), mapGeometry: vi.fn(async () => undefined),
    screenshot: vi.fn(async () => new Blob()), lookupValue: vi.fn(async () => ({}) as never),
    ...overrides,
  } as DatasetPreviewSource & { create: ReturnType<typeof vi.fn>; describe: ReturnType<typeof vi.fn> };
}

async function ready(s: ReturnType<typeof source>) {
  render(<DatasetPreviewSection datasetId="dataset-1" source={s} pollMs={1} />);
  await waitFor(() => expect(s.describe).toHaveBeenCalled());
  await waitFor(() => expect(screen.getByTestId('dt-preview-draw')).not.toBeDisabled());
}

describe('선택한 상세 미리보기만 명시 실행한다', () => {
  it('files 조회 성공 후 renderable 0건은 미지원으로 명시하고 만들지 않는다', async () => {
    const s = source({ files: vi.fn(async () => [{ fileId: FILE_A, fileName: 'index.bin', renderable: false }]) });
    render(<DatasetPreviewSection datasetId="dataset-1" source={s} pollMs={1} />);
    expect(await screen.findByTestId('dt-preview-unsupported')).toHaveTextContent('미리보기를 지원하는 파일이 없어요.');
    expect(screen.getByTestId('dt-preview-draw')).toBeDisabled();
    expect(s.create).not.toHaveBeenCalled();
  });
  it('mount와 선택 변경은 만들지 않고 선택 파일 후보만 조회한다', async () => {
    const s = source();
    await ready(s);
    expect(s.create).not.toHaveBeenCalled();
    expect(s.describe).toHaveBeenCalledWith(FILE_A);
    fireEvent.change(screen.getByTestId('dt-pick-file'), { target: { value: FILE_B } });
    await waitFor(() => expect(s.describe).toHaveBeenLastCalledWith(FILE_B));
    expect(s.create).not.toHaveBeenCalled();
  });

  it('보기 한 번은 표시된 선택값과 단일 파일만 한 번 보낸다', async () => {
    const s = source();
    await ready(s);
    fireEvent.change(screen.getByTestId('dt-pick-file'), { target: { value: FILE_B } });
    await waitFor(() => expect(s.describe).toHaveBeenLastCalledWith(FILE_B));
    fireEvent.change(screen.getByTestId('dt-pick-variable'), { target: { value: 'temperature' } });
    fireEvent.change(screen.getByTestId('dt-pick-instant'), { target: { value: '2024-01-02T00:00:00Z' } });
    fireEvent.click(screen.getByTestId('dt-preview-draw'));
    await waitFor(() => expect(s.create).toHaveBeenCalledTimes(1));
    expect(s.create).toHaveBeenCalledWith({
      datasetId: 'dataset-1', palette: 'viridis', classCount: 6, fileIds: [FILE_B],
      variable: 'temperature', instant: '2024-01-02T00:00:00Z',
    });
  });

  it('진행 중에는 중복 제출과 선택 변경을 막는다', async () => {
    let resolve!: (job: RenderJob) => void;
    const s = source({ create: vi.fn(() => new Promise<RenderJob>((r) => { resolve = r; })) });
    await ready(s);
    fireEvent.click(screen.getByTestId('dt-preview-draw'));
    fireEvent.click(screen.getByTestId('dt-preview-draw'));
    expect(s.create).toHaveBeenCalledTimes(1);
    expect(screen.getByTestId('dt-preview-draw')).toBeDisabled();
    expect(screen.getByTestId('dt-pick-file')).toBeDisabled();
    await act(async () => resolve({ renderId: RENDER_ID, status: '그리는 중' } as RenderJob));
  });

  it('create 응답을 잃으면 결과 불명으로 남기고 자동 재생성하지 않는다', async () => {
    const s = source({ create: vi.fn(async () => { throw new TypeError('connection lost'); }) });
    await ready(s);
    fireEvent.click(screen.getByTestId('dt-preview-draw'));
    expect(await screen.findByText('요청 결과를 확인할 수 없어요. 다시 실행하기 전에 작업 상태를 확인해 주세요.')).toBeTruthy();
    expect(s.create).toHaveBeenCalledTimes(1);
    expect(screen.getByTestId('dt-preview-draw')).toBeDisabled();
    fireEvent.click(screen.getByTestId('dt-preview-draw'));
    expect(s.create).toHaveBeenCalledTimes(1);
  });

  it('create의 PreviewUnavailable도 접수 여부 불명으로 잠그고 재생성하지 않는다', async () => {
    const { PreviewUnavailable } = await import('../src/components/preview/types');
    const s = source({ create: vi.fn(async () => { throw new PreviewUnavailable('gateway lost'); }) });
    await ready(s);
    fireEvent.click(screen.getByTestId('dt-preview-draw'));
    expect(await screen.findByText('요청 결과를 확인할 수 없어요. 다시 실행하기 전에 작업 상태를 확인해 주세요.')).toBeTruthy();
    expect(screen.getByTestId('dt-preview-draw')).toBeDisabled();
    fireEvent.click(screen.getByTestId('dt-preview-draw'));
    expect(s.create).toHaveBeenCalledTimes(1);
  });

  it('renderId를 받은 뒤 통신 실패는 같은 job 조회만 재개한다', async () => {
    const done = source().get(RENDER_ID);
    const get = vi.fn().mockRejectedValueOnce(new TypeError('connection lost')).mockImplementation(() => done);
    const s = source({ get });
    await ready(s);
    fireEvent.click(screen.getByTestId('dt-preview-draw'));
    await waitFor(() => expect(get).toHaveBeenCalledTimes(2));
    expect(s.create).toHaveBeenCalledTimes(1);
  });

  it('dataset/source 변경 뒤 이전 create 응답을 화면에 연결하지 않는다', async () => {
    let resolveOld!: (job: RenderJob) => void;
    const old = source({ create: vi.fn(() => new Promise<RenderJob>((resolve) => { resolveOld = resolve; })) });
    const next = source({ files: vi.fn(async () => [{ fileId: FILE_A, fileName: 'next.nc', renderable: true }]) });
    const view = render(<DatasetPreviewSection datasetId="dataset-1" source={old} pollMs={1} />);
    await waitFor(() => expect(screen.getByTestId('dt-preview-draw')).not.toBeDisabled());
    fireEvent.change(screen.getByTestId('dt-pick-file'), { target: { value: FILE_B } });
    await waitFor(() => expect(old.describe).toHaveBeenLastCalledWith(FILE_B));
    fireEvent.click(screen.getByTestId('dt-preview-draw'));
    view.rerender(<DatasetPreviewSection datasetId="dataset-2" source={next} pollMs={1} />);
    await act(async () => resolveOld({ renderId: `${RENDER_ID}-old`, status: '그리는 중' } as RenderJob));
    await waitFor(() => expect(screen.getByTestId('dt-preview-draw')).not.toBeDisabled());
    expect(next.describe).toHaveBeenLastCalledWith(FILE_A);
    expect((screen.getByTestId('dt-pick-file') as HTMLSelectElement).value).toBe(FILE_A);
    expect(old.get).not.toHaveBeenCalled();
    expect(next.create).not.toHaveBeenCalled();
  });
});

describe('화면 총 소요 시간', () => {
  it('실제 PNG decode 전에는 확정하지 않고 선택값과 renderId를 진단 이벤트에 연결한다', async () => {
    const s = source();
    const events: unknown[] = [];
    window.addEventListener('colab-preview-timing', ((e: CustomEvent) => { events.push(e.detail); }) as EventListener, { once: true });
    await ready(s);
    fireEvent.click(screen.getByTestId('dt-preview-draw'));
    const image = await screen.findByTestId('preview-single-image');
    let finishDecode!: () => void;
    Object.defineProperty(image, 'decode', { value: vi.fn(() => new Promise<void>((r) => { finishDecode = r; })) });
    fireEvent.load(image);
    expect(screen.queryByTestId('dt-preview-total')).toBeNull();
    expect(events).toHaveLength(0);
    await act(async () => finishDecode());
    expect(await screen.findByTestId('dt-preview-total')).toHaveTextContent('총 ');
    expect(events[0]).toMatchObject({ render_id: RENDER_ID, file_ids: [FILE_A], variable: 'rain', instant: '2024-01-01T00:00:00Z' });
  });

  it('이미지 decode 실패를 성공 시간으로 기록하지 않는다', async () => {
    const s = source();
    await ready(s);
    fireEvent.click(screen.getByTestId('dt-preview-draw'));
    const image = await screen.findByTestId('preview-single-image');
    Object.defineProperty(image, 'decode', { value: vi.fn(async () => { throw new Error('decode failed'); }) });
    fireEvent.load(image);
    await act(async () => { await Promise.resolve(); });
    expect(screen.queryByTestId('dt-preview-total')).toBeNull();
  });

  it('이전 요청의 늦은 decode가 새 요청의 시간과 선택값을 확정하지 않는다', async () => {
    const firstId = `${RENDER_ID}A`;
    const secondId = `${RENDER_ID}B`;
    const jobs = [firstId, secondId].map((renderId, index) => ({
      renderId, status: '완료',
      result: { imageUrl: `https://viz.example/${index}.png`, legend: { palette: 'viridis', classes: [] } },
    } as unknown as RenderJob));
    const create = vi.fn().mockResolvedValueOnce(jobs[0]).mockResolvedValueOnce(jobs[1]);
    const get = vi.fn(async (id: string) => jobs.find((job) => job.renderId === id)!);
    const s = source({ create, get });
    const events: Array<{ render_id: string; variable: string }> = [];
    window.addEventListener('colab-preview-timing', ((e: CustomEvent) => { events.push(e.detail); }) as EventListener);
    await ready(s);
    fireEvent.click(screen.getByTestId('dt-preview-draw'));
    const first = await screen.findByTestId('preview-single-image');
    let finishFirst!: () => void;
    Object.defineProperty(first, 'decode', { value: vi.fn(() => new Promise<void>((resolve) => { finishFirst = resolve; })) });
    fireEvent.load(first);
    await waitFor(() => expect(screen.getByTestId('dt-preview-draw')).not.toBeDisabled());
    fireEvent.change(screen.getByTestId('dt-pick-variable'), { target: { value: 'temperature' } });
    fireEvent.click(screen.getByTestId('dt-preview-draw'));
    const second = await screen.findByTestId('preview-single-image');
    let finishSecond!: () => void;
    Object.defineProperty(second, 'decode', { value: vi.fn(() => new Promise<void>((resolve) => { finishSecond = resolve; })) });
    fireEvent.load(second);
    await act(async () => finishFirst());
    expect(events).toHaveLength(0);
    expect(screen.queryByTestId('dt-preview-total')).toBeNull();
    await act(async () => finishSecond());
    expect(events).toEqual([expect.objectContaining({ render_id: secondId, variable: 'temperature' })]);
  });
});
