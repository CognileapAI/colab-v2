"""Selected, source-grounded search connections, distinct from read dependencies."""
from __future__ import annotations
from sqlalchemy import text
from .d3_search_facts import EXTRACTOR_VERSION

SELECTOR_VERSION="grounded-literal-v1"


def save(session, *, binding_id, dataset_id, selections):
    existing=session.execute(text('SELECT selector_version FROM d3_search_selection_receipt WHERE binding_id=:id'),{'id':binding_id}).scalar_one_or_none()
    if existing is not None and existing!=SELECTOR_VERSION:raise ValueError('selector receipt cannot be overwritten')
    session.execute(text("""INSERT INTO d3_search_selection_receipt(lab_id,binding_id,selector_version)
      VALUES (current_lab_id(),:id,:version) ON CONFLICT DO NOTHING"""),{'id':binding_id,'version':SELECTOR_VERSION})
    for row in selections:
        existing=session.execute(text("SELECT concept_id,label,quote,source_locator,terms FROM d3_search_concept_match WHERE binding_id=:binding AND concept_id=:concept_id"),
                                 {'binding':binding_id,**row}).mappings().first()
        if existing:
            if dict(existing)!=row:raise ValueError('cannot overwrite a grounded selection')
            continue
        session.execute(text("""INSERT INTO d3_search_concept_match
          (lab_id,binding_id,dataset_id,concept_id,label,quote,source_locator,terms)
          VALUES (current_lab_id(),:binding,:dataset,:concept_id,:label,:quote,:source_locator,:terms)"""),
          {'binding':binding_id,'dataset':dataset_id,**row})


# Materialize only term-matching, potentially current connections once. The cheap
# expected-digest check rejects obsolete history before the full receipt check;
# actual dependency rows and all existing RLS policies remain authoritative.
def current_ctes(extra_where=""):
    return """ontology_eligible AS MATERIALIZED (
      SELECT m.*, b.id, b.expected_dependencies, rel.manifest->'entries' AS current_entries,
        f.source_kind,f.source_id,f.source_version,f.source_sha256
      FROM d3_search_concept_match m
      JOIN d3_search_selection_receipt r ON r.binding_id=m.binding_id
      JOIN d3_search_ontology_binding b ON b.id=m.binding_id
      JOIN d3_search_fact_snapshot f ON f.id=b.fact_snapshot_id
      JOIN d3_search_ontology_head h ON h.lab_id=m.lab_id
      JOIN d3_search_ontology_release rel ON (rel.lab_id,rel.version)=(h.lab_id,h.version)
      WHERE :ontology_enabled AND r.selector_version=:selector AND f.extractor_version=:extractor
        AND m.terms && CAST(:ontology_terms AS text[])
        AND (rel.manifest->'entries') @> b.expected_dependencies """+extra_where+"""
    ), ontology_dependencies AS MATERIALIZED (
      SELECT dep.binding_id, count(*) AS actual_count,
        bool_or(dep.dependency_key='discovery') AS has_discovery,
        jsonb_object_agg(dep.dependency_key,dep.digest) AS actual_entries
      FROM d3_search_ontology_dependency dep
      WHERE EXISTS (SELECT 1 FROM ontology_eligible e WHERE e.id=dep.binding_id)
      GROUP BY dep.binding_id
    ), ontology_current AS MATERIALIZED (
      SELECT b.* FROM ontology_eligible b
      JOIN ontology_dependencies dep ON dep.binding_id=b.id
      WHERE dep.has_discovery AND dep.actual_entries=b.expected_dependencies
        AND dep.actual_count=(SELECT count(*) FROM jsonb_object_keys(b.expected_dependencies))
    )"""


CANDIDATE_CTES=current_ctes()+", ontology_candidates AS MATERIALIZED (SELECT DISTINCT dataset_id FROM ontology_current)"


def matching(session, *, terms, dataset_ids):
    from . import d3_search_changes as changes, d3_search_facts as facts
    normalized=sorted({t.casefold() for t in terms if isinstance(t,str) and t.strip()})
    if not normalized or not dataset_ids:return {}
    if len(dataset_ids)>1000:raise ValueError('result page exceeds bound')
    session.execute(text("SET LOCAL jit=off"))
    # At most three distinct concept explanations per displayed dataset. SQL first
    # excludes obsolete versions; old history cannot exhaust a Python scan window.
    rows=session.execute(text("WITH "+current_ctes(
        "AND m.dataset_id=ANY(CAST(:datasets AS char(26)[]))")+""", distinct_concepts AS (
      SELECT DISTINCT ON (dataset_id,concept_id) * FROM ontology_current
      ORDER BY dataset_id,concept_id,binding_id
    ), page AS (
      SELECT *,row_number() OVER (PARTITION BY dataset_id ORDER BY concept_id) AS ordinal FROM distinct_concepts
    ) SELECT * FROM page WHERE ordinal<=3 ORDER BY dataset_id,concept_id"""),
      {'datasets':list(dataset_ids),'ontology_terms':normalized,'selector':SELECTOR_VERSION,
       'extractor':EXTRACTOR_VERSION,'ontology_enabled':True}).mappings()
    out={}
    for row in rows:
        claim=changes.Claim(row['lab_id'],row['source_kind'],row['source_id'],row['dataset_id'],row['source_version'],0,False,0)
        current=facts.load_source(session,claim)
        if current and current['status']=='ready' and current['source_sha256']==row['source_sha256']:
            out.setdefault(row['dataset_id'],[]).append(dict(row))
    return out


def reconcile(session, *, limit=100):
    if type(limit) is not int or not 1<=limit<=1000:raise ValueError('invalid reconciliation limit')
    # Revisit legacy receipts and selector revisions, but retain valid empty selections.
    return list(session.execute(text("""WITH pending AS (
      SELECT q.lab_id,q.source_kind,q.source_id FROM d3_search_change q
      WHERE q.requested_version=q.processed_version AND q.lease_until IS NULL AND NOT q.deleted
        AND EXISTS (SELECT 1 FROM d3_search_fact_snapshot f WHERE f.lab_id=q.lab_id
          AND f.source_kind=q.source_kind AND f.source_id=q.source_id AND f.source_version=q.requested_version
          AND f.status='ready' AND f.extractor_version=:extractor)
        AND NOT EXISTS (SELECT 1 FROM d3_search_fact_snapshot f
          JOIN d3_search_ontology_binding b ON b.fact_snapshot_id=f.id
          JOIN d3_search_selection_receipt r ON r.binding_id=b.id
          WHERE f.lab_id=q.lab_id AND f.source_kind=q.source_kind AND f.source_id=q.source_id
            AND f.source_version=q.requested_version AND r.selector_version=:selector)
      ORDER BY q.source_kind,q.source_id LIMIT :limit FOR UPDATE OF q SKIP LOCKED
    ) UPDATE d3_search_change q SET requested_version=q.requested_version+1,
        retry_after=clock_timestamp(),updated_at=clock_timestamp()
      FROM pending p WHERE (q.lab_id,q.source_kind,q.source_id)=(p.lab_id,p.source_kind,p.source_id)
      RETURNING q.source_id"""),{'limit':limit,'extractor':EXTRACTOR_VERSION,'selector':SELECTOR_VERSION}).scalars())
