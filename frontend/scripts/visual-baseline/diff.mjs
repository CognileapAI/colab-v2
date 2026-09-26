#!/usr/bin/env node
// Pixel comparison of two capture directories written by capture.py.
// Spec: dev-package/prd/specs/S-DESIGN-STRUCTURE-P0-20260924.md (P0).
//
//   node diff.mjs [--subset] [--viewport <id>[,<id>...]] <baselineDir> <candidateDir> <reportDir>
//
// --viewport (spec S-DEVICE-WIDTH-INPUT-20260926 L0a): compare only the captures whose `viewport` id (index.json
//   schema 2) is listed — e.g. `--viewport 1440` for the mouse-only baseline. Applied on both sides after the scene /
//   manifest checks; the selected capture sets must still match. 0 selected captures (unknown id, schema-1 index
//   without `viewport`) is 78. Different from --subset, which narrows scenes, not viewports.
//
// --subset (P5 · spec S-DESIGN-STRUCTURE-P5-20260924): compare only the scenes present on both sides and skip the
//   manifest sha256 check — for linking a baseline taken before a scene was added to one taken after it. Both
//   manifest hashes and the scenes left out on each side are written to the report. Within the common scenes the
//   capture sets must still match; 0 common scenes is 78.
// Exit 0 = every capture has 0 strict diff pixels.
// Exit 1 = at least one capture differs (strict: threshold 0, includeAA true); <reportDir>/<name>.diff.png written.
// Exit 78 = cannot compare: missing index.json/PNG, scene or capture sets differ, manifest sha256 differs, 0 captures
//   (with --subset: no common scene, or capture sets differ within the common scenes).
import { createHash } from 'node:crypto';
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
  const usage = 'usage: node diff.mjs [--subset] [--viewport <id>[,<id>...]] <baselineDir> <candidateDir> <reportDir>';
  let subset = false;
  let viewportFilter = null;
  while (argv[0]?.startsWith('--')) {
    const flag = argv.shift();
    if (flag === '--subset') subset = true;
    else if (flag === '--viewport') {
      const ids = (argv.shift() ?? '').split(',').filter(Boolean);
      if (!ids.length) notReady(`--viewport needs an id list · ${usage}`);
      viewportFilter = ids;
    } else notReady(`unknown flag ${flag} · ${usage}`);
  }
  if (argv.length !== 3) notReady(usage);
  const [baseDir, candDir, reportDir] = argv;
  const base = readIndex(baseDir, 'baseline');
  const cand = readIndex(candDir, 'candidate');

  let baseCaps = base.captures ?? [];
  let candCaps = cand.captures ?? [];
  let subsetInfo = null;
  if (subset) {
    const bs = new Set(base.scenes ?? []);
    const cs = new Set(cand.scenes ?? []);
    const common = [...bs].filter((s) => cs.has(s));
    if (!common.length) notReady('--subset: no common scenes between baseline and candidate');
    subsetInfo = {
      baselineManifestSha256: base.manifestSha256, candidateManifestSha256: cand.manifestSha256,
      commonScenes: common.length, onlyBaseline: [...bs].filter((s) => !cs.has(s)), onlyCandidate: [...cs].filter((s) => !bs.has(s)),
    };
    baseCaps = baseCaps.filter((c) => cs.has(c.scene));
    candCaps = candCaps.filter((c) => bs.has(c.scene));
  } else {
    if (base.manifestSha256 !== cand.manifestSha256) {
      notReady(`manifest sha256 differs: baseline ${base.manifestSha256} vs candidate ${cand.manifestSha256}`);
    }
    if (!sameSet(base.scenes ?? [], cand.scenes ?? [])) notReady('scene sets differ between baseline and candidate');
  }
  if (viewportFilter) {
    const keep = new Set(viewportFilter);
    baseCaps = baseCaps.filter((c) => keep.has(c.viewport));
    candCaps = candCaps.filter((c) => keep.has(c.viewport));
    if (!baseCaps.length || !candCaps.length) notReady(`--viewport ${viewportFilter.join(',')}: 0 captures selected`);
  }
  const baseNames = baseCaps.map((c) => c.name);
  const candNames = candCaps.map((c) => c.name);
  if (!sameSet(baseNames, candNames)) notReady('capture sets differ between baseline and candidate');
  if (baseNames.length === 0) notReady('0 captures to compare');

  const missing = [];
  for (const c of baseCaps) {
    for (const dir of [baseDir, candDir]) {
      const file = resolve(dir, c.file);
      if (!existsSync(file)) missing.push(rel(file));
    }
  }
  if (missing.length) notReady(`PNG missing (${missing.length}): ${missing.join(', ')}`);

  mkdirSync(reportDir, { recursive: true });
  const rows = [];
  const candBy = new Map(candCaps.map((c) => [c.name, c]));
  const sha = (buf) => createHash('sha256').update(buf).digest('hex');
  for (const c of baseCaps) {
    const a = readFileSync(resolve(baseDir, c.file));
    const b = readFileSync(resolve(candDir, c.file));
    // A PNG whose bytes no longer match its own index.json was changed after capture.
    const edited = sha(a) !== c.sha256 || sha(b) !== candBy.get(c.name).sha256;
    const r = comparePng(a, b);
    const row = {
      name: c.name, scene: c.scene, theme: c.theme, viewport: c.viewport ?? null, width: c.width,
      strict: r.strict, strictPct: (r.strict / r.totalPixels) * 100, lenient: r.lenient,
      sizeMismatch: r.sizeMismatch, pixels: r.totalPixels, editedAfterCapture: edited, diffImage: null,
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
  const unstable = sameHead ? red.filter((r) => !r.editedAfterCapture).map((r) => r.name) : [];
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
    subset: subsetInfo,
    viewportFilter,
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
    ...(subsetInfo ? [`- **부분집합 대조(--subset)** — 공통 장면 ${subsetInfo.commonScenes}개만 비교 · 명세 sha256 기준 \`${subsetInfo.baselineManifestSha256}\` / 후보 \`${subsetInfo.candidateManifestSha256}\` · 기준에만 있는 장면: ${subsetInfo.onlyBaseline.join(', ') || '없음'} · 후보에만 있는 장면: ${subsetInfo.onlyCandidate.join(', ') || '없음'}`] : []),
    ...(viewportFilter ? [`- **뷰포트 거르기(--viewport)** — ${viewportFilter.join(', ')} 의 캡처만 비교`] : []),
    `- 캡처 ${report.totals.captures}장 · 장면 ${report.totals.scenes}개 · red ${red.length}장 · 엄격 차이 픽셀 합 ${report.totals.strictPixels} · 보조 차이 픽셀 합 ${report.totals.lenientPixels} · 크기 차이 ${report.totals.sizeMismatch}장`,
    `- 종료코드: **${exit}**`,
    '',
    '## red 목록',
    '',
    ...(red.length ? red.map((r) => `- \`${r.name}\` — 엄격 ${r.strict}px · 차이 이미지 \`${r.diffImage}\`${r.editedAfterCapture ? ' · PNG 가 캡처 뒤 바뀜(index.json sha256 불일치)' : ''}`) : ['없음']),
    '',
    '## 불안정 장면',
    '',
    sameHead
      ? (unstable.length ? unstable.map((n) => `- \`${n}\` (같은 HEAD 두 번 찍기에서 차이)`).join('\n') : red.length ? '없음 (red 는 모두 캡처 뒤 바뀐 PNG 다)' : '없음 (같은 HEAD 두 번 찍기 · 전 캡처 차이 0)')
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
