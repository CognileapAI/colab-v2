"""Emit strict knowledge DTOs from the internal contract and existing fact types.

Only the schema constructs used by this contract are supported. No runtime schema
engine or cross-service imports; generated modules work in isolated images.
"""
import json
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[2]
if sys.argv[1] == '--ids':
    source = (ROOT / 'services/core-api/src/colab_core/kernel/ids.py').read_text()
    Path(sys.argv[2]).write_text('# Auto-generated from core kernel ids; do not edit.\n' + source +
        '\n\ndef is_valid_ulid(value: object) -> bool:\n    return Ulid.is_valid(value)\n')
    raise SystemExit(0)
schema = json.loads((ROOT / 'contracts/schemas/knowledge-lifecycle.json').read_text())
common = json.loads((ROOT / 'contracts/schemas/common.json').read_text())
seam = yaml.safe_load((ROOT / 'contracts/seams/fe-core.yaml').read_text())
definitions = schema['$defs']
facts = seam['components']['schemas']['SearchEvidenceFacts']['properties']
ontology = yaml.safe_load((ROOT / 'contracts/seams/core-ai.yaml').read_text())
manifest_key = ontology['components']['schemas']['OntologyManifest']['properties']['entries']['propertyNames']
concept = definitions['ConceptId']
assert concept['maxLength'] + len('concept:') == manifest_key['maxLength'], 'concept identifier length drift'
assert '^(discovery|concept:' + concept['pattern'][1:-1] + ')$' == manifest_key['pattern'], 'concept identifier grammar drift'
lines = ['"""Auto-generated knowledge boundary values; do not edit. Not authentication."""',
         'from __future__ import annotations', 'from datetime import date',
         'import hashlib', 'import json', 'import re',
         'from typing import Annotated, Literal, Protocol',
         'from pydantic import BaseModel, ConfigDict, Field, model_validator',
         'from .ontology_wire import KEY_PATTERN', '',
         'class WireValue(BaseModel):',
         '    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False, hide_input_in_errors=True)', '']


def type_expr(node, name):
    if '$ref' in node:
        ref = node['$ref']
        if ref.startswith('common.json#/$defs/'):
            return type_expr(common['$defs'][ref.rsplit('/', 1)[1]], name)
        if ref.startswith('../seams/core-ai.yaml#'):
            target = ontology
            for part in ref.split('#/', 1)[1].split('/'):
                target = target[part]
            return type_expr({'type': 'string', **target}, name)
        return ref.rsplit('/', 1)[1]
    if 'oneOf' in node:
        return ' | '.join(type_expr(item, name) for item in node['oneOf'])
    if 'const' in node:
        return f'Literal[{node["const"]!r}]'
    if 'enum' in node:
        return 'Literal[' + ', '.join(repr(item) for item in node['enum']) + ']'
    kind = node['type']
    if kind == 'object':
        emit_model(name, node)
        return name
    base = {'string': 'str', 'integer': 'int', 'number': 'float', 'boolean': 'bool', 'array': 'list' }[kind]
    if kind == 'array':
        base = f'list[{type_expr(node["items"], name + "Item")}]'
    fields = {'minLength': 'min_length', 'maxLength': 'max_length', 'minimum': 'ge',
              'exclusiveMinimum': 'gt', 'minItems': 'min_length', 'maxItems': 'max_length', 'pattern': 'pattern'}
    constraints = [f'{target}={node[key]!r}' for key, target in fields.items() if key in node]
    return f'Annotated[{base}, Field({", ".join(constraints)})]' if constraints else base


