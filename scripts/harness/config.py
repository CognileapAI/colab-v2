"""Fail-closed loader for the shared, JSON-compatible harness contract."""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath


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
    if not isinstance(project, dict) or project.get("default_branch") != "main":
        raise ContractError("project.default_branch must be main")
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
