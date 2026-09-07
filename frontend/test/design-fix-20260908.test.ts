/**
 * WU-B11 · 디자인 검수 「있음」 6건 — CSS 계측 시험 (PRD-29 후속).
 *
 * 오라클 = `dev-package/prd/rounds/R-B-4-verify.md §2-A` 수용 기준 7건.
 * 판정표 = `dev-package/sessions/p3-design-audit-20260905.md` (WU-A11).
 * 화면을 그리지 않고 CSS 원문을 읽어 잰다 — jsdom 은 스타일을 계산하지 않는다.
 *
 *   ㈎ ⑥ `.catalog-page .card` 그림자 0건 · 팝오버 `.colmenu` 는 유지
 *   ㈏ ⑦ `lineageGraph.css` 13px 미만 `font-size` 0건
 *   ㈐ ⑧ 지목된 캡션 7곳 13px 이상
 *   ㈑ ⑨ 상세 컨테이너 ↔ 칸 구분선 토큰 상이 · 카탈로그 바깥선 ≥ 안쪽선 진하기
 *   ㈒ ⑩ 지목된 음수 상쇄 2건 0건
 *   ㈓ ⑪ 덮인 `display` 0건 ＋ 미정의 토큰 참조 0건
 */
// @ts-expect-error — 타입 선언 없이 런타임만 쓴다(vitest 는 node 위에서 돈다 · `lv-rules` 와 같은 규율).
import { readFileSync } from 'node:fs';
// @ts-expect-error — 같은 이유.
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

// vitest 의 실행 뿌리는 `frontend/` 다(`vite.config.ts` 자리 · `lv-rules` 와 같은 규율).
declare const process: { cwd(): string };

/** 주석은 걷어내고 읽는다 — 선언만 잰다(주석 속 선택자·값이 계측에 섞이지 않도록). */
const read = (rel: string): string =>
  String(readFileSync(resolve(process.cwd(), rel), 'utf8')).replace(/\/\*[\s\S]*?\*\//g, '');

const TOKENS = read('src/shell/tokens.css');
const SHELL = read('src/shell/shell.css');
const LINEAGE_GRAPH = read('src/components/lineage/lineageGraph.css');
const CATALOG = read('src/components/catalog/catalog.css');
const DETAIL = read('src/components/detail/detail.css');
const UPLOAD = read('src/components/upload/upload.css');

/** 선택자 하나의 선언 블록(`{ … }`)을 원문에서 잘라낸다. */
function block(css: string, selector: string): string {
  const at = css.indexOf(selector);
  expect(at, `선택자 부재: ${selector}`).toBeGreaterThan(-1);
  const open = css.indexOf('{', at);
  const close = css.indexOf('}', open);
  return css.slice(open + 1, close);
}

/** 블록 안 `font-size` 값(px). */
function fontPx(css: string, selector: string): number {
  const m = block(css, selector).match(/font-size:\s*([\d.]+)px/);
  if (!m) throw new Error(`font-size 부재: ${selector}`);
  return Number(m[1]);
}

/** `:root` 에 선 토큰 이름을 모은다. */
function defined(css: string): Set<string> {
  const set = new Set<string>();
  for (const m of css.matchAll(/(--[a-z0-9-]+)\s*:/g)) if (m[1]) set.add(m[1]);
  return set;
}

/** 6자리 hex → WCAG 상대휘도. 값이 클수록 밝다(＝ 연하다). */
function luminance(hex: string): number {
  const ch = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255);
  const lin = ch.map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4)) as [number, number, number];
  return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2];
}

/** 토큰 이름 → hex 값(정의처 여럿을 훑는다). */
function tokenHex(name: string): string {
  for (const css of [TOKENS, CATALOG, DETAIL]) {
    const m = css.match(new RegExp(`${name}:\\s*(#[0-9a-fA-F]{6})`));
    if (m?.[1]) return m[1];
  }
  throw new Error(`토큰 값 부재: ${name}`);
}

describe('WU-B11 ㈎ ⑥ 카드 그림자', () => {
  it('`.catalog-page .card` 에 그림자가 없다', () => {
    expect(block(CATALOG, '.catalog-page .card')).not.toMatch(/box-shadow/);
  });
  it('팝오버 `.colmenu` 는 그림자를 유지한다', () => {
    expect(block(CATALOG, '.colmenu')).toMatch(/box-shadow:\s*var\(--shadow-lg\)/);
  });
});

