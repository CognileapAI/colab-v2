"""Fail-closed loader for the shared, JSON-compatible harness contract."""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
import re
import subprocess
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
    "hygiene",
}

# A user home directory written as an absolute path. The user component is a real account
# name, so placeholders such as `<u>`, `$USER` or `…` never match. `/mnt/c/Users/<u>/` is
# listed first so the leftmost match reports the whole WSL form once.
HOME_PATH = re.compile(
    r"/mnt/[A-Za-z]/Users/[A-Za-z0-9._-]+/"
    r"|/home/[A-Za-z0-9._-]+/"
    r"|/Users/[A-Za-z0-9._-]+/"
    r"|[A-Za-z]:\\{1,2}Users\\{1,2}[A-Za-z0-9._-]+\\{1,2}"
)


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
    sources = value.get("sources")
    if not isinstance(sources, dict):
        raise ContractError("sources must be an object")
    registrations = sources.get("hook_registrations")
    if not isinstance(registrations, dict):
        raise ContractError("sources.hook_registrations must be an object")
    for name, entry in registrations.items():
        if (not isinstance(entry, dict) or set(entry) != {"event", "matcher"}
                or any(not isinstance(item, str) or not item.strip() for item in entry.values())):
            raise ContractError(f"sources.hook_registrations.{name} needs non-empty event and matcher")
    hygiene = value.get("hygiene")
    if not isinstance(hygiene, dict):
        raise ContractError("hygiene must be an object")
    limit = hygiene.get("always_on_max_lines")
    if type(limit) is not int or limit <= 0:
        raise ContractError("hygiene.always_on_max_lines must be a positive integer")
    for field in ("always_on_files", "home_path_roots"):
        for item in _strings(hygiene.get(field), f"hygiene.{field}"):
            _relative(item, f"hygiene.{field}")
    _strings(hygiene.get("home_path_allow"), "hygiene.home_path_allow", nonempty=False)
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
        errors += _check_hook_wiring(root, names, value["sources"]["hook_registrations"])
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


def _check_hook_wiring(root: Path, names: list, registrations: dict) -> list[str]:
    """Assert each declared hook is wired in `.claude/settings.json` under its event and matcher.

    `agent-bridge check` compares the Claude and Codex event/matcher sets, so dropping a whole
    matcher is caught there. Dropping one command line under a kept matcher is not — that is
    the path this check closes (intent 2026-09-25-external-harness-gap, outcome 1).
    """
    try:
        settings = json.loads((root / ".claude/settings.json").read_text(encoding="utf-8"))
        wired: dict[tuple[str, str], list] = {}
        for event, entries in settings["hooks"].items():
            for entry in entries:
                commands = [hook["command"] for hook in entry["hooks"]]
                wired.setdefault((event, entry["matcher"]), []).extend(commands)
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, AttributeError) as exc:
        return [f"cannot read hook registrations from .claude/settings.json: {exc}"]
    errors = []
    for name in names:
        if not isinstance(name, str) or not name.endswith(".sh") or PurePosixPath(name).name != name:
            continue  # already reported as an invalid shared hook name
        entry = registrations.get(name)
        if entry is None:
            errors.append(f"hook has no event/matcher registration: {name}")
            continue
        shim = re.compile(r"(?:^|[\s\"'/])\.claude/hooks/" + re.escape(name) + r"(?=$|[\s\"'])")
        commands = wired.get((entry["event"], entry["matcher"]), [])
        if not any(isinstance(command, str) and shim.search(command) for command in commands):
            errors.append(f"hook not registered in .claude/settings.json: {name} "
                          f"(event {entry['event']}, matcher {entry['matcher']})")
    for name in sorted(set(registrations) - set(names)):
        errors.append(f"hook registration names an undeclared hook: {name}")
    return errors


def check_always_on_lines(root: Path, value: dict) -> list[str]:
    """Documents loaded into every session stay under the declared line budget."""
    hygiene = value["hygiene"]
    limit = hygiene["always_on_max_lines"]
    errors = []
    for pattern in hygiene["always_on_files"]:
        if any(char in pattern for char in "*?["):
            paths = sorted(path for path in root.glob(pattern) if path.is_file())
            if not paths:
                errors.append(f"always-on pattern matches no file: {pattern}")
                continue
        else:
            if not (root / pattern).is_file():
                errors.append(f"always-on document is missing: {pattern}")
                continue
            paths = [root / pattern]
        for path in paths:
            relative = path.relative_to(root).as_posix()
            try:
                count = len(path.read_text(encoding="utf-8").splitlines())
            except (OSError, UnicodeError) as exc:
                errors.append(f"cannot read always-on document: {relative}: {exc}")
                continue
            if count > limit:
                errors.append(f"always-on document exceeds {limit} lines: {relative} ({count})")
    return errors


def check_home_paths(root: Path, value: dict) -> tuple[list[str], str | None]:
    """Reject user home absolute paths in harness documents.

    Returns (judgement errors, readiness reason). The file list comes from Git (tracked plus
    untracked-but-not-ignored), so nested worktrees and ignored runtime files are not read.
    Binary files are skipped. Not being able to list or read the files is readiness, not green.
    """
    hygiene = value["hygiene"]
    allowed = set(hygiene["home_path_allow"])
    try:
        listed = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z", "--cached", "--others", "--exclude-standard",
             "--", *hygiene["home_path_roots"]],
            capture_output=True, check=False)
    except OSError as exc:
        return [], f"cannot list harness documents: {exc}"
    if listed.returncode != 0:
        return [], "cannot list harness documents: " + listed.stderr.decode("utf-8", "replace").strip()
    names = sorted({name for name in listed.stdout.decode("utf-8").split("\0") if name})
    errors, scanned = [], 0
    for name in names:
        path = root / name
        if path.is_symlink() or not path.is_file():
            continue
        try:
            data = path.read_bytes()
        except OSError as exc:
            return errors, f"cannot read harness document {name}: {exc}"
        if b"\0" in data:
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            continue
        scanned += 1
        for number, line in enumerate(text.splitlines(), 1):
            for match in HOME_PATH.finditer(line):
                if match.group(0) not in allowed:
                    errors.append(f"home absolute path in {name}:{number}: {match.group(0)}")
    if scanned == 0:
        return errors, "home-path scan found no harness document to read"
    return errors, None
