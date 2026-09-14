/**
 * 검색 범위 줄 — **응답이 말한 범위를 그대로 말한다** (`R-LTH-REVIEW-1` Task 2 · spec §8-2 25).
 *
 * 이 회차의 변경은 서버 쪽(`services/core-api/.../routes/catalog.py`)이다 — 분모
 * (`searchedCount`)를 결과와 같은 유효 스코프에서 세고, `labName` 이 유효 연구실 집합을
 * 말한다. 화면은 그 두 값을 **가공하지 않고** 그대로 읽어야 하므로 이 파일은 **회귀 오라클**이다:
 * 화면이 소속 연구실 이름을 따로 조립하거나 건수를 다시 세면 서버의 정합이 화면에서 다시 깨진다.
 *
 * ⚠ **green 으로 시작하는 시험이다**(화면 구현 변경 0건). 서버 정합을 화면이 되돌리지
 * 못하게 고정하는 자리이고, 판정 red 는 `services/core-api/tests/test_search_scope.py` 가 냈다.
 */
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { SearchResultsPage } from '../src/routes/SearchResultsPage';
import type { SearchResultRow, SearchResults, SearchSource } from '../src/components/search/types';

const LAB_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AHU';

/** 운영자 범위 표기 — 상단 셸 칩(`Gnb.tsx`)·서버 상수(`OPERATOR_SCOPE_LABEL`)와 같은 말. */
const OPERATOR_SCOPE_LABEL = '전체 연구실 (읽기 전용)';

function hit(): SearchResultRow {
  return {
    mapState: '아직 모름',
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
    summary: '한강 유역 지점 강수 관측 원자료',
    period: null,
    relevanceBar: 1,
    rationale: '전체 연구실 (읽기 전용) 안 26건에서 ‘강수’가 이름에 맞았어요',
  };
}

function results(over: Partial<SearchResults> = {}): SearchResults {
  return {
    scope: { labId: LAB_ID, labName: '수자원순환연구실', searchedCount: 25 },
    isDataQuery: true,
    degraded: false,
    items: [hit()],
    totalCount: 1,
    nextCursor: null,
    ...over,
  };
}

function renderResults(body: SearchResults, q = '강수 데이터 있어?') {
  const source: SearchSource = { search: async () => body };
  return render(
    <MemoryRouter initialEntries={[`/datasets/search?q=${encodeURIComponent(q)}`]}>
      <Routes>
        <Route path="/datasets/search" element={<SearchResultsPage source={source} />} />
        <Route path="/datasets" element={<div>데이터셋 카탈로그 화면</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('검색 범위 줄은 응답의 범위를 그대로 말한다', () => {
  it('운영자 응답의 전체 연구실 표기와 건수를 그대로 말한다', async () => {
    renderResults(results({
      scope: { labId: LAB_ID, labName: OPERATOR_SCOPE_LABEL, searchedCount: 26 },
    }));
    const scope = await screen.findByTestId('search-scope');
    expect(scope.textContent).toContain(OPERATOR_SCOPE_LABEL);
    expect(scope.textContent).toContain('26건');
    // 화면이 소속 연구실 이름을 따로 조립하지 않는다.
    expect(scope.textContent).not.toContain('수자원순환연구실');
  });

  it('일반 구성원 응답의 소속 연구실 이름과 건수를 그대로 말한다', async () => {
    renderResults(results());
    const scope = await screen.findByTestId('search-scope');
    expect(scope.textContent).toContain('수자원순환연구실');
    expect(scope.textContent).toContain('25건');
    expect(scope.textContent).not.toContain(OPERATOR_SCOPE_LABEL);
  });

  it('0건에도 범위 줄이 먼저 서고 같은 두 값을 말한다', async () => {
    const { container } = renderResults(results({
      scope: { labId: LAB_ID, labName: OPERATOR_SCOPE_LABEL, searchedCount: 26 },
      items: [],
      totalCount: 0,
    }));
    const scope = await screen.findByTestId('search-scope');
    expect(scope.textContent).toContain(OPERATOR_SCOPE_LABEL);
    expect(scope.textContent).toContain('26건');
    // 0건 안내도 같은 범위·개수를 말한다 — 한 화면이 두 수를 말하지 않는다.
    const empty = await screen.findByTestId('search-empty');
    expect(empty.textContent).toContain(OPERATOR_SCOPE_LABEL);
    expect(empty.textContent).toContain('26');
    // 범위 줄이 0건 안내보다 먼저다.
    const notice = container.querySelector('[data-testid="search-empty"]')!;
    expect(scope.compareDocumentPosition(notice) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });
});
