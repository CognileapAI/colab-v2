import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { FileList } from '../src/components/detail/FileList';
import type { FileSource } from '../src/components/detail/types';
import { SearchEvidenceRequestError } from '../src/components/detail/searchEvidenceSource';
import type { SearchEvidenceItem, SearchEvidenceSource } from '../src/components/detail/searchEvidenceSource';
import { SessionProvider } from '../src/permission/session';
import { account } from './factories';

const DATASET_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA1';
const FILE_ID = '01JYZ9K7WQ3N8V4M2X6C5B0F01';

function fileSource(replace = vi.fn()): FileSource {
  return {
    list: async () => [{
      fileId: FILE_ID,
      fileName: 'rain.nc',
      kind: '본체',
      byteSize: 32,
      createdAt: '2026-09-12T00:00:00Z',
    }],
    downloadTicket: async () => ({
      url: '/download', expiresAt: '2026-09-13T00:00:00Z', fileName: 'rain.nc', byteSize: 32, scope: '파일',
    }),
    add: async () => { throw new Error('unused'); },
    replace: async (datasetId, fileId, file) => {
      replace(datasetId, fileId, file.name);
      return { fileId, fileName: file.name, kind: '본체', byteSize: file.size, createdAt: '2026-09-13T00:00:00Z' };
    },
    remove: async () => undefined,
  };
}

function item(over: Partial<SearchEvidenceItem> = {}): SearchEvidenceItem {
  return {
    fileId: FILE_ID,
    fileName: 'rain.nc',
    fileRevision: 3,
    evidence: null,
    ...over,
  };
}

function evidenceSource(initial = item()) {
  let current = initial;
  const calls = { list: 0, saves: [] as Parameters<SearchEvidenceSource['save']>[2][] };
  const source: SearchEvidenceSource = {
    async list() {
      calls.list += 1;
      return { items: [current] };
    },
    async save(_datasetId, _fileId, payload) {
      calls.saves.push(payload);
      current = item({
        evidence: {
          revision: payload.expectedRevision + 1,
          status: payload.status,
          facts: payload.facts,
          source: { ...payload.source, sha256: 'abc' },
          reviewedBy: payload.status === 'reviewed' ? '연구자' : null,
          reviewedAt: payload.status === 'reviewed' ? '2026-09-13T01:00:00Z' : null,
        },
      });
      return current.evidence!;
    },
  };
  return { source, calls, setCurrent: (next: SearchEvidenceItem) => { current = next; } };
}

function mount(evidence: SearchEvidenceSource, opts: { canEdit?: boolean; files?: FileSource } = {}) {
  render(
    <SessionProvider account={account({ '업로드·편집': opts.canEdit ?? true })}>
      <FileList
        datasetId={DATASET_ID}
        source={opts.files ?? fileSource()}
        evidenceSource={evidence}
        actions={{
          canRequestVerification: false,
          canApproveVerification: false,
          canCancelVerification: false,
          canEditLineage: false,
          canDelete: false,
          canDownload: true,
          canRequestAccess: false,
        }}
      />
    </SessionProvider>,
  );
}

async function openEvidence() {
  fireEvent.click(screen.getByTestId('dt-files-toggle'));
  await screen.findByTestId(`dt-file-${FILE_ID}`);
  fireEvent.click(screen.getByRole('button', { name: 'rain.nc 검색 근거' }));
  return screen.findByRole('form', { name: 'rain.nc 검색 근거' });
}

