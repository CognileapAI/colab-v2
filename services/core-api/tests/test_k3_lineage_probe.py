"""K3 `WU-S6` — **core-api 가 실제로 실어 보낼 후보와 대조군 4종을 적어 둔다.** 모델 호출 0회.

실측의 두 절반 중 이쪽이다. 모델 절반(`eval/k3-lineage/llm_lineage_probe.py`)은 DB 에
닿지 않으므로, 후보를 고르는 일은 D3 의 주인인 core-api 가 여기서 **제품 함수 그대로**
하고 그 결과를 `COLAB_K3_CANDIDATES_OUT` 에 적는다. 러너는 그 파일을 읽는다 —
두 절반이 같은 후보를 봤다는 것을 그 파일 하나가 보증한다.

고르는 자리는 `routes/ingestion._lineage_candidates` 하나다. 여기서 새 선정을 적으면
**중계가 보내는 후보와 실측이 본 후보가 갈리고, 그 어긋남은 아무도 못 센다.**

⭑ **⟨2026-09-24 · `WU-S6`⟩ 대조군 4종을 스냅샷 계보에서 **생성**한다**(손으로 적지 않는다).
Ted 판정 2회차 1 이 구조 보장의 범위를 **후손·자기 자신·후보 밖 ID·인용 오류** 넷으로
한정했으므로, 군마다 「무엇이 걸러졌나」를 나눠 적는다.
  ⑴ `removed`               정답 부모 제거 — 참인 인용의 비부모가 남을 수 있다(기록 대상)
  ⑵ `descendants`           자식의 **후손만** — 적격 필터가 통째로 새는지 보는 군
  ⑶ `siblings`              **형제만** — 축 신호는 겹치되 부모가 아닌 후보(기록 대상)
  ⑴′ `removed_and_siblings` 정답＋형제 제거 — **구조 보장 판정용** 군

세 수를 군마다 남긴다 — `population`(계보에서 뽑은 모집단) · `in_pool`(제품 선정이 실제로
집어 온 것) · `survived`(제품 적격 필터를 통과한 것). 셋을 한 칸으로 접으면 「구조가
막았다」와 「애초에 후보에 없었다」가 같은 0 으로 보인다.

⚠ **가공 단계의 출처는 스냅샷 v2 의 `processing_level` 열이다**(dev `processing_level_user_set`).
`seed_reference_corpus` 가 같은 값을 일회용 DB 에 싣는다. 그 값이 `lineage-cases.json`
의 `upload_level` 과 한 글자도 다르지 않다는 것은 `test_k3_candidate_recall.py` 가 **표식
없이** 지킨다(오타가 실측 직전에 드러나지 않게).

코퍼스 = K4 검색 절반과 같은 일회용 Postgres + 고정 ID(`seed_reference_corpus`).
dev 접속·재시드·승인 0건. 판정 게이트가 아니라 **측정**이다 — 표식 `k3_probe` 는 게이트
선택자에서 빠진다. 환경변수가 없으면 skip 이 아니라 **error** 다(K4 규율).
"""
import dataclasses
import json
import os
import subprocess
from pathlib import Path

import pytest

from conftest import ACC_A_RES, LAB_A, scoped_ro
from test_search_relay import fake_ai  # noqa: F401 — 실제 HTTP 시험 전송을 재사용한다
from test_search_reference_evidence import ROOT, seed_reference_corpus
from test_k3_candidate_recall import _cases, _snapshot, _upload_meta, snapshot_level
from colab_core.app import rule_suggest
from colab_core.app.routes import ingestion as _ing
from colab_core.domains import d3_catalog, d3_lineage_signals, d4_lineage
from colab_core.kernel.ids import Ulid

pytestmark = pytest.mark.k3_probe

#: 군 이름 다섯. 러너(`--groups`)와 **같은 문자열**이다 — 두 벌이면 표가 갈린다.
GROUPS = ("main", "removed", "descendants", "siblings", "removed_and_siblings")

#: 형제의 정의 두 가지. 정본은 ⓐ 이고, ⓐ 가 0건인 코퍼스에서만 ⓑ 로 떨어진다.
SIBLING_GRAPH = "graph"        # 부모를 하나라도 공유한다(intent 축자 「같은 부모를 공유하는 형제」)
SIBLING_SAME_LEVEL = "same_level"  # 같은 Lv · 자기 부모가 아님 · 자기 자신이 아님


