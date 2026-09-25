"""The producer uses the same strict boundary as the knowledge consumer."""
import importlib
import importlib.util

import pytest


def test_deletion_boolean_cannot_be_an_integer():
    wire=importlib.import_module('colab_core.kernel.knowledge_wire')
    assert wire.DeletedSourceVersion.model_validate({'revision':1,'deleted':True}).deleted is True
    for bad in (1,False,'true',None):
        with pytest.raises(ValueError):
            wire.DeletedSourceVersion.model_validate({'revision':1,'deleted':bad})


def test_source_versions_reject_coercion_and_unknown_fields():
    name = 'colab_core.kernel.knowledge_wire'
    assert importlib.util.find_spec(name) is not None, 'knowledge wire producer is missing'
    wire = importlib.import_module(name)
    body = {'revision': 1, 'digest': 'a' * 64, 'deleted': False}
    assert wire.SourceVersion.model_validate(body).model_dump() == body
    for change in ({'revision': '1'}, {'deleted': 0}, {'digest': 'not-a-digest'}, {'extra': 1}):
        with pytest.raises(ValueError):
            wire.SourceVersion.model_validate({**body, **change})
