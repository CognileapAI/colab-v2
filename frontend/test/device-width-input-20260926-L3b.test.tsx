/**
 * 휴대폰·패드 대응 20260926 L3b — 업로드 터치 문구 · 체크 칸 · 대표 라디오 누름 칸.
 *
 * 오라클 = `dev-package/prd/specs/S-DEVICE-WIDTH-INPUT-20260926.md` V7(체크 칸 2 · 부록 B 36 · 45) ·
 * V11(파일 올리기 안내 = 기존 「파일 고르기」 경로) · V12(업로드 문구) · 우려 2ⓐ(칸 전체를 감싸는 label ·
 * 터치 칸 높이 44 · 마우스 모양 불변) · 우려 9ⓐ(터치 문구에 폴더 없음) · 「새 문구안」 3–5(확정 · 원문 그대로) ·
 * 구현 결정 「문구」(새 터치 문구는 부품 안 마우스 문구 상수 바로 옆 · `toastCopy` 불변) · 「레인 확정」 파일 끝 터치 블록.
 * 입력 방식 훅은 L3a 와 같은 모듈 모의로 터치 · 마우스 두 갈래를 그린다. 마우스 갈래는 대상 요소 수를 먼저 센다
 * (green-by-skip 방지). jsdom 은 배치를 재지 않는다 — 44 높이 · 1440 픽셀 · 세로 넘침은 캡처 수치(레인 보고)가 근거다.
 */
// @ts-expect-error — 타입 선언 없이 런타임만 쓴다(선례 device-width-input-20260926-L2b · vitest css 스텁은 `?raw` 도 빈 문자열).
import { readFileSync } from 'node:fs';
// @ts-expect-error — 같은 이유.
import { resolve } from 'node:path';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import * as dropCard from '../src/components/upload/FileDropCard';
import { FileDropCard } from '../src/components/upload/FileDropCard';
import * as uploadModal from '../src/components/upload/UploadModal';
import { UploadEntry } from '../src/components/upload/UploadEntry';
import * as copy from '../src/components/common/toastCopy';
import { SessionProvider } from '../src/permission/session';
import { MemberPermissionGrid } from '../src/components/members/MemberPermissionGrid';
import type { MembersPort } from '../src/components/members/port';
import { PERMISSION_SWITCHES, type LabMember } from '../src/components/members/permissions';
import { VariableTable, type VariableRow } from '../src/components/common/VariableTable';
import type { CurrentAccount } from '../src/api/client';
import type { LineageSource, LineageSuggestionResponse } from '../src/components/lineage/types';
import type {
  IncompleteTransferItem,
  PreviewSource,
  ProjectSource,
  UploadSource,
  UploadSources,
} from '../src/components/upload/types';
import { researcher } from './factories';

declare const process: { cwd(): string };
const raw = (rel: string): string => String(readFileSync(resolve(process.cwd(), rel), 'utf8'));

const mode = vi.hoisted(() => ({ current: 'mouse' as 'touch' | 'mouse' }));
vi.mock('../src/components/common/useInputMode', () => ({ useInputMode: () => mode.current }));

afterEach(() => {
  mode.current = 'mouse';
});

/* ═══ 확정 문구(「새 문구안」 3–5 · 원문 그대로) · 마우스 원문(변경 없음) ═══════════════ */
const TITLE_TOUCH = '눌러서 파일을 고르세요';
const SUB_TOUCH = '여러 개를 한 번에 고를 수 있어요';
const RESUME_TOUCH = '같은 파일을 다시 고르면 남은 조각부터 이어서 올라가요.';
const TITLE_MOUSE = '파일을 끌어다 놓으세요';
const SUB_MOUSE = '여러 개를 한 번에, 폴더째 끌어다 놓아도 돼요';
const RESUME_MOUSE = '같은 파일을 다시 끌어다 놓으면 남은 조각부터 이어서 올라가요.';
const PICK_BUTTON = '파일 고르기';

