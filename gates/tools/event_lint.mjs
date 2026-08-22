// event-lint 게이트의 검사 엔진 (WU-D2b).
//
// 한 프로세스 안에서 두 겹을 다 본다 — 파일마다 ajv 를 새로 띄우면 게이트가 분 단위로 느려지고,
// 느린 게이트는 사람이 끄고 싶어지는 게이트다.
//   ① 스키마 유효성 — events/*.json 이 그 자체로 유효한 JSON Schema 2020-12 인가 (컴파일)
//   ② 인스턴스 검증 — valid 픽스처는 통과, invalid 픽스처는 **거부**되는가
//      ②가 없으면 "컴파일은 되는데 ../schemas/common.json $ref 가 실제로는 안 풀리는" 상태를 못 잡는다.
//
// strict 모드를 켜 둔다 — 오탈자 키워드(`requred`)가 조용히 무시되는 것을 막는다.
// 사용: node event_lint.mjs <common.json> <eventsDir> <fixturesRoot> <nodeToolDir>
// <nodeToolDir> = ajv 를 설치해 둔 곳(gates/tools/node). 도구 위치를 인자로 받아야
// selftest 가 "도구 부재" 케이스를 주입할 수 있다.
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

const [commonPath, eventsDir, fixRoot, nodeToolDir] = process.argv.slice(2);
if (!commonPath || !eventsDir || !fixRoot || !nodeToolDir) {
  console.error("usage: event_lint.mjs <common.json> <eventsDir> <fixturesRoot> <nodeToolDir>");
  process.exit(2);
}
const require = createRequire(path.join(path.resolve(nodeToolDir), "package.json"));
const Ajv2020 = require("ajv/dist/2020");
const addFormats = require("ajv-formats");

const rd = (p) => JSON.parse(fs.readFileSync(p, "utf8"));
const jsons = (d) =>
  (fs.existsSync(d) ? fs.readdirSync(d) : []).filter((f) => f.endsWith(".json")).sort()
    .map((f) => path.join(d, f));

let failed = false;
const fail = (msg) => { console.log(`::error::${msg}`); failed = true; };

const schemaFiles = jsons(eventsDir);

// ── ① 스키마 유효성 — 대상마다 나머지를 참조로 붙여 컴파일한다 ────────────────
for (const s of schemaFiles) {
  const ajv = new Ajv2020({ strict: true, allErrors: true, validateFormats: true });
  addFormats(ajv);
  try {
    ajv.addSchema(rd(commonPath));
    for (const o of schemaFiles) if (o !== s) ajv.addSchema(rd(o));
    ajv.compile(rd(s));           // $ref 가 끊겨 있으면 여기서 던진다
    console.log(`  compile OK — ${s}`);
  } catch (e) {
    console.log(`      ${e.message}`);
    fail(`스키마가 유효한 JSON Schema 2020-12 가 아니다: ${s}`);
  }
}

// ── ② 인스턴스 검증 ──────────────────────────────────────────────────────────
const ajv = new Ajv2020({ strict: true, allErrors: true, validateFormats: true });
addFormats(ajv);
let validate;
try {
  ajv.addSchema(rd(commonPath));
  for (const o of schemaFiles) ajv.addSchema(rd(o));
  validate = ajv.compile(rd(path.join(fixRoot, "entry.schema.json")));
} catch (e) {
  fail(`픽스처 진입 스키마를 컴파일하지 못했다: ${e.message}`);
  process.exit(1);
}

for (const d of jsons(path.join(fixRoot, "valid"))) {
  if (validate(rd(d))) console.log(`  valid   OK — ${d}`);
  else {
    console.log(ajv.errorsText(validate.errors, { separator: "\n      " }).replace(/^/, "      "));
    fail(`계약을 지킨 인스턴스가 거부됐다: ${d}`);
  }
}
for (const d of jsons(path.join(fixRoot, "invalid"))) {
  if (validate(rd(d))) fail(`계약을 어긴 인스턴스가 통과했다 (fail-open): ${d}`);
  else console.log(`  invalid 거부 OK — ${d}`);
}

process.exit(failed ? 1 : 0);
