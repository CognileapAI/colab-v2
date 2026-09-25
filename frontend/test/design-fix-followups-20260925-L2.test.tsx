/**
 * design-fix 후속 20260925 · L2(업로드) — CSS 정적 단언 ＋ RTL.
 *
 * 오라클 = `dev-package/prd/specs/S-DESIGN-FIX-FOLLOWUPS-20260925.md` 부록 C 「L2」 표.
 * 판정 = `dev-package/intent/2026-09-25-design-fix-followups.md` 설계트리 Q1e · Q2a · Q2b · Q2d · Q2f · Q3a · Q4 · Q8a · Q8b · Q8e.
 * CSS 방식은 `design-fix-followups-20260925-L1.test.ts` 와 같다 — 주석을 걷고 선택자 블록을 잘라 잰다.
 * 이 파일은 `@starting-style` 안 규칙도 잰다(매체 이름 `@starting-style` 로 모은다).
 * green-by-skip 방지: 대상 목록 길이를 먼저 단언하고, 선택자 블록을 못 찾으면 빈 문자열이 아니라 실패한다.
 */
// @ts-expect-error — 타입 선언 없이 런타임만 쓴다(vitest 는 node 위에서 돈다 · 선례와 같은 규율).
import { readFileSync } from 'node:fs';
// @ts-expect-error — 같은 이유.
import { resolve } from 'node:path';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { SessionProvider } from '../src/permission/session';
import { UploadEntry } from '../src/components/upload/UploadEntry';
import { PreviewPanel } from '../src/components/upload/PreviewPanel';
import { DEFAULT_CATEGORY, DEFAULT_DATA_TYPE } from '../src/components/upload/axisDict';
import type {
  PaletteOption,
  PreviewSource,
  ProjectSource,
  UploadSource,
  UploadSources,
} from '../src/components/upload/types';
import type { LineageSource, LineageSuggestionResponse } from '../src/components/lineage/types';
import type { CurrentAccount, Schemas } from '../src/api/client';

declare const process: { cwd(): string };

