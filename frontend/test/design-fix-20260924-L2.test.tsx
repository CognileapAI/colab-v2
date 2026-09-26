/**
 * design-fix 20260924 · L2 업로드 — #1 · #2 · #4 · #10 · WU-A4.
 *
 * 오라클 = `dev-package/prd/specs/S-DESIGN-FIX-20260924.md` §4 「L2」(advisor ① F6 · F7 포함)
 *          ＋ 「확정 값」 1 · 2 · 3 · 7 · 17 · #10.
 *
 * CSS 단언은 선례 `design-fix-20260908.test.ts` 처럼 원문에서 주석을 걷고 선택자 블록을 잘라 잰다
 * (jsdom 은 스타일을 계산하지 않는다). 입력은 vite 의 `?raw` 다 — `vite.config.ts` 의 `test.css.include`
 * 가 `upload.css?raw` · `tokens.css?raw` 를 허용한다. `UploadModal.tsx?raw` 는 소스 문자열이다.
 *
 * 동작 단언(#1 · #4)은 RTL. `upload.css` 는 시험에서 비어 있으므로(`test.css.include` 밖) 계산된 전환
 * 시간은 기본 0 이다 — 「0.3s 로 스텁한 경우」는 `getComputedStyle` 을 모달 요소에 한해 덮어 만든다.
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { useState } from 'react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';

import uploadCssRaw from '../src/components/upload/upload.css?raw';
import tokensCssRaw from '../src/shell/tokens.css?raw';
import uploadModalRaw from '../src/components/upload/UploadModal.tsx?raw';
import { SessionProvider } from '../src/permission/session';
import { UploadEntry } from '../src/components/upload/UploadEntry';
import { UploadModal } from '../src/components/upload/UploadModal';
import { FileDropCard } from '../src/components/upload/FileDropCard';
import type {
  PreviewSource,
  ProjectSource,
  UploadSource,
  UploadSources,
} from '../src/components/upload/types';
import type { LineageSource, LineageSuggestionResponse } from '../src/components/lineage/types';
import type { CurrentAccount, Schemas } from '../src/api/client';

// ─── CSS 원문 읽기 ─────────────────────────────────────────────────────────────

const stripCssComments = (css: string): string => css.replace(/\/\*[\s\S]*?\*\//g, '');
const UPLOAD = stripCssComments(uploadCssRaw);
const TOKENS = stripCssComments(tokensCssRaw);

interface Rule {
  selectors: string[];
  body: string;
  parents: string[];
  at: number;
}

/** 규칙 목록 — 중첩(@layer · @media · @starting-style) 을 따라 선택자 규칙만 모은다. */
function rules(css: string): Rule[] {
  const out: Rule[] = [];
  const stack: { header: string; start: number; at: number }[] = [];
  let headerStart = 0;
  for (let i = 0; i < css.length; i++) {
    const c = css[i];
    if (c === '{') {
      stack.push({ header: css.slice(headerStart, i).trim(), start: i + 1, at: headerStart });
      headerStart = i + 1;
    } else if (c === '}') {
      const top = stack.pop();
      if (top && !top.header.startsWith('@')) {
        out.push({
          selectors: top.header.split(',').map((s) => s.replace(/\s+/g, ' ').trim()),
          body: css.slice(top.start, i).replace(/\s+/g, ' ').trim(),
          parents: stack.map((s) => s.header.replace(/\s+/g, ' ')),
          at: top.at,
        });
      }
      headerStart = i + 1;
    } else if (c === ';' && stack.length > 0 && stack[stack.length - 1]?.header.startsWith('@')) {
      headerStart = i + 1;
    }
  }
  return out;
}

const UPLOAD_RULES = rules(UPLOAD);

// 'hover' = `@media (hover: hover)` 안 하나(spec S-DEVICE-WIDTH-INPUT-20260926 V10 · 2단계 Q3ⓑ 승인 매체 자리 변경 · 기대 값 불변).
type Where = 'plain' | 'starting-style' | 'max640' | 'hover';

