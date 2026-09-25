// Compile the actual wire schema with the same pinned AJV as event contracts.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const {resolve} = require('node:path');
const root = resolve(__dirname, '../..');
const Ajv = require('../../gates/tools/node/node_modules/ajv/dist/2020');
const formats = require('../../gates/tools/node/node_modules/ajv-formats');
// Resolve only repository-local references; no network or runtime dependency added.
const schema = JSON.parse(execFileSync(resolve(root, 'services/core-api/.venv/bin/python'), ['-c', `
import json, pathlib, yaml
root=pathlib.Path.cwd().resolve()
def expand(value, path):
    if isinstance(value,list): return [expand(v,path) for v in value]
    if not isinstance(value,dict): return value
    if '$ref' in value:
        file, pointer=value['$ref'].split('#',1)
        target=(path.parent/file).resolve() if file else path
        if not target.is_relative_to(root/'contracts'): raise ValueError('external reference')
        node=yaml.safe_load(target.read_text())
        for key in pointer.lstrip('/').split('/'):
            node=node[key.replace('~1','/').replace('~0','~')]
        return expand(node,target)
    return {k:expand(v,path) for k,v in value.items()}
path=root/'contracts/schemas/knowledge-lifecycle.json'
print(json.dumps(expand(json.loads(path.read_text()),path)))
`], {cwd: root, encoding:'utf8'}));
const ajv = new Ajv({strict:true, allErrors:true});
formats(ajv);

test('deletion requires only a proven deleted revision and generation, never source bytes or ontology', () => {
  const validate = ajv.compile(schema.$defs.InvalidateCommand);
  const command = {protocol:'knowledge-lifecycle/1',grant:'deletion-proof',
    source_key:{lab_id:'1'.repeat(26),dataset_id:'2'.repeat(26),source_kind:'evidence',source_id:'3'.repeat(26)},
    source_version:{revision:2,deleted:true},processing_version:{generation:2},reason:'deleted'};
  assert.equal(validate(command),true,JSON.stringify(validate.errors));
  for (const change of [{source_version:{revision:2,deleted:false}},
    {source_version:{revision:2,deleted:true,digest:'a'.repeat(64)}},
    {processing_version:{generation:2,ontology_release:'a'.repeat(64)}},
    {reason:'access_revoked'}]) {
    assert.equal(validate({...command,...change}),false);
  }
});

test('mapping IDs are representable by ontology manifest keys', () => {
  const validate = ajv.compile(schema.$defs.Mapping);
  const mapping = {fact_id:'3'.repeat(26), concept_id:'a'.repeat(60), basis:{mapping_rule_id:'rule-v1'}};
  assert.equal(validate(mapping), true, JSON.stringify(validate.errors));
  for (const concept_id of ['a'.repeat(61), 'NOT A CONCEPT']) {
    assert.equal(validate({...mapping, concept_id}), false);
  }
});

test('fact schema rejects invented predicates and incompatible values', () => {
  const validate = ajv.compile(schema.$defs.Evidence);
  const fact = {fact_id:'3'.repeat(26), predicate:'nativeResolutionM', value:100,
    source_locator:'file#/resolution', source_version:{revision:1,digest:'a'.repeat(64),deleted:false},
    evidence_kind:'file_measurement'};
  assert.equal(validate(fact), true, JSON.stringify(validate.errors));
  for (const change of [{predicate:'invented'}, {value:-1}, {value:'100'}, {extra:true}]) {
    assert.equal(validate({...fact,...change}), false);
  }
});
