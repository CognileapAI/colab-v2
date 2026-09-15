"""Fail-closed loader for the shared, JSON-compatible harness contract."""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
import tomllib


SCHEMA = "colab-harness/1"
TOP_LEVEL = {
    "schema",
    "project",
    "commands",
    "gates",
    "evidence",
    "sources",
    "adapters",
    "paths",
    "publication",
}


class ContractError(ValueError):
    """The contract cannot be used to make a harness decision."""


def _strings(value: object, field: str, *, nonempty: bool = True) -> list[str]:
    if not isinstance(value, list) or (nonempty and not value):
        raise ContractError(f"{field} must be a non-empty list")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ContractError(f"{field} must contain non-empty strings")
    return value


def _relative(value: str, field: str) -> None:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        raise ContractError(f"{field} must be repository-relative: {value}")


def validate_contract(value: object) -> dict:
    if not isinstance(value, dict):
        raise ContractError("contract must be an object")
    missing = sorted(TOP_LEVEL - set(value))
    if missing:
        raise ContractError("missing required keys: " + ", ".join(missing))
    if value.get("schema") != SCHEMA:
        raise ContractError(f"schema must be {SCHEMA}")
    project = value.get("project")
    if not isinstance(project, dict) or project.get("default_branch") != "develop":
        raise ContractError("project.default_branch must be develop")
    if project.get("deployment_branch") != "product":
        raise ContractError("project.deployment_branch must be product")
    gates = value.get("gates")
    if not isinstance(gates, dict):
        raise ContractError("gates must be an object")
    required = _strings(gates.get("required"), "gates.required")
    if len(required) != len(set(required)):
        raise ContractError("gates.required contains duplicates")
    if gates.get("states") != {"green": 0, "red_judgment": 1, "red_readiness": 78}:
        raise ContractError("gates.states must preserve exit 0/1/78")
    adapters = value.get("adapters")
    paths = value.get("paths")
    if not isinstance(adapters, dict) or not isinstance(paths, dict):
        raise ContractError("adapters and paths must be objects")
    for field, items in (
        ("adapters.required_files", _strings(adapters.get("required_files"), "adapters.required_files")),
        ("paths.required", _strings(paths.get("required"), "paths.required")),
        ("paths.compatibility_read_roots", _strings(paths.get("compatibility_read_roots"), "paths.compatibility_read_roots")),
    ):
        for item in items:
            _relative(item, field)
    retired = paths.get("retired_roots")
    if not isinstance(retired, list):
        raise ContractError("paths.retired_roots must be a list")
    for item in retired:
        if not isinstance(item, str) or not item:
            raise ContractError("paths.retired_roots must contain non-empty strings")
        _relative(item, "paths.retired_roots")
    return value


def load_contract(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot load harness contract: {exc}") from exc
    return validate_contract(value)


def check_contract(root: Path, value: dict) -> list[str]:
    errors: list[str] = []
    product = value['sources'].get('product')
    if product != '.agents/rules/product.md':
        errors.append('missing or invalid shared product mapping')
    elif not (root / product).is_file() or not (root / product).read_text(encoding='utf-8').strip():
        errors.append('missing shared product source')
    expected_product_adapter = ('# Claude adapter\n\n@AGENTS.md\n\n'
        '공통 제품 본문은 저장소 루트 기준 `.agents/rules/product.md`를 읽고 따른다.\n'
        '진입·인계 절차는 `AGENTS.md`가 우선하며, 이 파일에는 제품 본문을 복제하지 않는다.')
    try:
        if (root / 'CLAUDE.md').read_text(encoding='utf-8').strip() != expected_product_adapter:
            errors.append('invalid Claude product adapter')
    except OSError:
        errors.append('missing Claude product adapter')
    for kind, adapter_dir in (("rules", "rules"), ("roles", "agents")):
        names = value["sources"].get(kind)
        if not isinstance(names, list) or not names:
            errors.append(f"missing shared {kind} mappings")
            continue
        for name in names:
            if not isinstance(name, str) or not name or PurePosixPath(name).name != name:
                errors.append(f"invalid shared {kind} name")
                continue
            relative = f".agents/{kind}/{name}.md"
            source = root / relative
            if not source.is_file() or not source.read_text(encoding="utf-8").strip():
                errors.append(f"missing shared source: {relative}")
            adapter = root / f".claude/{adapter_dir}/{name}.md"
            expected = (
                "# Claude adapter\n\n"
                f"공통 본문은 저장소 루트 기준 `{relative}`를 읽고 따른다.\n"
                "이 파일의 Claude frontmatter는 도구별 등록 정보이며 공통 본문을 복제하지 않는다."
            )
            try:
                body = adapter.read_text(encoding="utf-8")
                if body.startswith("---\n"):
                    body = body.split("\n---\n", 1)[1]
                if body.strip() != expected:
                    errors.append(f"invalid Claude source adapter: {adapter.relative_to(root)}")
            except (OSError, IndexError):
                errors.append(f"missing or malformed Claude source adapter: {adapter.relative_to(root)}")
            if kind == "roles":
                try:
                    config = tomllib.loads((root / f".codex/agents/{name}.toml").read_text(encoding="utf-8"))
                    if config.get("name") != name or relative not in config.get("developer_instructions", ""):
                        errors.append(f"invalid Codex role source: {name}")
                except (OSError, tomllib.TOMLDecodeError):
                    errors.append(f"missing or malformed Codex role adapter: {name}")
    names = value["sources"].get("hook_names")
    if not isinstance(names, list) or not names:
        errors.append("missing shared hook mappings")
    else:
        for name in names:
            if not isinstance(name, str) or PurePosixPath(name).name != name or not name.endswith(".sh"):
                errors.append("invalid shared hook name")
                continue
            source = root / "scripts/harness/hooks" / name
            adapter = root / ".claude/hooks" / name
            if not source.is_file():
                errors.append(f"missing shared hook: {name}")
            expected = f'exec bash "$(dirname "${{BASH_SOURCE[0]}}")/../../scripts/harness/hooks/{name}" "$@"'
            try:
                statements = [line.strip() for line in adapter.read_text().splitlines()
                              if line.strip() and not line.lstrip().startswith("#")]
                if statements != [expected]:
                    errors.append(f"invalid hook adapter: {name}")
            except OSError:
                errors.append(f"missing hook adapter: {name}")
        if not (root / "scripts/harness/hooks/lifecycle_contract.py").is_file():
            errors.append("missing shared lifecycle contract")
    for name in value["adapters"]["required_files"]:
        if not (root / name).exists():
            errors.append(f"missing required adapter: {name}")
    for name in value["paths"]["required"]:
        if not (root / name).exists():
            errors.append(f"missing required path: {name}")
    for name in value["paths"]["retired_roots"]:
        if (root / name).exists():
            errors.append(f"retired path still exists: {name}")
    return errors