describe('WU-B11 ㈏ ⑦ 계보 그래프 라벨', () => {
  it('`lineageGraph.css` 에 13px 미만 `font-size` 선언이 0건이다', () => {
    const small = [...LINEAGE_GRAPH.matchAll(/font-size:\s*([\d.]+)px/g)]
      .map((m) => Number(m[1]))
      .filter((px) => px < 13);
    expect(small).toEqual([]);
  });
});

describe('WU-B11 ㈐ ⑧ 캡션 7곳', () => {
  const spots: [string, string][] = [
    ['detail.css', '.detail-page .filelist .fl-x'],
    ['detail.css', '.detail-page .filelist .fl-k'],
    ['upload.css', '.up-note'],
    ['lineageGraph.css', '.detail-page .lin-empty .muted'],
    ['lineageGraph.css', '.detail-page .lrow .ln-sub'],
    ['lineageGraph.css', '.detail-page .lrow .ln-name'],
  ];
  const src: Record<string, string> = {
    'detail.css': DETAIL,
    'upload.css': UPLOAD,
    'lineageGraph.css': LINEAGE_GRAPH,
  };
  for (const [file, sel] of spots) {
    it(`${file} ${sel} 가 13px 이상이다`, () => {
      expect(fontPx(src[file] ?? '', sel)).toBeGreaterThanOrEqual(13);
    });
  }
  it('오류 본문 `.vizerr, .warn` 은 이미 13px 이라 그대로다', () => {
    expect(fontPx(UPLOAD, '.vizerr, .warn')).toBe(13);
  });
});

describe('WU-B11 ㈑ ⑨ 보더 2층', () => {
  it('상세 컨테이너와 칸 구분선이 서로 다른 토큰이다', () => {
    const outer = block(DETAIL, '.detail-page .infogrid').match(/border:\s*1px solid var\((--[a-z-]+)\)/);
    const inner = block(DETAIL, '.detail-page .infogrid .ig ').match(/border-right:\s*1px solid var\((--[a-z-]+)\)/);
    if (!outer?.[1] || !inner?.[1]) throw new Error('보더 토큰 참조 부재');
    expect(outer[1]).not.toBe(inner[1]);
  });
  it('카탈로그 바깥선이 안쪽선보다 진하거나 같다', () => {
    const outer = block(CATALOG, '.catalog-page .card').match(/border:\s*1px solid var\((--[a-z-]+)\)/);
    const inner = block(CATALOG, '.tbl th ').match(/border-bottom:\s*1px solid var\((--[a-z-]+)\)/);
    if (!outer?.[1] || !inner?.[1]) throw new Error('보더 토큰 참조 부재');
    const lo = luminance(tokenHex(outer[1]));
    const li = luminance(tokenHex(inner[1]));
    expect(lo).toBeLessThanOrEqual(li);
  });
});

describe('WU-B11 ㈒ ⑩ 여백 소유권', () => {
  it('상세 파일 목록에 음수 상쇄가 없다', () => {
    expect(block(DETAIL, '.detail-page .filelist ')).not.toMatch(/margin[a-z-]*:[^;]*\s-\d/);
  });
  it('되돌아가기 링크에 음수 상쇄가 없다', () => {
    expect(block(SHELL, '.project-detail .backlink')).not.toMatch(/margin[a-z-]*:[^;]*\s-\d/);
  });
  it('컨테이너가 여백을 소유한다 — 업로드 카드 본문이 gap 을 진다', () => {
    expect(block(UPLOAD, '.up-card > .card-b')).toMatch(/gap:/);
  });
});

describe('WU-B11 ㈓ ⑪ 죽은 스타일', () => {
  it('`.lin-way` 에 덮인 `display` 선언이 없다', () => {
    const decls = [...block(LINEAGE_GRAPH, '.detail-page .lin-way').matchAll(/(^|;)\s*display:/g)];
    expect(decls.length).toBe(1);
  });
  it('`lineageGraph.css` 에 미정의 토큰 참조가 0건이다', () => {
    const known = new Set([...defined(TOKENS), ...defined(DETAIL)]);
    const missing = [...LINEAGE_GRAPH.matchAll(/var\((--[a-z0-9-]+)\)/g)]
      .map((m) => m[1] ?? '')
      .filter((name) => !known.has(name));
    expect([...new Set(missing)]).toEqual([]);
  });
});
