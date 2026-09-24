#!/usr/bin/env node
// frontend-design-lint judge (zero-dependency; node built-ins only).
//
// Usage: node scripts/design-lint.mjs --root <frontendDir> --same-in-dark <file> -- <css files relative to root...>
//   TS/TSX files under <root>/src are scanned for '--name' string literals (style={{'--w': v}} ·
//   setProperty('--x', ...)) and those names count as defined for rule b.
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
// `@layer` blocks are transparent: rules inside `@layer x { … }` are judged like unlayered ones.
// Exit: 0 green · 1 red · 78 readiness failure (no files, missing list, a listed file missing on disk).
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
import { join, relative, sep } from 'node:path';

const READINESS = 78;
const TOKENS = 'src/shell/tokens.css';
const CANON_PREFIX = /^--(color|space|text|radius|font|shadow|leading|tracking|fg|bg|accent)-/;
const COLOR_FAMILY = /^--(color|fg|bg|accent|shadow)-/;
const COLOR_LITERAL = /#[0-9a-fA-F]{3,8}\b|\b(rgba?|hsla?|hwb|lab|lch|oklab|oklch|color|color-mix)\(|\b(white|black)\b/;
const ROOT_SEL = /:root(?![\w-])/;
const DARK_SEL = /\[data-theme=["']?dark["']?\]/;

function args() {
  const argv = process.argv.slice(2);
  const out = { root: '.', sameInDark: null, files: [] };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--root') out.root = argv[++i];
    else if (argv[i] === '--same-in-dark') out.sameInDark = argv[++i];
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
          decls.push({ prop: m ? m[1] : null, value: m ? m[2].trim() : text.replace(/^[^:]*:/, '').trim(), line: bufLine, chain: stack.map(s => s.prelude) });
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

function parseSameInDark(path) {
  const entries = [];
  const text = readFileSync(path, 'utf8');
  text.split(/\r?\n/).forEach((raw, idx) => {
    const lineText = raw.trim();
    if (!lineText || lineText.startsWith('#')) return;
    const m = /^(--[A-Za-z0-9_-]+)\s*(?:·\s*(.*))?$/.exec(lineText);
    if (!m) { entries.push({ name: lineText, reason: '', line: idx + 1, malformed: true }); return; }
    entries.push({ name: m[1], reason: (m[2] || '').trim(), line: idx + 1 });
  });
  return entries;
}

const opt = args();
const root = opt.root;
const files = opt.files.map(f => f.split(sep).join('/')).filter(f => f.endsWith('.css'));
if (files.length === 0) readiness('대상 CSS 0건 — 검사한 것이 없다');
if (!opt.sameInDark || !existsSync(opt.sameInDark)) readiness(`same-in-dark 목록이 없다: ${opt.sameInDark ?? '(미지정)'}`);

const aRoot = [];      // {file,line,name}
const aScoped = [];    // canonical-family names in screen scope
const dHits = [];      // {file,line,what}
const refs = [];       // {file,line,name}
const defined = new Set();
const light = new Map(); // name -> value (tokens.css, non-dark)
const dark = new Map();
const scopedColor = []; // screen-scope defs whose value holds a colour literal
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
  for (const d of decls) {
    for (const n of varRefs(d.value)) refs.push({ file, line: d.line, name: n });
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

for (const tsFile of listTsFiles(join(root, 'src'))) {
  const text = readFileSync(tsFile, 'utf8');
  const re = /['"`](--[A-Za-z0-9_-]+)['"`]/g;
  let m;
  while ((m = re.exec(text))) defined.add(m[1]);
}

const bHits = refs.filter(r => !defined.has(r.name));

// c — dark pairing.
const entries = parseSameInDark(opt.sameInDark);
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
if (m) console.log(`면제(same-in-dark) ${m}: ${entries.map(e => `${e.name}(${e.reason || '사유 없음'})`).join(' · ')}`);

const redAll = a + b + c + d + (tokensSeen ? 0 : 1);
console.log(`파일 ${files.length} · :root 정의 밖 ${a} · 미정의 참조 ${b} · 다크 누락 ${c}(면제 ${m}) · :root/@import ${d} · 범위 색 토큰 ${scopedColor.length}(다크 미검사)`);
console.log(`design-lint-counts files=${files.length} a=${a} a_root=${aRoot.length} a_scoped=${aScoped.length} b=${b} c=${c} c_missing=${cMissing.length} c_dark_only=${cDarkOnly.length} c_holes=${cHoles.length} exempt=${m} d=${d} scoped_color=${scopedColor.length} tokens=${tokensSeen ? 1 : 0}`);
process.exit(redAll > 0 ? 1 : 0);
