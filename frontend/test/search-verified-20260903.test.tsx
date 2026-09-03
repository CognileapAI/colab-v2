/**
 * S-06 검색 결과 — **결과 헤드 · `Verified만 보기` 토글 · Verified 카드** (`PLAN-SoT §9 〈295〉`).
 *
 * 오라클 = 정본 `Policy_데이터_찾기.md` v2.0 축자
 *   · `§8 결과 헤드` 「찾은 건수("4건을 찾았어요." 형태)와 정렬 기준("Verified 우선 · 관련도 순")을
 *     한 줄에. 검색에는 정렬 선택 상자를 두지 않는다」
 *   · `§8 Verified만 보기` 「켜면 승인 결과만, 건수 갱신. **검색 전용이다.**」
 *   · `§8 Verified 카드` 「좌측 초록 룰 + 배지 + "교수 승인이라 위로 올렸어요" 문장」
 *   · 목업 `E-02 데이터_찾기_260817.html` `F-01` 383~395행
 *
 * 화면 검수 2026-09-03 #10(카드 Verified 미표시) · #11(정렬 근거 줄 없음) · #15(토글 없음)이
 * 가리킨 자리이고, `〈224〉`-㉯ 가 「Verified 우선 정렬 실행 경로 0건」으로 열어 둔 항목이다.
 *
 * ⚠ **정렬 자체는 이 파일이 오라클로 들지 않는다** — 순서는 서버 조립 루트(`routes/catalog.py`)가
 * `verified` 를 읽어야 서고, 그 파일은 이 회차의 범위 밖이다. 화면은 서버가 준 순서를
 * 다시 매기지 않는다(종전 성질 유지).
 *
 * ⭑ **2026-09-03 (`〈298〉` · 16차) — 그 자리가 착지했다.** 정렬은
 * `services/core-api/tests/test_search_verified_16.py` 가, 서버 걸름과 카드의 `요약`·`기간` 은
 * `test/search-contract-16.test.tsx` 가 진다. 이 파일은 `〈295〉` 의 오라클 셋을 그대로 지킨다.
 */
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { SearchResultsPage } from '../src/routes/SearchResultsPage';
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
    // ⭑ **⟨16차 해제 · `〈298〉`⟩ 두 칸이 늘었다** — `〈295〉`-㉰ 가 「계약에 칸이 없다」로
    // 멈춰 둔 자리다. 이 파일의 오라클(정렬 근거 줄 · 토글 · 배지)은 그대로다.
    summary: '한강 유역 지점 강수 관측 원자료',
    period: { start: '2025-06-01T00:00:00Z', end: '2025-09-30T00:00:00Z' },
    relevanceBar: 1,
    rationale: '수자원순환연구실 안 128건에서 ‘강수’가 이름에 맞았어요 — 기간·지역·품질은 이 검색이 확인하지 못했으니 카드의 값으로 직접 봐 주세요.',
    ...over,
  };
}

const APPROVED = hit({ datasetId: '01JYZ9K7WQ3N8V4M2X6C5B0A02', name: '낙동강 강우 (2025)', verified: true });
const PLAIN = hit({ datasetId: '01JYZ9K7WQ3N8V4M2X6C5B0A03', name: 'ERA5 강수 재분석', verified: false });

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

