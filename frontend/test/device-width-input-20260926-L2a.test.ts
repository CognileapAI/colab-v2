/**
 * 휴대폰·패드 대응 20260926 L2a — 셸 · 기본 · 프리미티브 CSS(hover 감싸기 · 16px 하한 한 곳 · 터치 44).
 *
 * 오라클 = `dev-package/prd/specs/S-DEVICE-WIDTH-INPUT-20260926.md` V7(맨 위 메뉴 · 셸) · V8(셸 · 기본 · 프리미티브) ·
 * V10(감싸기 9) · 구현 결정 「터치 규칙 CSS」 · 「입력 글자 하한 규칙」 · 「hover 감싸기」 · 부록 B(레인 L2a 9항목) ·
 * 부록 D(L2a 9규칙 = 셸 7 ＋ 프리미티브 2) · 부록 G(L2a 3곳) · 우려 3ⓐ.
 * 원문 CSS 에서 주석을 걷고 규칙을 잘라 잰다(선례 design-fix 20260924 F-css · jsdom 은 스타일을 계산하지 않는다).
 * 대상 목록 길이를 먼저 단언한다(green-by-skip 방지). 렌더된 누름 칸 · 글자 크기는 캡처 수치(레인 보고)가 확인한다.
 */
import { describe, expect, it } from 'vitest';
import baseCss from '../src/shell/base.css?raw';
import primitivesCss from '../src/shell/primitives.css?raw';
import shellCss from '../src/shell/shell.css?raw';
import tokensCss from '../src/shell/tokens.css?raw';

/**
 * 원문은 `?raw` 로 받는다 — `node:fs` 금지(`e01-apply-points.test.ts` 머리 주석 · 2026-09-02 배포 불가 사고).
 * vitest css 스텁은 허용 목록(`vite.config.ts` `test.css.include`) 밖 `?raw` 를 빈 문자열로 만든다 → 아래 「적재」 시험이 red.
 * 값 = [원문, 그 파일에 반드시 있는 선택자].
 */
const RAW_CSS: Record<string, readonly [string, string]> = {
  'src/shell/base.css': [baseCss, 'button, input, select, textarea'],
  'src/shell/primitives.css': [primitivesCss, '.btn-sm'],
  'src/shell/shell.css': [shellCss, '.backlink'],
  'src/shell/tokens.css': [tokensCss, '--shell-gnb-offset'],
};
const raw = (rel: string): string => {
  const hit = RAW_CSS[rel];
  if (!hit) throw new Error(`?raw 로 받지 않은 파일: ${rel}`);
  return hit[0];
};

