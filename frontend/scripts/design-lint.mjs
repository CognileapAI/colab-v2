#!/usr/bin/env node
// frontend-design-lint judge (node built-ins + the `typescript` devDependency for rule g; nothing new).
//
// Usage: node scripts/design-lint.mjs --root <frontendDir> --same-in-dark <file> -- <css files relative to root...>
//   TS/TSX files under <root>/src are scanned for '--name' string literals (style={{'--w': v}} ·
//   setProperty('--x', ...)) and those names count as defined for rule b.
//   `typescript` resolves from this script's own location (frontend/node_modules), not from <root>;
//   COLAB_DESIGN_LINT_TYPESCRIPT overrides the module specifier (selftest: missing parser → 78).
//
// Rules (spec S-DESIGN-STRUCTURE-P1-20260924):
//   a  custom property defined inside a `:root` rule outside src/shell/tokens.css, OR a
//      canonical-family name (--color- --space- --text- --radius- --font- --shadow- --leading-
//      --tracking- --fg- --bg- --accent-) defined in a screen-scope rule outside tokens.css.
//   b  var(--x) whose --x is defined nowhere (CSS in scope or TS/TSX literal), fallback or not.
//   c  light colour-family name (--color- --fg- --bg- --accent- --shadow-) in tokens.css :root
//      that is not in the dark block, not covered through a var() alias, and not in the
//      same-in-dark list; plus dark-only names; plus list holes (empty reason · stale · already dark).
//   d  `:root` selector outside tokens.css (any compound: `:root`, `html:root`, `:root[data-x]`) ·
//      `@import` in any CSS other than tokens.css (P2a: shell.css no longer imports; `@layer` blocks
//      make a late `@import` invalid anyway).
//   f  (P3) colour literal in any CSS other than tokens.css — hex · rgb()/rgba()/hsl()/hsla()/hwb()/
//      lab()/lch()/oklab()/oklch()/color()/color-mix() · the 148 CSS named colours — as a direct value
//      (a color-mix() of only var()/transparent/currentColor is a token mix, not a literal)
//      or inside a var() fallback. Not literals: transparent · currentColor · inherit · initial · unset.
//      Exemptions share the same-in-dark list: `f · <file> · <selector> · <property> · <literal> · <reason>`;
//      an entry with an empty reason or matching nothing (stale) is red and exempts nothing.
//   g  (P3) a JSX `style` attribute in <root>/src/**/*.tsx whose value is not an object literal made only of
//      `--*` keys (TS AST, not regex): any other key (incl. shorthand `{ width }` · spread · computed
//      non-literal) or a non-object value is red. `--*`-only objects count as variable assignments (v).
//      A `style` key inside a JSX spread attribute (`{...(c ? { style: {…} } : {})}`) is judged the same way.
//   e  (P2b · spec S-DESIGN-STRUCTURE-P2B-20260924) a bare primitive definition outside src/shell/primitives.css:
//      a selector-list argument that — after expanding `:is()`/`:where()` — is ONE compound made only of
//      classes from the primitives list (`--primitives`, one class per line, `.chip--*` prefix form) plus
//      pseudo-classes/-elements and attribute selectors (`.btn` · `.btn:hover` · `.chip--warning` ·
//      `:is(.inp, .sel)`). `:not()`/`:has()` arguments are not inspected. A compound mixed with a
//      non-listed class/type/id (`.btn.foo` · `button.btn`) and ancestor/descendant contexts (`.memgrid .btn`)
//      are allowed. Also red: `!important` inside src/shell/primitives.css or src/shell/base.css.
//      Exemptions live in their own list (`--primitives-exempt`, `<file> · <selector> · <reason>`): an empty
//      reason → red and exempts nothing · an entry matching nothing (stale) → red · count shown as 「(면제 m)」.
//   i  (spec S-DEVICE-WIDTH-INPUT-20260926 V10 · V13) width/input conditions. Every `@media` / `@container` prelude is one
//      header. A `@media` header is normalised (`@media(max-width:720px)` = `@media (max-width: 720px)`), split at
//      top-level commas (OR branches) and `and`, and each condition judged against design-families.mjs:
//        width   `(max-width: <n>px)` n in WIDTH_MAX · `(min-width: <n>px)` n in WIDTH_MIN — another px value is `i_media`;
//        input   `(pointer: coarse)` · `(hover: hover)` (INPUT_ALLOWED · 우려 11ⓐ);
//        counted only  `prefers-*` (`media_prefers`);
//        form (`i_form`)  anything else — height · range syntax · em/rem · orientation · aspect-ratio · any-pointer ·
//                         any-hover · (pointer: fine) · (hover: none) · not · only · media types · other features.
//      Every `@container` header is `i_container` unless declared. Declarations live in their own list
//      (`--media-exempt`, `file · header · count · reason`): an entry exempts the headers of that file whose normalised
//      header equals its own only when the count equals the number found — a malformed line, an empty reason, a count
//      mismatch, an entry matching nothing or a second entry for the same header is a hole (red, exempts nothing).
//      Sub-condition hover (`i_hover`, never exemptable): a rule whose selector holds `:hover` must sit inside at least
//      one `@media`, and every enclosing `@media` must have `(hover: hover)` as an `and` condition in every OR branch
//      (`@media (hover: hover), (max-width: 640px)` is red).
// `@layer` blocks are transparent: rules inside `@layer x { … }` are judged like unlayered ones.
// Exit: 0 green · 1 red · 78 readiness failure (no files, a missing list (same-in-dark · primitives ·
//   primitives-exempt · media-exempt), a listed file missing on disk,
//   `typescript` not resolvable).
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
import { createRequire } from 'node:module';
import { join, relative, sep } from 'node:path';
import { CANON_PREFIX, COLOR_FAMILY, INPUT_ALLOWED, WIDTH_MAX, WIDTH_MIN } from './design-families.mjs';

