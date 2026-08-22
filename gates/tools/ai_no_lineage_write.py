#!/usr/bin/env python3
"""ai-no-lineage-write 게이트 (WU-D3) — **음성 게이트**.

증명하려는 명제: "D10 → D4(Lineage) 쓰기 경로가 **존재하지 않는다**" (CLAUDE.md §3-2),
그리고 "db/ai 와 db/platform 의 마이그레이션 체인이 섞이지 않는다" (§3-3).

음성 명제는 "무엇이 있으면 red 인가"를 구체적으로 적어야만 검사가 된다. 세 층을 본다.

  L1 계약층  contracts/seams/core-ai.yaml 에 계보를 **확정·생성**하는 오퍼레이션이 없을 것
             red 조건 ①  계보 경로에 PUT/PATCH/DELETE 오퍼레이션이 하나라도 있다
                     ②  operationId 가 (확정 동사 × 계보 명사) 조합인데 허용 목록에 없다
                     ③  components.schemas 이름이 같은 조합이다 (요청 본문으로 새는 경로)
                     ④  seam 대상 파일이 0건이다 (검사 못 함은 통과가 아니다)
  L2 코드층  services/ai-service 코드가 플랫폼에 쓰지 못할 것
             red 조건 ⑤  금지 패키지 import (colab_core · alembic · db.platform …)
                     ⑥  D4 테이블 접두사(lineage_ · d4_)가 코드에 등장
                     ⑦  쓰기 SQL 키워드와 D4 테이블 접두사가 같은 줄에 등장
                     ⑧  ai-service 코드가 0건이다 → 증명 대상 미존재 = red
  L3 체인층  db/ai 와 db/platform 이 갈라져 있을 것
             red 조건 ⑨  db/ai 아래 파일이 db/platform(또는 D4 테이블)을 참조
                     ⑩  db/platform 아래 파일이 db/ai 를 참조
                     ⑪  두 체인의 alembic version_table 이 같거나 한쪽이 없다
                     ⑫  두 체인 중 하나라도 마이그레이션이 0건이다 → 증명 대상 미존재 = red

**대상 0건을 green 으로 세지 않는 이유**: 음성 명제는 대상이 없으면 공허하게 참이다.
"AI 가 계보에 쓰지 않는다"와 "AI 가 아직 없다"는 다른 사실이고, 게이트가 둘을 구분하지 못하면
그게 green-by-skip 이다 (v1 CI 가 DB 없이 RLS 테스트를 통과시킨 것과 같은 실패).

환경변수 (selftest 전용)
  COLAB_SEAM_DIR · COLAB_SERVICES_DIR · COLAB_DB_DIR · COLAB_BOUNDARY_CONFIG
"""
import ast
import configparser
import os
import pathlib
import re
import sys
import tomllib

import yaml

REPO = pathlib.Path(__file__).resolve().parents[2]
SEAMS = pathlib.Path(os.environ.get("COLAB_SEAM_DIR", REPO / "contracts/seams"))
SERVICES = pathlib.Path(os.environ.get("COLAB_SERVICES_DIR", REPO / "services"))
DB = pathlib.Path(os.environ.get("COLAB_DB_DIR", REPO / "db"))
CONFIG = pathlib.Path(os.environ.get("COLAB_BOUNDARY_CONFIG", REPO / "gates/config/boundaries.toml"))

WRITE_METHODS = {"put", "patch", "delete"}
TEXT_SUFFIXES = {".py", ".sql", ".ini", ".cfg", ".toml", ".yaml", ".yml", ".mako"}

FAILS = []


def fail(code, msg):
    FAILS.append(f"[{code}] {msg}")


def rel(p):
    try:
        return str(pathlib.Path(p).relative_to(REPO))
    except ValueError:
        return str(p)


def _tbl_re(prefixes):
    """D4 테이블 접두사 정규식.

    앞에 단어 문자가 붙은 경우는 제외한다 — D10 의 제안 임시 저장소는 `ai_` 접두사를 쓰기로 했고
    (`ai_lineage_suggestion` 등), 그건 db/ai 소유의 다른 테이블이지 D4 가 아니다.
    """
    return re.compile("(?<![A-Za-z0-9_])(" + "|".join(re.escape(x) for x in prefixes) + ")")


