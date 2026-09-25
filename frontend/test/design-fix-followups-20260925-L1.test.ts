/**
 * design-fix 후속 20260925 · L1(CSS · 문서) — CSS · 정본 문장 계측 시험.
 *
 * 오라클 = `dev-package/prd/specs/S-DESIGN-FIX-FOLLOWUPS-20260925.md` 부록 C 「L1」 표 ＋ 부록 F.
 * 판정 = `dev-package/intent/2026-09-25-design-fix-followups.md` 설계트리 Q1a–Q1f · Q3a · Q3c · Q5 · Q8b.
 * 방식은 `design-fix-20260924-F-css.test.ts` 와 같다 — CSS 원문에서 주석을 걷고 선택자 블록을 잘라 잰다
 * (jsdom 은 스타일을 계산하지 않는다). 대비는 WCAG 상대휘도 · 라이트 = `:root` · 다크 = `:root[data-theme="dark"]`.
 * green-by-skip 방지: 대상 목록 길이를 먼저 단언하고, 선택자 블록을 못 찾으면 빈 문자열이 아니라 실패한다.
 */
// @ts-expect-error — 타입 선언 없이 런타임만 쓴다(vitest 는 node 위에서 돈다 · 선례와 같은 규율).
import { readFileSync } from 'node:fs';
// @ts-expect-error — 같은 이유.
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

declare const process: { cwd(): string };

const raw = (rel: string): string => String(readFileSync(resolve(process.cwd(), rel), 'utf8'));
const strip = (css: string): string => css.replace(/\/\*[\s\S]*?\*\//g, '');
const read = (rel: string): string => strip(raw(rel));

const TOKENS = read('src/shell/tokens.css');
const PRIM = read('src/shell/primitives.css');
const SHELL = read('src/shell/shell.css');
const LOGIN = read('src/auth/login.css');
const DELETION = read('src/components/detail/deletion.css');
const DASH = read('src/components/dashboard/dashboard.css');
const PREVIEW = read('src/components/preview/preview.css');
const PROJECT = read('src/components/project/project.css');
const LINEAGE = read('src/components/lineage/lineage.css');
const DOC = raw('../docs/design-system.md');
const SKILL = raw('../.agents/skills/design-review/SKILL.md');

// ── 규칙 파서(F-css 시험과 같은 규칙) ─────────────────────────────────────
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
    else if (head.startsWith('@')) {
      /* @keyframes · @starting-style — 계측 밖 */
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

function bodies(css: string, selector: string, media = ''): string[] {
  return rules(css)
    .filter((r) => r.media === media && r.selectors.includes(selector))
    .map((r) => r.body);
}

function body(css: string, selector: string, media = ''): string {
  const found = bodies(css, selector, media);
  expect(found.length, `선택자 블록 수: ${selector} ${media}`).toBe(1);
  return found[0] ?? '';
}

function decls(b: string): string[] {
  return b
    .split(';')
    .map((d) => d.trim().replace(/\s+/g, ' '))
    .filter(Boolean);
}

/** 본문에서 속성 하나의 값(마지막 선언). */
function prop(b: string, name: string): string | undefined {
  let v: string | undefined;
  for (const d of decls(b)) {
    const at = d.indexOf(':');
    if (at > 0 && d.slice(0, at).trim() === name) v = d.slice(at + 1).trim();
  }
  return v;
}

/** 비활성 두 값만 있는 본문인가 — opacity 는 `.5` · `0.5` 표기 동치(spec 부록 C). */
function expectDisabledPair(b: string, label: string): void {
  const ds = decls(b);
  expect(ds.length, `${label} 선언 수`).toBe(2);
  expect(Number(prop(b, 'opacity')), `${label} opacity`).toBe(0.5);
  expect(prop(b, 'cursor'), `${label} cursor`).toBe('not-allowed');
  expect(b, `${label} !important`).not.toMatch(/!important/);
}

// ── 토큰 · 색 ────────────────────────────────────────────────────────────
function tokenMap(b: string): Map<string, string> {
  const m = new Map<string, string>();
  for (const d of decls(b)) {
    const at = d.indexOf(':');
    if (d.startsWith('--') && at > 0) m.set(d.slice(0, at).trim(), d.slice(at + 1).trim());
  }
  return m;
}
const LIGHT = tokenMap(
  rules(TOKENS).find((x) => x.media === '' && x.selectors.length === 1 && x.selectors[0] === ':root')?.body ?? '',
);
const DARK = tokenMap(rules(TOKENS).find((x) => x.selectors.includes(':root[data-theme="dark"]'))?.body ?? '');

type Theme = 'light' | 'dark';
const THEMES: Theme[] = ['light', 'dark'];

function resolveToken(name: string, theme: Theme, seen = 0): string {
  if (seen > 10) throw new Error(`순환: ${name}`);
  const v = (theme === 'dark' ? DARK.get(name) : undefined) ?? LIGHT.get(name);
  if (!v) throw new Error(`토큰 부재(${theme}): ${name}`);
  const m = v.match(/^var\((--[a-z0-9-]+)\)$/);
  return m?.[1] ? resolveToken(m[1], theme, seen + 1) : v;
}

type RGB = [number, number, number];
function parseHex(hex: string): RGB {
  const h = hex.replace('#', '');
  if (!/^[0-9a-fA-F]{6}$/.test(h)) throw new Error(`불투명 hex 아님: ${hex}`);
  return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16)) as RGB;
}
function lum(c: RGB): number {
  const lin = c.map((x) => {
    const v = x / 255;
    return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
  }) as RGB;
  return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2];
}
function tokenRatio(fg: string, bg: string, theme: Theme): number {
  const a = lum(parseHex(resolveToken(fg, theme)));
  const b = lum(parseHex(resolveToken(bg, theme)));
  return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
}