function inWhere(r: Rule, where: Where): boolean {
  const starting = r.parents.some((p) => p.startsWith('@starting-style'));
  const media = r.parents.filter((p) => p.startsWith('@media'));
  if (where === 'starting-style') return starting;
  if (where === 'hover') return !starting && media.length === 1 && media[0] === '@media (hover: hover)';
  if (where === 'max640') return !starting && media.some((p) => /max-width:\s*640px/.test(p));
  return !starting && media.length === 0;
}

/** 선택자 하나가 들어 있는 규칙 본문들(자리 조건 적용) — 여러 개면 이어 붙인다. */
function bodyOf(selector: string, where: Where = 'plain'): string {
  const found = UPLOAD_RULES.filter((r) => r.selectors.includes(selector) && inWhere(r, where));
  expect(found.length, `규칙 부재: ${selector} (${where})`).toBeGreaterThan(0);
  return found.map((r) => r.body).join(' ');
}

function firstAt(selector: string, where: Where = 'plain'): number {
  const r = UPLOAD_RULES.find((x) => x.selectors.includes(selector) && inWhere(x, where));
  expect(r, `규칙 부재: ${selector}`).toBeTruthy();
  return r?.at ?? -1;
}

/** 선언 하나 — 공백을 정규화해 `prop: value` 로 잰다. */
function hasDecl(body: string, prop: string, value: string): boolean {
  const norm = (s: string) => s.replace(/\s+/g, ' ').replace(/\s*,\s*/g, ', ').trim();
  return body
    .split(';')
    .map((d) => d.trim())
    .filter(Boolean)
    .some((d) => {
      const k = d.indexOf(':');
      return d.slice(0, k).trim() === prop && norm(d.slice(k + 1)) === norm(value);
    });
}

// ─── 대비 ─────────────────────────────────────────────────────────────────────

function themeBlock(css: string, head: string): string {
  const at = css.indexOf(head);
  expect(at, `테마 블록 부재: ${head}`).toBeGreaterThan(-1);
  const open = css.indexOf('{', at);
  const close = css.indexOf('}', open);
  return css.slice(open + 1, close);
}
const LIGHT = themeBlock(TOKENS, ':root {');
const DARK = themeBlock(TOKENS, ':root[data-theme="dark"] {');

function hexIn(block: string, name: string): string {
  const m = block.match(new RegExp(`${name}:\\s*(#[0-9a-fA-F]{6})\\b`));
  if (!m?.[1]) throw new Error(`토큰 hex 부재: ${name}`);
  return m[1];
}
function luminance(hex: string): number {
  const ch = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255);
  const lin = ch.map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4)) as [number, number, number];
  return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2];
}
function contrast(a: string, b: string): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x) as [number, number];
  return (hi + 0.05) / (lo + 0.05);
}

// ═══ #1 CSS — 업로드 모달 열기·닫기 전환 (값 1 · 값 2) ═══════════════════════
const EASE_1 = 'cubic-bezier(0.2, 0, 0, 1)';
describe('#1 CSS — keyframes → transition ＋ @starting-style ＋ closing', () => {
  it('`up-rise` 키프레임과 그 animation 이 없다', () => {
    expect(UPLOAD).not.toMatch(/@keyframes\s+up-rise/);
    expect(UPLOAD).not.toMatch(/animation:\s*up-rise/);
    expect(bodyOf('.modal.modal-takeover')).not.toMatch(/animation/);
  });

  it('`.modal.modal-takeover` 에 transform · opacity transition 0.3s (값 1)', () => {
    expect(
      hasDecl(
        bodyOf('.modal.modal-takeover'),
        'transition',
        `transform 0.3s ${EASE_1}, opacity 0.3s ${EASE_1}`,
      ),
    ).toBe(true);
  });

  it('`@starting-style` 안 같은 선택자에 시작 모양 translateY(3%) · opacity 0', () => {
    const body = bodyOf('.modal.modal-takeover', 'starting-style');
    expect(hasDecl(body, 'transform', 'translateY(3%)')).toBe(true);
    expect(hasDecl(body, 'opacity', '0')).toBe(true);
  });

  it('`[data-state="closing"]` 규칙에 같은 끝 모양', () => {
    const body = bodyOf('.modal.modal-takeover[data-state="closing"]');
    expect(hasDecl(body, 'transform', 'translateY(3%)')).toBe(true);
    expect(hasDecl(body, 'opacity', '0')).toBe(true);
  });

  it('닫는 중 배경은 누름을 통과시킨다 — pointer-events: none (값 2)', () => {
    expect(hasDecl(bodyOf('.modal-back.mb-takeover[data-state="closing"]'), 'pointer-events', 'none')).toBe(true);
  });
});