def combo_hit(name, verbs, nouns):
    low = (name or "").lower()
    return any(n in low for n in nouns) and any(v in low for v in verbs)


# ── L1 계약층 ────────────────────────────────────────────────────────────────
def check_contract(cfg):
    verbs, nouns = cfg["banned_operation_verbs"], cfg["lineage_nouns"]
    allowed = set(cfg["allowed_lineage_operations"])
    specs = sorted(p for p in SEAMS.glob("*.y*ml")) if SEAMS.is_dir() else []
    ai = [p for p in specs if "ai" in p.stem]
    print(f"  L1 계약층      seam {len(specs)}건 (그중 core-ai {len(ai)}건)")
    if not ai:
        fail("④", f"core-ai seam 계약이 0건이다 ({rel(SEAMS)}). 검사하지 못한 것은 통과가 아니다.")
        return
    for spec in ai:
        doc = yaml.safe_load(spec.read_text(encoding="utf-8")) or {}
        for path, item in (doc.get("paths") or {}).items():
            if not isinstance(item, dict):
                continue
            path_is_lineage = any(n in path.lower() for n in nouns)
            for method, op in item.items():
                if not isinstance(op, dict) or method.lower() not in (
                    "get", "put", "post", "delete", "patch", "head", "options", "trace"
                ):
                    continue
                opid = op.get("operationId", "")
                if path_is_lineage and method.lower() in WRITE_METHODS:
                    fail("①", f"{rel(spec)} {method.upper()} {path} — 계보 경로의 쓰기 메서드. "
                              f"AI 는 제안만 한다 (CLAUDE.md §3-2).")
                if combo_hit(opid, verbs, nouns) and opid not in allowed:
                    fail("②", f"{rel(spec)} operationId={opid} — 계보를 확정/생성하는 이름이다. "
                              f"허용된 것은 {sorted(allowed)} 뿐이다.")
        for sname in ((doc.get("components") or {}).get("schemas") or {}):
            if combo_hit(sname, verbs, nouns):
                fail("③", f"{rel(spec)} components.schemas.{sname} — 계보 확정 페이로드 형태다.")


# ── L2 코드층 ────────────────────────────────────────────────────────────────
def check_code(cfg):
    banned_imports = set(cfg["banned_imports"])
    prefixes = cfg["platform_lineage_tables"]
    kws = cfg["write_sql_keywords"]
    root = SERVICES / "ai-service"
    files = [p for p in sorted(root.rglob("*")) if p.is_file() and p.suffix in TEXT_SUFFIXES] if root.is_dir() else []
    pyfiles = [p for p in files if p.suffix == ".py"]
    print(f"  L2 코드층      ai-service 텍스트 {len(files)}건 (그중 .py {len(pyfiles)}건)")
    if not pyfiles:
        fail("⑧", "ai-service 코드가 0건이다. 'AI 가 계보에 쓰지 않는다'와 'AI 가 아직 없다'는 "
                  "다른 사실이고, 이 게이트는 둘을 구분해야 한다. P0 이후 green 이 될 수 있다.")

    tbl_re = _tbl_re(prefixes)
    kw_re = re.compile("|".join(re.escape(k) for k in kws), re.IGNORECASE)

    for p in pyfiles:
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        except (SyntaxError, UnicodeDecodeError) as e:
            fail("⑤", f"{rel(p)} 파싱 실패 ({e}). 읽지 못한 것은 통과가 아니다.")
            continue
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                names = [node.module or ""]
            for n in names:
                if any(n == b or n.startswith(b + ".") for b in banned_imports):
                    fail("⑤", f"{rel(p)}:{node.lineno} 금지 import `{n}` — "
                              f"ai-service 는 플랫폼 저장소에 손이 닿지 않는다.")

    for p in files:
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if tbl_re.search(line):
                if kw_re.search(line):
                    fail("⑦", f"{rel(p)}:{i} 쓰기 SQL + D4 테이블 — `{line.strip()[:90]}`")
                else:
                    fail("⑥", f"{rel(p)}:{i} D4 테이블 접두사 등장 — `{line.strip()[:90]}` "
                              f"(읽기여도 red 다. D4 는 core-api 의 것이고 ai-service 는 seam 으로만 말한다)")


