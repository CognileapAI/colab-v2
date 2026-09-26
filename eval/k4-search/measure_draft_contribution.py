"""초안(규칙 추론) 검색 사실의 **기여**를 경로 1·경로 2 따로 잰다 — `measure_evidence.py` 의 짝.

정본: `dev-package/intent/2026-09-21-evidence-promotion.md`(승인 2026-09-25, 결정 1–7 전부 권고대로).

무엇을 재나
  일회용 DB 의 **한 트랜잭션** 안에서 생성물 payload 의 `draftFacts` 를 각 데이터셋 본체 파일의
  reviewed `facts` 에 겹쳐 쓰고(합본), 케이스 전량을 두 경로로 평가한다. 그다음 초안을 **규칙 ID
  단위로 하나씩**, 이어서 **사실 하나씩** 빼며 다시 평가하고 끝에 **rollback** 한다. DB 에 초안을
  영속하지 않는다(측정 전후 `(file_id, revision, status, source_sha256, facts)` 지문을 대조한다).

  · 경로 1 = `client_search.plan_query` → `d3_client_search.candidates`(→ `client_search.evaluate`).
    실무자 probe 는 조건 집합이 곧 경로 1 술어라 `candidates` 에 바로 넣는다. 골든·heldout 질의는
    `plan_query` 가 알아들은(recognized) 것만 경로 1 로 간다 — 제품의 갈림(`routes/catalog.py`)과 같다.
  · 경로 2 = (녹화 해석 `interpret-fixture.json`) → `search_evidence_conditions.parse(query)` →
    `read_reviewed` 모양의 행 → `search_evidence_conditions.candidates` → `d3_catalog.search_datasets`.
    `routes/catalog.py` 의 경로 2 블록을 **도메인·순수 함수 호출로 재현**한다 — 라우트(HTTP 층)는
    부르지 않고 제품 코드는 한 줄도 고치지 않는다. 재현이므로 라우트가 바뀌면 이 파일도 따라가야
    한다(차이는 README 「초안 사실 기여 측정」 절의 한계에 적었다). 측정 중 모델을 부르지 않는다.
  · green — 골든: `golden_baseline.assess` 가 pass. probe: expectSeq ⊆ 결과 · forbidSeq ∩ 결과 = ∅ ·
    expectEmpty 면 결과 0건. 기여 = 빼면 green→fail 인 케이스 수, 역전 = 빼면 fail→green 인 케이스 수.
    순위(rank_delta)는 기록만 한다(결정 2).
  · 제외 — `maxMissingRatePercent` probe 는 `d3_dataset_variable` 을 읽어 근거 사실과 독립이다
    → 「근거 독립·제외」. 골든 `manual` 문항은 assess 가 판정하지 않는다 → 제외. heldout 은 승격
    근거에서 빼고 **사후 확인 열**로만 낸다(intent 위험 절).
  · 경로 1 오라클 — practitioner-conditions.json 의 `probes` 와 `measureOnlyProbes`(초안 값 측정 전용 ·
    정답 주장 아님 · 2026-09-26 Ted 「전부 권고대로」). `supersedes` 가 있는 measure_only probe 는 초안
    보류 때문에 기대가 바뀐 기존 probe 를 측정에서 대신한다.

**제품 코드가 아니다. 일회용 DB 전용이다.** localhost·127.0.0.1 이 아닌 URL 은 거절한다
(도커 브리지 IP 로만 닿는 게이트용 컨테이너는 `--i-know-this-is-disposable` 로 명시한다).
DEV·운영 DB 에 대지 않는다(결정 7).

쓰는 법
  # ① 일회용 DB 에 DEV 와 같은 28건(스냅숏 v2 · 본체 543)과 **dev 적재와 같은 payload** 를 싣고 잰다
  services/core-api/.venv/bin/python eval/k4-search/measure_draft_contribution.py <app-role-url> \\
      --seed-dev-like --output <새 디렉터리> [--i-know-this-is-disposable]
  # ② 승격 리허설 — 규칙 하나를 병합한 PUT 본문을 만들어 대조만 한다(보내지 않는다)
  services/core-api/.venv/bin/python eval/k4-search/measure_draft_contribution.py <app-role-url> \\
      --rehearse-promote platform-from-instrument [--i-know-this-is-disposable]

종료코드: 0 표를 냈다 · 1 판정 실패(지문 불일치·리허설에서 reviewed 사실 누락) ·
78 준비 실패(인자 없음 · DB 에 못 닿음 · 일회용이 아닌 URL · 입력 부재).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import pathlib
import re
import subprocess
import sys
from urllib.parse import urlsplit

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
CORE_SRC = REPO / "services" / "core-api" / "src"
TOOLS = REPO / "dev-package" / "tools"
DEFAULT_PAYLOAD = TOOLS / "generated" / "dataset-evidence-payloads.json"
SNAPSHOT_V2 = HERE / "fixtures" / "reference" / "dev-data-snapshot-v2.json"
SNAPSHOT_V1 = HERE / "fixtures" / "reference" / "dev-data-snapshot.json"
GOLDEN = HERE / "golden-cases.json"
PRACTITIONER = HERE / "practitioner-conditions.json"
HELDOUT = HERE / "heldout-cases.json"
INTERPRET_FIXTURE = HERE / "interpret-fixture.json"

#: 일회용 DB 의 시드 주체(`services/core-api/tests/fixtures/seed.sql` 의 A 연구실 · 소유 연구원).
LAB = "0000000000000000000000000A"
ACCOUNT = "000000000000000000000000A1"
#: `plan_query` 의 「작년」·「이번 달」을 고정한다 — 측정이 날짜에 따라 흔들리지 않게.
PLAN_NOW = dt.datetime(2026, 9, 25, tzinfo=dt.timezone(dt.timedelta(hours=9)))
#: 경로 2 가 `search_datasets` 에 넘기는 창. API 골든 회귀(`test_search_reference_evidence.py`)와 같다.
SEARCH_LIMIT = 100

#: 결정 5 가 심사하는 규칙 4개 + 보조 1개. payload 의 나머지 규칙도 표에 싣되 이 순서가 앞선다.
FOCUS_RULES = ("platform-from-instrument", "representation-from-shape",
               "direct-observation-from-level", "interpolated-from-lineage",
               "bbox-korea-peninsula")
#: 결정 5 축자 — 「interpolated-from-lineage 는 「미측정(경로 1)·보류」로 고정한다」.
FIXED_HOLD_RULES = {"interpolated-from-lineage"}

#: 경로 1 이 **읽을 수 있는** 사실 성분(`d3_client_search.candidates` 의 file_checks).
PATH_A_FACT_KEYS = frozenset({"platform", "provider", "representation", "cadence",
                              "directObservation", "variable", "region", "format",
                              "nativeResolutionM", "period", "statistics"})
#: 경로 2 가 읽을 수 있는 사실 성분(`search_evidence_conditions.assess`).
PATH_B_FACT_KEYS = frozenset({"model", "variable", "cadence", "directObservation",
                              "nativeResolutionM", "interpolated", "roles", "region", "period"})
#: 경로 1 술어 → 그 술어가 읽는 사실 성분.
A_CONDITION_READS = {"maxResolutionM": "nativeResolutionM", "coverageYear": "period",
                     "exactPeriod": "period"}
#: 근거 사실과 독립인 술어(`d3_dataset_variable` 을 읽는다) — 기여 측정에서 뺀다.
EVIDENCE_INDEPENDENT = frozenset({"maxMissingRatePercent"})
#: heldout 조건 문항의 condition → `search_evidence_conditions.assess` 의 라벨·성분.
HELDOUT_CONDITION = {"period": ("기간", "period"), "interpolation": ("보간", "interpolated"),
                     "direct_observation": ("직접 관측", "directObservation")}

DECISION_GROUPS = ("A", "B")
SIDE_GROUPS = ("heldout_A", "heldout_B")


class Refused(Exception):
    """준비 실패 — 판정할 수 없다(종료코드 78)."""


# ─────────────────────────────── 순수 부분 (DB 없음) ───────────────────────────────

def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_pure(name: str, path: pathlib.Path):
    """stdlib 만 쓰는 모듈을 **파일 경로로** 싣는다 — 패키지 `__init__`(fastapi)을 타지 않는다."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def conditions_module():
    return load_pure("k4_search_evidence_conditions",
                     CORE_SRC / "colab_core" / "app" / "search_evidence_conditions.py")


