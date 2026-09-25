/**
 * design-fix 20260924 · L1(CSS 공통·화면) — CSS 계측 시험.
 *
 * 오라클 = `dev-package/prd/specs/S-DESIGN-FIX-20260924.md` §4 「L1」 ＋ 「확정 값」(값 8–18 · Ted 2026-09-25).
 * 판정표 = `dev-package/sessions/design-review-20260924.md` §7 · §8.
 * 선례 `design-fix-20260908.test.ts` 처럼 CSS 원문에서 주석을 걷고 선택자 블록을 잘라 잰다
 * (jsdom 은 스타일을 계산하지 않는다). 대비는 WCAG 상대휘도 · 라이트 = `:root` · 다크 = `:root[data-theme="dark"]`.
 */
// @ts-expect-error — 타입 선언 없이 런타임만 쓴다(vitest 는 node 위에서 돈다 · 선례와 같은 규율).
import { readFileSync, readdirSync, statSync } from 'node:fs';
// @ts-expect-error — 같은 이유.
import { join, resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

declare const process: { cwd(): string };

const raw = (rel: string): string => String(readFileSync(resolve(process.cwd(), rel), 'utf8'));
const strip = (css: string): string => css.replace(/\/\*[\s\S]*?\*\//g, '');
const read = (rel: string): string => strip(raw(rel));

const TOKENS = read('src/shell/tokens.css');
const PRIM = read('src/shell/primitives.css');
const SHELL = read('src/shell/shell.css');
const CATALOG = read('src/components/catalog/catalog.css');
const DETAIL = read('src/components/detail/detail.css');
const LOGIN = read('src/auth/login.css');

// ── 규칙 파서 ─────────────────────────────────────────────────────────────
type Rule = { selectors: string[]; body: string; media: string };

/** 주석 걷은 CSS 를 규칙 목록으로 편다. `@layer` 는 투명, `@media` 는 조건을 달아 준다. */
function rules(css: string, media = ''): Rule[] {
  const out: Rule[] = [];
  let i = 0;
  while (i < css.length) {
    const open = css.indexOf('{', i);
    if (open < 0) break;
    const head = css.slice(i, open).trim();
    // 짝 닫는 괄호
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
      /* @keyframes · @starting-style 등 — L1 계측 밖 */
    } else {
      out.push({ selectors: splitList(head), body: inner.trim(), media });
    }
    i = j;
  }
  return out;
}

/** 선택자 목록을 괄호 밖 쉼표로 가른다. */
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

/** 선택자 하나(목록 원소 정확 일치)의 규칙 본문들. 미디어 조건을 주면 그 조건만. */
function bodies(css: string, selector: string, media = ''): string[] {
  return rules(css)
    .filter((r) => r.media === media && r.selectors.includes(selector))
    .map((r) => r.body);
}

/** 선택자 하나의 본문 — 정확히 하나여야 한다. */
function body(css: string, selector: string, media = ''): string {
  const found = bodies(css, selector, media);
  expect(found.length, `선택자 블록 수: ${selector} ${media}`).toBe(1);
  return found[0] ?? '';
}

/** 본문 → 정규화된 선언 목록(`prop: value`). */
function decls(b: string): string[] {
  return b
    .split(';')
    .map((d) => d.trim().replace(/\s+/g, ' '))
    .filter(Boolean);
}

// ── 대비 ─────────────────────────────────────────────────────────────────
function lightRoot(): string {
  const r = rules(TOKENS).find((x) => x.media === '' && x.selectors.length === 1 && x.selectors[0] === ':root');
  if (!r) throw new Error('라이트 :root 부재');
  return r.body;
}
function darkRoot(): string {
  const r = rules(TOKENS).find((x) => x.selectors.includes(':root[data-theme="dark"]'));
  if (!r) throw new Error('다크 블록 부재');
  return r.body;
}
function tokenMap(b: string): Map<string, string> {
  const m = new Map<string, string>();
  for (const d of decls(b)) {
    const at = d.indexOf(':');
    if (d.startsWith('--') && at > 0) m.set(d.slice(0, at).trim(), d.slice(at + 1).trim());
  }
  return m;
}
const LIGHT = tokenMap(lightRoot());
const DARK = tokenMap(darkRoot());

/** 토큰 → 색 문자열(var 사슬 해소 · 다크는 없으면 라이트 값). */
function resolveToken(name: string, theme: 'light' | 'dark', seen = 0): string {
  if (seen > 10) throw new Error(`순환: ${name}`);
  const v = (theme === 'dark' ? DARK.get(name) : undefined) ?? LIGHT.get(name);
  if (!v) throw new Error(`토큰 부재(${theme}): ${name}`);
  const m = v.match(/^var\((--[a-z0-9-]+)\)$/);
  return m?.[1] ? resolveToken(m[1], theme, seen + 1) : v;
}

type RGBA = [number, number, number, number];
function parseHex(hex: string): RGBA {
  const h = hex.replace('#', '');
  if (!/^[0-9a-fA-F]{6}([0-9a-fA-F]{2})?$/.test(h)) throw new Error(`hex 아님: ${hex}`);
  const ch = [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16));
  const a = h.length === 8 ? parseInt(h.slice(6, 8), 16) / 255 : 1;
  return [ch[0] ?? 0, ch[1] ?? 0, ch[2] ?? 0, a];
}
/** 반투명 글자·면은 아래 면에 합성한다. */
function over(top: RGBA, under: RGBA): RGBA {
  const a = top[3];
  return [0, 1, 2].map((i) => (top[i] ?? 0) * a + (under[i] ?? 0) * (1 - a)).concat(1) as RGBA;
}
function lum(c: RGBA): number {
  const lin = [0, 1, 2].map((i) => {
    const v = (c[i] ?? 0) / 255;
    return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
  }) as [number, number, number];
  return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2];
}
function ratio(fg: RGBA, bg: RGBA): number {
  const a = lum(fg);
  const b = lum(bg);
  return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
}
/** 토큰 글자 대 토큰 면(반투명 면은 테마 바탕면 `--color-surface` 에 합성). */
function tokenRatio(fg: string, bg: string, theme: 'light' | 'dark'): number {
  const surface = parseHex(resolveToken('--color-surface', theme));
  const back = over(parseHex(resolveToken(bg, theme)), surface);
  const front = over(parseHex(resolveToken(fg, theme)), back);
  return ratio(front, back);
}

