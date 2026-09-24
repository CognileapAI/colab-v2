#!/usr/bin/env node
// P2a ⓐ — layer wrapping count (zero-dependency). Run from frontend/.
// Every CSS under src/ except layers.css must be one `@layer <name> { … }` block from first to last
// non-comment character (tokens.css → tokens, the rest → screens); rules outside any layer = 0;
// shell/design-system.css absent; `.colab-ui` selectors only in the first rules of shell.css.
// Exit 0 green · 1 red · 78 no CSS found.
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
import { join, sep } from 'node:path';
import { parseCss } from './cascade-map.mjs';

const walk = (d) => readdirSync(d).flatMap((n) => { const p = join(d, n); return statSync(p).isDirectory() ? walk(p) : [p]; });
const files = walk('src').filter((p) => p.endsWith('.css')).map((p) => p.split(sep).join('/')).sort();
if (!files.length) { console.log('layer-count readiness: CSS 0건'); process.exit(78); }
const red = [];
let wrapped = 0; let unlayered = 0; let rules = 0;
for (const f of files) {
  const raw = readFileSync(f, 'utf8');
  if (f === 'src/shell/layers.css') {
    if (raw.trim() !== '@layer tokens, base, primitives, patterns, screens;') red.push(`${f}: 층 선언 문장이 다르다`);
    continue;
  }
  // P2b — base.css → base · primitives.css → primitives.
  const want = { 'src/shell/tokens.css': 'tokens', 'src/shell/base.css': 'base', 'src/shell/primitives.css': 'primitives' }[f] || 'screens';
  const t = raw.replace(/\/\*[\s\S]*?\*\//g, '').trim();
  if (!t.startsWith(`@layer ${want} {`) || !t.endsWith('}')) red.push(`${f}: @layer ${want} { … } 로 시작·끝나지 않는다`);
  else wrapped++;
  const { rules: rs, stats } = parseCss(raw, f);
  rules += rs.length;
  unlayered += stats.unlayeredRules;
  if (stats.unlayeredRules) red.push(`${f}: 층 밖 규칙 ${stats.unlayeredRules}`);
  if (stats.imports) red.push(`${f}: @import ${stats.imports}`);
  const colab = rs.filter((r) => /\.colab-ui\b/.test(r.selectorText));
  if (f === 'src/shell/shell.css') {
    const idx = colab.map((r) => rs.indexOf(r));
    if (colab.length !== 4 || idx.some((x, i) => x !== i)) red.push(`${f}: .colab-ui 규칙이 맨 앞 4개가 아니다(${idx.join(',')})`);
  } else if (colab.length) red.push(`${f}: .colab-ui 규칙 ${colab.length}`);
}
if (existsSync('src/shell/design-system.css')) red.push('src/shell/design-system.css 가 남아 있다');
for (const r of red) console.log(`  red: ${r}`);
console.log(`layer-count files=${files.length} wrapped=${wrapped} rules=${rules} unlayered=${unlayered} design_system=${existsSync('src/shell/design-system.css') ? 1 : 0} red=${red.length}`);
process.exit(red.length ? 1 : 0);
