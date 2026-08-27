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
  L3 체인층  db/ai 와 db/platform 이 갈라져 있을 것 (**주석·독스트링은 참조가 아니다** — 아래 참조)
             red 조건 ⑨  db/ai 아래 파일이 db/platform(또는 D4 테이블)을 참조
                     ⑩  db/platform 아래 파일이 db/ai 를 참조
                     ⑪  두 체인의 alembic version_table 이 같거나 한쪽이 없다
                     ⑫  두 체인 중 하나라도 마이그레이션이 0건이다 → 증명 대상 미존재 = red

**⑨⑩ 이 산문을 참조로 세지 않는 이유** (`PLAN-SoT §9 〈172〉`): 산문은 코드 경로를 만들지 못한다.
`db/ai/ai_db_url.py` 의 모듈 독스트링은 "platform 체인과 공유하지 말라"는 **경고문**인데,
줄 단위 문자열 매칭이 그 경고문 안의 다른 체인 경로를 참조로 읽어 red 를 냈다 — 오탐이다.
그래서 ⑨⑩ 은 **주석과 독스트링만** 공백으로 지운 뒤 남은 텍스트를 본다. 검사 대상을 줄이는 것이 아니다:

  - 주석이 **같은 줄 뒤에** 붙어 있어도 앞쪽 코드는 그대로 검사된다 (꼬리 주석 마스킹은 주석 부분만)
  - 주석 블록 **바로 다음 줄**은 조금도 지워지지 않는다
  - **독스트링이 아닌 문자열 리터럴은 지우지 않는다.** `importlib.import_module("db.platform.x")` 처럼
    문자열이 실제 경로를 만들 수 있기 때문이다. 지우는 것은 **아무도 실행하지 않는 산문** 뿐이다
  - 파이썬이 파싱조차 안 되면 마스킹을 포기하고 **원문 그대로** 검사한다 (fail-closed)

**대상 0건을 green 으로 세지 않는 이유**: 음성 명제는 대상이 없으면 공허하게 참이다.
"AI 가 계보에 쓰지 않는다"와 "AI 가 아직 없다"는 다른 사실이고, 게이트가 둘을 구분하지 못하면
그게 green-by-skip 이다 (v1 CI 가 DB 없이 RLS 테스트를 통과시킨 것과 같은 실패).

환경변수 (selftest 전용)
  COLAB_SEAM_DIR · COLAB_SERVICES_DIR · COLAB_DB_DIR · COLAB_BOUNDARY_CONFIG
