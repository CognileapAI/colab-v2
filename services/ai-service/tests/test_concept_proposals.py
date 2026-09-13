import json
import pytest
from fastapi.testclient import TestClient

from colab_ai.app.main import create_app
from colab_ai.kernel.config import Settings


def test_sonnet_has_no_execution_tools_and_uses_bounded_output():
    from colab_ai.app.concept_proposals import SonnetConceptProposer
    seen=[]
    def transport(payload):
        seen.append(payload)
        return {'stop_reason':'end_turn','content':[{'type':'text','text':'{"selections":[]}'}]}
    result=SonnetConceptProposer(api_key='fixture',transport=transport).propose({'facts':[]},[])
    assert result=={'selections':[]}
    assert seen[0]['model'].startswith('claude-sonnet-')
    assert 'tools' not in seen[0] and seen[0]['max_tokens']==1024
    assert 'fixture' not in json.dumps(seen)


@pytest.mark.parametrize('response',[{}, {'stop_reason':'max_tokens','content':[]},
    {'stop_reason':'end_turn','content':[{'type':'text','text':'{"sql":"delete"}'}]}])
def test_invalid_or_truncated_model_output_is_failure(response):
    from colab_ai.app.concept_proposals import SonnetConceptProposer
    with pytest.raises(ValueError):
        SonnetConceptProposer(api_key='fixture',transport=lambda p:response).propose({'facts':[]},[])


def test_missing_model_credentials_is_not_successful_empty_selection():
    from colab_ai.app.concept_proposals import SonnetConceptProposer
    with pytest.raises(ValueError):SonnetConceptProposer(api_key=None).propose({'facts':[]},[])


def test_proposal_endpoint_checks_service_identity_before_parsing_body():
    client = TestClient(create_app(Settings(service_token="service-secret")))
    response = client.post("/search-concept-proposals", content=b"not-json")
    assert response.status_code == 401


def test_proposal_endpoint_rejects_malformed_and_oversized_inputs():
    settings = Settings(service_token="service-secret", anthropic_api_key="model-secret")
    client = TestClient(create_app(settings))
    headers = {"Authorization": "Bearer service-secret"}
    assert client.post("/search-concept-proposals", content=b"not-json", headers=headers).status_code == 400
    assert client.post(
        "/search-concept-proposals", content=b"{" + b" " * (128 * 1024), headers=headers
    ).status_code == 400
    assert client.post(
        "/search-concept-proposals",
        json={"source": {"facts": []}, "concepts": [{}] * 7},
        headers=headers,
    ).status_code == 400


def test_proposal_endpoint_returns_validated_model_selection(monkeypatch):
    from colab_ai.app import concept_proposals

    monkeypatch.setattr(
        concept_proposals.SonnetConceptProposer,
        "propose",
        lambda self, source, concepts: {
            "selections": [{"concept_id": "rain", "predicate": "mentions", "quote": "rain fell"}]
        },
    )
    settings = Settings(service_token="service-secret", anthropic_api_key="model-secret")
    client = TestClient(create_app(settings))
    response = client.post(
        "/search-concept-proposals",
        json={
            "source": {"facts": [{"field": "abstract", "value": "rain fell"}]},
            "concepts": [{"concept_id": "rain", "label": "Rain"}],
        },
        headers={"Authorization": "Bearer service-secret"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "selections": [{"concept_id": "rain", "predicate": "mentions", "quote": "rain fell"}]
    }


def test_anthropic_settings_support_direct_and_file_credentials(tmp_path):
    token = tmp_path / "anthropic-key"
    token.write_text("model-secret\n")
    settings = Settings.from_env({"ANTHROPIC_API_KEY_FILE": str(token), "COLAB_AI_CONCEPT_MODEL": "fixed-model"})
    assert settings.anthropic_api_key == "model-secret"
    assert settings.concept_model == "fixed-model"
    assert "model-secret" not in repr(settings)
