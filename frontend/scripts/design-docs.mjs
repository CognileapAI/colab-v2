#!/usr/bin/env node
// Design-system document tables (spec S-DESIGN-STRUCTURE-P5-20260924) — node built-ins only.
//
// Rewrites exactly two marked blocks of the design-system document from the real inputs:
//   <!-- generated:tokens --> … <!-- /generated:tokens -->          ← tokens.css + same-in-dark.txt
//   <!-- generated:primitives --> … <!-- /generated:primitives -->  ← primitives.css + primitives.txt +
//                                                                      primitives-exempt.txt + same-in-dark.txt (f lines)
// Text outside the two blocks is hand-written and never touched or compared.
// Deterministic: the block text depends only on the input bytes (no dates, no absolute paths);
// each block lists the sha256 of the inputs it was built from.
//
// Usage (paths relative to the repository root unless absolute):
//   node frontend/scripts/design-docs.mjs            rewrite both blocks in place
//   node frontend/scripts/design-docs.mjs --check    compare both blocks only (gate frontend-design-lint h)
//   options: --doc <file> (default env COLAB_DESIGN_LINT_DOC, else docs/design-system.md) ·
//            --tokens <css> · --primitives-css <css> · --primitives <txt> · --primitives-exempt <txt> · --same-in-dark <txt>
//   The gate's own env names for the lists (COLAB_DESIGN_LINT_PRIMITIVES …) are deliberately NOT read here:
//   the document describes the repository, so the gate's fixture overrides must not change what h compares.
// Exit: 0 same (or written) · 1 a block differs (--check) · 78 missing document / marker pair / input file.
import { createHash } from 'node:crypto';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, isAbsolute, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const READINESS = 78;
const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..');
// Same families as design-lint.mjs rules a/c (kept in sync by hand — design-lint.mjs runs on import).
const CANON_FAMILIES = ['color', 'space', 'text', 'radius', 'font', 'shadow', 'leading', 'tracking', 'fg', 'bg', 'accent'];
const COLOR_FAMILY = /^--(color|fg|bg|accent|shadow)-/;
const DARK_SEL = /^:root\[data-theme=["']?dark["']?\]$/;

function notReady(msg) {
  console.log(`design-docs readiness: ${msg}`);
  process.exit(READINESS);
}

function args(argv) {
  const out = {
    check: false,
    doc: process.env.COLAB_DESIGN_LINT_DOC || 'docs/design-system.md',
    tokens: 'frontend/src/shell/tokens.css',
    primitivesCss: 'frontend/src/shell/primitives.css',
    primitives: 'gates/fixtures/frontend-design-lint/primitives.txt',
    primitivesExempt: 'gates/fixtures/frontend-design-lint/primitives-exempt.txt',
    sameInDark: 'gates/fixtures/frontend-design-lint/same-in-dark.txt',
  };
  const flags = { '--doc': 'doc', '--tokens': 'tokens', '--primitives-css': 'primitivesCss', '--primitives': 'primitives',
    '--primitives-exempt': 'primitivesExempt', '--same-in-dark': 'sameInDark' };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--check') out.check = true;
    else if (flags[argv[i]] && i + 1 < argv.length) out[flags[argv[i]]] = argv[++i];
    else notReady(`알 수 없는 인자 ${argv[i]}`);
  }
  return out;
}

const abs = p => (isAbsolute(p) ? p : resolve(ROOT, p));
function input(label, p) {
  const file = abs(p);
  if (!existsSync(file)) notReady(`${label} 부재: ${p}`);
  const buf = readFileSync(file);
  return { path: p, text: buf.toString('utf8'), sha: createHash('sha256').update(buf).digest('hex') };
}

// Minimal CSS walker (comments blanked): style rules with their enclosing at-rule chain and declarations.
function rulesOf(src) {
  src = src.replace(/\/\*[\s\S]*?\*\//g, m => m.replace(/[^\n]/g, ' '));
  const rules = [];
  const stack = [];
  let buf = '';
  let paren = 0;
  for (const ch of src) {
    if (ch === '(') paren++;
    if (ch === ')') paren = Math.max(0, paren - 1);
    if (paren === 0 && ch === '{') {
      const prelude = buf.replace(/\s+/g, ' ').trim();
      const node = { prelude, chain: stack.map(s => s.prelude), decls: [] };
      stack.push(node);
      if (!prelude.startsWith('@')) rules.push(node);
      buf = '';
    } else if (paren === 0 && ch === '}') {
      const top = stack.pop();
      if (top && buf.trim()) top.decls.push(buf.trim());
      buf = '';
    } else if (paren === 0 && ch === ';') {
      if (stack.length && buf.trim()) stack[stack.length - 1].decls.push(buf.trim());
      buf = '';
    } else buf += ch;
  }
  for (const r of rules) {
    r.media = r.chain.filter(c => c.startsWith('@media')).map(c => c.replace(/^@media\s*/, '')).join(' · ');
    r.decls = r.decls.filter(d => d.includes(':')).map(d => {
      const i = d.indexOf(':');
      return { name: d.slice(0, i).trim(), value: d.slice(i + 1).replace(/\s+/g, ' ').trim() };
    });
  }
  return rules;
}

const code = s => '`' + String(s).replace(/`/g, "'").replace(/\|/g, '\\|') + '`';
const cell = s => String(s).replace(/\|/g, '\\|');

function listLines(text) {
  return text.split('\n').map(raw => raw.trim()).filter(raw => raw && !raw.startsWith('#'));
}
const split = s => s.split('·').map(x => x.trim());

function sameInDark(inp) {
  const names = [];
  const f = [];
  for (const raw of listLines(inp.text)) {
    const parts = split(raw);
    if (parts[0] === 'f') f.push({ file: parts[1], selector: parts[2], property: parts[3], literal: parts[4], reason: parts.slice(5).join(' · ') });
    else names.push({ name: parts[0], reason: parts.slice(1).join(' · ') });
  }
  return { names, f };
}

const shaList = inputs => ['입력(sha256):', '', ...inputs.map(x => `- ${code(x.path)} ${code(x.sha)}`)].join('\n');

function tokensBlock(tokensIn, sidIn) {
  const rules = rulesOf(tokensIn.text);
  const light = new Map();
  const dark = new Map();
  const media = new Map();
  for (const r of rules) {
    const isRoot = r.prelude === ':root';
    const isDark = DARK_SEL.test(r.prelude);
    for (const d of r.decls) {
      if (!d.name.startsWith('--')) continue;
      if (isRoot && !r.media) light.set(d.name, d.value);
      else if (isDark && !r.media) dark.set(d.name, d.value);
      else if (isRoot || isDark) {
        const list = media.get(d.name) ?? [];
        list.push(`${isDark ? '다크 ' : ''}${r.media}: ${d.value}`);
        media.set(d.name, list);
      }
    }
  }
  const sid = sameInDark(sidIn);
  const exempt = new Set(sid.names.map(e => e.name));
  const darkCell = (name, value) => {
    if (dark.has(name)) return code(dark.get(name));
    if (exempt.has(name)) return '동일(면제)';
    if (/^var\(\s*--/.test(value)) return '별칭 따라감';
    if (COLOR_FAMILY.test(name)) return '**누락**';
    return '—';
  };
  const rows = [...light].map(([name, value]) =>
    `| ${code(name)} | ${code(value)} | ${darkCell(name, value)} | ${media.has(name) ? media.get(name).map(code).join('<br>') : ''} |`);
  const familyOf = name => CANON_FAMILIES.find(f => name.startsWith(`--${f}-`));
  const counts = CANON_FAMILIES.map(f => [f, [...light.keys()].filter(n => familyOf(n) === f).length]).filter(([, n]) => n);
  const other = [...light.keys()].filter(n => !familyOf(n));
  const darkOnly = [...dark.keys()].filter(n => !light.has(n));
  return [
    shaList([tokensIn, sidIn]),
    '',
    `라이트 \`:root\` 이름 ${light.size} · 다크 블록 이름 ${dark.size} · 폭 분기에서 다시 정의하는 이름 ${media.size} · 다크 동일 면제 ${exempt.size}${darkOnly.length ? ` · 다크에만 있는 이름 ${darkOnly.length}(${darkOnly.join(', ')})` : ''}`,
    '',
    '다크 칸: 값 = 다크 블록의 값 · 동일(면제) = `same-in-dark.txt` 에 사유와 함께 적힌 이름 · 별칭 따라감 = 라이트 값이 `var(--x)` 라 대상 이름의 다크 값을 따른다 · — = 색 계열이 아니라 다크 판정 대상이 아니다 · **누락** = 게이트 c red.',
    '',
    '| 이름 | 라이트 | 다크 | 폭 분기 |',
    '|---|---|---|---|',
    ...rows,
    '',
    '정본 계열 접두사(게이트 a 가 화면 범위 정의를 막는 이름 · c 는 그중 `--color-` `--fg-` `--bg-` `--accent-` `--shadow-`) — 라이트 이름 수:',
    '',
    '| 접두사 | 이름 수 |',
    '|---|---:|',
    ...counts.map(([f, n]) => `| ${code(`--${f}-`)} | ${n} |`),
    `| 계열 밖 | ${other.length} |`,
    '',
    `계열 밖 이름: ${other.map(code).join(' · ') || '없음'}`,
    '',
    `다크 동일 면제(\`same-in-dark.txt\` 이름 줄 ${exempt.size}):`,
    '',
    ...sid.names.map(e => `- ${code(e.name)} — ${cell(e.reason || '사유 없음')}`),
  ].join('\n');
}

function primitivesList(inp) {
  const families = [];
  let cur = null;
  for (const raw of inp.text.split('\n').map(s => s.trim())) {
    const fam = /^#\s*([a-z][a-z-]*)\s*$/.exec(raw);
    if (fam) { cur = { name: fam[1], classes: [] }; families.push(cur); continue; }
    if (raw.startsWith('.')) {
      if (!cur) { cur = { name: '(계열 없음)', classes: [] }; families.push(cur); }
      cur.classes.push(raw);
    }
  }
  return families;
}

// Class tokens of one selector-list argument, ignoring :not()/:has() arguments (they do not style the class).
function classTokens(arg) {
  let s = arg;
  for (;;) {
    const m = /:(not|has)\(/.exec(s);
    if (!m) break;
    let i = m.index + m[0].length;
    let depth = 1;
    while (i < s.length && depth) { if (s[i] === '(') depth++; else if (s[i] === ')') depth--; i++; }
    s = s.slice(0, m.index) + s.slice(i);
  }
  return [...s.matchAll(/\.([A-Za-z0-9_-]+)/g)].map(m => m[1]);
}
function splitArgs(prelude) {
  const out = [];
  let depth = 0;
  let buf = '';
  for (const ch of prelude) {
    if (ch === '(') depth++;
    if (ch === ')') depth--;
    if (ch === ',' && depth === 0) { out.push(buf.trim()); buf = ''; } else buf += ch;
  }
  if (buf.trim()) out.push(buf.trim());
  return out;
}

function primitivesBlock(cssIn, listIn, exemptIn, sidIn) {
  const rules = rulesOf(cssIn.text);
  const families = primitivesList(listIn);
  const matches = (cls, token) => (cls.endsWith('*') ? token.startsWith(cls.slice(1, -1)) : token === cls.slice(1));
  const tokensByRule = rules.map(r => new Set(splitArgs(r.prelude).flatMap(classTokens)));
  const ruleLabel = r => code(r.prelude) + (r.media ? ` · ${cell(r.media)}` : '');
  const classCount = families.reduce((n, x) => n + x.classes.length, 0);
  const classRows = [];
  const famRows = [];
  const claimed = new Set();
  let totalRules = 0;
  let totalDecls = 0;
  for (const fam of families) {
    const famRules = new Set();
    for (const cls of fam.classes) {
      const hit = rules.filter((r, i) => [...tokensByRule[i]].some(t => matches(cls, t)));
      hit.forEach(r => { famRules.add(r); claimed.add(r); });
      const decls = hit.reduce((n, r) => n + r.decls.length, 0);
      classRows.push(`| ${fam.name} | ${code(cls)} | ${hit.length || '정의 없음'} | ${hit.length ? decls : '—'} | ${hit.map(ruleLabel).join('<br>')} |`);
    }
    const decls = [...famRules].reduce((n, r) => n + r.decls.length, 0);
    totalRules += famRules.size;
    totalDecls += decls;
    famRows.push(`| ${fam.name} | ${fam.classes.length} | ${famRules.size} | ${decls} |`);
  }
  const unclaimed = rules.filter(r => !claimed.has(r));
  const exempt = listLines(exemptIn.text).map(split);
  const f = sameInDark(sidIn).f;
  return [
    shaList([cssIn, listIn, exemptIn, sidIn]),
    '',
    `목록 클래스 ${classCount}(계열 ${families.length}) · \`primitives.css\` 규칙 ${rules.length} · 선언 ${rules.reduce((n, r) => n + r.decls.length, 0)}`,
    '',
    '| 계열 | 목록 클래스 | 규칙 | 기본값 선언 |',
    '|---|---:|---:|---:|',
    ...famRows,
    `| **계** | ${classCount} | ${totalRules} | ${totalDecls} |`,
    '',
    '규칙 = 그 클래스가 `:not()`·`:has()` 인자 밖에 나오는 `primitives.css` 규칙(폭 분기 포함). 한 규칙이 두 클래스에 걸리면(`:is(.inp, .sel)`) 아래 표의 두 행에 모두 세고, 계열 합계는 한 번만 센다. 「정의 없음」 = 목록에는 있어 화면 파일의 맨 정의가 막히지만 기본값이 없다.',
    '',
    '| 계열 | 클래스 | 규칙 | 선언 | 선택자 |',
    '|---|---|---:|---:|---|',
    ...classRows,
    '',
    `목록 클래스에 걸리지 않는 \`primitives.css\` 규칙: ${unclaimed.map(ruleLabel).join(' · ') || '없음'}`,
    '',
    `프리미티브 맨 정의 면제(\`primitives-exempt.txt\` · 게이트 e): ${exempt.length}${exempt.length ? '' : ' — 없음'}`,
    ...(exempt.length ? [''] : []),
    ...exempt.map(p => `- ${code(p[0] ?? '')} ${code(p[1] ?? '')} — ${cell(p.slice(2).join(' · ') || '사유 없음')}`),
    '',
    `색 리터럴 면제(\`same-in-dark.txt\` 의 \`f\` 줄 · 게이트 f): ${f.length}${f.length ? '' : ' — 없음'}`,
    ...(f.length ? [''] : []),
    ...f.map(x => `- ${code(x.file)} ${code(x.selector)} ${code(`${x.property}: ${x.literal}`)} — ${cell(x.reason || '사유 없음')}`),
  ].join('\n');
}

function blockRange(doc, name) {
  const open = `<!-- generated:${name} -->`;
  const close = `<!-- /generated:${name} -->`;
  const count = s => doc.split(s).length - 1;
  if (count(open) !== 1 || count(close) !== 1) notReady(`표지 짝 부재·중복: ${open} ×${count(open)} · ${close} ×${count(close)}`);
  const start = doc.indexOf(open) + open.length;
  const end = doc.indexOf(close);
  if (end < start) notReady(`닫힘 표지가 여는 표지보다 앞에 있다: ${name}`);
  return { start, end };
}

function main() {
  const opt = args(process.argv.slice(2));
  if (!existsSync(abs(opt.doc))) notReady(`문서 부재: ${opt.doc}`);
  const tokensIn = input('토큰 정본', opt.tokens);
  const cssIn = input('프리미티브 CSS', opt.primitivesCss);
  const listIn = input('프리미티브 목록', opt.primitives);
  const exemptIn = input('프리미티브 면제 목록', opt.primitivesExempt);
  const sidIn = input('다크 동일·색 리터럴 면제 목록', opt.sameInDark);
  let doc = readFileSync(abs(opt.doc), 'utf8');
  const want = {
    tokens: tokensBlock(tokensIn, sidIn),
    primitives: primitivesBlock(cssIn, listIn, exemptIn, sidIn),
  };
  for (const name of Object.keys(want)) blockRange(doc, name); // both marker pairs must exist before anything is judged
  let drift = 0;
  for (const [name, body] of Object.entries(want)) {
    const { start, end } = blockRange(doc, name);
    const next = `\n${body}\n`;
    const have = doc.slice(start, end);
    if (have === next) { console.log(`h ${name} 같음`); continue; }
    drift++;
    if (opt.check) {
      const a = have.split('\n');
      const b = next.split('\n');
      let i = 0;
      while (i < Math.max(a.length, b.length) && a[i] === b[i]) i++;
      console.log(`h ${name} 갈림 — 블록 ${i}번째 줄부터 다르다`);
      console.log(`  문서: ${a[i] ?? '(없음)'}`);
      console.log(`  실물: ${b[i] ?? '(없음)'}`);
    } else {
      doc = doc.slice(0, start) + next + doc.slice(end);
      console.log(`h ${name} 다시 씀`);
    }
  }
  if (!opt.check && drift) writeFileSync(abs(opt.doc), doc);
  const h = opt.check ? drift : 0;
  console.log(`문서 표 갈림 ${h}`);
  console.log(`design-docs-counts blocks=${Object.keys(want).length} h=${h} written=${opt.check ? 0 : drift}`);
  if (h) console.log('고치는 법: node frontend/scripts/design-docs.mjs 로 두 블록을 다시 쓰고 커밋한다(블록 밖 손글은 그대로).');
  process.exit(h ? 1 : 0);
}

main();
