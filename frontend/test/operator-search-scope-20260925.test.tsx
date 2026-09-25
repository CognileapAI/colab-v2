/**
 * 운영자 검색 범위 — 전 연구실 결과 카드에 **소속 연구실 이름**이 붙는다.
 *
 * intent `dev-package/intent/2026-09-25-operator-search-scope.md` §설계트리 Q2·Q6 (이슈 #158).
 *   · 운영자 응답의 `scope` 는 `AiOperatorSearchScope`(`operatorScope: true` · `labId` 없음)다.
 *     범위 줄은 그 값을 그대로 말한다 — 「전체 연구실 데이터 N건을 뒤졌어요」.
 *   · 운영자 응답의 카드에는 `labName` 이 실리고, 화면은 그것을 카드마다 그린다.
 *   · 비운영자 응답에는 `labName` 이 없고, 카드에 연구실 표시가 서지 않는다(종전 화면 그대로).
 */
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { SearchResultsPage } from '../src/routes/SearchResultsPage';
import type { SearchResultRow, SearchResults, SearchSource } from '../src/components/search/types';

const OPERATOR_SCOPE_LABEL = '전체 연구실';

function hit(over: Partial<SearchResultRow>): SearchResultRow {
  return {
    mapState: '아직 모름',
    datasetId: '01JYZ9K7WQ3N8V4M2X6C5B0A01',
    name: '강우 원자료',
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
    summary: '관측 원자료',
    period: null,
    relevanceBar: 1,
    rationale: '전체 연구실 안 2건에서 ‘원자료’가 이름에 맞았어요',
    ...over,
  };
}

function renderResults(body: SearchResults) {
  const source: SearchSource = { search: async () => body };
  return render(
    <MemoryRouter initialEntries={[`/datasets/search?q=${encodeURIComponent('원자료')}`]}>
      <Routes>
        <Route path="/datasets/search" element={<SearchResultsPage source={source} />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('운영자 검색 결과는 카드마다 소속 연구실을 밝힌다', () => {
  it('운영자 범위 응답 — 범위 줄은 전체 연구실, 카드마다 연구실 이름', async () => {
    renderResults({
      scope: { operatorScope: true, labName: OPERATOR_SCOPE_LABEL, searchedCount: 4 },
      isDataQuery: true,
      degraded: false,
      items: [
        hit({ datasetId: '01JYZ9K7WQ3N8V4M2X6C5B0A01', labName: '수자원순환연구실' }),
        hit({ datasetId: '01JYZ9K7WQ3N8V4M2X6C5B0A02', labName: '대기환경연구실' }),
      ],
      totalCount: 2,
      nextCursor: null,
    });
    const scope = await screen.findByTestId('search-scope');
    expect(scope.textContent).toContain(`${OPERATOR_SCOPE_LABEL} 데이터 4건을 뒤졌어요`);
    const labs = await screen.findAllByTestId('hit-lab');
    expect(labs.map(el => el.textContent)).toEqual(['수자원순환연구실', '대기환경연구실']);
  });

  it('비운영자 응답 — 카드에 연구실 표시가 없다', async () => {
    renderResults({
      scope: { labId: '01JYZ9K7WQ3N8V4M2X6C5B0AHU', labName: '수자원순환연구실', searchedCount: 2 },
      isDataQuery: true,
      degraded: false,
      items: [hit({})],
      totalCount: 1,
      nextCursor: null,
    });
    await screen.findAllByTestId('search-hit');
    expect(screen.queryByTestId('hit-lab')).toBeNull();
  });
});
