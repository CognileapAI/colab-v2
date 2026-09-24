/**
 * design-fix 20260924 · 잔여 정리 레인 F-final.
 *
 * 오라클 = `dev-package/prd/specs/S-DESIGN-FIX-20260924.md` 「잔여 정리 레인 F-final」 1–5 ＋ 「통합 수정」 값 19.
 * 1(A21 값 19)은 `design-fix-20260924-L2.test.tsx` 고정값과 `design-fix-20260924-F-css.test.ts` 「누름 ≠ hover」 표가,
 * 4(FU-1)는 `design-fix-20260924-F-upload.test.tsx` 가 잰다. 여기서는 2 · 3 · 5(주석 공백)를 잰다.
 * 방식은 F-css 시험과 같다 — 원문에서 주석을 걷고 선택자 목록을 잘라 잰다(jsdom 은 스타일을 계산하지 않는다).
 */
// @ts-expect-error — 타입 선언 없이 런타임만 쓴다(vitest 는 node 위에서 돈다 · 선례와 같은 규율).
import { readFileSync } from 'node:fs';
// @ts-expect-error — 같은 이유.
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

declare const process: { cwd(): string };

const raw = (rel: string): string => String(readFileSync(resolve(process.cwd(), rel), 'utf8'));
const strip = (css: string): string => css.replace(/\/\*[\s\S]*?\*\//g, '');

/** 규칙의 선택자(쉼표 목록을 괄호 밖에서만 가른다). `@layer` · `@media` 안으로 들어가고 그 밖 @-규칙은 재지 않는다. */
function selectorsOf(css: string): { selector: string; body: string }[] {
  const out: { selector: string; body: string }[] = [];
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
    if (head.startsWith('@layer') || head.startsWith('@media')) out.push(...selectorsOf(css.slice(open + 1, j - 1)));
    else if (!head.startsWith('@')) {
      const body = css.slice(open + 1, j - 1);
      let paren = 0;
      let cur = '';
      for (const ch of head) {
        if (ch === '(') paren += 1;
        if (ch === ')') paren -= 1;
        if (ch === ',' && paren === 0) {
          out.push({ selector: cur.trim().replace(/\s+/g, ' '), body });
          cur = '';
        } else cur += ch;
      }
      if (cur.trim()) out.push({ selector: cur.trim().replace(/\s+/g, ' '), body });
    }
    i = j;
  }
  return out;
}

describe('F-final 3 · `.btn-strong` hover 는 비활성 단추를 뺀다(A2 와 같은 결함)', () => {
  const hovers = selectorsOf(strip(raw('src/components/upload/upload.css'))).filter(
    (r) => /^\.btn-strong\b/.test(r.selector) && r.selector.includes(':hover'),
  );
  it('upload.css 의 `.btn-strong` hover 선택자는 하나 이상 · 모두 `:disabled` 를 `:where()` 안에서 뺀다(특이도 무변)', () => {
    expect(hovers.length).toBeGreaterThan(0);
    for (const r of hovers) expect(r.selector, r.selector).toMatch(/:where\([^{]*:not\([^{]*:disabled[^{]*\)[^{]*\)/);
  });
  it('값은 그대로 primary-700(새 값 없음)', () => {
    for (const r of hovers) expect(r.body.replace(/\s+/g, ' ')).toContain('background: var(--color-primary-700)');
  });
});

describe('F-final 2 · 값 19 는 Ted 확정 — 정본에 A21 판정 대기가 없다', () => {
  const DOC = raw('../docs/design-system.md');
  const section = (head: string): string => {
    const from = DOC.indexOf(`\n## ${head}`);
    const to = DOC.indexOf('\n## ', from + 1);
    return DOC.slice(from, to < 0 ? undefined : to);
  };
  it('⑤ 누름 피드백 줄에 「⑦ 판정 대기」 지시가 없다', () => {
    const line = section('⑤').split('\n').find((l) => l.startsWith('- 누름 피드백')) ?? '';
    expect(line).toContain('--color-surface-pressed');
    expect(line).not.toContain('판정 대기');
  });
  it('⑦ 판정 대기 목록에 업로드 달력 누름(A21) 행이 없다', () => {
    const rows = section('⑦')
      .split('\n')
      .filter((l) => l.startsWith('|') && (l.includes('.dr-nav button') || l.includes('A21')));
    expect(rows).toEqual([]);
  });
});

describe('F-final 5 · `spring.ts` 닫힌 식 주석 공백(FP-3)', () => {
  it('「닫힌 식 `x(t)」 — 식 앞 공백', () => {
    const src = raw('src/components/preview/spring.ts');
    expect(src).toContain('닫힌 식 `x(t)');
    expect(src).not.toContain('닫힌 식`');
  });
});
