/**
 * design-fix 20260924 · 통합 레인 F-int — Fable advisor ② 지적 두 건의 동작 시험.
 *
 * 오라클 = `dev-package/prd/specs/S-DESIGN-FIX-20260924.md` 「확정 값」 2(닫는 도중 다시 열면 입력을 둔 채
 *          돌아온다) ＋ PRD-13(완전히 닫힌 모달은 ① 에서 다시 연다).
 *
 * 1. 등록·반영 성공 뒤 닫기 — 값 2 의 되살리기는 **사람이 닫은 미완 세션**에만 적용된다. 등록(또는 격자 반영)이
 *    확정된 뒤의 닫기는 완료된 닫기이므로, 닫기 전환(0.3s 스텁) 사이에 진입 단추를 눌러도 끝난 모달이 아니라
 *    **새 모달(① 파일 고르기)** 이 선다. `UploadEntry` · `GridAttachEntry` 두 부모 모두.
 * 2. `setPointerCapture` 가 던져도(예: 이미 끝난 포인터의 NotFoundError) 누름 처리기가 끊기지 않고,
 *    끌기 상태가 남아 뒤이은 포인터를 막지 않는다.
 *
 * 전환 시간 스텁은 선례 `design-fix-20260924-F-upload.test.tsx` 와 같은 방식(모달 요소에 한해 getComputedStyle 덮기).
 */
import { act, fireEvent, render, renderHook, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, useLocation } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { SessionProvider } from '../src/permission/session';
import { GridAttachEntry } from '../src/components/upload/GridAttachEntry';
import { UploadEntry } from '../src/components/upload/UploadEntry';
import { DEFAULT_CATEGORY, DEFAULT_DATA_TYPE } from '../src/components/upload/axisDict';
import { useZoomPan } from '../src/components/preview/useZoomPan';
import type {
  PreviewSource,
  ProjectSource,
  UploadSource,
  UploadSources,
} from '../src/components/upload/types';
import type { LineageSource, LineageSuggestionResponse } from '../src/components/lineage/types';
import type { CurrentAccount, Schemas } from '../src/api/client';

// ─── 고정물 ───────────────────────────────────────────────────────────────────

const UPLOAD_ID = '01JYZ9K7WQ3N8V4M2X6C5B0UP1';
const FILE_ID = '01JYZ9K7WQ3N8V4M2X6C5B0FI1';
const DATASET_ID = '01JYZ9K7WQ3N8V4M2X6C5B0DS1';

function account(): CurrentAccount {
  return {
    accountId: '01JYZ9K7WQ3N8V4M2X6C5B0AC1',
    name: '호랑이',
    email: 'tiger@example.ac.kr',
    role: '연구원',
    labId: '01JYZ9K7WQ3N8V4M2X6C5B0LB1',
    labName: '수자원순환연구실',
    permissions: {
      '업로드·편집': true,
      '프로젝트 생성': true,
      '승인 위임': false,
      '연구실 설정': false,
    } as Record<Schemas['PermissionSwitch'], boolean>,
  } as unknown as CurrentAccount;
}