def terms_module():
    return load_pure("k4_search_conditions", CORE_SRC / "colab_core" / "app" / "search_conditions.py")


def golden_assess():
    return load_pure("k4_golden_baseline", HERE / "golden_baseline.py").assess


def check_disposable_url(url: str, override: bool) -> str | None:
    """일회용이 아닌 DB 면 거절 사유를 돌려준다. None 이면 통과."""
    try:
        host = urlsplit(url).hostname
    except ValueError:
        return "DB URL 을 읽지 못했다"
    if host in ("localhost", "127.0.0.1", "::1"):
        return None
    if override:
        return None
    return (f"일회용 DB 가 아닐 수 있는 호스트다({host!r}) — localhost·127.0.0.1 만 받는다. "
            "게이트용 일회용 컨테이너(도커 브리지 IP)라면 --i-know-this-is-disposable 로 명시한다. "
            "DEV·운영 DB 에는 대지 않는다(intent 결정 7).")


def draft_facts(payload: dict) -> list[dict]:
    """payload 의 draftFacts 를 사실 단위로 편다. 규칙 ID 는 draftProvenance 의 rule:<ID> 에서 온다."""
    out = []
    for row in payload["datasets"]:
        for key, value in (row.get("draftFacts") or {}).items():
            found = re.search(r"rule:([A-Za-z0-9_-]+)", row["draftProvenance"].get(key, ""))
            if not found:
                raise Refused(f"seq {row['seq']} {key}: draftProvenance 에 rule:<ID> 가 없다")
            listed = {c["key"] for c in row.get("draftConflictsWithReviewed") or []}
            if key in (row.get("facts") or {}) and key not in listed:
                raise Refused(f"seq {row['seq']} {key}: 초안이 reviewed 와 겹치는데 draftConflictsWithReviewed 에 "
                              "적혀 있지 않다 — 생성기가 공존을 선언하지 않은 겹침이다")
            out.append({"fact_id": f"seq{row['seq']:02d}.{key}", "seq": row["seq"],
                        "name": row["name"], "key": key, "value": value, "rule": found[1],
                        "replacesReviewed": key in listed})
    return out


def rule_order(payload: dict, facts: list[dict]) -> list[str]:
    declared = list(payload.get("ruleSummary") or {}) or sorted({f["rule"] for f in facts})
    return [*FOCUS_RULES, *[r for r in declared if r not in FOCUS_RULES]]


def probe_green(probe: dict, seqs: list[int]) -> bool:
    got = set(seqs)
    if probe.get("expectEmpty"):
        return not got
    return set(probe["expectSeq"]) <= got and not (set(probe["forbidSeq"]) & got)


def probe_ranks(probe: dict, seqs: list[int]) -> dict:
    return {str(s): (seqs.index(s) + 1 if s in seqs else None) for s in probe["expectSeq"]}


def probe_reads(conditions: dict) -> frozenset:
    return frozenset(A_CONDITION_READS.get(k, k) for k in conditions)


def criteria_reads(criteria: dict) -> frozenset:
    """경로 2 는 topic 이 서고 unsupported 가 아닐 때만 사실을 읽는다(`candidates` 첫 줄)."""
    if not criteria.get("topic") or criteria.get("unsupported"):
        return frozenset()
    return frozenset(k for k in criteria if k in PATH_B_FACT_KEYS)


def compare(with_res: dict, without_res: dict) -> dict:
    """한 경로·한 케이스군에서 사실(들)을 뺐을 때의 뒤집힘."""
    flipped = sorted(c for c, v in with_res.items() if v["green"] and not without_res[c]["green"])
    reversal = sorted(c for c, v in with_res.items() if not v["green"] and without_res[c]["green"])
    ranks = {c: {"with": v["ranks"], "without": without_res[c]["ranks"]}
             for c, v in with_res.items() if v["ranks"] != without_res[c]["ranks"]}
    return {"green_with": sum(v["green"] for v in with_res.values()),
            "green_without": sum(v["green"] for v in without_res.values()),
            "flipped": flipped, "reversal": reversal, "rank_delta": ranks}


def measured(path: str, keys: set, case_reads: dict) -> str:
    readable = PATH_A_FACT_KEYS if path == "A" else PATH_B_FACT_KEYS
    if not keys:
        return "미측정(초안 0건)"
    if not keys & readable:
        return "미측정(술어 없음)"
    touching = [c for c, reads in case_reads.get(path, {}).items() if reads & keys]
    if not touching:
        return "미측정(케이스 0)"
    return f"측정({len(touching)}케이스)"


def suggest_fact(row: dict) -> str:
    """결정 3 — 1회차에는 회차 이력이 없으므로 승격·폐기(기여 0)는 「1회차 관측」으로만 낸다."""
    if row["reversal_A"] or row["reversal_B"]:
        return "폐기 제안 — 역전(결정 3: 회차와 무관하게 즉시)"
    if not any(row[f"measured_{p}"].startswith("측정") for p in DECISION_GROUPS):
        return "미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님)"
    cases = len(set(row["flipped_case_ids_A"]) | set(row["flipped_case_ids_B"]))
    if cases >= 2:
        return "1회차 관측 — 승격 케이스 기준(N=2) 충족 · 2회차 동일 방향 필요"
    if cases == 1:
        return "1회차 관측 — 기여 1(N=2 미달) · 보류"
    return "1회차 관측 — 기여 0 · 보류(폐기는 K=3 회차 연속 필요)"


def suggest_rule(row: dict) -> str:
    """결정 5 — 규칙 단위 지름길: 두 경로 역전 0 이고 기여 ≥1 이면 승격 제안."""
    if row["rule"] in FIXED_HOLD_RULES:
        return "미측정(경로 1)·보류 — 결정 5 고정"
    if row["facts"] == 0:
        return "미측정 — 초안 0건"
    if row["reversal_A"] or row["reversal_B"]:
        return "폐기 제안 — 역전(결정 3) · 결정 5 승격 조건(두 경로 역전 0) 불충족"
    if row["contribution_A"] + row["contribution_B"] >= 1:
        return "승격 제안 — 결정 5 지름길(두 경로 역전 0 · 기여 ≥1)"
    if not any(row[f"measured_{p}"].startswith("측정") for p in DECISION_GROUPS):
        return "미측정 · 보류"
    return "보류 — 기여 0"


def _row(base: dict, with_res: dict, without_res: dict) -> dict:
    row = dict(base)
    for group in (*DECISION_GROUPS, *SIDE_GROUPS):
        diff = compare(with_res[group], without_res[group])
        if group in DECISION_GROUPS:
            row[f"green_with_{group}"] = diff["green_with"]
            row[f"green_without_{group}"] = diff["green_without"]
            row[f"contribution_{group}"] = len(diff["flipped"])
            row[f"reversal_{group}"] = len(diff["reversal"])
            row[f"flipped_case_ids_{group}"] = diff["flipped"]
            row[f"reversal_case_ids_{group}"] = diff["reversal"]
            row[f"rank_delta_{group}"] = diff["rank_delta"]
        else:
            row[group] = {"green_with": diff["green_with"], "green_without": diff["green_without"],
                           "flipped": diff["flipped"], "reversal": diff["reversal"]}
    return row