# ─────────────────────────── 계보 그래프 (스냅샷에서 생성) ───────────────────────────
def _parent_map(snapshot: dict) -> dict[str, list[str]]:
    return {d["id"]: [p["parent_dataset_id"] for p in d["parents"]]
            for d in snapshot["datasets"]}


def _descendants(parents: dict[str, list[str]], root: str) -> set[str]:
    """자식의 **후손 전부**(손자까지). 자기 자신은 후손이 아니다."""
    children: dict[str, list[str]] = {}
    for child, mine in parents.items():
        for parent in mine:
            children.setdefault(parent, []).append(child)
    found: set[str] = set()
    stack = [root]
    while stack:
        for child in children.get(stack.pop(), ()):
            if child not in found:
                found.add(child)
                stack.append(child)
    return found


def _siblings(parents: dict[str, list[str]], levels: dict[str, int],
              child: str) -> tuple[set[str], str]:
    """형제 집합과 **어느 정의로 뽑았는지**를 함께 돌려준다.

    ⚠ 자식에 따라 **부모를 공유하는 형제가 한 건도 없다**(v1 9건은 계보 전체가 사슬 모양이었고,
    v2 에서도 사슬 끝 자식이 그렇다). 그대로 두면 ⑶ 군이 공집합이라 아무것도 재지 못하고, ⑴′ 가 ⑴ 과 글자 하나 다르지
    않게 된다 — 구조 보장 판정용으로 더한 군이 사라진다. 그래서 **정의를 넓힌 사실을
    출력에 적고**(`sibling_rule`) 넓은 쪽으로 떨어진다. 감추면 표가 거짓말을 한다.

    ⚠ graph 형제에서도 **자기 부모는 뺀다** — 부모 하나가 다른 부모의 부모이기도 하면
    (v2: Prediction ← DEM · Aspect, Aspect ← DEM) 그 부모가 형제로 섞여 「형제만」 군이 오염된다.
    """
    mine = set(parents.get(child, ()))
    graph = {other for other, theirs in parents.items()
             if other != child and other not in mine and mine & set(theirs)}
    if graph:
        return graph, SIBLING_GRAPH
    return ({other for other, level in levels.items()
             if other != child and other not in mine and level == levels[child]},
            SIBLING_SAME_LEVEL)


# ─────────────────────────── 코퍼스 준비 ───────────────────────────
def apply_snapshot_autometa(sql, snapshot: dict) -> dict[str, dict]:
    """⭑ **`seed_reference_corpus` 는 자동 메타 행을 빈 채로 넣는다** — 스냅샷이 들고 있는
    dev 의 실제 값을 여기서 덮어 쓴다.

    이 한 걸음이 없으면 후보 쪽 축이 **다섯 다 비고**, 비교기는 어떤 후보에도 맞는 축을
    찾지 못한다. 그러면 실측은 「구조가 막았다」와 「대조할 값이 애초에 없었다」를 가르지
    못하고, 빈 제안 4/4 가 구조의 공로처럼 읽힌다 — 재는 것이 제품이 아니라 **시드의
    빈칸**이 되는 자리다.

    ⚠ 값을 **지어내지 않는다.** 스냅샷에 적힌 것만 싣는다 — dev 에서도 `crs`·`grid`·
    `variables`·기간은 전부 비어 있고 `bundle_file_name` 만 있다. 그 빈곤 자체가 실측의
    표본 한계이고, 보고서 첫 줄이 그 사실을 적는다.
    """
    applied = {}
    for dataset in snapshot["datasets"]:
        meta = dataset.get("autometa") or {}
        sql("""UPDATE d3_dataset_autometa
                  SET format = :format, variables = :variables,
                      period_start = :period_start, period_end = :period_end,
                      crs = :crs, grid = :grid, bundle_file_name = :bundle,
                      updated_at = now()
                WHERE dataset_id = :id""",
            {"id": dataset["id"], "format": meta.get("format"),
             "variables": list(meta.get("variables") or ()),
             "period_start": meta.get("period_start"), "period_end": meta.get("period_end"),
             "crs": meta.get("crs"), "grid": meta.get("grid"),
             "bundle": meta.get("bundle_file_name")})
        applied[dataset["id"]] = meta
    return applied


