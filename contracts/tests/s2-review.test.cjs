// 실제 OpenAPI를 요청 검증기로 소비한다. 임의로 재작성한 스키마는 시험하지 않는다.
const assert = require('node:assert/strict');
const { test } = require('node:test');
const { execFileSync } = require('node:child_process');
const { readFileSync } = require('node:fs');
const path = require('node:path');
const Ajv = require('../../gates/tools/node/node_modules/ajv/dist/2020').default;
const root = path.resolve(__dirname, '../..');
const spec = JSON.parse(execFileSync(path.join(root, 'gates/.venv/bin/python'), [
  '-c', 'import json,sys,yaml; print(json.dumps(yaml.safe_load(open(sys.argv[1]))))',
  path.join(root, 'contracts/seams/core-viz.yaml'),
], { encoding: 'utf8' }));
const schemaId = 'https://contract.test/seams/core-viz.yaml';
const ajv = new Ajv({ strict: false, validateFormats: false });
ajv.addSchema(JSON.parse(readFileSync(path.join(root, 'contracts/schemas/common.json'))),
  'https://contract.test/schemas/common.json');
ajv.addSchema(spec, schemaId);
const validateScreenshot = ajv.compile({ $ref: schemaId + '#/components/schemas/ScreenshotRequest' });

test('실제 스크린샷 요청 계약은 1/8층을 받고 0/9층을 거절한다', () => {
  for (const [count, expected] of [[1, true], [8, true], [0, false], [9, false]]) {
    const request = {
      layers: Array.from({ length: count }, () => ({ renderId: '01JQ0000000000000000000001' })),
      viewport: { width: 512, height: 512, bounds: { west: 124, south: 31, east: 128, north: 34 } },
    };
    assert.equal(validateScreenshot(request), expected, `${count} layers: ${JSON.stringify(validateScreenshot.errors)}`);
  }
});

for (const [route, method] of [['/renders', 'post'], ['/renders/{renderId}', 'get'],
  ['/screenshots', 'post'], ['/value-lookups', 'post'], ['/target-descriptions', 'post']]) {
  test(`${method} ${route}: 연구실·계정 없는 요청은 계약에서 거절된다`, () => {
    const operation = spec.paths[route][method];
    const headers = [...(spec.paths[route].parameters || []), ...(operation.parameters || [])]
      .map(p => p.$ref ? spec.components.parameters[p.$ref.split('/').at(-1)] : p)
      .filter(p => p.in === 'header');
    const validate = ajv.compile({ type: 'object',
      properties: Object.fromEntries(headers.map(p => [p.name, p.schema.$ref
        ? { $ref: new URL(p.schema.$ref, schemaId).href } : p.schema])),
      required: headers.filter(p => p.required).map(p => p.name),
    });
    assert.equal(validate({ 'X-CoLAB-Lab': '01JQ0000000000000000000001',
      'X-CoLAB-Account': '01JQ0000000000000000000002' }), true);
    assert.equal(validate({ 'X-CoLAB-Account': '01JQ0000000000000000000002' }), false);
    assert.equal(validate({ 'X-CoLAB-Lab': '01JQ0000000000000000000001' }), false);
    for (const account of ['', '   ']) {
      assert.equal(validate({ 'X-CoLAB-Lab': '01JQ0000000000000000000001',
        'X-CoLAB-Account': account }), false);
    }
    assert.ok(operation.responses['400'], '경계 누락의 실제 400 응답을 계약 소비자가 알 수 있어야 한다');
  });
}