function fakes() {
  const calls = { registered: 0, attached: 0 };
  const file = {
    fileId: FILE_ID,
    fileName: 'nakdong_precip_2025_Lv2.nc',
    kind: '본체',
    byteSize: 349_000,
    createdAt: '2026-09-07T00:00:00Z',
  };
  const upload = {
    async create() {
      return { uploadId: UPLOAD_ID, files: [file] } as never;
    },
    async status() {
      return { uploadId: UPLOAD_ID, ready: true, failure: null, metadataComplete: true, files: [file] } as never;
    },
    async register() {
      calls.registered += 1;
      return { datasetId: DATASET_ID } as never;
    },
    async attachGrid() {
      calls.attached += 1;
      return [] as never;
    },
  } as unknown as UploadSource;
  const preview = {
    async palettes() {
      return [{ palette: 'viridis', label: '비리디스' }];
    },
    async createRender() {
      return { renderId: 'r', state: '실패', failure: null } as never;
    },
    async getRender() {
      return { renderId: 'r', state: '실패', failure: null } as never;
    },
  } as unknown as PreviewSource;
  const projects = {
    async list() {
      return [];
    },
    async create() {
      return { projectId: '01JYZ9K7WQ3N8V4M2X6C5B0PR9', name: 'x', type: '국가과제' } as never;
    },
  } as unknown as ProjectSource;
  const lineage = {
    async suggestions() {
      return {
        degraded: false,
        scope: { labId: 'l', labName: '수자원순환연구실', searchedCount: 0 },
        rawDataLikely: false,
        suggestions: [],
      } as unknown as LineageSuggestionResponse;
    },
    async candidates() {
      return [];
    },
  } as unknown as LineageSource;
  return { calls, sources: { upload, preview, projects, lineage } as UploadSources };
}

async function flush() {
  await act(async () => {});
}
async function click(el: Element | null) {
  fireEvent.click(el as HTMLElement);
  await flush();
}
async function change(el: Element | null, value: string) {
  fireEvent.change(el as HTMLElement, { target: { value } });
  await flush();
}

/** 계산된 전환 시간을 모달 요소에 한해 덮는다 — 나머지 요소는 jsdom 값 그대로. */
function stubTransition(duration: string, delay = '0s, 0s') {
  const real = window.getComputedStyle.bind(window);
  vi.spyOn(window, 'getComputedStyle').mockImplementation((el: Element, pseudo?: string | null) => {
    const cs = real(el, pseudo);
    if (!(el instanceof HTMLElement) || el.dataset.testid !== 'upload-modal') return cs;
    const over: Record<string, string> = {
      transitionDuration: duration,
      transitionDelay: delay,
      'transition-duration': duration,
      'transition-delay': delay,
    };
    return new Proxy(cs, {
      get(target, prop) {
        if (typeof prop === 'string' && prop in over) return over[prop];
        if (prop === 'getPropertyValue') {
          return (name: string) => (name in over ? over[name] : target.getPropertyValue(name));
        }
        const v = Reflect.get(target, prop, target) as unknown;
        return typeof v === 'function' ? (v as (...a: unknown[]) => unknown).bind(target) : v;
      },
    });
  });
}

function LocationProbe() {
  const loc = useLocation();
  return <output data-testid="probe-path">{loc.pathname}</output>;
}

function makeFile() {
  const f = new File(['x'], 'nakdong_precip_2025_Lv2.nc', { type: 'application/octet-stream' });
  Object.defineProperty(f, 'size', { value: 349_000 });
  return f;
}
async function dropOne() {
  fireEvent.change(screen.getByTestId('up-drop-input'), { target: { files: [makeFile()] } });
  await flush();
  await screen.findByTestId('up-files');
}

const modal = () => screen.queryByTestId('upload-modal');
const stepBtn = (n: '①' | '②' | '③') => screen.getByRole('button', { name: new RegExp(`^${n}`) });

/** 등록 게이트를 채운다 — 선례 `register-steps-20260907.test.tsx` 의 `fillRegisterGates` 와 같은 순서. */
async function fillRegister() {
  await click(await screen.findByTestId('reg-open'));
  await screen.findByTestId('reg-steps');
  await change(screen.getByTestId('reg-category'), DEFAULT_CATEGORY);
  await change(screen.getByTestId('reg-datatype'), DEFAULT_DATA_TYPE);
  await change(screen.getByTestId('reg-level'), 'Lv0');
  await click(stepBtn('②'));
  await change(screen.getByTestId('reg-summary'), '시험용 설명 한 줄');
  await click(screen.getByTestId('reg-period-open'));
  await click(screen.getByTestId('reg-period-unit-일'));
  await change(screen.getByTestId('reg-period-pop-start-year'), '2025');
  await change(screen.getByTestId('reg-period-pop-start-month'), '06');
  await change(screen.getByTestId('reg-period-pop-start-day'), '01');
  await click(screen.getByTestId('reg-period-apply'));
  await change(screen.getByTestId('reg-interval-value'), '1');
  await change(screen.getByTestId('reg-interval-unit'), '시');
  await click(stepBtn('③'));
  await change(screen.getByTestId('reg-source-url'), 'https://example.org/data');
  await change(screen.getByTestId('reg-source-downloaded-on'), '2025-06-01');
}

