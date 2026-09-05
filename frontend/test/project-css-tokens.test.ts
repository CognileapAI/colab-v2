/**
 * BF-11 — `project.css` 의 토큰 정합 · backrow/backlink 공용화 (정적 대조).
 *
 * 이 시험은 **규칙 원문**을 읽는다. jsdom 은 `var()` 의 미정의 여부를 계산값으로 말해 주지 않는다 —
 * 미정의 토큰은 조용히 폴백 리터럴로 그려지고, 폴백이 없으면 선언 자체가 버려진다.
 * 그래서 「무엇이 그려졌나」가 아니라 「무슨 이름을 참조하나」를 원문에서 센다.
 *
 * 입력은 전부 vite 의 `?raw` 다 — `node:fs` 를 쓰지 않는다
 * (`e01-apply-points.test.ts` 머리말의 2026-09-02 `main` 배포 불가 선례).
 * `vite.config.ts` 의 `test.css.include` 가 이 `?raw` id 들을 허용해야 문자열이 비지 않는다.
 */
import { describe, expect, it } from 'vitest';
import projectCss from '../src/components/project/project.css?raw';
import detailCss from '../src/components/detail/detail.css?raw';
import shellCss from '../src/shell/shell.css?raw';
import tokensCss from '../src/shell/tokens.css?raw';

/** `--이름: 값;` 으로 **정의된** 사용자 지정 속성 이름들. */
function definedNames(css: string): Set<string> {
  return new Set(Array.from(css.matchAll(/(--[a-z0-9-]+)\s*:/gi), (m) => m[1] as string));
}

/** `var(--이름` 으로 **참조된** 이름들. */
function referencedNames(css: string): string[] {
  return Array.from(new Set(Array.from(css.matchAll(/var\(\s*(--[a-z0-9-]+)/gi), (m) => m[1] as string)));
}

/** 폴백 리터럴이 달린 참조 — `var(--이름, 값)`. */
function referencesWithFallback(css: string): string[] {
  return Array.from(new Set(Array.from(css.matchAll(/var\(\s*(--[a-z0-9-]+)\s*,/gi), (m) => m[1] as string)));
}

describe('BF-11 · project.css 토큰 정합', () => {
  it('원문이 실려 있다 — 빈 문자열이면 시험이 아무것도 재지 않은 것이다', () => {
    for (const [name, css] of [
      ['project.css', projectCss],
      ['detail.css', detailCss],
      ['shell.css', shellCss],
      ['tokens.css', tokensCss],
    ] as const) {
      expect(
        css.length,
        `${name} 원문이 비었다 — vite.config.ts test.css.include 를 본다`,
      ).toBeGreaterThan(200);
    }
  });

  /**
   * 정본은 `shell/tokens.css` 다. 화면 CSS 가 제 화면에만 쓰는 값을 자기 `:root` 에 더하는 것은
   * 집 관례고(`detail.css`·`catalog.css` 머리 `:root`), 그 자리도 **선언된 이름**이다.
   * 막는 것은 「어디에도 정의가 없는 이름」이다 — 그것이 폴백 리터럴로만 그려지던 자리다.
   */
  it('project.css 가 참조하는 `--*` 는 tokens.css 또는 project.css 자신이 정의한다', () => {
    const known = new Set([...definedNames(tokensCss), ...definedNames(projectCss)]);
    const undefinedNames = referencedNames(projectCss).filter((n) => !known.has(n));
    expect(undefinedNames, `정의가 없는 토큰: ${undefinedNames.join(' · ')}`).toEqual([]);
  });

  it('project.css 에 폴백 리터럴이 남아 있지 않다 — 값의 정본이 두 곳으로 갈린다', () => {
    const withFallback = referencesWithFallback(projectCss);
    expect(withFallback, `폴백이 달린 참조: ${withFallback.join(' · ')}`).toEqual([]);
  });
});

describe('BF-11 · backrow/backlink 공용 한 벌', () => {
  it('공용 규칙은 shell.css 한 곳에 있다', () => {
    expect(shellCss).toMatch(/\.backrow\b/);
    expect(shellCss).toMatch(/\.backlink\b/);
  });

  it('detail.css · project.css 는 backrow/backlink 를 각자 다시 적지 않는다', () => {
    for (const [name, css] of [
      ['detail.css', detailCss],
      ['project.css', projectCss],
    ] as const) {
      expect(css, `${name} 에 backrow/backlink 사본이 남아 있다`).not.toMatch(/\.back(row|link)\b/);
    }
  });
});
