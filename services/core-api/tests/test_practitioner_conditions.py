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


CASES = {case["id"]: case for case in ORACLE["cases"]}
ASSERTABLE = [case["id"] for case in ORACLE["cases"] if case["mode"] != "blocked"]
BLOCKED = [case["id"] for case in ORACLE["cases"] if case["mode"] == "blocked"]


def test_oracle_shape_is_the_one_ted_approved():
    """가능 8 · 부분 3 · blocked 3 — Ted 결정 6 의 집계다. 수가 바뀌면 판정이 바뀐 것이다."""
    modes = [case["mode"] for case in ORACLE["cases"]]
    assert len(modes) == 14
    assert modes.count("full") == 8
    assert modes.count("partial") == 3
    assert modes.count("blocked") == 3
    for case in ORACLE["cases"]:
        if case["mode"] == "blocked":
            assert case["probes"] == [] and case["reason"].strip()
        else:
            assert case["probes"], f"{case['id']} 에 probe 가 없다 — 판정할 것이 없는 사례다"


@pytest.mark.parametrize("case_id", BLOCKED)
def test_blocked_cases_claim_nothing(case_id):
    """구조적 불가 3건은 green 을 주장하지 않는다. 이유만 기록된다."""
    case = CASES[case_id]
    assert case["mode"] == "blocked"
    assert case["expectedCount"] is None


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