def measure(evaluate, facts: list[dict], rules: list[str], case_reads: dict) -> dict:
    """`evaluate(removed: frozenset[fact_id]) -> {group: {case_id: {green, ranks}}}` 로 표를 만든다.

    DB 를 모른다 — 단위 시험이 고정 픽스처 평가기로 같은 판별을 검증한다.
    """
    with_all = evaluate(frozenset())
    everything = frozenset(f["fact_id"] for f in facts)
    without_all = evaluate(everything)
    rule_rows = []
    for rule in rules:
        mine = [f for f in facts if f["rule"] == rule]
        keys = {f["key"] for f in mine}
        without = evaluate(frozenset(f["fact_id"] for f in mine)) if mine else with_all
        row = _row({"rule": rule, "facts": len(mine), "predicates": sorted(keys)}, with_all, without)
        for path in DECISION_GROUPS:
            row[f"measured_{path}"] = measured(path, keys, case_reads)
        row["제안"] = suggest_rule(row)
        rule_rows.append(row)
    fact_rows = []
    for fact in facts:
        without = evaluate(frozenset({fact["fact_id"]}))
        row = _row({"fact_id": fact["fact_id"], "dataset_seq": fact["seq"], "dataset_name": fact["name"],
                    "predicate": fact["key"], "value": fact["value"], "rule_id": fact["rule"]},
                   with_all, without)
        for path in DECISION_GROUPS:
            row[f"measured_{path}"] = measured(path, {fact["key"]}, case_reads)
        row["제안"] = suggest_fact(row)
        fact_rows.append(row)
    summary = {group: {"withAllDrafts": sum(v["green"] for v in with_all[group].values()),
                       "withoutAnyDraft": sum(v["green"] for v in without_all[group].values()),
                       "cases": len(with_all[group])}
               for group in (*DECISION_GROUPS, *SIDE_GROUPS)}
    return {"summary": summary, "rules": rule_rows, "facts": fact_rows,
            "greenWithAllDrafts": {g: sorted(c for c, v in with_all[g].items() if v["green"])
                                   for g in (*DECISION_GROUPS, *SIDE_GROUPS)}}


def fingerprint_digest(rows: list[tuple]) -> dict:
    canonical = json.dumps(sorted([list(r) for r in rows]), ensure_ascii=False)
    return {"rows": len(rows), "sha256": hashlib.sha256(canonical.encode()).hexdigest()}


def fingerprints_equal(before: dict, after: dict) -> bool:
    return before["rows"] == after["rows"] and before["sha256"] == after["sha256"]


def rule_list(value) -> list[str]:
    """`a,b` 또는 목록 → 규칙 ID 목록(순서 유지·중복 제거)."""
    items = value.split(",") if isinstance(value, str) else list(value)
    return list(dict.fromkeys(r.strip() for r in items if r.strip()))


def promote_payload(payload: dict, rules, note: str, allow_replace=()) -> dict:
    """승격 판정을 반영한 payload 사본 — 규칙의 draftFacts 를 `facts` 로 옮기고 provenance 에 판정을 적는다.

    생성물(원본 payload)은 손대지 않는다. 결과는 **기존 적재기**(`dataset_evidence_apply.py`)의 입력이다 —
    적재기는 `facts` 전체를 reviewed 로 싣고, 같은 facts 면 쓰지 않는다(멱등). reviewed 값과 겹치는 성분이
    있으면 덮지 않고 거절한다(전체 교체 API 에서 조용히 값이 바뀌지 않게).

    ⭑ 2026-09-26(PR #174 수정) — 초안과 확정값이 한 키에 공존하는 행(`draftConflictsWithReviewed`)이 있다.
    그 규칙을 `allow_replace` 에 **명시**했을 때만 확정값을 초안으로 **대체**하고, 대체한 칸을
    `promotion.replaced` 에 옛 값과 함께 남긴다. 명시하지 않으면 종전처럼 거절한다.
    """
    wanted = set(rule_list(rules))
    replace_ok = set(rule_list(allow_replace)) if allow_replace else set()
    out = json.loads(json.dumps(payload, ensure_ascii=False))
    moved, replaced = 0, []
    for row in out["datasets"]:
        for key in list(row.get("draftFacts") or {}):
            found = re.search(r"rule:([A-Za-z0-9_-]+)", row["draftProvenance"].get(key, ""))
            if not found or found[1] not in wanted:
                continue
            if key in row["facts"]:
                if found[1] not in replace_ok:
                    raise Refused(f"seq {row['seq']} {key}: reviewed 사실과 겹친다 — 승격이 값을 덮는다"
                                  f"(대체하려면 --allow-replace {found[1]} 를 명시한다)")
                replaced.append({"seq": row["seq"], "key": key, "reviewed": row["facts"][key],
                                 "draft": row["draftFacts"][key], "rule": found[1]})
            row["facts"][key] = row["draftFacts"].pop(key)
            row["provenance"][key] = f"승격 · {row['draftProvenance'].pop(key)} · {note}"
            if row.get("draftConflictsWithReviewed"):
                row["draftConflictsWithReviewed"] = [c for c in row["draftConflictsWithReviewed"]
                                                     if c["key"] != key]
            moved += 1
    out["promotion"] = {"rules": sorted(wanted), "movedFacts": moved, "note": note,
                        "allowReplace": sorted(replace_ok), "replaced": replaced}
    return out


def rehearse(rows: list[dict], facts: list[dict], rule, seq_of_dataset: dict, allow_replace=()) -> dict:
    """규칙(하나 또는 여럿)을 병합한 PUT 본문(`EvidenceWrite`)을 만들고 reviewed 사실이 하나도 빠지지 않음을 대조한다.

    `rows` = 현재 행({file_id, dataset_id, revision, file_revision, status, facts, source_label,
    source_locator, source_text}). **보내지 않는다.** 같은 facts 면 본문을 만들지 않는다(멱등 판정).

    확정값과 다른 초안은 파일마다 `conflictsWithReviewed` 에 적는다. 그 규칙이 `allow_replace` 에
    명시돼 있으면 **대체(REPLACE)** 로 본문에 싣고(`action: replace`), 아니면 싣지 않고 `collisions` 로
    올려 `ok=false` 다 — 조용히 덮지 않는다.
    """
    rules = rule_list(rule)
    replace_ok = set(rule_list(allow_replace)) if allow_replace else set()
    promoted: dict = {}
    for fact in facts:
        if fact["rule"] in rules:
            promoted.setdefault(fact["seq"], {})[fact["key"]] = (fact["value"], fact["rule"])
    report = {"rule": ",".join(rules), "allowReplace": sorted(replace_ok),
              "promoted_facts": sum(len(v) for v in promoted.values()),
              "datasets": len(promoted), "files": 0, "bodies": 0, "unchanged": 0,
              "reviewed_facts_before": 0, "reviewed_facts_kept": 0, "reviewed_facts_replaced": 0,
              "promoted_added": 0, "collisions": [], "conflictsWithReviewed": [], "dropped": [],
              "not_reviewed": 0}
    bodies = []
    for row in rows:
        seq = seq_of_dataset.get(row["dataset_id"])
        if seq not in promoted:
            continue
        report["files"] += 1
        if row["status"] != "reviewed":
            report["not_reviewed"] += 1
        current = dict(row["facts"] or {})
        merged = dict(current)
        replaced_keys = set()
        conflicts = []
        for key, (value, rule_id) in promoted[seq].items():
            if key in current and current[key] != value:
                action = "replace" if rule_id in replace_ok else "refused"
                conflicts.append({"key": key, "reviewed": current[key], "draft": value,
                                  "rule": rule_id, "action": action})
                if action == "refused":
                    report["collisions"].append({"file_id": row["file_id"], "key": key})
                    continue
                replaced_keys.add(key)
            merged[key] = value
        if conflicts:
            report["conflictsWithReviewed"].append({"file_id": row["file_id"], "seq": seq,
                                                    "conflicts": conflicts})
        report["reviewed_facts_before"] += len(current)
        kept = [k for k, v in current.items() if merged.get(k) == v]
        report["reviewed_facts_kept"] += len(kept)
        report["reviewed_facts_replaced"] += len(replaced_keys)
        dropped = sorted(set(current) - set(kept) - replaced_keys)
        if dropped:
            report["dropped"].append({"file_id": row["file_id"], "keys": dropped})
        if merged == current:
            report["unchanged"] += 1
            continue
        report["promoted_added"] += len(set(merged) - set(current))
        bodies.append({"datasetId": row["dataset_id"], "fileId": row["file_id"], "body": {
            "expectedRevision": row["revision"], "expectedFileRevision": row["file_revision"],
            "facts": merged, "status": "reviewed",
            "source": {"label": row["source_label"], "locator": row["source_locator"],
                       "text": row["source_text"]}}})
    report["bodies"] = len(bodies)
    report["ok"] = not report["dropped"] and not report["collisions"] and \
        report["reviewed_facts_kept"] + report["reviewed_facts_replaced"] == report["reviewed_facts_before"]
    return {"report": report, "bodies": bodies}


