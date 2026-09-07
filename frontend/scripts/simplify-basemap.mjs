#!/usr/bin/env node
/**
 * Natural Earth 1:110m 원본 GeoJSON → **레포 반입용 간략화본** (WU-C5 · 축 ①-⑤b).
 *
 * ⚠ 지리를 잘라내지 않는다 — Ted 판정 「다른 지역이 나올 수도 있다」. 동아시아 자르기 **금지**.
 *   줄이는 것은 **표현의 군더더기**뿐이다.
 *
 *   ⑴ `properties`·`bbox`·`crs` 제거 — 배경 선을 긋는 데 쓰지 않는 필드다.
 *   ⑵ 좌표를 소수점 **3자리**로 반올림(≈ 110 m) — 1:110m 원본의 실제 정밀도보다 곱다.
 *   ⑶ 반올림 뒤 **연속 중복 점** 제거(2점 미만이 되는 조각은 버린다).
 *   ⑷ 들여쓰기 없는 한 줄 JSON.
 *
 * 사용 — `node frontend/scripts/simplify-basemap.mjs <입력> <출력>`
 */
import { readFileSync, writeFileSync } from 'node:fs';

const DECIMALS = 3;
const r = (v) => Number(v.toFixed(DECIMALS));

function line(coords) {
  const out = [];
  for (const [lon, lat] of coords) {
    const p = [r(lon), r(lat)];
    const last = out[out.length - 1];
    if (last && last[0] === p[0] && last[1] === p[1]) continue;
    out.push(p);
  }
  return out.length >= 2 ? out : null;
}

function geometry(g) {
  if (!g) return null;
  if (g.type === 'LineString') {
    const c = line(g.coordinates);
    return c ? { type: 'LineString', coordinates: c } : null;
  }
  if (g.type === 'MultiLineString') {
    const c = g.coordinates.map(line).filter(Boolean);
    return c.length ? { type: 'MultiLineString', coordinates: c } : null;
  }
  throw new Error(`지원하지 않는 geometry: ${g.type}`);
}

const [, , inPath, outPath] = process.argv;
if (!inPath || !outPath) {
  console.error('usage: simplify-basemap.mjs <in.geojson> <out.geojson>');
  process.exit(2);
}
const src = JSON.parse(readFileSync(inPath, 'utf8'));
const features = src.features
  .map((f) => {
    const geo = geometry(f.geometry);
    return geo ? { type: 'Feature', properties: {}, geometry: geo } : null;
  })
  .filter(Boolean);
writeFileSync(outPath, JSON.stringify({ type: 'FeatureCollection', features }));
console.log(`${outPath}: features ${features.length}`);
