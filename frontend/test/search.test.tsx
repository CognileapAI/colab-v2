/**
 * S-01 검색 히어로 · S-06 검색 결과 — 정본 대비 시험 (WU-P4 / `S1-fe-search`).
 *
 * 오라클 = `CLAUDE.md §3`(AI 응답 규격) · `S1-PLAN.md §6` 완료 정의 6
 * (뒤진 범위 · 근거 한 줄 · 관련도 막대 · 0건 안내 · 잠김 표시 · 장애 폴백) ·
 * `contracts/seams/fe-core.yaml` `searchDatasets` · `PERMISSION-PRINCIPLES P-13·P-34`.
 *
 * 화면이 **어휘 검색을 어휘 검색이라고 말하는가**가 이 파일이 지키는 것이다.
 */
import { render, screen, waitFor, within, fireEvent } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { LabPage } from '../src/routes/LabPage';
import { SearchResultsPage } from '../src/routes/SearchResultsPage';
import { SearchUnavailable } from '../src/components/search/types';
import type { SearchResultRow, SearchResults, SearchSource } from '../src/components/search/types';

const LAB_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AHU';

function hit(over: Partial<SearchResultRow> = {}): SearchResultRow {
  return {
    datasetId: '01JYZ9K7WQ3N8V4M2X6C5B0A01',
    name: '한강 유역 강수 관측',
    fileCount: 1,
    topic: '강수',
    processingLevel: 0,
    projects: { representative: null, moreCount: 0, names: [] },
    uploader: { accountId: '01JYZ9K7WQ3N8V4M2X6C5B0AHT', name: '호랑이' },
    lastModifiedAt: '2026-08-01T00:00:00Z',
    lineageState: '원천',
    lineageConfirmedAt: null,
    verified: false,
    accessState: '열림',
    bodyAccessible: true,
    // ⭑ **⟨16차 해제 · `〈298〉`⟩ 두 칸이 늘었다** (`SearchResultRow` 의 두 번째 객체).
    // 이 파일의 오라클(범위 줄 · 근거 한 줄 · 관련도 막대 · 0건 · 잠김 · 장애)은 그대로다.
    summary: '한강 유역 지점 강수 관측 원자료',
    period: { start: '2025-06-01T00:00:00Z', end: '2025-09-30T00:00:00Z' },
    relevanceBar: 1,
    rationale: '수자원순환연구실 안 128건에서 ‘강수’가 이름에 맞았다 — 기간·지역·품질은 이 검색이 확인하지 못했다.',
    ...over,
  };
}

function results(over: Partial<SearchResults> = {}): SearchResults {
  return {
    scope: { labId: LAB_ID, labName: '수자원순환연구실', searchedCount: 128 },
    isDataQuery: true,
    degraded: false,
    items: [hit()],
    totalCount: 1,
    nextCursor: null,
    ...over,
  };
}

function sourceOf(body: SearchResults): SearchSource {
  return { search: async () => body };
}

