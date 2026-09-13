import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { SearchResultsPage } from '../src/routes/SearchResultsPage';
import type { SearchAssessment, SearchResults } from '../src/components/search/types';

describe('client research search', () => {
  it('asks for context without claiming no data and resubmits explicit research conditions', async () => {
    const assessment:SearchAssessment = { status:'clarification',text:'연구 조건을 확인해 주세요.',questions:['현재 연구 정보가 없습니다.'],intent:'recommend',conditions:{variable:'land_surface_temperature'},asOf:'2026-09-13T12:00:00+09:00',semanticVersion:'a'.repeat(64),scope:'등록 자료',candidateLimitReached:false,comparisons:[],unknownCount:0 };
    const result:SearchResults = { scope:{labId:'L',labName:'연구실',searchedCount:10},isDataQuery:true,degraded:false,items:[],totalCount:0,nextCursor:null,assessment };
    const search=vi.fn().mockResolvedValue(result);
    render(<MemoryRouter initialEntries={['/search?q=지표면온도추천']}><SearchResultsPage source={{search}} /></MemoryRouter>);
    await screen.findByText('먼저 확인할 내용이 있어요');
    expect(screen.queryByTestId('search-empty')).toBeNull();
    expect(screen.queryByTestId('search-scope')).toBeNull();
    fireEvent.click(screen.getByText('연구 조건 입력·변경'));
    fireEvent.change(screen.getByLabelText('관측 변수'),{target:{value:'land_surface_temperature'}});
    fireEvent.change(screen.getByLabelText('지역'),{target:{value:'seoul'}});
    fireEvent.change(screen.getByLabelText('시작일'),{target:{value:'2025-01-01'}});
    fireEvent.change(screen.getByLabelText('종료일'),{target:{value:'2025-12-31'}});
    fireEvent.click(screen.getByText('이 연구 조건으로 다시 찾기'));
    await waitFor(() => expect(search).toHaveBeenLastCalledWith(expect.objectContaining({context:{research:{variable:'land_surface_temperature',region:'seoul',period:{start:'2025-01-01',end:'2025-12-31'}}}})));
  });
});
