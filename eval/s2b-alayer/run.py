#!/usr/bin/env python3
"""S2b 검색 평가셋 **A층 16건** 실행기 — 회차마다 손으로 재현하던 2단 절차를 스크립트로 고정한다.

**왜 있는가.** 직전 회차(`dev-package/sessions/DRIFT3-MEASURE.md §3`)는 A층 16건을 실제로
돌렸고, 그 결과 실패 8건의 **정체가 바뀌어 있었다** — `Q-07` 실패→통과, `Q-08`·`Q-09`
**통과→실패(회귀)**. 원인은 2026-08-27 에 채운 설명 2건이 새 토큰을 넣어 순위를 옮긴 것이다.
**그 회귀를 아무도 못 보고 있었다** — 레포에 A층 실행 수단이 없어 회차마다 손으로 재현했고,
그래서 「언제 나빠졌는가」를 추적할 수 없었다.

**무엇을 하지 않는가.**

- **합격/불합격을 반환하지 않는다.** 2026-08-29 Ted 판정 = 검색 평가셋을 이번 릴리즈 판정
  대상에서 뺀다(의미 검색이 들어오면 지금 실패의 상당수가 놓인 층 자체가 바뀐다). **단, 재는
  것은 남긴다** — 합격선은 걸지 않고 값만 기록한다. 그래서 이 파일은 `gates/` 에 있지 않다.
- **기대값을 고치지 않는다.** `evalset.json` 의 기대는 `S2b-SEARCH-EVALSET.md` 정본을 술어로
  옮긴 것뿐이다. 실물에 맞추려고 기대를 손대는 것이 이 레포가 금지한 「검사 대상 축소」다.
- **판정 불가를 통과로 세지 않는다.** `Q-12` 는 `kind=undecided` 로 남고, 층 밖 `Q-19`·`Q-20`
  은 **미실행 건수로 요약줄에 드러난다.**

**종료 코드는 판정이 아니라 「잴 수 있었는가」다.**

- `0` — A층 16건을 **전건 실행**했다. 항목별 결과와 기준선 대비 변화가 출력에 있다.
- `2` — **못 쟀다.** 컨테이너 부재·1단 실패·SQL 실패·대상 데이터셋 부족·항목 수 불일치.
  **대상 0건도 여기다** — 조용히 0건으로 통과시키지 않는다.

**운영 스택은 읽기 전용이다.** 2단은 `SELECT` 뿐이고, 1단은 컨테이너 안에서 `READ ONLY`
트랜잭션으로 사전 다섯 표를 읽는 `SqlDictionaries.expand` 호출뿐이다(`app/dictionaries.py`).
**컨테이너 안에 파일을 남기지 않는다** — 1단 스크립트는 `python -c`, 입력은 stdin 이다.
접속 문자열·비밀번호를 인자·출력 어디에도 두지 않는다(컨테이너 안의 `Settings.from_env()`
와 `psql` 의 로컬 소켓만 쓴다).

돌리는 법
    python3 eval/s2b-alayer/run.py                     # 값 출력 + 기준선 대조
    python3 eval/s2b-alayer/run.py --repeat 3          # 결정성(회차 안 md5 반복) 확인
    python3 eval/s2b-alayer/run.py --write-baseline    # 이번 값을 기준선으로 박는다
    python3 eval/s2b-alayer/run.py --json out.json     # 원자료를 파일로
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
HERE = pathlib.Path(__file__).resolve().parent
EVALSET = HERE / "evalset.json"
BASELINE = HERE / "baseline.json"
MANIFEST = REPO / "infra" / "staging" / "manifest-s2.json"
CATALOG_PY = REPO / "services" / "core-api" / "src" / "colab_core" / "domains" / "d3_catalog.py"

DEFAULT_PG = "colab_v2_staging_pg"
DEFAULT_AI = "colab_v2_staging_ai_service"
DEFAULT_DB = "colab_platform"
#: RLS 우회 롤. 이 연구실 밖 데이터셋이 0건이라 결과 집합에 영향이 없고, **그래서 `Q-20`
#: (연구실 경계)은 이 경로로 못 잰다** — 층 밖으로 남는 이유가 그것이다.
DEFAULT_ROLE = "postgres"
#: 2단 `LIMIT`. 순위는 `count(*) OVER ()` 가 따로 세므로 잘림은 총건수에 영향이 없고,
#: 실측 최대 집합(9건)보다 넉넉하다. **세는 기준으로 출력에 적힌다.**
SQL_LIMIT = 50


class Unmeasurable(RuntimeError):
    """잴 수 없었다. **통과가 아니라 실패로 끝난다.**"""


# ── 0. 실물에서 SQL 을 꺼낸다 ────────────────────────────────────────────────
# 2단은 「`_SEARCH`·`_SEARCH_TRGM` 과 **동형**」이 아니라 **그 문자열 자체**여야 한다.
# 여기서 SQL 을 다시 적으면 제품이 바뀌었을 때 평가셋만 옛 규칙을 재게 된다.

def _extract(src: str, name: str) -> str:
    m = re.search(name + r'\s*=\s*(?:text\(\s*)?"""(.*?)"""', src, re.S)
    if m is None:
        raise Unmeasurable(f"{CATALOG_PY.name} 에서 {name} 를 못 찾았다 — 제품 SQL 의 모양이 바뀌었다")
    return m.group(1)


def load_product_sql() -> tuple[str, str, float]:
    if not CATALOG_PY.is_file():
        raise Unmeasurable(f"제품 SQL 파일이 없다: {CATALOG_PY}")
    src = CATALOG_PY.read_text(encoding="utf-8")
    prefix = _extract(src, "_PREFIX_TSQUERY")
    # `_SEARCH` 는 원본에서 `_PREFIX_TSQUERY` 를 문자열 이음으로 끼워 넣는다. 그 이음을 그대로 흉내낸다.
    m = re.search(r'_SEARCH\s*=\s*text\("""(.*?)"""\s*\+\s*_PREFIX_TSQUERY\s*\+\s*"""(.*?)"""\)', src, re.S)
    if m is None:
        raise Unmeasurable("_SEARCH 의 조립 모양이 바뀌었다 — 실행기를 실물에 맞춰 고쳐야 한다")
    search = m.group(1) + prefix + m.group(2)
    trgm = _extract(src, "_SEARCH_TRGM")
    t = re.search(r"^TRGM_THRESHOLD\s*=\s*([0-9.]+)", src, re.M)
    if t is None:
        raise Unmeasurable("TRGM_THRESHOLD 를 못 찾았다")
    return search, trgm, float(t.group(1))


def _array_literal(values: list[str]) -> str:
    """`text[]` 리터럴. 사용자 문자열이 아니라 **평가셋 고정값**만 들어오지만 그래도 이스케이프한다."""
    parts = []
    for v in values:
        parts.append('"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"')
    return "'{" + ",".join(parts).replace("'", "''") + "}'"


_PARAM = re.compile(r"(?<!:):(terms|topic|limit|offset|threshold)\b")


def bind(sql: str, terms: list[str], threshold: float) -> str:
    repl = {
        "terms": _array_literal(terms),
        "topic": "NULL",          # DRIFT3 §3.1 과 같은 조건 — 주제 필터 없음
        "limit": str(SQL_LIMIT),
        "offset": "0",
        "threshold": repr(threshold),
    }
    return _PARAM.sub(lambda m: repl[m.group(1)], sql)


# ── 1. 대상 ─────────────────────────────────────────────────────────────────

def docker(container: str, args: list[str], stdin: str | None = None) -> str:
    cmd = ["docker", "exec"] + (["-i"] if stdin is not None else []) + [container] + args
    try:
        p = subprocess.run(cmd, input=stdin, capture_output=True, text=True, timeout=180)
    except FileNotFoundError as e:
        raise Unmeasurable(f"docker 를 못 찾았다: {e}") from e
    except subprocess.TimeoutExpired as e:
        raise Unmeasurable(f"{container} 응답 없음(180s 초과)") from e
    if p.returncode != 0:
        raise Unmeasurable(f"{container} 실행 실패(rc={p.returncode}): {p.stderr.strip()[:400]}")
    return p.stdout


def psql(container: str, db: str, role: str, sql: str) -> list[list[str]]:
    out = docker(container, ["psql", "-U", role, "-d", db, "-At", "-F", "\x1f",
                             "-v", "ON_ERROR_STOP=1", "-q", "-f", "-"], stdin=sql)
    return [line.split("\x1f") for line in out.splitlines() if line != ""]


def load_targets(pg: str, db: str, role: str) -> dict[str, str]:
    """이름 → D 코드. **정본은 적재 매니페스트다** — 실행기가 이름을 다시 적지 않는다."""
    if not MANIFEST.is_file():
        raise Unmeasurable(f"적재 매니페스트가 없다: {MANIFEST}")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    by_name = {d["name"]: d["key"] for d in manifest["datasets"]}
    rows = psql(pg, db, role,
                "SELECT d.id, dd.name FROM d3_dataset d "
                "JOIN d3_dataset_description dd ON dd.dataset_id = d.id "
                "WHERE d.deleted_at IS NULL ORDER BY d.id;")
    if not rows:
        raise Unmeasurable("대상 데이터셋 0건 — 잴 것이 없다. **0건은 통과가 아니다**")
    ids: dict[str, str] = {}
    unknown = []
    for dataset_id, name in rows:
        key = by_name.get(name)
        if key is None:
            unknown.append(name)
        else:
            ids[dataset_id] = key
    missing = sorted(set(by_name.values()) - set(ids.values()))
    if missing:
        raise Unmeasurable(f"매니페스트가 적은 데이터셋이 실물에 없다: {missing} — 이 상태의 값은 평가셋 값이 아니다")
    if unknown:
        raise Unmeasurable(f"매니페스트에 없는 데이터셋이 실물에 있다: {unknown} — 대상 집합이 바뀌었다")
    return ids


# ── 2. 1단 — staging ai-service 실호출 ──────────────────────────────────────

STAGE1 = r'''
import json, sys
from colab_ai.kernel.config import Settings
from colab_ai.kernel.db import make_engine
from colab_ai.app.dictionaries import SqlDictionaries
s = Settings.from_env()
if not s.dict_db_url:
    sys.stderr.write("dict_db_url 미배선 — 사전 확장을 못 잰다\n")
    raise SystemExit(3)
d = SqlDictionaries(make_engine(s.dict_db_url))
out = {}
for it in json.loads(sys.stdin.read()):
    e = d.expand(tuple(it["terms"]), it["query"])
    out[it["id"]] = {"terms": list(e.terms), "topic": e.topic}
sys.stdout.write(json.dumps(out, ensure_ascii=False))
'''


def stage1(ai: str, items: list[dict]) -> dict[str, dict]:
    payload = json.dumps([{"id": i["id"], "terms": i["terms"], "query": i["query"]}
                          for i in items], ensure_ascii=False)
    raw = docker(ai, ["python", "-c", STAGE1], stdin=payload)
    try:
        got = json.loads(raw)
    except json.JSONDecodeError as e:
        raise Unmeasurable(f"1단 산출이 JSON 이 아니다: {raw[:200]!r}") from e
    if set(got) != {i["id"] for i in items}:
        raise Unmeasurable("1단이 일부 질의를 안 냈다 — 건너뛴 채 2단으로 가지 않는다")
    return got


# ── 3. 2단 — 제품 SQL 을 staging colab_platform 에 ──────────────────────────

def stage2(pg: str, db: str, role: str, terms: list[str], ids: dict[str, str],
           search_sql: str, trgm_sql: str, threshold: float) -> dict:
    rows = psql(pg, db, role, bind(search_sql, terms, threshold).strip().rstrip(";") + ";")
    arm = "tsvector"
    if not rows:
        # 보조 팔은 **`tsvector` 가 한 건도 못 잡았을 때만** 돈다 (`〈89〉-㉮②`). 그 성질을
        # 실행기도 지킨다 — 합쳐 돌리면 순위가 유사도에 오염된다.
        arm = "pg_trgm"
        rows = psql(pg, db, role, bind(trgm_sql, terms, threshold).strip().rstrip(";") + ";")
    hits = [{"key": ids[r[0]], "rank": round(float(r[1]), 4)} for r in rows]
    return {"arm": arm, "hits": hits, "count": len(hits),
            "total_count": int(rows[0][-1]) if rows else 0}


# ── 4. 기대 대조 — **판정이 아니라 대조다** ─────────────────────────────────

def compare(check: dict, hits: list[dict]) -> tuple[str, str]:
    """(결과, 한 줄 사유). 결과는 `충족` · `미충족` · `판정보류` 셋이다.

    ⚠ **`충족`/`미충족` 은 합격/불합격이 아니다** — 2026-08-29 Ted 판정으로 이 평가셋에는
    합격선이 걸려 있지 않다. 「정본의 기대문과 실물이 맞는가」의 값일 뿐이다.
    """
    keys = [h["key"] for h in hits]
    kind = check["kind"]
    if kind == "undecided":
        seen = [k for k in check.get("observe", []) if k in keys]
        miss = [k for k in check.get("observe", []) if k not in keys]
        return "판정보류", f"{check['reason']} 관측: 걸린 것 {seen or '없음'} · 안 걸린 것 {miss or '없음'} · 전체 {keys}"
    if kind == "exact_set":
        want, got = set(check["value"]), set(keys)
        if want == got:
            return "충족", f"집합 일치 {sorted(want)}"
        return "미충족", f"기대 {sorted(want)} · 실제 {keys} · 초과 {sorted(got - want)} · 결손 {sorted(want - got)}"
    if kind == "top3_set":
        top3 = keys[:3]
        bad = [k for k in check.get("not_in_top3", []) if k in top3]
        if set(top3) == set(check["value"]) and not bad:
            return "충족", f"상위3 = {top3}"
        return "미충족", f"기대 상위3 {sorted(check['value'])} · 실제 상위3 {top3}" + (f" · 상위3 금지 위반 {bad}" if bad else "") + f" · 전체 {keys}"
    if kind == "rank1_and_set":
        want, got = set(check["value"]), set(keys)
        ok = want == got and keys[:1] == [check["rank1"]]
        return ("충족" if ok else "미충족",
                f"기대 {sorted(want)} · 1위 {check['rank1']} / 실제 {keys}")
    if kind == "top1_and_contains":
        ok = keys[:1] == [check["top1"]] and all(c in keys for c in check["contains"])
        return ("충족" if ok else "미충족",
                f"기대 1위 {check['top1']} · 포함 {check['contains']} / 실제 {keys}")
    raise Unmeasurable(f"모르는 기대 형식: {kind}")


# ── 5. 한 회차 ──────────────────────────────────────────────────────────────

def run_round(cfg, evalset, ids, sqls) -> dict:
    search_sql, trgm_sql, threshold = sqls
    items = evalset["items"]
    exp = stage1(cfg.ai, items)
    out = {}
    for it in items:
        got_terms = exp[it["id"]]["terms"]
        res = stage2(cfg.pg, cfg.db, cfg.role, got_terms, ids, search_sql, trgm_sql, threshold)
        verdict, why = compare(it["check"], res["hits"])
        res.update({
            "expansion": got_terms,
            "expansion_topic": exp[it["id"]]["topic"],
            "expansion_matches_evalset": sorted(got_terms) == sorted(it["expected_expansion"]),
            "verdict": verdict, "why": why,
        })
        out[it["id"]] = res
    return out


def digest(rnd: dict) -> str:
    canon = json.dumps({k: {"arm": v["arm"], "hits": v["hits"], "expansion": v["expansion"]}
                        for k, v in sorted(rnd.items())}, ensure_ascii=False, sort_keys=True)
    return hashlib.md5(canon.encode()).hexdigest()


# ── 6. 출력 ─────────────────────────────────────────────────────────────────

MARK = {"충족": "○", "미충족": "×", "판정보류": "?"}


def report(evalset, rnd, base, cfg, md5s) -> None:
    items = evalset["items"]
    print("═══ S2b 검색 평가셋 A층 — 실측값 ═══")
    print("⚠ 합격선 없음. 2026-08-29 Ted 판정으로 이 평가셋은 이번 릴리즈 판정 대상 밖이다 — 값만 기록한다.")
    print(f"시점 = {datetime.datetime.now().astimezone().isoformat(timespec='seconds')}")
    print(f"세는 기준 = 대상 데이터셋 {cfg.n_targets}건 · 고정 검색어 §2.9.1 무수정 · "
          f"1단 = {cfg.ai} 실호출 · 2단 = {CATALOG_PY.name} 의 _SEARCH/_SEARCH_TRGM 원문 "
          f"(topic 필터 NULL · LIMIT {SQL_LIMIT} · 롤 {cfg.role} — RLS 우회)")
    print(f"결정성 = 2단 포함 전량 {len(md5s)}회 반복 md5 " +
          ("**전회 동일** " if len(set(md5s)) == 1 else "**갈림** ") + str(sorted(set(md5s))))
    print("  ⚠ md5 는 이 실행기의 출력 형식에 대한 값이다 — 회차 간 비교 대상이 아니다(평가셋 §2.10.7).")
    print()
    hdr = f"{'#':<6}{'결과':<7}{'건':>3}  {'팔':<9}{'기준선 대비':<14}내역"
    print(hdr)
    print("─" * 118)
    changes, counts = [], {"충족": 0, "미충족": 0, "판정보류": 0}
    drift = []
    for it in items:
        qid = it["id"]
        r = rnd[qid]
        counts[r["verdict"]] += 1
        prev = (base or {}).get("results", {}).get(qid)
        if prev is None:
            delta = "기준선 없음"
        elif prev["verdict"] != r["verdict"]:
            delta = f"⭑ {prev['verdict']}→{r['verdict']}"
            changes.append((qid, prev["verdict"], r["verdict"]))
        elif [h["key"] for h in prev["hits"]] != [h["key"] for h in r["hits"]]:
            delta = "△ 집합·순위 변화"
            changes.append((qid, "집합·순위", "변화"))
        else:
            delta = "—"
        if not r["expansion_matches_evalset"]:
            drift.append(qid)
        keys = ",".join(f"{h['key']}({h['rank']})" for h in r["hits"]) or "0건"
        print(f"{qid:<6}{MARK[r['verdict']]} {r['verdict']:<5}{r['count']:>3}  {r['arm']:<9}{delta:<14}{keys}")
    print("─" * 118)
    ool = evalset["out_of_layer"]
    print(f"A층 {len(items)}건 실행 — 기대 충족 {counts['충족']} · 미충족 {counts['미충족']} · "
          f"판정보류 {counts['판정보류']} ｜ **미실행 {len(ool)}건**"
          f"({'·'.join(o['id'] for o in ool)}) = `[미확인]` — 통과로 세지 않는다 ｜ B층 16건 미실행")
    for o in ool:
        print(f"    미실행 {o['id']} — {o['사유']}")
    if drift:
        print(f"⚠ 1단 확장이 평가셋 §2.9.1 표와 다른 항목: {drift} — 사전·그래프가 움직였다는 뜻이다")
    print()
    if base:
        print(f"기준선 = {base['시점']} ({base.get('사유', '')})")
        if changes:
            print("★ 기준선 대비 변화 — **이 줄이 이 실행기의 값어치다**")
            for qid, a, b in changes:
                print(f"    {qid}: {a} → {b}")
        else:
            print("★ 기준선 대비 변화 없음.")
        gone = sorted(set(base.get("results", {})) - {i["id"] for i in items})
        if gone:
            print(f"⚠ 기준선에 있는데 이번 평가셋에 없는 항목: {gone}")
    else:
        print("기준선 파일이 없다 — `--write-baseline` 으로 이번 값을 박으면 다음 회차가 회귀를 본다.")
    print()
    for it in items:
        r = rnd[it["id"]]
        if r["verdict"] != "충족":
            print(f"  {it['id']} [{r['verdict']}] {r['why']}")


def main() -> int:
    ap = argparse.ArgumentParser(description="S2b 검색 평가셋 A층 실행기 (판정하지 않는다 — 잰다)")
    ap.add_argument("--pg", default=DEFAULT_PG)
    ap.add_argument("--ai", default=DEFAULT_AI)
    ap.add_argument("--db", default=DEFAULT_DB)
    ap.add_argument("--role", default=DEFAULT_ROLE)
    ap.add_argument("--repeat", type=int, default=1, help="결정성 확인 반복 회수")
    ap.add_argument("--json", metavar="PATH", help="원자료를 이 경로에 쓴다")
    ap.add_argument("--write-baseline", action="store_true")
    ap.add_argument("--baseline-note", default="")
    cfg = ap.parse_args()

    try:
        evalset = json.loads(EVALSET.read_text(encoding="utf-8"))
        if len(evalset["items"]) != 16:
            raise Unmeasurable(f"A층은 16건이다 — 평가셋에 {len(evalset['items'])}건이 있다")
        sqls = load_product_sql()
        ids = load_targets(cfg.pg, cfg.db, cfg.role)
        cfg.n_targets = len(ids)
        rounds = [run_round(cfg, evalset, ids, sqls) for _ in range(max(1, cfg.repeat))]
    except Unmeasurable as e:
        print(f"⛔ 못 쟀다 — {e}", file=sys.stderr)
        print("   건너뛴 것을 통과로 세지 않는다. 이 실행은 **실패**로 끝난다.", file=sys.stderr)
        return 2

    md5s = [digest(r) for r in rounds]
    rnd = rounds[0]
    base = json.loads(BASELINE.read_text(encoding="utf-8")) if BASELINE.is_file() else None
    report(evalset, rnd, base, cfg, md5s)

    payload = {
        "시점": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "세는_기준": {
            "대상_데이터셋": cfg.n_targets, "고정_검색어": "S2b-SEARCH-EVALSET §2.9.1 무수정",
            "1단": f"{cfg.ai} 컨테이너 SqlDictionaries.expand 실호출",
            "2단": f"{CATALOG_PY.name} _SEARCH/_SEARCH_TRGM 원문 · topic=NULL · LIMIT {SQL_LIMIT}",
            "롤": f"{cfg.role} (RLS 우회 — Q-20 은 이 경로로 못 잰다)",
            "반복": len(md5s), "md5": md5s,
        },
        "미실행": [o["id"] for o in evalset["out_of_layer"]] + ["B층 16건"],
        "results": rnd,
    }
    if cfg.json:
        pathlib.Path(cfg.json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n원자료 → {cfg.json}")
    if cfg.write_baseline:
        payload["사유"] = cfg.baseline_note or "이 회차 실측"
        BASELINE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n기준선 갱신 → {BASELINE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
