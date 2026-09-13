/**
 * 가공 전 데이터 후보 선택 모달 — 기획서 rev2 ＋ 기획자 2026-09-13 구두 피드백.
 *
 * 오라클 = `업로드_계보_260905_rev2.html` 의 `#findModal`(라디오 행 · 취소／이 데이터로 연결)
 * ＋ 기획자 피드백 「핵심 정보만」·「대표 파일명 외 N개」·「검색어 하나만」·「하단 고정 영역」.
 *
 *   ㈎ 필터는 **검색어 하나**다 — 분류·주제·가공 단계·기간 칸이 없다.
 *   ㈏ 후보 줄은 **라디오 단일 선택**이다.
 *   ㈐ 파일은 **대표 하나 ＋ 「외 N개」** 다 — 전체 나열이 없다.
 *   ㈑ 행이 적는 것은 **이름 · 가공 단계 · 분류 · 기간** 뿐이다.
 *   ㈒ 하단 고정 영역이 선택 요약을 갱신한다 — 고르기 전에는 「후보를 고르세요」.
 *   ㈓ 하단의 **가공 방식** 입력값이 `onPick` 으로 가고, 연결 카드의 초기값이 된다.
 *   ㈔ 초과 후보는 **보이되 못 고른다**(회귀 — `R-21`).
 *
 * 단언마다 **대상 건수를 먼저 잰다** — 빈 집합 통과(green-by-skip)를 막는다.
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { ParentPicker } from '../src/components/lineage/ParentPicker';
import { SessionProvider } from '../src/permission/session';
import { UploadEntry } from '../src/components/upload/UploadEntry';
import type {
  LineageCandidate,
  LineageSource,
  LineageSuggestionResponse,
} from '../src/components/lineage/types';
import type {
  PreviewSource,
  ProjectSource,
  UploadSource,
  UploadSources,
} from '../src/components/upload/types';
import type { CurrentAccount, Schemas } from '../src/api/client';

const RAIN = '01JYZ9K7WQ3N8V4M2X6C5B0D01';
const SOIL = '01JYZ9K7WQ3N8V4M2X6C5B0D03';
const UPLOAD_ID = '01JYZ9K7WQ3N8V4M2X6C5B0UP1';
const FILE_ID = '01JYZ9K7WQ3N8V4M2X6C5B0FI1';

function candidate(
  over: Partial<LineageCandidate> & { datasetId: string; name: string },
): LineageCandidate {
  return {
    fileNames: [],
    fileExtensions: [],
    category: null,
    period: null,
    source: { label: null, url: null, downloadedOn: null },
    processingLevel: 1,
    topic: null,
    bodyAccessible: true,
    ...over,
  } as LineageCandidate;
}

const ROWS: LineageCandidate[] = [
  candidate({
    datasetId: RAIN,
    name: '낙동강 강우',
    fileNames: ['rain_2025_01.nc', 'rain_2025_02.nc', 'rain_2025_03.nc'],
    fileExtensions: ['nc'],
    category: '기상·기후 인자',
    period: { start: '2025-01-01T00:00:00Z', end: '2025-12-31T00:00:00Z' },
    source: { label: 'ERA5 재분석', url: null, downloadedOn: null },
    processingLevel: 1,
    topic: '강우·강수',
  }),
  candidate({
    datasetId: SOIL,
    name: '유역 토양도',
    fileNames: ['soil.tif'],
    fileExtensions: ['tif'],
    category: '환경 인자',
    processingLevel: 3,
    topic: '토지피복·LULC',
  }),
];

const BASE = {
  selfLv: 2,
  candidates: ROWS,
  levelFilter: null,
  onLevelFilterChange: vi.fn(),
  onSearch: vi.fn(),
  onLoadMore: vi.fn(),
  nextCursor: null,
  testId: 'lin-picker',
};

function openPicker(onPick = vi.fn()) {
  render(<ParentPicker {...BASE} onPick={onPick} onClose={() => {}} />);
  return onPick;
}

function radios(): HTMLInputElement[] {
  return [RAIN, SOIL].map((id) => screen.getByTestId(`lin-pick-${id}`) as HTMLInputElement);
}

// ═══ ㈎ 필터는 검색어 하나 ═══
describe('후보 선택 모달의 필터', () => {
  it('검색어 한 칸만 남고 분류·주제·가공 단계·기간 칸이 없다', () => {
    openPicker();
    expect(screen.getAllByRole('searchbox')).toHaveLength(1);
    expect(screen.queryByLabelText('분류')).toBeNull();
    expect(screen.queryByLabelText('주제')).toBeNull();
    expect(screen.queryByTestId('lin-lv-filter')).toBeNull();
    expect(screen.queryByLabelText('후보 기간 시작')).toBeNull();
    expect(screen.queryByLabelText('후보 기간 끝')).toBeNull();
    expect(screen.queryAllByRole('combobox')).toHaveLength(0);
  });

  it('검색어를 적으면 그 한 조건만 서버 질의로 간다', () => {
    const onSearch = vi.fn();
    render(<ParentPicker {...BASE} onSearch={onSearch} onPick={vi.fn()} onClose={() => {}} />);
    fireEvent.change(screen.getByRole('searchbox'), { target: { value: '강우' } });
    expect(onSearch).toHaveBeenCalledTimes(1);
    expect(onSearch).toHaveBeenLastCalledWith({ q: '강우', limit: 25 });
  });
});

// ═══ ㈏ 라디오 단일 선택 ═══
describe('후보 줄은 라디오 단일 선택이다', () => {
  it('후보마다 같은 이름의 라디오가 서고 마지막에 고른 하나만 선택된다', () => {
    openPicker();
    const [rain, soil] = radios();
    expect(rain!.type).toBe('radio');
    expect(soil!.type).toBe('radio');
    expect(rain!.name).toBe(soil!.name);
    expect(rain!.name).not.toBe('');

    fireEvent.click(rain!);
    expect(rain!.checked).toBe(true);
    expect(soil!.checked).toBe(false);
  });
});

// ═══ ㈐ 파일은 대표 하나 ＋ 「외 N개」 ═══
describe('후보 줄의 파일 표기', () => {
  it('파일이 3건이면 대표 하나와 「외 2개」만 적고 나머지 파일명을 나열하지 않는다', () => {
    openPicker();
    const files = screen.getByTestId(`lin-files-${RAIN}`);
    expect(files.textContent).toBe('rain_2025_01.nc 외 2개');
    expect(screen.queryByText(/rain_2025_02\.nc/)).toBeNull();
    expect(screen.queryByText(/rain_2025_03\.nc/)).toBeNull();
  });

  it('파일이 1건이면 이름만 적고 「외」를 붙이지 않는다', () => {
    openPicker();
    expect(screen.getByTestId(`lin-files-${SOIL}`).textContent).toBe('soil.tif');
  });
});

// ═══ ㈑ 행이 적는 것은 이름·가공 단계·분류·기간 뿐 ═══
describe('후보 줄이 적는 값', () => {
  it('이름·가공 단계·분류·기간만 적고 주제와 원천 표기는 적지 않는다', () => {
    openPicker();
    const row = screen.getByTestId(`lin-row-${RAIN}`);
    expect(row.textContent).toContain('낙동강 강우');
    expect(row.textContent).toContain('Lv1');
    expect(row.textContent).toContain('기상·기후 인자');
    expect(row.textContent).toContain('2025-01-01 ~ 2025-12-31');
    expect(row.textContent).not.toContain('강우·강수');
    expect(row.textContent).not.toContain('ERA5 재분석');
  });
});

// ═══ ㈒ 하단 고정 영역의 선택 요약 ═══
describe('하단 고정 영역', () => {
  it('고르기 전에는 「후보를 고르세요」이고 고르면 이름·단계·분류로 갱신된다', () => {
    openPicker();
    const summary = screen.getByTestId('lin-find-summary');
    expect(summary.textContent).toBe('후보를 고르세요');
    fireEvent.click(radios()[0]!);
    expect(screen.getByTestId('lin-find-summary').textContent).toBe(
      '낙동강 강우 · Lv1 · 기상·기후 인자',
    );
  });

  it('고르기 전에는 「이 데이터로 연결」을 누를 수 없다', () => {
    const onPick = openPicker();
    expect(screen.getByRole('button', { name: '이 데이터로 연결' })).toBeDisabled();
    expect(screen.getByRole('button', { name: '취소' })).toBeInTheDocument();
    fireEvent.click(radios()[0]!);
    expect(screen.getByRole('button', { name: '이 데이터로 연결' })).toBeEnabled();
    expect(onPick).not.toHaveBeenCalled();
  });
});

// ═══ ㈓ 가공 방식이 onPick 으로 간다 ═══
describe('하단의 가공 방식 입력', () => {
  it('적은 값이 연결할 때 `onPick` 의 두 번째 인자로 간다', () => {
    const onPick = openPicker();
    fireEvent.click(radios()[0]!);
    fireEvent.change(screen.getByTestId('lin-find-method'), {
      target: { value: '유역 클리핑 · 유역 평균' },
    });
    fireEvent.click(screen.getByRole('button', { name: '이 데이터로 연결' }));
    expect(onPick).toHaveBeenCalledTimes(1);
    expect(onPick).toHaveBeenCalledWith(ROWS[0], '유역 클리핑 · 유역 평균');
  });
});

// ═══ ㈔ 초과 후보는 보이되 못 고른다 (회귀) ═══
describe('초과 후보', () => {
  it('자기 Lv 보다 높은 후보는 라디오가 비활성이고 사유가 읽힌다', () => {
    openPicker();
    expect(radios()[1]!.disabled).toBe(true);
    expect(screen.getByTestId(`lin-over-${SOIL}`).textContent).toContain('연결을 지우거나');
    expect(screen.getByTestId(`lin-row-${SOIL}`).textContent).toContain('유역 토양도');
  });
});

// ═══ 등록 ③ 연결 단계와의 연결 ═══
function account(): CurrentAccount {
  return {
    accountId: '01JYZ9K7WQ3N8V4M2X6C5B0AC1',
    name: '호랑이',
    email: 'tiger@example.ac.kr',
    role: '연구원',
    labId: '01JYZ9K7WQ3N8V4M2X6C5B0LB1',
    labName: '수자원순환연구실',
    permissions: {
      '업로드·편집': true,
      '프로젝트 생성': true,
      '승인 위임': false,
      '연구실 설정': false,
    } as Record<Schemas['PermissionSwitch'], boolean>,
  } as unknown as CurrentAccount;
}

function fakes(): UploadSources {
  const files = [
    {
      fileId: FILE_ID,
      fileName: 'nakdong_precip_2025_Lv2.nc',
      kind: '본체',
      byteSize: 349_000,
      createdAt: '2026-09-14T00:00:00Z',
    },
  ];
  const upload = {
    async create() {
      return { uploadId: UPLOAD_ID, files } as never;
    },
    async status() {
      return {
        uploadId: UPLOAD_ID,
        ready: true,
        failure: null,
        metadataComplete: true,
        files,
      } as never;
    },
    async register() {
      return { datasetId: '01JYZ9K7WQ3N8V4M2X6C5B0DS1' } as never;
    },
    async attachGrid() {
      return [] as never;
    },
  } as unknown as UploadSource;
  const preview = {
    async palettes() {
      return [{ palette: 'viridis', label: '비리디스' }];
    },
    async createRender() {
      return { renderId: 'r', state: '실패', failure: null } as never;
    },
    async getRender() {
      return { renderId: 'r', state: '실패', failure: null } as never;
    },
  } as unknown as PreviewSource;
  const projects = {
    async list() {
      return [];
    },
    async create() {
      return { projectId: '01JYZ9K7WQ3N8V4M2X6C5B0PR9', name: 'x', type: '국가과제' } as never;
    },
  } as unknown as ProjectSource;
  const lineage: LineageSource = {
    async suggestions() {
      return {
        degraded: false,
        scope: { labId: 'l', labName: '수자원순환연구실', searchedCount: 0 },
        rawDataLikely: false,
        suggestions: [],
      } as unknown as LineageSuggestionResponse;
    },
    async candidates() {
      return ROWS as never;
    },
  };
  return { upload, preview, projects, lineage } as unknown as UploadSources;
}

async function click(el: Element | null) {
  fireEvent.click(el as HTMLElement);
  await act(async () => {});
}

function makeFile() {
  const f = new File(['x'], 'nakdong_precip_2025_Lv2.nc', { type: 'application/octet-stream' });
  Object.defineProperty(f, 'size', { value: 349_000 });
  return f;
}

async function openLineage() {
  render(
    <MemoryRouter initialEntries={['/datasets']}>
      <SessionProvider account={account()}>
        <UploadEntry sources={fakes()} />
      </SessionProvider>
    </MemoryRouter>,
  );
  await click(screen.getByTestId('gnb-upload'));
  await screen.findByTestId('upload-modal');
  fireEvent.change(screen.getByTestId('up-drop-input'), { target: { files: [makeFile()] } });
  await act(async () => {});
  await screen.findByTestId('up-files');
  await click(await screen.findByTestId('reg-open'));
  await screen.findByTestId('reg-steps');
  fireEvent.change(screen.getByTestId('reg-level'), { target: { value: 'Lv2' } });
  await act(async () => {});
  await click(screen.getByRole('button', { name: /^③/ }));
  await screen.findByTestId('lin-step');
}

describe('③ 연결 단계의 문구와 모달 연동', () => {
  it('직접 추가 버튼 문구가 기획서 축자이고 연결 0건이면 빈 상태 한 줄이 선다', async () => {
    await openLineage();
    expect(screen.getByTestId('lin-add').textContent).toBe('+ 가공 전 데이터 추가');
    expect(screen.getByTestId('lin-hint').textContent).toBe('아직 연결한 가공 전 데이터가 없어요');
  });

  it('모달에서 적은 가공 방식이 연결 카드의 초기값으로 들어온다', async () => {
    await openLineage();
    await click(screen.getByTestId('lin-add'));
    await screen.findByTestId('lin-picker');
    await click(screen.getByTestId(`lin-pick-${RAIN}`));
    fireEvent.change(screen.getByTestId('lin-find-method'), { target: { value: '유역 평균' } });
    await act(async () => {});
    await click(screen.getByRole('button', { name: '이 데이터로 연결' }));
    expect(screen.getAllByTestId('lin-card')).toHaveLength(1);
    expect((screen.getByTestId('lin-method') as HTMLInputElement).value).toBe('유역 평균');
    // 연결이 생기면 빈 상태 한 줄은 사라진다.
    expect(screen.queryByTestId('lin-hint')).toBeNull();
  });
});
