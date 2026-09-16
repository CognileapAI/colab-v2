import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import { DatasetPreviewSection } from '../src/components/datasetpreview/DatasetPreviewSection';
import type { DatasetPreviewSource } from '../src/components/datasetpreview/types';
import { SessionProvider } from '../src/permission/session';
import { account } from './factories';

const palettes = [{ palette: 'server-a', label: '서버 A' }, { palette: 'server-b', label: '서버 B' }, { palette: 'server-c', label: '서버 C' }];
function source(): DatasetPreviewSource {
  const job = { renderId: 'R1', status: '실패' as const, failure: { code: 'NO_DATA', message: '그릴 자료 없음' } };
  return {
    palettes: async () => palettes,
    files: async () => [{ fileId: 'F1', fileName: 'fixture.nc', renderable: true }],
    describe: async () => ({ variables: ['fixture'], instants: null, default: { variable: 'fixture', instant: null } }),
    create: vi.fn(async () => job), get: async () => job,
    probeTile: async () => 'ok', mapGeometry: async () => undefined,
    screenshot: async () => new Blob(), lookupValue: async () => { throw new Error('unused'); },
  };
}

it('편집자는 서버 팔레트 3종과 3~9 구간의 모든 21조합으로 다시 그릴 수 있다', async () => {
  const data = source();
  render(<SessionProvider account={account({ '업로드·편집': true })}><DatasetPreviewSection datasetId="D1" source={data} /></SessionProvider>);
  const palette = await screen.findByLabelText('팔레트');
  const count = screen.getByLabelText('구간 수');
  expect(Array.from((palette as HTMLSelectElement).options).map(option => option.text)).toEqual(palettes.map(p => p.label));
  for (const p of palettes) {
    await act(async () => { fireEvent.change(palette, { target: { value: p.palette } }); });
    for (const n of [3, 4, 5, 6, 7, 8, 9]) {
      await act(async () => { fireEvent.change(count, { target: { value: String(n) } }); });
      await act(async () => { fireEvent.click(screen.getByTestId('dt-preview-draw')); });
      await waitFor(() => expect(data.create).toHaveBeenLastCalledWith(expect.objectContaining({ palette: p.palette, classCount: n })));
    }
  }
});

it('보기 전용에는 팔레트·구간 수 조작이 없다', async () => {
  const data = source();
  render(<SessionProvider account={account()}><DatasetPreviewSection datasetId="D1" source={data} /></SessionProvider>);
  const draw = await screen.findByTestId('dt-preview-draw');
  await waitFor(() => expect((draw as HTMLButtonElement).disabled).toBe(false));
  fireEvent.click(draw);
  await waitFor(() => expect(data.create).toHaveBeenCalledTimes(1));
  expect(screen.queryByLabelText('팔레트')).toBeNull();
  expect(screen.queryByLabelText('구간 수')).toBeNull();
});
