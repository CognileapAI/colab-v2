"""D3-owned immutable copy of a canonical D5 receipt, after final byte verification.

Later reads use current D3 viewer/file authority only. D5 receipt revocation needs
a future invalidation signal; storage keys are identity, not an ongoing byte scan.
"""
from dataclasses import asdict
import hashlib
import json
from sqlalchemy import text
from ..ports.ingestion import FileMeasurementReceipt

EXTRACTOR = 'file-measurement-v1'


def bind(session, *, receipt: FileMeasurementReceipt, dataset_id: str, storage_key: str):
    if not isinstance(receipt, FileMeasurementReceipt):
        raise ValueError('canonical D5 receipt required')
    row = session.execute(text('''INSERT INTO d3_file_measurement
      (file_id,lab_id,dataset_id,file_revision,storage_key,receipt_id,issuer,parser_version,
       source_digest,byte_size,measured_format)
      SELECT f.id,f.lab_id,f.dataset_id,f.content_revision,f.storage_key,
        :receipt_id,:issuer,:parser_version,:digest,:size_bytes,:format
      FROM d3_file f WHERE f.id=:file_id AND f.lab_id=:lab_id AND f.dataset_id=:dataset
        AND f.content_revision=1 AND f.storage_key=:destination
      ON CONFLICT (file_id) DO NOTHING RETURNING file_id'''),
      {**asdict(receipt),'dataset':str(dataset_id),'destination':storage_key}).scalar_one_or_none()
    if row is None:
        raise ValueError('file measurement binding rejected')


def load_source(session, item):
    row = session.execute(text('''SELECT m.* FROM d3_file_measurement m
      JOIN d3_file f ON f.id=m.file_id AND f.dataset_id=m.dataset_id AND f.lab_id=m.lab_id
      JOIN d3_dataset d ON d.id=f.dataset_id AND d.deleted_at IS NULL
      WHERE m.file_id=:source_id AND m.dataset_id=:dataset_id AND m.lab_id=:lab_id
        AND m.file_revision=f.content_revision AND m.storage_key=f.storage_key'''),asdict(item)).mappings().first()
    if row is None:
        return None
    proof={name:row[name] for name in ('receipt_id','issuer','parser_version','source_digest',
                                     'byte_size','measured_format','file_revision','storage_key')}
    digest=hashlib.sha256(json.dumps(proof,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return {'source_sha256':digest,'file_revision':row['file_revision'],'evidence_revision':None,
            'status':'ready','facts':[{'predicate':'format','value':row['measured_format'],
             'source_locator':'measurement:'+row['receipt_id']+'#/format'}]}