/** `var(--x)` 한 개짜리 값에서 토큰 이름을 꺼낸다. */
function varName(b: string, prop: string): string {
  const m = b.match(new RegExp(`(?:^|;|\\s)${prop}:\\s*var\\((--[a-z0-9-]+)\\)`));
  if (!m?.[1]) throw new Error(`${prop}: var() 부재`);
  return m[1];
}

// ── 시험 ─────────────────────────────────────────────────────────────────

describe('WU-A1 · 버튼 누름(값 14)', () => {
  it('plain · ghost · secondary 누름 = gray-100', () => {
    expect(decls(body(PRIM, '.btn:where(:not(.btn-primary)):active'))).toContain('background: var(--color-gray-100)');
  });
  it('`.btn-primary:active` = primary-800(design-fix 후속 20260925 Q3a · hover 보다 한 단 진한 값)', () => {
    expect(decls(body(PRIM, '.btn-primary:active'))).toEqual(['background: var(--color-primary-800)']);
  });
  it('primitives.css 에 `!important` 0', () => {
    expect(PRIM).not.toMatch(/!important/);
  });
});

describe('#9 · 기본·보조 단추 hover(값 10)', () => {
  // F-css A2 · A5 · A13 — 비활성 단추는 hover 에서 제외(`:where()` 로 특이도 무변).
  it('`.btn-primary:where(:not(:disabled)):hover` = primary-700', () => {
    expect(decls(body(PRIM, '.btn-primary:where(:not(:disabled)):hover'))).toContain('background: var(--color-primary-700)');
  });
  it('hover 제외 목록에 `.btn-secondary` 가 없다', () => {
    const hover = rules(PRIM).filter((r) => r.selectors.some((s) => /^\.btn:where\(:not\(.*\)\):hover$/.test(s)));
    expect(hover.length).toBe(1);
    const sel = hover[0]?.selectors.find((s) => s.endsWith(':hover')) ?? '';
    expect(sel).not.toContain('.btn-secondary');
    expect(decls(hover[0]?.body ?? '')).toContain('background: var(--color-gray-50)');
  });
  for (const theme of ['light', 'dark'] as const) {
    it(`on-primary 대 primary-700 대비 ≥ 4.5(${theme})`, () => {
      expect(tokenRatio('--color-on-primary', '--color-primary-700', theme)).toBeGreaterThanOrEqual(4.5);
    });
  }
});

