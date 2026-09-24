/**
 * design-fix 20260924 · 수정 레인 F-upload — A17 · A19.
 *
 * 오라클 = `dev-package/prd/specs/S-DESIGN-FIX-20260924.md` 「통합 수정」 수정 레인 표 F-upload 행
 *          ＋ 「확정 값」 2(닫는 중 배경은 누름을 통과시킨다 · 닫는 도중 다시 열면 같은 창으로 돌아온다).
 * 결함 원문 = `dev-package/sessions/design-fix-20260924-acceptance.md` A17 · A19.
 *
 * A17 — 닫는 동안 모달 **안 모든 요소**가 누름을 받지 않는다. `pointer-events: none` 은 배경 한 겹에만
 *   걸려 있어 안쪽에서 `pointer-events: auto` 를 명시한 패널(미리보기 도구 등)은 여전히 누름을 받는다.
 *   HTML `inert` 는 하위 전부를 hit-test·초점·보조기기에서 뺀다(명시 `auto` 자손 포함). jsdom 은 스타일을
 *   계산하지 않으므로 「모든 자손이 `[inert]` 조상(자기 포함)을 가진다」로 잰다.
 * A19 — `GridAttachEntry` 의 `open`/`rendered`/`onCloseStart` 배선에 대한 동작 시험(다시 열기 경로).
 *
 * 전환 시간 스텁은 선례 `design-fix-20260924-L2.test.tsx` 와 같은 방식(모달 요소에 한해 getComputedStyle 덮기).
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { SessionProvider } from '../src/permission/session';
import { GridAttachEntry } from '../src/components/upload/GridAttachEntry';
import { UploadEntry } from '../src/components/upload/UploadEntry';
import { UploadModal } from '../src/components/upload/UploadModal';
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

function fakes(): UploadSources {
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
      return { datasetId: DATASET_ID } as never;
    },
    async attachGrid() {
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
  return { upload, preview, projects, lineage };
}

async function flush() {
  await act(async () => {});
}
async function click(el: Element | null) {
  fireEvent.click(el as HTMLElement);
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

function renderEntry() {
  render(
    <MemoryRouter initialEntries={['/datasets']}>
      <SessionProvider account={account()}>
        <UploadEntry sources={fakes()} />
      </SessionProvider>
    </MemoryRouter>,
  );
}

function renderModal(onClose: () => void) {
  render(
    <MemoryRouter initialEntries={['/datasets']}>
      <SessionProvider account={account()}>
        <UploadModal sources={fakes()} onClose={onClose} />
      </SessionProvider>
    </MemoryRouter>,
  );
}

function renderGridAttach() {
  render(
    <MemoryRouter initialEntries={[`/datasets/${DATASET_ID}`]}>
      <SessionProvider account={account()}>
        <GridAttachEntry datasetId={DATASET_ID} datasetName="낙동강 강수" sources={fakes()} />
      </SessionProvider>
    </MemoryRouter>,
  );
}

const modal = () => screen.queryByTestId('upload-modal');
const backdrop = () => screen.queryByTestId('upload-backdrop');

/** 닫기 확인이 뜨면 「닫기」 쪽(강조 단추)을 누른다 — 입력이 없으면 확인 없이 곧바로 닫기가 시작된다. */
async function closeViaX() {
  await click(screen.getByTestId('upload-close'));
  const confirm = screen.queryByTestId('upload-close-confirm');
  if (confirm) await click(confirm.querySelector('.btn-strong'));
}

/** 배경 아래 모든 요소(배경 자신 포함)가 `[inert]` 조상-또는-자기를 가지는가. */
function everyDescendantInert(root: Element): { total: number; live: string[] } {
  const all = [root, ...Array.from(root.querySelectorAll('*'))];
  const live = all
    .filter((el) => el.closest('[inert]') === null)
    .map((el) => `${el.tagName.toLowerCase()}${(el as HTMLElement).dataset?.testid ? `[${(el as HTMLElement).dataset.testid}]` : ''}`);
  return { total: all.length, live };
}

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});