def _axes_json(axes) -> dict:
    """비교기 축 한 벌을 **러너가 그대로 되세울 수 있는 모양**으로 적는다.

    기간은 `datetime` 이라 ISO 문자열로 적는다 — 되읽는 쪽(`_instant`)이 같은 규칙으로
    읽으므로 값이 갈리지 않는다. 축 이름은 비교기의 필드명 그대로다(두 벌 금지).
    """
    row = dataclasses.asdict(axes)
    row["variables"] = list(row.get("variables") or ())
    for key in ("period_start", "period_end"):
        value = row.get(key)
        row[key] = None if value is None else (
            value.isoformat() if hasattr(value, "isoformat") else str(value))
    return row


def _eligible(level: int | None, upload_level: int) -> bool:
    """제품 적격 판정 한 줄 — `d3_catalog.select_lineage_candidates` 의 그 조건이다.

    ⚠ **모르면 거르지 않는다**(열린 권고 ③ 채택) — 「모른다」를 이유로 진짜 부모를 지우지
    않는다. 판정값을 만드는 함수는 제품(`d3_catalog.eligibility_level`)의 것을 그대로 부른다.
    """
    return level is None or level <= upload_level


def _corpus_pool(session, *, upload_meta: dict) -> dict[str, dict]:
    """대조군의 **모집단**. 후손은 제품 선정(`filtered`)이 걸러 낸 뒤라 거기 없을 수 있어서,
    무필터 최근순(`recent`)으로 연구실 전부를 한 번 집어 온다.

    ⚠ **여기서 새 질의를 만들지 않는다** — 제품의 같은 함수를 전략만 바꿔 부르고, 본문
    한 장도 제품 조립기(`_lineage_candidate`)가 만든다. 두 벌로 적으면 대조군이 본 후보와
    본군이 본 후보가 다른 모양이 된다.
    """
    summaries_port = d4_lineage.LineageSummaryAdapter(session)
    picked = d3_catalog.select_lineage_candidates(
        session, lab_id=LAB_A, upload_meta=upload_meta,
        strategy=d3_catalog.RECENT_CANDIDATES, k=_ing.LINEAGE_CANDIDATE_LIMIT,
        lineage_summaries=summaries_port, upload_level=None)
    ids = [Ulid(c.core.dataset_id) for c in picked]
    metas = d3_catalog.autometa_of(session, ids)
    summaries = summaries_port.summaries(ids)
    pool: dict[str, dict] = {}
    for candidate in picked:
        dataset_id = candidate.core.dataset_id
        meta = metas.get(dataset_id)
        pool[dataset_id] = dict(
            payload=_ing._lineage_candidate(candidate, meta),
            axes=d3_lineage_signals.CandidateAxes.from_autometa(dataset_id, meta or {}),
            eligibility=d3_catalog.eligibility_level(
                candidate.core, summaries.get(dataset_id), derived_known=True),
            derived_level=candidate.derived_level)
    return pool


# ─────────────────────────── 군 생성 ───────────────────────────
def _from_main(main_payload: list[dict], drop: set[str]) -> list[dict]:
    """본군에서 ID 몇을 뺀 군. **순위를 다시 매기지 않는다** — 제품이 세운 순서 그대로다."""
    return [dict(c) for c in main_payload if c["datasetId"] not in drop]


def _from_pool(pool: dict[str, dict], ids, upload_level: int) -> tuple[list[dict], list[str]]:
    """계보에서 뽑은 모집단에 **제품 적격 필터를 다시 건다.** 통과한 것만 후보가 된다."""
    in_pool = [i for i in sorted(ids) if i in pool]
    kept = [i for i in in_pool if _eligible(pool[i]["eligibility"], upload_level)]
    return [dict(pool[i]["payload"]) for i in kept], in_pool