const raw = (rel: string): string => String(readFileSync(resolve(process.cwd(), rel), 'utf8'));
const strip = (css: string): string => css.replace(/\/\*[\s\S]*?\*\//g, '');

const UPLOAD = strip(raw('src/components/upload/upload.css'));
const PRIM = strip(raw('src/shell/primitives.css'));

// ── 규칙 파서(L1 시험과 같은 규칙 ＋ `@starting-style`) ─────────────────────
type Rule = { selectors: string[]; body: string; media: string };

function rules(css: string, media = ''): Rule[] {
  const out: Rule[] = [];
  let i = 0;
  while (i < css.length) {
    const open = css.indexOf('{', i);
    if (open < 0) break;
    const head = css.slice(i, open).trim();
    let depth = 1;
    let j = open + 1;
    while (j < css.length && depth > 0) {
      if (css[j] === '{') depth += 1;
      else if (css[j] === '}') depth -= 1;
      j += 1;
    }
    const inner = css.slice(open + 1, j - 1);
    if (head.startsWith('@layer')) out.push(...rules(inner, media));
    else if (head.startsWith('@media')) out.push(...rules(inner, head));
    else if (head.startsWith('@starting-style')) out.push(...rules(inner, '@starting-style'));
    else if (head.startsWith('@')) {
      /* @keyframes — 계측 밖 */
    } else {
      out.push({ selectors: splitList(head), body: inner.trim(), media });
    }
    i = j;
  }
  return out;
}

function splitList(head: string): string[] {
  const parts: string[] = [];
  let depth = 0;
  let cur = '';
  for (const ch of head) {
    if (ch === '(') depth += 1;
    if (ch === ')') depth -= 1;
    if (ch === ',' && depth === 0) {
      parts.push(cur.trim());
      cur = '';
    } else cur += ch;
  }
  if (cur.trim()) parts.push(cur.trim());
  return parts.map((s) => s.replace(/\s+/g, ' '));
}

function body(css: string, selector: string, media = ''): string {
  const found = rules(css)
    .filter((r) => r.media === media && r.selectors.includes(selector))
    .map((r) => r.body);
  expect(found.length, `선택자 블록 수: ${selector} ${media}`).toBe(1);
  return found[0] ?? '';
}

function decls(b: string): string[] {
  return b
    .split(';')
    .map((d) => d.trim().replace(/\s+/g, ' '))
    .filter(Boolean);
}

function prop(b: string, name: string): string | undefined {
  let v: string | undefined;
  for (const d of decls(b)) {
    const at = d.indexOf(':');
    if (at > 0 && d.slice(0, at).trim() === name) v = d.slice(at + 1).trim();
  }
  return v;
}

function expectDisabledPair(b: string, label: string): void {
  expect(decls(b).length, `${label} 선언 수`).toBe(2);
  expect(Number(prop(b, 'opacity')), `${label} opacity`).toBe(0.5);
  expect(prop(b, 'cursor'), `${label} cursor`).toBe('not-allowed');
  expect(b, `${label} !important`).not.toMatch(/!important/);
}

// ── 대상 목록(개수 먼저) ────────────────────────────────────────────────────
const DISABLED_TARGETS = ['.thumbrow .th-slot:disabled', '.regsteps button:disabled'];
const BLUE_PRESS = ['.btn-strong:active'];
const PALETTE_CASES: (number | 'fail')[] = [0, 1, 2, 3, 4, 'fail'];
const DIALOGS = ['.confirm-back .modal', '.modal.pvx'];
const EASE = '0.3s cubic-bezier(0.2, 0, 0, 1)';

describe('L2 개수 — 대상 목록 길이(green-by-skip 방지)', () => {
  it('비활성 선택자 2 · 파란 채움 누름 1 · 팔레트 경우 6', () => {
    expect(DISABLED_TARGETS.length).toBe(2);
    expect(BLUE_PRESS.length).toBe(1);
    expect(PALETTE_CASES.length).toBe(6);
  });
});

// ═══ V1 Q1e — 격자 칸 · 등록 단계 비활성 ═════════════════════════════════════
describe('V1 업로드 비활성 두 곳 — opacity .5 · cursor not-allowed', () => {
  for (const sel of DISABLED_TARGETS) {
    it(`${sel} = 두 값`, () => {
      expectDisabledPair(body(UPLOAD, sel), sel);
    });
  }
  it('격자 칸 hover 는 비활성을 뺀다(프리미티브 `:where(:not(:disabled))` 형태)', () => {
    const hovers = rules(UPLOAD).flatMap((r) =>
      r.selectors.filter((s) => s.startsWith('.thumbrow .th-slot') && s.endsWith(':hover')),
    );
    expect(hovers.length, '격자 칸 hover 선택자 수').toBe(1);
    expect(hovers[0]).toBe('.thumbrow .th-slot:where(:not(:disabled)):hover');
    expect(prop(body(UPLOAD, hovers[0] ?? ''), 'border-color')).toBe('var(--color-primary-600)');
  });
  it('`.btn-strong` 규칙은 cursor · opacity 를 정하지 않는다(프리미티브 비활성 규칙이 닿는다)', () => {
    const strong = rules(UPLOAD).filter((r) => r.selectors.some((s) => s.startsWith('.btn-strong')));
    expect(strong.length, '.btn-strong 규칙 수').toBeGreaterThan(0);
    for (const r of strong) {
      expect(prop(r.body, 'cursor'), r.selectors.join(', ')).toBeUndefined();
      expect(prop(r.body, 'opacity'), r.selectors.join(', ')).toBeUndefined();
    }
  });
});

// ═══ V2 Q3a — 강조 단추 누름 ═══════════════════════════════════════════════════
describe('V2 `.btn-strong` 누름 = primary-800', () => {
  for (const sel of BLUE_PRESS) {
    it(`${sel} 배경 = var(--color-primary-800)`, () => {
      expect(prop(body(UPLOAD, sel), 'background')).toBe('var(--color-primary-800)');
    });
  }
});

// ═══ V4 Q2a — 두 대화상자 ═══════════════════════════════════════════════════════
describe('V4 닫기 확인창 · 미리보기 확대창 = 그림자 0 ＋ 1px border-strong', () => {
  it('대상 2', () => expect(DIALOGS.length).toBe(2));
  for (const sel of DIALOGS) {
    it(sel, () => {
      const b = body(UPLOAD, sel);
      expect(prop(b, 'box-shadow'), `${sel} box-shadow`).toBe('none');
      expect(prop(b, 'border'), `${sel} border`).toBe('1px solid var(--color-border-strong)');
    });
  }
  it('전역 `.modal` 기본 그림자는 그대로다(회귀 잠금)', () => {
    expect(prop(body(PRIM, '.modal'), 'box-shadow')).toBe('var(--shadow-sm)');
  });
});

// ═══ V5 Q2b — 뒤판 배경색 전환 ═══════════════════════════════════════════════════
describe('V5 업로드 모달 뒤판 — 배경색 0.3s 전환 · 시작 · 닫는 중 투명', () => {
  it('뒤판 transition = background-color 0.3s cubic-bezier(0.2, 0, 0, 1)', () => {
    expect(prop(body(UPLOAD, '.modal-back.mb-takeover'), 'transition')).toBe(`background-color ${EASE}`);
  });
  it('`@starting-style` 안 뒤판 배경 = transparent', () => {
    expect(prop(body(UPLOAD, '.modal-back.mb-takeover', '@starting-style'), 'background-color')).toBe('transparent');
  });
  it('닫는 중 뒤판 = 배경 transparent ＋ pointer-events none 유지', () => {
    const b = body(UPLOAD, '.modal-back.mb-takeover[data-state="closing"]');
    expect(prop(b, 'background-color')).toBe('transparent');
    expect(prop(b, 'pointer-events')).toBe('none');
  });
  it('모달 본체 transition 원문 불변', () => {
    expect(prop(body(UPLOAD, '.modal.modal-takeover'), 'transition')).toBe(`transform ${EASE}, opacity ${EASE}`);
  });
});

// ═══ 공통 고정물(RTL) ══════════════════════════════════════════════════════════
const UPLOAD_ID = '01JYZ9K7WQ3N8V4M2X6C5B0UP1';
const FILE_ID = '01JYZ9K7WQ3N8V4M2X6C5B0FI1';
const DATASET_ID = '01JYZ9K7WQ3N8V4M2X6C5B0DS1';
const UNAVAILABLE = '지금 미리보기를 만들 수 없어요. 잠시 뒤 다시 시도해 주세요.';

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

function uploadSources(): UploadSources {
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
  return { upload, preview, projects, lineage } as UploadSources;
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

/** 등록 화면 ② 까지 — 기간 칸이 서는 단계. */
async function openPeriodStep() {
  render(
    <MemoryRouter initialEntries={['/datasets']}>
      <SessionProvider account={account()}>
        <UploadEntry sources={uploadSources()} />
      </SessionProvider>
    </MemoryRouter>,
  );
  await click(screen.getByTestId('gnb-upload'));
  const f = new File(['x'], 'nakdong_precip_2025_Lv2.nc', { type: 'application/octet-stream' });
  Object.defineProperty(f, 'size', { value: 349_000 });
  fireEvent.change(screen.getByTestId('up-drop-input'), { target: { files: [f] } });
  await flush();
  await screen.findByTestId('up-files');
  await click(await screen.findByTestId('reg-open'));
  await screen.findByTestId('reg-steps');
  await change(screen.getByTestId('reg-category'), DEFAULT_CATEGORY);
  await change(screen.getByTestId('reg-datatype'), DEFAULT_DATA_TYPE);
  await change(screen.getByTestId('reg-level'), 'Lv0');
  await click(screen.getByRole('button', { name: /^②/ }));
}

afterEach(() => {
  vi.restoreAllMocks();
  delete (Element.prototype as { scrollIntoView?: unknown }).scrollIntoView;
});

// ═══ V6 Q2d — 달력 팝오버 열 때 스크롤 ═══════════════════════════════════════════
describe('V6 기간 달력 팝오버 — 열 때 자기 자리로 한 번 스크롤', () => {
  it('`.dr-pop` 스크롤 아래 여백 = 88px(등록 본문 아래 여백 재사용 · 우려 2 ⓐ)', () => {
    expect(prop(body(UPLOAD, '.dr-pop'), 'scroll-margin-bottom')).toBe('88px');
    // 재사용하는 값의 출처가 그대로 있다.
    expect(prop(body(UPLOAD, '.modal-takeover[data-scene="register"] .up-body'), 'padding')).toBe('20px 32px 88px');
  });

  it('기간 칸 누름 → 팝오버 루트에 scrollIntoView 1회 · block nearest · smooth 아님 · 다시 렌더에 추가 0', async () => {
    const calls: { el: Element; arg: unknown }[] = [];
    (Element.prototype as { scrollIntoView?: unknown }).scrollIntoView = function (this: Element, arg?: unknown) {
      calls.push({ el: this, arg });
    };
    await openPeriodStep();
    expect(calls.length, '열기 전 호출').toBe(0);
    await click(screen.getByTestId('reg-period-open'));
    const pop = await screen.findByTestId('reg-period-pop');
    expect(calls.length).toBe(1);
    expect(calls[0]?.el).toBe(pop);
    const arg = calls[0]?.arg as ScrollIntoViewOptions;
    expect(arg.block).toBe('nearest');
    expect(arg.behavior).not.toBe('smooth');

    // 팝오버 안 조작으로 다시 렌더 — 추가 호출이 없다.
    await click(screen.getByTestId('reg-period-unit-일'));
    await change(screen.getByTestId('reg-period-pop-start-year'), '2025');
    expect(screen.getByTestId('reg-period-pop')).toBe(pop);
    expect(calls.length).toBe(1);
  });

  it('scrollIntoView 가 없는 jsdom 에서도 예외 없이 열린다', async () => {
    expect('scrollIntoView' in Element.prototype).toBe(false);
    await openPeriodStep();
    await click(screen.getByTestId('reg-period-open'));
    expect(await screen.findByTestId('reg-period-pop')).toBeTruthy();
  });
});

// ═══ V7 Q2f · Q8a — 팔레트 안내 · 다시 시도 ══════════════════════════════════════
function palettesOf(n: number): PaletteOption[] {
  return ['viridis', 'magma', 'cividis', 'plasma'].slice(0, n).map((p) => ({ palette: p, label: p })) as PaletteOption[];
}

function previewSource(palettes: () => Promise<PaletteOption[]>, createRender?: () => Promise<unknown>) {
  return {
    palettes: vi.fn(palettes),
    createRender: vi.fn(createRender ?? (async () => ({ renderId: 'r', status: '그리는 중' }))),
    getRender: vi.fn(async () => ({ renderId: 'r', status: '그리는 중' })),
  };
}

function mountPanel(src: ReturnType<typeof previewSource>) {
  return render(<PreviewPanel source={src as unknown as PreviewSource} uploadId={UPLOAD_ID} hasReferenceGrid />);
}

const retryButtons = () => screen.queryAllByRole('button', { name: '다시 시도' });

describe('V7 팔레트 안내 = 1개 이상이면서 3개가 아닐 때만 · 0개 · 실패 = UNAVAILABLE ＋ 「다시 시도」', () => {
  it('0개 → 안내 없음 · 오류 = UNAVAILABLE · 「다시 시도」 1 · 그리기 비활성', async () => {
    const src = previewSource(async () => []);
    mountPanel(src);
    const err = await screen.findByTestId('up-preview-error');
    expect(err.textContent).toBe(UNAVAILABLE);
    expect(screen.queryByTestId('up-palette-issue')).toBeNull();
    expect(retryButtons().length).toBe(1);
    expect(retryButtons()[0]?.className).toBe('btn btn-sm');
    expect(screen.getByTestId('up-preview-draw')).toBeDisabled();
  });

  for (const n of [1, 2, 4]) {
    it(`${n}개 → 안내 있음 · 「다시 시도」 0`, async () => {
      const src = previewSource(async () => palettesOf(n));
      mountPanel(src);
      const issue = await screen.findByTestId('up-palette-issue');
      expect(issue.textContent).toContain('팔레트 목록이 예상한 3종과 달라요.');
      expect(retryButtons().length).toBe(0);
      expect(screen.queryByTestId('up-preview-error')).toBeNull();
    });
  }

  it('3개 → 안내 없음 · 오류 없음', async () => {
    const src = previewSource(async () => palettesOf(3));
    mountPanel(src);
    await waitFor(() => expect(screen.getByTestId('up-preview-draw')).toBeEnabled());
    expect(screen.queryByTestId('up-palette-issue')).toBeNull();
    expect(screen.queryByTestId('up-preview-error')).toBeNull();
    expect(retryButtons().length).toBe(0);
  });

  it('조회 실패 → 「다시 시도」 → 다시 조회(2회) · 3개 성공 뒤 오류 0 · 그리기 활성', async () => {
    let n = 0;
    const src = previewSource(async () => {
      n += 1;
      if (n === 1) throw new Error('palettes unavailable');
      return palettesOf(3);
    });
    mountPanel(src);
    const err = await screen.findByTestId('up-preview-error');
    expect(err.textContent).toBe(UNAVAILABLE);
    expect(screen.queryByTestId('up-palette-issue')).toBeNull();
    expect(retryButtons().length).toBe(1);

    await click(retryButtons()[0] ?? null);
    await waitFor(() => expect(src.palettes).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(screen.getByTestId('up-preview-draw')).toBeEnabled());
    expect(screen.queryByTestId('up-preview-error')).toBeNull();
    expect(retryButtons().length).toBe(0);
  });

  it('0개에서 「다시 시도」도 다시 조회한다(우려 4 ⓐ)', async () => {
    const src = previewSource(async () => []);
    mountPanel(src);
    await screen.findByTestId('up-preview-error');
    await click(retryButtons()[0] ?? null);
    await waitFor(() => expect(src.palettes).toHaveBeenCalledTimes(2));
    expect(await screen.findByTestId('up-preview-error')).toBeTruthy();
    expect(retryButtons().length).toBe(1);
  });

  it('그리기 실패 오류에는 「다시 시도」가 없다', async () => {
    const src = previewSource(
      async () => palettesOf(3),
      async () => {
        throw new Error('render unreachable');
      },
    );
    mountPanel(src);
    await waitFor(() => expect(screen.getByTestId('up-preview-draw')).toBeEnabled());
    await click(screen.getByTestId('up-preview-draw'));
    const err = await screen.findByTestId('up-preview-error');
    expect(err.textContent).toBe(UNAVAILABLE);
    expect(retryButtons().length).toBe(0);
    expect(src.palettes).toHaveBeenCalledTimes(1);
  });
});

// ═══ V9 Q8b · Q8e — 원문 ═══════════════════════════════════════════════════════
describe('V9 정리 — 시험 제목 · 업로드 모달 머리 주석', () => {
  it('F-preview A30 제목에 「16ms 마다 1px 씩」 0', () => {
    expect(raw('test/design-fix-20260924-F-preview.test.tsx')).not.toContain('16ms 마다 1px 씩');
  });
  it('`UploadModal.tsx` 머리 주석(첫 import 앞)에 새 부모 = `useUploadModalPresence` 필수', () => {
    const src = raw('src/components/upload/UploadModal.tsx');
    const head = src.slice(0, src.indexOf('\nimport '));
    expect(head).toMatch(/새 부모.*useUploadModalPresence.*필수/);
  });
});

// ═══ V10 Q4 — 등록 성공 픽스처 분기 ══════════════════════════════════════════════
describe('V10 등록 성공 픽스처 — 질의 분기 1 · 기본 동작 불변 · 장면 1', () => {
  const AUDIT = raw('audit-upload.tsx');
  it('`register=ok` 분기가 두 실제 부모(UploadEntry · GridAttachEntry)를 쓴다', () => {
    expect(AUDIT).toMatch(/get\('register'\) === 'ok'/);
    expect(AUDIT).toMatch(/<UploadEntry /);
    expect(AUDIT).toMatch(/<GridAttachEntry /);
  });
  it('분기가 없으면 기존 동작 — 등록 실패 모의 ＋ 빈 닫기의 `UploadModal` 그대로', () => {
    expect(AUDIT).toContain("register: async () => { throw new Error('시각 검수 전용: 저장하지 않습니다'); },");
    expect(AUDIT).toContain('<UploadModal sources={sources} onClose={() => {}} />');
  });
  it('`scenes.json` 에 등록 성공 장면 1 · 기존 upload 장면 질의 불변', () => {
    const scenes = JSON.parse(raw('scripts/visual-baseline/scenes.json')) as {
      scenes: { name: string; entry: string; query: Record<string, string> }[];
    };
    const ok = scenes.scenes.filter((s) => s.query.register === 'ok');
    expect(ok.length).toBe(1);
    expect(ok[0]?.entry).toBe('audit-upload.html');
    const plain = scenes.scenes.filter((s) => s.entry === 'audit-upload.html' && s.query.register !== 'ok');
    expect(plain.map((s) => s.name)).toEqual(['upload', 'upload-classify', 'upload-metadata', 'upload-link']);
    for (const s of plain) expect(s.query).toEqual({});
  });
});
