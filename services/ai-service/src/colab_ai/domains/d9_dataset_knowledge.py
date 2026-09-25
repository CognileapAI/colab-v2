"""Atomic scoped knowledge replacement. Authority belongs to the fixed adapter.

This repository never opens another domain's database. Physical persistence does
not authorize a future reader: source/identity must be rechecked on every read.
"""
import json

from sqlalchemy import text

from ..kernel.ids import Ulid
from ..kernel.knowledge_wire import KnowledgeReceipt, ReplaceCommand, InvalidationReceipt, InvalidateCommand, payload_digest

_KEY = 'lab_id=:lab_id AND dataset_id=:dataset_id AND source_kind=:source_kind AND source_id=:source_id'


def read(session, key, *, include_payload=False):
    """Internal exact-source lookup; caller must authorize before requesting payload."""
    values = key.model_dump()
    for field,value in values.items():
        session.execute(text('SELECT set_config(:name,:value,true)'),
                        {'name':'knowledge.'+field,'value':value})
    fields = 'receipt,payload_digest,generation,source_revision,publication_sequence'
    if include_payload:
        fields += ',payload'
    return session.execute(text('SELECT '+fields+' FROM knowledge.d9_knowledge_source WHERE '+_KEY),values).mappings().first()


def replace(session, command: ReplaceCommand) -> KnowledgeReceipt:
    return _store(session,command,KnowledgeReceipt,'replaced')


def invalidate(session, command: InvalidateCommand) -> InvalidationReceipt:
    return _store(session,command,InvalidationReceipt,'invalidated')


def _store(session, command, receipt_type, status):
    key = command.source_key.model_dump()
    for field, value in key.items():
        session.execute(text('SELECT set_config(:name,:value,true)'),
                        {'name': 'knowledge.' + field, 'value': value})
    digest = payload_digest(command)
    payload = command.model_dump(mode='json', exclude={'grant'})

    def receipt(sequence):
        return receipt_type(protocol=command.protocol, issuer='D9', receipt_id=Ulid.generate(),
                                source_key=command.source_key, source_version=command.source_version,
                                processing_version=command.processing_version,
                                publication_sequence=sequence, payload_digest=digest, status=status)

    proposed = receipt(1)
    values = {**key, 'generation': command.processing_version.generation,
              'revision': command.source_version.revision, 'digest': digest,
              'payload': json.dumps(payload, ensure_ascii=False, allow_nan=False),
              'receipt': proposed.model_dump_json()}
    inserted = session.execute(text('''INSERT INTO knowledge.d9_knowledge_source
        (lab_id,dataset_id,source_kind,source_id,generation,source_revision,payload_digest,payload,receipt,publication_sequence)
        VALUES (:lab_id,:dataset_id,:source_kind,:source_id,:generation,:revision,:digest,
                CAST(:payload AS jsonb),CAST(:receipt AS jsonb),1)
        ON CONFLICT (lab_id,dataset_id,source_kind,source_id) DO NOTHING RETURNING receipt'''), values).scalar()
    if inserted is not None:
        return receipt_type.model_validate(inserted)
    row = session.execute(text('SELECT * FROM knowledge.d9_knowledge_source WHERE ' + _KEY + ' FOR UPDATE'), key).mappings().one()
    if command.source_version.revision < row['source_revision']:
        raise ValueError('stale_source')
    if command.processing_version.generation < row['generation']:
        raise ValueError('stale_generation')
    if command.processing_version.generation == row['generation']:
        if digest != row['payload_digest']:
            raise ValueError('idempotency_conflict')
        return receipt_type.model_validate(row['receipt'])
    proposed = receipt(row['publication_sequence'] + 1)
    values.update(receipt=proposed.model_dump_json(), sequence=proposed.publication_sequence)
    session.execute(text('''UPDATE knowledge.d9_knowledge_source SET generation=:generation,source_revision=:revision,
        payload_digest=:digest,payload=CAST(:payload AS jsonb),receipt=CAST(:receipt AS jsonb),
        publication_sequence=:sequence WHERE ''' + _KEY), values)
    return proposed