// ═══ A17 — 닫는 동안 모달 안 모든 요소가 누름을 받지 않는다 ═══════════════════════
describe('A17 닫는 동안 모달 전체가 inert', () => {
  it('열린 동안에는 배경·모달 어디에도 inert 가 없다', async () => {
    stubTransition('0.3s, 0.3s');
    renderModal(() => {});
    expect(backdrop()?.hasAttribute('inert')).toBe(false);
    expect(modal()?.closest('[inert]')).toBeNull();
    expect(screen.getByTestId('upload-close').closest('[inert]')).toBeNull();
  });

  it('× 로 닫기가 시작되면(data-state="closing") 배경에 inert — 하위 모든 요소가 inert 안에 든다', async () => {
    stubTransition('0.3s, 0.3s');
    renderModal(() => {});
    await closeViaX();
    const back = backdrop() as HTMLElement;
    expect(back.getAttribute('data-state')).toBe('closing');
    expect(back.hasAttribute('inert')).toBe(true);
    const { total, live } = everyDescendantInert(back);
    expect(total).toBeGreaterThan(1);
    expect(live).toEqual([]);
  });

  it('안쪽에서 pointer-events:auto 를 명시한 요소도 inert 안에 든다', async () => {
    stubTransition('0.3s, 0.3s');
    renderModal(() => {});
    // 미리보기 도구 패널처럼 명시 `auto` 를 가진 자손을 모달 안에 둔다.
    const panel = document.createElement('div');
    panel.style.pointerEvents = 'auto';
    panel.dataset.testid = 'explicit-auto-panel';
    const btn = document.createElement('button');
    panel.appendChild(btn);
    (modal() as HTMLElement).appendChild(panel);
    await closeViaX();
    expect(panel.style.pointerEvents).toBe('auto');
    expect(panel.closest('[inert]')).not.toBeNull();
    expect(btn.closest('[inert]')).not.toBeNull();
    panel.remove();
  });

  it('닫는 도중 다시 열면(UploadEntry) inert 가 풀린다', async () => {
    stubTransition('0.3s, 0.3s');
    renderEntry();
    await click(screen.getByTestId('gnb-upload'));
    await closeViaX();
    expect(backdrop()?.hasAttribute('inert')).toBe(true);
    await click(screen.getByTestId('gnb-upload'));
    expect(modal()).not.toBeNull();
    expect(backdrop()?.getAttribute('data-state')).not.toBe('closing');
    expect(backdrop()?.hasAttribute('inert')).toBe(false);
    expect(modal()?.closest('[inert]')).toBeNull();
  });

  it('전환 시간 0 이면 같은 틱에 닫힌다 — inert 를 남긴 채 모달이 남지 않는다', async () => {
    const onClose = vi.fn();
    renderModal(onClose);
    fireEvent.click(screen.getByTestId('upload-close'));
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});

// ═══ A19 — GridAttachEntry 다시 열기 경로 (값 2) ══════════════════════════════════
describe('A19 GridAttachEntry — 닫는 도중 「기준 격자 추가」를 다시 누르면 같은 창으로 돌아온다', () => {
  it('열기 → 모달이 격자 추가 모드로 뜬다', async () => {
    renderGridAttach();
    expect(modal()).toBeNull();
    await click(screen.getByTestId('grid-attach-open'));
    expect(modal()).not.toBeNull();
    expect(modal()?.getAttribute('data-mode')).toBe('grid-attach');
  });

  it('× (0.3s 스텁) → closing · 다시 열기 → closing 해제 · 언마운트 안 됨(transitionend · 대비 타이머 뒤에도)', async () => {
    stubTransition('0.3s, 0.3s');
    renderGridAttach();
    await click(screen.getByTestId('grid-attach-open'));
    await closeViaX();
    expect(modal()?.getAttribute('data-state')).toBe('closing');
    expect(backdrop()?.getAttribute('data-state')).toBe('closing');

    await click(screen.getByTestId('grid-attach-open'));
    expect(modal()).not.toBeNull();
    expect(modal()?.getAttribute('data-mode')).toBe('grid-attach');
    expect(modal()?.getAttribute('data-state')).not.toBe('closing');
    expect(backdrop()?.getAttribute('data-state')).not.toBe('closing');

    // 되돌아가는 전환의 transitionend 도 닫지 않는다(onClose 미호출 = 언마운트 없음).
    fireEvent.transitionEnd(modal() as HTMLElement, { propertyName: 'opacity' });
    await flush();
    expect(modal()).not.toBeNull();
    // 걸려 있던 대비 타이머(300 ＋ 50ms)도 풀렸다.
    await act(async () => {
      await new Promise((r) => setTimeout(r, 420));
    });
    expect(modal()).not.toBeNull();
    expect(modal()?.getAttribute('data-state')).not.toBe('closing');
  });

  it('다시 열지 않으면 transitionend 뒤 언마운트 → 다시 열면 새 모달', async () => {
    stubTransition('0.3s, 0.3s');
    renderGridAttach();
    await click(screen.getByTestId('grid-attach-open'));
    await closeViaX();
    fireEvent.transitionEnd(modal() as HTMLElement, { propertyName: 'opacity' });
    await flush();
    expect(modal()).toBeNull();

    await click(screen.getByTestId('grid-attach-open'));
    expect(modal()).not.toBeNull();
    expect(modal()?.getAttribute('data-state')).not.toBe('closing');
  });
});