// ═══ #2 — 달력 팝오버 기준점 ＋ 여는 전환 (값 3) ═══════════════════════════════
describe('#2 `.dr-pop` 기준점 ＋ 여는 전환', () => {
  it('`.dr-pop` 블록에 transform-origin top left · opacity/transform 전환 var(--ease)', () => {
    const body = bodyOf('.dr-pop');
    expect(hasDecl(body, 'transform-origin', 'top left')).toBe(true);
    expect(hasDecl(body, 'transition', 'opacity var(--ease), transform var(--ease)')).toBe(true);
  });
  it('`@starting-style` 안 `.dr-pop` 시작 모양 opacity 0 · scale(0.96)', () => {
    const body = bodyOf('.dr-pop', 'starting-style');
    expect(hasDecl(body, 'opacity', '0')).toBe(true);
    expect(hasDecl(body, 'transform', 'scale(0.96)')).toBe(true);
  });
  it('640px 이하 바닥 시트 `.dr-pop` 은 transform-origin bottom center', () => {
    expect(hasDecl(bodyOf('.dr-pop', 'max640'), 'transform-origin', 'bottom center')).toBe(true);
  });
});

// ═══ #4 CSS — 드롭 영역 끌어 들어옴 (값 7) ════════════════════════════════════
describe('#4 CSS `.dropzone.is-dragover`', () => {
  for (const sel of ['.dropzone.is-dragover', '.up-empty .dropzone.is-dragover']) {
    it(`${sel} — 테두리 primary-600 · 바탕 primary-50`, () => {
      const body = bodyOf(sel);
      expect(hasDecl(body, 'border-color', 'var(--color-primary-600)')).toBe(true);
      expect(hasDecl(body, 'background', 'var(--color-primary-50)')).toBe(true);
    });
  }
  it('분석 장면(테두리 0 · 투명)은 그대로 — 같은 특이도의 분석 규칙이 뒤에 선다', () => {
    const analyze = '.modal-takeover[data-scene="analyze"] .dropzone';
    expect(hasDecl(bodyOf(analyze), 'border', '0')).toBe(true);
    expect(firstAt('.up-empty .dropzone.is-dragover')).toBeLessThan(firstAt(analyze));
  });
});

// ═══ #10 — `.btn-strong:hover` primary-700 ═════════════════════════════════════
describe('#10 `.btn-strong:hover`', () => {
  it('배경 var(--color-primary-700)', () => {
    // design-fix 20260924 F-final 3 — 비활성 제외는 `:where()` 안(특이도 무변 · A2 선례).
    expect(hasDecl(bodyOf('.btn-strong:where(:not(:disabled)):hover', 'hover'), 'background', 'var(--color-primary-700)')).toBe(true);
  });
  it('--color-on-primary 대 primary-700 대비 두 테마 ≥ 4.5', () => {
    for (const block of [LIGHT, DARK]) {
      expect(contrast(hexIn(block, '--color-on-primary'), hexIn(block, '--color-primary-700'))).toBeGreaterThanOrEqual(4.5);
    }
  });
});