/* ═══ 1. 문구 자리(구현 결정 「문구」 · advisor ① 1) ═══════════════════════════════════ */
describe('문구 상수 — 부품 안 마우스 문구 상수 바로 옆 · 등록부(toastCopy) 불변', () => {
  const sources = import.meta.glob('../src/**/*.{ts,tsx}', {
    query: '?raw',
    import: 'default',
    eager: true,
  }) as Record<string, string>;
  const quoted = (text: string) => {
    const esc = text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    return new RegExp(`(['"\`])${esc}\\1|>\\s*${esc}\\s*<`);
  };
  const PAIRS: { home: string; mouse: string; touch: string; mouseName: string; touchName: string }[] = [
    { home: 'components/upload/FileDropCard.tsx', mouse: TITLE_MOUSE, touch: TITLE_TOUCH, mouseName: 'DROP_TITLE', touchName: 'DROP_TITLE_TOUCH' },
    { home: 'components/upload/FileDropCard.tsx', mouse: SUB_MOUSE, touch: SUB_TOUCH, mouseName: 'DROP_SUB', touchName: 'DROP_SUB_TOUCH' },
    { home: 'components/upload/UploadModal.tsx', mouse: RESUME_MOUSE, touch: RESUME_TOUCH, mouseName: 'RESUME_HINT', touchName: 'RESUME_HINT_TOUCH' },
  ];

  it('대상 = 3쌍(업로드 드롭 영역 2 · 이어 올리기 안내 1) · 원천 파일 수 > 50', () => {
    expect(PAIRS.length).toBe(3);
    expect(Object.keys(sources).length).toBeGreaterThan(50);
  });

  for (const p of PAIRS) {
    it(`${p.touchName} = 「${p.touch}」 — ${p.home} 한 곳 · ${p.mouseName} 바로 다음 줄`, () => {
      const exported = { ...dropCard, ...uploadModal } as Record<string, unknown>;
      expect(exported[p.mouseName]).toBe(p.mouse);
      expect(exported[p.touchName]).toBe(p.touch);
      for (const text of [p.mouse, p.touch]) {
        const homes = Object.entries(sources).filter(([, src]) => quoted(text).test(src)).map(([path]) => path);
        expect(homes, text).toEqual([`../src/${p.home}`]);
      }
      const lines = (sources[`../src/${p.home}`] ?? '').split('\n');
      const at = (name: string) => lines.findIndex((l) => l.startsWith(`export const ${name} =`));
      expect(at(p.mouseName)).toBeGreaterThanOrEqual(0);
      expect(at(p.touchName) - at(p.mouseName)).toBe(1);
    });
  }

  it('등록부 `toastCopy` 에 새 문구 0 · 중복 문자열 검사 대상(FIXED_COPY)과 겹침 0', () => {
    const home = Object.entries(sources).find(([path]) => path.endsWith('common/toastCopy.ts'))?.[1] ?? '';
    expect(home.length).toBeGreaterThan(0);
    for (const text of [TITLE_TOUCH, SUB_TOUCH, RESUME_TOUCH]) {
      expect(home).not.toContain(text);
      expect(copy.FIXED_COPY as readonly string[]).not.toContain(text);
    }
  });
});

/* ═══ 2. 드롭 영역 문구(V12 · 우려 9ⓐ · V11) ═════════════════════════════════════════ */
function drawDrop() {
  render(<FileDropCard picked={[]} onPick={vi.fn()} onKind={vi.fn()} onRemove={vi.fn()} />);
  const zone = screen.getByTestId('up-drop');
  const one = (sel: string) => {
    const found = zone.querySelectorAll(sel);
    expect(found.length, sel).toBe(1);
    return found[0] as HTMLElement;
  };
  return { zone, title: one('.big'), sub: one('.muted'), pick: one('.up-file-choose'), input: one('input[type=file]') };
}

