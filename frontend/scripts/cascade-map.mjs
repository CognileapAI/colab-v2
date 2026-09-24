#!/usr/bin/env node
// Cascade map for the design-system.css absorption (zero-dependency; node built-ins only).
// Spec: dev-package/prd/specs/S-DESIGN-STRUCTURE-P2A-20260924.md (구현 결정 0).
//
// Usage (cwd = frontend/):
//   node scripts/cascade-map.mjs map    [--rev <git-rev>] [--out <dir>]
//   node scripts/cascade-map.mjs verify --base <git-rev> [--out <dir>]
//
// map    — parses every CSS file under src/ in load order and, for every declaration of every
//          design-system.css rule (per selector-list entry and per top-level `:is()` argument),
//          lists competing rules (last compound shares a class / type / attribute name, or is a
//          type-only / universal compound compatible with it, including state variants such as
//          :hover · :focus · [readonly] · [aria-*]), today's winner, and 되살아남 후보: competitors
//          that lose today and would win once the prefix is gone
//            · spec(C) > spec(S)                → 필연 (wins wherever S is placed)
//            · spec(C) == spec(S)               → 순서 (wins when C comes after S's new position)
//          Specificity: :is()/:not()/:has() = max of arguments, :where() = 0,
//          prefix :is(.colab-ui, .design-preview) = +0,1,0 (today), per :is() argument after the move.
// verify — reads the base tree from git and the working tree from disk. For every base
//          design-system.css declaration it finds the moved declaration in the working tree
//          (same selector argument · same media · same property · same value) and recomputes every
//          competitor outcome with working-tree positions. Reports: missing moves, outcome flips
//          whose values differ (red), deleted/changed non-design-system declarations (with a subset
//          check), leftover design-system.css. Exit 0 green · 1 red · 78 readiness.
//
// Load order: src/shell/styles.ts imports; shell.css `@import`s expand in place before the shell.css
// body; CSS imported only by components (deletion.css) comes after the styles.ts set.
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs';
import { dirname, join, posix, relative, sep } from 'node:path';

const READINESS = 78;
const DS = 'src/shell/design-system.css';
const STYLES = 'src/shell/styles.ts';
const DEFAULT_OUT = '../dev-package/reports/design-system/20260924/p2a';

// ---------------------------------------------------------------- file access (disk or git rev)
function lister(rev) {
  if (!rev) {
    const walk = (d) => readdirSync(d).flatMap((n) => {
      const p = join(d, n);
      return statSync(p).isDirectory() ? walk(p) : [p];
    });
    return {
      files: () => walk('src').map((p) => p.split(sep).join('/')),
      read: (p) => (existsSync(p) ? readFileSync(p, 'utf8') : null),
    };
  }
  const git = (...a) => execFileSync('git', a, { encoding: 'utf8', maxBuffer: 64 << 20 });
  const prefix = git('rev-parse', '--show-prefix').trim();
  return {
    files: () => git('ls-tree', '-r', '--name-only', rev, 'src').split('\n').filter(Boolean)
      .map((p) => (p.startsWith(prefix) ? p.slice(prefix.length) : p)),
    read: (p) => {
      try { return git('show', `${rev}:${prefix}${p}`); } catch { return null; }
    },
  };
}

function loadOrder(fs) {
  const all = fs.files().filter((p) => p.endsWith('.css'));
  const styles = fs.read(STYLES);
  if (styles == null) throw new Error(`${STYLES} missing`);
  const order = [];
  const seen = new Set();
  const add = (p, via) => {
    if (seen.has(p)) return;
    const text = fs.read(p);
    if (text == null) throw new Error(`${p} missing (${via})`);
    seen.add(p);
    for (const m of text.matchAll(/@import\s+['"]([^'"]+)['"]/g)) add(posix.join(posix.dirname(p), m[1]), p);
    order.push(p);
  };
  for (const m of styles.matchAll(/^import\s+['"]([^'"]+\.css)['"]/gm)) {
    if (!m[1].startsWith('.')) continue; // package CSS (pretendard) = @font-face only
    add(posix.join(posix.dirname(STYLES), m[1]), STYLES);
  }
  for (const p of all.sort()) add(p, 'component import');
  return order;
}