// ═══ WU-A4 — 업로드 `:active` (값 17) ══════════════════════════════════════════
describe('WU-A4 업로드 누름 피드백', () => {
  const cases: [string, string, string][] = [
    // design-fix 후속 20260925 Q3a — 파란 채움 누름 = hover(primary-700)보다 한 단 진한 primary-800.
    ['.btn-strong:active', 'background', 'var(--color-primary-800)'],
    // design-fix 20260924 F-final · A21 — hover 가 surface-hover 인 누름 자리 = 값 19.
    ['.dr-nav button:active', 'background', 'var(--color-surface-pressed)'],
    ['.dr-cal-d:active', 'background', 'var(--color-primary-200)'],
    ['.dr-useg button:active', 'background', 'var(--color-surface-pressed)'],
    ['.dr-field:active', 'border-color', 'var(--color-primary-600)'],
  ];
  for (const [sel, prop, value] of cases) {
    it(`${sel} { ${prop}: ${value} }`, () => {
      expect(hasDecl(bodyOf(sel), prop, value)).toBe(true);
    });
  }
  it('`.dr-useg button.on` 은 누르는 중에도 primary-600 — `.on` 규칙이 `:active` 뒤에 선다', () => {
    expect(hasDecl(bodyOf('.dr-useg button.on'), 'background', 'var(--color-primary-600)')).toBe(true);
    expect(firstAt('.dr-useg button:active')).toBeLessThan(firstAt('.dr-useg button.on'));
  });
});