describe('파일별 검색 근거', () => {
  it('파일 목록과 근거는 각각 사람이 열기 전까지 조회하지 않는다', async () => {
    const evidence = evidenceSource();
    mount(evidence.source);
    expect(evidence.calls.list).toBe(0);
    fireEvent.click(screen.getByTestId('dt-files-toggle'));
    await screen.findByTestId(`dt-file-${FILE_ID}`);
    expect(evidence.calls.list).toBe(0);
    fireEvent.click(screen.getByRole('button', { name: 'rain.nc 검색 근거' }));
    await screen.findByRole('form', { name: 'rain.nc 검색 근거' });
    expect(evidence.calls.list).toBe(1);
  });

  it('출처와 선택적 사실을 초안으로 저장한 뒤 서버 값을 다시 조회한다', async () => {
    const evidence = evidenceSource();
    mount(evidence.source);
    const form = await openEvidence();
    fireEvent.click(within(form).getByLabelText('학습 입력'));
    fireEvent.click(within(form).getByLabelText('검증'));
    fireEvent.click(within(form).getByLabelText('설명서'));
    fireEvent.click(within(form).getByLabelText('분석 코드'));
    fireEvent.change(within(form).getByLabelText('설명서 이름'), { target: { value: 'README.md' } });
    fireEvent.change(within(form).getByLabelText('절 또는 문단'), { target: { value: '2. 자료 범위' } });
    fireEvent.change(within(form).getByLabelText('원문 발췌'), { target: { value: '매일 관측한 강우 자료' } });
    fireEvent.change(within(form).getByLabelText('기간 시작'), { target: { value: '2025-01-01' } });
    fireEvent.change(within(form).getByLabelText('기간 끝'), { target: { value: '2025-12-31' } });
    fireEvent.change(within(form).getByLabelText('직접 관측'), { target: { value: 'yes' } });
    fireEvent.change(within(form).getByLabelText('보간'), { target: { value: 'no' } });
    fireEvent.click(within(form).getByRole('button', { name: '초안 저장' }));
    await waitFor(() => expect(evidence.calls.saves).toHaveLength(1));
    expect(evidence.calls.saves[0]).toEqual({
      expectedRevision: 0,
      expectedFileRevision: 3,
      facts: {
        roles: ['model_input', 'validation', 'documentation', 'analysis_code'],
        period: { start: '2025-01-01', end: '2025-12-31' },
        directObservation: true,
        interpolated: false,
      },
      source: { label: 'README.md', locator: '2. 자료 범위', text: '매일 관측한 강우 자료' },
      status: 'draft',
    });
    expect(evidence.calls.list).toBe(2);
    expect(await within(form).findByRole('status')).toHaveTextContent('상태: 초안');
  });

  it('검토 완료 저장은 별도 버튼이며 stale 근거는 재확인 필요를 표시한다', async () => {
    const evidence = evidenceSource(item({
      evidence: {
        revision: 4,
        status: 'stale',
        facts: { variable: 'rainfall' },
        source: { label: 'manual.pdf', locator: 'p. 7', text: '강우 변수', sha256: 'old' },
        reviewedBy: '연구자',
        reviewedAt: '2026-09-12T01:00:00Z',
      },
    }));
    mount(evidence.source);
    const form = await openEvidence();
    expect(within(form).getByRole('status')).toHaveTextContent('파일 내용이 바뀌어 재확인이 필요합니다.');
    expect(within(form).queryByText('Verified')).toBeNull();
    fireEvent.click(within(form).getByRole('button', { name: '확인하고 저장' }));
    await waitFor(() => expect(evidence.calls.saves).toHaveLength(1));
    expect(evidence.calls.saves[0]?.status).toBe('reviewed');
    expect(evidence.calls.saves[0]?.expectedRevision).toBe(4);
  });

  it('409이면 작성 중인 원문을 보존하고 서버 값 재조회 동작을 제공한다', async () => {
    const current = item({ evidence: {
      revision: 2, status: 'draft', facts: { region: '낙동강' },
      source: { label: 'old.pdf', locator: 'p. 1', text: 'old', sha256: 'old' },
      reviewedBy: null, reviewedAt: null,
    } });
    let listCalls = 0;
    const source: SearchEvidenceSource = {
      async list() { listCalls += 1; return { items: [current] }; },
      async save() { throw new SearchEvidenceRequestError(409); },
    };
    mount(source);
    const form = await openEvidence();
    const excerpt = within(form).getByLabelText('원문 발췌');
    fireEvent.change(excerpt, { target: { value: '내가 작성 중인 원문' } });
    fireEvent.click(within(form).getByRole('button', { name: '초안 저장' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('다른 변경이 먼저 저장되었습니다.');
    expect(excerpt).toHaveValue('내가 작성 중인 원문');
    fireEvent.click(screen.getByRole('button', { name: '서버 값 다시 불러오기' }));
    expect(screen.getByRole('alertdialog', { name: '작성 중인 검색 근거 처리' })).toBeInTheDocument();
    expect(excerpt).toHaveValue('내가 작성 중인 원문');
    fireEvent.click(screen.getByRole('button', { name: '작성 내용 버리기' }));
    await waitFor(() => expect(listCalls).toBe(2));
    expect(excerpt).toHaveValue('old');
  });

  it('기간 한쪽만 입력하면 작성값을 보존하고 저장을 막는다', async () => {
    const evidence = evidenceSource();
    mount(evidence.source);
    const form = await openEvidence();
    fireEvent.change(within(form).getByLabelText('설명서 이름'), { target: { value: 'manual.pdf' } });
    fireEvent.change(within(form).getByLabelText('절 또는 문단'), { target: { value: 'p. 2' } });
    fireEvent.change(within(form).getByLabelText('원문 발췌'), { target: { value: '관측 기간' } });
    fireEvent.change(within(form).getByLabelText('기간 시작'), { target: { value: '2025-01-01' } });
    expect(within(form).getByRole('alert')).toHaveTextContent('기간은 시작과 끝을 함께 입력해 주세요.');
    expect(within(form).getByRole('button', { name: '초안 저장' })).toBeDisabled();
    expect(within(form).getByLabelText('기간 시작')).toHaveValue('2025-01-01');
    expect(evidence.calls.saves).toHaveLength(0);
  });

  it('작성 중 닫기는 확인을 거치고 계속 작성을 선택하면 입력을 보존한다', async () => {
    const evidence = evidenceSource();
    mount(evidence.source);
    const form = await openEvidence();
    const region = within(form).getByLabelText('지역');
    fireEvent.change(region, { target: { value: '한강' } });
    fireEvent.click(screen.getByRole('button', { name: '닫기' }));
    const dialog = screen.getByRole('alertdialog', { name: '작성 중인 검색 근거 처리' });
    fireEvent.click(within(dialog).getByRole('button', { name: '계속 작성' }));
    expect(region).toHaveValue('한강');
    expect(screen.getByRole('form', { name: 'rain.nc 검색 근거' })).toBeInTheDocument();
  });

  it('파일 교체 뒤 열려 있던 근거 편집기를 닫아 이전 파일 내용 근거를 무효화한다', async () => {
    const evidence = evidenceSource();
    const replace = vi.fn();
    mount(evidence.source, { files: fileSource(replace) });
    await openEvidence();
    fireEvent.change(screen.getByTestId(`dt-file-replace-${FILE_ID}`), {
      target: { files: [new File(['new'], 'rain-new.nc')] },
    });
    await waitFor(() => expect(replace).toHaveBeenCalledTimes(1));
    expect(screen.queryByRole('form', { name: 'rain.nc 검색 근거' })).toBeNull();
  });

  it('업로드·편집 권한이 없어도 근거를 읽지만 입력 폼과 저장 동작은 그리지 않는다', async () => {
    const evidence = evidenceSource(item({ evidence: {
      revision: 2,
      status: 'reviewed',
      facts: { roles: ['documentation'], region: '낙동강' },
      source: { label: 'README.md', locator: '2절', text: '관측 범위 원문', sha256: 'abc' },
      reviewedBy: '연구자',
      reviewedAt: '2026-09-13T01:00:00Z',
    } }));
    mount(evidence.source, { canEdit: false });
    fireEvent.click(screen.getByTestId('dt-files-toggle'));
    await screen.findByTestId(`dt-file-${FILE_ID}`);
    fireEvent.click(screen.getByRole('button', { name: 'rain.nc 검색 근거' }));
    const evidenceView = await screen.findByRole('region', { name: 'rain.nc 검색 근거' });
    expect(evidence.calls.list).toBe(1);
    expect(evidenceView).toHaveTextContent('README.md');
    expect(evidenceView).toHaveTextContent('2절');
    expect(evidenceView).toHaveTextContent('관측 범위 원문');
    expect(evidenceView).toHaveTextContent('설명서');
    expect(evidenceView).toHaveTextContent('낙동강');
    expect(within(evidenceView).queryByRole('form')).toBeNull();
    expect(within(evidenceView).queryByRole('button', { name: '초안 저장' })).toBeNull();
    expect(within(evidenceView).queryByRole('button', { name: '확인하고 저장' })).toBeNull();
  });
});
