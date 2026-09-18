/**
 * 이슈 #121 — 계정 관리 화면의 탭~카드 여백 소유자 단일화 · 계정 목록 표 열 폭 고정 · 액션 열 고정.
 *
 * 오라클 = `dev-package/prd/specs/2026-09-18-issue-121-account-admin-gap-table.md`
 *          「시험 결정 ⑴⑵」 ＋ 「advisor ① 검토 결과 A1·A2·A3·A4·A8」.
 *
 * 화면을 그리지 않고 **CSS 원문**을 읽어 잰다 — jsdom 은 배치를 계산하지 않아
 * 여백·열 폭·고정 열을 단위 시험으로 판정할 수 없다(레포 관행: `css-residual-rc11.test.ts`).
 * ⚠ 이 파일은 실브라우저 계측의 **대체가 아니다.** ⓐ~ⓕ·ⓘ 판정은 `dev-package/reports/issue-121/`
 *   의 `get box` 계측이 지고, 여기서는 그 계측이 재는 **선언이 실제로 서 있는지**만 잠근다.
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

const LOGIN = read('src/auth/login.css');
const MEMBERS = read('src/components/members/members.css');
const DESIGN = read('src/shell/design-system.css');

/** `선택자 {` 로 시작하는 규칙 한 덩이의 **선언부**. 없으면 null — 「없어야 할 것이 없다」로 통과하지 않게 한다. */
function rule(css: string, selector: string): string | null {
  const at = css.indexOf(selector + ' {');
  if (at < 0) return null;
  const open = css.indexOf('{', at);
  const close = css.indexOf('}', open);
  return close < 0 ? null : css.slice(open + 1, close);
}

/** `@media <질의> { … }` 한 덩이의 속. 중괄호 깊이를 세어 안쪽 규칙까지 통째로 돌려준다. */
function media(css: string, query: string): string {
  const at = css.indexOf('@media ' + query + ' {');
  if (at < 0) return '';
  const start = css.indexOf('{', at);
  let depth = 0;
  let i = start;
  for (; i < css.length; i += 1) {
    if (css[i] === '{') depth += 1;
    else if (css[i] === '}') { depth -= 1; if (depth === 0) break; }
  }
  return css.slice(start + 1, i);
}

const WIDE = media(LOGIN, '(min-width: 1024px)');
const NARROW = media(LOGIN, '(max-width: 640px)');

