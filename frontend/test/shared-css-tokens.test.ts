/** BF-13: 화면 로컬 토큰의 위치와 값을 유지하고, 같은 이름의 값이 갈리는 것만 막는다. */
import { describe, expect, it } from 'vitest';
import catalog from '../src/components/catalog/catalog.css?raw';
import detail from '../src/components/detail/detail.css?raw';
import project from '../src/components/project/project.css?raw';

type Declaration = { file: string; value: string };
const sources = { catalog, detail, project };

function declarations(inputs: Record<string, string>): Map<string, Declaration[]> {
  const result = new Map<string, Declaration[]>();
  for (const [file, raw] of Object.entries(inputs)) {
    const css = raw.replace(/\/\*[\s\S]*?\*\//g, '');
    for (const block of css.matchAll(/:root\s*\{([^{}]*)\}/g)) {
      for (const match of block[1]!.matchAll(/(--[a-z0-9-]+)\s*:\s*([^;]+)(?:;|$)/gi)) {
        const entries = result.get(match[1]!) ?? [];
        entries.push({ file, value: match[2]!.trim() });
        result.set(match[1]!, entries);
      }
    }
  }
  return result;
}

function conflicts(inputs: Record<string, string>): string[] {
  return [...declarations(inputs)]
    .filter(([, entries]) => new Set(entries.map(entry => entry.file)).size > 1
      && new Set(entries.map(entry => entry.value)).size > 1)
    .map(([name, entries]) => `${name}: ${entries.map(entry => `${entry.file}=${entry.value}`).join(' · ')}`);
}

describe('BF-13 · 화면 CSS 공통 토큰 값', () => {
  it('세 raw 원문과 실제 공통 선언을 읽는다', () => {
    for (const [file, css] of Object.entries(sources)) {
      expect(css.length, `${file} raw CSS가 비었다`).toBeGreaterThan(200);
      expect(declarations({ [file]: css }).size).toBeGreaterThan(0);
    }
    expect([...declarations(sources).values()].filter(
      entries => new Set(entries.map(entry => entry.file)).size > 1,
    ).length).toBeGreaterThan(0);
  });

  it('둘 이상의 화면이 정의한 같은 이름은 값이 글자 그대로 같다', () => {
    expect(conflicts(sources)).toEqual([]);
  });

  it('마지막 선언의 세미콜론을 생략해도 값 불일치를 검출한다', () => {
    expect(conflicts({
      first: ':root { --color-shared: #ffffff; }',
      second: ':root { --color-shared: #000000 }',
    })).toHaveLength(1);
  });

  it('각 공통 토큰의 한쪽 값을 바꾸면 그 이름의 불일치를 검출한다', () => {
    for (const [name, entries] of declarations(sources)) {
      if (new Set(entries.map(entry => entry.file)).size < 2) continue;
      const file = entries[0]!.file as keyof typeof sources;
      const mutated = { ...sources, [file]: sources[file].replace(
        new RegExp(`(${name}\\s*:\\s*)[^;]+;`), '$1BF13-MUTATED;',
      ) };
      expect(conflicts(mutated).some(issue => issue.startsWith(`${name}:`)), name).toBe(true);
    }
  });
});
