/**
 * 휴대폰·패드 대응 20260926 L2b — 화면 CSS(hover 감싸기 · 화면 16px 하한 삭제 · 터치 44).
 *
 * 오라클 = `dev-package/prd/specs/S-DEVICE-WIDTH-INPUT-20260926.md` V7(화면) · V8(화면) · V10(감싸기) ·
 * 구현 결정 「터치 규칙 CSS」 · 「입력 글자 하한 규칙」 · 「hover 감싸기」 · 부록 B(레인 L2b) · 부록 D(레인 L2b) ·
 * 부록 G(레인 L2b) · 우려 1ⓐ · 「레인 확정」 L2b 분할.
 * L2b-1(목록 · 검색 · 상세 · 계보 그래프 · 계보 · 승인 6파일)이 만들고, L2b-2(대시보드 · 프로젝트 · 구성원 · 변수 표 ·
 * 업로드 · 로그인 6파일)가 개수 단언을 spec 총합(hover 24 · 44 대상 34 · 화면 `@media` 16px 하한 0 · 12파일)으로 올렸다.
 * 원문 CSS 에서 주석을 걷고 규칙을 잘라 잰다(선례 L2a · jsdom 은 스타일을 계산하지 않는다).
 * 캡처 사각 대상(15–17 · 28 · 47–49)은 캡처 장면이 없어 이 시험의 CSS 규칙 존재 단언이 유일한 확인이다.
 *
 * L3b 가 넓히는 법(「레인 확정」 파일 끝 터치 블록 규칙 · 단언 삭제 0): 구성원 권한 체크 칸(36) · 변수 표 대표 라디오(45)의
 * 누름 칸 규칙을 `members.css` · `variableTable.css` 끝 `(pointer: coarse)` 블록 안에 넣을 때, 이 파일의 `TAPS` 에
 * `{ n: 36, file: 'members', block: [<label 선택자>] }` · `{ n: 45, file: 'variableTable', block: [...] }` 을 더하고
 * 「레인 L2b 34」 단언은 `lane` 이 L2b 인 번호만 대조하도록 두고 레인 L3b 2항목 단언을 옆에 더한다(`TAPS.length` 34 → 36).
 * 「체크 칸 · 대표 라디오 선택자 0」 시험(`L3B_ONLY`)은 그때 기대값을 L3b 선택자 목록으로 바꾼다(단언을 지우지 않는다).
 * 블록 = 1 · 파일 끝 단언은 그대로 둔다.
 */
// @ts-expect-error — 타입 선언 없이 런타임만 쓴다(vitest 는 node 위에서 돈다 · 선례 design-fix-20260924-L1).
import { readFileSync } from 'node:fs';
// @ts-expect-error — 같은 이유.
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

declare const process: { cwd(): string };

