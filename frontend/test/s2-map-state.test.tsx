import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { expect, it, vi } from 'vitest';
import { DatasetsPage } from '../src/routes/DatasetsPage';
import { FIXTURE_ROWS } from '../src/components/catalog/fixture';
import { queryParams } from '../src/components/catalog/catalogSource';
import { DEFAULT_SORT, type CatalogQuery } from '../src/components/catalog/types';

it('지도 상태를 이름 옆에 표시하고 선택한 상태를 서버 필터로 전달한다', async () => {
  const rows = [
    { ...FIXTURE_ROWS[0]!, mapState: '지도 없음' as const },
    { ...FIXTURE_ROWS[1]!, mapState: '아직 모름' as const },
    { ...FIXTURE_ROWS[2]!, mapState: '지도 있음' as const },
  ];
  const list = vi.fn(async (_query: CatalogQuery) => ({ items: rows, totalCount: 3 }));
  render(<MemoryRouter><DatasetsPage source={{ list, facets: async () => ({ columns: [] }) }} /></MemoryRouter>);
  await screen.findByText(rows[0]!.name);
  const cells = screen.getAllByRole('row').slice(1).map(row => within(row).getAllByRole('cell')[0]!);
  expect(cells[0]).toHaveTextContent('지도 없음');
  expect(cells[1]).toHaveTextContent('아직 모름');
  expect(cells[2]).not.toHaveTextContent('지도 있음');
  fireEvent.change(screen.getByLabelText('지도 상태'), { target: { value: '지도 없음' } });
  await waitFor(() => expect(list.mock.calls.at(-1)?.[0].mapState).toBe('지도 없음'));
  expect(queryParams(list.mock.calls.at(-1)![0])).toMatchObject({ mapState: '지도 없음' });
  expect(queryParams({ sort: DEFAULT_SORT, axes: {}, filters: {} })).not.toHaveProperty('mapState');
});
