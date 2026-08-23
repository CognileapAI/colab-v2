import json
import sys
from pathlib import Path

import pytest

# 픽스처 빌더를 테스트에서 평이하게 import 하기 위해
sys.path.insert(0, str(Path(__file__).parent))


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """레포 루트 — 계약 정본을 읽는 자리. 문서 규칙(절대경로 금지)과 같은 이유로 계산해 쓴다."""
    p = Path(__file__).resolve()
    for parent in p.parents:
        if (parent / "contracts" / "events" / "envelope.json").is_file():
            return parent
    pytest.fail("레포 루트를 찾지 못했다 (contracts/events/envelope.json 기준)")


@pytest.fixture(scope="session")
def event_validator(repo_root):
    """동결 계약(`contracts/events/core-pipeline.json#AnyEvent`)으로 봉투를 검증한다.

    계약을 **다시 적지 않는다** — 파일을 그대로 읽어 `$ref` 를 로컬에서 해석한다.
    """
    jsonschema = pytest.importorskip("jsonschema")
    from referencing import Registry, Resource

    events = repo_root / "contracts" / "events"
    base = "https://colab.cognileap.ai/events/"

    def _load(name: str) -> dict:
        return json.loads((events / name).read_text("utf-8"))

    common = json.loads((repo_root / "contracts" / "schemas" / "common.json").read_text("utf-8"))
    resources = [
        (base + "envelope.json", _load("envelope.json")),
        (base + "core-pipeline.json", _load("core-pipeline.json")),
        (base + "../schemas/common.json", common),
        ("https://colab.cognileap.ai/schemas/common.json", common),
    ]
    registry = Registry().with_resources(
        [(uri, Resource.from_contents(doc)) for uri, doc in resources]
    )
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": base + "any-event-check.json",
        "$ref": "core-pipeline.json#/$defs/AnyEvent",
    }
    validator = jsonschema.Draft202012Validator(schema, registry=registry)

    def _validate(instance) -> list[str]:
        return [f"{list(e.absolute_path)}: {e.message}" for e in validator.iter_errors(instance)]

    return _validate