const READINESS = 78;
const TOKENS = 'src/shell/tokens.css';
// CANON_PREFIX · COLOR_FAMILY come from design-families.mjs (shared with design-docs.mjs · P5 advisor ②).
const COLOR_LITERAL = /#[0-9a-fA-F]{3,8}\b|\b(rgba?|hsla?|hwb|lab|lch|oklab|oklch|color|color-mix)\(|\b(white|black)\b/;
// CSS Color 4 named colours (148 · `transparent`/`currentcolor` are keywords, not in this list).
const COLOR_NAMES = new Set(('aliceblue antiquewhite aqua aquamarine azure beige bisque black blanchedalmond blue '
  + 'blueviolet brown burlywood cadetblue chartreuse chocolate coral cornflowerblue cornsilk crimson cyan darkblue '
  + 'darkcyan darkgoldenrod darkgray darkgreen darkgrey darkkhaki darkmagenta darkolivegreen darkorange darkorchid '
  + 'darkred darksalmon darkseagreen darkslateblue darkslategray darkslategrey darkturquoise darkviolet deeppink '
  + 'deepskyblue dimgray dimgrey dodgerblue firebrick floralwhite forestgreen fuchsia gainsboro ghostwhite gold '
  + 'goldenrod gray green greenyellow grey honeydew hotpink indianred indigo ivory khaki lavender lavenderblush '
  + 'lawngreen lemonchiffon lightblue lightcoral lightcyan lightgoldenrodyellow lightgray lightgreen lightgrey '
  + 'lightpink lightsalmon lightseagreen lightskyblue lightslategray lightslategrey lightsteelblue lightyellow lime '
  + 'limegreen linen magenta maroon mediumaquamarine mediumblue mediumorchid mediumpurple mediumseagreen '
  + 'mediumslateblue mediumspringgreen mediumturquoise mediumvioletred midnightblue mintcream mistyrose moccasin '
  + 'navajowhite navy oldlace olive olivedrab orange orangered orchid palegoldenrod palegreen paleturquoise '
  + 'palevioletred papayawhip peachpuff peru pink plum powderblue purple rebeccapurple red rosybrown royalblue '
  + 'saddlebrown salmon sandybrown seagreen seashell sienna silver skyblue slateblue slategray slategrey snow '
  + 'springgreen steelblue tan teal thistle tomato turquoise violet wheat white whitesmoke yellow yellowgreen').split(' '));