describe('#12 · `.btn-sm`(값 11)', () => {
  // F-css A4 — `label.btn` 의 글자 세로 가운데를 위해 inline-flex · align-items center 두 선언을 더한다.
  it('여섯 선언 = 29px · 29px · 0 11px · caption ＋ inline-flex · center', () => {
    expect(decls(body(PRIM, '.btn-sm')).sort()).toEqual(
      [
        'align-items: center',
        'display: inline-flex',
        'font-size: var(--text-caption)',
        'height: 29px',
        'min-height: 29px',
        'padding: 0 11px',
      ].sort(),
    );
  });
  it('640px 이하 또는 터치가 주 입력인 기기에서는 `--control-height` 하한(design-fix 후속 20260925 Q3c)', () => {
    expect(decls(body(PRIM, '.btn-sm', '@media (max-width: 640px), (pointer: coarse)'))).toContain(
      'min-height: var(--control-height)',
    );
  });
});

describe('#11 · 칩 배경(값 12) ＋ 칩 테두리(값 18)', () => {
  it('`.chip` 배경 = gray-100 · 테두리색 = border-strong', () => {
    const d = decls(body(PRIM, '.chip'));
    expect(d).toContain('background: var(--color-gray-100)');
    expect(d).toContain('border-color: var(--color-border-strong)');
  });
  it('primitives.css(주석 포함)에 `#eef2f7` 0', () => {
    expect(raw('src/shell/primitives.css')).not.toMatch(/#eef2f7/i);
  });
  it('same-in-dark.txt 에 `.chip` 의 f 면제 줄 0', () => {
    const lines = raw('../gates/fixtures/frontend-design-lint/same-in-dark.txt').split('\n');
    expect(lines.filter((l) => /^f\s*·/.test(l) && /·\s*\.chip\s*·/.test(l))).toEqual([]);
  });
  for (const theme of ['light', 'dark'] as const) {
    it(`muted · 본문색 대 gray-100 대비 ≥ 4.5(${theme})`, () => {
      expect(tokenRatio('--color-text-muted', '--color-gray-100', theme)).toBeGreaterThanOrEqual(4.5);
      expect(tokenRatio('--color-text', '--color-gray-100', theme)).toBeGreaterThanOrEqual(4.5);
    });
  }
});

describe('#13 · 떠 있는 층 그림자(회귀 고정 · 합격선 예외)', () => {
  it('`.gnb` · `.modal` 그림자 sm · `.modal--dialog` 없음 — 원문 불변', () => {
    expect(decls(body(SHELL, '.gnb'))).toContain('box-shadow: var(--shadow-sm)');
    expect(decls(body(PRIM, '.modal'))).toContain('box-shadow: var(--shadow-sm)');
    expect(decls(body(PRIM, '.modal--dialog'))).toContain('box-shadow: none');
  });
  it('두 자리에 「합격선 예외 #13」 주석', () => {
    expect(raw('src/shell/shell.css')).toContain('합격선 예외 #13');
    expect(raw('src/shell/primitives.css')).toContain('합격선 예외 #13');
  });
});

describe('#14 · 계정 관리 모달 층', () => {
  it('`.account-modal-back` z-index = `.modal-back` z-index = 200', () => {
    const z = (b: string) => decls(b).find((d) => d.startsWith('z-index:'));
    expect(z(body(LOGIN, '.account-modal-back'))).toBe('z-index: 200');
    expect(z(body(PRIM, '.modal-back'))).toBe('z-index: 200');
  });
});

/** frontend/src 아래 CSS 파일 전부(상대경로). */
function cssFiles(dir = 'src'): string[] {
  const out: string[] = [];
  for (const name of readdirSync(resolve(process.cwd(), dir)) as string[]) {
    const rel = join(dir, name);
    if (statSync(resolve(process.cwd(), rel)).isDirectory()) out.push(...cssFiles(rel));
    else if (rel.endsWith('.css')) out.push(rel);
  }
  return out;
}

describe('#7 · 자간 토큰(값 8 · 9)', () => {
  it('tokens.css 에 heading −0.02em · label 0.05em', () => {
    expect(LIGHT.get('--tracking-heading')).toBe('-0.02em');
    expect(LIGHT.get('--tracking-label')).toBe('0.05em');
  });
  const files = cssFiles().filter((f) => !f.endsWith('shell/tokens.css'));
  const allowed = new Set(['var(--tracking-heading)', 'var(--tracking-label)', 'var(--tracking-body)', '0', 'normal', 'inherit']);
  it('모든 자간 값이 토큰 · 0 · normal · inherit(`.login-brand` 1곳 예외)', () => {
    const bad: string[] = [];
    for (const f of files) {
      for (const r of rules(read(f))) {
        for (const d of decls(r.body)) {
          const m = d.match(/^letter-spacing:\s*(.+)$/);
          if (!m?.[1] || allowed.has(m[1].trim())) continue;
          if (f.endsWith('auth/login.css') && r.selectors.join(',') === '.login-brand') continue;
          bad.push(`${f} ${r.selectors.join(',')} ${m[1]}`);
        }
      }
    }
    expect(bad).toEqual([]);
  });
  it('heading 참조 8 · label 참조 7', () => {
    const all = files.map((f) => read(f)).join('\n');
    expect(all.match(/letter-spacing:\s*var\(--tracking-heading\)/g)?.length ?? 0).toBe(8);
    expect(all.match(/letter-spacing:\s*var\(--tracking-label\)/g)?.length ?? 0).toBe(7);
  });
});

describe('#8 · 글자 크기 토큰 rem', () => {
  const want: [string, string][] = [
    ['--text-h2', '1.75rem'],
    ['--text-h3', '1.125rem'],
    ['--text-section', '1rem'],
    ['--text-body', '0.9375rem'],
    ['--text-body-sm', '0.875rem'],
    ['--text-caption', '0.8125rem'],
  ];
  for (const [name, v] of want) {
    it(`${name} = ${v}`, () => expect(LIGHT.get(name)).toBe(v));
  }
  it('px 로 끝나는 `--text-*` 0', () => {
    expect(TOKENS.match(/--text-[a-z0-9-]+:\s*[\d.]+px/g) ?? []).toEqual([]);
  });
});

describe('#17 · 색 배경 위 글자 토큰(값 13)', () => {
  it('라이트 · 다크 모두 `--color-on-text-body` 정의', () => {
    expect(LIGHT.has('--color-on-text-body')).toBe(true);
    expect(DARK.has('--color-on-text-body')).toBe(true);
  });
  it('`.de-req` 글자 = `--color-on-text-body`', () => {
    expect(varName(body(DETAIL, '.detail-page .dt-edit .de-req'), 'color')).toBe('--color-on-text-body');
  });
  for (const theme of ['light', 'dark'] as const) {
    it(`글자 대 --color-text-body 대비 ≥ 4.5(${theme})`, () => {
      expect(tokenRatio('--color-on-text-body', '--color-text-body', theme)).toBeGreaterThanOrEqual(4.5);
    });
  }
});

describe('#15 · 장식 글리프(회귀 고정 · 합격선 예외)', () => {
  it('`.thf::before` 9px 불변 ＋ 예외 주석', () => {
    expect(decls(body(CATALOG, '.tbl thead th > .thf::before'))).toContain('font-size: 9px');
    expect(raw('src/components/catalog/catalog.css')).toContain('합격선 예외 #15');
  });
});

describe('#16 · 「불일치」 글자', () => {
  it('`.lvl-mismatch` = caption · catalog.css 에 12px 0', () => {
    expect(decls(body(CATALOG, '.lvl-mismatch'))).toContain('font-size: var(--text-caption)');
    expect(CATALOG).not.toMatch(/font-size:\s*12px/);
  });
});

describe('#19 · 계보 안내 줄 주석', () => {
  // F-css A1 — 안내 줄은 `.lin-scope-lv`(muted on surface-alt)다. 세부 단언은 F-css 시험.
  it('주석 포함 원문에 `#5b6472` 0 · 안내 줄 주석이 `.lin-scope-lv` 의 muted', () => {
    const src = raw('src/components/lineage/lineage.css');
    expect(src).not.toMatch(/#5b6472/i);
    const lines = src.split('\n').filter((l) => l.includes('안내 줄'));
    expect(lines.some((l) => l.includes('.lin-scope-lv') && l.includes('--color-text-muted'))).toBe(true);
  });
});

describe('WU-A2 · 셸 대화형 10종 누름(값 15)', () => {
  const want: [string, string][] = [
    ['.detail-page .backlink:active', 'var(--color-gray-100)'],
    ['.project-detail .backlink:active', 'var(--color-gray-100)'],
    ['.mainnav a:active', 'var(--color-surface-pressed)'], // F-css A3 · A10 · 값 19
    ['.gnb-settings:active', 'var(--color-gray-100)'],
    ['.gnb-upload:active', 'var(--color-primary-800)'], // design-fix 후속 20260925 Q3a
    ['.gnb-more:active', 'var(--color-gray-100)'],
    ['.gnb-more-item:active', 'var(--color-gray-100)'],
    ['.gnb-logout:active', 'var(--color-gray-100)'],
    ['.loadfail-retry:active', 'var(--color-gray-100)'],
    ['.theme-switcher:active', 'var(--color-gray-100)'],
    [':is(.lin-find, .lin-fix, .modal-takeover) .modal-h .x:active', 'var(--color-gray-100)'],
  ];
  for (const [sel, bg] of want) {
    it(`${sel} → ${bg}`, () => {
      expect(decls(body(SHELL, sel))).toContain(`background: ${bg}`);
    });
  }
  it('reduced-motion 블록 원문 불변', () => {
    expect(SHELL).toContain(
      '@media (prefers-reduced-motion: reduce) {\n  *, *::before, *::after { transition: none !important; scroll-behavior: auto !important; }\n}',
    );
  });
  const hovers: [string, string[]][] = [
    ['.detail-page .backlink:hover', ['border-color: var(--color-border-strong)', 'background: var(--color-surface)', 'color: var(--color-text)']],
    ['.mainnav a:hover', ['background: var(--color-surface-hover)', 'color: var(--color-text)']],
    ['.gnb-settings:hover', ['background: var(--color-gray-50)', 'border-color: var(--color-gray-400)']],
    ['.gnb-upload:hover', ['background: var(--color-primary-700)']],
    ['.gnb-more:hover', ['background: var(--color-gray-50)', 'border-color: var(--color-gray-400)']],
    ['.gnb-more-item:hover', ['background: var(--color-gray-50)']],
    ['.gnb-logout:hover', ['color: var(--color-text)', 'border-color: var(--color-border-shell)']],
  ];
  for (const [sel, d] of hovers) {
    it(`기존 hover 불변: ${sel}`, () => {
      expect(decls(body(SHELL, sel))).toEqual(d);
    });
  }
});

describe('WU-A3 · 표 행 누름(값 16)', () => {
  // F-css A3 · A10 · 값 19 — hover 가 surface-hover 인 자리의 누름은 surface-pressed.
  it('`.tbl tr.clk:active td` = surface-pressed', () => {
    expect(decls(body(CATALOG, '.tbl tr.clk:active td'))).toContain('background: var(--color-surface-pressed)');
  });
  it('`.tbl tr.clk td` transition 불변', () => {
    expect(decls(body(CATALOG, '.tbl tr.clk td'))).toEqual(['transition: background var(--ease), box-shadow var(--ease)']);
  });
});