/** 새 모달(① 파일 고르기)인가 — 끝난 모달의 입력·등록 카드가 남아 있지 않다. */
function expectFreshModal() {
  expect(modal()).not.toBeNull();
  expect(modal()?.getAttribute('data-state')).not.toBe('closing');
  expect(modal()?.getAttribute('data-scene')).toBe('pick');
  expect(screen.queryByTestId('up-files')).toBeNull();
  expect(screen.queryByTestId('reg-steps')).toBeNull();
}

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});

// ═══ 1 · UploadEntry — 등록 성공 뒤 닫는 도중 다시 열면 새 모달 ═══════════════════
describe('F-int 1 UploadEntry — 등록 성공 뒤 닫기 전환 사이 업로드 단추 = 새 모달(PRD-13)', () => {
  it('등록 → closing · 이동 → 업로드 단추 → ① 파일 고르기(입력 없음) · 대비 타이머 뒤에도 남는다', async () => {
    stubTransition('0.3s, 0.3s');
    const { calls, sources } = fakes();
    render(
      <MemoryRouter initialEntries={['/datasets']}>
        <SessionProvider account={account()}>
          <UploadEntry sources={sources} />
          <LocationProbe />
        </SessionProvider>
      </MemoryRouter>,
    );
    await click(screen.getByTestId('gnb-upload'));
    await dropOne();
    await fillRegister();
    await click(screen.getByTestId('reg-done'));
    await waitFor(() => expect(modal()?.getAttribute('data-state')).toBe('closing'));
    expect(calls.registered).toBe(1);
    expect(screen.getByTestId('probe-path').textContent).toBe(`/datasets/${DATASET_ID}`);

    await click(screen.getByTestId('gnb-upload'));
    expectFreshModal();

    // 앞 모달의 대비 타이머(300 ＋ 50ms)가 새 모달을 내리지 않는다.
    await act(async () => {
      await new Promise((r) => setTimeout(r, 420));
    });
    expectFreshModal();
  });
});

// ═══ 1 · GridAttachEntry — 반영 성공 뒤 닫는 도중 다시 열면 새 모달 ═══════════════
describe('F-int 1 GridAttachEntry — 반영 성공 뒤 닫기 전환 사이 「기준 격자 추가」 = 새 모달(PRD-13)', () => {
  it('반영 → closing → 「기준 격자 추가」 → ① 파일 고르기(입력 없음) · 대비 타이머 뒤에도 남는다', async () => {
    stubTransition('0.3s, 0.3s');
    const { calls, sources } = fakes();
    const onAttached = vi.fn();
    render(
      <MemoryRouter initialEntries={[`/datasets/${DATASET_ID}`]}>
        <SessionProvider account={account()}>
          <GridAttachEntry
            datasetId={DATASET_ID}
            datasetName="낙동강 강수"
            onAttached={onAttached}
            sources={sources}
          />
        </SessionProvider>
      </MemoryRouter>,
    );
    await click(screen.getByTestId('grid-attach-open'));
    await dropOne();
    await waitFor(() => expect(screen.getByTestId('grid-attach-confirm')).toBeEnabled());
    await click(screen.getByTestId('grid-attach-confirm'));
    await waitFor(() => expect(modal()?.getAttribute('data-state')).toBe('closing'));
    expect(calls.attached).toBe(1);
    expect(onAttached).toHaveBeenCalledTimes(1);

    await click(screen.getByTestId('grid-attach-open'));
    expectFreshModal();
    expect(modal()?.getAttribute('data-mode')).toBe('grid-attach');

    await act(async () => {
      await new Promise((r) => setTimeout(r, 420));
    });
    expectFreshModal();
  });
});

