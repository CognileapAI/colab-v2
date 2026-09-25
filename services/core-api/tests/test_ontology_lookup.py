import hashlib,json
from copy import deepcopy
import pytest
from colab_core.ports.ontology import validate_manifest


def fixture():
    node={'concept_id':'rain','label':'강수','kind':'주제','expandable':True,'source_note':'fixture'}
    proof={'node':node,'edges':[],'neighbors':[]}
    digest=lambda v:hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    entries={'discovery':'a'*64,'concept:rain':digest(['dictionary-first-one-hop-fanout-six-v1',node,[],[]])}
    body={'protocol':'ontology-manifest-v1','entries':entries}
    manifest={**body,'version':digest(body)}
    return manifest,{'version':manifest['version'],'concepts':[proof]}


def test_lookup_content_proof_rejects_tampering_and_unknown_concept():
    from colab_core.ports.ontology import validate_lookup
    manifest,response=fixture()
    assert validate_lookup(response,manifest)==response
    bad=deepcopy(response);bad['concepts'][0]['node']['label']='made up'
    with pytest.raises(ValueError):validate_lookup(bad,manifest)
    bad=deepcopy(response);bad['version']='0'*64
    with pytest.raises(ValueError):validate_lookup(bad,manifest)


def test_lookup_duplicate_candidates_rejected():
    from colab_core.ports.ontology import validate_lookup
    manifest,response=fixture();response['concepts']*=2
    with pytest.raises(ValueError):validate_lookup(response,manifest)
