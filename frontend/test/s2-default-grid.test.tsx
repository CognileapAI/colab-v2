import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import { DefaultGridButton } from '../src/components/detail/DefaultGridButton';
import { SessionProvider } from '../src/permission/session';
import { account } from './factories';

it('교수의 명시적 지정만 저장하며 성공과 실패를 화면에 알린다', async () => {
  const save = vi.fn().mockRejectedValueOnce(new Error('격자 프로필이 없어요')).mockResolvedValueOnce(undefined);
  render(<SessionProvider account={{ ...account(), role: '교수' }}><DefaultGridButton datasetId="D1" save={save} /></SessionProvider>);
  expect(save).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: '연구실 기본 격자로 지정' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('격자 프로필이 없어요');
  fireEvent.click(screen.getByRole('button', { name: '연구실 기본 격자로 지정' }));
  await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('연구실 기본 격자로 지정했어요'));
  expect(save).toHaveBeenLastCalledWith('D1');
});

it('연구실 설정을 위임받아도 연구원에게 기본 격자 지정 조작은 없다', () => {
  const save = vi.fn();
  render(<SessionProvider account={account({ '연구실 설정': true })}><DefaultGridButton datasetId="D1" save={save} /></SessionProvider>);
  expect(screen.queryByRole('button')).toBeNull();
});