// ---------------------------------------------------------------- CSS parsing
function stripComments(t) {
  return t.replace(/\/\*[\s\S]*?\*\//g, (c) => c.replace(/[^\n]/g, ' '));
}

function splitTop(s, sepChar) {
  const out = [];
  let depth = 0; let quote = null; let cur = '';
  for (const ch of s) {
    if (quote) { cur += ch; if (ch === quote) quote = null; continue; }
    if (ch === '"' || ch === "'") { quote = ch; cur += ch; continue; }
    if (ch === '(' || ch === '[') depth++;
    if (ch === ')' || ch === ']') depth--;
    if (ch === sepChar && depth === 0) { out.push(cur); cur = ''; continue; }
    cur += ch;
  }
  out.push(cur);
  return out;
}

function parseDecls(body, line0) {
  const decls = [];
  let offset = 0;
  for (const raw of splitTop(body, ';')) {
    const line = line0 + (body.slice(0, offset).match(/\n/g) || []).length + (raw.match(/^\s*/)[0].match(/\n/g) || []).length;
    offset += raw.length + 1;
    const t = raw.trim();
    if (!t) continue;
    const i = t.indexOf(':');
    if (i < 0) continue;
    let value = t.slice(i + 1).trim().replace(/\s+/g, ' ');
    const important = /!\s*important$/i.test(value);
    if (important) value = value.replace(/\s*!\s*important$/i, '');
    decls.push({ prop: t.slice(0, i).trim().toLowerCase(), value, important, line });
  }
  return decls;
}

// Returns rules [{file, line, media: [cond...], layer, selectorText, selectors, decls}] and layer info.
function parseCss(text, file) {
  const t = stripComments(text);
  const rules = [];
  const stats = { layerBlocks: [], layerStatements: 0, unlayeredRules: 0, imports: 0 };
  const lineAt = (i) => (t.slice(0, i).match(/\n/g) || []).length + 1;
  function block(start, end, media, layer) {
    let i = start;
    while (i < end) {
      while (i < end && /\s/.test(t[i])) i++;
      if (i >= end) break;
      if (t[i] === '}') { i++; continue; }
      // prelude up to { or ;
      let j = i; let depth = 0; let quote = null;
      while (j < end) {
        const ch = t[j];
        if (quote) { if (ch === quote) quote = null; j++; continue; }
        if (ch === '"' || ch === "'") quote = ch;
        else if (ch === '(') depth++;
        else if (ch === ')') depth--;
        else if ((ch === '{' || ch === ';') && depth === 0) break;
        j++;
      }
      const prelude = t.slice(i, j).trim();
      if (t[j] === ';' || j >= end) { // statement at-rule
        if (/^@import/i.test(prelude)) stats.imports++;
        if (/^@layer/i.test(prelude)) stats.layerStatements++;
        i = j + 1;
        continue;
      }
      // find matching }
      let k = j + 1; let d = 1; quote = null;
      while (k < end && d > 0) {
        const ch = t[k];
        if (quote) { if (ch === quote) quote = null; } else if (ch === '"' || ch === "'") quote = ch;
        else if (ch === '{') d++;
        else if (ch === '}') d--;
        k++;
      }
      const bodyStart = j + 1; const bodyEnd = k - 1;
      if (/^@media/i.test(prelude)) {
        block(bodyStart, bodyEnd, [...media, prelude.replace(/^@media\s*/i, '').replace(/\s+/g, ' ')], layer);
      } else if (/^@layer/i.test(prelude)) {
        const name = prelude.replace(/^@layer\s*/i, '').trim();
        stats.layerBlocks.push({ name, line: lineAt(i) });
        block(bodyStart, bodyEnd, media, layer ? `${layer}.${name}` : name);
      } else if (/^@/.test(prelude)) {
        // @keyframes, @font-face, @supports … — not selector rules
      } else {
        const selectorText = prelude.replace(/\s+/g, ' ');
        if (!layer) stats.unlayeredRules++;
        rules.push({ file, line: lineAt(i), media, layer, selectorText, selectors: splitTop(selectorText, ',').map((s) => s.trim()).filter(Boolean),
          decls: parseDecls(t.slice(bodyStart, bodyEnd), lineAt(bodyStart)) });
      }
      i = k;
    }
  }
  block(0, t.length, [], null);
  return { rules, stats };
}

// ---------------------------------------------------------------- selectors
// compound = {simples: [{kind, name, args?}], pseudoElement}
function parseSelector(sel) {
  const compounds = []; const combinators = [];
  let cur = { simples: [], pseudoElement: null };
  let i = 0; const s = sel.trim();
  const ident = () => { const m = /^-?[A-Za-z_\\\u0080-\uffff][\w\\\u0080-\uffff-]*|^--[\w\u0080-\uffff-]*/.exec(s.slice(i)); if (!m) throw new Error(`bad selector ${sel} @${i}`); i += m[0].length; return m[0]; };
  const balanced = (open, close) => { let d = 0; const st = i; for (; i < s.length; i++) { if (s[i] === open) d++; else if (s[i] === close) { d--; if (d === 0) { i++; return s.slice(st + 1, i - 1); } } } throw new Error(`unbalanced ${sel}`); };
  const push = () => { compounds.push(cur); cur = { simples: [], pseudoElement: null }; };
  let pendingComb = null;
  while (i < s.length) {
    const ch = s[i];
    if (/[\s>+~]/.test(ch)) {
      let comb = ' ';
      while (i < s.length && /[\s>+~]/.test(s[i])) { if (s[i] !== ' ') comb = s[i]; i++; }
      if (cur.simples.length || cur.pseudoElement) { push(); pendingComb = comb; }
      continue;
    }
    if (pendingComb) { combinators.push(pendingComb); pendingComb = null; }
    if (ch === '.') { i++; cur.simples.push({ kind: 'class', name: ident() }); }
    else if (ch === '#') { i++; cur.simples.push({ kind: 'id', name: ident() }); }
    else if (ch === '*') { i++; cur.simples.push({ kind: 'universal', name: '*' }); }
    else if (ch === '[') { const inner = balanced('[', ']'); cur.simples.push({ kind: 'attr', name: inner.split(/[~|^$*]?=/)[0].trim().toLowerCase(), text: inner.replace(/\s+/g, '') }); }
    else if (ch === ':' && s[i + 1] === ':') { i += 2; const n = ident().toLowerCase(); let args; if (s[i] === '(') args = balanced('(', ')'); cur.pseudoElement = args ? `${n}(${args})` : n; }
    else if (ch === ':') {
      i++; const n = ident().toLowerCase();
      if (['before', 'after', 'first-line', 'first-letter'].includes(n)) { cur.pseudoElement = n; continue; }
      if (s[i] === '(') { const args = balanced('(', ')'); cur.simples.push({ kind: 'pseudo', name: n, args }); }
      else cur.simples.push({ kind: 'pseudo', name: n });
    } else { cur.simples.push({ kind: 'type', name: ident().toLowerCase() }); }
  }
  if (cur.simples.length || cur.pseudoElement) push();
  return { compounds, combinators };
}

const SEL_FN = new Set(['is', 'not', 'has', 'matches', '-webkit-any']);
function add3(a, b) { return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]; }
function cmp3(a, b) { return a[0] - b[0] || a[1] - b[1] || a[2] - b[2]; }
function max3(list) { return list.reduce((m, x) => (cmp3(x, m) > 0 ? x : m), [0, 0, 0]); }
function specOfList(text) { return max3(splitTop(text, ',').map((x) => specificity(x.trim()))); }
function specificity(sel) {
  let sp = [0, 0, 0];
  for (const c of parseSelector(sel).compounds) {
    for (const x of c.simples) {
      if (x.kind === 'id') sp = add3(sp, [1, 0, 0]);
      else if (x.kind === 'class' || x.kind === 'attr') sp = add3(sp, [0, 1, 0]);
      else if (x.kind === 'type') sp = add3(sp, [0, 0, 1]);
      else if (x.kind === 'pseudo') {
        if (x.name === 'where') continue;
        if (SEL_FN.has(x.name)) sp = add3(sp, specOfList(x.args));
        else if (/^nth-/.test(x.name) && / of /.test(x.args || '')) sp = add3(add3(sp, [0, 1, 0]), specOfList(x.args.split(/ of /)[1]));
        else sp = add3(sp, [0, 1, 0]);
      }
    }
    if (c.pseudoElement) sp = add3(sp, [0, 0, 1]);
  }
  return sp;
}
const fmt3 = (s) => s.join(',');

