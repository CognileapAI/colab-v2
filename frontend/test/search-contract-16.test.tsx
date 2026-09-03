/**
 * S-06 검색 결과 — **`Verified만 보기` 서버 걸름 · 카드의 `요약`·`기간`** (`PLAN-SoT §9 〈298〉`).
 *
 * `〈295〉` 가 화면 레인에서 멈춘 셋 중 **둘이 화면 쪽 절반**이다 —
 *   · 토글이 「한 쪽(`limit` 기본 20) 안에서만」 걸렀다(`〈295〉`-㉲-ⓑ 의 ⚠ 한계).
 *     16차가 `SearchQuery.verified` 를 열었으므로 **걸름은 서버가 진다.**
 *   · 카드에 `요약`·`기간` 을 못 그렸다 — 「계약에 칸이 없다」(`〈295〉`-㉰).
 *     16차가 `SearchResultRow` 두 번째 객체에 두 칸을 더했다.
 *
 * 오라클 = 정본 `Policy_데이터_찾기.md` v2.1
 *   · `:120` 「결과 카드 구성 = 파일명 · 포맷 · Lv · Verified · 관련도 막대 · **요약** ·
 *     AI 근거 · **기간** · 원천 · 소유」
 *   · `:150` 「Verified만 보기 … 켜면 승인 결과만, 건수 갱신. 검색 전용이다」
 *   · `:151` 「잠긴 결과 카드 … **기간·원천·소유 메타 줄은 두지 않는다**」
 *   · `〈283〉`(14차) 「끝이 없으면 무기한」 — 열린 기간 문면은 `detail/format.ts` 를 재사용한다.
 */
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { SearchResultsPage } from '../src/routes/SearchResultsPage';
import type {
  SearchRequest,
  SearchResultRow,
  SearchResults,
  SearchSource,
} from '../src/components/search/types';

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
    relevanceBar: 1,
    rationale: '‘강수’가 이름에 맞았어요 — 기간·지역·품질은 이 검색이 확인하지 못했어요.',
    summary: '한강 유역 지점 강수 관측 원자료',
    period: { start: '2025-06-01T00:00:00Z', end: '2025-09-30T00:00:00Z' },
    ...over,
  };
}

function results(items: SearchResultRow[]): SearchResults {
  return {
    scope: { labId: LAB_ID, labName: '수자원순환연구실', searchedCount: 128 },
    isDataQuery: true,
    degraded: false,
    items,
    totalCount: items.length,
    nextCursor: null,
  };
}

/** 서버를 흉내 낸다 — **`verified` 를 실제로 읽어서 거른다.** 안 읽으면 시험이 「보냈다」만
 *  재고 「걸러졌다」는 못 재서, 서버 걸름과 화면 걸름을 구분하지 못한다. */
function recordingSource(items: SearchResultRow[]) {
  const seen: SearchRequest[] = [];
  const source: SearchSource = {
    async search(request) {
      seen.push(request);
      return results(request.verified ? items.filter((i) => i.verified) : items);
    },
  };
  return { seen, source };
}