// ═══ 2 · useZoomPan — setPointerCapture 가 던져도 처리기가 끊기지 않는다 ═══════════
function mountHook() {
  const vp = document.createElement('div');
  Object.defineProperty(vp, 'clientWidth', { value: 512, configurable: true });
  Object.defineProperty(vp, 'clientHeight', { value: 512, configurable: true });
  const lay = document.createElement('div');
  Object.defineProperty(lay, 'offsetWidth', { value: 512, configurable: true });
  Object.defineProperty(lay, 'offsetHeight', { value: 1600, configurable: true });
  const hook = renderHook(() => useZoomPan({ bounds: { west: -90, south: -10, east: 90, north: 10 } }));
  act(() => {
    hook.result.current.viewportRef(vp as HTMLDivElement);
    hook.result.current.layersRef(lay);
  });
  act(() => hook.result.current.onNativeWidth(4096));
  return hook;
}

function throwingTarget() {
  return {
    setPointerCapture: vi.fn(() => {
      throw new DOMException('No active pointer with the given id is found.', 'NotFoundError');
    }),
  } as unknown as EventTarget;
}

describe('F-int 2 useZoomPan — setPointerCapture 가 던져도(NotFoundError) 누름 처리기가 끊기지 않는다', () => {
  it('누름 처리기가 예외를 밖으로 내지 않는다', () => {
    const hook = mountHook();
    const target = throwingTarget();
    let thrown: unknown = null;
    try {
      act(() =>
        hook.result.current.onPointerDown({ pointerId: 1, clientX: 300, clientY: 300, button: 0, currentTarget: target }),
      );
    } catch (e) {
      thrown = e;
    }
    expect((target as unknown as { setPointerCapture: ReturnType<typeof vi.fn> }).setPointerCapture).toHaveBeenCalledWith(1);
    expect(thrown).toBeNull();
  });

  it('던진 포인터의 끌기 상태가 남지 않는다 — 뒤이은 다른 포인터의 끌기가 화면을 옮긴다', () => {
    const hook = mountHook();
    try {
      act(() =>
        hook.result.current.onPointerDown({
          pointerId: 1,
          clientX: 300,
          clientY: 300,
          button: 0,
          currentTarget: throwingTarget(),
        }),
      );
    } catch {
      // 첫 시험이 이 예외 자체를 잰다 — 여기서는 뒤이은 포인터만 본다.
    }
    expect(hook.result.current.panOffset).toEqual({ x: 0, y: 0 });
    act(() => hook.result.current.onPointerDown({ pointerId: 2, clientX: 300, clientY: 300, button: 0 }));
    act(() => {
      fireEvent.pointerMove(window, { pointerId: 2, clientX: 300, clientY: 340 });
    });
    fireEvent.pointerUp(window, { pointerId: 2, clientX: 300, clientY: 340 });
    expect(hook.result.current.panOffset.y).toBeGreaterThan(0);
  });

  it('던진 포인터 자신의 움직임은 끌기로 이어지지 않는다(끝난 포인터)', () => {
    const hook = mountHook();
    try {
      act(() =>
        hook.result.current.onPointerDown({
          pointerId: 1,
          clientX: 300,
          clientY: 300,
          button: 0,
          currentTarget: throwingTarget(),
        }),
      );
    } catch {
      // 위와 같다.
    }
    act(() => {
      fireEvent.pointerMove(window, { pointerId: 1, clientX: 300, clientY: 340 });
    });
    expect(hook.result.current.panOffset).toEqual({ x: 0, y: 0 });
  });
});