def _rule_arm(*, candidates: list[dict], axes: dict, upload_meta: dict,
              upload_level: int, searched: int) -> dict:
    """규칙 팔을 **제품 클래스 그대로** 돌린다. 모델 호출 0회 · DB 접속 0회."""
    suggester = rule_suggest.RuleBasedLineageSuggester()
    return suggester.suggest(
        lab_id=LAB_A, lab_name="연구실", account_id=ACC_A_RES,
        file_meta=upload_meta["file"], candidates=candidates, searched_count=searched,
        dataset_name_draft=upload_meta.get("datasetNameDraft"),
        subject=upload_meta.get("subject"), processing_level=upload_level,
        upload_axes=d3_lineage_signals.UploadAxes.from_file_meta(upload_meta["file"]),
        candidate_axes={i: axes[i] for i in (c["datasetId"] for c in candidates)})


def test_k3_계보_제안_후보와_대조군_4종을_적어_둔다(p2_client, sql, fake_ai, session_factory):
    out_path = Path(os.environ["COLAB_K3_CANDIDATES_OUT"])
    assert not out_path.exists(), "출력이 이미 있다 — 새 실행 경로를 고른다(준비 실패)"
    cases = _cases()
    snapshot = _snapshot()
    _, datasets = seed_reference_corpus(p2_client, sql, fake_ai)
    autometa = apply_snapshot_autometa(sql, snapshot)
    by_id = {d["id"]: d for d in datasets}
    assert {c["child_dataset_id"] for c in cases["cases"]} <= set(by_id)

    parents_of = _parent_map(snapshot)
    levels = {d["id"]: snapshot_level(d) for d in snapshot["datasets"]}

    rows = []
    sibling_rules: set[str] = set()
    with scoped_ro(session_factory, ACC_A_RES, LAB_A) as session:
        searched = d3_catalog.count_datasets(session)
        for case in cases["cases"]:
            child_id = case["child_dataset_id"]
            upload_meta = _upload_meta(case)
            upload_level = levels[child_id]
            assert upload_level == case["upload_level"], "정답 파일의 업로드 Lv 가 스냅샷과 다르다"

            # **제품이 부르는 그 함수.** 전략(`filtered`)·상한(k=20)·계약 필드 집합이
            # 전부 저쪽 상수에서 온다 — 여기서 갈아끼우지 않는다.
            # ⭑ ⟨`WU-S1b`⟩ `upload_level` 이 **필수 인자**가 됐다. 안 넘기면 터진다 —
            #   적격 필터 없는 측정을 「제품을 쟀다」로 적지 않는다.
            main_payload, main_axes = _ing._lineage_candidates(
                session, lab_id=LAB_A, upload_meta=upload_meta, upload_level=upload_level)
            pool = _corpus_pool(session, upload_meta=upload_meta)
            axes = {**{i: row["axes"] for i, row in pool.items()}, **main_axes}

            true_parents = {p["parent_dataset_id"] for p in case["parents"]}
            descendants = _descendants(parents_of, child_id)
            siblings, sibling_rule = _siblings(parents_of, levels, child_id)
            sibling_rules.add(sibling_rule)

            desc_payload, desc_in_pool = _from_pool(pool, descendants, upload_level)
            sib_payload, sib_in_pool = _from_pool(pool, siblings, upload_level)
            main_ids = [c["datasetId"] for c in main_payload]
            # ⭑ **군마다 거르는 주체가 다르다 — 한 칸에 접지 않는다.**
            #   `eligibility` 군 은 제품 적격 필터가 거르고,
            #   `removed` 군 은 우리가 정답을 지워 만든 군이다.
            built = {
                "main": ("eligibility", main_payload, main_ids, main_ids),
                "removed": ("removed", _from_main(main_payload, true_parents),
                            main_ids, main_ids),
                "descendants": ("eligibility", desc_payload, sorted(descendants), desc_in_pool),
                "siblings": ("eligibility", sib_payload, sorted(siblings), sib_in_pool),
                "removed_and_siblings": ("removed",
                                         _from_main(main_payload, true_parents | siblings),
                                         main_ids, main_ids),
            }
            groups = {}
            for name in GROUPS:
                kind, payload, population, in_pool = built[name]
                kept = [c["datasetId"] for c in payload]
                lost = len(in_pool) - len(kept)
                groups[name] = dict(
                    group=name, filter=kind,
                    population=len(population), population_ids=population,
                    in_pool=len(in_pool), in_pool_ids=in_pool,
                    survived=len(kept), candidate_ids=kept,
                    # ⭑ **몇 건이 무엇에 걸렸나** — 「구조가 막았다」·「후보에 없었다」·
                    #   「우리가 지웠다」 셋을 같은 0 으로 접지 않는다.
                    blocked_by_level=lost if kind == "eligibility" else 0,
                    removed_by_design=lost if kind == "removed" else 0,
                    not_in_pool=len(population) - len(in_pool),
                    candidates=payload,
                    rule_arm=_rule_arm(candidates=payload, axes=axes, upload_meta=upload_meta,
                                       upload_level=upload_level, searched=searched))

            order = [c["datasetId"] for c in main_payload]
            rows.append(dict(
                id=case["id"], child_dataset_id=child_id, child_name=case["child_name"],
                topic=case["topic"], upload_level=upload_level, upload_meta=upload_meta,
                # 러너가 생산자에게 그대로 넘길 값들 — 중계가 넘기는 것과 같은 모양이다.
                file_meta=upload_meta["file"],
                dataset_name_draft=upload_meta.get("datasetNameDraft"),
                subject=upload_meta.get("subject"), searched_count=searched,
                candidates=main_payload, candidate_count=len(main_payload),
                child_itself_in_candidates=child_id in order,
                candidates_outside_corpus=[i for i in order if i not in by_id],
                sibling_rule=sibling_rule,
                descendant_ids=sorted(descendants), sibling_ids=sorted(siblings),
                upload_axes=_axes_json(
                    d3_lineage_signals.UploadAxes.from_file_meta(upload_meta["file"])),
                candidate_axes={i: _axes_json(a) for i, a in axes.items()},
                eligibility={i: row["eligibility"] for i, row in pool.items()},
                derived_level={i: row["derived_level"] for i, row in pool.items()},
                groups=groups,
                parents=[dict(
                    parent_dataset_id=p["parent_dataset_id"], parent_name=p["parent_name"],
                    parent_role=p["parent_role"],
                    in_candidates=p["parent_dataset_id"] in order,
                    rank=(order.index(p["parent_dataset_id"]) + 1
                          if p["parent_dataset_id"] in order else None),
                ) for p in case["parents"]]))

    report = dict(
        kind=("K3 WU-S6 — core-api 가 계보 제안 요청에 실을 후보 + 대조군 4종 + 규칙 팔 기록. "
              "모델 호출 0회 · 판정 게이트 아님"),
        corpus=f"eval/k4-search/fixtures/reference/dev-data-snapshot-v2.json 의 {len(datasets)}건을 일회용 DB 에 재생",
        sample_limits=cases["sample_limits"],
        groups=list(GROUPS), sibling_rules=sorted(sibling_rules),
        strategy=_ing.LINEAGE_CANDIDATE_STRATEGY, k=_ing.LINEAGE_CANDIDATE_LIMIT,
        corpus_size=len(datasets), visible_datasets_in_dev=snapshot["visible_datasets"],
        level_source=("스냅샷 v2 의 processing_level 열(dev processing_level_user_set). "
                      "일회용 DB 에도 같은 값을 싣고 "
                      "`lineage-cases.json` 의 upload_level 과 대조해 오타를 막는다."),
        autometa_note=("`seed_reference_corpus` 는 자동 메타 행을 빈 채로 넣으므로 스냅샷의 "
                       "실제 값을 덮어 썼다. 축별로 채워진 건수는 autometa_axes_present 에 적는다 — "
                       "빈 축은 지어내지 않는다(v2 에서도 variables 는 전 건 비어 있다)."),
        autometa_axes_present={
            axis: sum(1 for m in autometa.values() if m.get(column))
            for axis, column in (("period", "period_start"), ("crs", "crs"), ("grid", "grid"),
                                 ("variables", "variables"), ("fileName", "bundle_file_name"))},
        seed_rows_note=("일회용 DB 에는 시험 시드(DSA1·DSA2)가 같은 연구실에 함께 서 있다."
                        " 그 둘도 사람이 고를 수 있는 진짜 후보라 후보에 세고, 케이스마다"
                        " `candidates_outside_corpus` 로 몇 건인지 드러낸다."),
        child_itself_note=("⭑ 2026-09-24 Ted 결정 ⑦ 뒤 — 업로드의 **이름 초안과 파일명이 둘 다**"
                           " 같은 데이터셋은 후보에서 빠진다(`d3_catalog._self_candidate_ids`)."),
        local_sha=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        cases=rows)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")

    # 기록 자체가 산출물이다 — **구조 무결성만** 단언한다. 수치로 합격/불합격을 가르지 않는다.
    assert len(rows) == cases["sample_limits"]["children"]
    assert sum(len(r["parents"]) for r in rows) == cases["sample_limits"]["edges"]
    assert all(1 <= r["candidate_count"] <= _ing.LINEAGE_CANDIDATE_LIMIT for r in rows)
    assert not any(r["child_itself_in_candidates"] for r in rows), \
        "자식 자신이 후보에 남았다 — 정답 부모가 없을 때 모델이 고르는 것이 바로 그것이다."
    assert all(r["upload_meta"]["file"]["fileName"] for r in rows), \
        "파일명 없는 업로드 메타로는 자기 자신을 가릴 수 없다."
    # ⭑ ⟨2026-09-25 intent O2⟩ **측정 성립 조건** — 업로드 축이 `file_name` 뿐인 자식이 하나라도
    #   있으면 이 실행은 「양쪽 축이 채워진 대조」가 아니다. 여기 exit 1 은 판정 red 가 아니라
    #   「측정 불성립」이고 수치를 쓰지 않는다(사전 등록 78 표 · 후보 절반 칸).
    empty_axes = [r["id"] for r in rows
                  if not any(r["upload_axes"].get(k) for k in
                             ("crs", "grid", "variables", "period_start", "period_end"))]
    assert not empty_axes, f"측정 불성립 — 업로드 축이 file_name 뿐인 자식: {empty_axes}"

    for row in rows:
        child = row["child_dataset_id"]
        truth = {p["parent_dataset_id"] for p in row["parents"]}
        for name, group in row["groups"].items():
            assert child not in group["candidate_ids"], f"{name} 군에 자식 자신이 있다"
        # ⑴·⑴′ — **정답이 실제로 빠졌는가**(생성 오류 방지).
        assert not truth & set(row["groups"]["removed"]["candidate_ids"])
        assert not truth & set(row["groups"]["removed_and_siblings"]["candidate_ids"])
        # ⑵ — ⭑ ⟨2026-09-25 사용자 서명 ②⟩ **필터 일관성**: 모집단에 든 후손마다
        #     「적격 Lv ≤ 업로드 Lv ⇔ ⑵ 후보에 남음」. 종전 단언(모든 후손 적격 Lv > 업로드 Lv ·
        #     `survived` == 0)은 DEM(Lv1) → 후손 Aspect(적격 Lv1)에서 제품 규칙과 어긋났다 —
        #     같은 Lv 후손이 남는 것은 제품 적격 규칙(`d3_catalog.eligibility_level`)대로다.
        #     그 후보에 두 팔이 무엇을 하는지는 러너의 ⑵ 판정(구조 군)이 잰다.
        survivors = set(row["groups"]["descendants"]["candidate_ids"])
        for dataset_id in row["groups"]["descendants"]["in_pool_ids"]:
            eligible = _eligible(row["eligibility"][dataset_id], row["upload_level"])
            assert eligible == (dataset_id in survivors), \
                f"후손 {dataset_id} 의 적격 판정과 ⑵ 후보 잔존이 갈린다 — 필터가 새는 자리다"
        assert survivors <= set(row["groups"]["descendants"]["in_pool_ids"])
        # ⑶ — 형제 군에 자식 자신·진짜 부모가 한 건도 없다.
        assert not truth & set(row["groups"]["siblings"]["candidate_ids"])
        # 모든 군의 후보는 축 기록을 갖는다 — 러너가 되세울 수 있어야 한다.
        for group in row["groups"].values():
            assert set(group["candidate_ids"]) <= set(row["candidate_axes"])