"""
import ast
import configparser
import io
import os
import pathlib
import re
import sys
import tokenize
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


# ── 주석·독스트링 마스킹 (⑨⑩ 전용) ─────────────────────────────────────────
# 원칙: **지우는 것은 산문뿐이다.** 문자열 리터럴(독스트링 제외)·코드는 한 글자도 지우지 않는다.
# 지운 자리는 공백으로 채워 줄 번호와 열 위치를 보존한다 — 신고 줄 번호가 어긋나면 안 된다.

#: 확장자별 주석 문법. (줄 주석 토큰, 블록 주석 (열림, 닫힘) 목록)
_COMMENT_SYNTAX = {
    ".sql": (["--"], [("/*", "*/")]),
    ".ini": (["#", ";"], []),
    ".cfg": (["#", ";"], []),
    ".toml": (["#"], []),
    ".yaml": (["#"], []),
    ".yml": (["#"], []),
    ".mako": (["##"], [("<%doc>", "</%doc>")]),
}


def _blank_spans(text, spans):
    """(시작(행,열), 끝(행,열)) 구간을 공백으로 지운다. 줄바꿈은 남긴다."""
    lines = text.splitlines(keepends=True)
    buf = [list(l) for l in lines]
    for (sr, sc), (er, ec) in spans:
        for r in range(sr, er + 1):
            if not (1 <= r <= len(buf)):
                continue
            row = buf[r - 1]
            lo = sc if r == sr else 0
            hi = ec if r == er else len(row)
            for c in range(max(lo, 0), min(hi, len(row))):
                if row[c] != "\n":
                    row[c] = " "
    return "".join("".join(r) for r in buf)


def _mask_python(text):
    """파이썬 주석 + **독스트링**만 지운다. 실패하면 None (원문으로 검사)."""
    spans = []
    try:
        for t in tokenize.generate_tokens(io.StringIO(text).readline):
            if t.type == tokenize.COMMENT:
                spans.append((t.start, t.end))
        tree = ast.parse(text)
    except (tokenize.TokenError, SyntaxError, IndentationError, ValueError):
        return None
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not body or not isinstance(body[0], ast.Expr):
            continue
        v = body[0].value
        if isinstance(v, ast.Constant) and isinstance(v.value, str) and v.end_lineno is not None:
            spans.append(((v.lineno, v.col_offset), (v.end_lineno, v.end_col_offset)))
    return _blank_spans(text, spans)


def _mask_generic(text, suffix):
    """따옴표를 인식하며 줄/블록 주석만 지운다. 문법을 모르는 확장자는 원문 그대로."""
    syntax = _COMMENT_SYNTAX.get(suffix)
    if not syntax:
        return text
    line_toks, block_toks = syntax
    out = list(text)
    i, n = 0, len(text)
    quote = None
    at_line_start = True
    while i < n:
        ch = text[i]
        if quote:
            if ch == "\\" and quote in ("'", '"'):
                i += 2
                continue
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch in ("'", '"'):
            quote = ch
            i += 1
            at_line_start = False
            continue
        if ch == "\n":
            at_line_start = True
            i += 1
            continue
        hit = None
        for op, cl in block_toks:
            if text.startswith(op, i):
                end = text.find(cl, i + len(op))
                end = n if end < 0 else end + len(cl)
                hit = end
                break
        if hit is not None:
            for k in range(i, hit):
                if out[k] != "\n":
                    out[k] = " "
            i = hit
            continue
        prev_ws = at_line_start or (i > 0 and text[i - 1] in " \t")
        for tok in line_toks:
            # `#`·`;` 는 앞이 공백이거나 줄 머리일 때만 주석이다 (URL 의 `#` 를 잘라내지 않는다).
            if text.startswith(tok, i) and (tok.startswith("-") or prev_ws):
                eol = text.find("\n", i)
                eol = n if eol < 0 else eol
                for k in range(i, eol):
                    out[k] = " "
                i = eol
                hit = True
                break
        if hit:
            continue
        if not ch.isspace():
            at_line_start = False
        i += 1
    return "".join(out)


def code_text(path, text):
    """⑨⑩ 이 볼 텍스트 — 주석·독스트링을 지운 판. 지우지 못하면 원문(fail-closed)."""
    if path.suffix == ".py":
        masked = _mask_python(text)
        return text if masked is None else masked
    return _mask_generic(text, path.suffix)


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
    # 산문(주석·독스트링)은 코드 경로가 아니다 — 지운 판에서 찾고, 신고는 원문 줄로 한다.
    for p in [q for q in (ai_dir.rglob("*") if ai_dir.is_dir() else []) if q.is_file() and q.suffix in TEXT_SUFFIXES]:
        raw = p.read_text(encoding="utf-8", errors="replace")
        raw_lines = raw.splitlines()
        for i, line in enumerate(code_text(p, raw).splitlines(), 1):
            src = raw_lines[i - 1].strip()[:90] if i <= len(raw_lines) else line.strip()[:90]
            if "db/platform" in line or "db.platform" in line:
                fail("⑨", f"{rel(p)}:{i} db/ai 가 플랫폼 체인을 참조한다 — `{src}`")
            elif tbl_re.search(line):
                fail("⑨", f"{rel(p)}:{i} db/ai 에 D4 테이블이 나타난다 — `{src}`")
    for p in [q for q in (pf_dir.rglob("*") if pf_dir.is_dir() else []) if q.is_file() and q.suffix in TEXT_SUFFIXES]:
        raw = p.read_text(encoding="utf-8", errors="replace")
        raw_lines = raw.splitlines()
        for i, line in enumerate(code_text(p, raw).splitlines(), 1):
            src = raw_lines[i - 1].strip()[:90] if i <= len(raw_lines) else line.strip()[:90]
            if "db/ai" in line or "db.ai" in line:
                fail("⑩", f"{rel(p)}:{i} db/platform 이 ai 체인을 참조한다 — `{src}`")

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
