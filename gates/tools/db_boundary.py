#!/usr/bin/env python3
"""db-boundary — 배포 단위가 **허용된 DB 체인 밖으로 접속을 선언하는지** 본다.

왜 있나
  CLAUDE.md §3-1 은 cross-domain 을 Port 로만 넘기라 하고, §3-3 은 db/ai 와 db/platform 을
  갈라 놓는다. 그런데 2026-08-25 에 ai-service(D10)가 `COLAB_AI_CATALOG_DB_URL` 로
  D3 카탈로그에 **직접 붙었고, 모든 게이트가 green 이었다.** 횡단이 import 가 아니라
  **DB 접속**이었기 때문이다 — import-boundary 는 import 만 본다. 사람이 잡았고 기계는 못 잡았다.
  이 게이트는 그 계열을 닫는다.

정의처
  gates/config/db-boundaries.toml 하나뿐. 게이트 스크립트에 표를 다시 적지 않는다.

보는 것 (정직하게 — 못 보는 것은 gates/README.md 에 적어 둔다)
  ① 각 단위 Dockerfile 의 `ENV` / `ARG` 선언 (주석 제외)
  ② 각 단위 파이썬 소스(src/ · tests/)의 **문자열 리터럴** — docstring 은 뺀다.
     주석·docstring 은 AST 에 없으므로 「없앴다」고 적힌 산문이 위반으로 잡히지 않는다
  ③ infra/staging/compose.i2.yml 의 서비스별 `environment`
  ④ chains = [] 인 단위 안의 접속 개시 호출(create_engine 류)

fail-closed (CLAUDE.md §4)
  매니페스트 부재·파싱 실패 · 단위 디렉터리 부재 · compose 파일 부재 · 파이썬 파싱 실패 ·
  스캔 대상 0건 · 단위 0건 · 「DB 처럼 생겼는데 어느 체인에도 안 맞는 env」 → 전부 red.
"""
from __future__ import annotations

import ast
import os
import pathlib
import re
import sys
import tomllib

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
MANIFEST = pathlib.Path(
    os.environ.get("COLAB_DB_BOUNDARY_MANIFEST") or (REPO_ROOT / "gates/config/db-boundaries.toml")
)
ROOT = pathlib.Path(os.environ.get("COLAB_DB_BOUNDARY_ROOT") or REPO_ROOT)
#: 보는 compose 는 **둘 다**다 — staging(`compose.i2.yml`)과 dev(`infra/dev/compose.yml`, `〈342〉`).
#: `COLAB_DB_BOUNDARY_COMPOSE` 로 바꿀 수 있다(단일 경로 또는 `:` 목록 — selftest 가 단일 경로를 준다).
#: 목록 중 하나라도 없으면 red 다 — 없는 파일을 건너뛰면 그 배선이 조용히 사각이 된다.
_COMPOSE_ENV = os.environ.get("COLAB_DB_BOUNDARY_COMPOSE")
COMPOSES: list[pathlib.Path] = (
    [pathlib.Path(p) for p in _COMPOSE_ENV.split(":") if p]
    if _COMPOSE_ENV
    else [ROOT / "infra/staging/compose.i2.yml", ROOT / "infra/dev/compose.yml"]
)
COMPOSE = COMPOSES[0]  # 옛 이름 — 단일 경로를 기대하던 호출자용

SRC_SUBDIRS = ("src", "tests")


def die(msg: str) -> None:
    print(f"::error::db-boundary — {msg}")
    sys.exit(1)


# ── 매니페스트 ──────────────────────────────────────────────────────────────
def load_manifest() -> dict:
    if not MANIFEST.is_file():
        die(f"매니페스트가 없다: {MANIFEST}. 없으면 green 이 아니라 red 다")
    try:
        m = tomllib.loads(MANIFEST.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        die(f"매니페스트 파싱 실패: {MANIFEST} — {e}")
    for key in ("chains", "units", "detect"):
        if not m.get(key):
            die(f"매니페스트에 [{key}] 가 비어 있다: {MANIFEST}")
    if not m["detect"].get("env_is_db"):
        die("매니페스트 [detect].env_is_db 가 없다")
    return m


def classify(env: str, chains: dict) -> str | None:
    for name, spec in chains.items():
        for pat in spec.get("env_patterns", []):
            if re.match(pat, env):
                return name
    return None


# ── 수집기 ──────────────────────────────────────────────────────────────────
def dockerfile_envs(path: pathlib.Path) -> list[tuple[str, int, str]]:
    out: list[tuple[str, int, str]] = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        s = line.strip()
        if s.startswith("#"):
            continue
        m = re.match(r"^(ENV|ARG)\s+(.*)$", s)
        if not m:
            continue
        for tok in re.findall(r"([A-Za-z_][A-Za-z0-9_]*)\s*=", m.group(2)):
            out.append((tok, i, "Dockerfile"))
        if "=" not in m.group(2):
            for tok in m.group(2).split():
                out.append((tok, i, "Dockerfile"))
    return out


def python_strings(path: pathlib.Path) -> list[tuple[str, int]]:
    """docstring 을 뺀 문자열 리터럴. 주석은 AST 에 없어 자동으로 빠진다."""
    text = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as e:
        die(f"파이썬 파싱 실패(대상을 읽지 못했다): {path} — {e}")
    doc_nodes: set[int] = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if isinstance(body, list) and body:
            first = body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) \
                    and isinstance(first.value.value, str):
                doc_nodes.add(id(first.value))
    out: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in doc_nodes:
            out.append((node.value, node.lineno))
    return out