describe('⑴ 고쳐야 하는 선언이 실제로 서 있다', () => {
  it('탭~카드 여백의 소유자가 `.login.account-admin` 의 row-gap 하나다', () => {
    const container = rule(LOGIN, '.login.account-admin');
    expect(container).not.toBeNull();
    expect(container).toContain('row-gap: var(--space-section)');
    // 종전 소유자 둘을 같은 화면 범위에서 지운다 — 형제 마진이 더해지는 꼴을 버린다.
    expect(rule(LOGIN, '.login.account-admin .settabs')).toContain('margin-bottom: 0');
    expect(rule(LOGIN, '.account-list-card')).not.toContain('margin-top');
  });

  it('A8 `h1` 은 아래 마진만 덮는다 — `margin: 0` 은 제목 위 여백까지 지운다', () => {
    const h1 = rule(LOGIN, '.login.account-admin > h1');
    expect(h1).not.toBeNull();
    expect(h1).toContain('margin-block-end: 0');
    expect(h1).not.toMatch(/(^|;)\s*margin:/);
  });

  it('같은 grid 의 `message` 문단도 소유자 하나로 맞춘다', () => {
    expect(rule(LOGIN, '.login.account-admin > .account-status')).toContain('margin-top: 0');
  });

  it('A2 목록 패널이 grid 열 폭까지 늘고, 그 규칙에 `display` 가 없다', () => {
    const panel = rule(LOGIN, '.account-list-panel');
    expect(panel).not.toBeNull();
    expect(panel).toContain('justify-self: stretch');
    expect(panel).toContain('min-width: 0');
    // ⛔ `display` 를 선언하면 UA `[hidden] { display: none }` 이 깨져 숨은 탭이 보인다.
    expect(panel).not.toContain('display');
  });

  it('폭 상한은 `.account-list-card` 에만 오른다 — 공용 `.login-card` 는 360px 그대로', () => {
    expect(rule(LOGIN, '.account-list-card')).toContain('max-width: 1600px');
    expect(rule(LOGIN, '.login-card')).toContain('max-width: 360px');
  });

  it('표가 `table-layout: fixed` 와 열 폭 합계 `min-width` 를 갖는다', () => {
    const table = rule(LOGIN, '.account-table');
    expect(table).toContain('table-layout: fixed');
    expect(table).toContain('min-width: 1304px');
  });

  it('우려 6 — 열 폭은 `thead th` 에만 준다(`table-layout: fixed` 는 첫 행에서만 읽는다)', () => {
    // px 열 여섯 + 액션 열. 값은 HEAD 실측 max-content 에서 온다(보고서 `before-loaded.json`).
    const widths: Array<[number, string]> = [
      [2, '64px'], [3, '92px'], [4, '96px'], [5, '68px'], [6, '104px'], [7, '104px'], [8, '576px'],
    ];
    for (const [n, px] of widths) {
      expect(rule(LOGIN, `.account-table thead th:nth-child(${n})`)).toContain(`width: ${px}`);
    }
    // 이메일 열은 남은 폭을 받는다 — 폭 선언을 두지 않는다.
    expect(rule(LOGIN, '.account-table thead th:nth-child(1)')).toBeNull();
    // `td` 선택자에 폭을 주면 시험은 green 인데 화면은 안 바뀐다.
    expect(LOGIN).not.toMatch(/\.account-table\s+tbody\s+td:nth-child\(\d\)\s*\{[^}]*width:/);
  });

  it('A1 액션 `td` 는 table-cell 로 남고 flex 는 안쪽 div 가 진다', () => {
    expect(LOGIN).toContain('.account-table td.account-row-actions-cell');
    // ⛔ 액션 `td` 를 잡는 어떤 규칙도 `display` 를 선언하지 않는다 — 선언하면 익명 셀이
    //    담기 상자가 되어 그 위의 `position: sticky` 가 붙지 않는다(A1).
    const cellRules = LOGIN.match(/[^{}]*account-row-actions-cell[^{]*\{[^}]*\}/g) ?? [];
    expect(cellRules.length).toBeGreaterThan(0);
    for (const block of cellRules) expect(block).not.toContain('display');
    expect(rule(LOGIN, '.account-row-actions')).toContain('display: flex');
    // 버튼은 줄어들지 않는다 — 줄어들면 문면이 잘리고 클릭 영역이 좁아진다.
    expect(rule(LOGIN, '.account-row-actions > .btn')).toContain('flex: 0 0 auto');
  });

  it('A3 액션 열 고정은 `@media (min-width: 1024px)` 안에서만 걸린다', () => {
    expect(WIDE).not.toBe('');
    expect(WIDE).toContain('.account-table thead th:last-child');
    expect(WIDE).toContain('.account-table td.account-row-actions-cell');
    expect(WIDE).toContain('position: sticky');
    expect(WIDE).toContain('right: 0');
    // 우려 3 — 반투명이면 아래 행이 비쳐 보이고 `frontend-visual` 대비 판정이 서지 않는다.
    expect(WIDE).toContain('background: var(--color-surface)');
    // A4 1차안 — 경계는 보더로만. 그림자는 쓰지 않는다.
    expect(WIDE).toContain('border-left: 1px solid var(--color-border)');
    expect(WIDE).not.toContain('box-shadow');
    // 좁은 폭에서 고정하면 왼쪽 버튼이 영구히 가려진다 — 분기 밖에는 sticky 가 없다.
    expect(LOGIN.replace(WIDE, '')).not.toContain('position: sticky');
  });

  it('A3 ≤640px 에서는 액션 열이 HEAD 실측 폭으로 돌아가 같은 줄바꿈을 낸다', () => {
    expect(NARROW).toContain('flex-wrap: wrap');
    expect(rule(NARROW, '.account-table thead th:nth-child(8)')).toContain('width: 194px');
  });

  it('자유 문자열 셀은 생략 부호로 처리한다', () => {
    const text = rule(LOGIN, '.account-table td.account-cell-text');
    expect(text).toContain('overflow: hidden');
    expect(text).toContain('text-overflow: ellipsis');
    // 우려 7 — note 도 같은 처리를 받되 폭 0 으로 사라지지 않는다(액션 열 폭이 자리를 남긴다).
    const note = rule(LOGIN, '.account-row-note');
    expect(note).toContain('min-width: 0');
    expect(note).toContain('text-overflow: ellipsis');
  });
});

describe('⑵ 금지 조건 — 바뀌지 않아야 하는 원문이 그대로 있다', () => {
  it('본문 글자 크기를 줄이지 않았다', () => {
    expect(rule(LOGIN, '.account-table')).toContain('font-size: var(--text-body-sm)');
    expect(rule(LOGIN, '.account-row-note')).toContain('font-size: var(--text-caption)');
  });

  it('행 높이를 바꿀 선언을 건드리지 않았다', () => {
    const cells = rule(LOGIN, '.account-table th, .account-table td');
    expect(cells).toContain('padding: 10px 12px');
    expect(cells).toContain('white-space: nowrap');
    // `border-collapse` 를 바꾸면 행 높이가 함께 움직인다(A4).
    expect(rule(LOGIN, '.account-table')).toContain('border-collapse: collapse');
  });

  it('공용 `.login` · `.login-card` 기본 규칙이 그대로다', () => {
    expect(rule(LOGIN, '.login')).toBe(
      '\n  min-height: 100dvh;\n  display: grid;\n  place-items: center;\n' +
      '  grid-template-columns: minmax(0, 1fr);\n  background: var(--color-bg);\n  padding: 24px;\n',
    );
    expect(rule(LOGIN, '.login-card')).toContain('padding: 32px 28px');
  });

  it('공용 `.settabs`(members.css) 와 `.table-scroll-hint`(design-system.css) 를 고치지 않았다', () => {
    expect(rule(MEMBERS, '.settabs')).toContain('margin-bottom: 14px');
    // 이슈 제안의 1280px 분기를 새로 만들지 않는다 — 공용 1100px 분기 그대로.
    expect(DESIGN).toContain('.table-scroll-hint');
    expect(media(DESIGN, '(max-width: 1100px)')).toContain('.table-scroll-hint');
    expect(DESIGN).not.toMatch(/@media[^{]*1280px[^{]*\{[^}]*table-scroll-hint/);
  });
});
