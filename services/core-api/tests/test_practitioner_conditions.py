"""실무자 사례 14건의 조건 검색 오라클 — DEV 와 같은 28건을 일회용 DB 에 세워 잰다.

**적재 전에 red 를 낸다.** `eval/k4-search/practitioner-conditions.json` 의 probe 들은
`d3_search_evidence` 에 근거가 있어야만 성립한다. 근거 0건이면 조건 검색은 0건을 돌려주고
(`d3_client_search.candidates` 의 LATERAL 이 근거 없는 데이터셋을 통째로 떨군다) 이 파일은
전부 실패한다 — 그것이 전이의 출발점이다((v) 어휘 픽스처 선례와 같은 규율).

자료는 DEV 제품 DB 가 아니라 **게이트가 띄우는 일회용 postgres** 다. 28건의 이름·기간·주제는
`dev-package/tools/dev-seed/canonical-metadata.json` · `plan-manifest.yaml` 전재이고,
근거는 `dev-package/tools/generated/dataset-evidence-payloads.json`(생성물) 이 있을 때만 실린다.
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest
from conftest import ACC_A_RES, LAB_A

pytestmark = pytest.mark.search_golden

REPO = pathlib.Path(__file__).resolve().parents[3]
TOOLS = REPO / "dev-package" / "tools"
ORACLE_PATH = REPO / "eval" / "k4-search" / "practitioner-conditions.json"
CANONICAL_PATH = TOOLS / "dev-seed" / "canonical-metadata.json"
PAYLOAD_PATH = TOOLS / "generated" / "dataset-evidence-payloads.json"

ORACLE = json.loads(ORACLE_PATH.read_text(encoding="utf-8"))
CANONICAL = json.loads(CANONICAL_PATH.read_text(encoding="utf-8"))
NAME_BY_SEQ = {row["seq"]: row["name"] for row in CANONICAL["datasets"]}

#: 프로젝트 4 ↔ `d3_dataset_description.topic` CHECK 6값. `plan-manifest.yaml` 의 project 와
#: 자료 성격(DEM·경사향 = 지형, 토지피복 = LULC)을 그대로 옮긴 것이다.
TOPIC_BY_SEQ = {
    **{seq: "강우·강수" for seq in range(1, 6)},
    6: "식생·NDVI", 7: "식생·NDVI", 8: "식생·NDVI",
    9: "지형·DEM", 10: "지형·DEM", 11: "토지피복·LULC", 12: "식생·NDVI",
    13: "가뭄", 14: "가뭄",
    **{seq: "파일 포맷 예제" for seq in range(15, 29)},
}


def dataset_id(seq: int) -> str:
    return f"{'0' * 22}DV{seq:02d}"


def file_id(seq: int) -> str:
    return f"{'0' * 22}FV{seq:02d}"


def _seed_dev_like(sql) -> None:
    """DEV 와 같은 28건을 A 연구실에 세운다. 데이터셋마다 본체 파일 하나."""
    datasets, descriptions, autometa, files, access = [], [], [], [], []
    for seq, name in sorted(NAME_BY_SEQ.items()):
        did, fid = dataset_id(seq), file_id(seq)
        datasets.append(f"('{did}', current_lab_id(), '{ACC_A_RES}', '{ACC_A_RES}', "
                        f"'2026-03-{seq:02d}T00:00:00Z', '2026-03-{seq:02d}T00:00:00Z')")
        descriptions.append(f"('{did}', current_lab_id(), :name{seq}, '{TOPIC_BY_SEQ[seq]}', "
                            f"'DEV 정본 28건 재현 — seq {seq}')")
        autometa.append(f"('{did}', current_lab_id(), 0)")
        files.append(f"('{fid}', current_lab_id(), '{did}', '본체', 'dev-{seq:02d}.dat', "
                     f"{100 + seq}, 'k/dev{seq:02d}', false, false)")
        access.append(f"('{did}', current_lab_id(), '열림')")
    names = {f"name{seq}": name for seq, name in NAME_BY_SEQ.items()}
    sql("INSERT INTO d3_dataset (id, lab_id, owner_account_id, uploader_account_id,"
        " uploaded_at, last_modified_at) VALUES " + ",".join(datasets))
    sql("INSERT INTO d3_dataset_description (dataset_id, lab_id, name, topic, summary) VALUES "
        + ",".join(descriptions), names)
    sql("INSERT INTO d3_dataset_autometa (dataset_id, lab_id, total_size_bytes) VALUES "
        + ",".join(autometa))
    sql("INSERT INTO d3_file (id, lab_id, dataset_id, kind, file_name, size_bytes, storage_key,"
        " carries_lat, carries_lon) VALUES " + ",".join(files))
    sql("INSERT INTO d2_dataset_access (dataset_id, lab_id, state) VALUES " + ",".join(access))


def _apply_generated_evidence(sql) -> int:
    """생성물 payload 를 같은 적용기로 싣는다. 파일이 없으면 0건 — 그것이 red 의 뜻이다."""
    if not PAYLOAD_PATH.exists():
        return 0
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    from dataset_evidence_apply import apply_payloads  # noqa: PLC0415

    payloads = json.loads(PAYLOAD_PATH.read_text(encoding="utf-8"))
    report = apply_payloads(sql, payloads, reviewer_id=ACC_A_RES)
    return report["evidence"]


@pytest.fixture()
def dev_like(sql):
    _seed_dev_like(sql)
    applied = _apply_generated_evidence(sql)
    return {"applied": applied}


def _search(session_factory, conditions):
    from colab_core.domains import d3_client_search
    from colab_core.kernel.auth import Subject
    from colab_core.kernel.ids import Ulid
    from colab_core.kernel.scope import read_only_scope

    with read_only_scope(session_factory,
                         Subject(account_id=Ulid(ACC_A_RES), lab_id=Ulid(LAB_A))) as session:
        rows, _capped = d3_client_search.candidates(session, dict(conditions))
    by_id = {dataset_id(seq): seq for seq in NAME_BY_SEQ}
    return sorted(by_id[row["dataset_id"]] for row in rows if row["dataset_id"] in by_id)


#: probe 가 없는 두 등급. `blocked` 는 구조적 불가(자료·성분 부재)이고 `blocked_draft` 는
#: 규칙 추론값이 초안이라 이번 회차에 판정하지 않는 것이다(2026-09-21 Ted 결정 1).
NO_CLAIM_MODES = ("blocked", "blocked_draft")

CASES = {case["id"]: case for case in ORACLE["cases"]}
ASSERTABLE = [case["id"] for case in ORACLE["cases"] if case["mode"] not in NO_CLAIM_MODES]
BLOCKED = [case["id"] for case in ORACLE["cases"] if case["mode"] in NO_CLAIM_MODES]


def test_oracle_shape_is_the_one_ted_approved():
    """2회차 집계 — 가능 3 · 부분 5 · blocked 3 · blocked_draft 3.

    1회차는 가능 8 · 부분 3 · blocked 3 이었다. 줄어든 자리는 **규칙 추론값을 초안으로 내린
    것**이다(Ted 결정 1). platform·directObservation 으로 서 있던 probe 는 조건 검색이
    reviewed 만 읽으므로 판정이 서지 않는다 — green 을 주장하지 않고 등급으로 드러낸다.
    수가 바뀌면 판정이 바뀐 것이다.
    """
    modes = [case["mode"] for case in ORACLE["cases"]]
    assert len(modes) == 14
    assert modes.count("full") == 3
    assert modes.count("partial") == 5
    assert modes.count("blocked") == 3
    assert modes.count("blocked_draft") == 3
    for case in ORACLE["cases"]:
        if case["mode"] in NO_CLAIM_MODES:
            assert case["probes"] == [] and case["reason"].strip()
        else:
            assert case["probes"], f"{case['id']} 에 probe 가 없다 — 판정할 것이 없는 사례다"


@pytest.mark.parametrize("case_id", BLOCKED)
def test_blocked_cases_claim_nothing(case_id):
    """판정이 서지 않는 6건은 green 을 주장하지 않는다. 이유만 기록된다."""
    case = CASES[case_id]
    assert case["mode"] in NO_CLAIM_MODES
    assert case["expectedCount"] is None


def test_measure_only_probes_are_excluded_from_the_green_claim():
    """되살린 1회차 probe(2026-09-26 Ted 「전부 권고대로」)는 **초안 값 측정 전용**이다.

    `measureOnlyProbes` 는 초안 기여 측정기(`eval/k4-search/measure_draft_contribution.py`)의 공식
    오라클이고, 이 파일의 조건 검색 판정(`case["probes"]` 만 돈다)에는 들어오지 않는다 — reviewed 만
    읽는 조건 검색에 대고 green 을 주장하지 않는다. 사례의 mode·probe 수도 바꾸지 않는다.
    """
    restored = [(case["id"], probe) for case in ORACLE["cases"]
                for probe in case.get("measureOnlyProbes", [])]
    # 11 = 1회차 복원(2026-09-26 「전부 권고대로」) · +5 = 2회차 지역 「한반도」 region probe
    # (Ted 판정 2026-09-26 「자료 지역 확정」 — PC-1-3·1-4·2-3·2-4·2-7).
    assert len(restored) == 16
    assert "measure_only" in ORACLE["modes"]
    for case_id, probe in restored:
        case = CASES[case_id]
        assert probe["mode"] == "measure_only" and probe["reason"] == "초안 값 측정 전용 · 정답 주장 아님"
        assert case["mode"] != "measure_only"
        assert probe not in case["probes"], f"{case_id} · {probe['name']} 가 green 판정 대상에 섞였다"


def test_rule_inferred_facts_are_never_loaded_as_reviewed():
    """규칙 추론값은 reviewed 사실에 섞이지 않는다 — 초안은 DB 에 실리지 않는다(결정 1).

    `d3_search_evidence` 는 `file_id` 가 PK 이고 `status` 가 행 단위라 한 파일이 reviewed 와
    draft 를 함께 가질 수 없다. 그래서 적용기는 `draftFacts` 를 쓰지 않는다. 이 시험은 생성물이
    그 경계를 지키고 있는지, 초안마다 `rule:<ID>` locator 가 남아 있는지를 본다.
    """
    if not PAYLOAD_PATH.exists():
        pytest.skip("생성물이 없다 — 적재 전 red 의 자리다")
    payloads = json.loads(PAYLOAD_PATH.read_text(encoding="utf-8"))
    rules = set(payloads["rules"])
    drafted = 0
    for row in payloads["datasets"]:
        assert row["status"] == "reviewed"
        # 2026-09-26(PR #174 수정) — 확정값과 **공존**하는 초안은 draftConflictsWithReviewed 에 선언돼야
        # 한다(타일 코드 reviewed region + bbox 초안 「한반도」). reviewed 값 자체는 정본전재 그대로다.
        declared = {c["key"]: c for c in row.get("draftConflictsWithReviewed", [])}
        for key in row["draftFacts"]:
            if key in row["facts"]:
                assert key in declared, f"{row['name']}: 규칙값 {key} 가 선언 없이 reviewed 와 겹친다"
                assert declared[key]["reviewed"] == row["facts"][key]
                assert declared[key]["draft"] == row["draftFacts"][key]
            locator = row["draftProvenance"][key]
            assert "rule:" in locator, f"{row['name']}: 초안 {key} 에 규칙 ID 가 없다"
            assert locator.split("rule:", 1)[1].split(" ", 1)[0] in rules
            drafted += 1
        for key, note in row["provenance"].items():
            assert note.startswith("정본전재"), f"{row['name']}: {key} 가 정본전재가 아니다"
    assert drafted == sum(payloads["ruleSummary"].values())


def test_bbox_auxiliary_rule_only_speaks_inside_the_peninsula():
    """보조 규칙은 한반도 상자 안에 **온전히** 들어갈 때만 말한다(Ted 결정 2 — 보조)."""
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    from dataset_evidence_backfill import region_from_bbox  # noqa: PLC0415

    assert region_from_bbox({"west": 126.0, "south": 34.0,
                             "east": 129.0, "north": 38.0}) == "한반도"
    assert region_from_bbox({"west": 126.0, "south": 34.0,
                             "east": 140.0, "north": 38.0}) is None  # 상자 밖으로 새어 나간다
    assert region_from_bbox({"west": -180.0, "south": -90.0,
                             "east": 180.0, "north": 90.0}) is None  # 전지구
    assert region_from_bbox(None) is None                            # 없는 것은 말하지 않는다
    assert region_from_bbox({"west": 126.0, "south": 34.0}) is None  # 반쪽 상자


@pytest.mark.parametrize("case_id", ASSERTABLE)
def test_condition_search_meets_the_practitioner_case(case_id, dev_like, session_factory):
    case = CASES[case_id]
    for probe in case["probes"]:
        found = _search(session_factory, probe["conditions"])
        where = f"{case_id} · {probe['name']} · 근거 적재 {dev_like['applied']}건"
        if probe.get("expectEmpty"):
            assert found == [], f"{where}: 0건이어야 하는데 {found}"
            continue
        missing = [seq for seq in probe["expectSeq"] if seq not in found]
        assert not missing, f"{where}: 빠진 seq {missing} (실제 {found})"
        leaked = [seq for seq in probe["forbidSeq"] if seq in found]
        assert not leaked, f"{where}: 들어오면 안 되는 seq {leaked} (실제 {found})"