def compose_envs(path: pathlib.Path) -> dict[str, list[str]]:
    try:
        import yaml  # noqa: PLC0415
    except ImportError:
        die("pyyaml 이 없다 — compose 를 읽지 못하면 skip 이 아니라 red 다")
    if not path.is_file():
        die(f"compose 파일이 없다: {path}")
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as e:  # noqa: BLE001
        die(f"compose 파싱 실패: {path} — {e}")
    services = doc.get("services") or {}
    if not services:
        die(f"compose 에 services 가 0건이다: {path}")
    out: dict[str, list[str]] = {}
    for name, spec in services.items():
        env = (spec or {}).get("environment") or {}
        if isinstance(env, dict):
            out[name] = list(env.keys())
        elif isinstance(env, list):
            out[name] = [str(e).split("=", 1)[0] for e in env]
        else:
            out[name] = []
    return out


# ── 판정 ────────────────────────────────────────────────────────────────────
def main() -> int:
    m = load_manifest()
    chains: dict = m["chains"]
    units: dict = m["units"]
    detect: dict = m["detect"]
    is_db = re.compile(detect["env_is_db"])
    connect_calls = detect.get("connect_calls", [])

    violations: list[str] = []
    scanned = 0
    unit_targets = 0

    def judge(owner: str, allowed: list[str], env: str, where: str) -> None:
        if not is_db.search(env):
            return
        chain = classify(env, chains)
        if chain is None:
            violations.append(
                f"{owner}: `{env}` 는 DB URL 로 보이는데 어느 체인에도 속하지 않는다 ({where}). "
                f"체인을 매니페스트에 밝히기 전까지 red 다"
            )
        elif chain not in allowed:
            allow = ", ".join(allowed) if allowed else "없음"
            violations.append(
                f"{owner}: `{env}` → 체인 `{chain}` (허용: {allow}) — 체인 횡단 ({where})"
            )

    # ① 단위 디렉터리 (Dockerfile · 파이썬 소스)
    for unit, spec in units.items():
        allowed = spec.get("chains", [])
        d = spec.get("dir")
        if not d:
            continue  # compose 전용 러너
        udir = ROOT / d
        if not udir.is_dir():
            die(f"매니페스트가 가리키는 단위 디렉터리가 없다: {udir} (단위 {unit})")
        df = udir / "Dockerfile"
        if df.is_file():
            scanned += 1
            unit_targets += 1
            for env, line, kind in dockerfile_envs(df):
                judge(unit, allowed, env, f"{d}/Dockerfile:{line} {kind}")
        for sub in SRC_SUBDIRS:
            for py in sorted((udir / sub).rglob("*.py")):
                scanned += 1
                unit_targets += 1
                text = py.read_text(encoding="utf-8")
                for s, line in python_strings(py):
                    judge(unit, allowed, s, f"{py.relative_to(ROOT)}:{line}")
                if not allowed:
                    for call in connect_calls:
                        if re.search(rf"(?<![\w.]){re.escape(call)}\s*\(", text):
                            violations.append(
                                f"{unit}: 접속 개시 호출 `{call}(` 가 있다 — 이 단위는 "
                                f"어떤 체인에도 붙지 않는다 ({py.relative_to(ROOT)})"
                            )

    # ③ compose — 파일마다 따로 판정한다. 서비스명이 곧 단위 키다(`compose_service`).
    by_service = {
        spec.get("compose_service"): (unit, spec.get("chains", []))
        for unit, spec in units.items()
        if spec.get("compose_service")
    }
    for compose in COMPOSES:
        svc_envs = compose_envs(compose)
        scanned += 1
        where_file = str(compose.relative_to(ROOT)) if compose.is_relative_to(ROOT) else compose.name
        for svc, envs in svc_envs.items():
            db_envs = [e for e in envs if is_db.search(e)]
            if not db_envs:
                continue
            if svc not in by_service:
                violations.append(
                    f"compose 서비스 `{svc}` 가 DB URL {db_envs} 를 선언하는데 매니페스트에 없다 — "
                    f"허용 체인을 밝히기 전까지 red 다 ({where_file})"
                )
                continue
            unit, allowed = by_service[svc]
            for env in db_envs:
                judge(unit, allowed, env, f"{where_file}:services.{svc}.environment")

    if not units:
        die("매니페스트의 단위가 0건이다")
    if unit_targets == 0:
        die("단위에서 스캔한 대상이 0건이다 — 조용히 아무것도 못 찾은 게이트가 v1 의 실패다")

    if violations:
        print(f"::error::db-boundary — 체인 밖 DB 접속 선언 {len(violations)}건")
        for v in violations:
            print(f"  · {v}")
        return 1

    print(f"db-boundary: green — 단위 {len(units)}개 · 스캔 대상 {scanned}건 · 위반 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