// Tokens of the subject (last) compound: classes, types, attribute names; descends into
// :is/:where/:matches (not :not/:has). Returns {tokens:Set, hasKey, types:Set, pseudoElement, states}.
function subjectInfo(sel) {
  const { compounds } = parseSelector(sel);
  const last = compounds[compounds.length - 1] || { simples: [], pseudoElement: null };
  const tokens = new Set(); const types = new Set(); const states = [];
  let hasKey = false;
  const visit = (simples, top) => {
    for (const x of simples) {
      if (x.kind === 'class') { tokens.add(`.${x.name}`); hasKey = true; }
      else if (x.kind === 'attr') { tokens.add(`[${x.name}]`); hasKey = true; if (top) states.push(`[${x.text}]`); }
      else if (x.kind === 'id') { tokens.add(`#${x.name}`); hasKey = true; }
      else if (x.kind === 'type') { tokens.add(x.name); types.add(x.name); }
      else if (x.kind === 'pseudo' && ['is', 'where', 'matches'].includes(x.name)) {
        for (const a of splitTop(x.args, ',')) {
          const sub = parseSelector(a.trim()).compounds;
          visit(sub[sub.length - 1].simples, false);
        }
      } else if (x.kind === 'pseudo' && top) states.push(`:${x.name}${x.args ? `(${x.args})` : ''}`);
    }
  };
  visit(last.simples, true);
  return { tokens, types, hasKey, pseudoElement: last.pseudoElement, states };
}

// Is every element matched by `inner` also matched by `outer`? (conservative: true only when provable)
function subsetOf(inner, outer) {
  const a = parseSelector(inner); const b = parseSelector(outer);
  const simpleSet = (c) => new Set(c.simples.map((x) => JSON.stringify([x.kind, x.name, x.args || x.text || ''])));
  const covers = (ci, co) => { // every simple of co is in ci (co less restrictive)
    const si = simpleSet(ci);
    return [...simpleSet(co)].every((x) => si.has(x)) && (co.pseudoElement || null) === (ci.pseudoElement || null);
  };
  if (!b.compounds.length || !a.compounds.length) return false;
  if (!covers(a.compounds[a.compounds.length - 1], b.compounds[b.compounds.length - 1])) return false;
  // outer ancestors (descendant/child combinators) must map in order onto inner ancestors
  let ai = a.compounds.length - 2;
  for (let bi = b.compounds.length - 2; bi >= 0; bi--) {
    const comb = b.combinators[bi];
    if (comb !== ' ' && comb !== '>') return false;
    if (comb === '>') {
      if (ai < 0 || a.combinators[ai] !== '>' || !covers(a.compounds[ai], b.compounds[bi])) return false;
      ai--; continue;
    }
    while (ai >= 0 && !covers(a.compounds[ai], b.compounds[bi])) ai--;
    if (ai < 0) return false;
    ai--;
  }
  return true;
}