# ─────────────────────────────── DB 부분 (일회용 DB) ───────────────────────────────

def _db():
    """DB·앱 모듈은 여기서만 싣는다 — 단위 시험은 이 함수를 부르지 않는다."""
    if str(CORE_SRC) not in sys.path:
        sys.path.insert(0, str(CORE_SRC))
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    from sqlalchemy import text  # noqa: PLC0415

    from colab_core.app import client_search  # noqa: PLC0415
    from colab_core.domains import (d3_catalog, d3_client_search, d3_search_evidence,  # noqa: PLC0415
                                    d4_lineage)
    from colab_core.kernel.auth import Subject  # noqa: PLC0415
    from colab_core.kernel.db import make_engine, make_session_factory  # noqa: PLC0415
    from colab_core.kernel.ids import Ulid  # noqa: PLC0415
    from colab_core.kernel.scope import apply_scope  # noqa: PLC0415
    import dataset_evidence_apply  # noqa: PLC0415
    return argparse.Namespace(**locals())


def _open(db, url: str):
    factory = db.make_session_factory(db.make_engine(url))
    session = factory()
    try:
        session.begin()
        db.apply_scope(session, db.Subject(account_id=db.Ulid(ACCOUNT), lab_id=db.Ulid(LAB)))
        session.execute(db.text("SELECT 1"))
    except Exception as exc:  # 연결 실패는 준비 실패다
        session.close()
        raise Refused(f"DB 에 닿지 못했다: {type(exc).__name__}") from None
    return factory, session


_FINGERPRINT = """SELECT file_id::text, revision, status, source_sha256, md5(facts::text)
 FROM d3_search_evidence ORDER BY file_id"""


def db_fingerprint(db, session) -> dict:
    return fingerprint_digest([tuple(r) for r in session.execute(db.text(_FINGERPRINT))])


def seed_dev_like(db, session, payload: dict) -> dict:
    """스냅숏 v2 의 28건(고정 ID · 본체 543 · 계보)을 A 연구실에 세우고 payload 를 **같은 적용기**로 싣는다.

    `services/core-api/tests/test_search_reference_evidence.py::seed_reference_corpus` 의 삽입과 같은 열을
    쓴다. 이미 있으면 거절한다(재시드가 아니다). 이 한 번만 커밋한다 — 측정 자체는 rollback 이다.
    """
    snapshot = json.loads(SNAPSHOT_V2.read_text(encoding="utf-8"))["datasets"]
    ids = [d["id"] for d in snapshot]
    present = session.execute(db.text("SELECT count(*) FROM d3_dataset WHERE id::text = ANY(:ids)"),
                              {"ids": ids}).scalar()
    if present:
        raise Refused(f"스냅숏 데이터셋 {present}건이 이미 있다 — --seed-dev-like 는 빈 일회용 DB 에만 쓴다")
    sql = lambda statement, params=None: session.execute(db.text(statement), params or {})  # noqa: E731
    for d in snapshot:
        sql("""INSERT INTO d3_dataset(id,lab_id,owner_account_id,uploader_account_id,source_label,
               processing_level_user_set) VALUES(:id,:lab,:account,:account,:source,:level)""",
            {"id": d["id"], "lab": LAB, "account": ACCOUNT, "source": d["source_label"],
             "level": d["processing_level"]})
        sql("""INSERT INTO d3_dataset_description(dataset_id,lab_id,name,topic,summary)
               VALUES(:id,:lab,:name,:topic,:summary)""",
            {"id": d["id"], "lab": LAB, "name": d["name"], "topic": d["topic"], "summary": d["summary"]})
        sql("INSERT INTO d3_dataset_autometa(dataset_id,lab_id) VALUES(:id,:lab)", {"id": d["id"], "lab": LAB})
        for f in d["files"]:
            grid = f["kind"] == "기준 격자 파일"
            sql("""INSERT INTO d3_file(id,lab_id,dataset_id,kind,file_name,storage_key,carries_lat,carries_lon)
                   VALUES(:id,:lab,:dataset,:kind,:name,:storage,:lat,:lon)""",
                {"id": f["id"], "lab": LAB, "dataset": d["id"], "kind": f["kind"], "name": f["file_name"],
                 "storage": "fixture/" + f["id"], "lat": grid and "lat" in f["file_name"].lower(),
                 "lon": grid and "lon" in f["file_name"].lower()})
    for d in snapshot:
        for edge in d["parents"]:
            sql("""INSERT INTO d4_lineage_edge(id,lab_id,child_dataset_id,parent_dataset_id,parent_role,origin,
                   confirmed_by_account_id,confirmed_at) VALUES(:id,:lab,:child,:parent,:role,'manual',:account,now())""",
                {"id": str(db.Ulid.generate()), "lab": LAB, "child": d["id"],
                 "parent": edge["parent_dataset_id"], "role": edge["parent_role"], "account": ACCOUNT})
    report = db.dataset_evidence_apply.apply_payloads(
        db.dataset_evidence_apply._sqlalchemy_executor(session), payload, reviewer_id=ACCOUNT)
    return {"datasets": len(snapshot), "bodyFiles": sum(f["kind"] == "본체" for d in snapshot for f in d["files"]),
            "lineageEdges": sum(len(d["parents"]) for d in snapshot), "apply": report}