describe('업로드 드롭 영역 — 입력 방식별 문구', () => {
  it('터치: 제목 「눌러서 파일을 고르세요」 · 보조 줄 「여러 개를 한 번에 고를 수 있어요」 · 폴더 · 끌어다 문구 0', () => {
    mode.current = 'touch';
    const { zone, title, sub, pick, input } = drawDrop();
    expect(title.textContent).toBe(TITLE_TOUCH);
    expect(sub.textContent).toBe(SUB_TOUCH);
    expect(zone.textContent).not.toContain('폴더');
    expect(zone.textContent).not.toContain('끌어다');
    // V11 — 파일 올리기 안내는 기존 「파일 고르기」 경로 그대로(여러 개 고르기 유지).
    expect(pick.textContent).toBe(PICK_BUTTON);
    expect(input).toHaveAttribute('multiple');
  });

  it('마우스(판별 불가 포함): 제목 · 보조 줄 원문 그대로 · 「파일 고르기」 그대로', () => {
    mode.current = 'mouse';
    const { title, sub, pick, input } = drawDrop();
    expect(title.textContent).toBe(TITLE_MOUSE);
    expect(sub.textContent).toBe(SUB_MOUSE);
    expect(pick.textContent).toBe(PICK_BUTTON);
    expect(input).toHaveAttribute('multiple');
  });
});

/* ═══ 3. 이어 올리기 안내(V12) — 진입 컴포넌트 실물(선례 unfinished-uploads #33 ㉠) ═══════════ */
const LAB = '01JYZ9K7WQ3N8V4M2X6C5B0LB1';
const T1 = '01JYZ9K7WQ3N8V4M2X6C5B0TR1';

function account(): CurrentAccount {
  return {
    accountId: 'A1', name: '호랑이', email: 't@e.ac.kr', role: '연구원',
    labId: LAB, labName: '수자원순환연구실', permissions: { '업로드·편집': true },
  } as CurrentAccount;
}

const ITEM: IncompleteTransferItem = {
  uploadId: T1, sourceLabel: '기상 폴더', uploadedFiles: 3, plannedFiles: 8,
  uploadedBytes: 300, plannedBytes: 800, createdAt: 'x', expiresAt: 'y',
};

function modalSources(): UploadSources {
  const upload = {
    create: vi.fn(), register: vi.fn(), attachGrid: vi.fn(),
    incomplete: async () => [ITEM],
    status: async () => { throw new Error('없음'); },
  } as unknown as UploadSource;
  const preview: PreviewSource = {
    async palettes() { return [{ palette: 'viridis', label: '비리디스' }]; },
    async createRender() { return { renderId: 'R1', status: '그리는 중', stage: '파일 읽는 중' } as never; },
    async getRender() { return { renderId: 'R1', status: '그리는 중', stage: '파일 읽는 중' } as never; },
  };
  const projects: ProjectSource = {
    async list() { return []; },
    async create(body) { return { projectId: 'P9', name: body.name, type: body.type }; },
  };
  const lineage: LineageSource = {
    async suggestions() {
      return {
        degraded: false,
        scope: { labId: LAB, labName: '수자원순환연구실', searchedCount: 0 },
        rawDataLikely: false,
        suggestions: [],
      } as LineageSuggestionResponse;
    },
    async candidates() { return []; },
  };
  return { upload, preview, projects, lineage };
}

async function drawResumeHint(): Promise<HTMLElement> {
  render(
    <MemoryRouter initialEntries={['/datasets']}>
      <SessionProvider account={account()}>
        <UploadEntry sources={modalSources()} openRequest={{ seq: 1, resumeUploadId: T1 }} />
      </SessionProvider>
    </MemoryRouter>,
  );
  await screen.findByTestId('upload-modal');
  await waitFor(() => expect(screen.getAllByTestId('up-resume-hint').length).toBe(1));
  return screen.getByTestId('up-resume-hint');
}

describe('이어 올리기 안내 — 입력 방식별 문구', () => {
  it('터치: 「같은 파일을 다시 고르면 남은 조각부터 이어서 올라가요.」', async () => {
    mode.current = 'touch';
    const hint = await drawResumeHint();
    expect(hint.textContent).toBe(RESUME_TOUCH);
    expect(hint).toHaveClass('ub-hint');
  });

  it('마우스: 원문 그대로', async () => {
    mode.current = 'mouse';
    const hint = await drawResumeHint();
    expect(hint.textContent).toBe(RESUME_MOUSE);
    expect(hint).toHaveClass('ub-hint');
  });
});

/* ═══ 4. 칸 전체를 감싸는 label(우려 2ⓐ · 부록 B 36 · 45) ═════════════════════════════════ */
const ACTIVE_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AH2';
const OTHER_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AH4';

