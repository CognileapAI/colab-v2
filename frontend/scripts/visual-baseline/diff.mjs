#!/usr/bin/env node
// Pixel comparison of two capture directories written by capture.py.
// Spec: dev-package/prd/specs/S-DESIGN-STRUCTURE-P0-20260924.md (P0).
//
//   node diff.mjs <baselineDir> <candidateDir> <reportDir>
//
// Exit 0 = every capture has 0 strict diff pixels.
// Exit 1 = at least one capture differs (strict: threshold 0, includeAA true); <reportDir>/<name>.diff.png written.
// Exit 78 = cannot compare: missing index.json/PNG, scene or capture sets differ, manifest sha256 differs, 0 captures.
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { comparePng } from './compare.mjs';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..', '..');
const READINESS = 78;
const rel = (p) => {
  const r = relative(ROOT, resolve(p));
  return r.startsWith('..') ? resolve(p) : r;
};

function notReady(message) {
  console.error(`::visual-diff-readiness:: ${message}`);
  process.exit(READINESS);
}

function readIndex(dir, side) {
  const file = resolve(dir, 'index.json');
  if (!existsSync(file)) notReady(`${side} index.json missing: ${rel(file)}`);
  try {
    return JSON.parse(readFileSync(file, 'utf8'));
  } catch (e) {
    notReady(`${side} index.json unreadable: ${e.message}`);
  }
}

const sameSet = (a, b) => a.length === b.length && [...a].sort().every((v, i) => v === [...b].sort()[i]);

function main(argv) {
  if (argv.length !== 3) notReady('usage: node diff.mjs <baselineDir> <candidateDir> <reportDir>');
  const [baseDir, candDir, reportDir] = argv;
  const base = readIndex(baseDir, 'baseline');
  const cand = readIndex(candDir, 'candidate');

  if (base.manifestSha256 !== cand.manifestSha256) {
    notReady(`manifest sha256 differs: baseline ${base.manifestSha256} vs candidate ${cand.manifestSha256}`);
  }
  if (!sameSet(base.scenes ?? [], cand.scenes ?? [])) notReady('scene sets differ between baseline and candidate');
  const baseNames = (base.captures ?? []).map((c) => c.name);
  const candNames = (cand.captures ?? []).map((c) => c.name);
  if (!sameSet(baseNames, candNames)) notReady('capture sets differ between baseline and candidate');
  if (baseNames.length === 0) notReady('0 captures to compare');

  const missing = [];
  for (const c of base.captures) {
    for (const dir of [baseDir, candDir]) {
      const file = resolve(dir, c.file);
      if (!existsSync(file)) missing.push(rel(file));
    }
  }
  if (missing.length) notReady(`PNG missing (${missing.length}): ${missing.join(', ')}`);

  mkdirSync(reportDir, { recursive: true });
  const rows = [];
  for (const c of base.captures) {
    const r = comparePng(readFileSync(resolve(baseDir, c.file)), readFileSync(resolve(candDir, c.file)));
    const row = {
      name: c.name, scene: c.scene, theme: c.theme, width: c.width,
      strict: r.strict, strictPct: (r.strict / r.totalPixels) * 100, lenient: r.lenient,
      sizeMismatch: r.sizeMismatch, pixels: r.totalPixels, diffImage: null,
    };
    if (r.strict > 0) {
      const out = resolve(reportDir, `${c.name}.diff.png`);
      writeFileSync(out, r.diffPng);
      row.diffImage = `${c.name}.diff.png`;
    }
    rows.push(row);
  }

  const red = rows.filter((r) => r.strict > 0);
  // Same HEAD, clean trees, same manifest: any difference is capture instability, not a code change.
  const sameHead = Boolean(base.gitHead) && base.gitHead === cand.gitHead && !base.gitDirty && !cand.gitDirty;
  const unstable = sameHead ? red.map((r) => r.name) : [];
  const exit = red.length ? 1 : 0;
  const side = (idx, dir) => ({
    dir: rel(dir), gitHead: idx.gitHead, gitDirty: idx.gitDirty, capturedAt: idx.capturedAt,
    captureCount: idx.captures.length, parallel: idx.parallel,
  });
  const report = {
    schema: 'colab-visual-diff/1',
    verdictSetting: { threshold: 0, includeAA: true },
    referenceSetting: { threshold: 0.1 },
    manifestSha256: base.manifestSha256,
    baseline: side(base, baseDir),
    candidate: side(cand, candDir),
    sameHead,
    exit,
    totals: {
      captures: rows.length,
      scenes: new Set(rows.map((r) => r.scene)).size,
      red: red.length,
      strictPixels: rows.reduce((s, r) => s + r.strict, 0),
      lenientPixels: rows.reduce((s, r) => s + r.lenient, 0),
      sizeMismatch: rows.filter((r) => r.sizeMismatch).length,
    },
    red: red.map((r) => r.name),
    unstable,
    rows,
  };
  writeFileSync(resolve(reportDir, 'report.json'), JSON.stringify(report, null, 2) + '\n');

  const pct = (v) => (v === 0 ? '0' : v < 0.001 ? '<0.001' : v.toFixed(3));
  const md = [
    '# 시각 대조 보고',
    '',
    `- 판정 설정: pixelmatch \`threshold 0\` · \`includeAA true\` (엄격). 보조 열: \`threshold 0.1\`.`,
    `- 기준: \`${report.baseline.dir}\` · HEAD \`${base.gitHead}\`${base.gitDirty ? ' (미커밋 변경 있음)' : ''} · ${base.capturedAt}`,
    `- 후보: \`${report.candidate.dir}\` · HEAD \`${cand.gitHead}\`${cand.gitDirty ? ' (미커밋 변경 있음)' : ''} · ${cand.capturedAt}`,
    `- 명세 sha256: \`${base.manifestSha256}\``,
    `- 캡처 ${report.totals.captures}장 · 장면 ${report.totals.scenes}개 · red ${red.length}장 · 엄격 차이 픽셀 합 ${report.totals.strictPixels} · 보조 차이 픽셀 합 ${report.totals.lenientPixels} · 크기 차이 ${report.totals.sizeMismatch}장`,
    `- 종료코드: **${exit}**`,
    '',
    '## red 목록',
    '',
    ...(red.length ? red.map((r) => `- \`${r.name}\` — 엄격 ${r.strict}px · 차이 이미지 \`${r.diffImage}\``) : ['없음']),
    '',
    '## 불안정 장면',
    '',
    sameHead
      ? (unstable.length ? unstable.map((n) => `- \`${n}\` (같은 HEAD 두 번 찍기에서 차이)`).join('\n') : '없음 (같은 HEAD 두 번 찍기 · 전 캡처 차이 0)')
      : '해당 없음 (기준·후보의 HEAD 가 다르거나 미커밋 변경이 있다 — 차이는 코드 변경 후보로 읽는다)',
    '',
    '## 캡처별 표',
    '',
    '| 캡처 | 엄격 px | 엄격 % | 보조 px | 크기 차이 |',
    '|---|---:|---:|---:|---|',
    ...rows.map((r) => `| \`${r.name}\` | ${r.strict} | ${pct(r.strictPct)} | ${r.lenient} | ${r.sizeMismatch ? '예' : '아니오'} |`),
    '',
  ].join('\n');
  writeFileSync(resolve(reportDir, 'report.md'), md);
  console.log(`${rows.length} captures · red ${red.length} · strict px ${report.totals.strictPixels} · exit ${exit}`);
  process.exit(exit);
}

main(process.argv.slice(2));
