"""Bounded one-hop content proofs; no product data reads or ontology writes."""
from __future__ import annotations
import threading
from . import ontology_manifest as manifests
from ..kernel.ontology_wire import MAX_CONCEPTS


def lookup(content, *, query: str, expected_version: str) -> dict:
    if not isinstance(query,str) or len(query)>16000:
        raise ValueError('invalid concept query')
    manifest=manifests.build_manifest(content)
    if manifest['version']!=expected_version:
        raise ValueError('ontology version unavailable')
    clean={name:sorted(({k:v for k,v in row.items() if k!='created_at'} for row in content[name]),key=manifests._json)
           for name in ('concepts','edges')}
    nodes={node['concept_id']:node for node in clean['concepts']}
    matches=sorted((n for n in nodes.values() if n['label'].casefold() in query.casefold()),
                   key=lambda n:(-len(n['label']),n['concept_id']))[:MAX_CONCEPTS]
    proofs=[]
    for node in matches:
        cid=node['concept_id'];edges=[e for e in clean['edges'] if cid in (e['src'],e['dst'])]
        ids=sorted({e['src'] for e in edges}|{e['dst'] for e in edges})
        if len(edges)>64 or len(ids)>65:
            raise ValueError('concept neighborhood exceeds bound')
        proofs.append({'node':node,'edges':edges,'neighbors':[nodes[i] for i in ids]})
    return {'version':expected_version,'concepts':proofs}


class ContentReader:
    """One immutable snapshot per requested version; product rows are never scanned.

    Manifest polling discovers changes. An old snapshot may be served consistently;
    the caller's current manifest fence decides whether it can still be committed.
    """
    def __init__(self,engine):
        self.engine=engine;self._lock=threading.Lock();self._version=None;self._content=None

    def lookup(self, *, query, expected_version):
        with self._lock:
            if self._version!=expected_version:
                content=manifests.load_content(self.engine)
                if manifests.build_manifest(content)['version']!=expected_version:
                    raise ValueError('ontology version unavailable')
                self._content,self._version=content,expected_version
            return lookup(self._content,query=query,expected_version=expected_version)
