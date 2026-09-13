"""Transport-neutral D9 content receipt. No connection to the knowledge database."""
from __future__ import annotations

import hashlib
import json
import re
from typing import Protocol
from ..kernel.ontology_wire import PROTOCOL, MAX_ENTRIES, MAX_KEY_LENGTH, KEY_PATTERN, DIGEST_PATTERN


class OntologyManifestPort(Protocol):
    def load_manifest(self) -> dict: ...


def validate_manifest(value: dict) -> dict:
    if not isinstance(value, dict) or set(value)!={'protocol','entries','version'}:
        raise ValueError('invalid ontology manifest shape')
    entries=value['entries']
    if value['protocol']!=PROTOCOL or not isinstance(entries,dict) or 'discovery' not in entries:
        raise ValueError('unsupported ontology manifest')
    if len(entries)>MAX_ENTRIES:
        raise ValueError('ontology manifest too large')
    for key,digest in entries.items():
        if not isinstance(key,str) or not re.fullmatch(KEY_PATTERN,key) or len(key)>MAX_KEY_LENGTH:
            raise ValueError('invalid dependency key')
        if not isinstance(digest,str) or not re.fullmatch(DIGEST_PATTERN,digest):
            raise ValueError('invalid dependency digest')
    body={'protocol':value['protocol'],'entries':dict(entries)}
    version=hashlib.sha256(json.dumps(body,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if value['version']!=version:
        raise ValueError('ontology content digest mismatch')
    return {**body,'version':version}


def validate_lookup(value: dict, manifest: dict) -> dict:
    """Verify each complete one-hop proof against the trusted content receipt."""
    from ..kernel.ontology_wire import MAX_CONCEPTS
    manifest=validate_manifest(manifest)
    if not isinstance(value,dict) or set(value)!={'version','concepts'} or value['version']!=manifest['version']:
        raise ValueError('invalid concept lookup version')
    proofs=value['concepts']
    if not isinstance(proofs,list) or len(proofs)>MAX_CONCEPTS:
        raise ValueError('invalid concept lookup bound')
    seen=set()
    try:
        for proof in proofs:
            if set(proof)!={'node','edges','neighbors'} or len(proof['edges'])>64 or len(proof['neighbors'])>65:
                raise ValueError('invalid concept proof')
            cid=proof['node']['concept_id']
            if cid in seen:raise ValueError('duplicate concept proof')
            seen.add(cid)
            body=['dictionary-first-one-hop-fanout-six-v1',proof['node'],proof['edges'],proof['neighbors']]
            digest=hashlib.sha256(json.dumps(body,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
            if manifest['entries'].get('concept:'+cid)!=digest:
                raise ValueError('concept content digest mismatch')
    except (KeyError,TypeError):
        raise ValueError('invalid concept proof') from None
    return json.loads(json.dumps(value,ensure_ascii=False))