// ── 대상 목록 ────────────────────────────────────────────────────────────
/** btn 밖 비활성 자리 중 L1 몫(Q1e) — [파일 이름, CSS, `:disabled` 선택자]. */
const DISABLED_L1: [string, string, string][] = [
  ['dashboard.css', DASH, '.titem button:disabled'],
  ['dashboard.css', DASH, '.dash-section-label:disabled'],
  ['preview.css', PREVIEW, '.pv-zoom button:disabled'],
  ['project.css', PROJECT, '.pj-x:disabled'],
];
/** 파란 채움 누름 중 L1 몫(Q3a) — `.btn-strong` 은 L2. */
const PRESS_L1: [string, string, string][] = [
  ['primitives.css', PRIM, '.btn-primary:active'],
  ['shell.css', SHELL, '.gnb-upload:active'],
];
const COARSE = '@media (pointer: coarse)';

// ── 시험 ─────────────────────────────────────────────────────────────────

describe('대상 개수(green-by-skip 방지)', () => {
  it('L1 비활성 대상 선택자 = 4 · 파란 채움 누름 = 2', () => {
    expect(DISABLED_L1.length).toBe(4);
    expect(PRESS_L1.length).toBe(2);
  });
});

describe('V1 · Q1a · Q1b — 단추 프리미티브 비활성', () => {
  it('`primitives.css` `.btn:disabled` 블록 1개 = opacity .5 · cursor not-allowed', () => {
    expectDisabledPair(body(PRIM, '.btn:disabled'), '.btn:disabled');
  });
  it('primitives.css 에 `!important` 0', () => {
    expect(PRIM).not.toMatch(/!important/);
  });
  it('기존 hover 비활성 제외 원문 불변', () => {
    const src = raw('src/shell/primitives.css');
    expect(src).toContain('.btn:where(:not(.btn-primary, :disabled)):hover { background: var(--color-gray-50); }');
    expect(src).toContain('.btn-primary:where(:not(:disabled)):hover { background: var(--color-primary-700); }');
  });
});

describe('V1 · Q1c — 로그인 제출 비활성 = 같은 두 값', () => {
  it('`.login-submit:disabled` = opacity .5 · cursor not-allowed(회색 채움 · default 커서 0)', () => {
    const b = body(LOGIN, '.login-submit:disabled');
    expectDisabledPair(b, '.login-submit:disabled');
    expect(prop(b, 'background')).toBeUndefined();
    expect(b).not.toContain('cursor: default');
  });
});

describe('V1 · Q1d — 상세 삭제 단추 겹치는 규칙 삭제', () => {
  it('`deletion.css` 에 `:disabled` 0', () => {
    expect(DELETION).not.toContain(':disabled');
  });
});

describe('V1 · Q1e — btn 밖 비활성 자리(L1 몫 4)', () => {
  for (const [file, css, sel] of DISABLED_L1) {
    it(`${file} \`${sel}\` = opacity .5 · cursor not-allowed`, () => {
      expectDisabledPair(body(css, sel), sel);
    });
  }
});

describe('V2 · Q3a — 파란 채움 누름 = primary-800', () => {
  for (const [file, css, sel] of PRESS_L1) {
    it(`${file} \`${sel}\` 배경 = var(--color-primary-800)`, () => {
      expect(prop(body(css, sel), 'background')).toBe('var(--color-primary-800)');
    });
  }
  for (const theme of THEMES) {
    it(`on-primary 대 primary-800 대비 ≥ 4.5(${theme})`, () => {
      expect(tokenRatio('--color-on-primary', '--color-primary-800', theme)).toBeGreaterThanOrEqual(4.5);
    });
  }
  it('primitives.css 주석에 「primary 는 primary-700 유지」 0(값과 어긋난 주석 · spec 위험 9)', () => {
    expect(raw('src/shell/primitives.css')).not.toContain('primary 는 primary-700 유지');
  });
});

