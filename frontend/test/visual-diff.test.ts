/**
 * 디자인 구조 P0 — 픽셀 대조 함수(`scripts/visual-baseline/compare.mjs`)를 PNG 픽스처 4종으로 잠근다.
 *
 * 오라클 = `dev-package/prd/specs/S-DESIGN-STRUCTURE-P0-20260924.md` 「시험 결정 ⓓ」.
 * 판정은 엄격 설정(threshold 0 · includeAA true)이고, 보조 열은 threshold 0.1 이다.
 * 픽스처 PNG 는 시험 안에서 pngjs 로 만든다(`encodePng` · 바이너리 커밋 없음). 실제 브라우저 없이 돈다.
 */
import { describe, expect, it } from 'vitest';
import { comparePng, decodePng, encodePng } from '../scripts/visual-baseline/compare.mjs';

type Rgba = readonly [number, number, number, number];

/** 한 색으로 칠한 w×h PNG. `paint` 로 개별 픽셀을 덮어쓴다. */
function png(w: number, h: number, fill: Rgba, paint: {x: number; y: number; c: Rgba}[] = []): Uint8Array {
  const data = new Uint8Array(w * h * 4);
  for (let i = 0; i < w * h; i++) data.set(fill, i * 4);
  for (const p of paint) data.set(p.c, (p.y * w + p.x) * 4);
  return encodePng({width: w, height: h, data});
}

const GREY: Rgba = [100, 100, 100, 255];

describe('visual-diff compare — PNG 픽스처 4종(동일 · 1픽셀 다름 · 미세 색 1픽셀 · 크기 다름)', () => {
  it('① 동일한 두 장 → 엄격 0 · 보조 0 · 크기 일치', () => {
    const r = comparePng(png(8, 6, GREY), png(8, 6, GREY));
    expect(r).toMatchObject({strict: 0, lenient: 0, sizeMismatch: false, width: 8, height: 6, totalPixels: 48});
  });

  it('② 1픽셀이 완전히 다르면 → 엄격 1 · 보조 1 · 차이 이미지는 같은 크기의 PNG', () => {
    const r = comparePng(png(8, 6, GREY), png(8, 6, GREY, [{x: 3, y: 2, c: [255, 255, 255, 255]}]));
    expect(r.strict).toBe(1);
    expect(r.lenient).toBe(1);
    expect(r.sizeMismatch).toBe(false);
    const diff = decodePng(r.diffPng);
    expect([diff.width, diff.height]).toEqual([8, 6]);
  });

  it('③ 미세한 색 차이 1픽셀(R 100→101) → 엄격 1 · 보조 0 — 판정은 엄격 값을 쓴다', () => {
    const r = comparePng(png(8, 6, GREY), png(8, 6, GREY, [{x: 5, y: 4, c: [101, 100, 100, 255]}]));
    expect(r.strict).toBe(1);
    expect(r.lenient).toBe(0);
  });

  it('④ 크기가 다르면 → 크기 차이 표기 · 겹치지 않는 영역을 차이로 센다', () => {
    const r = comparePng(png(8, 6, GREY), png(9, 6, GREY));
    expect(r.sizeMismatch).toBe(true);
    expect([r.width, r.height]).toEqual([9, 6]);
    expect(r.strict).toBe(6);
    expect(r.lenient).toBe(6);
  });
});