def load_cases() -> dict:
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))["cases"]
    practitioner = json.loads(PRACTITIONER.read_text(encoding="utf-8"))["cases"]
    heldout = json.loads(HELDOUT.read_text(encoding="utf-8"))
    interpret = {e["id"]: e for e in json.loads(INTERPRET_FIXTURE.read_text(encoding="utf-8"))["entries"]}
    for case in [*golden, *heldout]:
        if case["id"] not in interpret or interpret[case["id"]]["query"] != case["query"]:
            raise Refused(f"녹화 해석이 없거나 질의가 다르다: {case['id']}")
    probes, excluded = [], []
    for case in practitioner:
        # measure_only(2026-09-26 Ted 「전부 권고대로」) — 2회차가 거두거나 바꾼 1회차 probe. 조건 검색
        # pytest 의 green 주장에는 안 들어가지만 **이 측정의 공식 오라클**이다. supersedes 가 있으면
        # 그 이름의 probe(초안 보류 때문에 기대가 바뀐 것) 대신 이것을 잰다.
        restored = case.get("measureOnlyProbes") or []
        superseded = {m["supersedes"]: f"{case['id']}#m{i}" for i, m in enumerate(restored, 1) if m.get("supersedes")}
        for index, probe in enumerate(case.get("probes") or [], 1):
            pid = f"{case['id']}#p{index}"
            if set(probe["conditions"]) & EVIDENCE_INDEPENDENT:
                excluded.append({"id": pid, "path": "A", "reason": "근거 독립·제외(maxMissingRatePercent → d3_dataset_variable)"})
                continue
            if probe["name"] in superseded:
                excluded.append({"id": pid, "path": "A", "reason": (
                    f"{superseded[probe['name']]}(measure_only)가 대신한다 — 초안 보류 때문에 바뀐 기대다")})
                continue
            probes.append(dict(probe, id=pid))
        for index, probe in enumerate(restored, 1):
            if probe.get("mode") != "measure_only":
                raise Refused(f"{case['id']} measureOnlyProbes[{index}] 의 mode 가 measure_only 가 아니다")
            probes.append(dict(probe, id=f"{case['id']}#m{index}"))
        if not case.get("probes") and not restored:
            excluded.append({"id": case["id"], "path": "A",
                             "reason": f"probe 0건(mode {case['mode']}) — 판정할 것이 없다"})
    return {"golden": golden, "probes": probes, "heldout": heldout, "interpret": interpret,
            "excluded": excluded}


def heldout_targets() -> dict:
    """heldout 의 files·related(v1 manifest_key)를 v2 데이터셋 ID 로 잇는다 — 본체 파일 이름 대응."""
    v2 = json.loads(SNAPSHOT_V2.read_text(encoding="utf-8"))["datasets"]
    v1 = json.loads(SNAPSHOT_V1.read_text(encoding="utf-8"))["datasets"]
    by_file: dict[str, set] = {}
    for d in v2:
        for f in d["files"]:
            if f["kind"] == "본체":
                by_file.setdefault(f["file_name"], set()).add(d["id"])
    by_key = {}
    for d in v1:
        found: set = set()
        for f in d.get("files", []):
            found.update(by_file.get(f["file_name"], set()))
        by_key[d["manifest_key"]] = found
    return {"by_file": by_file, "by_key": by_key}


class Evaluator:
    """한 트랜잭션 안에서 초안 겹쳐쓰기 상태를 바꾸며 두 경로를 평가한다."""

    def __init__(self, db, session, payload, facts, cases):
        self.db, self.s, self.cases = db, session, cases
        self.sec, self.terms = conditions_module(), terms_module()
        self.assess = golden_assess()
        names = {r["name"]: r["seq"] for r in payload["datasets"]}
        rows = session.execute(db.text(
            "SELECT d.id::text AS id, dd.name FROM d3_dataset d JOIN d3_dataset_description dd "
            "ON dd.dataset_id=d.id WHERE d.deleted_at IS NULL")).mappings().all()
        self.seq_of = {r["id"]: names[r["name"]] for r in rows if r["name"] in names}
        self.id_of = {seq: i for i, seq in self.seq_of.items()}
        missing = sorted(set(names.values()) - set(self.id_of))
        if missing:
            raise Refused(f"DB 에 payload 데이터셋이 없다(seq {missing}) — --seed-dev-like 로 먼저 싣는다")
        base = session.execute(db.text(
            "SELECT file_id::text AS file_id, dataset_id::text AS dataset_id, facts FROM d3_search_evidence "
            "WHERE dataset_id::text = ANY(:ids)"), {"ids": list(self.id_of.values())}).mappings().all()
        self.groups: dict[str, dict[str, tuple]] = {}
        for r in base:
            key = json.dumps(r["facts"], sort_keys=True, ensure_ascii=False)
            self.groups.setdefault(r["dataset_id"], {}).setdefault(key, (r["facts"], []))[1].append(r["file_id"])
        self.body_files = {ds: sorted(fid for _, ids in g.values() for fid in ids) for ds, g in self.groups.items()}
        self.drafts: dict[str, dict[str, tuple]] = {}
        self.collisions = []
        self.replaces_reviewed = []
        for f in facts:
            ds = self.id_of[f["seq"]]
            for facts_value, _ in self.groups.get(ds, {}).values():
                if f["key"] in facts_value:
                    # 생성기가 공존을 선언한 칸(draftConflictsWithReviewed)은 측정에서 **대체**로 겹친다 —
                    # 「이 초안을 승격해 확정값을 바꾸면」의 반사실이다. 선언 없는 겹침은 종전처럼 거절한다.
                    (self.replaces_reviewed if f.get("replacesReviewed") else self.collisions).append(f["fact_id"])
            self.drafts.setdefault(ds, {})[f["fact_id"]] = (f["key"], f["value"])
        if self.collisions:
            raise Refused(f"초안 성분이 reviewed 사실과 겹친다: {self.collisions} — 합본이 reviewed 값을 덮는다")
        self.applied: dict[str, frozenset] = {}
        self.topics = {c.dataset_id: c.topic for c in db.d3_catalog.list_dataset_cores(session)}
        self.plans = {c["id"]: db.client_search.plan_query(c["query"], now=PLAN_NOW)
                      for c in [*cases["golden"], *cases["heldout"]]}
        self.targets = heldout_targets()
        self.case_reads = self._case_reads()
        self.evaluations = 0

    # ── 상태 ──
    def set_state(self, removed: frozenset) -> None:
        for ds, drafts in self.drafts.items():
            want = frozenset(f for f in drafts if f not in removed)
            if self.applied.get(ds) == want:
                continue
            overlay = {drafts[f][0]: drafts[f][1] for f in want}
            for facts_value, file_ids in self.groups.get(ds, {}).values():
                self.s.execute(self.db.text(
                    "UPDATE d3_search_evidence SET facts = CAST(:facts AS jsonb) WHERE file_id::text = ANY(:ids)"),
                    {"facts": json.dumps({**facts_value, **overlay}, ensure_ascii=False), "ids": file_ids})
            self.applied[ds] = want

    # ── 경로 1 ──
    def _seqs(self, rows) -> list[int]:
        return [self.seq_of[r["dataset_id"]] for r in rows if r["dataset_id"] in self.seq_of]

    def path_a_probe(self, probe) -> dict:
        rows, _capped = self.db.d3_client_search.candidates(self.s, dict(probe["conditions"]))
        seqs = self._seqs(rows)
        return {"green": probe_green(probe, seqs), "ranks": probe_ranks(probe, seqs)}

    def path_a_query_ids(self, case_id) -> list[str]:
        plan = self.plans[case_id]
        if plan["questions"]:
            return []
        rows, _capped = self.db.d3_client_search.candidates(self.s, dict(plan["conditions"]))
        return [r["dataset_id"] for r in rows
                if self.db.client_search.evaluate(plan, r, [r["evidence"]])["status"] == "supported"]

    # ── 경로 2 (routes/catalog.py 경로 2 블록의 도메인 재현) ──
    def path_b_ids(self, query, interp, reviewed, body_cache) -> list[str]:
        terms = self.terms.candidate_terms(query, list(interp["terms"]))
        if not (interp["isDataQuery"] and terms):
            return []
        criteria = self.sec.parse(query)
        include_ids, exclude_ids = [], []
        if reviewed and criteria["topic"] and not criteria["unsupported"]:
            relevant = [r for r in reviewed if self.topics.get(r["dataset_id"]) == criteria["topic"]]
            if relevant:
                key = tuple(sorted({r["dataset_id"] for r in relevant}))
                if key not in body_cache:
                    body_cache[key] = self.db.d3_catalog.body_file_ids(self.s, list(key))
                include_ids, exclude_ids = self.sec.candidates(criteria, relevant, body_cache[key])
                if re.search(r"원자료|바로\s*앞|입력\s*데이터셋", query):
                    notes: dict[str, list] = {}
                    for owner in [r for r in relevant if r["file_name"].casefold() in query.casefold()]:
                        for edge in self.db.d4_lineage.edges_of(self.s, self.db.Ulid(owner["dataset_id"])):
                            parent = str(edge["parent_dataset_id"])
                            if str(edge["child_dataset_id"]) == owner["dataset_id"] \
                                    and self.topics.get(parent) == criteria["topic"]:
                                notes.setdefault(parent, []).append(owner["file_name"])
                    if notes:
                        include_ids = list(notes)
                        exclude_ids = [i for i in exclude_ids if i not in notes]
        matches, _total = self.db.d3_catalog.search_datasets(
            self.s, terms=tuple(terms), topic=interp["topic"], limit=SEARCH_LIMIT, offset=0,
            evidence_ids=tuple(include_ids), excluded_ids=tuple(exclude_ids), include_ontology=True)
        return [m.dataset_id for m in matches]

    def _golden(self, case, ids) -> dict:
        judged = self.assess(case, [{"dataset_id": i} for i in ids], len(ids))
        return {"green": judged["retrieval"] == "pass", "ranks": judged["required_ranks"]}

    def _heldout(self, case, ids, reviewed_by_ds, criteria) -> dict:
        if case.get("files"):
            wanted = set().union(*(self.targets["by_file"].get(n, set()) for n in case["files"]))
            ranks = {w: (ids.index(w) + 1 if w in ids else None) for w in sorted(wanted)}
            return {"green": bool(wanted) and wanted <= set(ids), "ranks": ranks}
        label, _key = HELDOUT_CONDITION[case["condition"]]
        related = sorted(self.targets["by_key"].get(case["related"], set()))
        states = []
        for ds in related:
            rows = reviewed_by_ds.get(ds) or []
            checks = self.sec.assess(criteria, rows[0]["facts"]) if rows else {}
            states.append(checks.get(label, ("absent",))[0])
        return {"green": bool(states) and all(s == case["expected"] for s in states), "ranks": states}

    def evaluate(self, removed: frozenset) -> dict:
        self.evaluations += 1
        self.set_state(removed)
        out = {g: {} for g in (*DECISION_GROUPS, *SIDE_GROUPS)}
        for probe in self.cases["probes"]:
            out["A"][probe["id"]] = self.path_a_probe(probe)
        reviewed = self.db.d3_search_evidence.read_reviewed(self.s, include_source_text=False)
        reviewed_by_ds: dict[str, list] = {}
        for r in sorted(reviewed, key=lambda r: r["file_id"]):
            reviewed_by_ds.setdefault(r["dataset_id"], []).append(r)
        body_cache: dict = {}
        for case in self.cases["golden"]:
            if case["mode"] == "manual":
                continue
            if self.plans[case["id"]]["recognized"]:
                out["A"][case["id"]] = self._golden(case, self.path_a_query_ids(case["id"]))
            ids = self.path_b_ids(case["query"], self.cases["interpret"][case["id"]], reviewed, body_cache)
            out["B"][case["id"]] = self._golden(case, ids)
        for case in self.cases["heldout"]:
            criteria = self.sec.parse(case["query"])
            if self.plans[case["id"]]["recognized"] and case.get("files"):
                out["heldout_A"][case["id"]] = self._heldout(case, self.path_a_query_ids(case["id"]), {}, {})
            ids = self.path_b_ids(case["query"], self.cases["interpret"][case["id"]], reviewed, body_cache)
            out["heldout_B"][case["id"]] = self._heldout(case, ids, reviewed_by_ds, criteria)
        return out

    def _case_reads(self) -> dict:
        reads = {"A": {}, "B": {}}
        for probe in self.cases["probes"]:
            reads["A"][probe["id"]] = probe_reads(probe["conditions"])
        for case in self.cases["golden"]:
            if case["mode"] == "manual":
                continue
            if self.plans[case["id"]]["recognized"]:
                reads["A"][case["id"]] = probe_reads(self.plans[case["id"]]["conditions"])
            reads["B"][case["id"]] = criteria_reads(self.sec.parse(case["query"]))
        return reads

    def excluded(self) -> list[dict]:
        out = list(self.cases["excluded"])
        for case in self.cases["golden"]:
            if case["mode"] == "manual":
                out.append({"id": case["id"], "path": "A·B", "reason": "manual — golden_baseline.assess 가 판정하지 않는다"})
            elif not self.plans[case["id"]]["recognized"]:
                out.append({"id": case["id"], "path": "A",
                            "reason": "plan_query 미인식 — 제품에서 경로 1 로 가지 않는다(경로 2 만 측정)"})
        return out