if (COLOR_NAMES.size !== 148) throw new Error(`COLOR_NAMES must hold 148 names, has ${COLOR_NAMES.size}`);
const COLOR_FN = /^(rgba?|hsla?|hwb|lab|lch|oklab|oklch|color|color-mix)$/i;
// Properties whose identifiers are names, not colours (font families, animation/grid/counter names).
const NAME_PROPS = /^(font|font-family|animation|animation-name|grid-area|grid-row|grid-column|grid-template-areas|grid-template|counter-reset|counter-increment|counter-set|transition-property|will-change|content|quotes|list-style-type|view-transition-name|container-name|anchor-name|position-anchor)$/i;
const ROOT_SEL = /:root(?![\w-])/;
const DARK_SEL = /\[data-theme=["']?dark["']?\]/;

function args() {
  const argv = process.argv.slice(2);
  const out = { root: '.', sameInDark: null, primitives: null, primitivesExempt: null, mediaExempt: null, files: [] };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--root') out.root = argv[++i];
    else if (argv[i] === '--same-in-dark') out.sameInDark = argv[++i];
    else if (argv[i] === '--primitives') out.primitives = argv[++i];
    else if (argv[i] === '--primitives-exempt') out.primitivesExempt = argv[++i];
    else if (argv[i] === '--media-exempt') out.mediaExempt = argv[++i];
    else if (argv[i] === '--') { out.files = argv.slice(i + 1); break; }
  }
  return out;
}

function readiness(msg) {
  console.log(`design-lint readiness: ${msg}`);
  process.exit(READINESS);
}

// Replace comments with blanks, keeping newlines so line numbers stay true.
function stripComments(src) {
  return src.replace(/\/\*[\s\S]*?\*\//g, m => m.replace(/[^\n]/g, ' '));
}

// Minimal CSS walker: yields declarations (with the chain of enclosing preludes),
// top-level at-statements (@import), and rule preludes.
function walk(src) {
  const decls = [];
  const statements = [];
  const rules = [];
  const stack = [];
  let buf = '';
  let bufLine = 1;
  let line = 1;
  let paren = 0;
  let quote = null;
  for (let i = 0; i < src.length; i++) {
    const ch = src[i];
    if (ch === '\n') line++;
    if (quote) { buf += ch; if (ch === quote && src[i - 1] !== '\\') quote = null; continue; }
    if (ch === '"' || ch === "'") { if (!buf.trim()) bufLine = line; buf += ch; quote = ch; continue; }
    if (ch === '(') paren++;
    if (ch === ')') paren = Math.max(0, paren - 1);
    if (paren === 0 && ch === '{') {
      const prelude = buf.trim();
      stack.push({ prelude, line: bufLine });
      rules.push({ prelude, line: bufLine, chain: stack.map(s => s.prelude) });
      buf = '';
      continue;
    }
    if (paren === 0 && (ch === ';' || ch === '}')) {
      const text = buf.trim();
      if (text) {
        if (stack.length === 0 || text.startsWith('@')) statements.push({ text, line: bufLine, depth: stack.length });
        else {
          const m = /^(--[A-Za-z0-9_-]+)\s*:([\s\S]*)$/.exec(text);
          decls.push({ prop: m ? m[1] : null, name: (/^([-\w]+)\s*:/.exec(text) || [])[1] || null, value: m ? m[2].trim() : text.replace(/^[^:]*:/, '').trim(), line: bufLine, chain: stack.map(s => s.prelude) });
        }
      }
      buf = '';
      if (ch === '}') stack.pop();
      continue;
    }
    if (!buf.trim() && /\S/.test(ch)) bufLine = line;
    buf += ch;
  }
  return { decls, statements, rules };
}

function selectorOf(chain) {
  for (let i = chain.length - 1; i >= 0; i--) if (!chain[i].startsWith('@')) return chain[i];
  return '';
}

function varRefs(value) {
  const out = [];
  const re = /var\(\s*(--[A-Za-z0-9_-]+)/g;
  let m;
  while ((m = re.exec(value))) out.push(m[1]);
  return out;
}

// Index of the `)` closing the `(` at `open` (strings already blanked), or value.length.
function closeParen(value, open) {
  let depth = 0;
  for (let i = open; i < value.length; i++) {
    if (value[i] === '(') depth++;
    else if (value[i] === ')' && --depth === 0) return i;
  }
  return value.length;
}

// color-mix(<interpolation>, <colour> [<pct>]?, <colour> [<pct>]?) — true when every colour argument is a
// var() reference, `transparent` or `currentColor` (percentages allowed).
function tokenOnlyMix(inner) {
  const args = [];
  let depth = 0, start = 0;
  for (let i = 0; i <= inner.length; i++) {
    const ch = inner[i];
    if (ch === '(') depth++;
    else if (ch === ')') depth--;
    else if ((ch === ',' || i === inner.length) && depth === 0) { args.push(inner.slice(start, i).trim()); start = i + 1; }
  }
  if (args.length < 3 || !/^in\s/i.test(args[0])) return false;
  return args.slice(1).every(a => {
    const colour = a.replace(/(^|\s)-?[\d.]+%(?=\s|$)/g, ' ').trim();
    return /^var\(\s*--[\w-]+\s*\)$/.test(colour) || /^(transparent|currentcolor)$/i.test(colour);
  });
}

// f — colour literals in one declaration value: [{ kind: 'direct'|'fallback'|'name', literal }].
function colourLiterals(prop, rawValue) {
  // Blank strings and url(...) bodies (keeping length) so `#id`, quoted text and file names never match.
  let value = rawValue.replace(/(["'])(?:\\.|(?!\1)[^\\])*\1/g, m => ' '.repeat(m.length));
  value = value.replace(/\burl\(([^)]*)\)/gi, (m, body) => `url(${' '.repeat(body.length)})`);
  const fallbacks = []; // [start, end) of every var() fallback
  for (const m of value.matchAll(/(?<![\w-])var\(/gi)) {
    const open = m.index + 3;
    const close = closeParen(value, open);
    let depth = 0;
    for (let i = open + 1; i < close; i++) {
      if (value[i] === '(') depth++;
      else if (value[i] === ')') depth--;
      else if (value[i] === ',' && depth === 0) { fallbacks.push([i + 1, close]); break; }
    }
  }
  const inFallback = pos => fallbacks.some(([s, e]) => pos >= s && pos < e);
  const out = [];
  const taken = []; // [start, end) of colour functions — their inner tokens are not counted again
  for (const m of value.matchAll(/(?<![\w-])([A-Za-z][\w-]*)\(/g)) {
    if (!COLOR_FN.test(m[1])) continue;
    const end = closeParen(value, m.index + m[1].length) + 1;
    if (taken.some(([s, e]) => m.index >= s && m.index < e)) continue;
    // color-mix() whose colours are only var()/transparent/currentColor mixes tokens — not a literal.
    // Its inner tokens are then scanned like any other value (a literal nested inside still counts).
    if (/^color-mix$/i.test(m[1]) && tokenOnlyMix(value.slice(m.index + m[1].length + 1, end - 1))) continue;
    taken.push([m.index, end]);
    out.push({ kind: inFallback(m.index) ? 'fallback' : 'direct', literal: rawValue.slice(m.index, end) });
  }
  const inTaken = pos => taken.some(([s, e]) => pos >= s && pos < e);
  for (const m of value.matchAll(/#([0-9a-fA-F]+)(?![\w-])/g)) {
    if (![3, 4, 6, 8].includes(m[1].length) || inTaken(m.index)) continue;
    out.push({ kind: inFallback(m.index) ? 'fallback' : 'direct', literal: m[0] });
  }
  if (!NAME_PROPS.test(prop || '')) {
    for (const m of value.matchAll(/(?<![\w#-])([A-Za-z]+)(?![\w(-])/g)) {
      if (!COLOR_NAMES.has(m[1].toLowerCase()) || inTaken(m.index)) continue;
      out.push({ kind: inFallback(m.index) ? 'fallback' : 'name', literal: m[1] });
    }
  }
  return out;
}

const norm = s => s.replace(/\s+/g, ' ').trim();

function listTsFiles(dir, acc = []) {
  if (!existsSync(dir)) return acc;
  for (const name of readdirSync(dir)) {
    if (name === 'node_modules' || name.startsWith('.')) continue;
    const p = join(dir, name);
    const st = statSync(p);
    if (st.isDirectory()) listTsFiles(p, acc);
    else if (/\.(ts|tsx)$/.test(name)) acc.push(p);
  }
  return acc;
}

// One list, two entry forms: `--name · reason` (c) and `f · file · selector · property · literal · reason` (f).
function parseSameInDark(path) {
  const entries = [];
  const fEntries = [];
  const text = readFileSync(path, 'utf8');
  text.split(/\r?\n/).forEach((raw, idx) => {
    const lineText = raw.trim();
    if (!lineText || lineText.startsWith('#')) return;
    if (/^f\s*·/.test(lineText)) {
      const parts = lineText.split('·').map(s => s.trim());
      if (parts.length < 6) { fEntries.push({ line: idx + 1, malformed: true, text: lineText }); return; }
      const [, file, selector, property, literal, ...reason] = parts;
      fEntries.push({ line: idx + 1, file, selector: norm(selector), property: property.toLowerCase(),
        literal: norm(literal).toLowerCase(), reason: reason.join(' · ').trim(), used: 0 });
      return;
    }
    const m = /^(--[A-Za-z0-9_-]+)\s*(?:·\s*(.*))?$/.exec(lineText);
    if (!m) { entries.push({ name: lineText, reason: '', line: idx + 1, malformed: true }); return; }
    entries.push({ name: m[1], reason: (m[2] || '').trim(), line: idx + 1 });
  });
  return { entries, fEntries };
}

// e — primitive list (`.btn` · `.chip--*`) and its exemption list (`file · selector · reason`).
function parsePrimitives(path) {
  const exact = new Set(); const prefixes = []; const bad = [];
  readFileSync(path, 'utf8').split(/\r?\n/).forEach((raw, idx) => {
    const t = raw.trim();
    if (!t || t.startsWith('#')) return;
    const m = /^\.(-?[A-Za-z_][\w-]*?)(\*)?$/.exec(t);
    if (!m) { bad.push(`primitives.txt:${idx + 1} 형식 오류 「${t}」(한 줄에 클래스 하나 · 접두 표기 .x--*)`); return; }
    if (m[2]) prefixes.push(m[1]); else exact.add(m[1]);
  });
  return { bad, size: exact.size + prefixes.length, has: n => exact.has(n) || prefixes.some(x => n.startsWith(x)) };
}
function parsePrimitivesExempt(path) {
  const out = [];
  readFileSync(path, 'utf8').split(/\r?\n/).forEach((raw, idx) => {
    const t = raw.trim();
    if (!t || t.startsWith('#')) return;
    const parts = t.split('·').map(x => x.trim());
    if (parts.length < 3) { out.push({ line: idx + 1, malformed: true, text: t }); return; }
    const [file, selector, ...reason] = parts;
    out.push({ line: idx + 1, file, selector: norm(selector), reason: reason.join(' · ').trim(), used: 0 });
  });
  return out;
}
// Split at top-level commas (outside (), [] and quotes).
function splitList(s) {
  const out = []; let depth = 0; let quote = null; let cur = '';
  for (const ch of s) {
    if (quote) { cur += ch; if (ch === quote) quote = null; continue; }
    if (ch === '"' || ch === "'") { quote = ch; cur += ch; continue; }
    if (ch === '(' || ch === '[') depth++;
    if (ch === ')' || ch === ']') depth--;
    if (ch === ',' && depth === 0) { out.push(cur.trim()); cur = ''; continue; }
    cur += ch;
  }
  if (cur.trim()) out.push(cur.trim());
  return out;
}
// Expand the first top-level `:is(`/`:where(` of a selector into one selector per argument (recursively).
function expandIsWhere(sel) {
  let depth = 0; let quote = null;
  for (let i = 0; i < sel.length; i++) {
    const ch = sel[i];
    if (quote) { if (ch === quote) quote = null; continue; }
    if (ch === '"' || ch === "'") { quote = ch; continue; }
    if (ch === '(' || ch === '[') { depth++; continue; }
    if (ch === ')' || ch === ']') { depth--; continue; }
    if (depth !== 0 || ch !== ':' || sel[i + 1] === ':' || sel[i - 1] === ':') continue;
    const m = /^:(is|where|matches|-webkit-any)\(/i.exec(sel.slice(i));
    if (!m) continue;
    const open = i + m[0].length - 1;
    let d = 0; let j = open;
    for (; j < sel.length; j++) { if (sel[j] === '(') d++; else if (sel[j] === ')') { d--; if (d === 0) break; } }
    const before = sel.slice(0, i); const after = sel.slice(j + 1);
    return splitList(sel.slice(open + 1, j)).flatMap(a => expandIsWhere(before + a + after));
  }
  return [sel];
}
// One compound → its simple selectors, or null when a top-level combinator makes it complex.
function compoundSimples(sel) {
  const s = sel.trim(); const simples = [];
  let i = 0;
  const ident = () => { const m = /^-?[A-Za-z_\\\u0080-￿][\w\\\u0080-￿-]*/.exec(s.slice(i)); if (!m) return null; i += m[0].length; return m[0]; };
  const balanced = (open, close) => { let d = 0; const st = i; for (; i < s.length; i++) { if (s[i] === open) d++; else if (s[i] === close) { d--; if (d === 0) { i++; return s.slice(st + 1, i - 1); } } } return null; };
  while (i < s.length) {
    const ch = s[i];
    if (/[\s>+~]/.test(ch)) return null;
    if (ch === '.') { i++; const n = ident(); if (n == null) return null; simples.push({ kind: 'class', name: n }); }
    else if (ch === '#') { i++; ident(); simples.push({ kind: 'id' }); }
    else if (ch === '*') { i++; simples.push({ kind: 'type' }); }
    else if (ch === '[') { if (balanced('[', ']') == null) return null; simples.push({ kind: 'attr' }); }
    else if (ch === ':') {
      i++; if (s[i] === ':') i++;
      if (ident() == null) return null;
      if (s[i] === '(' && balanced('(', ')') == null) return null;
      simples.push({ kind: 'pseudo' });
    } else { if (ident() == null) return null; simples.push({ kind: 'type' }); }
  }
  return simples;
}
// Is this selector-list argument a bare primitive definition (after :is()/:where() expansion)?
function barePrimitive(arg, prim) {
  for (const x of expandIsWhere(arg)) {
    const simples = compoundSimples(x);
    if (!simples) continue;
    const classes = simples.filter(y => y.kind === 'class');
    if (!classes.length || simples.some(y => y.kind === 'type' || y.kind === 'id')) continue;
    if (classes.every(y => prim.has(y.name))) return x.trim();
  }
  return null;
}
// i — width/input conditions. Tokens of one prelude body: balanced `( … )` groups and bare words.
function mediaTokens(body) {
  const out = []; let i = 0;
  while (i < body.length) {
    const ch = body[i];
    if (/\s/.test(ch)) { i++; continue; }
    if (ch === '(') {
      let d = 0; const st = i;
      for (; i < body.length; i++) { if (body[i] === '(') d++; else if (body[i] === ')' && --d === 0) { i++; break; } }
      out.push(body.slice(st, i)); continue;
    }
    const st = i;
    while (i < body.length && !/[\s(]/.test(body[i])) i++;
    out.push(body.slice(st, i).toLowerCase());
  }
  return out;
}
// `( name : value )` → `(name: value)` (lowercase · single spaces); anything without a plain colon keeps its text.
function normFeature(t) {
  const inner = t.slice(1, -1).replace(/\s+/g, ' ').trim().toLowerCase();
  const m = /^([a-z-]+) ?: ?(.+)$/.exec(inner);
  return m ? `(${m[1]}: ${m[2].trim()})` : `(${inner})`;
}
const normTokens = body => mediaTokens(body).map(t => (t.startsWith('(') ? normFeature(t) : t));
const AT_KIND = /^@(media|container)\b/i;
// Normalised header text: `@media (max-width: 720px), (pointer: coarse)` · `@container name (max-width: 400px)`.
function normHeader(prelude) {
  const m = AT_KIND.exec(prelude.trim());
  if (!m) return norm(prelude);
  const body = prelude.trim().slice(m[0].length);
  return `@${m[1].toLowerCase()} ${splitList(body).map(b => normTokens(b).join(' ')).join(', ')}`.trim();
}
// One condition → problems ([] = allowed · 'prefers' = counted only).
function judgeFeature(f) {
  const m = /^\(([a-z-]+): (.+)\)$/.exec(f);
  if (!m) return [{ kind: 'form', why: `${f} 범위 문법·이름 없는 조건` }];
  const [, name, value] = m;
  if (name === 'max-width' || name === 'min-width') {
    const px = /^(\d+)px$/.exec(value);
    if (!px) return [{ kind: 'form', why: `${f} 폭 값은 px 정수로만(em · rem · calc 는 형식 밖)` }];
    const allowed = name === 'max-width' ? WIDTH_MAX : WIDTH_MIN;
    return allowed.includes(Number(px[1])) ? [] : [{ kind: 'width', why: `${f} 허용 값 밖(${name} ${allowed.join(' · ')}px)` }];
  }
  if (INPUT_ALLOWED.includes(f)) return [];
  if (name.startsWith('prefers-')) return [{ kind: 'prefers' }];
  return [{ kind: 'form', why: `${f} 형식 밖(허용 = 폭 px · ${INPUT_ALLOWED.join(' · ')} · prefers-*)` }];
}
// One OR branch: `feature (and feature)*` — media types · not · only · or · a missing condition are form problems.
function judgeBranch(all) {
  if (!all.length) return [{ kind: 'form', why: '빈 조건' }];
  const out = [];
  let tokens = all;
  if (tokens[0] === 'not' || tokens[0] === 'only') { out.push({ kind: 'form', why: `「${tokens[0]}」 형식 밖` }); tokens = tokens.slice(1); }
  if (tokens.length && !tokens[0].startsWith('(')) {
    out.push({ kind: 'form', why: `매체 종류 「${tokens[0]}」 형식 밖` });
    tokens = tokens.slice(tokens[1] === 'and' ? 2 : 1);
    if (!tokens.length) return out;
  }
  tokens.forEach((t, k) => {
    if (k % 2 === 1) { if (t !== 'and') out.push({ kind: 'form', why: `「${t}」 조건은 and 로만 잇는다` }); return; }
    if (!t.startsWith('(')) { out.push({ kind: 'form', why: `「${t}」 형식 밖(조건은 괄호 하나씩)` }); return; }
    out.push(...judgeFeature(t));
  });
  if (tokens.length % 2 === 0) out.push({ kind: 'form', why: '마지막 and 뒤에 조건이 없다' });
  return out;
}
// Does every OR branch of this @media prelude carry `(hover: hover)` as an `and` condition?
function hoverGuarded(prelude) {
  const m = AT_KIND.exec(prelude.trim());
  return splitList(prelude.trim().slice(m[0].length)).every(b => {
    const t = normTokens(b);
    return t[0] !== 'not' && t.some((x, k) => k % 2 === 0 && x === '(hover: hover)');
  });
}
function parseMediaExempt(path) {
  const out = [];
  readFileSync(path, 'utf8').split(/\r?\n/).forEach((raw, idx) => {
    const t = raw.trim();
    if (!t || t.startsWith('#')) return;
    const parts = t.split('·').map(x => x.trim());
    if (parts.length < 4 || !/^[1-9]\d*$/.test(parts[2]) || !AT_KIND.test(parts[1])) { out.push({ line: idx + 1, malformed: true, text: t }); return; }
    const [file, header, count, ...reason] = parts;
    out.push({ line: idx + 1, file, header: normHeader(header), count: Number(count), reason: reason.join(' · ').trim() });
  });
  return out;
}

const PRIMITIVES_CSS = 'src/shell/primitives.css';
const NO_IMPORTANT = new Set([PRIMITIVES_CSS, 'src/shell/base.css']);

const opt = args();
const root = opt.root;
const files = opt.files.map(f => f.split(sep).join('/')).filter(f => f.endsWith('.css'));
if (files.length === 0) readiness('대상 CSS 0건 — 검사한 것이 없다');
if (!opt.sameInDark || !existsSync(opt.sameInDark)) readiness(`same-in-dark 목록이 없다: ${opt.sameInDark ?? '(미지정)'}`);
if (!opt.primitives || !existsSync(opt.primitives)) readiness(`프리미티브 목록이 없다: ${opt.primitives ?? '(미지정)'} — 목록이 없으면 e 를 판정할 수 없다`);
if (!opt.primitivesExempt || !existsSync(opt.primitivesExempt)) readiness(`프리미티브 면제 목록이 없다: ${opt.primitivesExempt ?? '(미지정)'}`);
if (!opt.mediaExempt || !existsSync(opt.mediaExempt)) readiness(`폭·입력 조건 면제 목록이 없다: ${opt.mediaExempt ?? '(미지정)'} — 선언이 없으면 i 의 면제를 셀 수 없다`);
const prim = parsePrimitives(opt.primitives);
const eHits = [];      // {file,line,sel,expanded} — bare primitive definitions outside primitives.css
const eImportant = []; // {file,line,sel,prop} — !important inside primitives.css / base.css

const aRoot = [];      // {file,line,name}
const aScoped = [];    // canonical-family names in screen scope
const dHits = [];      // {file,line,what}
const refs = [];       // {file,line,name}
const defined = new Set();
const light = new Map(); // name -> value (tokens.css, non-dark)
const dark = new Map();
const scopedColor = []; // screen-scope defs whose value holds a colour literal
const iHeads = [];      // {file,line,header,kind:'width'|'form'|'container',why} — i violations before exemptions
const iHover = [];      // {file,line,sel,media} — :hover rules outside (hover: hover)
let mediaRules = 0, containerRules = 0, hoverRules = 0, mediaPrefers = 0;
const fHits = [];       // {file,line,sel,prop,kind,literal} — colour literals outside tokens.css
let tokensSeen = false;

for (const file of files) {
  const abs = join(root, file);
  if (!existsSync(abs)) readiness(`대상 목록의 파일이 디스크에 없다: ${file} — 추적 중인데 지워졌다면 git rm 으로 목록에서도 뺀다`);
  const src = stripComments(readFileSync(abs, 'utf8'));
  const { decls, statements, rules } = walk(src);
  const isTokens = file === TOKENS;
  if (isTokens) tokensSeen = true;
  for (const st of statements) {
    if (/^@import\b/.test(st.text) && !isTokens) dHits.push({ file, line: st.line, what: st.text.replace(/\s+/g, ' ') });
  }
  if (!isTokens) {
    for (const r of rules) {
      if (!r.prelude.startsWith('@') && ROOT_SEL.test(r.prelude)) dHits.push({ file, line: r.line, what: `:root 셀렉터 「${r.prelude.replace(/\s+/g, ' ')}」` });
    }
  }
  if (file !== PRIMITIVES_CSS) {
    for (const r of rules) {
      if (r.prelude.startsWith('@') || r.chain.some(c => /^@(-webkit-)?(keyframes|font-face)/i.test(c))) continue;
      for (const arg of splitList(r.prelude)) {
        const hit = barePrimitive(arg, prim);
        if (hit) eHits.push({ file, line: r.line, sel: norm(arg), expanded: norm(hit) });
      }
    }
  }
  for (const r of rules) {
    const at = AT_KIND.exec(r.prelude);
    if (at && at[1].toLowerCase() === 'container') {
      containerRules++;
      iHeads.push({ file, line: r.line, header: normHeader(r.prelude), kind: 'container', why: '부품 칸 폭 조건은 면제 목록 선언이 있어야 한다' });
    } else if (at) {
      mediaRules++;
      const branches = splitList(r.prelude.trim().slice(at[0].length));
      const probs = branches.length ? branches.flatMap(b => judgeBranch(normTokens(b))) : [{ kind: 'form', why: '조건 없는 @media' }];
      if (probs.some(p => p.kind === 'prefers')) mediaPrefers++;
      const bad = probs.filter(p => p.kind === 'form' || p.kind === 'width');
      if (bad.length) iHeads.push({ file, line: r.line, header: normHeader(r.prelude), kind: bad.some(p => p.kind === 'form') ? 'form' : 'width', why: bad.map(p => p.why).join(' · ') });
    } else if (!r.prelude.startsWith('@') && /:hover(?![\w-])/.test(r.prelude) && !r.chain.some(c => /^@(-webkit-)?keyframes/i.test(c))) {
      hoverRules++;
      const media = r.chain.filter(c => /^@media\b/i.test(c));
      if (!media.length || !media.every(hoverGuarded)) iHover.push({ file, line: r.line, sel: norm(r.prelude), media: media.map(normHeader).join(' 안 ') || '조건 없음' });
    }
  }
  if (NO_IMPORTANT.has(file)) {
    for (const d of decls) if (/!\s*important\s*$/i.test(d.value)) eImportant.push({ file, line: d.line, sel: norm(selectorOf(d.chain)), prop: d.name || '' });
  }
  for (const d of decls) {
    for (const n of varRefs(d.value)) refs.push({ file, line: d.line, name: n });
    if (!isTokens) {
      for (const lit of colourLiterals(d.name, d.value)) {
        fHits.push({ file, line: d.line, sel: norm(selectorOf(d.chain)), prop: (d.name || '').toLowerCase(), ...lit });
      }
    }
    if (!d.prop) continue;
    defined.add(d.prop);
    const sel = selectorOf(d.chain);
    if (isTokens) {
      if (DARK_SEL.test(sel)) dark.set(d.prop, d.value);
      else light.set(d.prop, d.value);
      continue;
    }
    if (ROOT_SEL.test(sel)) aRoot.push({ file, line: d.line, name: d.prop });
    else {
      if (CANON_PREFIX.test(d.prop)) aScoped.push({ file, line: d.line, name: d.prop, sel });
      if (COLOR_LITERAL.test(d.value)) scopedColor.push({ file, line: d.line, name: d.prop, sel });
    }
  }
}

// g — JSX `style` attributes, read through the TypeScript AST.
let ts;
try {
  ts = createRequire(import.meta.url)(process.env.COLAB_DESIGN_LINT_TYPESCRIPT || 'typescript');
} catch (e) {
  readiness(`typescript 파서를 불러오지 못했다(${process.env.COLAB_DESIGN_LINT_TYPESCRIPT || 'typescript'}) — frontend 에서 npm ci 가 먼저다: ${String(e.message).split('\n')[0]}`);
}
const gHits = [];    // {file,line,keys}
const gSpread = [];  // {file,line} — `style` keys inside JSX spread attributes (judged like attributes)
let gVars = 0;
let tsxCount = 0;
const unwrap = n => {
  while (n && (ts.isParenthesizedExpression(n) || ts.isAsExpression(n) || ts.isTypeAssertionExpression(n)
    || ts.isNonNullExpression(n) || (ts.isSatisfiesExpression && ts.isSatisfiesExpression(n)))) n = n.expression;
  return n;
};
const keyText = (p, sf) => {
  if (ts.isShorthandPropertyAssignment(p)) return { key: p.name.text, shorthand: true };
  if (ts.isSpreadAssignment(p)) return { key: `...${p.expression.getText(sf)}` };
  const name = p.name;
  if (!name) return { key: p.getText(sf) };
  if (ts.isIdentifier(name) || ts.isStringLiteral(name) || ts.isNoSubstitutionTemplateLiteral(name) || ts.isNumericLiteral(name)) return { key: name.text };
  if (ts.isComputedPropertyName(name)) {
    const e = unwrap(name.expression);
    if (ts.isStringLiteral(e) || ts.isNoSubstitutionTemplateLiteral(e)) return { key: e.text };
    return { key: `[${name.expression.getText(sf)}]` };
  }
  return { key: name.getText(sf) };
};
function scanStyles(rel, text) {
  const sf = ts.createSourceFile(rel, text, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  const lineOf = n => sf.getLineAndCharacterOfPosition(n.getStart(sf)).line + 1;
  // One judgement for both forms: `style={…}` and a `style` key inside a JSX spread attribute.
  const judge = (at, expr, raw, via) => {
    const obj = expr ? unwrap(expr) : null;
    if (!obj || !ts.isObjectLiteralExpression(obj)) {
      gHits.push({ file: rel, line: lineOf(at), via, keys: [`(객체 리터럴 아님: ${raw ? raw.getText(sf).slice(0, 60) : '값 없음'})`] });
      return;
    }
    const keys = obj.properties.map(p => keyText(p, sf));
    const bad = keys.filter(k => !k.key.startsWith('--'));
    if (bad.length) gHits.push({ file: rel, line: lineOf(at), via, keys: bad.map(k => (k.shorthand ? `${k.key}(축약형)` : k.key)) });
    else if (keys.length) gVars++;
  };
  const visit = node => {
    if (ts.isJsxAttribute(node) && node.name.getText(sf) === 'style') {
      const init = node.initializer;
      judge(node, init && ts.isJsxExpression(init) ? init.expression : null, init, 'attr');
    }
    if (ts.isJsxSpreadAttribute(node)) {
      const find = n => {
        if ((ts.isPropertyAssignment(n) || ts.isShorthandPropertyAssignment(n)) && keyText(n, sf).key === 'style') {
          gSpread.push({ file: rel, line: lineOf(n) });
          judge(n, ts.isPropertyAssignment(n) ? n.initializer : null, n, 'spread');
        }
        ts.forEachChild(n, find);
      };
      find(node.expression);
    }
    ts.forEachChild(node, visit);
  };
  visit(sf);
}

for (const tsFile of listTsFiles(join(root, 'src'))) {
  const text = readFileSync(tsFile, 'utf8');
  const re = /['"`](--[A-Za-z0-9_-]+)['"`]/g;
  let m;
  while ((m = re.exec(text))) defined.add(m[1]);
  if (tsFile.endsWith('.tsx')) {
    tsxCount++;
    scanStyles(relative(root, tsFile).split(sep).join('/'), text);
  }
}

const bHits = refs.filter(r => !defined.has(r.name));

// c — dark pairing.
const { entries, fEntries } = parseSameInDark(opt.sameInDark);
const exempt = new Map(entries.filter(e => !e.malformed).map(e => [e.name, e]));
const covered = name => {
  const seen = new Set();
  let cur = name;
  while (cur && !seen.has(cur)) {
    seen.add(cur);
    if (dark.has(cur)) return true;
    const v = light.get(cur);
    if (v === undefined) return false;
    const m = /^var\(\s*(--[A-Za-z0-9_-]+)/.exec(v);
    if (!m) return false;
    if (exempt.has(m[1]) && light.has(m[1]) && !dark.has(m[1])) return true;
    cur = m[1];
  }
  return false;
};
const cMissing = [...light.keys()].filter(n => COLOR_FAMILY.test(n) && !covered(n) && !exempt.has(n));
const cDarkOnly = [...dark.keys()].filter(n => !light.has(n) && n.startsWith('--'));
const cHoles = [];
for (const e of entries) {
  if (e.malformed) cHoles.push(`same-in-dark.txt:${e.line} 형식 오류 「${e.name}」(이름 · 사유)`);
  else if (!e.reason) cHoles.push(`same-in-dark.txt:${e.line} ${e.name} — 사유 칸이 비었다`);
  else if (!light.has(e.name)) cHoles.push(`same-in-dark.txt:${e.line} ${e.name} — 라이트 :root 에 없는 이름(낡은 항목)`);
  else if (dark.has(e.name)) cHoles.push(`same-in-dark.txt:${e.line} ${e.name} — 다크 블록에 이미 있다`);
}

const a = aRoot.length + aScoped.length;
const b = bHits.length;
const c = cMissing.length + cDarkOnly.length + cHoles.length;
const d = dHits.length;
const m = entries.length;

// f — match exemptions (file · selector · property · literal), then count what is left.
const fHoles = [];
const fExempted = [];
const fLive = [];
for (const h of fHits) {
  const e = fEntries.find(x => !x.malformed && x.reason && x.file === h.file && x.selector === h.sel
    && x.property === h.prop && x.literal === norm(h.literal).toLowerCase());
  if (e) { e.used++; fExempted.push(h); } else fLive.push(h);
}
for (const e of fEntries) {
  if (e.malformed) fHoles.push(`same-in-dark.txt:${e.line} f 형식 오류 「${e.text}」(f · 파일 · 선택자 · 속성 · 리터럴 · 사유)`);
  else if (!e.reason) fHoles.push(`same-in-dark.txt:${e.line} f ${e.file} ${e.selector} ${e.property} ${e.literal} — 사유 칸이 비었다(면제하지 않는다)`);
  else if (!e.used) fHoles.push(`same-in-dark.txt:${e.line} f ${e.file} ${e.selector} ${e.property} ${e.literal} — 걸리는 리터럴이 없다(낡은 항목)`);
}
const fCount = kind => fLive.filter(h => h.kind === kind).length;

// e — match exemptions (file · selector-list argument), then count what is left.
const eEntries = parsePrimitivesExempt(opt.primitivesExempt);
const eHoles = [...prim.bad];
const eExempted = [];
const eLive = [];
for (const h of eHits) {
  const x = eEntries.find(y => !y.malformed && y.reason && y.file === h.file && y.selector === h.sel);
  if (x) { x.used++; eExempted.push(h); } else eLive.push(h);
}
for (const x of eEntries) {
  if (x.malformed) eHoles.push(`primitives-exempt.txt:${x.line} 형식 오류 「${x.text}」(파일 · 선택자 · 사유)`);
  else if (!x.reason) eHoles.push(`primitives-exempt.txt:${x.line} ${x.file} ${x.selector} — 사유 칸이 비었다(면제하지 않는다)`);
  else if (!x.used) eHoles.push(`primitives-exempt.txt:${x.line} ${x.file} ${x.selector} — 걸리는 맨 정의가 없다(낡은 항목)`);
}
// i — match declarations (file · normalised header · count), then count what is left.
const iEntries = parseMediaExempt(opt.mediaExempt);
const iHoles = [];
const iExempted = [];
const seenKey = new Set();
for (const x of iEntries) {
  if (x.malformed) { iHoles.push(`media-exempt.txt:${x.line} 형식 오류 「${x.text}」(파일 · 조건 · 개수 · 사유)`); continue; }
  const key = `${x.file} ${x.header}`;
  const hits = iHeads.filter(h => h.file === x.file && h.header === x.header);
  const where = `media-exempt.txt:${x.line} ${x.file} ${x.header}`;
  if (seenKey.has(key)) iHoles.push(`${where} — 같은 조건의 두 번째 줄(면제하지 않는다)`);
  else if (!x.reason) iHoles.push(`${where} — 사유 칸이 비었다(면제하지 않는다)`);
  else if (!hits.length) iHoles.push(`${where} — 맞는 머리가 없다(낡은 줄)`);
  else if (hits.length !== x.count) iHoles.push(`${where} — 선언 ${x.count} · 찾은 ${hits.length}(개수가 어긋나 면제하지 않는다)`);
  else iExempted.push(...hits);
  seenKey.add(key);
}
const iLive = iHeads.filter(h => !iExempted.includes(h));
const iKind = k => iLive.filter(h => h.kind === k);
const i = iLive.length + iHover.length + iHoles.length;
const im = iEntries.length;
const e = eLive.length + eImportant.length + eHoles.length;
const em = eEntries.length;
const f = fLive.length + fHoles.length;
const fm = fEntries.length;
const g = gHits.length;

const show = (title, items, fmt) => {
  if (!items.length) return;
  console.log(`${title} ${items.length}`);
  for (const it of items) console.log(`  ${fmt(it)}`);
};
if (!tokensSeen) console.log(`정본 ${TOKENS} 가 대상에 없다 — 라이트·다크 목록이 비어 c 를 잴 수 없다`);
show('a :root 안 정의(정본 밖)', aRoot, x => `${x.file}:${x.line} ${x.name}`);
show('a 화면 범위의 정본 계열 이름', aScoped, x => `${x.file}:${x.line} ${x.name} (${x.sel})`);
show('b 미정의 참조', bHits, x => `${x.file}:${x.line} var(${x.name})`);
show('c 다크 누락', cMissing, x => x);
show('c 다크에만 있는 이름', cDarkOnly, x => x);
show('c 면제 목록 구멍', cHoles, x => x);
show('d :root/@import', dHits, x => `${x.file}:${x.line} ${x.what}`);
if (scopedColor.length) show('참고 · 범위 색 토큰(다크 미검사)', scopedColor, x => `${x.file}:${x.line} ${x.name} (${x.sel})`);
show('f 색 리터럴(정본 밖)', fLive, x => `${x.file}:${x.line} ${x.sel} { ${x.prop}: … ${x.literal} } (${x.kind === 'fallback' ? 'var() 폴백' : x.kind === 'name' ? '색 이름' : '직접'})`);
show('f 면제 목록 구멍', fHoles, x => x);
show('g 인라인 style 의 비변수 키', gHits, x => `${x.file}:${x.line} ${x.keys.join(', ')}${x.via === 'spread' ? ' (펼침 속성)' : ''}`);
show('e 프리미티브 맨 정의(primitives.css 밖)', eLive, x => `${x.file}:${x.line} ${x.sel}${x.expanded !== x.sel ? ` (펼침 ${x.expanded})` : ''}`);
show('e primitives.css·base.css 의 !important', eImportant, x => `${x.file}:${x.line} ${x.sel} { ${x.prop} }`);
show('e 목록·면제 구멍', eHoles, x => x);
show('i 폭 조건(허용 값 밖)', iKind('width'), x => `${x.file}:${x.line} ${x.header} — ${x.why}`);
show('i 형식 밖 조건', iKind('form'), x => `${x.file}:${x.line} ${x.header} — ${x.why}`);
show('i 선언 없는 @container', iKind('container'), x => `${x.file}:${x.line} ${x.header} — ${x.why}`);
show('i (hover: hover) 밖 :hover', iHover, x => `${x.file}:${x.line} ${x.sel} (둘러싼 @media: ${x.media})`);
show('i 면제 목록 구멍', iHoles, x => x);
if (em) console.log(`면제(e) ${em}: ${eEntries.map(x => x.malformed ? `형식 오류(${x.line}행)` : `${x.file} ${x.selector}(${x.reason || '사유 없음'})`).join(' · ')}`);
if (fm) console.log(`면제(f) ${fm}: ${fEntries.map(e => e.malformed ? `형식 오류(${e.line}행)` : `${e.file} ${e.selector} ${e.property} ${e.literal}(${e.reason || '사유 없음'})`).join(' · ')}`);
if (im) console.log(`면제(i) ${im}줄 · 적중 ${iExempted.length}: ${iEntries.map(x => x.malformed ? `형식 오류(${x.line}행)` : `${x.file} ${x.header} ×${x.count}(${x.reason || '사유 없음'})`).join(' · ')}`);
if (m) console.log(`면제(same-in-dark) ${m}: ${entries.map(e => `${e.name}(${e.reason || '사유 없음'})`).join(' · ')}`);

const redAll = a + b + c + d + e + f + g + i + (tokensSeen ? 0 : 1);
console.log(`파일 ${files.length} · :root 정의 밖 ${a} · 미정의 참조 ${b} · 다크 누락 ${c}(면제 ${m}) · :root/@import ${d} · 범위 색 토큰 ${scopedColor.length}(다크 미검사) · 색 리터럴 ${f}(면제 ${fm}) · 인라인 ${g}(변수 대입 ${gVars}) · 프리미티브 맨 정의 밖 ${e}(면제 ${em}) · 폭·입력 조건 밖 ${i}(면제 ${im})`);
console.log(`design-lint-counts files=${files.length} a=${a} a_root=${aRoot.length} a_scoped=${aScoped.length} b=${b} c=${c} c_missing=${cMissing.length} c_dark_only=${cDarkOnly.length} c_holes=${cHoles.length} exempt=${m} d=${d} scoped_color=${scopedColor.length} f=${f} f_direct=${fCount('direct')} f_fallback=${fCount('fallback')} f_name=${fCount('name')} f_holes=${fHoles.length} f_exempt=${fm} f_exempted_hits=${fExempted.length} g=${g} g_vars=${gVars} g_spread=${gSpread.length} tsx=${tsxCount} e=${e} e_bare=${eLive.length} e_important=${eImportant.length} e_holes=${eHoles.length} e_exempt=${em} e_exempted_hits=${eExempted.length} primitives=${prim.size} tokens=${tokensSeen ? 1 : 0} i=${i} i_media=${iKind('width').length} i_container=${iKind('container').length} i_form=${iKind('form').length} i_hover=${iHover.length} i_holes=${iHoles.length} i_exempt=${im} i_exempted_hits=${iExempted.length} media_rules=${mediaRules} container_rules=${containerRules} hover_rules=${hoverRules} media_prefers=${mediaPrefers}`);
process.exit(redAll > 0 ? 1 : 0);
