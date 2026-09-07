/**
 * WU-C11 · CSS 잔여 (R-B 판정 45·46·47·48·49) — CSS 원문 계측 시험.
 *
 * 오라클 = `dev-package/prd/rounds/R-C-2-frontend.md §2 WU-C11` 수용 기준
 *          ＋ `dev-package/sessions/R-B-ROUND-20260908.md §5` 45~49.
 * 화면을 그리지 않고 CSS 원문을 읽어 잰다 — jsdom 은 스타일을 계산하지 않는다
 * (`design-fix-20260908.test.ts` 와 같은 규율).
 *
 *   ㈎ 45 `.lvl-3` 4단째가 서 있고 Lv2 와 같은 계열 한 단 진하다 ＋ 글자 대비 AA
 *   ㈏ 46 `.lin--none` 대비 ≥ 4.5:1 (종전 3.41:1)
 *   ㈐ 47 `.dt-gridact` 음수 margin 0
 *   ㈑ 49 `upload.css` 지목 블록의 자식 `margin-top` 0곳 ＋ 컨테이너가 gap 을 진다
 *   ㈒ 49 `.dsec` 부모 컨테이너 클래스가 TSX 에 있다
 *   ㈓ 48 액센트 토큰이 목업 `:root` 축자로 서 있다 ＋ 미정의 토큰 참조 0건
 */
// @ts-expect-error — 타입 선언 없이 런타임만 쓴다(vitest 는 node 위에서 돈다).
import { readFileSync } from 'node:fs';
// @ts-expect-error — 같은 이유.
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

declare const process: { cwd(): string };

/** 주석은 걷어내고 읽는다 — 선언만 잰다. */
const read = (rel: string): string =>
  String(readFileSync(resolve(process.cwd(), rel), 'utf8')).replace(/\/\*[\s\S]*?\*\//g, '');

const TOKENS = read('src/shell/tokens.css');
const CATALOG = read('src/components/catalog/catalog.css');
const DETAIL = read('src/components/detail/detail.css');
const UPLOAD = read('src/components/upload/upload.css');
const LINEAGE_GRAPH = read('src/components/lineage/lineageGraph.css');
const DETAIL_PAGE_TSX = String(
  readFileSync(resolve(process.cwd(), 'src/routes/DatasetDetailPage.tsx'), 'utf8'),
);

/** 선택자 하나의 선언 블록(`{ … }`). */
function block(css: string, selector: string): string {
  const at = css.indexOf(selector);
  expect(at, `선택자 부재: ${selector}`).toBeGreaterThan(-1);
  const open = css.indexOf('{', at);
  const close = css.indexOf('}', open);
  return css.slice(open + 1, close);
}

/** 6자리 hex → WCAG 상대휘도. */
function luminance(hex: string): number {
  const ch = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255);
  const lin = ch.map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4)) as [
    number,
    number,
    number,
  ];
  return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2];
}

/** 토큰 이름 → hex 값(정의처 여럿을 훑는다 · `var()` 별칭 한 겹까지 푼다). */
function tokenHex(name: string): string {
  for (const css of [TOKENS, CATALOG, DETAIL]) {
    const m = css.match(new RegExp(`${name}:\\s*(#[0-9a-fA-F]{6})`));
    if (m?.[1]) return m[1];
  }
  throw new Error(`토큰 값 부재: ${name}`);
}

/** WCAG 대비비 — 두 hex 사이. */
function ratio(a: string, b: string): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x) as [number, number];
  return (hi + 0.05) / (lo + 0.05);
}

/** 블록에서 `background`/`color` 가 참조하는 토큰 이름. */
function refOf(decls: string, prop: 'background' | 'color'): string {
  const m = decls.match(new RegExp(`(?:^|;)\\s*${prop}:\\s*var\\((--[a-z0-9-]+)\\)`));
  if (!m?.[1]) throw new Error(`${prop} 토큰 참조 부재`);
  return m[1];
}

describe('WU-C11 ㈎ 45 `.lvl-3` 4단째', () => {
  for (const [file, css] of [
    ['catalog.css', CATALOG],
    ['detail.css', DETAIL],
  ] as [string, string][]) {
    const sel = file === 'catalog.css' ? '.lvl-3 ' : '.detail-page .lvl-3 ';
    const lv2 = file === 'catalog.css' ? '.lvl-2 ' : '.detail-page .lvl-2 ';

    it(`${file} 에 \`.lvl-3\` 규칙이 홀로 서 있다`, () => {
      expect(css).toMatch(new RegExp(`(^|\\n)${sel.trim().replace(/\./g, '\\.')}\\s*\\{`));
      // Lv2 와 한 규칙에 묶여 있으면 4단째가 무색이다.
      expect(block(css, lv2)).not.toBe(block(css, sel));
    });

    it(`${file} \`.lvl-3\` 배경이 Lv2 와 같은 계열 한 단 진하다`, () => {
      const bg3 = refOf(block(css, sel), 'background');
      const bg2 = refOf(block(css, lv2), 'background');
      expect(bg3.replace(/-\d+$/, '')).toBe(bg2.replace(/-\d+$/, '')); // 같은 계열
      expect(luminance(tokenHex(bg3))).toBeLessThan(luminance(tokenHex(bg2))); // 한 단 진하게
    });

    it(`${file} \`.lvl-3\` 칩 글자 대비가 4.5:1 이상이다`, () => {
      const d = block(css, sel);
      const r = ratio(tokenHex(refOf(d, 'color')), tokenHex(refOf(d, 'background')));
      expect(r).toBeGreaterThanOrEqual(4.5);
    });
  }
});

