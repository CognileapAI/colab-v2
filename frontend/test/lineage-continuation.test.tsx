import { act, fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { ParentPicker } from '../src/components/lineage/ParentPicker';
import { LineageFixModal } from '../src/components/lineage/LineageFixModal';
import type { DatasetRow } from '../src/components/lineage/types';
const rows = [{ datasetId: 'rain', name: 'Rain.nc', processingLevel: 1, topic: '강우' }, { datasetId: 'soil', name: 'Soil.nc', processingLevel: 3, topic: '토양' }] as DatasetRow[];
const props = { selfLv: 2, candidates: rows, levelFilter: null, onLevelFilterChange: vi.fn(), testId: 'picker' };
describe('계보 직접 찾기 복구와 선택', () => {
  it('이름 검색으로 결과를 좁히고 확정 전에는 연결하지 않는다', () => {
    const onPick = vi.fn();
    render(<ParentPicker {...props} onPick={onPick} onClose={() => {}} />);
    fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'rain' } });
    expect(screen.queryByText('Soil.nc')).not.toBeInTheDocument();
    fireEvent.click(screen.getByTestId('lin-pick-rain'));
    expect(onPick).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: '이 데이터로 연결' }));
    expect(onPick).toHaveBeenCalledWith(rows[0]);
  });
  it('후보 읽기 실패를 빈 결과와 구분하고 다시 시도한다', async () => {
    const candidates = vi.fn().mockRejectedValueOnce(new Error('offline')).mockResolvedValue(rows);
    render(<LineageFixModal datasetId="self" selfLv={2} candidateSource={{ candidates }} editSource={{ addParent: vi.fn() }} onSaved={vi.fn()} requestClose={vi.fn()} />);
    expect(await screen.findByRole('alert')).toHaveTextContent('읽지 못');
    expect(screen.queryByText('고를 수 있는 연구실 데이터가 아직 없어요.')).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '다시 시도' }));
    expect(await screen.findByTestId('lin-pick-rain')).toBeEnabled();
    expect(screen.getByTestId('lin-pick-soil')).toBeDisabled();
  });
  it('이전 단계 필터 응답이 늦어도 최신 결과를 덮지 않는다', async () => {
    let resolveOld!: (r: DatasetRow[]) => void;
    const candidates = vi.fn().mockImplementationOnce(() => new Promise<DatasetRow[]>(r => { resolveOld = r; })).mockResolvedValue([rows[1]]);
    render(<LineageFixModal datasetId="self" selfLv={3} candidateSource={{ candidates }} editSource={{ addParent: vi.fn() }} onSaved={vi.fn()} requestClose={vi.fn()} />);
    fireEvent.change(screen.getByTestId('lin-lv-filter'), { target: { value: '3' } });
    await screen.findByTestId('lin-pick-soil');
    await act(async () => resolveOld([rows[0]!]));
    expect(screen.getByTestId('lin-pick-soil')).toBeInTheDocument();
    expect(screen.queryByTestId('lin-pick-rain')).not.toBeInTheDocument();
  });
});

