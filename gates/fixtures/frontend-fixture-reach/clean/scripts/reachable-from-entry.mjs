// 운영 진입점(`src/main.tsx`)에서 **실제로 닿는** 모듈을 세어 낸다.
//
// 왜 있는가 — 「픽스처는 시험에서만 쓴다」는 주석으로는 증명되지 않는다. 상대 경로 import 를
// 따라가 닿는 파일 목록을 만들고, 그 안에 픽스처가 있으면 실패로 말한다
// (`CODE-REVIEW-20260903` 9 — 픽스처 폴백 제거의 회귀 방지).
//
// 쓰는 법 — `node scripts/reachable-from-entry.mjs [entry]`. 닿는 모듈 수를 찍고, 금지 목록에
// 하나라도 닿으면 rc=1 로 끝난다. `entry` 는 **cwd 기준 상대경로**(생략 시 `src/main.tsx`) —
// 루트는 이 스크립트를 부르는 쪽이 `cwd` 로 정한다(게이트 셀프테스트가 픽스처 트리를 이 인자로 먹인다).
import { readFileSync, existsSync } from 'node:fs';
import { dirname, resolve } from 'node:path';

const ENTRY = process.argv[2] || 'src/main.tsx';
/** 운영 경로에 있어서는 안 되는 모듈 (경로 조각으로 판정한다). */
const FORBIDDEN = ['/fixture.ts', '/graphFixture.ts', '/localEngine.ts'];
const EXTS = ['', '.ts', '.tsx', '.js', '.jsx', '/index.ts', '/index.tsx'];

function resolveSpecifier(fromFile, spec) {
  if (!spec.startsWith('.')) return null; // 패키지는 따라가지 않는다
  const base = resolve(dirname(fromFile), spec);
  for (const ext of EXTS) {
    const candidate = base + ext;
    if (existsSync(candidate) && !candidate.endsWith('/')) return candidate;
  }
  return null;
}

const seen = new Set();
const queue = [resolve(ENTRY)];
while (queue.length) {
  const file = queue.pop();
  if (seen.has(file)) continue;
  seen.add(file);
  if (!/\.(ts|tsx|js|jsx)$/.test(file)) continue;
  const src = readFileSync(file, 'utf8');
  // `import ... from '…'` · `export ... from '…'` · `import('…')`
  const specs = [...src.matchAll(/(?:from|import)\s*\(?\s*['"]([^'"]+)['"]/g)].map((m) => m[1]);
  for (const spec of specs) {
    const target = resolveSpecifier(file, spec);
    if (target) queue.push(target);
  }
}

const root = resolve('.') + '/';
const reached = [...seen].map((f) => f.replace(root, '')).sort();
const hits = reached.filter((f) => FORBIDDEN.some((bad) => ('/' + f).includes(bad)));

console.log(`entry=${ENTRY} reached=${reached.length}`);
if (hits.length) {
  console.error('운영 경로가 픽스처에 닿는다:');
  for (const h of hits) console.error(`  ${h}`);
  process.exit(1);
}
console.log('금지 모듈에 닿지 않는다: ' + FORBIDDEN.join(' · '));