function renderResults(items: SearchResultRow[]) {
  // ⭑ **⟨16차 해제 · `〈298〉`⟩ 걸름이 서버로 갔다** — 그래서 이 흉내 서버가 `verified` 를
  // 실제로 읽는다. 종전에는 화면이 걸렀으므로 요청을 안 읽어도 시험이 섰다(`〈295〉`).
  // **값을 지우지 않고 시점을 붙인다** — 아래 오라클(건수 갱신·토글 상태)은 그대로다.
  const source: SearchSource = {
    search: async (request) =>
      results(request.verified ? items.filter((i) => i.verified) : items),
  };
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

// ── #11 결과 헤드 ───────────────────────────────────────────────────────────
describe('#11 결과 헤드 — 건수와 정렬 기준이 한 줄에 선다', () => {
  it('「N건을 찾았어요.」와 「Verified 우선 · 관련도 순」이 같은 줄에 있다', async () => {
    renderResults([APPROVED, PLAIN]);
    const head = await screen.findByTestId('search-result-head');
    expect(head.textContent).toContain('2건');
    expect(head.textContent).toContain('찾았어요');
    expect(head.textContent).toContain('Verified 우선 · 관련도 순');
  });

  it('검색에는 정렬 선택 상자를 두지 않는다 (순서를 고르는 조작은 카탈로그에만)', async () => {
    const { container } = renderResults([APPROVED, PLAIN]);
    await screen.findByTestId('search-result-head');
    expect(container.querySelector('select')).toBeNull();
  });

  it('범위 표시줄은 뒤진 범위만 말한다 — 건수는 결과 헤드가 진다', async () => {
    renderResults([APPROVED, PLAIN]);
    const scope = await screen.findByTestId('search-scope');
    expect(scope.textContent).toContain('128건');
    expect(scope.textContent).not.toContain('찾았어요');
  });
});

// ── #15 Verified만 보기 토글 ────────────────────────────────────────────────
describe('#15 Verified만 보기 — 검색 전용 토글', () => {
  it('토글이 결과 헤드에 선다', async () => {
    renderResults([APPROVED, PLAIN]);
    const head = await screen.findByTestId('search-result-head');
    const toggle = within(head).getByTestId('verified-only');
    expect(toggle.textContent).toContain('Verified만 보기');
    expect(toggle).toHaveAttribute('aria-pressed', 'false');
  });

  it('켜면 승인된 결과만 남고 건수가 갱신된다', async () => {
    renderResults([APPROVED, PLAIN]);
    const toggle = await screen.findByTestId('verified-only');
    fireEvent.click(toggle);
    await waitFor(() => expect(screen.getAllByTestId('search-hit')).toHaveLength(1));
    expect(screen.getByTestId('verified-only')).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByTestId('search-result-head').textContent).toContain('1건');
    expect(screen.getByTestId('search-results').textContent).toContain('낙동강 강우 (2025)');
    expect(screen.getByTestId('search-results').textContent).not.toContain('ERA5 강수 재분석');
  });

  it('다시 끄면 전체 결과가 돌아온다', async () => {
    renderResults([APPROVED, PLAIN]);
    const toggle = await screen.findByTestId('verified-only');
    fireEvent.click(toggle);
    await waitFor(() => expect(screen.getAllByTestId('search-hit')).toHaveLength(1));
    fireEvent.click(screen.getByTestId('verified-only'));
    await waitFor(() => expect(screen.getAllByTestId('search-hit')).toHaveLength(2));
    expect(screen.getByTestId('search-result-head').textContent).toContain('2건');
  });

  it('0건 상태에는 토글도 결과 헤드도 두지 않는다 — 켜고 끌 것이 없다', async () => {
    renderResults([]);
    await screen.findByTestId('search-empty');
    expect(screen.queryByTestId('search-result-head')).toBeNull();
    expect(screen.queryByTestId('verified-only')).toBeNull();
  });
});

// ── #10 카드의 Verified 표시 ────────────────────────────────────────────────
describe('#10 Verified 카드 — 배지와 정렬 이유 문장', () => {
  it('승인된 카드에 배지와 「교수 승인이라 위로 올렸어요」가 붙는다', async () => {
    renderResults([APPROVED]);
    const card = await screen.findByTestId('search-hit');
    expect(within(card).getByTestId('hit-verified').textContent).toContain('Verified');
    expect(card.textContent).toContain('교수 승인이라 위로 올렸어요');
    expect(card.className).toContain('is-verified');
  });

  it('미승인 카드에는 배지도 문장도 두지 않는다 — 카탈로그의 취소선 표기를 카드로 옮기지 않는다', async () => {
    renderResults([PLAIN]);
    const card = await screen.findByTestId('search-hit');
    expect(within(card).queryByTestId('hit-verified')).toBeNull();
    expect(card.textContent).not.toContain('교수 승인이라 위로 올렸어요');
    expect(card.querySelector('.verified--pending')).toBeNull();
  });
});
