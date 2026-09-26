#!/usr/bin/env node
// Numeric judge of capture metrics written by capture.py (--metrics / --metrics-only · measure.js).
// Spec: dev-package/prd/specs/S-DEVICE-WIDTH-INPUT-20260926.md 「구현 결정 · 수치 판정 스크립트」 · 부록 B · 부록 I (L0b).
// A pure function (judge / links) plus a CLI. Not a gate: lanes run it on their own numeric-only captures.
//
//   node judge.mjs [--lane L1|L2a|L2b|L3a|L3b] [--targets <targets.json>] [--exempt <judge-exempt.txt>] [--out <report.json>] <dir|file>...
//   node judge.mjs --links [--targets <targets.json>] [--out <report.json>] <dir|file>...
//
// Inputs: `*.metrics.json` files (a directory is read one level deep), the target list (부록 B) and the exemption list
// (`지표 · 선택자 · 사유`).
// Red: target tap box < 44 (1–49 both axes · 50–53 height only · an element also matched by 1–49 is judged only there) ·
//   input text < 16 · unclipped horizontal overflow roots > 0 · occlusion by the four tools (legend · value lookup ·
//   coordinates · screenshot) > 0 in an occlusion-judged scene whose map cell (section.pv-map width) is < 810 ·
//   exemption lines with a format error, an empty reason, an unknown metric, or (without --lane) no match (a hole).
// Recorded only: zoom group (+ fit button) occlusion, `upload-preview-expand` occlusion, map cell ≥ 810, touch-action,
//   drag axis, value panel state, small tap targets outside the list.
// Not measured (「재지 않음」, not red): a matched element without a box (display none · width or height 0).
// --lane: judge only that lane's targets (+ 50–53) plus 16 and overflow (occlusion: L1 only). Red outside the filter is
//   counted only. A lane target without the capture-blind mark that never has a box in any file of the run is 78.
// --links: for 390 touch files, the scenes where each target has a box. Every L1–L3b target that is neither capture
//   blind nor width hidden needs one scene of its own lane (50–53: any lane scene), and a declared scene that was
//   measured must draw the target; otherwise 78 with the target numbers.
// Exit 0 = no red · 1 = red · 78 = cannot judge (no files, malformed or stale metrics, map cell width missing in an
//   occlusion-judged scene, occlusion not measured, a scene whose declared targets all match nothing, unmeasured lane
//   target, unknown lane or flag).
import { existsSync, readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

export const METRICS_SCHEMA = 'colab-visual-metrics/1';
export const OCCLUSION_SCENES = ['detail-preview-map', 'detail-preview-map-value', 'preview-done'];
export const MAP_BOUNDARY = 810;
export const MIN_TAP = 44;
export const MIN_FONT = 16;
export const LANES = ['L1', 'L2a', 'L2b', 'L3a', 'L3b'];
export const EXEMPT_METRICS = ['44', '16', '넘침'];
const READINESS = 78;
const HERE = dirname(fileURLToPath(import.meta.url));

/** `지표 · 선택자 · 사유` lines. Comments (#) and blank lines are skipped; every other bad line is an error. */
export function parseExempt(text) {
  const lines = [];
  const errors = [];
  String(text).split(/\r?\n/).forEach((raw, i) => {
    const line = i + 1;
    const trimmed = raw.trim();
    if (!trimmed || trimmed.startsWith('#')) return;
    const parts = raw.split('·').map((p) => p.trim());
    const bad = (why) => errors.push({ line, text: trimmed, why });
    if (parts.length < 3) return bad('칸 수 오류(지표 · 선택자 · 사유)');
    const [metric, selector] = parts;
    const reason = parts.slice(2).join(' · ').trim();
    if (!EXEMPT_METRICS.includes(metric)) return bad(`모르는 지표 ${metric}`);
    if (!selector) return bad('빈 선택자');
    if (!reason) return bad('빈 사유');
    lines.push({ line, metric, selector, reason });
  });
  return { lines, errors };
}

const capName = (m) => `${m.scene}-${m.theme}-${m.viewport}`;

function checkShape(m, targetNs) {
  const problems = [];
  if (!m || m.schema !== METRICS_SCHEMA) return [`schema ${m?.schema} is not ${METRICS_SCHEMA}`];
  for (const key of ['scene', 'theme', 'viewport']) if (typeof m[key] !== 'string' || !m[key]) problems.push(`${key} missing`);
  if (!(m.width > 0 && m.height > 0)) problems.push('width/height missing');
  if (m.input !== 'touch' && m.input !== 'mouse') problems.push(`input ${m.input}`);
  if (!m.overflow || !Array.isArray(m.overflow.roots)) problems.push('overflow missing');
  if (m.input === 'touch') {
    if (!Array.isArray(m.targets)) problems.push('targets missing (touch)');
    else {
      const got = m.targets.map((t) => t.n).join(',');
      if (got !== targetNs.join(',')) problems.push('target numbers differ from the target list (measured with another list)');
      for (const t of m.targets) {
        if (t.error) problems.push(`target ${t.n}: ${t.error}`);
        else if (!Array.isArray(t.hits)) problems.push(`target ${t.n}: hits missing`);
      }
    }
    if (!m.inputFont || !Array.isArray(m.inputFont.small)) problems.push('inputFont missing (touch)');
  }
  return problems;
}

/**
 * @param {{metrics: object[], targets: {laneScenes: Record<string,string[]>, targets: object[]}, exempt: {lines: object[], errors: object[]}, lane?: string|null}} input
 */
export function judge({ metrics, targets, exempt, lane = null }) {
  const readiness = [];
  const red = [];
  const recorded = [];
  const outsideRed = { 44: 0, 16: 0, 넘침: 0, 가림: 0 };
  const list = targets.targets;
  const targetNs = list.map((t) => t.n);
  const byN = new Map(list.map((t) => [t.n, t]));
  const laneOn = lane !== null && lane !== undefined;
  if (laneOn && !LANES.includes(lane)) readiness.push(`unknown lane ${lane} (known: ${LANES.join(', ')})`);
  if (!metrics.length) readiness.push('0 metrics files');
  const exemptKey = JSON.stringify(exempt.lines.map((l) => ({ metric: l.metric, selector: l.selector })));
  const used = new Set();
  let exemptHits = 0;
  let notMeasured = 0;
  let smallOther = 0;
  const measured = new Set();
  for (const e of exempt.errors) red.push({ metric: '면제', capture: null, line: e.line, value: e.text, why: e.why });

  const in44 = (t) => !laneOn || t.lane === lane || t.lane === '—';
  const inOcclusion = !laneOn || lane === 'L1';
  const push = (item, inside) => {
    if (inside) red.push(item);
    else outsideRed[item.metric] += 1;
  };
  const exempted = (idxs, metric) => {
    const hit = (idxs ?? []).filter((i) => exempt.lines[i]?.metric === metric);
    if (!hit.length) return false;
    hit.forEach((i) => used.add(i));
    exemptHits += 1;
    return true;
  };

  for (const m of metrics) {
    const cap = m && m.scene ? capName(m) : '(unnamed)';
    const problems = checkShape(m, targetNs);
    if (problems.length) {
      readiness.push(`${cap}: ${problems.join('; ')}`);
      continue;
    }
    if (JSON.stringify(m.exemptList ?? null) !== exemptKey) {
      readiness.push(`${cap}: measured with another exemption list — measure again after changing judge-exempt.txt`);
      continue;
    }
    if (m.input === 'touch') {
      const entry = new Map(m.targets.map((t) => [t.n, t]));
      const claimed = new Set(m.targets.filter((t) => t.n <= 49).flatMap((t) => t.hits.map((h) => h.id)));
      for (const t of m.targets) {
        const target = byN.get(t.n);
        for (const h of t.hits) {
          if (!h.box) {
            notMeasured += 1;
            continue;
          }
          measured.add(t.n);
          if (target.heightOnly && claimed.has(h.id)) continue;
          const small = target.heightOnly ? h.h < MIN_TAP : h.w < MIN_TAP || h.h < MIN_TAP;
          if (!small || exempted(h.exempt, '44')) continue;
          push({ metric: '44', capture: cap, n: t.n, selector: target.selector, value: `${h.w}x${h.h}`, path: h.path }, in44(target));
        }
      }
      const declared = list.filter((t) => !t.captureBlind && t.scenes.includes(m.scene));
      if (declared.length && declared.every((t) => (entry.get(t.n)?.hits.length ?? 0) === 0)) {
        readiness.push(`${cap}: none of the targets declared for scene ${m.scene} matched (${declared.map((t) => t.n).join(', ')})`);
      }
      smallOther += m.smallOther?.count ?? 0;
      for (const f of m.inputFont.small) {
        if (exempted(f.exempt, '16')) continue;
        push({ metric: '16', capture: cap, value: f.fontSize, path: f.path }, true);
      }
    }
    for (const r of m.overflow.roots) {
      if (exempted(r.exempt, '넘침')) continue;
      push({ metric: '넘침', capture: cap, value: r.right, path: r.path }, true);
    }
    if (OCCLUSION_SCENES.includes(m.scene)) {
      const cell = m.map?.cellWidth;
      if (!(typeof cell === 'number' && cell > 0)) {
        readiness.push(`${cap}: map cell width (section.pv-map) missing in an occlusion-judged scene`);
        continue;
      }
      if (cell < MAP_BOUNDARY) {
        const cov = m.map.coverage;
        if (!cov || typeof cov.fourTools !== 'number') {
          readiness.push(`${cap}: occlusion not measured (map cell ${cell} < ${MAP_BOUNDARY})`);
          continue;
        }
        if (cov.fourTools > 0) push({ metric: '가림', capture: cap, value: cov.fourTools, cellWidth: cell }, inOcclusion);
      }
    }
    if (m.map) {
      recorded.push({
        capture: cap, cellWidth: m.map.cellWidth ?? null, judged: OCCLUSION_SCENES.includes(m.scene) && m.map.cellWidth < MAP_BOUNDARY,
        fourTools: m.map.coverage?.fourTools ?? null, zoomGroup: m.map.coverage?.zoomGroup ?? null, tools: m.map.coverage?.tools ?? null,
        touchAction: m.map.touchAction ?? null, dragAxis: m.map.dragAxis ?? null, valueState: m.map.valueState ?? null,
      });
    }
  }

  const scoped = laneOn ? list.filter((t) => t.lane === lane) : list;
  const unmeasured = laneOn ? scoped.filter((t) => !t.captureBlind && !measured.has(t.n)).map((t) => t.n) : [];
  if (unmeasured.length) readiness.push(`lane ${lane} targets never measured with a box: ${unmeasured.join(', ')}`);
  const unusedLines = exempt.lines.filter((_, i) => !used.has(i));
  const exemptHoles = laneOn ? [] : unusedLines;
  for (const l of exemptHoles) red.push({ metric: '면제', capture: null, line: l.line, value: `${l.metric} · ${l.selector}`, why: '구멍(맞는 것 없음)' });
  const code = readiness.length ? READINESS : red.length ? 1 : 0;
  return {
    code, lane: laneOn ? lane : null, files: metrics.length, readiness, red, outsideRed, unmeasured, notMeasured,
    captureBlind: scoped.filter((t) => t.captureBlind).length, exemptHits, exemptHoles, exemptUnused: laneOn ? unusedLines : [],
    smallOther, recorded,
  };
}

/** Scenes where each target has a box in the 390 touch files, and the linking rule (부록 I L0b). */
export function links({ metrics, targets }) {
  const drawn = new Map(targets.targets.map((t) => [t.n, new Set()]));
  const measuredScenes = new Set();
  for (const m of metrics) {
    if (m?.viewport !== '390' || m.input !== 'touch' || !Array.isArray(m.targets)) continue;
    measuredScenes.add(m.scene);
    for (const t of m.targets) if ((t.hits ?? []).some((h) => h.box)) drawn.get(t.n)?.add(m.scene);
  }
  const anyLane = new Set(Object.values(targets.laneScenes).flat());
  const missing = targets.targets.filter((t) => {
    if (t.captureBlind || t.widthHidden) return false;
    const own = t.lane === '—' ? anyLane : new Set(targets.laneScenes[t.lane] ?? []);
    return ![...drawn.get(t.n)].some((s) => own.has(s));
  }).map((t) => t.n);
  const declaredNotDrawn = targets.targets.flatMap((t) => (t.widthHidden ? [] : t.scenes)
    .filter((s) => measuredScenes.has(s) && !drawn.get(t.n).has(s)).map((s) => ({ n: t.n, scene: s })));
  const code = !measuredScenes.size || missing.length || declaredNotDrawn.length ? READINESS : 0;
  return {
    code, measuredScenes: [...measuredScenes], missing, declaredNotDrawn,
    drawnIn: Object.fromEntries([...drawn].map(([n, s]) => [n, [...s]])),
  };
}

function collect(paths) {
  const files = [];
  for (const p of paths) {
    if (!existsSync(p)) throw new Error(`not found: ${p}`);
    if (statSync(p).isDirectory()) {
      for (const f of readdirSync(p).sort()) if (f.endsWith('.metrics.json')) files.push(join(p, f));
    } else files.push(p);
  }
  return files;
}

function main(argv) {
  const usage = 'usage: node judge.mjs [--lane <L>] [--links] [--targets <file>] [--exempt <file>] [--out <file>] <dir|file>...';
  const opts = { lane: null, links: false, targets: join(HERE, 'targets.json'), exempt: join(HERE, 'judge-exempt.txt'), out: null };
  const rest = [];
  while (argv.length) {
    const a = argv.shift();
    if (a === '--links') opts.links = true;
    else if (['--lane', '--targets', '--exempt', '--out'].includes(a)) {
      const v = argv.shift();
      if (!v) return fail(`${a} needs a value · ${usage}`);
      opts[a.slice(2)] = v;
    } else if (a.startsWith('--')) return fail(`unknown flag ${a} · ${usage}`);
    else rest.push(a);
  }
  if (!rest.length) return fail(usage);
  let metrics;
  let targets;
  let exempt;
  try {
    targets = JSON.parse(readFileSync(opts.targets, 'utf8'));
    exempt = parseExempt(readFileSync(opts.exempt, 'utf8'));
    metrics = collect(rest).map((f) => JSON.parse(readFileSync(f, 'utf8')));
  } catch (e) {
    return fail(e.message);
  }
  const result = opts.links ? links({ metrics, targets }) : judge({ metrics, targets, exempt, lane: opts.lane });
  if (opts.out) writeFileSync(resolve(opts.out), JSON.stringify({ mode: opts.links ? 'links' : 'judge', ...result }, null, 2) + '\n');
  if (opts.links) {
    console.log(`::visual-judge-links:: scenes=${result.measuredScenes.length} missing=${result.missing.join(',') || '-'} declaredNotDrawn=${result.declaredNotDrawn.length} exit=${result.code}`);
    for (const d of result.declaredNotDrawn) console.log(`declared-not-drawn ${d.n} ${d.scene}`);
  } else {
    const outside = Object.entries(result.outsideRed).map(([k, v]) => `${k}:${v}`).join(',');
    console.log(`::visual-judge:: files=${result.files} lane=${result.lane ?? '-'} red=${result.red.length} readiness=${result.readiness.length} ` +
      `notMeasured=${result.notMeasured} captureBlind=${result.captureBlind} exemptHits=${result.exemptHits} smallOther=${result.smallOther} ` +
      `outsideRed=${outside} exit=${result.code}`);
    for (const r of result.red) console.log(`red ${r.metric} ${r.capture ?? '-'} ${r.n ?? ''} ${r.value ?? ''} ${r.path ?? r.why ?? ''}`.replace(/ +/g, ' '));
    for (const r of result.recorded) console.log(`map ${r.capture} cell=${r.cellWidth} judged=${r.judged} fourTools=${r.fourTools} zoomGroup=${r.zoomGroup} touchAction=${r.touchAction} dragAxis=${r.dragAxis} value=${r.valueState}`);
  }
  for (const r of result.readiness ?? []) console.error(`::visual-judge-readiness:: ${r}`);
  if (opts.links && result.code) console.error(`::visual-judge-readiness:: links: missing ${result.missing.join(', ') || '-'} · declared-not-drawn ${result.declaredNotDrawn.length}${result.measuredScenes.length ? '' : ' · no 390 touch files'}`);
  process.exit(result.code);
}

function fail(message) {
  console.error(`::visual-judge-readiness:: ${message}`);
  process.exit(READINESS);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main(process.argv.slice(2));