describe('WU-C11 ㈏ 46 `.lin--none` 대비', () => {
  it('흰 면 위 대비가 4.5:1 이상이다 (종전 gray-400 3.41:1)', () => {
    const fg = tokenHex(refOf(block(CATALOG, '.lin--none '), 'color'));
    expect(ratio(fg, '#ffffff')).toBeGreaterThanOrEqual(4.5);
  });
});

describe('WU-C11 ㈐ 47 `.dt-gridact` 음수 상쇄', () => {
  it('음수 margin 선언이 없다', () => {
    expect(block(DETAIL, '.detail-page .dt-gridact ')).not.toMatch(/margin[a-z-]*:[^;]*-\d/);
  });
  it('여백은 부모 `.dt-split-r` 이 gap 으로 갖는다', () => {
    expect(block(DETAIL, '.detail-page .dt-split-r {')).toMatch(/gap:/);
  });
});

describe('WU-C11 ㈑ 49 `upload.css` 여백 컨테이너 이관', () => {
  /** R-B 49 가 지목한 블록(재측정 뒤 이름으로 적는다 — 줄 번호는 앞 WU 가 바꾼다). */
  const spots = [
    '.vizsetup ',
    '.vizload ',
    '.vizerr, .warn ',
    '.vizpartial ',
    '.mapcanvas .tile ',
    '.up-steps ',
    '.projpick ',
    '.qproj {',
    '.qproj .qf ',
    '.qproj .qnote ',
    '.reg-actions {',
    '.lineage-slot ',
  ];
  it('지목된 블록의 자식 `margin-top` 이 0곳이다', () => {
    const left = spots.filter((sel) => /margin-top:/.test(block(UPLOAD, sel)));
    expect(left).toEqual([]);
  });
  for (const [container, child] of [
    ['.mapstage {', '.vizsetup / .vizload / .vizerr / .vizpartial'],
    ['.regarea {', '.up-steps / .reg-actions'],
    ['.up-card > .card-b ', '.projpick / .lineage-slot'],
    ['.projpick ', '.qproj'],
    ['.qproj {', '.qf / .qnote'],
  ] as [string, string][]) {
    it(`컨테이너 \`${container.replace(/[{ ]+$/, '')}\` 가 gap 으로 ${child} 의 여백을 진다`, () => {
      expect(block(UPLOAD, container)).toMatch(/gap:/);
    });
  }
});

describe('WU-C11 ㈒ 49 `.dsec` 부모 컨테이너', () => {
  it('`.dsec` 자식이 `margin-top` 을 지지 않는다', () => {
    expect(LINEAGE_GRAPH).not.toMatch(/\.dsec\s*\{[^}]*margin-top/);
  });
  it('부모 컨테이너 `.dt-secs` 가 gap 을 진다', () => {
    expect(block(DETAIL, '.detail-page .dt-secs ')).toMatch(/gap:/);
  });
  it('`DatasetDetailPage.tsx` 의 부모 요소에 그 클래스가 붙어 있다', () => {
    expect(DETAIL_PAGE_TSX).toMatch(/className="dt-secs"/);
  });
});

describe('WU-C11 ㈓ 48 액센트 토큰 회수', () => {
  it('액센트 토큰이 목업 `:root` 축자로 서 있다', () => {
    expect(tokenHex('--color-accent-50')).toBe('#f1e8ff');
    expect(tokenHex('--color-accent-700')).toBe('#4821db');
  });
  it('AI 표식 `.aiflag` 가 액센트 계열이고 대비가 4.5:1 이상이다', () => {
    const d = block(LINEAGE_GRAPH, '.detail-page .aiflag ');
    expect(refOf(d, 'color')).toMatch(/^--color-accent-/);
    const r = ratio(tokenHex(refOf(d, 'color')), tokenHex(refOf(d, 'background')));
    expect(r).toBeGreaterThanOrEqual(4.5);
  });
  it('`lineageGraph.css` 에 미정의 토큰 참조가 0건이다 (B11 회귀)', () => {
    const known = new Set<string>();
    for (const css of [TOKENS, DETAIL]) {
      for (const m of css.matchAll(/(--[a-z0-9-]+)\s*:/g)) if (m[1]) known.add(m[1]);
    }
    const missing = [...LINEAGE_GRAPH.matchAll(/var\((--[a-z0-9-]+)\)/g)]
      .map((m) => m[1] ?? '')
      .filter((name) => !known.has(name));
    expect([...new Set(missing)]).toEqual([]);
  });
});