import { MemoryRouter } from 'react-router-dom';
import { LineageSection } from '../src/components/lineage/LineageSection';
import { FIXTURE_LINEAGE } from '../src/components/lineage/graphFixture';
import { apiLineageEditSource } from '../src/components/lineage/lineageEditSource';
const graph = { ...Object.values(FIXTURE_LINEAGE)[0]!, canEdit: true };
const parent = graph.edges.find(e => e.childDatasetId === graph.datasetId && e.parentDatasetId)!;
it('가공 방식을 저장한 서버 그래프로 교체하고 관계 제거 후 재조회 결과를 보여준다', async () => {
  const changed = { ...graph, edges: graph.edges.map(e => e === parent ? { ...e, method: '새 가공법' } : e) };
  const removed = { ...graph, nodes: graph.nodes.filter(n => n.datasetId !== parent.parentDatasetId), edges: graph.edges.filter(e => e.parentDatasetId !== parent.parentDatasetId) };
  const updateMethod = vi.fn().mockResolvedValue(changed);
  const removeParent = vi.fn().mockResolvedValue(removed);
  render(<MemoryRouter><LineageSection graph={graph} editSource={{ addParent: vi.fn(), updateMethod, removeParent }} /></MemoryRouter>);
  fireEvent.click(screen.getByRole('button', { name: '가공 방식 수정' }));
  fireEvent.change(screen.getByLabelText('가공 방식'), { target: { value: '새 가공법' } });
  fireEvent.click(screen.getByRole('button', { name: '가공 방식 저장' }));
  expect(await screen.findByText('가공 방식: 새 가공법 ·')).toBeInTheDocument();
  expect(updateMethod).toHaveBeenCalledWith(graph.datasetId, parent.parentDatasetId, '새 가공법');
  fireEvent.click(screen.getByRole('button', { name: '연결 제거' }));
  fireEvent.click(screen.getByRole('button', { name: '이 연결 제거' }));
  await act(async () => {});
  expect(screen.queryByText('가공 방식: 새 가공법 ·')).not.toBeInTheDocument();
  expect(removeParent).toHaveBeenCalledWith(graph.datasetId, parent.parentDatasetId);
});
it('가공 방식 저장 실패 시 입력을 보존하여 재시도하고 권한 없으면 수정하지 못한다', async () => {
  const updateMethod = vi.fn().mockRejectedValue(new Error('저장 연결 실패'));
  const { rerender } = render(<MemoryRouter><LineageSection graph={graph} editSource={{ addParent: vi.fn(), updateMethod }} /></MemoryRouter>);
  fireEvent.click(screen.getByRole('button', { name: '가공 방식 수정' }));
  fireEvent.change(screen.getByLabelText('가공 방식'), { target: { value: '유역 평균' } });
  fireEvent.click(screen.getByRole('button', { name: '가공 방식 저장' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('저장 연결 실패');
  expect(screen.getByLabelText('가공 방식')).toHaveValue('유역 평균');
  rerender(<MemoryRouter><LineageSection graph={{ ...graph, canEdit: false }} editSource={{ addParent: vi.fn(), updateMethod }} /></MemoryRouter>);
  expect(screen.queryByRole('button', { name: '가공 방식 수정' })).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: '가공 방식 저장' })).not.toBeInTheDocument();
});
it('실제 API 출처는 빈 가공법을 null로 저장하고 삭제 204 후 그래프를 다시 읽는다', async () => {
  const calls: Request[] = [];
  const fetcher = vi.spyOn(globalThis, 'fetch').mockImplementation(async input => {
    const request = input as Request; calls.push(request);
    return request.method === 'DELETE' ? new Response(null, { status: 204 }) : new Response(JSON.stringify(graph), { status: 200, headers: { 'Content-Type': 'application/json' } });
  });
  try {
    const source = apiLineageEditSource();
    await source.updateMethod!(graph.datasetId, parent.parentDatasetId!, '');
    expect(await calls[0]!.json()).toEqual({ method: null });
    await source.removeParent!(graph.datasetId, parent.parentDatasetId!);
    expect(calls.map(c => c.method)).toEqual(['PATCH', 'DELETE', 'GET']);
    expect(calls[2]!.url).toContain(`/datasets/${graph.datasetId}/lineage`);
  } finally { fetcher.mockRestore(); }
});

import { apiLineageSource } from '../src/components/lineage/lineageSource';
it('직접 찾기는 첫 페이지 뒤의 후보도 포함하고 모든 페이지에 Lv 조건을 유지한다', async () => {
  const calls: string[] = [];
  const fetcher = vi.spyOn(globalThis, 'fetch').mockImplementation(async input => {
    const url = (input as Request).url; calls.push(url);
    const next = calls.length === 1;
    return new Response(JSON.stringify({ items: [rows[next ? 0 : 1]], totalCount: 2, nextCursor: next ? 'second' : null }), { status: 200, headers: { 'Content-Type': 'application/json' } });
  });
  try {
    expect(await apiLineageSource().candidates(1)).toHaveLength(2);
    expect(calls[1]).toContain('cursor=second');
    expect(calls.every(url => url.includes('processingLevel=1'))).toBe(true);
  } finally { fetcher.mockRestore(); }
});
it('닫힌 계보 추가 화면의 늦은 저장 응답은 다음 화면을 바꾸지 않는다', async () => {
  let finish!: (value: typeof graph) => void;
  const onSaved = vi.fn();
  const addParent = vi.fn(() => new Promise<typeof graph>(resolve => { finish = resolve; }));
  const { unmount } = render(<LineageFixModal datasetId="self" selfLv={2} candidateSource={{ candidates: async () => rows }} editSource={{ addParent }} onSaved={onSaved} requestClose={vi.fn()} />);
  fireEvent.click(await screen.findByTestId('lin-pick-rain'));
  fireEvent.click(screen.getByTestId('lin-fix-save'));
  unmount();
  await act(async () => finish(graph));
  expect(onSaved).not.toHaveBeenCalled();
});
it('같은 데이터셋 그래프가 새로 도착해도 열린 계보 추가 화면을 닫지 않는다', async () => {
  const candidateSource = { candidates: async () => rows };
  const { rerender } = render(<MemoryRouter><LineageSection graph={graph} candidateSource={candidateSource} /></MemoryRouter>);
  fireEvent.click(screen.getByTestId('lin-edit'));
  await screen.findByTestId('lin-fix-modal');
  rerender(<MemoryRouter><LineageSection graph={{ ...graph }} candidateSource={candidateSource} /></MemoryRouter>);
  expect(screen.getByTestId('lin-fix-modal')).toBeInTheDocument();
});