# ─────────────────────────────── 산출물 ───────────────────────────────

def _git_head() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True,
                              check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


#: 적재기(`dataset_evidence_apply.py`)와 이 측정이 실제로 읽는 칸.
PAYLOAD_MEASURED_FIELDS = ("name", "topic", "sourceLabel", "status", "facts", "draftFacts",
                           "draftProvenance", "source")


def regeneration_check(payload: dict) -> dict:
    """생성기를 다시 돌려(쓰지 않고 build 만) 적재 payload 와 대조한다 — 측정이 읽는 칸과 나머지를 가른다."""
    try:
        backfill = load_pure("k4_dataset_evidence_backfill", TOOLS / "dataset_evidence_backfill.py")
        rebuilt = backfill.build()
    except SystemExit as exc:
        return {"measuredFieldsEqual": None, "note": f"생성기가 비영 종료: {exc}"}
    measured_diff, other_diff = [], []
    for new, old in zip(rebuilt["datasets"], payload["datasets"]):
        for key in sorted(set(new) | set(old)):
            if new.get(key) != old.get(key):
                (measured_diff if key in PAYLOAD_MEASURED_FIELDS else other_diff).append(
                    {"seq": old.get("seq"), "field": key, "payload": old.get(key), "regenerated": new.get(key)})
    return {"measuredFieldsEqual": not measured_diff and len(rebuilt["datasets"]) == len(payload["datasets"]),
            "rulesEqual": rebuilt["rules"] == payload["rules"],
            "measuredFieldDiffs": measured_diff, "otherFieldDiffs": other_diff,
            "note": ("dataset_evidence_backfill.build() 재생성과 비교. 측정은 dev 적재와 같은 **커밋된 payload** 로 한다"
                     "(결정 7) — 적재기가 읽지 않는 칸(auxiliaryRole 등)의 차이는 측정에 닿지 않는다.")}


def _dump(result: dict) -> str:
    """머리는 들여 쓰고 규칙·사실 행은 한 줄에 하나 — 회차마다 diff 로 읽히게, 파일은 작게."""
    head = {k: v for k, v in result.items() if k not in ("rules", "facts")}
    text = json.dumps(head, ensure_ascii=False, indent=1, default=str)
    blocks = []
    for key in ("rules", "facts"):
        rows = ",\n  ".join(json.dumps(r, ensure_ascii=False, separators=(",", ":"), default=str)
                             for r in result[key])
        blocks.append(f' "{key}": [\n  {rows}\n ]')
    out = text[:-2] + ",\n" + ",\n".join(blocks) + "\n}\n"
    json.loads(out)
    return out


def _cell(row, path):
    return (f"{row[f'green_with_{path}']}→{row[f'green_without_{path}']} · 기여 {row[f'contribution_{path}']}"
            f" · 역전 {row[f'reversal_{path}']} · {row[f'measured_{path}']}")


