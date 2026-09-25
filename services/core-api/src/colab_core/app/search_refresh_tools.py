"""Scoped capabilities for a future agent runner. No arbitrary SQL or fact input.

A trusted caller injects the authenticated subject. The instance is short-lived;
process loss recovers through existing lease expiry, not persisted capabilities.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import copy
import secrets
import threading
import time
from ..kernel.scope import scoped_session
from ..ports.ontology import OntologyManifestPort, validate_lookup
from ..ports.search_annotations import validate_selections
from ..domains import d3_search_annotations as annotations
from ..domains import d3_search_changes as changes
from ..domains import d3_search_facts as facts
from ..domains import d3_search_ontology as ontology


@dataclass
class _Handle:
    claim: changes.Claim
    expires: float
    source: dict | None = None
    ontology_version: str | None = None
    lookup: dict | None = None


class SearchRefreshTools:
    def __init__(self, session_factory, subject, manifest_port: OntologyManifestPort, *, validate_subject=None):
        if subject.must_change_password:
            raise ValueError('unrestricted authenticated subject required')
        self._factory,self._subject,self._port=session_factory,subject,manifest_port
        self._validate_subject=validate_subject
        self._handles: dict[str,_Handle]={}
        self._mutex=threading.RLock()

    def _scope(self):
        if self._validate_subject is not None:self._validate_subject(self._subject)
        return scoped_session(self._factory,self._subject)

    def _prune(self):
        now=time.monotonic()
        self._handles={key:item for key,item in self._handles.items() if item.expires>now}

    def _get(self, handle):
        self._prune()
        if not isinstance(handle,str) or handle not in self._handles:
            raise ValueError('unknown or expired work handle')
        return self._handles[handle]

    def sync_manifest(self) -> str:
        with self._scope() as s:previous=ontology.current_manifest(s)
        manifest=self._port.load_manifest()  # No DB session spans the network request.
        with self._scope() as s:
            return ontology.publish(s,manifest,expected_previous=previous['version'] if previous else None)

    def claim(self, *, limit: int = 100) -> list[dict]:
        if type(limit) is not int or not 1<=limit<=100:
            raise ValueError('claim limit must be 1..100')
        with self._mutex:
            self._prune()
            if len(self._handles)+limit>1000:
                raise ValueError('outstanding work handle limit reached')
            expires=time.monotonic()+300
            with self._scope() as s:items=changes.claim(s,limit=limit,lease_seconds=300,authorized_only=True)
            out=[]
            for item in items:
                handle=secrets.token_urlsafe(32)
                self._handles[handle]=_Handle(item,expires)
                out.append({'handle':handle,'source_kind':item.source_kind})
            return out

    def _source(self, session, item):
        if facts.source_deleted(session,item.claim):
            return {'deleted':True}
        return facts.load_source(session,item.claim)

    def read(self, handle: str) -> dict:
        with self._mutex:
            item=self._get(handle)
            with self._scope() as s:
                manifest=ontology.current_manifest(s)
                if not manifest or not changes.is_current(s,item.claim):
                    raise ValueError('current ontology and lease required')
                source=self._source(s,item)
                if source is None:
                    raise ValueError('source unavailable')
            # Store our own copy: a caller cannot alter the remembered read proof.
            item.source=copy.deepcopy(source)
            item.ontology_version=manifest['version']
            item.lookup=None
            return {'source':source,'ontology_version':manifest['version']}

    def lookup(self, handle: str) -> dict:
        with self._mutex:
            item=self._get(handle)
            if item.source is None or item.source.get('status')!='ready':
                raise ValueError('read a ready source first')
            with self._scope() as s:
                manifest=ontology.current_manifest(s)
                if (not manifest or manifest['version']!=item.ontology_version or not changes.is_current(s,item.claim)
                    or self._source(s,item)!=item.source):
                    raise ValueError('source or ontology changed')
            query=json.dumps([f['value'] for f in item.source['facts']],ensure_ascii=False)
            if len(query)>16000:raise ValueError('source concept context exceeds bound')
            result=validate_lookup(self._port.lookup(query=query,manifest=manifest),manifest)
            item.lookup=copy.deepcopy(result)
            return result

    def propose(self, handle: str) -> dict:
        with self._mutex:
            item=self._get(handle)
            if item.lookup is None:raise ValueError('read concept content first')
            # Revalidate access before any source is sent across the service Port.
            with self._scope() as s:
                if not changes.is_current(s,item.claim) or self._source(s,item)!=item.source:
                    raise ValueError('source or access changed')
            proposal=self._port.propose(copy.deepcopy(item.source),copy.deepcopy(item.lookup['concepts']))
            validate_selections(item.source,item.lookup['concepts'],proposal)
            return proposal

    def fail(self, handle: str, *, error_code='processing_failed') -> bool:
        with self._mutex:
            item=self._get(handle)
            with self._scope() as s:
                ok=changes.fail(s,item.claim,error_code=error_code,
                    retry_seconds=min(86400,60*2**min(max(item.claim.attempts-1,0),11)))
            del self._handles[handle]
            return ok

    def reconcile(self, *, limit=100):
        with self._scope() as s:
            old=facts.reconcile(s,limit=limit)
            changed=ontology.requeue(s,limit=limit)
            selected=annotations.reconcile(s,limit=limit)
            return len(old)+len(changed)+len(selected)

    def complete(self, handle: str, *, expected_version: str, concept_ids: list[str], selections=None) -> dict:
        with self._mutex:
            item=self._get(handle)
            if item.source is None or item.ontology_version!=expected_version:
                raise ValueError('read the source and ontology version before completion')
            if not isinstance(concept_ids,list) or len(concept_ids)>1000 or any(not isinstance(c,str) for c in concept_ids):
                raise ValueError('concept IDs must be a bounded list of strings')
            if (item.source.get('deleted') or item.source.get('status')=='candidate') and concept_ids:
                raise ValueError('candidate/deleted sources cannot receive concept bindings')
            grounded=[]
            if selections is not None:
                if item.lookup is None:raise ValueError('read concept content before selection')
                read_ids={p['node']['concept_id'] for p in item.lookup['concepts']}
                if set(concept_ids)!=read_ids:raise ValueError('all read dependencies must be recorded')
                grounded=validate_selections(item.source,item.lookup['concepts'],{'selections':selections})
            with self._scope() as s:
                manifest=ontology.current_manifest(s)  # Ontology lock before queue lock.
                if not manifest or manifest['version']!=expected_version:
                    raise ValueError('ontology changed after read')
                if not changes.is_current(s,item.claim) or self._source(s,item)!=item.source:
                    raise ValueError('source or lease changed after read')
                status=facts.process(s,item.claim)
                if status in {'candidate','deleted'}:
                    result={'status':status,'fact_id':None,'binding_id':None}
                elif status=='ready':
                    rows=facts.read_current(s,item.claim.dataset_id)
                    fact=next((row for row in rows if row['source_kind']==item.claim.source_kind
                               and row['source_id']==item.claim.source_id
                               and row['source_version']==item.claim.claimed_version),None)
                    if fact is None:
                        raise ValueError('source changed during completion')
                    binding=ontology.bind(s,fact['id'],expected_version=expected_version,concept_ids=concept_ids)
                    if selections is not None:
                        annotations.save(s,binding_id=binding,dataset_id=item.claim.dataset_id,selections=grounded)
                    result={'status':status,'fact_id':fact['id'],'binding_id':binding}
                else:
                    raise ValueError('source could not be completed')
            del self._handles[handle]  # Only after successful transaction commit.
            return result


def build_search_refresh_tools(session_factory, subject, settings) -> SearchRefreshTools:
    """Trusted runtime assembly; no user-controlled URL or service credentials."""
    from .ontology_client import OntologyHttpClient
    if not settings.ai_base_url or not settings.ai_service_token:
        raise ValueError('ontology transport is not configured')
    return SearchRefreshTools(session_factory,subject,
        OntologyHttpClient(settings.ai_base_url,token=settings.ai_service_token))
