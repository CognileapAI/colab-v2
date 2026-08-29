#!/usr/bin/env python3
"""2세대 검색 평가셋 실행기 — **데이터에서 뽑은 기대**와 제품 검색 경로의 실측을 대조한다.

**1세대(`eval/s2b-alayer/`)와의 관계.** 1세대는 지우지 않는다. 그쪽의 기대는 산문 정본을 옮긴
것이고, 그 산문이 설명 본문 적재보다 앞서 쓰였다는 것이 직전 회차 판정에서 드러났다
(`dev-package/sessions/K4-ALAYER-ADJUDICATION.md`). 건별로 기대를 고치면 같은 노후를 회차마다
다시 다투게 되므로 **세대를 갈랐다.** 두 세대의 기준선·판정 기록은 둘 다 남는다.

**이 실행기가 지키는 한 가지.** 기대는 `derive.py` 가 **적재된 이름·주제·설명과 사전 확장**에서
계산한 것뿐이다. 이 실행기는 기대를 만들지 않고, 제품 결과를 보고 기대를 고치지도 않는다.
시작할 때 **커밋된 기대가 지금 실물과 같은지 다시 도출해 대조**하고, 다르면 **못 쟀다로 끝난다.**

종료 코드는 판정이 아니라 「잴 수 있었는가」다.

- `0` — 전건 실행했다. 판정은 출력에 있다.
- `2` — 못 쟀다(컨테이너 부재 · 사전 미배선 · SQL 실패 · 대상 0건 · 제품 SQL 모양 변경 ·
  **커밋된 기대와 실물 불일치**). 건너뛴 것을 통과로 세지 않는다.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import common as C


# ── 제품 SQL 을 실물에서 꺼낸다(베껴 적으면 평가셋만 옛 규칙을 재게 된다) ──

def _extract(src: str, name: str) -> str:
    m = re.search(name + r'\s*=\s*(?:text\(\s*)?"""(.*?)"""', src, re.S)
    if m is None:
        raise C.Unmeasurable(f"{C.CATALOG_PY.name} 에서 {name} 를 못 찾았다 — 제품 SQL 의 모양이 바뀌었다")
    return m.group(1)


def load_product_sql() -> tuple[str, str, float]:
    if not C.CATALOG_PY.is_file():
        raise C.Unmeasurable(f"제품 SQL 파일이 없다: {C.CATALOG_PY}")
    src = C.CATALOG_PY.read_text(encoding="utf-8")
    prefix = _extract(src, "_PREFIX_TSQUERY")
    m = re.search(r'_SEARCH\s*=\s*text\("""(.*?)"""\s*\+\s*_PREFIX_TSQUERY\s*\+\s*"""(.*?)"""\)', src, re.S)
    if m is None:
        raise C.Unmeasurable("_SEARCH 의 조립 모양이 바뀌었다 — 실행기를 실물에 맞춰 고쳐야 한다")
    t = re.search(r"^TRGM_THRESHOLD\s*=\s*([0-9.]+)", src, re.M)
    if t is None:
        raise C.Unmeasurable("TRGM_THRESHOLD 를 못 찾았다")
    return m.group(1) + prefix + m.group(2), _extract(src, "_SEARCH_TRGM"), float(t.group(1))


def _array_literal(values: list[str]) -> str:
    parts = ['"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"' for v in values]
    return "'{" + ",".join(parts).replace("'", "''") + "}'"


_PARAM = re.compile(r"(?<!:):(terms|topic|limit|offset|threshold)\b")


def bind(sql: str, terms: list[str], threshold: float) -> str:
    repl = {"terms": _array_literal(terms), "topic": "NULL", "limit": str(C.SQL_LIMIT),
            "offset": "0", "threshold": repr(threshold)}
    return _PARAM.sub(lambda m: repl[m.group(1)], sql)


def search(cfg, terms, ids, search_sql, trgm_sql, threshold) -> dict:
    rows = C.psql(cfg.pg, cfg.db, cfg.role, bind(search_sql, terms, threshold).strip().rstrip(";") + ";")
    arm = "tsvector"
    if not rows:
        # 보조 팔은 tsvector 팔이 한 건도 못 잡았을 때만 돈다. 합쳐 돌리면 순위가 유사도에 오염된다.
        arm = "pg_trgm"
        rows = C.psql(cfg.pg, cfg.db, cfg.role, bind(trgm_sql, terms, threshold).strip().rstrip(";") + ";")
    return {"arm": arm, "hits": [{"key": ids[r[0]], "rank": round(float(r[1]), 4)} for r in rows]}


# ── 대조 ────────────────────────────────────────────────────────────────────

def compare(item: dict, keys: list[str]) -> tuple[str, str]:
    """(판정, 사유). 판정은 `통과` · `실패` · `범위 밖` 셋이다. **범위 밖은 통과로 세지 않는다.**"""
    kind = item["kind"]
    if kind == "out_of_scope":
        return "범위 밖", f"{item['derivation']['사유']} 관측: {keys or '0건'}"
    if kind == "derived_exact":
        want, got = set(item["expected"]), set(keys)
        if want == got:
            return "통과", f"집합 일치 {sorted(want)}"
        return "실패", (f"데이터에서 뽑은 기대 {sorted(want)} · 실제 {keys} · "
                       f"초과 {sorted(got - want)} · 결손 {sorted(want - got)}")
    if kind == "derived_bounds":
        lo, hi, got = set(item["expected"]["하계"]), set(item["expected"]["상계"]), set(keys)
        over, under = sorted(got - hi), sorted(lo - got)
        if not over and not under:
            return "통과", f"경계 안 — 하계 {sorted(lo)} ⊆ 실제 {keys} ⊆ 상계 {sorted(hi)}"
        return "실패", f"상계 밖 {over} · 하계 결손 {under} · 실제 {keys} (결합 규칙과 무관하게 어긋난 것이다)"
    if kind == "derived_field_order":
        pos = {k: i for i, k in enumerate(keys)}
        front = [k for k in item["expected"]["앞"] if k in pos]
        back = [k for k in item["expected"]["뒤"] if k in pos]
        if not front or not back:
            return "실패", f"순위를 비교할 두 쪽 중 하나가 결과에 없다 — 앞 {front} · 뒤 {back} · 실제 {keys}"
        bad = [(a, b) for a in front for b in back if pos[a] > pos[b]]
        if bad:
            return "실패", f"이름 매칭이 본문 매칭보다 뒤에 온 쌍 {bad} · 실제 {keys}"
        return "통과", f"이름 매칭 {front} 가 본문 매칭 {back} 보다 앞선다 · 실제 {keys}"
    raise C.Unmeasurable(f"모르는 기대 갈래: {kind}")


def digest(results: dict) -> str:
    canon = json.dumps({k: {"arm": v["arm"], "hits": v["hits"]} for k, v in sorted(results.items())},
                       ensure_ascii=False, sort_keys=True)
    return hashlib.md5(canon.encode()).hexdigest()


MARK = {"통과": "○", "실패": "×", "범위 밖": "▷"}


def main() -> int:
    ap = argparse.ArgumentParser(description="2세대 검색 평가셋 실행기")
    ap.add_argument("--pg", default=C.DEFAULT_PG)
    ap.add_argument("--ai", default=C.DEFAULT_AI)
    ap.add_argument("--db", default=C.DEFAULT_DB)
    ap.add_argument("--role", default=C.DEFAULT_ROLE)
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--json", metavar="PATH")
    ap.add_argument("--write-baseline", action="store_true")
    ap.add_argument("--baseline-note", default="")
    cfg = ap.parse_args()

    try:
        if not C.EVALSET.is_file():
            raise C.Unmeasurable(f"기대 파일이 없다: {C.EVALSET} — `derive.py --write` 를 먼저 돌린다")
        evalset = json.loads(C.EVALSET.read_text(encoding="utf-8"))
        cases_doc = json.loads(C.CASES.read_text(encoding="utf-8"))
        sqls = load_product_sql()
        data, ids = C.measure_ground_truth(cfg.pg, cfg.db, cfg.role)
        expansions = C.measure_expansion(cfg.ai, cases_doc["cases"])
        fresh = C.build_evalset(cases_doc, data, expansions)
        if json.dumps(fresh["items"], ensure_ascii=False, sort_keys=True) != \
           json.dumps(evalset["items"], ensure_ascii=False, sort_keys=True):
            raise C.Unmeasurable(
                "커밋된 기대와 지금 실물에서 뽑은 기대가 다르다 — 적재분이나 사전이 움직였다. "
                "`derive.py --write` 로 다시 뽑고 무엇이 달라졌는지 회차 문서에 적는다. "
                "**제품 결과에 맞춰 기대를 고치는 것이 아니다**")
        rounds = []
        for _ in range(max(1, cfg.repeat)):
            rounds.append({it["id"]: search(cfg, it["expansion"], ids, *sqls) for it in evalset["items"]})
    except C.Unmeasurable as e:
        print(f"⛔ 못 쟀다 — {e}", file=sys.stderr)
        print("   건너뛴 것을 통과로 세지 않는다. 이 실행은 **실패**로 끝난다.", file=sys.stderr)
        return 2

    md5s = [digest(r) for r in rounds]
    res = rounds[0]
    base = json.loads(C.BASELINE.read_text(encoding="utf-8")) if C.BASELINE.is_file() else None
    gt = evalset["ground_truth"]

    print("═══ 검색 평가셋 2세대 — 데이터에서 뽑은 기대 대비 실측 ═══")
    print(f"시점 = {datetime.datetime.now().astimezone().isoformat(timespec='seconds')}")
    print(f"기대 도출 시점 = {evalset.get('도출_시점', '[미확인]')} (실행 직전 재도출해 동일함을 확인했다)")
    print(f"세는 기준 = 대상 데이터셋 {gt['대상_데이터셋']}건 · 최신 설명 갱신 {gt['최신_설명_갱신시각']} · "
          f"1단 {cfg.ai} 사전 실호출 · 2단 {C.CATALOG_PY.name} 원문 (topic=NULL · LIMIT {C.SQL_LIMIT} · 롤 {cfg.role})")
    print(f"결정성 = {len(md5s)}회 반복 md5 " + ("전회 동일" if len(set(md5s)) == 1 else f"갈림 {sorted(set(md5s))}"))
    print()
    print(f"{'#':<6}{'판정':<8}{'건':>3}  {'팔':<9}{'기준선':<14}결과")
    print("─" * 118)
    counts = {"통과": 0, "실패": 0, "범위 밖": 0}
    changes, verdicts = [], {}
    for it in evalset["items"]:
        qid = it["id"]
        keys = [h["key"] for h in res[qid]["hits"]]
        verdict, why = compare(it, keys)
        verdicts[qid] = {"verdict": verdict, "why": why, **res[qid]}
        counts[verdict] += 1
        prev = (base or {}).get("results", {}).get(qid)
        if prev is None:
            delta = "기준선 없음"
        elif prev["verdict"] != verdict:
            delta = f"⭑ {prev['verdict']}→{verdict}"
            changes.append(f"{qid}: {prev['verdict']} → {verdict}")
        elif [h["key"] for h in prev["hits"]] != keys:
            delta = "△ 집합·순위 변화"
            changes.append(f"{qid}: 집합·순위 변화")
        else:
            delta = "—"
        print(f"{qid:<6}{MARK[verdict]} {verdict:<6}{len(keys):>3}  {res[qid]['arm']:<9}{delta:<14}"
              + (",".join(f"{h['key']}({h['rank']})" for h in res[qid]['hits']) or "0건"))
    print("─" * 118)
    print(f"{len(evalset['items'])}건 실행 — 통과 {counts['통과']} · 실패 {counts['실패']} · "
          f"범위 밖 {counts['범위 밖']} (범위 밖은 통과로 세지 않는다) ｜ 미판정 0")
    print("미실행 = 검색 중단 시 응답 · 연구실 경계 · 자연어 해석 층 — `[미확인]`, 통과가 아니다")
    if changes:
        print("★ 기준선 대비 변화")
        for c in changes:
            print(f"    {c}")
    elif base:
        print(f"★ 기준선({base['시점']}) 대비 변화 없음")
    else:
        print("기준선 파일이 없다 — `--write-baseline` 으로 박으면 다음 회차가 회귀를 본다")
    print()
    for it in evalset["items"]:
        if verdicts[it["id"]]["verdict"] != "통과":
            print(f"  {it['id']} [{verdicts[it['id']]['verdict']}] {verdicts[it['id']]['why']}")

    payload = {"시점": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
               "세는_기준": {"대상_데이터셋": gt["대상_데이터셋"], "최신_설명_갱신시각": gt["최신_설명_갱신시각"],
                             "반복": len(md5s), "md5": md5s},
               "미실행": ["검색 중단 시 응답", "연구실 경계", "자연어 해석 B층"],
               "results": verdicts}
    if cfg.json:
        pathlib.Path(cfg.json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n원자료 → {cfg.json}")
    if cfg.write_baseline:
        payload["사유"] = cfg.baseline_note or "이 회차 실측"
        C.BASELINE.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"\n기준선 갱신 → {C.BASELINE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