def render_markdown(result: dict) -> str:
    inputs, db = result["inputs"], result["db"]
    lines = [
        f"# 초안 사실 검토 표 — {result['round']} ({result['measuredAt'][:10]})", "",
        "생성: `eval/k4-search/measure_draft_contribution.py` · 정본 intent "
        "`dev-package/intent/2026-09-21-evidence-promotion.md` · **기계는 제안만 한다. 판정은 Ted.**", "",
        "## 입력", "",
        f"- payload `{inputs['payload']['path']}` sha256 `{inputs['payload']['sha256']}`"
        f" · 생성기 재생성 대조: 측정 칸 동일 = {inputs['payload']['regeneration'].get('measuredFieldsEqual')}"
        f" · 그 밖의 칸 차이 {len(inputs['payload']['regeneration'].get('otherFieldDiffs') or [])}건",
    ]
    if result.get("seed"):
        apply = result["seed"]["apply"]
        lines.append(f"- 일회용 DB 시드: 데이터셋 {result['seed']['datasets']} · 본체 {result['seed']['bodyFiles']}"
                     f" · 계보 {result['seed']['lineageEdges']} · 적재 보고 evidence {apply['evidence']} · topic "
                     f"{apply['topic']} · source_label {apply['source_label']} · draft_withheld {apply['draft_withheld']}")
    for name, sha in inputs["caseSets"].items():
        lines.append(f"- `{name}` sha256 `{sha}`")
    lines += [f"- DB 지문 전 {db['before']['rows']}행 `{db['before']['sha256'][:16]}…` · 후 {db['after']['rows']}행 "
              f"`{db['after']['sha256'][:16]}…` → **남은 변경 {'0' if db['unchanged'] else '있음(실패)'}**",
              f"- 평가 {result['evaluations']}회 · 모델 호출 0회 · 경로 2 해석 = `interpret-fixture.json`(규칙 기반 녹화, LLM 아님)",
              "", "## 기준선 (green 케이스 수)", "",
              "| 케이스군 | 케이스 | 초안 전부 포함 | 초안 전부 제외 |", "|---|---:|---:|---:|"]
    labels = {"A": "경로 1 (결정 근거)", "B": "경로 2 (결정 근거)", "heldout_A": "heldout 경로 1 (사후 확인)",
              "heldout_B": "heldout 경로 2 (사후 확인)"}
    for group, s in result["summary"].items():
        lines.append(f"| {labels[group]} | {s['cases']} | {s['withAllDrafts']} | {s['withoutAnyDraft']} |")
    lines += ["", "## 규칙 단위 (결정 5)", "",
              "형식: green 포함→제외 · 기여 · 역전 · 측정 여부", "",
              "| 규칙 | 초안 | 경로 1 | 경로 2 | heldout 1/2 뒤집힘(사후 확인) | 제안 |",
              "|---|---:|---|---|---|---|"]
    for row in result["rules"]:
        side = (f"{len(row['heldout_A']['flipped'])}/{len(row['heldout_B']['flipped'])} 기여 · "
                f"{len(row['heldout_A']['reversal'])}/{len(row['heldout_B']['reversal'])} 역전")
        lines.append(f"| `{row['rule']}` | {row['facts']} | {_cell(row, 'A')} | {_cell(row, 'B')} | {side} | "
                     f"{row['제안']} |")
    lines += ["", "뒤집힌 케이스:", ""]
    for row in result["rules"]:
        bits = [f"{k} {row[k]}" for k in ("flipped_case_ids_A", "reversal_case_ids_A",
                                           "flipped_case_ids_B", "reversal_case_ids_B") if row[k]]
        for side in SIDE_GROUPS:
            if row[side]["flipped"] or row[side]["reversal"]:
                bits.append(f"{side} 기여 {row[side]['flipped']} · 역전 {row[side]['reversal']}")
        if bits:
            lines.append(f"- `{row['rule']}` — " + " · ".join(bits))
    lines += ["", "## 사실 단위 (110칸)", "",
              "| 사실 | 값 | 규칙 | 경로 1 | 경로 2 | 제안 |", "|---|---|---|---|---|---|"]
    for row in result["facts"]:
        lines.append(f"| `{row['fact_id']}` {row['dataset_name']} | `{json.dumps(row['value'], ensure_ascii=False)}` | "
                     f"`{row['rule_id']}` | {_cell(row, 'A')} | {_cell(row, 'B')} | {row['제안']} |")
    lines += ["", "사실 단위 뒤집힘(경로 1·2 · heldout):", ""]
    for row in result["facts"]:
        bits = [f"{k} {row[k]}" for k in ("flipped_case_ids_A", "reversal_case_ids_A",
                                           "flipped_case_ids_B", "reversal_case_ids_B") if row[k]]
        for side in SIDE_GROUPS:
            if row[side]["flipped"] or row[side]["reversal"]:
                bits.append(f"{side} 기여 {row[side]['flipped']} · 역전 {row[side]['reversal']}")
        if bits:
            lines.append(f"- `{row['fact_id']}` — " + " · ".join(bits))
    lines += ["", "## 제외한 케이스", ""]
    lines += [f"- `{e['id']}` ({e['path']}) — {e['reason']}" for e in result["cases"]["excluded"]]
    lines += ["", "## 읽는 법·한계", "",
              "- 기여 = 그 초안을 빼면 green→fail 로 뒤집히는 케이스 수. 역전 = 빼면 fail→green. 순위 변화는 JSON `rank_delta_*` 에만 적는다.",
              "- 「미측정(술어 없음)」 = 그 경로가 이 성분을 읽지 않는다(경로 1 은 interpolated, 경로 2 는 platform·representation). "
              "「미측정(케이스 0)」 = 읽지만 그 술어를 부르는 케이스가 없다 — 폐기 근거가 아니다(결정 3).",
              "- 사실 단위 제안은 1회차라 회차 이력이 없다 — 승격(2회차)·폐기(K=3)는 「1회차 관측」으로만 낸다. 역전만 즉시 폐기 제안이다.",
              "- heldout 은 제안에 쓰지 않는다(과적합 완화 · 사후 확인).",
              "- 경로 1 오라클 = practitioner-conditions.json 의 probes(판정용) + measureOnlyProbes(초안 값 측정 전용 · "
              "정답 주장 아님 · 2026-09-26 Ted 「전부 권고대로」로 되살린 1회차 probe). `#m` 이 measure_only 다.",
              "- 경로 2 는 `routes/catalog.py` 경로 2 블록의 도메인 재현이다. 라우트의 verified·잠김 조립·근거 문장은 green 판정에 들어가지 않는다.",
              ""]
    return "\n".join(lines)


# ─────────────────────────────── 진입 ───────────────────────────────