// ---------------------------------------------------------------- properties
const SIDES = ['top', 'right', 'bottom', 'left'];
const CORNERS = ['top-left', 'top-right', 'bottom-right', 'bottom-left'];
function longhands(p) {
  const box = (base) => ({
    [base]: SIDES.map((s) => `${base}-${s}`),
    [`${base}-inline`]: [`${base}-left`, `${base}-right`], [`${base}-block`]: [`${base}-top`, `${base}-bottom`],
    [`${base}-inline-start`]: [`${base}-left`], [`${base}-inline-end`]: [`${base}-right`],
    [`${base}-block-start`]: [`${base}-top`], [`${base}-block-end`]: [`${base}-bottom`],
  });
  const map = {
    ...box('padding'), ...box('margin'), ...box('scroll-margin'), ...box('scroll-padding'),
    inset: SIDES, 'inset-inline': ['left', 'right'], 'inset-block': ['top', 'bottom'],
    border: SIDES.flatMap((s) => ['width', 'style', 'color'].map((k) => `border-${s}-${k}`)),
    'border-color': SIDES.map((s) => `border-${s}-color`), 'border-width': SIDES.map((s) => `border-${s}-width`), 'border-style': SIDES.map((s) => `border-${s}-style`),
    'border-inline': ['left', 'right'].flatMap((s) => ['width', 'style', 'color'].map((k) => `border-${s}-${k}`)),
    'border-block': ['top', 'bottom'].flatMap((s) => ['width', 'style', 'color'].map((k) => `border-${s}-${k}`)),
    'border-radius': CORNERS.map((c) => `border-${c}-radius`),
    outline: ['outline-width', 'outline-style', 'outline-color'],
    font: ['font-style', 'font-variant', 'font-weight', 'font-stretch', 'font-size', 'line-height', 'font-family'],
    background: ['background-color', 'background-image', 'background-position', 'background-size', 'background-repeat', 'background-origin', 'background-clip', 'background-attachment'],
    flex: ['flex-grow', 'flex-shrink', 'flex-basis'], 'flex-flow': ['flex-direction', 'flex-wrap'],
    gap: ['row-gap', 'column-gap'], 'grid-gap': ['row-gap', 'column-gap'],
    'grid-template': ['grid-template-rows', 'grid-template-columns', 'grid-template-areas'],
    'grid-column': ['grid-column-start', 'grid-column-end'], 'grid-row': ['grid-row-start', 'grid-row-end'],
    'grid-area': ['grid-row-start', 'grid-column-start', 'grid-row-end', 'grid-column-end'],
    overflow: ['overflow-x', 'overflow-y'],
    'text-decoration': ['text-decoration-line', 'text-decoration-color', 'text-decoration-style', 'text-decoration-thickness'],
    'place-items': ['align-items', 'justify-items'], 'place-content': ['align-content', 'justify-content'], 'place-self': ['align-self', 'justify-self'],
    'list-style': ['list-style-type', 'list-style-position', 'list-style-image'],
    transition: ['transition-property', 'transition-duration', 'transition-timing-function', 'transition-delay'],
    animation: ['animation-name', 'animation-duration', 'animation-timing-function', 'animation-delay', 'animation-iteration-count', 'animation-direction', 'animation-fill-mode', 'animation-play-state'],
  };
  // nested shorthands: border-top → width/style/color of that side
  for (const s of SIDES) map[`border-${s}`] = ['width', 'style', 'color'].map((k) => `border-${s}-${k}`);
  const aliases = { 'grid-row-gap': ['row-gap'], 'grid-column-gap': ['column-gap'], 'word-wrap': ['overflow-wrap'] };
  const l = map[p] || aliases[p];
  if (!l) return [p];
  return [...new Set(l.flatMap((x) => (x === p ? [x] : longhands(x))))];
}
function overlap(p, q) { const a = new Set(longhands(p)); return longhands(q).some((x) => a.has(x)); }

// ---------------------------------------------------------------- media
function mediaRange(conds) {
  let lo = 0; let hi = Infinity; const feats = new Set();
  for (const c of conds) {
    for (const part of c.split(/\band\b/)) {
      const m = /\(\s*(max|min)-width\s*:\s*(\d+)px\s*\)/.exec(part);
      if (m) { if (m[1] === 'max') hi = Math.min(hi, +m[2]); else lo = Math.max(lo, +m[2]); } else if (part.trim()) feats.add(part.trim().replace(/\s+/g, ''));
    }
  }
  return { lo, hi, feats };
}
function mediaOverlap(a, b) { const x = mediaRange(a); const y = mediaRange(b); return Math.max(x.lo, y.lo) <= Math.min(x.hi, y.hi); }
function mediaSubset(inner, outer) { const x = mediaRange(inner); const y = mediaRange(outer); return x.lo >= y.lo && x.hi <= y.hi && [...y.feats].every((f) => x.feats.has(f)); }
const mediaKey = (m) => m.join(' and ');

// ---------------------------------------------------------------- model
function buildModel(fs) {
  const order = loadOrder(fs);
  const rules = []; const files = {};
  order.forEach((file, fi) => {
    const { rules: rs, stats } = parseCss(fs.read(file), file);
    files[file] = { index: fi, stats, ruleCount: rs.length };
    for (const r of rs) { r.pos = rules.length; r.fileIndex = fi; rules.push(r); }
  });
  return { order, rules, files };
}

