// P2a (spec S-DESIGN-STRUCTURE-P2A-20260924) — test 전용 `@layer` 껍질 제거 플러그인.
// jsdom 29 는 `@layer` 블록 안 규칙을 계산값에 넣지 않는다. vite.config.ts 의 test 모드 플러그인이
// stylesheet 로 실리는 CSS 에서 `@layer a, b;` 문장과 `@layer x {` 껍질·짝 `}` 만 벗긴다.
// 이 우회 때문에 vitest 는 층 순서를 검증하지 못한다 — 층 판정의 증거는 실브라우저 캡처다.
import { stripLayerBlocks } from '../vite.config';

const LAYERED = [
  '@layer tokens, base, primitives, patterns, screens;',
  '@layer screens {',
  '/* 주석 속 @layer x { 와 } 는 그대로 */',
  '.a { color: rgb(255, 0, 0); content: "@layer y { }"; }',
  '@media (max-width: 640px) {',
  '  .a { color: rgb(0, 0, 255); }',
  '}',
  '}',
  '',
].join('\n');

describe('test 전용 @layer 껍질 제거', () => {
  it('층 선언 문장과 층 블록 껍질만 벗기고 규칙·중첩 @media·주석·문자열은 그대로 둔다', () => {
    const out = stripLayerBlocks(LAYERED);
    expect(out).not.toMatch(/^@layer/m);
    expect(out).toContain('/* 주석 속 @layer x { 와 } 는 그대로 */');
    expect(out).toContain('.a { color: rgb(255, 0, 0); content: "@layer y { }"; }');
    expect(out).toMatch(/@media \(max-width: 640px\) \{\n {2}\.a \{ color: rgb\(0, 0, 255\); \}\n\}/);
    const opens = out.replace(/\/\*[\s\S]*?\*\//g, '').replace(/"[^"]*"/g, '').split('{').length;
    const closes = out.replace(/\/\*[\s\S]*?\*\//g, '').replace(/"[^"]*"/g, '').split('}').length;
    expect(opens).toBe(closes);
  });

  it('층이 없는 CSS 는 바이트 그대로 돌려준다', () => {
    const plain = '.b { margin: 0; }\n@media (min-width: 1024px) { .b { margin: 4px; } }\n';
    expect(stripLayerBlocks(plain)).toBe(plain);
  });

  it('jsdom 은 층 블록 안 규칙을 계산값에 넣지 않고, 벗긴 CSS 는 넣는다', () => {
    const el = document.createElement('div');
    el.className = 'a';
    document.body.appendChild(el);
    const style = document.createElement('style');
    style.textContent = LAYERED;
    document.head.appendChild(style);
    const layered = getComputedStyle(el).color;
    style.textContent = stripLayerBlocks(LAYERED);
    const stripped = getComputedStyle(el).color;
    style.remove();
    el.remove();
    expect(layered).not.toBe('rgb(255, 0, 0)');
    expect(stripped).toBe('rgb(255, 0, 0)');
  });
});
