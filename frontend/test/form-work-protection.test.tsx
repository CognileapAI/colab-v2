import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ProjectFormModal } from '../src/components/project/ProjectFormModal';
import { SessionProvider } from '../src/permission/session';
import type { CurrentAccount } from '../src/api/client';
import {
  canTransition,
  discardAccountWork,
  resetWorkGuardForTests,
  setCurrentAccountId,
} from '../src/auth/workGuard';

describe('비업로드 폼 작업 보호', () => {
  beforeEach(() => {
    resetWorkGuardForTests();
    setCurrentAccountId('account-a');
  });

  afterEach(() => resetWorkGuardForTests());

  it('프로젝트 폼은 실제 변경만 전환을 막고 명시 폐기하면 React 상태를 닫는다', async () => {
    const onClose = vi.fn();
    render(
      <SessionProvider account={{ accountId: 'account-a' } as CurrentAccount}>
        <ProjectFormModal
          mode={{ kind: '새 프로젝트' }}
          onSubmit={vi.fn()}
          onClose={onClose}
        />
      </SessionProvider>,
    );

    expect(canTransition()).toBe(true);
    fireEvent.change(screen.getByLabelText('이름'), { target: { value: '새 과제' } });
    expect(canTransition()).toBe(false);

    await discardAccountWork('account-a');
    expect(onClose).toHaveBeenCalledTimes(1);
    expect(canTransition()).toBe(true);
  });
});