def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("database_url", help="일회용 DB 의 앱 롤 URL (DEV·운영 금지)")
    p.add_argument("--payload", type=pathlib.Path, default=DEFAULT_PAYLOAD)
    p.add_argument("--output", type=pathlib.Path, help="산출 디렉터리(새 경로)")
    p.add_argument("--seed-dev-like", action="store_true",
                   help="빈 일회용 DB 에 스냅숏 v2 28건과 payload 를 먼저 싣는다(이것만 커밋)")
    p.add_argument("--rehearse-promote", metavar="RULE_ID[,RULE_ID]",
                   help="규칙(쉼표로 여럿)의 승격 PUT 본문을 만들어 reviewed 사실 보존만 대조한다(보내지 않는다)")
    p.add_argument("--allow-replace", metavar="RULE_ID[,RULE_ID]", default="",
                   help="확정값과 공존하는 초안(draftConflictsWithReviewed)을 승격하며 확정값을 대체해도 되는 규칙 — 명시한 것만")
    p.add_argument("--write-promoted-payload", type=pathlib.Path, metavar="PATH",
                   help="리허설과 함께 승격 반영 payload 사본을 쓴다 — dataset_evidence_apply.py 의 입력")
    p.add_argument("--promotion-note", default="판정 결과 미기재",
                   help="승격 payload provenance 에 붙일 판정 근거(회차 intent 판정 결과 절)")
    p.add_argument("--round", default="1회차", help="산출물에 적을 회차 이름(예: 2회차 지역)")
    p.add_argument("--i-know-this-is-disposable", action="store_true",
                   help="localhost 가 아닌 일회용 DB(도커 브리지 IP 등)임을 명시한다")
    return p


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print(__doc__)
        return 78
    args = _parser().parse_args(argv)
    refusal = check_disposable_url(args.database_url, args.i_know_this_is_disposable)
    if refusal:
        print(f"준비 실패: {refusal}", file=sys.stderr)
        return 78
    if not args.rehearse_promote and not args.output:
        print("준비 실패: 측정에는 --output <새 디렉터리> 가 필요하다", file=sys.stderr)
        return 78
    if not args.rehearse_promote and args.output and args.output.exists() and any(args.output.iterdir()):
        print(f"준비 실패: 산출 디렉터리가 비어 있지 않다 — {args.output}", file=sys.stderr)
        return 78
    try:
        payload = json.loads(args.payload.read_text(encoding="utf-8"))
        facts = draft_facts(payload)
        db = _db()
        factory, session = _open(db, args.database_url)
    except (OSError, ValueError, Refused) as exc:
        print(f"준비 실패: {exc}", file=sys.stderr)
        return 78
    try:
        if args.rehearse_promote:
            return _rehearse(db, session, payload, facts, args)
        return _measure(db, factory, session, payload, facts, args)
    except Refused as exc:
        print(f"준비 실패: {exc}", file=sys.stderr)
        return 78
    finally:
        session.rollback()
        session.close()


def _rehearse(db, session, payload, facts, args) -> int:
    from colab_core.app.routes.search_evidence import EvidenceWrite  # noqa: PLC0415 — 계약 검증만
    rules = rule_list(args.rehearse_promote)
    missing = [r for r in rules if r not in {f["rule"] for f in facts}]
    if missing:
        raise Refused(f"payload 에 그 규칙의 초안이 없다: {missing}")
    names = {r["name"]: r["seq"] for r in payload["datasets"]}
    seq_of = {r["id"]: names[r["name"]] for r in session.execute(db.text(
        "SELECT d.id::text AS id, dd.name FROM d3_dataset d JOIN d3_dataset_description dd ON dd.dataset_id=d.id"
    )).mappings() if r["name"] in names}
    rows = [dict(r) for r in session.execute(db.text(
        """SELECT file_id::text AS file_id, dataset_id::text AS dataset_id, revision, file_revision, status, facts,
           source_label, source_locator, source_text FROM d3_search_evidence ORDER BY file_id""")).mappings()]
    out = rehearse(rows, facts, rules, seq_of, args.allow_replace)
    for item in out["bodies"]:
        EvidenceWrite.model_validate(item["body"])  # 전체 교체 본문이 계약을 통과하는지 — 보내지는 않는다
    report = dict(out["report"], contract_validated=len(out["bodies"]), sent=0)
    print(json.dumps(report, ensure_ascii=False))
    if args.output:
        target = args.output / f"rehearse-{'+'.join(rules)}.json"
        if target.exists():
            raise Refused(f"리허설 산출물이 이미 있다 — {target}")
        args.output.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if args.write_promoted_payload:
        if args.write_promoted_payload.exists():
            raise Refused(f"승격 payload 가 이미 있다 — {args.write_promoted_payload}")
        promoted = promote_payload(payload, rules, args.promotion_note, args.allow_replace)
        args.write_promoted_payload.parent.mkdir(parents=True, exist_ok=True)
        args.write_promoted_payload.write_text(
            json.dumps(promoted, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"승격 payload {args.write_promoted_payload} — 옮긴 사실 {promoted['promotion']['movedFacts']}칸 · "
              f"sha256 {sha256_file(args.write_promoted_payload)}")
    return 0 if report["ok"] else 1


def _measure(db, factory, session, payload, facts, args) -> int:
    seed = None
    if args.seed_dev_like:
        seed = seed_dev_like(db, session, payload)
        session.commit()
        print("시드 적재 " + json.dumps(seed, ensure_ascii=False))
        session.begin()
        db.apply_scope(session, db.Subject(account_id=db.Ulid(ACCOUNT), lab_id=db.Ulid(LAB)))
    before = db_fingerprint(db, session)
    session.rollback()
    # ── 측정: 한 트랜잭션 · 끝에 rollback ──
    session.begin()
    db.apply_scope(session, db.Subject(account_id=db.Ulid(ACCOUNT), lab_id=db.Ulid(LAB)))
    cases = load_cases()
    evaluator = Evaluator(db, session, payload, facts, cases)
    table = measure(evaluator.evaluate, facts, rule_order(payload, facts), evaluator.case_reads)
    session.rollback()
    check = factory()
    try:
        check.begin()
        db.apply_scope(check, db.Subject(account_id=db.Ulid(ACCOUNT), lab_id=db.Ulid(LAB)))
        after = db_fingerprint(db, check)
    finally:
        check.rollback()
        check.close()
    session.begin()  # finally 의 rollback 짝
    unchanged = fingerprints_equal(before, after)
    result = {
        "schema": "colab-draft-contribution/1",
        "round": args.round,
        "measuredAt": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "tool": {"path": "eval/k4-search/measure_draft_contribution.py",
                 "sha256": sha256_file(pathlib.Path(__file__)), "gitHead": _git_head()},
        "intent": "dev-package/intent/2026-09-21-evidence-promotion.md",
        "inputs": {
            "payload": {"path": str(args.payload.resolve().relative_to(REPO)) if args.payload.resolve().is_relative_to(REPO) else str(args.payload),
                        "sha256": sha256_file(args.payload), "draftFacts": len(facts),
                        "ruleSummary": payload.get("ruleSummary"),
                        "regeneration": regeneration_check(payload)},
            "caseSets": {p.name: sha256_file(p) for p in (GOLDEN, PRACTITIONER, HELDOUT, INTERPRET_FIXTURE,
                                                          SNAPSHOT_V2)},
            "planNow": PLAN_NOW.isoformat(), "searchLimit": SEARCH_LIMIT, "modelCalls": 0,
        },
        "seed": seed,
        "db": {"before": before, "after": after, "unchanged": unchanged,
               "fingerprint": "(file_id, revision, status, source_sha256, md5(facts)) 전 행 · A 연구실 스코프"},
        "evaluations": evaluator.evaluations,
        "cases": {"A": sorted(evaluator.case_reads["A"]), "B": sorted(evaluator.case_reads["B"]),
                  "heldout": [c["id"] for c in cases["heldout"]],
                  "excluded": evaluator.excluded()},
        "draftReplacesReviewed": sorted(evaluator.replaces_reviewed),
        "bodyFilesByDataset": {str(evaluator.seq_of[ds]): len(ids) for ds, ids in evaluator.body_files.items()},
        **table,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "draft-contribution.json").write_text(_dump(result), encoding="utf-8")
    (args.output / "draft-contribution-review.md").write_text(render_markdown(result), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "evaluations": evaluator.evaluations,
                      "summary": result["summary"], "dbUnchanged": unchanged,
                      "rules": {r["rule"]: {p: (r[f"contribution_{p}"], r[f"reversal_{p}"]) for p in DECISION_GROUPS}
                                for r in result["rules"]}}, ensure_ascii=False))
    if not unchanged:
        print("판정 실패: 측정 전후 d3_search_evidence 지문이 다르다 — 남은 변경이 있다", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