def emit_model(name, node):
    assert node['additionalProperties'] is False
    assert set(node['required']) == set(node['properties']), f'optional fields unsupported: {name}'
    fields = []
    for key, value in node['properties'].items():
        expr = type_expr(value, name + key.title())
        suffix = ' = Field(repr=False)' if key == 'grant' else ''
        fields.append(f'    {key}: {expr}{suffix}')
    lines.extend([f'class {name}(WireValue):', *fields])
    if name == 'DeletedSourceVersion':
        lines.extend(['', '    @model_validator(mode="before")', '    @classmethod',
                     '    def strict_deleted(cls, value):',
                     '        if isinstance(value, dict) and value.get("deleted") is not True:',
                     '            raise ValueError("explicit deleted boolean required")', '        return value'])
    if name == 'Mapping':
        lines.extend(['', '    @model_validator(mode="after")',
                     '    def concept_key(self):',
                     '        if re.fullmatch(KEY_PATTERN, "concept:" + self.concept_id) is None:',
                     '            raise ValueError("invalid concept identifier")', '        return self'])
    if name.endswith('PeriodValue'):
        lines.extend(['', '    @model_validator(mode="after")', '    def ordered(self):',
                     '        start, end = date.fromisoformat(self.start), date.fromisoformat(self.end)',
                     '        if str(start) != self.start or str(end) != self.end or end < start:',
                     '            raise ValueError("invalid evidence period")', '        return self'])
    if name == 'EvidenceRoles':
        lines.extend(['', '    @model_validator(mode="after")', '    def unique_roles(self):',
                     '        if len(set(self.value)) != len(self.value):',
                     '            raise ValueError("duplicate evidence roles")', '        return self'])
    if name in {'ReplaceCommand', 'KnowledgePayload'}:
        lines.extend(['', '    @model_validator(mode="after")', '    def coherent(self):',
                     '        ids = {fact.fact_id for fact in self.facts}',
                     '        if self.source_version.deleted or len(ids) != len(self.facts):',
                     '            raise ValueError("deleted source or duplicate fact")',
                     '        if any(fact.source_version != self.source_version for fact in self.facts):',
                     '            raise ValueError("fact source version mismatch")',
                     '        if any(mapping.fact_id not in ids for mapping in self.mappings):',
                     '            raise ValueError("mapping references missing fact")',
                     '        keys = [(m.fact_id, m.concept_id) for m in self.mappings]',
                     '        if len(set(keys)) != len(keys):',
                     '            raise ValueError("duplicate mapping")', '        return self'])
    if name == 'AuthorizedKnowledge':
        lines.extend(['', '    @model_validator(mode="after")', '    def coherent(self):',
                     '        if self.receipt.status != "replaced":',
                     '            raise ValueError("knowledge unavailable")',
                     '        for field in ("protocol", "source_key", "source_version", "processing_version"):',
                     '            if getattr(self.payload, field) != getattr(self.receipt, field):',
                     '                raise ValueError("knowledge mismatch")',
                     '        if payload_digest(self.payload) != self.receipt.payload_digest:',
                     '            raise ValueError("knowledge digest mismatch")', '        return self'])
    lines.append('')


for name, node in definitions.items():
    if name == 'Evidence':
        names = []
        for option in node['oneOf']:
            predicate = option['properties']['predicate']['const']
            ref = option['properties']['value']['$ref']
            assert ref == '../seams/fe-core.yaml#/components/schemas/SearchEvidenceFacts/properties/' + predicate
            value = facts[predicate]
            model_name = 'Evidence' + predicate[0].upper() + predicate[1:]
            names.append(model_name)
            variant = {**node, 'properties': {**node['properties'],
                       'predicate': {'const': predicate}, 'value': value}}
            emit_model(model_name, variant)
        lines.extend(['Evidence = Annotated[' + ' | '.join(names) + ', Field(discriminator="predicate")]', ''])
    elif node.get('type') == 'object':
        emit_model(name, node)
    else:
        lines.extend([f'{name} = {type_expr(node, name)}', ''])

lines.extend(['''
def payload_digest(command: ReplaceCommand | InvalidateCommand | KnowledgePayload) -> str:
    """Canonical wire digest excludes the secret grant; it is NOT authentication.

    Lists retain their order. Retry producers must preserve the exact ordered
    payload. The authority binds this digest to source/processing/principal.
    """
    body = command.model_dump(mode="json", exclude={"grant"})
    return hashlib.sha256(json.dumps(body, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()


class KnowledgeWriter(Protocol):
    def replace(self, command: ReplaceCommand) -> KnowledgeReceipt: ...
    def invalidate(self, command: InvalidateCommand) -> InvalidationReceipt: ...
'''])
Path(sys.argv[1]).write_text('\n'.join(lines) + '\n')
