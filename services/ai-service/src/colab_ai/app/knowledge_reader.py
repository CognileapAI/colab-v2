"""Protected current-viewer reads, not a distributed source/DB transaction.

The existing factory is reused with READ ONLY transactions. This is not a
separate SELECT-only credential. Projection must recheck source after callback.
"""
from sqlalchemy import text
from ..domains import d9_dataset_knowledge
from ..kernel.knowledge_wire import AuthorizedKnowledge, KnowledgeReceipt, KnowledgeReadRequest
from .ontology_manifest import load_manifest


class KnowledgeReader:
    def __init__(self,factory,authority):
        self._factory,self._authority=factory,authority

    def _row(self,key,*,payload=False):
        with self._factory() as session:
            session.execute(text('SET TRANSACTION READ ONLY'))
            return d9_dataset_knowledge.read(session,key,include_payload=payload)

    def read(self,key,expected_receipt_id):
        request = KnowledgeReadRequest.model_validate({'source_key':key.model_dump(),'expected_receipt_id':expected_receipt_id})
        first = self._row(request.source_key)
        if first is None or first['receipt'].get('status') != 'replaced':
            raise ValueError('forbidden')
        receipt = KnowledgeReceipt.model_validate(first['receipt'])
        if (receipt.receipt_id != request.expected_receipt_id or receipt.source_key != request.source_key
            or receipt.status != 'replaced' or receipt.payload_digest != first['payload_digest']
            or receipt.processing_version.generation != first['generation']
            or receipt.source_version.revision != first['source_revision']
            or receipt.publication_sequence != first['publication_sequence']):
            raise ValueError('forbidden')
        principal = self._authority.authorize_read(receipt)
        if principal.lab_id != key.lab_id:
            raise ValueError('forbidden')
        with self._factory() as session:
            engine = session.get_bind().execution_options(postgresql_readonly=True)
            manifest = load_manifest(engine)
        if manifest['version'] != receipt.processing_version.ontology_release:
            raise ValueError('stale_release')
        final = self._row(key,payload=True)
        if final is None or any(final[field] != value for field,value in first.items()):
            raise ValueError('forbidden')
        return AuthorizedKnowledge.model_validate({'payload':final['payload'],'receipt':final['receipt']})