const PREFIX_IS = ':is(.colab-ui, .design-preview)';
function stripPrefix(sel) {
  const s = sel.replace(/\s+/g, ' ').trim();
  if (s === PREFIX_IS) return { kind: 'document', s };
  if (s.startsWith(`${PREFIX_IS} `)) return { kind: 'is', s: s.slice(PREFIX_IS.length + 1) };
  if (s.startsWith('.colab-ui ')) return { kind: 'colab-ui', s: s.slice('.colab-ui '.length) };
  if (s.includes(PREFIX_IS)) return { kind: 'compound', s: s.replace(PREFIX_IS, '') };
  return { kind: 'none', s };
}
// Expand the first top-level :is(list) whose compound can take a textual substitution.
function expandIs(s) {
  const m = /:is\(/.exec(s);
  if (!m) return [s];
  let d = 0; let j = m.index + 3;
  for (; j < s.length; j++) { if (s[j] === '(') d++; else if (s[j] === ')') { d--; if (d === 0) break; } }
  const args = splitTop(s.slice(m.index + 4, j), ',').map((x) => x.trim());
  const before = s.slice(0, m.index); const after = s.slice(j + 1);
  const standalone = (before === '' || /[\s>+~]$/.test(before)) && (after === '' || /^[\s>+~:[.]/.test(after));
  const complex = args.some((a) => /[\s>+~]/.test(a));
  if (complex && !standalone) return [s];
  if (!standalone && args.some((a) => /^[a-z]/i.test(a)) && before !== '' && !/[\s>+~]$/.test(before)) return [s];
  return args.flatMap((a) => expandIs(before + a + after));
}

function competitorsFor(model, dsRule, sel, decl, opts = {}) {
  const info = subjectInfo(sel);
  const out = [];
  for (const r of model.rules) {
    if (r === dsRule && !opts.includeSelf) continue;
    if (!mediaOverlap(r.media, dsRule.media)) continue;
    for (const t of r.selectors) {
      if (opts.skip && opts.skip(r, t)) continue;
      const ti = subjectInfo(t);
      if ((ti.pseudoElement || null) !== (info.pseudoElement || null)) continue;
      const shared = [...ti.tokens].filter((x) => info.tokens.has(x));
      let kind = null;
      if (shared.some((x) => /^[.#[]/.test(x))) kind = 'key';
      else if (shared.length) kind = 'type';
      else if (!ti.hasKey && (ti.types.size === 0 || info.types.size === 0 || [...ti.types].some((x) => info.types.has(x)))) kind = ti.types.size ? 'type' : 'universal';
      else if (!info.hasKey && info.types.size && ti.types.size && [...ti.types].some((x) => info.types.has(x))) kind = 'type';
      if (!kind) continue;
      if (info.types.size && ti.types.size && ![...ti.types].some((x) => info.types.has(x)) && !shared.length) continue;
      for (const d of r.decls) {
        if (!overlap(d.prop, decl.prop)) continue;
        out.push({ rule: r, selector: t, decl: d, spec: specificity(t), kind, states: ti.states });
      }
    }
  }
  return out;
}

const beats = (aSpec, aPos, aImp, bSpec, bPos, bImp) => (aImp !== bImp ? aImp : (cmp3(aSpec, bSpec) || aPos - bPos) > 0);

function mapDs(model, researchOwners) {
  const dsRules = model.rules.filter((r) => r.file === DS);
  const shellFirst = model.rules.find((r) => r.file === 'src/shell/shell.css')?.pos ?? Infinity;
  return dsRules.map((r, idx) => {
    const no = idx + 1;
    const entries = r.selectors.map((full) => {
      const pre = stripPrefix(full);
      const args = pre.kind === 'document' ? [pre.s] : expandIs(pre.s);
      return {
        full, prefix: pre.kind, specToday: specificity(full), stripped: pre.s,
        args: args.map((arg) => {
          const specAfter = pre.kind === 'document' ? specificity(full) : specificity(arg);
          return {
            arg, specAfter,
            decls: r.decls.map((d) => {
              const comps = competitorsFor(model, r, full === arg ? full : arg, d).map((c) => {
                const dsWinsToday = beats(specificity(full), r.pos, d.important, c.spec, c.rule.pos, c.decl.important);
                const isDs = c.rule.file === DS;
                const cSpecAfter = isDs ? specificity(stripPrefix(c.selector).s) : c.spec;
                const cmpAfter = cmp3(cSpecAfter, specAfter);
                let revive = null;
                if (dsWinsToday && c.decl.important === d.important) {
                  if (isDs) revive = cmpAfter > 0 ? 'DS쌍(특이도)' : cmpAfter === 0 ? 'DS쌍(순서)' : null;
                  else if (cmpAfter > 0) revive = '필연';
                  else if (cmpAfter === 0) revive = c.rule.pos > r.pos ? '순서(셸 본문)' : '순서';
                }
                const sameValue = c.decl.value === d.value;
                return { file: c.rule.file, line: c.decl.line, pos: c.rule.pos, media: mediaKey(c.rule.media), selector: c.selector, prop: c.decl.prop, value: c.decl.value,
                  spec: fmt3(c.spec), kind: c.kind, states: c.states, winnerToday: dsWinsToday ? 'DS' : 'C', revive, sameValue,
                  subsetOfS: pre.kind === 'document' ? false : subsetOf(c.selector, arg) && mediaSubset(c.rule.media, r.media) };
              });
              const losesTo = comps.filter((c) => c.winnerToday === 'C' && !c.sameValue && c.kind === 'key');
              return { prop: d.prop, value: d.value, line: d.line, competitors: comps, losesToday: losesTo.length,
                revive: comps.filter((c) => c.revive && !c.sameValue && c.kind === 'key'),
                reviveTypeCompat: comps.filter((c) => c.revive && !c.sameValue && c.kind !== 'key').length };
            }),
          };
        }),
      };
    });
    return { no, line: r.line, media: mediaKey(r.media), selectorText: r.selectorText, declCount: r.decls.length, research: researchOwners[no] || null, entries, beforeShellBody: r.pos < shellFirst };
  });
}

function readResearchOwners() {
  const p = '../dev-package/reports/design-system/20260924/p2/design-system-map.md';
  const out = {};
  if (!existsSync(p)) return out;
  for (const line of readFileSync(p, 'utf8').split('\n')) {
    const m = /^\| (\d+) \| (L\d+[^|]*)\| (.*?) \| (\d+) \| ([^|]+) \| ([^|]+) \|/.exec(line);
    if (m) out[+m[1]] = { owner: m[5].trim(), target: m[6].trim(), decl: +m[4] };
  }
  return out;
}

// ---------------------------------------------------------------- output (map)
function writeMap(out, model, map, rev) {
  mkdirSync(out, { recursive: true });
  const rel = (c) => `${c.file.replace(/^src\//, '')}:${c.line}`;
  let reviveTotal = 0; let loseDecls = 0; let declTotal = 0; let stateRevive = 0; let typeCompat = 0;
  const reviveRows = [];
  for (const r of map) for (const e of r.entries) for (const a of e.args) for (const d of a.decls) {
    declTotal++;
    if (d.losesToday) loseDecls++;
    typeCompat += d.reviveTypeCompat;
    for (const c of d.revive) {
      reviveTotal++;
      if (c.states.length) stateRevive++;
      reviveRows.push({ no: r.no, arg: a.arg, specAfter: fmt3(a.specAfter), prop: d.prop, dsValue: d.value, c });
    }
  }
  const lines = [];
  lines.push('# P2a cascade map — design-system.css 규칙별 경쟁 · 오늘의 승자 · 되살아남 후보');
  lines.push('');
  lines.push(`생성: \`node frontend/scripts/cascade-map.mjs map${rev ? ` --rev ${rev}` : ''}\` · 적재 순서 ${model.order.length}파일 · 규칙 ${model.rules.length} · design-system.css 규칙 ${map.length}. 조사 부록 A(휴리스틱 쌍)를 대체한다.`);
  lines.push('');
  lines.push('적재 순서: ' + model.order.map((f) => `\`${f.replace(/^src\//, '')}\``).join(' → '));
  lines.push('');
  lines.push('판정: 경쟁 규칙 = 속성(longhand)과 미디어 범위가 겹치고, 마지막 compound 가 클래스·속성·id 이름을 공유(`key` · 표에 싣는 것)하거나 요소 이름만 공유·키 없는 요소·전체 compound 인 규칙(`type`·`universal` · 같은 요소에 걸리는지 선택자만으로 알 수 없어 건수만 싣고, 렌더 장면의 계산값 전수 대조로 확인한다). 오늘의 승자 = !important → 특이도(접두 포함) → 순서. 되살아남 = 오늘 DS 가 이기고 값이 다른데, 접두를 뗀 특이도로는 C 가 이기는 것(`필연` = 특이도가 더 큼 · `순서` = 같은 특이도라 새 위치보다 뒤면 이김 · `순서(셸 본문)` = 같은 특이도로 `shell.css` 본문에 있어 셸 맨 앞에 두어도 이김). `⊆S` = C 가 맞는 요소는 전부 S 도 맞는다(선택자·미디어로 증명 · 오늘 그 선언은 모든 문맥에서 죽음 → 삭제 가능).');
  lines.push('');
  lines.push(`## 합계`);
  lines.push('');
  lines.push(`| 항목 | 값 |`);
  lines.push('|---|---:|');
  lines.push(`| DS 규칙 | ${map.length} |`);
  lines.push(`| (선택자 인자 × 선언) 단위 | ${declTotal} |`);
  lines.push(`| 오늘 어떤 경쟁 규칙에 지는 선언 단위(값 다름) | ${loseDecls} |`);
  lines.push(`| 되살아남 후보(값 다름) | ${reviveTotal} |`);
  lines.push(`| 그중 상태 선택자(:hover·:focus·[readonly]·[aria-*] 등) | ${stateRevive} |`);
  lines.push(`| 요소·전체 compound 호환 후보(\`type\`·\`universal\` · 표 밖 · 렌더 대조로 확인) | ${typeCompat} |`);
  lines.push('');
  lines.push('## 되살아남 후보 (값 다름)');
  lines.push('');
  lines.push('| DS# | S(인자) | spec 뒤 | 속성 | DS 값 | 경쟁 C | 위치 | spec C | 미디어 C | C 값 | 종류 | 상태 | ⊆S |');
  lines.push('|---:|---|---|---|---|---|---|---|---|---|---|---|---|');
  for (const x of reviveRows) {
    lines.push(`| ${x.no} | \`${x.arg}\` | ${x.specAfter} | ${x.prop} | \`${x.dsValue}\` | \`${x.c.selector}\` | ${rel(x.c)} | ${x.c.spec} | ${x.c.media || '-'} | \`${x.c.value}\` | ${x.c.revive} | ${x.c.states.join(' ') || '-'} | ${x.c.subsetOfS ? '예' : '아니오'} |`);
  }
  lines.push('');
  lines.push('## 규칙별 표');
  lines.push('');
  lines.push('`DS 짐` = 오늘 그 선언이 지는 경쟁(값 다름) · `되살` = 되살아남 후보 수. 경쟁 전수는 `cascade-map.json`.');
  lines.push('');
  lines.push('| # | 행 | 미디어 | 선택자 인자 | spec 오늘→뒤 | 선언 | DS 짐 | 되살 | 조사 owner | 조사 target |');
  lines.push('|---:|---:|---|---|---|---:|---|---|---|---|');
  for (const r of map) for (const e of r.entries) for (const a of e.args) {
    const lose = a.decls.filter((d) => d.losesToday).map((d) => `${d.prop}(${d.losesToday})`).join(' ') || '-';
    const rev = a.decls.filter((d) => d.revive.length).map((d) => `${d.prop}(${d.revive.length})`).join(' ') || '-';
    lines.push(`| ${r.no} | ${r.line} | ${r.media || '-'} | \`${a.arg}\` | ${fmt3(e.specToday)}→${fmt3(a.specAfter)} | ${a.decls.length} | ${lose} | ${rev} | ${r.research?.owner ?? '?'} | ${r.research?.target ?? '?'} |`);
  }
  lines.push('');
  writeFileSync(join(out, 'cascade-map.md'), lines.join('\n'));
  const json = { schema: 'colab-cascade-map/1', rev: rev || 'worktree', order: model.order, ruleCount: model.rules.length, dsRules: map.length,
    totals: { declUnits: declTotal, losesToday: loseDecls, revive: reviveTotal, stateRevive, typeCompat },
    rules: map.map((r) => ({ ...r, entries: r.entries.map((e) => ({ ...e, specToday: fmt3(e.specToday), args: e.args.map((a) => ({ ...a, specAfter: fmt3(a.specAfter), decls: a.decls.map((d) => ({ ...d, competitors: d.competitors.filter((c) => c.kind === 'key') })) })) })) })) };
  writeFileSync(join(out, 'cascade-map.json'), JSON.stringify(json) + '\n');
  console.log(`cascade-map: ds rules ${map.length} · units ${declTotal} · loses-today ${loseDecls} · revive ${reviveTotal} (state ${stateRevive}) -> ${relative('.', join(out, 'cascade-map.md'))}`);
  return json;
}

// ---------------------------------------------------------------- verify
function normSel(s) { return s.replace(/\s+/g, ' ').replace(/\s*([>+~,])\s*/g, '$1').replace(/"/g, "'").trim(); }
function verify(out, baseRev) {
  const base = buildModel(lister(baseRev));
  const cur = buildModel(lister(null));
  const map = mapDs(base, readResearchOwners());
  const problems = []; const moved = []; const dropped = [];
  if (cur.order.includes(DS)) problems.push({ kind: 'ds-still-present' });
  // index current rules by (normalized selector argument, media) — expanding each selector's :is() as well
  const index = new Map();
  for (const r of cur.rules) for (const t of r.selectors) {
    for (const k of new Set([normSel(t), ...expandIs(t).map(normSel)])) {
      const key = `${k}@@${mediaKey(r.media)}`;
      if (!index.has(key)) index.set(key, []);
      index.get(key).push({ rule: r, selector: t });
    }
  }
  const dsRules = base.rules.filter((r) => r.file === DS);
  for (const m of map) {
    const r = dsRules[m.no - 1];
    for (const e of m.entries) for (const a of e.args) for (const d of a.decls) {
      const key = `${normSel(e.prefix === 'document' ? e.full : a.arg)}@@${m.media}`;
      const homes = (index.get(key) || []).filter((h) => h.rule.decls.some((x) => x.prop === d.prop));
      // effective home = the last-positioned candidate carrying the property
      const home = homes.sort((x, y) => x.rule.pos - y.rule.pos).at(-1);
      const homeDecl = home?.rule.decls.filter((x) => x.prop === d.prop).at(-1);
      const unit = { no: m.no, arg: a.arg, prop: d.prop, value: d.value, home: home ? `${home.rule.file}:${homeDecl.line}` : null };
      if (!home || homeDecl.value !== d.value) {
        // allowed only when declared dropped: loses in every context (duplicate)
        unit.status = home ? 'value-differs' : 'missing';
        unit.homeValue = homeDecl?.value;
        dropped.push(unit);
        continue;
      }
      // recompute competitor outcomes with current positions
      const homeSpec = specificity(home.selector);
      const flips = [];
      for (const c of competitorsFor(cur, home.rule, a.arg, { prop: d.prop, value: d.value }, { skip: (rr) => rr === home.rule })) {
        if (c.decl.value === d.value) continue;
        const nowWins = beats(homeSpec, home.rule.pos, homeDecl.important, c.spec, c.rule.pos, c.decl.important);
        // same-rule later overlapping declarations are handled by source order within the rule
        const todayComp = m.entries.flatMap((x) => x.args).find((x) => x.arg === a.arg)?.decls.find((x) => x.prop === d.prop)?.competitors
          .find((x) => normSel(x.selector) === normSel(c.selector) && x.prop === c.decl.prop && x.media === mediaKey(c.rule.media) && x.file === c.rule.file && x.value === c.decl.value);
        const wonToday = todayComp ? todayComp.winnerToday === 'DS' : null;
        if (!nowWins && wonToday !== false) flips.push({ selector: c.selector, file: c.rule.file, line: c.decl.line, prop: c.decl.prop, value: c.decl.value, spec: fmt3(c.spec), today: todayComp ? 'DS won' : 'new competitor', states: c.states });
      }
      // later declaration in the same home rule overriding it
      const idx = home.rule.decls.lastIndexOf(homeDecl);
      for (const x of home.rule.decls.slice(idx + 1)) if (overlap(x.prop, d.prop) && x.value !== d.value) flips.push({ selector: home.selector, file: home.rule.file, line: x.line, prop: x.prop, value: x.value, spec: fmt3(homeSpec), today: 'same-rule later' });
      unit.flips = flips;
      moved.push(unit);
      if (flips.length) problems.push({ kind: 'flip', ...unit });
    }
  }
  // non-DS declarations removed or changed (base → current), with dead-today proof
  const declKey = (r, d) => `${r.file}|${normSel(r.selectorText)}|${mediaKey(r.media)}|${d.prop}`;
  const curDecls = new Map();
  for (const r of cur.rules) for (const d of r.decls) curDecls.set(declKey(r, d), d.value);
  const changed = [];
  for (const r of base.rules) {
    if (r.file === DS) continue;
    for (const d of r.decls) {
      const k = declKey(r, d);
      const now = curDecls.get(k);
      if (now === d.value) continue;
      // proof: some DS argument S with the property and a value ≠ this beats it today and it is ⊆ S
      const proofs = [];
      for (const m of map) for (const e of m.entries) for (const a of e.args) for (const dd of a.decls) {
        const c = dd.competitors.find((x) => x.file === r.file && x.line === d.line && x.prop === d.prop && r.selectors.some((t) => normSel(t) === normSel(x.selector)));
        if (c && c.winnerToday === 'DS' && c.subsetOfS && overlap(dd.prop, d.prop) && longhands(d.prop).every((lh) => longhands(dd.prop).includes(lh) || a.decls.some((z) => longhands(z.prop).includes(lh)))) proofs.push({ no: m.no, arg: a.arg, prop: dd.prop, value: dd.value });
      }
      changed.push({ file: r.file, line: d.line, selector: r.selectorText, media: mediaKey(r.media), prop: d.prop, from: d.value, to: now ?? null, deadToday: proofs.length > 0, proofs: proofs.slice(0, 3) });
    }
  }
  for (const c of changed) if (!c.deadToday) problems.push({ kind: 'changed-live', ...c });
  mkdirSync(out, { recursive: true });
  const res = { schema: 'colab-cascade-verify/1', base: baseRev, dsUnits: moved.length + dropped.length, moved: moved.length, dropped, changed, problems,
    layers: Object.fromEntries(Object.entries(cur.files).map(([f, v]) => [f, { layerBlocks: v.stats.layerBlocks.map((b) => b.name), unlayeredRules: v.stats.unlayeredRules, imports: v.stats.imports, rules: v.ruleCount }])) };
  writeFileSync(join(out, 'cascade-verify.json'), JSON.stringify(res, null, 1));
  const lines = ['# P2a cascade verify', '', `기준 \`${baseRev}\` → 작업 트리 · DS 선언 단위 ${res.dsUnits} · 옮겨짐 ${moved.length} · 버림/불일치 ${dropped.length} · 비DS 선언 변경 ${changed.length}(오늘 죽음 증명 ${changed.filter((c) => c.deadToday).length}) · 문제 ${problems.length}`, ''];
  lines.push('## 버림·불일치 (DS 선언이 새 자리에서 같은 값으로 발견되지 않음)', '', '| DS# | 인자 | 속성 | DS 값 | 상태 | 찾은 값 |', '|---:|---|---|---|---|---|');
  for (const x of dropped) lines.push(`| ${x.no} | \`${x.arg}\` | ${x.prop} | \`${x.value}\` | ${x.status} | ${x.homeValue ? `\`${x.homeValue}\`` : '-'} |`);
  lines.push('', '## 비DS 선언 변경 (삭제·값 일치)', '', '| 파일:행 | 선택자 | 미디어 | 속성 | 원래 값 | 뒤 | 오늘 죽음 증명 |', '|---|---|---|---|---|---|---|');
  for (const x of changed) lines.push(`| ${x.file.replace(/^src\//, '')}:${x.line} | \`${x.selector}\` | ${x.media || '-'} | ${x.prop} | \`${x.from}\` | ${x.to == null ? '삭제' : `\`${x.to}\``} | ${x.deadToday ? x.proofs.map((p) => `DS#${p.no} \`${p.arg}\``).join(' · ') : '**없음**'} |`);
  lines.push('', '## 문제', '', '| 종류 | 내용 |', '|---|---|');
  for (const p of problems) lines.push(`| ${p.kind} | ${p.kind === 'flip' ? `DS#${p.no} \`${p.arg}\` ${p.prop}=\`${p.value}\` @ ${p.home} ← ${p.flips.map((f) => `\`${f.selector}\` ${f.file.replace(/^src\//, '')}:${f.line} ${f.prop}=\`${f.value}\` (${f.spec} · ${f.today})`).join(' · ')}` : p.kind === 'changed-live' ? `${p.file}:${p.line} \`${p.selector}\` ${p.prop} \`${p.from}\` → ${p.to ?? '삭제'}` : JSON.stringify(p)} |`);
  writeFileSync(join(out, 'cascade-verify.md'), lines.join('\n') + '\n');
  console.log(`cascade-verify: units ${res.dsUnits} · moved ${moved.length} · dropped ${dropped.length} · changed ${changed.length} · problems ${problems.length} -> ${relative('.', join(out, 'cascade-verify.md'))}`);
  return problems.length ? 1 : 0;
}

// ---------------------------------------------------------------- main
function main() {
  const argv = process.argv.slice(2);
  const mode = argv[0];
  const opt = (n) => { const i = argv.indexOf(n); return i >= 0 ? argv[i + 1] : null; };
  const out = opt('--out') || DEFAULT_OUT;
  try {
    if (mode === 'map') {
      const rev = opt('--rev');
      const model = buildModel(lister(rev));
      if (!model.order.includes(DS)) { console.error(`::cascade-map:: ${DS} not in load order`); return READINESS; }
      writeMap(out, model, mapDs(model, readResearchOwners()), rev);
      return 0;
    }
    if (mode === 'verify') {
      const base = opt('--base');
      if (!base) { console.error('::cascade-map:: verify needs --base <rev>'); return READINESS; }
      return verify(out, base);
    }
  } catch (e) {
    console.error(`::cascade-map:: ${e.stack || e.message}`);
    return READINESS;
  }
  console.error('usage: cascade-map.mjs map [--rev R] [--out D] | verify --base R [--out D]');
  return READINESS;
}
process.exitCode = main();
export { specificity, parseSelector, subsetOf, longhands, expandIs, stripPrefix, parseCss, dirname };