function members(): LabMember[] {
  const on = { '업로드·편집': true, '프로젝트 생성': true, '승인 위임': false, '연구실 설정': false };
  return [
    { ...researcher(ACTIVE_ID, '호랑이', { ...on }), accountStatus: 'active', editablePermissions: [...PERMISSION_SWITCHES] },
    { ...researcher(OTHER_ID, '두루미', { ...on }), accountStatus: 'active', editablePermissions: [...PERMISSION_SWITCHES] },
  ];
}

async function drawGrid() {
  const items = members();
  const port: MembersPort = { list: async () => ({ ok: true, items }), save: vi.fn(async () => ({ ok: true as const, items })) };
  render(<MemberPermissionGrid port={port} />);
  await screen.findByRole('table');
}

/** label 계약 — 입력 하나만 감싸고 글자 0 · 이름은 입력의 `aria-label` 이 진다. */
function expectWrapped(input: HTMLInputElement, cellMatch: (td: HTMLElement) => boolean) {
  const label = input.parentElement as HTMLElement;
  expect(label.tagName).toBe('LABEL');
  expect(label.textContent).toBe('');
  expect(label.children.length).toBe(1);
  expect(label.hasAttribute('for')).toBe(false);
  expect(label.hasAttribute('aria-label')).toBe(false);
  const td = label.parentElement as HTMLElement;
  expect(td.tagName).toBe('TD');
  expect(td.children.length).toBe(1);
  expect(cellMatch(td)).toBe(true);
  return label;
}

describe('구성원 권한 체크 칸(36) — 칸을 감싸는 label', () => {
  for (const m of ['touch', 'mouse'] as const) {
    it(`${m}: 체크 칸 8(2명 × 4열) 모두 label 안 · 글자 0 · 이름 = aria-label 「{이름} · {열}」`, async () => {
      mode.current = m;
      await drawGrid();
      const boxes = screen.getAllByRole('checkbox') as HTMLInputElement[];
      expect(boxes.length).toBe(2 * PERMISSION_SWITCHES.length);
      for (const box of boxes) {
        expectWrapped(box, (td) => td.classList.contains('pc'));
        const name = box.getAttribute('aria-label') ?? '';
        expect(name).toMatch(/ · /);
        expect(screen.getByRole('checkbox', { name })).toBe(box);
      }
    });
  }

  it('한 번 누르면 바뀜 한 번(label 을 눌러도 · 체크 칸을 눌러도 · 두 번 불리면 되돌아간다)', async () => {
    await drawGrid();
    fireEvent.click(screen.getByRole('button', { name: '권한 편집' }));
    const box = screen.getByRole('checkbox', { name: '호랑이 · 승인 위임' }) as HTMLInputElement;
    const label = box.parentElement as HTMLElement;
    expect(label.tagName).toBe('LABEL');
    expect(box.checked).toBe(false);
    fireEvent.click(label);
    expect(box.checked).toBe(true);
    expect(box.closest('td')).toHaveClass('is-chg');
    fireEvent.click(box);
    expect(box.checked).toBe(false);
    expect(box.closest('td')).not.toHaveClass('is-chg');
    const other = screen.getByRole('checkbox', { name: '두루미 · 승인 위임' }) as HTMLInputElement;
    expect(other.checked).toBe(false);
  });
});