describe('CSS 원문 적재 — `?raw` 가 비지 않고 알려진 선택자를 담는다(허용 목록 누락 = red)', () => {
  it.each(Object.entries(RAW_CSS))('%s', (rel, [css, known]) => {
    expect(css.length, rel).toBeGreaterThan(0);
    expect(css, rel).toContain(known);
  });
});
const strip = (css: string): string => css.replace(/\/\*[\s\S]*?\*\//g, '');

const FILES = {
  base: 'src/shell/base.css',
  primitives: 'src/shell/primitives.css',
  shell: 'src/shell/shell.css',
} as const;
type FileName = keyof typeof FILES;
const CSS: Record<FileName, string> = {
  base: strip(raw(FILES.base)),
  primitives: strip(raw(FILES.primitives)),
  shell: strip(raw(FILES.shell)),
};
const TOKENS = strip(raw('src/shell/tokens.css'));

const HOVER = '@media (hover: hover)';
const COARSE = '@media (pointer: coarse)';
const FLOOR = '@media (max-width: 640px), (pointer: coarse)';

// ── 규칙 파서(선례 design-fix-20260924-L1 과 같은 규칙) ─────────────────────
type Rule = { selectors: string[]; body: string; media: string; top: number };

/** 주석 걷은 CSS 를 규칙 목록으로 편다. `@layer` 는 투명, `@media` 는 조건을 달아 준다. `top` = 층 안 맨 위 블록 순번. */
function rules(css: string, media = '', topBase = -1): Rule[] {
  const out: Rule[] = [];
  let i = 0;
  let n = 0;
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
    const top = topBase < 0 ? n : topBase;
    if (head.startsWith('@layer')) out.push(...rules(inner, media, -1));
    else if (head.startsWith('@media')) out.push(...rules(inner, head, top));
    else if (head.startsWith('@')) {
      /* @keyframes 등 — 계측 밖 */
    } else {
      out.push({ selectors: splitList(head), body: inner.trim(), media, top });
    }
    n += 1;
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

function decls(b: string): string[] {
  return b
    .split(';')
    .map((d) => d.trim().replace(/\s+/g, ' '))
    .filter(Boolean);
}

/** 선택자 하나가 든 규칙 — 정확히 하나여야 한다(못 찾으면 빈 값이 아니라 실패). */
function only(file: FileName, selector: string): Rule {
  const found = rules(CSS[file]).filter((r) => r.selectors.includes(selector));
  expect(found.length, `규칙 수: ${file} ${selector}`).toBe(1);
  return found[0] as Rule;
}

// ── 대상 목록 ────────────────────────────────────────────────────────────
/** 부록 D 레인 L2a — [파일, 선택자 목록(한 규칙), 선언]. 규칙 9 · 선택자 10. */
const HOVERS: [FileName, string[], string[]][] = [
  ['shell', ['.detail-page .backlink:hover', '.project-detail .backlink:hover'],
    ['border-color: var(--color-border-strong)', 'background: var(--color-surface)', 'color: var(--color-text)']],
  ['shell', ['.mainnav a:hover'], ['background: var(--color-surface-hover)', 'color: var(--color-text)']],
  ['shell', ['.gnb-settings:hover'], ['background: var(--color-gray-50)', 'border-color: var(--color-gray-400)']],
  ['shell', ['.gnb-upload:hover'], ['background: var(--color-primary-700)']],
  ['shell', ['.gnb-more:hover'], ['background: var(--color-gray-50)', 'border-color: var(--color-gray-400)']],
  ['shell', ['.gnb-more-item:hover'], ['background: var(--color-gray-50)']],
  ['shell', ['.gnb-logout:hover'], ['color: var(--color-text)', 'border-color: var(--color-border-shell)']],
  ['primitives', ['.btn:where(:not(.btn-primary, :disabled)):hover'], ['background: var(--color-gray-50)']],
  ['primitives', ['.btn-primary:where(:not(:disabled)):hover'], ['background: var(--color-primary-700)']],
];

/** 부록 B 레인 L2a — [번호, 측정 선택자, 셸 CSS 터치 블록의 선택자]. 폭 숨김 = 3 · 4. */
const TAPS: [number, string, string][] = [
  [1, 'a.brand', '.gnb a.brand'],
  [2, '.mainnav a', '.gnb .mainnav a'],
  [3, '.gnb-settings', '.gnb :is(.gnb-settings, .gnb-upload, .gnb-more)'],
  [4, '.gnb-upload', '.gnb :is(.gnb-settings, .gnb-upload, .gnb-more)'],
  [5, '.gnb-more', '.gnb :is(.gnb-settings, .gnb-upload, .gnb-more)'],
  [6, '.gnb-logout', '.gnb .gnb-logout'],
  [7, 'select.theme-switcher', '.theme-switcher'],
  [21, '.notfound a', '.notfound a'],
  [22, '.backlink', '.detail-page .backlink'],
];
const WIDTH_HIDDEN = [3, 4];

/** 입력 글자 하한을 세는 선택자(V8 세는 범위) — `input` · `select` · `textarea` · `.inp` · `.sel`. */
const FIELD = /(^|[\s,(>+~])(input|select|textarea)(?![\w-])|\.(inp|sel)(?![\w-])/;
const isFloor = (r: Rule): boolean =>
  r.media !== '' && r.selectors.some((s) => FIELD.test(s)) && decls(r.body).some((d) => /^font-size:.*16px/.test(d));

// ── 시험 ─────────────────────────────────────────────────────────────────

describe('대상 개수(green-by-skip 방지)', () => {
  it('hover 규칙 = 9(셸 7 ＋ 프리미티브 2) · 선택자 10', () => {
    expect(HOVERS.length).toBe(9);
    expect(HOVERS.filter(([f]) => f === 'shell').length).toBe(7);
    expect(HOVERS.filter(([f]) => f === 'primitives').length).toBe(2);
    expect(HOVERS.flatMap(([, s]) => s).length).toBe(10);
  });
  it('터치 44 대상 = 9(부록 B 레인 L2a) · 폭 숨김 2', () => {
    expect(TAPS.map(([n]) => n)).toEqual([1, 2, 3, 4, 5, 6, 7, 21, 22]);
    expect(WIDTH_HIDDEN.length).toBe(2);
  });
});

describe('V10 · hover 감싸기(L2a 9규칙)', () => {
  for (const [file, sels, want] of HOVERS) {
    it(`${file} \`${sels.join(', ')}\` → \`${HOVER}\` 안 · 선언 불변`, () => {
      const r = only(file, sels[0] ?? '');
      expect(r.media).toBe(HOVER);
      expect(r.selectors).toEqual(sels);
      expect(decls(r.body)).toEqual(want);
    });
  }
  it('세 파일의 `:hover` 규칙 = 9 · 모두 `(hover: hover)` 안(조건 밖 0)', () => {
    const all = (Object.keys(FILES) as FileName[]).flatMap((f) =>
      rules(CSS[f]).filter((r) => r.selectors.some((s) => s.includes(':hover'))),
    );
    expect(all.length).toBe(9);
    expect(all.filter((r) => r.media !== HOVER)).toEqual([]);
  });
  it('초점 윤곽(`:focus-visible`)은 조건 없이 남는다 · hover 와 묶인 규칙 0', () => {
    const focus = rules(CSS.base).filter((r) => r.selectors.some((s) => s.includes(':focus-visible')));
    expect(focus.length).toBe(1);
    expect(focus[0]?.media).toBe('');
    const mixed = (Object.keys(FILES) as FileName[]).flatMap((f) =>
      rules(CSS[f]).filter((r) => r.selectors.some((s) => s.includes(':hover')) && r.selectors.some((s) => s.includes(':focus'))),
    );
    expect(mixed).toEqual([]);
  });
  it('프리미티브 hover 원문 한 줄 유지(followups L1 원문 단언과 같은 줄)', () => {
    const src = raw(FILES.primitives);
    expect(src).toContain(`${HOVER} { .btn:where(:not(.btn-primary, :disabled)):hover { background: var(--color-gray-50); } }`);
    expect(src).toContain(`${HOVER} { .btn-primary:where(:not(:disabled)):hover { background: var(--color-primary-700); } }`);
  });
});

describe('V8 · 16px 입력 글자 하한 한 곳(우려 3ⓐ)', () => {
  it('세 파일에서 `@media` 안 하한 선언 = 1 · 조건 = 640px 이하 또는 터치 기기', () => {
    const floors = (Object.keys(FILES) as FileName[]).flatMap((f) => rules(CSS[f]).filter(isFloor).map((r) => ({ f, r })));
    expect(floors.length).toBe(1);
    expect(floors[0]?.f).toBe('shell');
    expect(floors[0]?.r.media).toBe(FLOOR);
    expect(floors[0]?.r.selectors).toEqual(['body input', 'body select', 'body textarea']);
    expect(decls(floors[0]?.r.body ?? '')).toEqual(['font-size: max(16px, 1em) !important']);
  });
  it('하한 블록 안 규칙은 하한 하나뿐', () => {
    expect(rules(CSS.shell).filter((r) => r.media === FLOOR).length).toBe(1);
  });
  it('기본 층 `base.css` 에 `@media` 0 · 프리미티브 `:is(.inp, .sel)` 은 기본 블록 하나', () => {
    expect(rules(CSS.base).filter((r) => r.media !== '')).toEqual([]);
    const field = rules(CSS.primitives).filter((r) => r.selectors.includes(':is(.inp, .sel)'));
    expect(field.length).toBe(1);
    expect(field[0]?.media).toBe('');
  });
  it('셸 640px 블록의 나머지 규칙은 그대로(노치 여백 · 로그아웃 · 설정 · 없는 페이지 여백)', () => {
    const narrow = rules(CSS.shell).filter((r) => r.media === '@media (max-width: 640px)' && r.top === rules(CSS.shell).find((x) => x.selectors.includes('.appmain') && x.media === '@media (max-width: 640px)')?.top);
    expect(narrow.map((r) => r.selectors.join(', '))).toEqual(['.gnb', '.appmain', '.avatar', '.gnb-logout', '.settings-page, .notfound']);
  });
});

describe('V7 · 터치 44(부록 B 레인 L2a · 셸 CSS 끝 `(pointer: coarse)` 블록 하나)', () => {
  const shellRules = rules(CSS.shell);
  const coarse = shellRules.filter((r) => r.media === COARSE);
  it('셸 CSS 의 `(pointer: coarse)` 블록 = 1 · 파일 끝 블록', () => {
    const tops = new Set(coarse.map((r) => r.top));
    expect(tops.size).toBe(1);
    const lastTop = Math.max(...shellRules.map((r) => r.top));
    expect([...tops][0]).toBe(lastTop);
  });
  for (const [n, measured, sel] of TAPS) {
    it(`${n} \`${measured}\` → \`${sel}\` 최소 높이 · 최소 가로 = var(--control-height)`, () => {
      const hit = coarse.filter((r) => r.selectors.includes(sel));
      expect(hit.length, sel).toBeGreaterThanOrEqual(1);
      const d = hit.flatMap((r) => decls(r.body));
      expect(d).toContain('min-height: var(--control-height)');
      expect(d).toContain('min-width: var(--control-height)');
    });
  }
  it('22 `.backlink` 은 두 화면 한정 선택자 둘 다(미등록 미리보기 `.preview-page .backlink` 제외 · L1 몫)', () => {
    const sels = coarse.flatMap((r) => r.selectors);
    expect(sels).toContain('.detail-page .backlink');
    expect(sels).toContain('.project-detail .backlink');
    expect(sels.some((s) => s.includes('.preview-page'))).toBe(false);
  });
  it('21 `.notfound a` 는 글자 크기를 바꾸지 않고 inline-flex 누름 상자만', () => {
    const d = coarse.filter((r) => r.selectors.includes('.notfound a')).flatMap((r) => decls(r.body));
    expect(d).toContain('display: inline-flex');
    expect(d).toContain('align-items: center');
    expect(d.some((x) => x.startsWith('font'))).toBe(false);
  });
  it('640px · 900px 규칙과 같은 선택자(명시도 같음 · 뒤 순서가 이긴다)', () => {
    const narrow = shellRules.filter((r) => r.media === '@media (max-width: 640px)').flatMap((r) => r.selectors);
    expect(narrow).toContain('.gnb :is(.labswitch, .gnb-settings, .gnb-upload, .gnb-more, .avatar)');
    expect(narrow).toContain('.gnb .gnb-logout');
    expect(narrow).toContain('.theme-switcher');
    const mid = shellRules.filter((r) => r.media === '@media (max-width: 900px)').flatMap((r) => r.selectors);
    expect(mid).toContain('.gnb .mainnav a');
  });
  it('아바타 · 로그아웃 묶음은 터치에서 한 줄(1024 터치 막대 넘침 수정 · flex · 줄바꿈 없음)', () => {
    const wrap = coarse.filter((r) => r.selectors.includes('.gnb .avatar-wrap'));
    expect(wrap.length).toBe(1);
    expect(decls(wrap[0]?.body ?? '')).toEqual(['display: flex', 'align-items: center', 'white-space: nowrap']);
    // 마우스 쪽은 그대로 — 터치 블록 밖에서 묶음의 display 를 바꾸는 규칙 0(1440 마우스 픽셀 불변).
    const outside = shellRules.filter((r) => r.media !== COARSE && r.selectors.some((s) => s.includes('.avatar-wrap')));
    expect(outside.flatMap((r) => decls(r.body)).filter((d) => d.startsWith('display') || d.startsWith('white-space'))).toEqual([]);
  });
  it('로고 묶음(`.gnb a.brand`)은 터치에서 줄어들지 않는다(1024 터치 로고 표식 20.2 · 10.3 눌림 수정 · E 보고 §5-3)', () => {
    // 터치 44 의 min-width 가 자동 최소 폭(내용 폭)을 대신해 묶음이 내용보다 좁게 눌렸다. 표식만 막으면 글자가 묶음 밖으로 넘친다.
    const brand = coarse.filter((r) => r.selectors.length === 1 && r.selectors[0] === '.gnb a.brand');
    expect(brand.length).toBe(1);
    expect(decls(brand[0]?.body ?? '')).toEqual(['flex-shrink: 0']);
    // 마우스 쪽은 그대로 — 터치 블록 밖에서 로고 묶음 · 표식의 flex 를 바꾸는 규칙 0(1440 마우스 픽셀 불변).
    const outside = shellRules.filter(
      (r) => r.media !== COARSE && r.selectors.some((s) => /\.brand\b|\.logo\b/.test(s)),
    );
    expect(outside.length).toBeGreaterThan(0);
    expect(outside.flatMap((r) => decls(r.body)).filter((d) => d.startsWith('flex'))).toEqual([]);
  });
  it('터치 블록에 글자 크기 선언 0', () => {
    expect(coarse.flatMap((r) => decls(r.body)).filter((d) => d.startsWith('font'))).toEqual([]);
  });
  it('기본 · 프리미티브 CSS 에 `(pointer: coarse)` 단독 블록 0(프리미티브 `.btn-sm` 블록은 그대로)', () => {
    expect(rules(CSS.base).filter((r) => r.media === COARSE)).toEqual([]);
    expect(rules(CSS.primitives).filter((r) => r.media === COARSE)).toEqual([]);
    const sm = rules(CSS.primitives).filter((r) => r.media !== '' && r.selectors.includes('.btn-sm'));
    expect(sm.length).toBe(1);
    expect(sm[0]?.media).toBe(FLOOR);
  });
  it('토큰 층 터치 블록 = 선언 1(`--control-height: 44px`) 불변', () => {
    const t = rules(TOKENS).filter((r) => r.media === COARSE);
    expect(t.length).toBe(1);
    expect(decls(t[0]?.body ?? '')).toEqual(['--control-height: 44px']);
  });
  it('회귀 감시 50–53 토큰 하한 불변(`.btn` · `.btn-sm` · `:is(.inp, .sel)` 의 min-height = var(--control-height))', () => {
    expect(decls(only('primitives', '.btn').body)).toContain('min-height: var(--control-height)');
    expect(decls(rules(CSS.primitives).find((r) => r.media === FLOOR && r.selectors.includes('.btn-sm'))?.body ?? '')).toEqual([
      'min-height: var(--control-height)',
    ]);
    expect(decls(only('primitives', ':is(.inp, .sel)').body)).toContain('min-height: var(--control-height)');
  });
});