const raw = (rel: string): string => String(readFileSync(resolve(process.cwd(), rel), 'utf8'));
const strip = (css: string): string => css.replace(/\/\*[\s\S]*?\*\//g, '');

const FILES = {
  catalog: 'src/components/catalog/catalog.css',
  search: 'src/components/search/search.css',
  detail: 'src/components/detail/detail.css',
  lineageGraph: 'src/components/lineage/lineageGraph.css',
  lineage: 'src/components/lineage/lineage.css',
  approval: 'src/components/approval/approval.css',
  dashboard: 'src/components/dashboard/dashboard.css',
  project: 'src/components/project/project.css',
  members: 'src/components/members/members.css',
  variableTable: 'src/components/common/variableTable.css',
  upload: 'src/components/upload/upload.css',
  login: 'src/auth/login.css',
} as const;
type FileName = keyof typeof FILES;
const NAMES = Object.keys(FILES) as FileName[];
const CSS = Object.fromEntries(NAMES.map((f) => [f, strip(raw(FILES[f]))])) as Record<FileName, string>;
const TARGETS = JSON.parse(raw('scripts/visual-baseline/targets.json')) as {
  targets: { n: number; selector: string; lane: string; captureBlind?: boolean; measure?: string }[];
};

const HOVER = '@media (hover: hover)';
const COARSE = '@media (pointer: coarse)';
const CONTROL = 'var(--control-height)';

// ── 규칙 파서(선례 L2a 와 같은 규칙) ────────────────────────────────────────
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

const ALL = Object.fromEntries(NAMES.map((f) => [f, rules(CSS[f])])) as Record<FileName, Rule[]>;

// ── 대상 목록 ────────────────────────────────────────────────────────────
/** 부록 D 레인 L2b 11파일 — [파일, 선택자, 한 줄 원문, 원문 모양]. 규칙 24 · 선택자 24.
 *  목록 행 작업 칸 규칙(`catalog.css` hover + focus-within 한 줄)은 hover 쪽만 여기 있다(초점 쪽은 조건 없음 · 2단계 Q3ⓑ).
 *  원문 모양 `block` = 원문이 여러 줄 규칙이라 L2a 선례(셸 CSS)대로 `@media (hover: hover) {` 블록 안에 들여 쓴다
 *  (세 번째 원소는 그 규칙을 한 줄로 편 것 · 선언 대조용). 생략 = 한 줄 원문을 같은 줄에서 감싼다. */
const HOVERS: [FileName, string, string, 'block'?][] = [
  ['catalog', '.tbl tr.clk:hover td', '.tbl tr.clk:hover td { background: var(--color-surface-hover); }'],
  ['catalog', '.tbl tr.clk:hover td:first-child', '.tbl tr.clk:hover td:first-child { box-shadow: inset 2px 0 0 var(--color-primary-600); }'],
  ['catalog', '.tbl thead th > .thf:hover', '.tbl thead th > .thf:hover { background: var(--color-gray-100); }'],
  ['catalog', '.colmenu button.cm-i:hover', '.colmenu button.cm-i:hover { background: var(--color-gray-100); }'],
  ['catalog', '.colmenu .cm-clr:hover', '.colmenu .cm-clr:hover { background: var(--color-gray-100); color: var(--color-text); }'],
  ['catalog', '.tbl tbody tr:hover td.rowact .ra', '.tbl tbody tr:hover td.rowact .ra { opacity: 1; }'],
  ['catalog', '.tbl td.rowact .rab:hover', '.tbl td.rowact .rab:hover { border-color: var(--color-primary-600); color: var(--color-primary-700); }'],
  ['catalog', '.catalog-open:hover', '.catalog-open:hover { text-decoration: underline; text-underline-offset: 3px; }'],
  ['search', '.search-page .hit-name:hover', '.search-page .hit-name:hover { text-decoration: underline; }'],
  ['detail', '.detail-page .use-sec .use-t a:hover', '.detail-page .use-sec .use-t a:hover { text-decoration: underline; }'],
  ['detail', '.detail-page .dsec-menu-i:hover', '.detail-page .dsec-menu-i:hover { background: var(--color-gray-100); }'],
  ['lineageGraph', '.detail-page a.ln:hover', '.detail-page a.ln:hover { border-color: var(--color-primary-600); }'],
  ['lineageGraph', '.detail-page .lrow .ln-go:hover .ln-name', '.detail-page .lrow .ln-go:hover .ln-name { color: var(--color-primary-600); text-decoration: underline; text-underline-offset: 2px; }'],
  ['approval', '.dh-menu button:hover', '.dh-menu button:hover { background: var(--color-surface-hover); }'],
  ['dashboard', '.dash-open-catalog:hover', '.dash-open-catalog:hover { background: var(--color-surface-hover); }'],
  ['upload', '.btn-strong:where(:not(:disabled)):hover', '.btn-strong:where(:not(:disabled)):hover { background: var(--color-primary-700); }'],
  ['upload', '.thumbrow .th-slot:where(:not(:disabled)):hover', '.thumbrow .th-slot:where(:not(:disabled)):hover { border-color: var(--color-primary-600); }'],
  ['upload', '.dr-field:hover', '.dr-field:hover{border-color:var(--color-gray-400);}'],
  ['upload', '.dr-nav button:hover', '.dr-nav button:hover{background:var(--color-surface-hover);}'],
  ['upload', '.dr-cal-d:hover', '.dr-cal-d:hover{background:var(--color-primary-100);}'],
  ['upload', '.dr-useg button:hover', '.dr-useg button:hover{background:var(--color-surface-hover);}'],
  ['variableTable', '.vt-del:hover', '.vt-del:hover { color: var(--fg-danger); }', 'block'],
  ['variableTable', '.vt-add:hover', '.vt-add:hover { background: var(--color-surface-hover); }', 'block'],
  ['login', '.login-submit:hover:not(:disabled)', '.login-submit:hover:not(:disabled) { background: var(--color-primary-700); }', 'block'],
];

type Tap = { n: number; file: FileName; block: string[]; blind?: true; row?: true; text?: true; wide?: true };
/** 부록 B 레인 L2b — 34 개(L2b-1 13 ＋ L2b-2 21). 캡처 사각 15–17 · 28 · 47–49. 13 은 행 높이로 잰다(우려 1ⓐ · 링크 모양 불변).
 *  `text` = 글자 링크 · 탭(inline-flex 누름 상자만 키움 · 글자 크기 불변).
 *  `wide` = 가로만 모자란 대상(31 · 42 · 부록 B 「이미 세로 44 라 가로만」) — 터치 블록은 최소 가로만 둔다(advisor ① L2b-2).
 *  42 의 규칙은 셸 CSS 가 아니라 업로드 CSS 터치 블록에 둔다(advisor ① L2b-2 · 셸 CSS 변경 0). */
const TAPS: Tap[] = [
  { n: 13, file: 'catalog', block: ['.tbl tr.clk'], row: true },
  { n: 14, file: 'catalog', block: ['.tbl .rowact .rab'] },
  { n: 15, file: 'catalog', block: ['.colmenu button'], blind: true },
  { n: 16, file: 'catalog', block: ['.fchips .fc button'], blind: true },
  { n: 17, file: 'catalog', block: ['.fchips .fall'], blind: true },
  { n: 18, file: 'search', block: ['.search-page .hit-name'] },
  { n: 19, file: 'search', block: ['.crosslink a'], text: true },
  { n: 24, file: 'detail', block: ['.detail-page .dsec-menu-i'], text: true },
  { n: 25, file: 'detail', block: ['.detail-page .infogrid .ig .v .ig-more'] },
  { n: 26, file: 'lineageGraph', block: ['.detail-page .lrow .ln-go'] },
  { n: 27, file: 'lineageGraph', block: ['.detail-page .lin-use'] },
  { n: 28, file: 'detail', block: ['.detail-page .dt-edit.de-inline input', '.detail-page .dt-edit.de-inline select'], blind: true },
  { n: 46, file: 'lineage', block: ['.lin-link'] },
  { n: 8, file: 'dashboard', block: ['.dash-section-label'] },
  { n: 9, file: 'dashboard', block: ['.dash-quiet'] },
  { n: 10, file: 'dashboard', block: ['.dash-bar'] },
  { n: 11, file: 'dashboard', block: ['.titem button'] },
  { n: 12, file: 'dashboard', block: ['.todo-more', '.todo-all'] },
  { n: 31, file: 'project', block: ['.pj-views button'], wide: true },
  { n: 32, file: 'project', block: ['.pd-sect .quiet', 'td.right .quiet'] },
  { n: 33, file: 'project', block: ['.pd-linkurl'], text: true },
  { n: 34, file: 'project', block: ['.pj-seg button'] },
  { n: 35, file: 'members', block: ['.settabs .st'] },
  { n: 37, file: 'login', block: ['.login-input'] },
  { n: 38, file: 'login', block: ['.login-submit'] },
  { n: 39, file: 'upload', block: ['.regsteps .rs-x'] },
  { n: 40, file: 'upload', block: ['.up-preview-options > summary'] },
  { n: 41, file: 'upload', block: ['.up-file-management > summary'] },
  { n: 42, file: 'upload', block: ['.mapbar .btn-ghost'], wide: true },
  { n: 43, file: 'variableTable', block: ['.vt-del'] },
  { n: 44, file: 'variableTable', block: ['.vt-add'] },
  { n: 47, file: 'upload', block: ['.dr-nav button'], blind: true },
  { n: 48, file: 'upload', block: ['.dr-useg button'], blind: true },
  { n: 49, file: 'upload', block: ['.dr-cal-d'], blind: true },
];

/** 입력 글자 하한을 세는 선택자(V8 세는 범위) — `input` · `select` · `textarea` · `.inp` · `.sel`. */
const FIELD = /(^|[\s,(>+~])(input|select|textarea)(?![\w-])|\.(inp|sel)(?![\w-])/;
const isFloor = (r: Rule): boolean =>
  r.media !== '' && r.selectors.some((s) => FIELD.test(s)) && decls(r.body).some((d) => /^font-size:.*16px/.test(d));

const coarseOf = (f: FileName): Rule[] => ALL[f].filter((r) => r.media === COARSE);

// ── 시험 ─────────────────────────────────────────────────────────────────

describe('대상 개수(green-by-skip 방지 · spec 총합)', () => {
  it('hover 규칙 = 24 · 선택자 24(목록 8 · 검색 1 · 상세 2 · 계보 그래프 2 · 계보 0 · 승인 1 · 대시보드 1 · 프로젝트 0 · 구성원 0 · 변수 표 2 · 업로드 6 · 로그인 1)', () => {
    expect(HOVERS.length).toBe(24);
    expect(new Set(HOVERS.map(([, sel]) => sel)).size).toBe(24);
    const per = (f: FileName) => HOVERS.filter(([x]) => x === f).length;
    expect(NAMES).toEqual(['catalog', 'search', 'detail', 'lineageGraph', 'lineage', 'approval', 'dashboard', 'project', 'members', 'variableTable', 'upload', 'login']);
    expect(NAMES.map(per)).toEqual([8, 1, 2, 2, 0, 1, 1, 0, 0, 2, 6, 1]);
  });
  it('터치 44 대상 = 34 · 캡처 사각 7(15–17 · 28 · 47–49) · 가로만 2(31 · 42) · 대상 목록(targets.json)의 레인 L2b 34 와 같은 번호', () => {
    expect(TAPS.length).toBe(34);
    expect(TAPS.map((t) => t.n).sort((a, b) => a - b)).toEqual([
      8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 24, 25, 26, 27, 28, 31, 32, 33, 34, 35, 37, 38, 39, 40, 41, 42, 43, 44, 46, 47, 48, 49,
    ]);
    expect(TAPS.filter((t) => t.blind).map((t) => t.n)).toEqual([15, 16, 17, 28, 47, 48, 49]);
    expect(TAPS.filter((t) => t.wide).map((t) => t.n)).toEqual([31, 42]);
    const lane = TARGETS.targets.filter((t) => t.lane === 'L2b');
    expect(lane.length).toBe(34);
    expect(lane.map((t) => t.n).sort((a, b) => a - b)).toEqual(TAPS.map((t) => t.n).sort((a, b) => a - b));
    expect(lane.filter((t) => t.captureBlind).map((t) => t.n)).toEqual([15, 16, 17, 28, 47, 48, 49]);
    expect(lane.filter((t) => t.measure === 'row').map((t) => t.n)).toEqual([13]);
  });
});

describe('V10 · hover 감싸기(spec 총합 24규칙)', () => {
  for (const [file, sel, line, form] of HOVERS) {
    it(`${file} \`${sel}\` → \`${HOVER}\` 안 · 선언 불변 · ${form === 'block' ? '여러 줄 원문을 블록 안에 들여 씀' : '한 줄 원문 유지'}`, () => {
      const found = ALL[file].filter((r) => r.selectors.includes(sel));
      expect(found.length, `규칙 수: ${file} ${sel}`).toBe(1);
      expect(found[0]?.media).toBe(HOVER);
      expect(found[0]?.selectors).toEqual([sel]);
      const want = decls(line.slice(line.indexOf('{') + 1, line.lastIndexOf('}')));
      expect(decls(found[0]?.body ?? '')).toEqual(want);
      if (form === 'block') expect(raw(FILES[file])).toContain(`${HOVER} {\n  ${sel} {\n`);
      else expect(raw(FILES[file])).toContain(`${HOVER} { ${line} }`);
    });
  }
  it('열두 파일의 `:hover` 규칙 = 24 · 모두 `(hover: hover)` 안(조건 밖 0)', () => {
    const all = NAMES.flatMap((f) => ALL[f].filter((r) => r.selectors.some((s) => s.includes(':hover'))));
    expect(all.length).toBe(24);
    expect(all.filter((r) => r.media !== HOVER)).toEqual([]);
  });
  it('목록 행 작업 칸: 초점(`:focus-within`) 쪽은 조건 없이 따로 남는다 · hover 와 묶인 규칙 0', () => {
    const focus = ALL.catalog.filter((r) => r.selectors.includes('.tbl td.rowact .ra:focus-within'));
    expect(focus.length).toBe(1);
    expect(focus[0]?.media).toBe('');
    expect(focus[0]?.selectors).toEqual(['.tbl td.rowact .ra:focus-within']);
    expect(decls(focus[0]?.body ?? '')).toEqual(['opacity: 1']);
    const mixed = NAMES.flatMap((f) =>
      ALL[f].filter((r) => r.selectors.some((s) => s.includes(':hover')) && r.selectors.some((s) => s.includes(':focus'))),
    );
    expect(mixed).toEqual([]);
  });
});

describe('V8 · 화면 16px 하한 삭제(부록 G 레인 L2b 5곳 · 목록 · 검색 · 프로젝트 2 · 로그인)', () => {
  it('열두 파일의 `@media` 안 입력 16px 하한 = 0(하한은 셸 CSS 한 곳 · 새 하한 0)', () => {
    expect(NAMES.length).toBe(12);
    expect(NAMES.flatMap((f) => ALL[f].filter(isFloor))).toEqual([]);
  });
  it('프로젝트 입력 · 글상자: 640px 블록의 16px 규칙만 빠지고 나머지 규칙은 그대로', () => {
    const back = ALL.project.find(
      (r) => r.media === '@media (max-width: 640px)' && r.selectors.includes('.pj-modal-back') && decls(r.body).join() === 'padding: 16px',
    );
    expect(back).toBeTruthy();
    const block = ALL.project.filter((r) => r.media === '@media (max-width: 640px)' && r.top === back?.top);
    expect(block.map((r) => r.selectors.join(', '))).toEqual(['.pj-modal-back', '.pj-modal', '.pj-cards']);
    expect(ALL.project.filter((r) => r.media !== '' && r.selectors.some((s) => s === '.pj-inp' || s === '.pj-tarea'))).toEqual([]);
  });
  it('프로젝트 조정 선택: 640px 규칙에서 `font-size` 선언만 빠지고 `width: 100%` 는 남는다', () => {
    const sel = ALL.project.filter((r) => r.media === '@media (max-width: 640px)' && r.selectors.includes('.pj-ctl select'));
    expect(sel.length).toBe(1);
    expect(decls(sel[0]?.body ?? '')).toEqual(['width: 100%']);
    const block = ALL.project.filter((r) => r.media === '@media (max-width: 640px)' && r.top === sel[0]?.top);
    expect(block.map((r) => r.selectors.join(', '))).toEqual(['.pj-toolbar', '.pj-ctl', '.pj-ctl select', '.pj-count']);
  });
  it('로그인 입력: 한 규칙뿐인 640px 블록째 삭제 · 기본 규칙은 그대로', () => {
    expect(ALL.login.filter((r) => r.media === '@media (max-width: 640px)' && r.selectors.includes('.login-input'))).toEqual([]);
    expect(ALL.login.filter((r) => r.media === '' && r.selectors.includes('.login-input')).length).toBe(1);
    expect(ALL.login.filter((r) => r.media === '@media (max-width: 640px)').map((r) => r.selectors.join(', '))).toEqual([
      '.account-row-actions',
      '.account-table thead th:nth-child(8)',
    ]);
  });
  it('업로드 끌어다 놓기 큰 글자(`.dropzone .big` 16px)는 하한이 아니라 기본 크기라 그대로(부록 G 계수 제외)', () => {
    const big = ALL.upload.filter((r) => r.selectors.includes('.dropzone .big'));
    expect(big.length).toBe(1);
    expect(big[0]?.media).toBe('');
    expect(decls(big[0]?.body ?? '')).toContain('font-size: 16px');
  });
  it('목록 필터 선택: 640px 블록의 16px 규칙만 빠지고 나머지 규칙은 그대로', () => {
    const narrowDesc = ALL.catalog.find((r) => r.media === '@media (max-width: 640px)' && r.selectors.includes('.catalog-page .desc'));
    expect(narrowDesc).toBeTruthy();
    const block = ALL.catalog.filter((r) => r.media === '@media (max-width: 640px)' && r.top === narrowDesc?.top);
    expect(block.map((r) => r.selectors.join(', '))).toEqual(['.catalog-page', '.catalog-filters', '.catalog-page .desc']);
    expect(ALL.catalog.filter((r) => r.media !== '' && r.selectors.includes('.catalog-filters select'))).toEqual([]);
  });
  it('검색 입력: 한 줄 640px 블록째 삭제 · 기본 규칙은 그대로', () => {
    expect(ALL.search.filter((r) => r.media !== '' && r.selectors.includes('.search-hero input'))).toEqual([]);
    expect(ALL.search.filter((r) => r.media === '' && r.selectors.includes('.search-hero input')).length).toBe(1);
  });
  it('열두 파일에 강제 우선(`!important`) 0', () => {
    for (const f of NAMES) expect(CSS[f], f).not.toContain('!important');
  });
});

describe('V7 · 터치 44(부록 B 레인 L2b 34 · 화면 CSS 끝 `(pointer: coarse)` 블록 하나)', () => {
  const tapFiles = [...new Set(TAPS.map((t) => t.file))];
  it('대상이 있는 11파일은 `(pointer: coarse)` 블록 = 1 · 파일 끝 블록 · 승인 CSS 는 0', () => {
    expect(tapFiles).toEqual([
      'catalog', 'search', 'detail', 'lineageGraph', 'lineage', 'dashboard', 'project', 'members', 'login', 'upload', 'variableTable',
    ]);
    for (const f of tapFiles) {
      const tops = new Set(coarseOf(f).map((r) => r.top));
      expect(tops.size, f).toBe(1);
      expect([...tops][0], f).toBe(Math.max(...ALL[f].map((r) => r.top)));
    }
    expect(coarseOf('approval')).toEqual([]);
  });
  it('터치 블록 선택자 = 대상 선택자뿐(다른 규칙을 끼워 넣지 않는다)', () => {
    for (const f of tapFiles) {
      const want = TAPS.filter((t) => t.file === f).flatMap((t) => t.block).sort();
      expect(coarseOf(f).flatMap((r) => r.selectors).sort(), f).toEqual(want);
    }
  });
  for (const t of TAPS) {
    const label = `${t.n}${t.blind ? '(캡처 사각 · CSS 규칙 존재 단언)' : ''}${t.row ? '(행 높이로 잼)' : ''}${t.wide ? '(가로만)' : ''}`;
    const what = t.row ? '행 높이' : t.wide ? '최소 가로' : '최소 높이 · 최소 가로';
    it(`${label} \`${t.block.join(', ')}\` → ${what} = ${CONTROL}`, () => {
      for (const sel of t.block) {
        const d = coarseOf(t.file).filter((r) => r.selectors.includes(sel)).flatMap((r) => decls(r.body));
        expect(d.length, `${t.file} ${sel}`).toBeGreaterThan(0);
        if (t.row) {
          expect(d).toEqual([`height: ${CONTROL}`]);
        } else if (t.wide) {
          expect(d).toEqual([`min-width: ${CONTROL}`]);
        } else {
          expect(d).toContain(`min-height: ${CONTROL}`);
          expect(d).toContain(`min-width: ${CONTROL}`);
        }
        if (t.text) {
          expect(d).toContain('display: inline-flex');
          expect(d).toContain('align-items: center');
        }
      }
    });
  }
  it('터치 블록에 글자 크기 선언 0(글자 링크 · 탭은 누름 상자만 키운다)', () => {
    for (const f of tapFiles) expect(coarseOf(f).flatMap((r) => decls(r.body)).filter((d) => d.startsWith('font')), f).toEqual([]);
  });
  it('우려 1ⓐ — 13 「열기」 링크 자체와 20 검색 중단 문장 속 링크는 터치 블록에 없다', () => {
    const sels = tapFiles.flatMap((f) => coarseOf(f).flatMap((r) => r.selectors));
    expect(sels.some((s) => s.includes('.catalog-open'))).toBe(false);
    expect(sels.some((s) => s.includes('.notice'))).toBe(false);
  });
  it('명시도: 14 · 15 는 640px 규칙과 같은 선택자 · 28 은 기본 규칙과 같은 선택자(뒤 순서가 이긴다)', () => {
    const narrow = ALL.catalog.filter((r) => r.media === '@media (max-width: 640px)').flatMap((r) => r.selectors);
    expect(narrow).toContain('.tbl .rowact .rab');
    expect(narrow).toContain('.colmenu button');
    const base = ALL.detail.filter((r) => r.media === '' && r.selectors.includes('.detail-page .dt-edit.de-inline input'));
    expect(base.length).toBe(1);
    expect(base[0]?.selectors).toEqual(['.detail-page .dt-edit.de-inline input', '.detail-page .dt-edit.de-inline select']);
    expect(decls(base[0]?.body ?? '')).toContain('min-height: 40px');
  });
  it('상세 CSS 순서: L1a 의 머리 파일 경로 줄바꿈 규칙 뒤에 터치 블록(파일 끝)', () => {
    const wrap = ALL.detail.filter(
      (r) => r.media === '' && r.selectors.includes('.detail-page .dh-file') && decls(r.body).join() === 'overflow-wrap: anywhere',
    );
    expect(wrap.length).toBe(1);
    const coarseTop = coarseOf('detail')[0]?.top ?? -1;
    expect(wrap[0]!.top).toBeLessThan(coarseTop);
    expect(coarseTop).toBe(Math.max(...ALL.detail.map((r) => r.top)));
  });
  // 640px 이하 규칙과 선택자를 함께 쓰는 대상(advisor ① L2b-2 · L2b-1 14 · 15 선례): 같은 선택자 · 같은 명시도라
  // 파일 끝 터치 블록이 뒤 순서로 이긴다. 640px 규칙은 원문 그대로 둔다(「기존 640px 이하 44 규칙은 옮기지 않는다」).
  const NARROW_SHARED: [FileName, string, string[]][] = [
    ['dashboard', '.dash-bar', ['min-height: 44px', 'grid-template-columns: 96px minmax(0, 1fr) 36px']],
    ['project', '.pj-seg button', ['min-height: 44px']],
    ['upload', '.dr-cal-d', ['height: 44px']],
  ];
  for (const [file, sel, narrowDecls] of NARROW_SHARED) {
    it(`명시도 · 순서: \`${sel}\` 640px 규칙(원문 그대로) 뒤에 같은 선택자의 터치 블록 규칙`, () => {
      const narrow = ALL[file].filter((r) => r.media === '@media (max-width: 640px)' && r.selectors.includes(sel));
      expect(narrow.length, `${file} ${sel} 640px`).toBe(1);
      expect(narrow[0]?.selectors).toEqual([sel]);
      expect(decls(narrow[0]?.body ?? '')).toEqual(narrowDecls);
      const coarse = coarseOf(file).filter((r) => r.selectors.includes(sel));
      expect(coarse.length, `${file} ${sel} coarse`).toBe(1);
      expect(narrow[0]!.top).toBeLessThan(coarse[0]!.top);
    });
  }
  it('업로드 720px 블록 6개(규칙 7)는 이번에 옮기지 · 바꾸지 않는다(다음 intent · advisor ① L2b-2)', () => {
    const n720 = ALL.upload.filter((r) => /^@media\s*\(max-width:\s*720px\)$/.test(r.media));
    expect(n720.map((r) => `${r.selectors.join(', ')} { ${decls(r.body).join('; ')} }`)).toEqual([
      '.regsteps .rs-f { display: none }',
      '.form-2 { grid-template-columns: 1fr }',
      '.form-3 { grid-template-columns: minmax(0, 1fr) }',
      '.reg-actions .uf-hint { display: none }',
      '.modal-takeover[data-scene="register"] .up-body { padding:16px 16px 88px }',
      '.up-empty .reggate .rg-t { font-size:13px }',
      '.modal-takeover[data-scene="register"] .regsteps .rs-f { max-width:100%; margin:4px 0 }',
    ]);
    expect(new Set(n720.map((r) => r.top)).size).toBe(6);
  });
  // L3b 앞 경계(advisor ① L2b-2): 구성원 · 변수 표 터치 블록에는 35 · 43 · 44 만 있다. 체크 칸(36) · 대표 라디오(45)는 L3b 몫.
  const L3B_ONLY = /input|checkbox|radio|label|\.pc\b|memtbl|vartable/;
  it('구성원 · 변수 표 터치 블록 = 35 · 43 · 44 선택자뿐 · 체크 칸 · 대표 라디오 선택자 0(L3b 몫)', () => {
    expect(coarseOf('members').flatMap((r) => r.selectors)).toEqual(['.settabs .st']);
    expect(coarseOf('variableTable').flatMap((r) => r.selectors).sort()).toEqual(['.vt-add', '.vt-del']);
    for (const f of ['members', 'variableTable'] as const) {
      expect(coarseOf(f).flatMap((r) => r.selectors).filter((s) => L3B_ONLY.test(s)), f).toEqual([]);
    }
  });
  it('42 확장보기 단추(`.mapbar .btn-ghost`) 규칙은 업로드 CSS 터치 블록에만 있다(셸 · 프리미티브 CSS 변경 0)', () => {
    const hits = NAMES.flatMap((f) => coarseOf(f).filter((r) => r.selectors.includes('.mapbar .btn-ghost')).map(() => f));
    expect(hits).toEqual(['upload']);
  });
});
