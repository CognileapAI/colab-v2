/**
 * S-02 프로젝트 목록 · S-02b 상세 — 정본 대비 시험 (WU-P5).
 * 오라클 = `E-05_프로젝트/documents/Policy_프로젝트.md` (v2.0) 와 그 목업 `프로젝트_260817.html`.
 * 화면 글자는 정본에서 그대로 온다 — 여기서 새 한국어 라벨을 만들지 않는다.
 */
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { ProjectsPage } from '../src/routes/ProjectsPage';
import { ProjectDetailPage } from '../src/routes/ProjectDetailPage';
import { FIXTURE_PROJECTS, fixtureProjectSource } from '../src/components/project/fixture';
import type { ProjectDetail, ProjectSource } from '../src/components/project/types';
import { ProjectGone } from '../src/components/project/types';

/** fireEvent 를 쓴다 — user-event 를 새로 들이지 않는다(집 관례, `test/members.test.tsx`). */
async function click(el: HTMLElement | null) {
  fireEvent.click(el as HTMLElement);
  await Promise.resolve();
}

async function select(el: HTMLElement | null, value: string) {
  fireEvent.change(el as HTMLElement, { target: { value } });
  await Promise.resolve();
}

function renderList(source: ProjectSource = fixtureProjectSource()) {
  return render(
    <MemoryRouter initialEntries={['/projects']}>
      <Routes>
        <Route path="/projects" element={<ProjectsPage source={source} />} />
        <Route path="/projects/:projectId" element={<div>프로젝트 상세</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

function renderDetail(projectId: string, source: ProjectSource = fixtureProjectSource()) {
  return render(
    <MemoryRouter initialEntries={[`/projects/${projectId}`]}>
      <Routes>
        <Route path="/projects/:projectId" element={<ProjectDetailPage source={source} />} />
        <Route path="/projects" element={<div>프로젝트 목록 화면</div>} />
        <Route path="/datasets/:datasetId" element={<div>데이터셋 상세 화면</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

const detailOf = (projectId: string): ProjectDetail =>
  structuredClone(FIXTURE_PROJECTS.find((p) => p.projectId === projectId)!);

function sourceReturning(detail: ProjectDetail): ProjectSource {
  return {
    list: async () => ({ items: [], totalCount: 0 }),
    get: async () => detail,
  };
}

// ════════════════════════════════════════════════════════════════════════════
// §8 목록 — 화면 소개와 툴바
// ════════════════════════════════════════════════════════════════════════════

describe('§8 목록 상단 — 무엇을 보관하는 곳인지를 한 문장으로', () => {
  it('정의문이 아니라 화면 소개가 선다 (v1.3 이력)', async () => {
    renderList();
    expect(await screen.findByRole('heading', { level: 1, name: '프로젝트' })).toBeInTheDocument();
    expect(
      screen.getByText(
        '우리 연구실의 과제와 논문을 등록해 두고, 각각에 어떤 데이터를 썼는지 모아 보는 곳이에요.',
      ),
    ).toBeInTheDocument();
  });

  it('정의·공동연구 범위 안내는 목록에 두지 않는다 — 새 프로젝트 모달의 몫이다', async () => {
    renderList();
    await screen.findByRole('heading', { level: 1, name: '프로젝트' });
    expect(screen.queryByText(/공동연구는 아직 지원하지 않아요/)).toBeNull();
  });
});

describe('§8 필터 바 — 툴바 한 줄에 모은다', () => {
  it('상태·유형·정렬 세 컨트롤과 보기 전환이 목록 위 툴바에 있다', async () => {
    renderList();
    const toolbar = await screen.findByTestId('project-toolbar');
    expect(within(toolbar).getByLabelText('상태')).toBeInTheDocument();
    expect(within(toolbar).getByLabelText('유형')).toBeInTheDocument();
    expect(within(toolbar).getByLabelText('정렬')).toBeInTheDocument();
    expect(within(toolbar).getByRole('radio', { name: '카드' })).toBeInTheDocument();
    expect(within(toolbar).getByRole('radio', { name: '표' })).toBeInTheDocument();
  });

  it('기본값은 상태 `진행 중` · 유형 전체 · `최근 시작 순` · 카드 보기다 (§5 목록 기본값)', async () => {
    renderList();
    const toolbar = await screen.findByTestId('project-toolbar');
    expect(within(toolbar).getByLabelText('상태')).toHaveValue('진행 중');
    expect(within(toolbar).getByLabelText('유형')).toHaveValue('전체');
    expect(within(toolbar).getByLabelText('정렬')).toHaveValue('최근 시작 순');
    expect(within(toolbar).getByRole('radio', { name: '카드' })).toBeChecked();
  });

  it('숨은 닫힘 건수를 적는다 — 숨김과 삭제가 헷갈리지 않게 (§8)', async () => {
    renderList();
    expect(await screen.findByText(/닫힘 1건은 숨겨져 있어요/)).toBeInTheDocument();
    expect(screen.getByText(/^4건/)).toBeInTheDocument();
  });

  it('상태를 `전체` 로 바꾸면 닫힌 것이 다시 보이고 숨은 건수 안내가 사라진다', async () => {
    renderList();
    await screen.findByText(/닫힘 1건은 숨겨져 있어요/);
    await select(screen.getByLabelText('상태'), '전체');
    await waitFor(() => expect(screen.getByText(/^5건/)).toBeInTheDocument());
    expect(screen.queryByText(/숨겨져 있어요/)).toBeNull();
  });
});

// ════════════════════════════════════════════════════════════════════════════
// §5 카드 보기
// ════════════════════════════════════════════════════════════════════════════

describe('§5 카드 — 지표 타일 세 칸과 이동 안내 한 줄', () => {
  it('카드마다 데이터셋 · 승인 · 기록 없음 세 칸이 있고 0이어도 칸을 비우지 않는다', async () => {
    renderList();
    const card = await screen.findByTestId('project-card-p3');
    const tiles = within(card).getAllByTestId('metric-tile');
    expect(tiles).toHaveLength(3);
    expect(tiles.map((t) => t.textContent)).toEqual(['5데이터셋', '2승인', '1기록 없음']);

    // p1 은 기록 없음 2건, p2 는 2건 — 0인 칸도 사라지지 않는다
    const zero = within(await screen.findByTestId('project-card-p4')).getAllByTestId('metric-tile');
    expect(zero.map((t) => t.textContent)).toEqual(['3데이터셋', '0승인', '1기록 없음']);
  });

  it('기록 없음은 1건부터 강조색이고 0이면 흐리게다 (§5 지표 타일)', async () => {
    renderList();
    const card = await screen.findByTestId('project-card-p3');
    const tiles = within(card).getAllByTestId('metric-tile');
    expect(tiles[1]).not.toHaveAttribute('data-zero', 'true'); // 승인 2
    expect(tiles[2]).toHaveAttribute('data-warn', 'true'); // 기록 없음 1
  });

  it('카드는 이동 안내 한 줄로 닫는다 — 그 안에 또 하나의 클릭 대상을 세우지 않는다 (§8)', async () => {
    renderList();
    const card = await screen.findByTestId('project-card-p3');
    const cta = within(card).getByTestId('card-cta');
    expect(cta.textContent).toContain('데이터셋 5개 보기');
    expect(within(cta).queryByRole('button')).toBeNull();
    expect(within(cta).queryByRole('link')).toBeNull();
  });

  it('설명이 비면 적기를 권하는 자리가 대신 선다 (§5 설명)', async () => {
    renderList();
    const empty = await screen.findByTestId('project-card-p4');
    expect(within(empty).getByText('설명을 적어 두면 나중에 찾기 쉬워요')).toBeInTheDocument();
  });

  it('닫힌 프로젝트는 `닫힘` 칩으로 밝힌다 — 투명도로 흐리게 만들지 않는다 (§5)', async () => {
    renderList();
    await select(await screen.findByLabelText('상태'), '전체');
    const closed = await screen.findByTestId('project-card-p5');
    expect(within(closed).getByText('닫힘')).toBeInTheDocument();
  });

  it('진행 바를 두지 않는다 — 계보 진척은 퍼센트가 아니라 남은 건수다 (§5)', async () => {
    renderList();
    await screen.findByTestId('project-card-p3');
    expect(screen.queryByRole('progressbar')).toBeNull();
  });
});

// ════════════════════════════════════════════════════════════════════════════
// §5 표 보기 · 두 보기의 관계
// ════════════════════════════════════════════════════════════════════════════

describe('§5 표 보기 — 견줄 때의 자리', () => {
  it('열은 여섯이다 — 이름 · 유형 · 데이터셋 수 · 기간 · 기록 없음 · 승인', async () => {
    renderList();
    await click(await screen.findByRole('radio', { name: '표' }));
    const headers = (await screen.findAllByRole('columnheader')).map((h) => h.textContent);
    expect(headers).toEqual(['프로젝트', '유형', '데이터셋', '기간', '기록 없음', 'Verified']);
  });

  it('승인 열은 `승인 / 전체` 로 적는다 — 분모는 데이터셋 수다 (§5·§8)', async () => {
    renderList();
    await click(await screen.findByRole('radio', { name: '표' }));
    const row = await screen.findByTestId('project-trow-p3');
    expect(within(row).getByTestId('verified-cell').textContent).toBe('2 / 5');
  });

  it('보기를 바꿔도 거른 결과와 정렬 순서는 그대로다 (§8 보기 전환)', async () => {
    renderList();
    await select(await screen.findByLabelText('정렬'), '데이터셋 많은 순');
    // 다시 세운 목록이 자리를 잡을 때까지 기다린다 — 갈아타는 도중을 재면 오라클이 아니다
    await waitFor(() =>
      expect(screen.getAllByTestId(/^project-card-/)[0]).toHaveAttribute(
        'data-testid',
        'project-card-p1',
      ),
    );
    const cardOrder = screen
      .getAllByTestId(/^project-card-/)
      .map((c) => c.getAttribute('data-testid'));
    await click(screen.getByRole('radio', { name: '표' }));
    const rowOrder = (await screen.findAllByTestId(/^project-trow-/)).map((r) =>
      (r.getAttribute('data-testid') ?? '').replace('trow', 'card'),
    );
    expect(rowOrder).toEqual(cardOrder);
    expect(rowOrder[0]).toBe('project-card-p1'); // 12건이 가장 많다
  });

  it('행을 펴지 않는다 — 카드도 행도 누르면 상세로 간다 (§8 · 1.5 이력)', async () => {
    renderList();
    await click(await screen.findByTestId('project-card-p3'));
    expect(await screen.findByText('프로젝트 상세')).toBeInTheDocument();
  });
});

// ════════════════════════════════════════════════════════════════════════════
// S-02b 상세
// ════════════════════════════════════════════════════════════════════════════

describe('§8 상세 — 돌아가기는 제목 위 한 줄', () => {
  it('`← 프로젝트 목록` 하나뿐이고 형제 전환도 경로도 없다 (v2.0 이력)', async () => {
    renderDetail('p1');
    await screen.findByRole('heading', { level: 1, name: '낙동강 유역 홍수기 강우-유출 응답 분석' });
    const back = screen.getByTestId('project-backrow');
    expect(within(back).getAllByRole('link')).toHaveLength(1);
    expect(back.textContent).toContain('프로젝트 목록');
    expect(screen.queryByRole('navigation', { name: '경로' })).toBeNull();
    expect(screen.queryByText(/다른 프로젝트/)).toBeNull();
  });

  it('없는 프로젝트는 목록으로 돌려보낸다 — 남의 연구실과 지워진 것을 가르지 않는다', async () => {
    renderDetail('없는것', {
      list: async () => ({ items: [], totalCount: 0 }),
      get: async () => {
        throw new ProjectGone();
      },
    });
    expect(await screen.findByTestId('project-gone')).toBeInTheDocument();
  });
});

describe('§1.2·§8 연결 주소 — 설명·기간과 다른 묶음', () => {
  it('개요와 다른 카드에 서고 `계보` 표시가 붙는다', async () => {
    renderDetail('p1');
    const link = await screen.findByTestId('project-link-card');
    expect(within(link).getByText('계보')).toBeInTheDocument();
    expect(within(link).getByRole('link', { name: 'https://www.ntis.go.kr/project/2025-NRF-0413' }))
      .toBeInTheDocument();
    expect(screen.getByTestId('project-overview').contains(link)).toBe(false);
  });

  it('주소가 없으면 다음 행동을 안내한다 (§8 빈 상태)', async () => {
    renderDetail('p4');
    expect(await screen.findByText('아직 적지 않았어요.')).toBeInTheDocument();
    expect(screen.queryByTestId('project-link-url')).toBeNull();
  });

  it('값을 고쳐 보여주지 않는다 — 받아 적은 그대로 링크다 (§1.3-3)', async () => {
    renderDetail('p2');
    const anchor = await screen.findByTestId('project-link-url');
    expect(anchor).toHaveTextContent('https://doi.org/10.1234/colab.2025.0182');
    expect(anchor).toHaveAttribute('href', 'https://doi.org/10.1234/colab.2025.0182');
  });
});

describe('§5 소속 데이터셋 표 — 행에서 판단이 끝난다', () => {
  it('열은 여섯이고 포맷 열은 없다 (v1.6 이력)', async () => {
    renderDetail('p3');
    const table = await screen.findByTestId('project-datasets');
    const headers = within(table).getAllByRole('columnheader').map((h) => h.textContent);
    expect(headers).toEqual(['데이터셋', '가공 단계', '기간', '계보', 'Verified', '']);
    expect(headers).not.toContain('포맷');
  });

  it('**전부 그린다 — 자르지 않는다** (§5 표 범위)', async () => {
    renderDetail('p1');
    const table = await screen.findByTestId('project-datasets');
    expect(within(table).getAllByTestId(/^pds-/)).toHaveLength(12);
    expect(screen.queryByText(/더 보기/)).toBeNull();
  });

  it('조각이 여럿이면 이름 뒤에 `조각 N` 칩을 붙인다 (E-02 와 같은 규칙)', async () => {
    renderDetail('p1');
    const row = await screen.findByTestId('pds-nakdong_precip_2025_Lv2.nc');
    expect(within(row).getByText('조각 4')).toBeInTheDocument();
    const single = screen.getByTestId('pds-nakdong_runoff_2025_Lv2.nc');
    expect(within(single).queryByText(/조각/)).toBeNull();
  });

  it('Verified 는 상태 글자이고, 없으면 `—` 다 — 빈칸을 두지 않는다 (§8)', async () => {
    renderDetail('p3');
    const yes = await screen.findByTestId('pds-hangang_DEM_5m_Lv1.tif');
    expect(within(yes).getByText('승인됨')).toBeInTheDocument();
    const no = screen.getByTestId('pds-hangang_DEM_10m_Lv1.tif');
    expect(within(no).getByTestId('dataset-verified').textContent).toBe('—');
  });

  it('행을 누르면 데이터셋 상세로 간다 (§2 규칙 맵)', async () => {
    renderDetail('p3');
    await click(await screen.findByTestId('pds-hangang_DEM_5m_Lv1.tif'));
    expect(await screen.findByText('데이터셋 상세 화면')).toBeInTheDocument();
  });
});

// ════════════════════════════════════════════════════════════════════════════
// 잠긴 데이터 (P-13·P-34) · 권한 (P-12 · §6)
// ════════════════════════════════════════════════════════════════════════════

describe('P-13 잠긴 데이터셋은 소속 데이터셋 표에서 사라지지 않는다', () => {
  const locked = (): ProjectDetail => {
    const detail = detailOf('p3');
    const [first, ...rest] = detail.datasets;
    detail.datasets = [{ ...first!, accessState: '잠김', bodyAccessible: false }, ...rest];
    return detail;
  };

  it('이름은 그대로 보이고 행이 사라지지 않는다 — 숨기면 접근 요청 흐름이 죽는다', async () => {
    renderDetail('p3', sourceReturning(locked()));
    const table = await screen.findByTestId('project-datasets');
    expect(within(table).getAllByTestId(/^pds-/)).toHaveLength(5);
    const row = screen.getByTestId('pds-hangang_DEM_5m_Lv1.tif');
    expect(within(row).getByText(/hangang_DEM_5m_Lv1\.tif/)).toBeInTheDocument();
  });

  it('그 행이 잠김으로 표시되고 본체 쪽 값은 그 자리에 서지 않는다 (P-34)', async () => {
    renderDetail('p3', sourceReturning(locked()));
    const row = await screen.findByTestId('pds-hangang_DEM_5m_Lv1.tif');
    expect(row).toHaveAttribute('data-locked', 'true');
    // 자물쇠·`접근 요청` 의 실물은 WU-P6 이 채운다 — 여기서는 그 자리가 있음을 잰다.
    expect(row.querySelector('[data-slot="lock-indicator"]')).not.toBeNull();
  });

  it('잠긴 행도 카드의 데이터셋 수에서 빠지지 않는다', async () => {
    renderDetail('p3', sourceReturning(locked()));
    const table = await screen.findByTestId('project-datasets');
    expect(within(table).getAllByTestId(/^pds-/)).toHaveLength(5);
  });
});

describe('§6 권한 — `프로젝트 생성` 이 꺼지면 쓰기 자리를 숨긴다 (P-12)', () => {
  it('`canManage` 가 false 면 정보 수정·닫기·소속 해제가 DOM 에서 사라진다', async () => {
    const detail = detailOf('p3');
    detail.canManage = false;
    renderDetail('p3', sourceReturning(detail));
    await screen.findByRole('heading', { level: 1, name: '한강 상류 DEM 기반 유역 경계 재산정' });
    expect(screen.queryByText('정보 수정')).toBeNull();
    expect(screen.queryByText('프로젝트 닫기')).toBeNull();
    expect(screen.queryByText('소속 해제')).toBeNull();
  });

  it('켜져 있으면 자리가 선다 — 조회에는 권한 차이가 없다 (§6)', async () => {
    renderDetail('p3');
    await screen.findByRole('heading', { level: 1, name: '한강 상류 DEM 기반 유역 경계 재산정' });
    expect(screen.getByText('정보 수정')).toBeInTheDocument();
    expect(screen.getAllByText('소속 해제')).toHaveLength(5);
  });

  it('삭제는 데이터셋 0건일 때만 보인다 (§1.3-6 · §8)', async () => {
    renderDetail('p3');
    await screen.findByTestId('project-datasets');
    expect(screen.queryByText('삭제')).toBeNull();

    const empty = detailOf('p3');
    empty.datasets = [];
    renderDetail('p3', sourceReturning(empty));
    await waitFor(() => expect(screen.getAllByText('삭제').length).toBeGreaterThan(0));
  });
});
