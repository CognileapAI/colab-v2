"""Read-only content manifest for the existing one-hop ontology rules.

This is a transport-neutral adapter; it neither publishes knowledge nor reads files.
"""
from __future__ import annotations

import hashlib
import json
from sqlalchemy import text

from colab_ai.kernel.ontology_wire import PROTOCOL
from colab_ai.kernel.search_semantics import SEMANTIC_VERSION
MATCHER = 'dictionary-first-one-hop-fanout-six-v1'


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def _hash(value):
    return hashlib.sha256(_json(value).encode()).hexdigest()


def build_manifest(content: dict) -> dict:
    clean = {name: sorted(({k:v for k,v in row.items() if k!='created_at'} for row in content[name]), key=_json)
             for name in ('methods','topics','places','concepts','edges')}
    nodes = {row['concept_id']:row for row in clean['concepts']}
    if len(nodes)!=len(clean['concepts']):
        raise ValueError('duplicate concept ID')
    entries = {'discovery': _hash([MATCHER, SEMANTIC_VERSION, clean['methods'], clean['topics'], clean['places'],
        [{k:row[k] for k in ('concept_id','kind','label')} for row in clean['concepts']]])}
    for cid, node in nodes.items():
        edges = [edge for edge in clean['edges'] if cid in (edge['src'],edge['dst'])]
        neighbors = sorted({edge['src'] for edge in edges}|{edge['dst'] for edge in edges})
        if any(n not in nodes for n in neighbors):
            raise ValueError('dangling concept edge')
        entries['concept:'+cid] = _hash([MATCHER,node,edges,[nodes[n] for n in neighbors]])
    body = {'protocol':PROTOCOL,'entries':entries}
    return {**body,'version':_hash(body)}


def load_content(engine) -> dict:
    # A single PostgreSQL statement gives all five tables the same MVCC snapshot.
    with engine.connect() as connection:
        content = connection.execute(text('''SELECT jsonb_build_object(
          'methods', (SELECT coalesce(jsonb_agg(to_jsonb(t)-'created_at'),'[]') FROM d9_method_term t),
          'topics', (SELECT coalesce(jsonb_agg(to_jsonb(t)-'created_at'),'[]') FROM d9_topic_synonym t),
          'places', (SELECT coalesce(jsonb_agg(to_jsonb(t)-'created_at'),'[]') FROM d9_place_alias t),
          'concepts', (SELECT coalesce(jsonb_agg(to_jsonb(t)-'created_at'),'[]') FROM d9_concept t),
          'edges', (SELECT coalesce(jsonb_agg(to_jsonb(t)-'created_at'),'[]') FROM d9_concept_edge t)
        )''')).scalar_one()
    return content


def load_manifest(engine) -> dict:
    return build_manifest(load_content(engine))