// ═══ #1 F6 — 닫기 경로 하나 ═════════════════════════════════════════════════════
describe('#1 advisor ① F6 — UploadModal 안 모든 닫기 경로가 닫기 요청 함수 하나를 탄다', () => {
  const code = uploadModalRaw
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .split('\n')
    .map((l) => l.replace(/(^|[^:'"`])\/\/.*$/, '$1'))
    .join('\n');
  it('`props.onClose` 참조는 1곳(전환이 끝난 뒤 부르는 자리)뿐이다', () => {
    expect(code.match(/props\.onClose\b/g) ?? []).toHaveLength(1);
  });
  it('계정 전환 보호의 discard 도 닫기 요청 함수를 부른다', () => {
    expect(code).toMatch(/discard:\s*beginClose\b/);
  });
});

// ─── RTL 고정물 ───────────────────────────────────────────────────────────────

const UPLOAD_ID = '01JYZ9K7WQ3N8V4M2X6C5B0UP1';
const FILE_ID = '01JYZ9K7WQ3N8V4M2X6C5B0FI1';

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
      return { datasetId: '01JYZ9K7WQ3N8V4M2X6C5B0DS1' } as never;
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

const modal = () => screen.queryByTestId('upload-modal');

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});

// ═══ #1 동작 — 닫기 전환 · 지연 언마운트 ════════════════════════════════════════
describe('#1 동작 — 전환 시간 0.3s(스텁)', () => {
  it('× 누름 → 모달이 남고 data-state="closing" → transitionend 뒤 언마운트', async () => {
    stubTransition('0.3s, 0.3s');
    renderEntry();
    await click(screen.getByTestId('gnb-upload'));
    await click(screen.getByTestId('upload-close'));
    expect(modal()).not.toBeNull();
    expect(modal()?.getAttribute('data-state')).toBe('closing');
    expect(screen.getByTestId('upload-backdrop').getAttribute('data-state')).toBe('closing');
    fireEvent.transitionEnd(modal() as HTMLElement, { propertyName: 'opacity' });
    await flush();
    expect(modal()).toBeNull();
  });

  it('transitionend 두 번(transform · opacity)이 와도 onClose 는 1회', async () => {
    stubTransition('0.3s, 0.3s');
    const onClose = vi.fn();
    renderModal(onClose);
    await click(screen.getByTestId('upload-close'));
    expect(onClose).toHaveBeenCalledTimes(0);
    fireEvent.transitionEnd(modal() as HTMLElement, { propertyName: 'transform' });
    fireEvent.transitionEnd(modal() as HTMLElement, { propertyName: 'opacity' });
    await flush();
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('모달 안 자식 요소의 transitionend(버블)는 닫기를 끝내지 않는다', async () => {
    stubTransition('0.3s, 0.3s');
    const onClose = vi.fn();
    renderModal(onClose);
    await click(screen.getByTestId('upload-close'));
    fireEvent.transitionEnd(screen.getByTestId('upload-close'), { propertyName: 'background-color' });
    await flush();
    expect(onClose).toHaveBeenCalledTimes(0);
    expect(modal()?.getAttribute('data-state')).toBe('closing');
  });

  it('transitionend 가 없어도 전환 시간 ＋ 50ms 뒤 onClose(가짜 타이머)', async () => {
    vi.useFakeTimers();
    stubTransition('0.3s, 0.3s');
    const onClose = vi.fn();
    renderModal(onClose);
    fireEvent.click(screen.getByTestId('upload-close'));
    act(() => {
      vi.advanceTimersByTime(349);
    });
    expect(onClose).toHaveBeenCalledTimes(0);
    act(() => {
      vi.advanceTimersByTime(1);
    });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('여는 도중(마운트 직후) 닫기 → 곧바로 closing', async () => {
    stubTransition('0.3s, 0.3s');
    const onClose = vi.fn();
    renderModal(onClose);
    fireEvent.click(screen.getByTestId('upload-close'));
    expect(modal()?.getAttribute('data-state')).toBe('closing');
    expect(onClose).toHaveBeenCalledTimes(0);
  });

  it('닫는 중에는 Esc · 배경 누름을 다시 받지 않는다', async () => {
    stubTransition('0.3s, 0.3s');
    const onClose = vi.fn();
    renderModal(onClose);
    await click(screen.getByTestId('upload-close'));
    fireEvent.keyDown(document, { key: 'Escape' });
    const back = screen.getByTestId('upload-backdrop');
    fireEvent.mouseDown(back);
    fireEvent.click(back);
    await flush();
    expect(onClose).toHaveBeenCalledTimes(0);
    expect(screen.queryByTestId('upload-close-confirm')).toBeNull();
    expect(modal()?.getAttribute('data-state')).toBe('closing');
  });
});

describe('#1 동작 — 전환 시간 0(jsdom 기본 · 전역 reduced-motion)', () => {
  it('× 누름과 같은 틱에 언마운트 — onClose 1회', async () => {
    const onClose = vi.fn();
    renderModal(onClose);
    fireEvent.click(screen.getByTestId('upload-close'));
    expect(onClose).toHaveBeenCalledTimes(1);
  });
  it('UploadEntry 에서도 × 뒤 곧바로 모달이 사라진다', async () => {
    renderEntry();
    await click(screen.getByTestId('gnb-upload'));
    await click(screen.getByTestId('upload-close'));
    expect(modal()).toBeNull();
  });
});

// ═══ #1 동작 — 닫는 중 다시 열기 (값 2) ══════════════════════════════════════════
describe('#1 값 2 — 닫는 도중 업로드 단추를 누르면 같은 창으로 돌아온다', () => {
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

  it('closing 해제 · 입력값 유지 · onClose 0회(전환이 끝나도 · 타이머가 지나도 남는다)', async () => {
    stubTransition('0.3s, 0.3s');
    renderEntry();
    await click(screen.getByTestId('gnb-upload'));
    await dropOne();
    await click(screen.getByTestId('upload-close'));
    const confirm = screen.queryByTestId('upload-close-confirm');
    if (confirm) await click(confirm.querySelector('.btn-strong'));
    expect(modal()?.getAttribute('data-state')).toBe('closing');

    await click(screen.getByTestId('gnb-upload'));
    expect(modal()).not.toBeNull();
    expect(modal()?.getAttribute('data-state')).not.toBe('closing');
    expect(screen.getByTestId('upload-backdrop').getAttribute('data-state')).not.toBe('closing');
    expect(screen.getByTestId('up-files')).toBeTruthy();

    // 되돌아가는 전환이 끝나며 오는 transitionend 도 닫지 않는다.
    fireEvent.transitionEnd(modal() as HTMLElement, { propertyName: 'opacity' });
    await flush();
    expect(modal()).not.toBeNull();
    // 걸려 있던 대비 타이머도 풀렸다.
    await act(async () => {
      await new Promise((r) => setTimeout(r, 420));
    });
    expect(modal()).not.toBeNull();
    expect(screen.getByTestId('up-files')).toBeTruthy();
  });

  it('완전히 닫힌 뒤 다시 열면 처음(파일 고르기) 장면이다 (PRD-13)', async () => {
    stubTransition('0.3s, 0.3s');
    renderEntry();
    await click(screen.getByTestId('gnb-upload'));
    await dropOne();
    await click(screen.getByTestId('upload-close'));
    const confirm = screen.queryByTestId('upload-close-confirm');
    if (confirm) await click(confirm.querySelector('.btn-strong'));
    fireEvent.transitionEnd(modal() as HTMLElement, { propertyName: 'opacity' });
    await flush();
    expect(modal()).toBeNull();

    await click(screen.getByTestId('gnb-upload'));
    expect(modal()?.getAttribute('data-scene')).toBe('pick');
    expect(screen.queryByTestId('up-files')).toBeNull();
    expect(modal()?.getAttribute('data-state')).not.toBe('closing');
  });
});

// ═══ #4 동작 — 드롭 영역 끌어 들어옴·나감 ═══════════════════════════════════════
describe('#4 동작 — `is-dragover`', () => {
  function Harness(props: { onPick: (files: File[]) => void }) {
    const [picked] = useState([]);
    return <FileDropCard picked={picked} onPick={props.onPick} onKind={() => {}} />;
  }
  const drop = () => screen.getByTestId('up-drop');
  const child = () => drop().querySelector('.big') as HTMLElement;

  it('dragEnter → is-dragover 부여', () => {
    render(<Harness onPick={() => {}} />);
    expect(drop().classList.contains('is-dragover')).toBe(false);
    fireEvent.dragEnter(drop());
    expect(drop().classList.contains('is-dragover')).toBe(true);
  });

  it('자식 요소의 dragEnter/dragLeave 짝이 와도 유지 · 바깥 dragLeave 로 해제', () => {
    render(<Harness onPick={() => {}} />);
    fireEvent.dragEnter(drop());
    // 라벨 → 자식: 자식 enter 가 먼저, 라벨 leave 가 뒤 (브라우저 순서).
    fireEvent.dragEnter(child());
    fireEvent.dragLeave(drop());
    expect(drop().classList.contains('is-dragover')).toBe(true);
    // 자식 → 라벨: 라벨 enter, 자식 leave.
    fireEvent.dragEnter(drop());
    fireEvent.dragLeave(child());
    expect(drop().classList.contains('is-dragover')).toBe(true);
    // 라벨 → 바깥.
    fireEvent.dragLeave(drop());
    expect(drop().classList.contains('is-dragover')).toBe(false);
  });

  it('drop 뒤 해제', async () => {
    const onPick = vi.fn();
    render(<Harness onPick={onPick} />);
    fireEvent.dragEnter(drop());
    fireEvent.dragEnter(child());
    fireEvent.drop(child(), { dataTransfer: { files: [], items: [] } });
    await flush();
    expect(drop().classList.contains('is-dragover')).toBe(false);
    // 다음 끌기도 다시 켜진다(계수가 0 으로 돌아왔다).
    fireEvent.dragEnter(drop());
    expect(drop().classList.contains('is-dragover')).toBe(true);
  });

  it('dragOver 는 여전히 preventDefault ＋ stopPropagation (두 번 접수 방지)', () => {
    render(<Harness onPick={() => {}} />);
    const onDoc = vi.fn();
    document.addEventListener('dragover', onDoc);
    try {
      const notPrevented = fireEvent.dragOver(drop());
      expect(notPrevented).toBe(false);
      expect(onDoc).not.toHaveBeenCalled();
    } finally {
      document.removeEventListener('dragover', onDoc);
    }
  });
});