describe('변수 표 대표 라디오(45) — 칸을 감싸는 label', () => {
  const rows = (): VariableRow[] => [
    { name: 'tp', unit: 'mm', valueRange: null, missingRate: null, representative: true },
    { name: 't2m', unit: 'K', valueRange: null, missingRate: null, representative: false },
  ];

  for (const m of ['touch', 'mouse'] as const) {
    it(`${m}: 편집 · 읽기 전용 모두 라디오 2 가 label 안 · 글자 0 · 이름 = 「대표 {n}」`, () => {
      mode.current = m;
      const edit = render(<VariableTable rows={rows()} onRows={vi.fn()} />);
      const radios = within(edit.container).getAllByRole('radio') as HTMLInputElement[];
      expect(radios.length).toBe(2);
      radios.forEach((r, i) => {
        expectWrapped(r, (td) => td.querySelector('input[type=radio]') === r);
        expect(within(edit.container).getByRole('radio', { name: `대표 ${i + 1}` })).toBe(r);
      });
      edit.unmount();
      const ro = render(<VariableTable rows={rows()} />);
      const roRadios = within(ro.container).getAllByRole('radio') as HTMLInputElement[];
      expect(roRadios.length).toBe(2);
      for (const r of roRadios) {
        expectWrapped(r, (td) => td.querySelector('input[type=radio]') === r);
        expect(r).toBeDisabled();
      }
    });
  }

  it('label 을 한 번 누르면 onRows 한 번 · 라디오를 한 번 누르면 onRows 한 번(두 번 불림 0)', () => {
    const onRows = vi.fn();
    render(<VariableTable rows={rows()} onRows={onRows} />);
    const second = screen.getByRole('radio', { name: '대표 2' }) as HTMLInputElement;
    const label = second.parentElement as HTMLElement;
    expect(label.tagName).toBe('LABEL');
    fireEvent.click(label);
    expect(onRows).toHaveBeenCalledTimes(1);
    expect((onRows.mock.calls[0]?.[0] as VariableRow[]).map((r) => r.representative)).toEqual([false, true]);
    fireEvent.click(second);
    expect(onRows).toHaveBeenCalledTimes(2);
  });
});

/* ═══ 5. CSS — 마우스 기본 규칙 · 파일 끝 터치 블록(원문 CSS · 선례 L2b 파서) ═══════════════ */
const strip = (css: string): string => css.replace(/\/\*[\s\S]*?\*\//g, '');
type Rule = { selectors: string[]; decls: string[]; media: string };
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
    else if (!head.startsWith('@')) {
      out.push({
        selectors: head.split(',').map((s) => s.trim().replace(/\s+/g, ' ')),
        decls: inner.split(';').map((d) => d.trim().replace(/\s*:\s*/, ': ')).filter(Boolean),
        media,
      });
    }
    i = j;
  }
  return out;
}

const COARSE = '@media (pointer: coarse)';
const CONTROL = 'var(--control-height)';
const LABEL_CSS: { n: number; file: string; css: string; sel: string }[] = [
  { n: 36, file: 'members.css', css: raw('src/components/members/members.css'), sel: '.memtbl td.pc > label' },
  { n: 45, file: 'variableTable.css', css: raw('src/components/common/variableTable.css'), sel: '.vartable td > label' },
];

describe('누름 칸 CSS — label 이 칸을 채움(마우스 모양 불변) · 터치 44', () => {
  it('대상 2(36 · 45) · 두 파일', () => {
    expect(LABEL_CSS.map((t) => t.n)).toEqual([36, 45]);
    for (const t of LABEL_CSS) expect(rules(strip(t.css)).length, t.file).toBeGreaterThan(5);
  });
  for (const t of LABEL_CSS) {
    it(`${t.n} ${t.file}: 조건 없는 \`${t.sel} { display: block }\` 하나`, () => {
      const base = rules(strip(t.css)).filter((r) => r.media === '' && r.selectors.includes(t.sel));
      expect(base.length).toBe(1);
      expect(base[0]?.selectors).toEqual([t.sel]);
      expect(base[0]?.decls).toEqual(['display: block']);
    });
    it(`${t.n} ${t.file}: 터치 블록 \`${t.sel}\` → 최소 높이 · 최소 가로 ${CONTROL} · 가운데 정렬 · 글자 선언 0`, () => {
      const coarse = rules(strip(t.css)).filter((r) => r.media === COARSE && r.selectors.includes(t.sel));
      expect(coarse.length).toBe(1);
      expect(coarse[0]?.selectors).toEqual([t.sel]);
      expect(coarse[0]?.decls).toEqual([
        'display: flex',
        'align-items: center',
        'justify-content: center',
        `min-height: ${CONTROL}`,
        `min-width: ${CONTROL}`,
      ]);
    });
    it(`${t.n} ${t.file}: label 을 고르는 규칙 = 위 둘뿐 · 다른 매체 조건 0`, () => {
      const all = rules(strip(t.css)).filter((r) => r.selectors.some((s) => /(^|[\s>])label\b/.test(s)));
      expect(all.map((r) => r.media).sort()).toEqual(['', COARSE]);
    });
  }
});
