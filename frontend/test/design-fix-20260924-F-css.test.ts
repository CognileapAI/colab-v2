/**
 * design-fix 20260924 · 수정 레인 F-css — CSS 계측 시험.
 *
 * 오라클 = `dev-package/prd/specs/S-DESIGN-FIX-20260924.md` 「통합 수정」(값 19–21 · 수정 레인 표 F-css 행)
 * ＋ 「확정 값」. 결함 원문 = `dev-package/sessions/design-fix-20260924-acceptance.md` A1–A22(F-css 몫).
 * 방식은 L1 시험과 같다 — CSS 원문에서 주석을 걷고 선택자 블록을 잘라 잰다(jsdom 은 스타일을 계산하지 않는다).
 * 대비·같음 판정은 WCAG 상대휘도 · 라이트 = `:root` · 다크 = `:root[data-theme="dark"]` · 반투명 면은 `--color-surface` 에 합성.
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
const SEARCH = read('src/components/search/search.css');
const LINEAGE = read('src/components/lineage/lineage.css');
const UPLOAD = read('src/components/upload/upload.css');

// ── 규칙 파서(L1 시험과 같은 규칙) ─────────────────────────────────────────
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

/** 토큰 → 색 문자열(var 사슬 해소 · 다크는 없으면 라이트 값). */
function resolveToken(name: string, theme: Theme, seen = 0): string {
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
/** 배경 값(`var(--x)` · `transparent`)을 테마 바탕면 위에 합성한 불투명 색. */
function paint(value: string, theme: Theme): RGBA {
  const surface = parseHex(resolveToken('--color-surface', theme));
  if (value === 'transparent' || value === 'none') return surface;
  const m = value.match(/^var\((--[a-z0-9-]+)\)$/);
  if (!m?.[1]) throw new Error(`토큰 한 개짜리 값이 아니다: ${value}`);
  return over(parseHex(resolveToken(m[1], theme)), surface);
}
const hexOf = (c: RGBA): string =>
  c
    .slice(0, 3)
    .map((v) => Math.round(v).toString(16).padStart(2, '0'))
    .join('');

// ── 시험 ─────────────────────────────────────────────────────────────────

describe('값 19 · `--color-surface-pressed`', () => {
  it('라이트 = gray-100 과 같은 값 #e8ecf2', () => {
    expect(resolveToken('--color-surface-pressed', 'light').toLowerCase()).toBe('#e8ecf2');
    expect(resolveToken('--color-surface-pressed', 'light')).toBe(resolveToken('--color-gray-100', 'light'));
  });
  it('다크 = gray-200 과 같은 값 #45566a(다크 블록에 정의)', () => {
    expect(DARK.has('--color-surface-pressed')).toBe(true);
    expect(resolveToken('--color-surface-pressed', 'dark').toLowerCase()).toBe('#45566a');
    expect(resolveToken('--color-surface-pressed', 'dark')).toBe(resolveToken('--color-gray-200', 'dark'));
  });
  it('다크 누름 대 hover(surface-hover) 1.61:1', () => {
    const r = ratio(paint('var(--color-surface-pressed)', 'dark'), paint('var(--color-surface-hover)', 'dark'));
    expect(r.toFixed(2)).toBe('1.61');
  });
});

describe('A3 · A10 · A8 · 값 19 소비처 — hover 가 surface-hover 인 누름 자리', () => {
  const want: [string, string][] = [
    [CATALOG, '.tbl tr.clk:active td'],
    [SHELL, '.mainnav a:active'],
    [SHELL, '.mainnav a.is-active:active'],
  ];
  for (const [css, sel] of want) {
    it(`${sel} → var(--color-surface-pressed)`, () => {
      expect(prop(body(css, sel), 'background')).toBe('var(--color-surface-pressed)');
    });
  }
});

describe('누름 ≠ hover(두 테마) — 회색 계열 누름 자리 전부', () => {
  // [파일 이름, CSS, 누름 선택자, 비교 대상 선택자(hover · hover 가 없으면 평상시), 비교 대상 매체 자리(생략 = 조건 없음)]
  const pairs: [string, string, string, string, string?][] = [
    ['primitives', PRIM, '.btn:where(:not(.btn-primary)):active', '.btn:where(:not(.btn-primary, :disabled)):hover', '@media (hover: hover)'],
    ['shell', SHELL, '.loadfail-retry:active', '.loadfail-retry'],
    ['shell', SHELL, '.detail-page .backlink:active', '.detail-page .backlink:hover', '@media (hover: hover)'],
    ['shell', SHELL, '.mainnav a:active', '.mainnav a:hover', '@media (hover: hover)'],
    ['shell', SHELL, '.mainnav a.is-active:active', '.mainnav a.is-active'],
    ['shell', SHELL, '.gnb-settings:active', '.gnb-settings:hover', '@media (hover: hover)'],
    ['shell', SHELL, '.gnb-more:active', '.gnb-more:hover', '@media (hover: hover)'],
    ['shell', SHELL, '.gnb-more-item:active', '.gnb-more-item:hover', '@media (hover: hover)'],
    ['shell', SHELL, '.gnb-logout:active', '.gnb-logout'],
    ['shell', SHELL, '.theme-switcher:active', '.theme-switcher'],
    ['shell', SHELL, ':is(.lin-find, .lin-fix, .modal-takeover) .modal-h .x:active', ':is(.lin-find, .lin-fix, .modal-takeover) .modal-h .x'],
    ['catalog', CATALOG, '.tbl tr.clk:active td', '.tbl tr.clk:hover td', '@media (hover: hover)'],
    ['upload', UPLOAD, '.dr-cal-d:active', '.dr-cal-d:hover'],
    // F-final 1 · A21 — 업로드 달력 누름(값 19).
    ['upload', UPLOAD, '.dr-nav button:active', '.dr-nav button:hover'],
    ['upload', UPLOAD, '.dr-useg button:active', '.dr-useg button:hover'],
  ];
  for (const [file, css, active, other, otherMedia = ''] of pairs) {
    for (const theme of THEMES) {
      it(`${file} ${active} ≠ ${other}(${theme})`, () => {
        const a = prop(body(css, active), 'background');
        const b = prop(body(css, other, otherMedia), 'background') ?? 'transparent';
        expect(a, `${active} background`).toBeDefined();
        expect(hexOf(paint(a ?? '', theme))).not.toBe(hexOf(paint(b, theme)));
      });
    }
  }
});

describe('A2 · A5 · A13 · 비활성 단추 hover 제외', () => {
  it('plain · ghost · secondary hover 선택자 = `.btn:where(:not(.btn-primary, :disabled)):hover` · gray-50', () => {
    expect(prop(body(PRIM, '.btn:where(:not(.btn-primary, :disabled)):hover', '@media (hover: hover)'), 'background')).toBe('var(--color-gray-50)');
  });
  it('primary hover 선택자 = `.btn-primary:where(:not(:disabled)):hover` · primary-700', () => {
    expect(prop(body(PRIM, '.btn-primary:where(:not(:disabled)):hover', '@media (hover: hover)'), 'background')).toBe('var(--color-primary-700)');
  });
  it('primitives.css 의 `.btn` 계열 `:hover` 선택자는 모두 `:disabled` 를 `:where()` 안에서 뺀다(특이도 무변 → 누름이 이긴다)', () => {
    const hovers = rules(PRIM)
      .flatMap((r) => r.selectors)
      .filter((s) => /^\.btn[\w-]*/.test(s) && s.includes(':hover'));
    expect(hovers.length).toBe(2);
    for (const s of hovers) expect(s, s).toMatch(/:where\([^{]*:disabled[^{]*\)/);
  });
});

describe('A4 · `.btn-sm` 글자 세로 가운데', () => {
  it('`.btn-sm` = inline-flex · align-items center', () => {
    const d = decls(body(PRIM, '.btn-sm'));
    expect(d).toContain('display: inline-flex');
    expect(d).toContain('align-items: center');
  });
});

describe('A6 · A7 · A14 · A12 · 칩 테두리색(값 18)이 덮이지 않는다', () => {
  it('`.chip--off` 에 `border` 단축형 · 다른 `border-color` 0', () => {
    const d = decls(body(PRIM, '.chip--off'));
    expect(d.filter((x) => /^border(-color)?:/.test(x))).toEqual([]);
    expect(d).toContain('color: var(--color-text-muted)');
  });
  it('primitives.css 의 칩 수식자 블록 어디에도 `border` 단축형 · border-strong 밖 `border-color` 0', () => {
    const bad = rules(PRIM)
      .filter((r) => r.selectors.some((s) => /\.chip(--|:)/.test(s)))
      .flatMap((r) => decls(r.body).filter((d) => /^border:/.test(d) || (/^border-color:/.test(d) && d !== 'border-color: var(--color-border-strong)')).map((d) => `${r.selectors.join(',')} ${d}`));
    expect(bad).toEqual([]);
  });
  it('`.search-page .chip` 에 `border` 단축형 · `border-color` 0', () => {
    expect(decls(body(SEARCH, '.search-page .chip')).filter((x) => /^border(-color)?:/.test(x))).toEqual([]);
  });
  it('화면 CSS(primitives 밖) 어디에도 `.chip` 으로 끝나는 선택자의 `border` · `border-color` 선언 0', () => {
    const bad: string[] = [];
    const files = (function walk(dir: string): string[] {
      const out: string[] = [];
      for (const name of readdirSync(resolve(process.cwd(), dir)) as string[]) {
        const rel = join(dir, name);
        if (statSync(resolve(process.cwd(), rel)).isDirectory()) out.push(...walk(rel));
        else if (rel.endsWith('.css') && !rel.endsWith('primitives.css')) out.push(rel);
      }
      return out;
    })('src');
    for (const f of files) {
      for (const r of rules(read(f))) {
        if (!r.selectors.some((s) => /\.chip(\[[^\]]*\]|:[\w-]+)*$/.test(s))) continue;
        for (const d of decls(r.body)) if (/^border(-color)?:/.test(d)) bad.push(`${f} ${r.selectors.join(',')} ${d}`);
      }
    }
    expect(bad).toEqual([]);
  });
});

describe('A18 · 값 21 · 끌어 오는 동안 드롭 아이콘 동그라미', () => {
  it('`.dropzone.is-dragover .up-drop-icon` 바탕 = var(--color-surface)', () => {
    expect(prop(body(UPLOAD, '.dropzone.is-dragover .up-drop-icon'), 'background')).toBe('var(--color-surface)');
  });
  for (const theme of THEMES) {
    it(`아이콘 바탕 ≠ 드롭 영역 바탕 primary-50(${theme})`, () => {
      const icon = prop(body(UPLOAD, '.dropzone.is-dragover .up-drop-icon'), 'background') ?? '';
      const zone = prop(body(UPLOAD, '.up-empty .dropzone.is-dragover'), 'background') ?? '';
      expect(hexOf(paint(icon, theme))).not.toBe(hexOf(paint(zone, theme)));
    });
  }
});

describe('A22 · 드롭 영역 주석의 특이도', () => {
  it('「같은 특이도로 한 줄 더 둔다」 문구 0 · (0,3,0) 대 (0,2,0) 명시', () => {
    const src = raw('src/components/upload/upload.css');
    expect(src).not.toContain('같은 특이도로 한 줄 더 둔다');
    expect(src).toMatch(/\(0,3,0\)[^\n]*\(0,2,0\)/);
  });
});

describe('A1 · 계보 안내 줄 주석을 실제 요소에 맞춤', () => {
  const src = raw('src/components/lineage/lineage.css');
  const line = src.split('\n').find((l) => l.includes('안내 줄')) ?? '';
  it('안내 줄 주석 = `.lin-scope-lv` · muted on surface-alt · 6.30:1', () => {
    expect(line).toContain('.lin-scope-lv');
    expect(line).toContain('--color-text-muted');
    expect(line).toContain('--color-surface-alt');
    expect(line).toContain('6.30:1');
    expect(line).not.toContain('.lin-over-why');
  });
  it('주석이 말하는 두 값 = `.lin-scope-lv` 가 실제로 쓰는 값', () => {
    const b = body(LINEAGE, '.lin-scope-lv');
    expect(prop(b, 'color')).toBe('var(--color-text-muted)');
    expect(prop(b, 'background')).toBe('var(--color-surface-alt)');
  });
  it('라이트 대비 계측 = 6.30', () => {
    expect(ratio(paint('var(--color-text-muted)', 'light'), paint('var(--color-surface-alt)', 'light')).toFixed(2)).toBe('6.30');
  });
});

describe('A11 · 값 20 · 누르는 동안(`:active`) 대비 예외를 정본에 적음', () => {
  it('docs/design-system.md 점검표의 대비 합격선 줄에 `:active` 예외', () => {
    const line = raw('../docs/design-system.md').split('\n').find((l) => l.includes('대비 4.5:1 이상')) ?? '';
    expect(line).toContain(':active');
    expect(line).toContain('예외');
  });
  it('design-review SKILL §0 정적 합격선 행에 `:active` 예외', () => {
    const line = raw('../.agents/skills/design-review/SKILL.md').split('\n').find((l) => l.startsWith('| 정적 합격선')) ?? '';
    expect(line).toContain(':active');
    expect(line).toContain('예외');
  });
});

describe('수정 라운드 F2 · 정본 ⑤ 누름 줄은 규칙만', () => {
  const DOC = raw('../docs/design-system.md');
  const section = (head: string): string => {
    const from = DOC.indexOf(`\n## ${head}`);
    const to = DOC.indexOf('\n## ', from + 1);
    return DOC.slice(from, to < 0 ? undefined : to);
  };
  it('⑤ 누름 피드백 줄에 레인 상태(미적용 · 레인 보고서)가 없다', () => {
    const line = section('⑤').split('\n').find((l) => l.startsWith('- 누름 피드백')) ?? '';
    expect(line).toContain('--color-surface-pressed');
    expect(line).not.toMatch(/미적용|레인 보고서|아직/);
  });
});