describe('V3 · Q3c — 터치가 주 입력인 기기(`pointer: coarse`) 하한', () => {
  it('`tokens.css` 에 `@media (pointer: coarse)` 블록 1 · 안의 선언 = `--control-height: 44px` 1개', () => {
    const blocks = rules(TOKENS).filter((r) => r.media === COARSE);
    expect(blocks.length).toBe(1);
    expect(blocks[0]?.selectors).toEqual([':root']);
    expect(decls(blocks[0]?.body ?? '')).toEqual(['--control-height: 44px']);
  });
  it('기본 `:root` `--control-height` = 40px 불변', () => {
    expect(LIGHT.get('--control-height')).toBe('40px');
  });
  it('640px 블록 원문 불변(여백 토큰 3 ＋ 44px)', () => {
    expect(decls(body(TOKENS, ':root', '@media (max-width: 640px)'))).toEqual([
      '--space-page: 16px',
      '--space-card: 20px',
      '--space-section: 20px',
      '--control-height: 44px',
    ]);
  });
  it('`.btn-sm` 하한 블록 매체 조건에 `(max-width: 640px)` 와 `(pointer: coarse)` 둘 다', () => {
    const sized = rules(PRIM).filter((r) => r.media !== '' && r.selectors.includes('.btn-sm'));
    expect(sized.length).toBe(1);
    expect(sized[0]?.media).toContain('(max-width: 640px)');
    expect(sized[0]?.media).toContain('(pointer: coarse)');
    expect(decls(sized[0]?.body ?? '')).toEqual(['min-height: var(--control-height)']);
  });
  it('tokens.css 머리 주석 구조 문장에 coarse 분기가 있다(spec 위험 9)', () => {
    const lines = raw('src/shell/tokens.css').split('\n');
    const at = lines.findIndex((l) => l.includes('구조:'));
    expect(at).toBeGreaterThanOrEqual(0);
    // 구조 문장은 두 줄에 걸친다(이어지는 줄까지 본다).
    expect(`${lines[at]} ${lines[at + 1] ?? ''}`).toContain('(pointer: coarse)');
  });
});

describe('V8 · Q1f · Q1d · Q3a · Q5 — 정본 기록', () => {
  const EXEMPT = '비활성(`:disabled`) 컨트롤은 합격선 밖 — WCAG 1.4.3 · 1.4.11 비활성 예외';
  const section = (head: string): string => {
    const from = DOC.indexOf(`\n## ${head}`);
    expect(from, `절 부재: ${head}`).toBeGreaterThanOrEqual(0);
    const to = DOC.indexOf('\n## ', from + 1);
    return DOC.slice(from, to < 0 ? undefined : to);
  };
  it('docs/design-system.md 합격선 줄에 비활성 예외', () => {
    const lines = DOC.split('\n').filter((l) => l.includes('대비 4.5:1 이상'));
    expect(lines.length).toBe(1);
    expect(lines[0]).toContain(EXEMPT);
  });
  it('design-review SKILL §0 정적 합격선 행에 같은 비활성 예외', () => {
    const lines = SKILL.split('\n').filter((l) => l.startsWith('| 정적 합격선'));
    expect(lines.length).toBe(1);
    expect(lines[0]).toContain(EXEMPT);
  });
  it('btn 행 수식자에 `disabled`(opacity .5 · cursor not-allowed) · 작은 단추 터치 조건', () => {
    const rows = DOC.split('\n').filter((l) => l.startsWith('| btn |') && l.includes('<button class="btn"'));
    expect(rows.length).toBe(1);
    expect(rows[0]).toContain('`disabled`(opacity .5 · cursor not-allowed)');
    expect(rows[0]).toContain('640px 이하 또는 터치가 주 입력인 기기에서는 `--control-height`');
  });
  it('누름 규칙 줄 = 파란 채움 primary-800 · primary-700 0 · 바로 다음 줄 = 비활성 규칙', () => {
    const lines = section('⑤').split('\n');
    const at = lines.findIndex((l) => l.startsWith('- 누름 피드백'));
    expect(at).toBeGreaterThanOrEqual(0);
    expect(lines[at]).toContain('파란 채움은 primary-800');
    expect(lines[at]).not.toContain('primary-700');
    expect(lines[at + 1] ?? '').toContain('비활성 = opacity .5 · cursor not-allowed');
  });
  it('⑦ 시각 값 표 17 행 = 빨간 삭제 단추 hover · 누름 없음', () => {
    const s = section('⑦');
    const table = s.slice(s.indexOf('### 시각 값'), s.indexOf('\n### ', s.indexOf('### 시각 값') + 1));
    const rows = table.split('\n').filter((l) => l.startsWith('| 17 |'));
    expect(rows.length).toBe(1);
    expect(rows[0]).toContain('빨간 삭제 단추 hover · 누름 없음');
    expect(rows[0]).toContain('`.btn-danger`');
  });
  it('③ 편차 칸 `.detail-page .btn-danger(:disabled)` 0', () => {
    expect(DOC).not.toContain('.btn-danger(:disabled)');
    expect(DOC).toContain('`.detail-page .btn-danger`');
  });
});

describe('V9 · Q8b — 계보 죽은 규칙 삭제', () => {
  it('`lineage.css` 에 `.lin-unknown-why` 0', () => {
    expect(LINEAGE).not.toContain('.lin-unknown-why');
  });
});