function renderWith(source: SearchSource) {
  return render(
    <MemoryRouter initialEntries={['/datasets/search?q=%EA%B0%95%EC%88%98']}>
      <Routes>
        <Route path="/datasets/search" element={<SearchResultsPage source={source} />} />
        <Route path="/datasets" element={<div>데이터셋 카탈로그 화면</div>} />
        <Route path="/datasets/:datasetId" element={<div>데이터셋 상세 화면</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

const APPROVED = hit({ datasetId: '01JYZ9K7WQ3N8V4M2X6C5B0A02', name: '낙동강 강우 (2025)', verified: true });
const PLAIN = hit({ datasetId: '01JYZ9K7WQ3N8V4M2X6C5B0A03', name: 'ERA5 강수 재분석', verified: false });

// ── 토글이 서버에 간다 ──────────────────────────────────────────────────────
describe('Verified만 보기 — 걸름은 서버가 진다', () => {
  it('첫 질의에는 `verified` 를 싣지 않는다 — 생략이 「거르지 않는다」다', async () => {
    const { seen, source } = recordingSource([APPROVED, PLAIN]);
    renderWith(source);
    await screen.findByTestId('search-result-head');
    expect(seen).toHaveLength(1);
    expect(seen[0]?.verified).toBeFalsy();
  });

  it('토글을 켜면 `verified: true` 로 다시 묻는다', async () => {
    const { seen, source } = recordingSource([APPROVED, PLAIN]);
    renderWith(source);
    fireEvent.click(await screen.findByTestId('verified-only'));
    await waitFor(() => expect(seen).toHaveLength(2));
    expect(seen[1]?.verified).toBe(true);
    await waitFor(() => expect(screen.getAllByTestId('search-hit')).toHaveLength(1));
    expect(screen.getByTestId('search-result-head').textContent).toContain('1건');
  });

  it('화면이 받은 쪽을 다시 거르지 않는다 — 서버가 준 행은 그대로 선다', async () => {
    /* 걸름이 화면에 남아 있으면 이 요청은 0건으로 그려진다. 서버 걸름이면 2건 그대로다.
       (실서버는 이런 응답을 내지 않는다 — **어느 쪽이 거르는가**를 가르는 시험이다.) */
    const source: SearchSource = { search: async () => results([APPROVED, PLAIN]) };
    renderWith(source);
    fireEvent.click(await screen.findByTestId('verified-only'));
    await waitFor(() =>
      expect(screen.getByTestId('verified-only')).toHaveAttribute('aria-pressed', 'true'),
    );
    expect(screen.getAllByTestId('search-hit')).toHaveLength(2);
  });

  it('서버가 준 순서를 화면이 다시 매기지 않는다 — Verified 우선은 서버의 일이다', async () => {
    const { source } = recordingSource([APPROVED, PLAIN]);
    renderWith(source);
    await screen.findByTestId('search-results');
    const names = screen.getAllByTestId('hit-name').map((n) => n.textContent);
    expect(names).toEqual(['낙동강 강우 (2025)', 'ERA5 강수 재분석']);
  });
});

// ── 카드의 `요약`·`기간` ────────────────────────────────────────────────────
describe('결과 카드 — 요약과 기간 (`Policy §8` :120)', () => {
  it('요약을 그린다', async () => {
    renderWith({ search: async () => results([hit()]) });
    const card = await screen.findByTestId('search-hit');
    expect(within(card).getByTestId('hit-summary').textContent).toBe('한강 유역 지점 강수 관측 원자료');
  });

  it('요약이 비면 빈 표시다 — 없는 문장을 지어내지 않는다', async () => {
    renderWith({ search: async () => results([hit({ summary: null })]) });
    const card = await screen.findByTestId('search-hit');
    expect(within(card).getByTestId('hit-summary').textContent).toBe('—');
  });

  it('기간을 그린다 — 해가 같으면 뒤쪽 해를 다시 적지 않는다', async () => {
    renderWith({ search: async () => results([hit()]) });
    const card = await screen.findByTestId('search-hit');
    expect(within(card).getByTestId('hit-period').textContent).toBe('2025-06 ~ 09');
  });

  it('끝이 없는 기간은 무기한으로 읽힌다 (`〈283〉` · 상세와 같은 문면)', async () => {
    renderWith({
      search: async () => results([hit({ period: { start: '2024-01-01T00:00:00Z', end: null } })]),
    });
    const card = await screen.findByTestId('search-hit');
    expect(within(card).getByTestId('hit-period').textContent).toBe('2024-01 ~ 진행 중');
  });

  it('기간이 없으면 빈 표시다', async () => {
    renderWith({ search: async () => results([hit({ period: null })]) });
    const card = await screen.findByTestId('search-hit');
    expect(within(card).getByTestId('hit-period').textContent).toBe('—');
  });

  it('잠긴 카드에는 기간을 두지 않는다 — 요약은 그대로 선다 (`P-13`)', async () => {
    renderWith({
      search: async () =>
        results([hit({ bodyAccessible: false, accessState: '잠김', summary: '잠긴 데이터의 요약' })]),
    });
    const card = await screen.findByTestId('search-hit');
    expect(within(card).queryByTestId('hit-period')).toBeNull();
    expect(within(card).getByTestId('hit-summary').textContent).toBe('잠긴 데이터의 요약');
  });
});
