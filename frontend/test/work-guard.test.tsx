import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  canTransition,
  discardAccountWork,
  registerWork,
  resetWorkGuardForTests,
  beginTransition,
} from '../src/auth/workGuard';

beforeEach(() => resetWorkGuardForTests());

describe('work guard', () => {
  it('blocks transitions until dirty work is released', () => {
    const release = registerWork('project', {
      accountId: 'A',
      dirty: true,
      inFlight: false,
    });
    expect(canTransition()).toBe(false);
    release();
    expect(canTransition()).toBe(true);
  });

  it('aborts and discards every registered item for an account', async () => {
    const discard = vi.fn();
    const abort = vi.fn();
    registerWork('upload', {
      accountId: 'A',
      dirty: true,
      inFlight: true,
      discard,
      abort,
    });
    await discardAccountWork('A');
    expect(abort).toHaveBeenCalledOnce();
    expect(discard).toHaveBeenCalledOnce();
    expect(canTransition()).toBe(true);
  });

  it('records work that appears during a transition so it cannot be silently lost', () => {
    const finish = beginTransition();
    expect(() => registerWork('late', {
      accountId: 'A', dirty: true, inFlight: false,
    })).not.toThrow();
    expect(canTransition()).toBe(false);
    finish();
  });
});