function renderResults(source: SearchSource, q = '강수 데이터 있어?') {
  return render(
    <MemoryRouter initialEntries={[`/datasets/search?q=${encodeURIComponent(q)}`]}>
      <Routes>
        <Route path="/datasets/search" element={<SearchResultsPage source={source} />} />
        <Route path="/datasets" element={<div>데이터셋 카탈로그 화면</div>} />
        <Route path="/datasets/:datasetId" element={<div>데이터셋 상세 화면</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

// ════════════════════════════════════════════════════════════════════════════
// S-01 검색 히어로
// ════════════════════════════════════════════════════════════════════════════

describe('S-01 검색 히어로', () => {
  it('연구실 화면에 검색 입력칸이 하나 선다 (질문은 1~200자)', () => {
    render(
      <MemoryRouter initialEntries={['/lab']}>
        <Routes>
          <Route path="/lab" element={<LabPage />} />
          <Route path="/datasets/search" element={<div>검색 결과 화면</div>} />
        </Routes>
      </MemoryRouter>,
    );
    const box = screen.getByLabelText('검색 질문') as HTMLInputElement;
    expect(box.maxLength).toBe(200);
  });

  it('히어로가 어휘 검색임을 미리 말한다 — 뜻으로 찾아 준다고 약속하지 않는다', () => {
    render(
      <MemoryRouter initialEntries={['/lab']}>
        <Routes>
          <Route path="/lab" element={<LabPage />} />
          <Route path="/datasets/search" element={<div>검색 결과 화면</div>} />
        </Routes>
      </MemoryRouter>,
    );
    expect(screen.getByTestId('search-hero-note').textContent).toContain('적혀 있는 낱말 그대로');
  });

  it('질문을 넣고 찾으면 검색 결과 화면으로 간다', async () => {
    render(
      <MemoryRouter initialEntries={['/lab']}>
        <Routes>
          <Route path="/lab" element={<LabPage />} />
          <Route path="/datasets/search" element={<div>검색 결과 화면</div>} />
        </Routes>
      </MemoryRouter>,
    );
    fireEvent.change(screen.getByLabelText('검색 질문'), { target: { value: '강수' } });
    fireEvent.click(screen.getByRole('button', { name: '찾기' }));
    await waitFor(() => expect(screen.getByText('검색 결과 화면')).toBeTruthy());
  });

  it('빈 질문으로는 넘어가지 않는다 — 빈 검색을 서버에 보내지 않는다', async () => {
    render(
      <MemoryRouter initialEntries={['/lab']}>
        <Routes>
          <Route path="/lab" element={<LabPage />} />
          <Route path="/datasets/search" element={<div>검색 결과 화면</div>} />
        </Routes>
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole('button', { name: '찾기' }));
    await Promise.resolve();
    expect(screen.queryByText('검색 결과 화면')).toBeNull();
  });
});

// ════════════════════════════════════════════════════════════════════════════
// S-06 검색 결과 — 뒤진 범위가 먼저다
// ════════════════════════════════════════════════════════════════════════════

describe('S-06 뒤진 범위', () => {
  it('뒤진 범위 줄이 결과보다 **먼저** 나온다 (DOM 순서로 확인한다)', async () => {
    const { container } = renderResults(sourceOf(results()));
    const scope = await screen.findByTestId('search-scope');
    expect(scope.textContent).toContain('수자원순환연구실');
    expect(scope.textContent).toContain('128건');
    const list = container.querySelector('[data-testid="search-results"]')!;
    expect(scope.compareDocumentPosition(list) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it('0건이어도 뒤진 범위가 먼저 나온다', async () => {
    renderResults(sourceOf(results({ items: [], totalCount: 0 })));
    const scope = await screen.findByTestId('search-scope');
    expect(scope.textContent).toContain('128건');
  });
});

// ════════════════════════════════════════════════════════════════════════════
// 근거 한 줄 · 관련도 막대
// ════════════════════════════════════════════════════════════════════════════

describe('S-06 결과 카드', () => {
  it('카드마다 근거가 한 줄로 붙는다 — 펼침·더보기가 없다', async () => {
    renderResults(sourceOf(results()));
    const card = await screen.findByTestId('search-hit');
    const why = within(card).getByTestId('search-rationale');
    expect(why.textContent).toBe(hit().rationale);
    expect(why.textContent).not.toContain('\n');
    expect(within(card).queryByText('더보기')).toBeNull();
  });

  it('관련도는 막대 하나다 — 퍼센트도 등급 텍스트도 숫자도 화면에 없다', async () => {
    const { container } = renderResults(
      sourceOf(results({ items: [hit({ relevanceBar: 0.42 })] })),
    );
    const card = await screen.findByTestId('search-hit');
    const bar = within(card).getByTestId('relevance-bar');
    // 길이는 막대에만 실린다 — 사람이 읽는 자리에 숫자가 서면 정본 위반이다
    expect((bar.firstElementChild as HTMLElement).style.width).toBe('42%');
    expect(card.textContent).not.toMatch(/%|42|0\.42|확실|애매|모름/);
    expect(container.querySelector('[aria-valuenow]')).toBeNull();
  });

  it('결과 순서를 화면이 다시 매기지 않는다 — 서버가 준 순서 그대로다', async () => {
    const rows = [
      hit({ datasetId: '01JYZ9K7WQ3N8V4M2X6C5B0AA1', name: '먼저', relevanceBar: 1 }),
      hit({ datasetId: '01JYZ9K7WQ3N8V4M2X6C5B0AA2', name: '나중', relevanceBar: 0.2 }),
    ];
    renderResults(sourceOf(results({ items: rows, totalCount: 2 })));
    const cards = await screen.findAllByTestId('search-hit');
    expect(cards.map((c) => within(c).getByTestId('hit-name').textContent)).toEqual(['먼저', '나중']);
  });

  it('결과를 누르면 데이터셋 상세로 간다', async () => {
    renderResults(sourceOf(results()));
    fireEvent.click(await screen.findByTestId('hit-name'));
    await waitFor(() => expect(screen.getByText('데이터셋 상세 화면')).toBeTruthy());
  });
});

// ════════════════════════════════════════════════════════════════════════════
// 잠김 — P-13·P-34
// ════════════════════════════════════════════════════════════════════════════

describe('S-06 잠긴 데이터', () => {
  it('잠긴 데이터도 결과에 남고 이름이 보이며 자물쇠가 붙는다', async () => {
    renderResults(
      sourceOf(
        results({
          items: [hit({ name: '잠긴 관측자료', accessState: '잠김', bodyAccessible: false })],
        }),
      ),
    );
    const card = await screen.findByTestId('search-hit');
    expect(within(card).getByTestId('hit-name').textContent).toBe('잠긴 관측자료');
    expect(within(card).getByText('잠김')).toBeTruthy();
    expect(within(card).getByLabelText('잠긴 데이터')).toBeTruthy();
    // 누가 올렸는지는 잠김에서 더 필요하다 (요청할 상대)
    expect(card.textContent).toContain('호랑이');
  });
});

// ════════════════════════════════════════════════════════════════════════════
// 0건 — 정직한 빈 상태
// ════════════════════════════════════════════════════════════════════════════

describe('S-06 0건', () => {
  it('무엇을 뒤졌고 아무것도 안 맞았다고 말한다', async () => {
    renderResults(sourceOf(results({ items: [], totalCount: 0 })));
    const empty = await screen.findByTestId('search-empty');
    expect(empty.textContent).toContain('맞는 것이 없었어요');
  });

  it('낱말을 그대로 찾는다는 사실과 그 예를 말한다 (ts_config=simple 의 현실)', async () => {
    renderResults(sourceOf(results({ items: [], totalCount: 0 })));
    const empty = await screen.findByTestId('search-empty');
    expect(empty.textContent).toContain('「강수량」으로는 「강수」');
  });

  it('억지 제안을 하지 않는다 — 0건에 결과 카드가 하나도 없다', async () => {
    renderResults(sourceOf(results({ items: [], totalCount: 0 })));
    await screen.findByTestId('search-empty');
    expect(screen.queryAllByTestId('search-hit')).toHaveLength(0);
    expect(screen.queryByText(/이런 데이터는 어때요|추천/)).toBeNull();
  });

  it('카탈로그로 가는 길을 준다 — 결과를 지어내는 대신', async () => {
    renderResults(sourceOf(results({ items: [], totalCount: 0 })));
    const empty = await screen.findByTestId('search-empty');
    fireEvent.click(within(empty).getByRole('link', { name: /카탈로그/ }));
    await waitFor(() => expect(screen.getByText('데이터셋 카탈로그 화면')).toBeTruthy());
  });
});

// ════════════════════════════════════════════════════════════════════════════
// 데이터를 찾는 질문이 아닐 때 — 오류가 아니다
// ════════════════════════════════════════════════════════════════════════════

describe('S-06 데이터 질문이 아닐 때', () => {
  it('오류가 아니라 안내로 답한다', async () => {
    renderResults(sourceOf(results({ isDataQuery: false, items: [], totalCount: 0 })));
    expect((await screen.findByTestId('search-not-data-query')).textContent).toContain(
      '데이터를 찾는 질문에 답해요',
    );
    expect(screen.queryByTestId('search-empty')).toBeNull();
  });
});

// ════════════════════════════════════════════════════════════════════════════
// 장애 폴백 — 감추지 않는다
// ════════════════════════════════════════════════════════════════════════════

describe('S-06 장애 폴백', () => {
  it('degraded 면 그 사실을 말하고 결과는 그대로 보여준다', async () => {
    renderResults(sourceOf(results({ degraded: true, degradedReason: '해석기가 죽었다' })));
    const banner = await screen.findByTestId('search-degraded');
    expect(banner.textContent).toContain('낱말 그대로');
    expect(await screen.findByTestId('search-hit')).toBeTruthy();
    // AI 가 준 문구를 그대로 화면에 싣지 않는다 (화면 문구는 이쪽이 정한다)
    expect(banner.textContent).not.toContain('해석기가 죽었다');
  });

  it('검색이 아예 닿지 않으면 카탈로그 길을 주고, 도는 척하지 않는다', async () => {
    const dead: SearchSource = {
      search: async () => {
        throw new SearchUnavailable('닿지 않았다');
      },
    };
    renderResults(dead);
    const down = await screen.findByTestId('search-unavailable');
    expect(down.textContent).toContain('검색이 지금 동작하지 않아요');
    expect(screen.queryByTestId('search-loading')).toBeNull();
    fireEvent.click(within(down).getByRole('link', { name: /카탈로그/ }));
    await waitFor(() => expect(screen.getByText('데이터셋 카탈로그 화면')).toBeTruthy());
  });

  it('닿지 않았을 때 가짜 결과를 지어내지 않는다', async () => {
    const dead: SearchSource = {
      search: async () => {
        throw new SearchUnavailable('닿지 않았다');
      },
    };
    renderResults(dead);
    await screen.findByTestId('search-unavailable');
    expect(screen.queryAllByTestId('search-hit')).toHaveLength(0);
  });
});