# ── L3 체인층 ────────────────────────────────────────────────────────────────
def _migrations(d):
    return [p for p in d.rglob("*") if p.is_file() and p.suffix in {".py", ".sql"}
            and p.name != "__init__.py"] if d.is_dir() else []


def check_chains(cfg):
    prefixes = cfg["platform_lineage_tables"]
    ai_dir, pf_dir = DB / "ai", DB / "platform"
    ai_mig, pf_mig = _migrations(ai_dir), _migrations(pf_dir)
    print(f"  L3 체인층      db/ai 마이그레이션 {len(ai_mig)}건 · db/platform {len(pf_mig)}건")
    if not ai_mig or not pf_mig:
        fail("⑫", f"마이그레이션이 없다 (db/ai {len(ai_mig)}건 · db/platform {len(pf_mig)}건). "
                  "체인이 갈라져 있음을 증명할 체인 자체가 아직 없다. P0 이후 green 이 될 수 있다.")

    tbl_re = _tbl_re(prefixes)
    for p in [q for q in (ai_dir.rglob("*") if ai_dir.is_dir() else []) if q.is_file() and q.suffix in TEXT_SUFFIXES]:
        txt = p.read_text(encoding="utf-8", errors="replace")
        for i, line in enumerate(txt.splitlines(), 1):
            if "db/platform" in line or "db.platform" in line:
                fail("⑨", f"{rel(p)}:{i} db/ai 가 플랫폼 체인을 참조한다 — `{line.strip()[:90]}`")
            elif tbl_re.search(line):
                fail("⑨", f"{rel(p)}:{i} db/ai 에 D4 테이블이 나타난다 — `{line.strip()[:90]}`")
    for p in [q for q in (pf_dir.rglob("*") if pf_dir.is_dir() else []) if q.is_file() and q.suffix in TEXT_SUFFIXES]:
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if "db/ai" in line or "db.ai" in line:
                fail("⑩", f"{rel(p)}:{i} db/platform 이 ai 체인을 참조한다 — `{line.strip()[:90]}`")

    # alembic version_table 이 같으면 두 체인이 같은 head 를 공유하게 된다 = 체인 분리 실패.
    vt = {}
    for label, d in (("ai", ai_dir), ("platform", pf_dir)):
        ini = d / "alembic.ini"
        if not ini.is_file():
            fail("⑪", f"{rel(ini)} 가 없다. 독립 체인은 자기 alembic.ini 를 가져야 한다 (CLAUDE.md §3-3).")
            continue
        cp = configparser.ConfigParser()
        cp.read(ini)
        vt[label] = cp.get("alembic", "version_table", fallback=None)
        if not vt[label]:
            fail("⑪", f"{rel(ini)} 에 version_table 이 선언되지 않았다. "
                      "기본값(alembic_version)을 두 체인이 공유하면 체인이 섞인다.")
    if len(vt) == 2 and vt.get("ai") and vt["ai"] == vt.get("platform"):
        fail("⑪", f"두 체인의 version_table 이 같다 ({vt['ai']}). 체인이 갈라져 있지 않다.")


def main():
    if not CONFIG.is_file():
        print(f"::error::ai-no-lineage-write red — 설정이 없다: {CONFIG}")
        return 1
    cfg = tomllib.load(CONFIG.open("rb"))["ai_no_lineage_write"]
    print("# 음성 게이트 — 'D10 → D4 쓰기 경로 없음'을 세 층에서 확인한다")
    check_contract(cfg)
    check_code(cfg)
    check_chains(cfg)
    if FAILS:
        print("::error::ai-no-lineage-write red — 다음이 존재해서는 안 된다:")
        for f in FAILS:
            print(f"     - {f}")
        return 1
    print("ai-no-lineage-write green — 계약·코드·체인 세 층 모두에서 쓰기 경로가 없다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
