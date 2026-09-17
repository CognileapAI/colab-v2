"""Wire-boundary failures, not authentication/endpoint acceptance tests."""
import importlib
import importlib.util
from copy import deepcopy

import pytest


def wire():
    name = 'colab_ai.kernel.knowledge_wire'
    assert importlib.util.find_spec(name) is not None, 'knowledge wire consumer is missing'
    return importlib.import_module(name)


def command():
    return {
        'protocol': 'knowledge-lifecycle/1', 'grant': 'opaque-grant-handle',
        'source_key': {'lab_id': '0' * 26, 'dataset_id': '1' * 26,
                       'source_kind': 'file', 'source_id': '2' * 26},
        'source_version': {'revision': 1, 'digest': 'a' * 64, 'deleted': False},
        'processing_version': {'generation': 1, 'extractor_version': 'structured-v1',
                               'mapping_version': 'rules-v1', 'ontology_release': 'b' * 64},
        'facts': [{'fact_id': '3' * 26, 'predicate': 'nativeResolutionM', 'value': 100,
                   'source_locator': 'file#/resolution', 'evidence_kind': 'file_measurement',
                   'source_version': {'revision': 1, 'digest': 'a' * 64, 'deleted': False}}],
        'mappings': [{'fact_id': '3' * 26, 'concept_id': 'ndvi',
                      'basis': {'mapping_rule_id': 'native-resolution-v1'}}],
        'dependencies': [{'owner': 'D5', 'resource_id': '2' * 26, 'revision': 1}],
    }


def test_valid_replace_round_trips_without_invented_defaults():
    body = command()
    assert wire().ReplaceCommand.model_validate(body).model_dump() == body


def test_reader_payload_is_typed_and_has_no_grant():
    module = wire()
    body = command()
    body.pop('grant')
    payload = module.KnowledgePayload.model_validate(body)
    assert module.payload_digest(payload) == module.payload_digest(module.ReplaceCommand.model_validate(command()))
    with pytest.raises(ValueError):
        module.KnowledgePayload.model_validate(command())
    body['facts'][0]['source_version']['revision'] = 2
    with pytest.raises(ValueError):
        module.KnowledgePayload.model_validate(body)


def test_reader_request_accepts_only_source_and_expected_receipt():
    module = wire()
    body = {'source_key': command()['source_key'], 'expected_receipt_id': '4' * 26}
    assert module.KnowledgeReadRequest.model_validate(body).model_dump() == body
    for extra in ('principal', 'grant', 'authority_url', 'facts'):
        with pytest.raises(ValueError):
            module.KnowledgeReadRequest.model_validate({**body, extra: {}})


def test_mapping_identifier_fits_ontology_manifest_key():
    body = command()
    body['mappings'][0]['concept_id'] = 'a' * 60
    assert wire().ReplaceCommand.model_validate(body).mappings[0].concept_id == 'a' * 60
    for identifier in ('a' * 61, 'NOT A CONCEPT'):
        body['mappings'][0]['concept_id'] = identifier
        with pytest.raises(ValueError):
            wire().ReplaceCommand.model_validate(body)


def test_payload_digest_binds_content_but_not_rotating_grant():
    module = wire()
    first = module.ReplaceCommand.model_validate(command())
    rotated = module.ReplaceCommand.model_validate({**command(), 'grant': 'renewed-grant'})
    assert module.payload_digest(first) == module.payload_digest(rotated)
    changed = command()
    changed['facts'][0]['value'] = 200
    assert module.payload_digest(first) != module.payload_digest(module.ReplaceCommand.model_validate(changed))


@pytest.mark.parametrize('path,value', [
    (('protocol',), 'knowledge-lifecycle/2'),
    (('authority_url',), 'https://untrusted.example'),
    (('source_key', 'lab_id'), 'not-an-id'),
    (('source_version', 'revision'), 0),
    (('source_version', 'revision'), True),
    (('processing_version', 'generation'), '1'),
    (('processing_version', 'ontology_release'), 'old-release'),
    (('facts', 0, 'predicate'), 'arbitrary_assertion'),
    (('facts', 0, 'value'), -1),
    (('facts', 0, 'value'), float('nan')),
    (('facts', 0, 'value'), True),
    (('facts', 0, 'extra'), 'secret'),
    (('facts', 0, 'source_version', 'revision'), 2),
    (('mappings', 0, 'fact_id'), '5' * 26),
    (('mappings', 0, 'concept_id'), 'NOT A CONCEPT'),
    (('mappings', 0, 'basis'), {'confidence': '확실'}),
    (('mappings', 0, 'basis'), {'mapping_rule_id': 'rule', 'review_id': '6' * 26}),
    (('facts',), []),
])
def test_malformed_or_inconsistent_replace_is_rejected(path, value):
    module = wire()
    body = command()
    parent = body
    for key in path[:-1]:
        parent = parent[key]
    parent[path[-1]] = value
    with pytest.raises(ValueError):
        module.ReplaceCommand.model_validate(body)


@pytest.mark.parametrize('field', ['facts', 'mappings', 'dependencies'])
def test_unbounded_payload_is_rejected(field):
    module = wire()
    body = command()
    body[field] = [deepcopy(body[field][0]) for _ in range(1001)]
    with pytest.raises(ValueError):
        module.ReplaceCommand.model_validate(body)


def test_receipt_requires_d9_issuer_and_positive_sequence():
    module = wire()
    body = command()
    receipt = {key: body[key] for key in ('protocol', 'source_key', 'source_version', 'processing_version')}
    receipt.update(receipt_id='7' * 26, issuer='D9', publication_sequence=1,
                   payload_digest='c' * 64, status='replaced')
    assert module.KnowledgeReceipt.model_validate(receipt).issuer == 'D9'
    for change in ({'issuer': 'D10'}, {'publication_sequence': 0}, {'payload_digest': 'fake'}):
        with pytest.raises(ValueError):
            module.KnowledgeReceipt.model_validate({**receipt, **change})


def test_mapping_cannot_claim_two_approval_bases():
    module = wire()
    body = command()
    body['mappings'][0]['basis'] = {'review_id': '6' * 26}
    assert module.ReplaceCommand.model_validate(body).mappings[0].basis.review_id == '6' * 26


def test_period_order_and_unique_roles_are_checked():
    module = wire()
    for predicate, value in [('period', {'start': '2026-02-01', 'end': '2026-01-01'}),
                             ('period', {'start': '2026-02-30', 'end': '2026-03-01'}),
                             ('roles', ['prediction', 'prediction'])]:
        body = command()
        body['facts'][0].update(predicate=predicate, value=value)
        with pytest.raises(ValueError):
            module.ReplaceCommand.model_validate(body)


def test_grant_is_not_exposed_in_repr_or_validation_message():
    module = wire()
    body = command()
    parsed = module.ReplaceCommand.model_validate(body)
    assert body['grant'] not in repr(parsed)
    with pytest.raises(ValueError) as error:
        module.ReplaceCommand.model_validate({**body, 'facts': []})
    assert body['grant'] not in str(error.value)


def test_ontology_dependencies_use_manifest_keys_and_content_digests():
    module = wire()
    body = command()
    body['dependencies'] = [{'owner': 'D9', 'resource_id': 'concept:ndvi', 'revision': 'a' * 64}]
    assert module.ReplaceCommand.model_validate(body).dependencies[0].resource_id == 'concept:ndvi'
    for change in ({'resource_id': 'unknown:key'}, {'revision': 1}, {'owner': 'D3'}):
        body['dependencies'] = [{**body['dependencies'][0], **change}]
        with pytest.raises(ValueError):
            module.ReplaceCommand.model_validate(body)
