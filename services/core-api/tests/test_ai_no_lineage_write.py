"""**음성 ㉵** — D10 이 D4 에 쓸 경로가 **존재하지 않는다** (`CLAUDE.md §3-2`).

게이트 `ai-no-lineage-write` 가 레포 전체를 보고, 이 파일은 **P2 가 방금 연 쓰기 경로**를
본다. 게이트는 「ai-service 가 D4 를 만지는가」를 묻고, 여기서는 「core-api 의 새 계보 쓰기가
사람 확인 없이 도달 가능한가」를 묻는다 — 같은 불변식의 다른 얼굴이다.

**P2 가 위험을 새로 만들었다.** 이 WU 이전에는 D4 에 쓰는 코드가 아예 없었다.
"""
from __future__ import annotations

import inspect
import pathlib

from conftest import DS_A1, TOKEN_RES, auth

from colab_core.app.main import API_PREFIX

SRC = pathlib.Path(__file__).resolve().parents[1] / "src" / "colab_core"


def test_d4_writes_all_require_a_human_confirmer() -> None:
    """관계를 넣는 함수는 **`confirmed_by` 를 필수 인자로 받는다.**

    기본값이 생기는 순간 「누가 확인했는지 모르는 관계」가 들어갈 수 있게 된다.
    `d4_lineage_edge.confirmed_by_account_id` 가 NOT NULL 인 것의 코드 쪽 표현이다.
    """
    from colab_core.domains import d4_lineage
    signature = inspect.signature(d4_lineage.add_parent)
    confirmed_by = signature.parameters["confirmed_by"]
    assert confirmed_by.default is inspect.Parameter.empty, \
        "`confirmed_by` 에 기본값이 생겼다 — 확인자 없는 계보가 들어갈 수 있다."
    origin = signature.parameters["origin"]
    assert origin.default is inspect.Parameter.empty, \
        "`origin` 에 기본값이 생겼다 — 만들어진 경로가 조용히 정해진다."


def test_no_module_in_core_api_writes_d4_except_the_owning_domain() -> None:
    """D4 표에 쓰는 SQL 은 **`domains/d4_lineage.py` 안에만** 있다."""
    offenders = []
    for path in sorted(SRC.rglob("*.py")):
        if path.name == "d4_lineage.py":
            continue
        text = path.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), start=1):
            upper = line.upper()
            if "D4_" in upper and any(verb in upper for verb in
                                      ("INSERT INTO", "UPDATE ", "DELETE FROM")):
                offenders.append(f"{path.name}:{line_no}: {line.strip()}")
    assert offenders == [], f"D4 에 쓰는 코드가 소유 도메인 밖에 있다:\n" + "\n".join(offenders)


def test_the_ai_relay_cannot_reach_the_lineage_write_path() -> None:
    """중계 모듈이 D4 쓰기 함수를 부르지 않는다 — **제안은 읽기로만 들어온다.**"""
    relay = (SRC / "app" / "relay.py").read_text(encoding="utf-8")
    for forbidden in ("add_parent", "d4_lineage", "confirm_lineage", "mark_unknown"):
        assert forbidden not in relay, f"중계가 계보 쓰기에 닿는다: {forbidden}"


def test_the_suggestion_op_never_writes_anything(p2_client, sql) -> None:
    """제안 조회는 **확정 오퍼레이션이 아니다** — 부르고 나서 D4 가 그대로여야 한다."""
    from test_dataset_registration import make_upload
    client = p2_client()
    receipt = make_upload(client)
    before = sql("SELECT count(*) AS n FROM d4_lineage_edge")[0]["n"]

    r = client.get(f"{API_PREFIX}/uploads/{receipt['uploadId']}/lineage-suggestions",
                   headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    assert sql("SELECT count(*) AS n FROM d4_lineage_edge")[0]["n"] == before
    assert sql("SELECT count(*) AS n FROM d4_lineage_unknown")[0]["n"] >= 0


def test_a_request_cannot_forge_the_ai_confirmed_origin(p2_client, sql) -> None:
    """상세 화면의 수동 추가로는 **`AI 제안을 사람이 확인` 을 만들 수 없다.**

    그 값을 요청이 고를 수 있으면, 사람이 직접 그은 선이 AI 가 그은 것처럼 기록된다 —
    거꾸로도 마찬가지다. 어느 쪽이든 「누가 그었는가」의 기록이 거짓이 된다.
    """
    from test_lineage_confirm import _new_dataset
    client = p2_client()
    child = _new_dataset(client, "위조 시험")
    r = client.post(f"{API_PREFIX}/datasets/{child}/lineage/parents",
                    json={"parentDatasetId": DS_A1, "origin": "AI 제안을 사람이 확인"},
                    headers=auth(TOKEN_RES))
    assert r.status_code == 400
    assert sql("SELECT count(*) AS n FROM d4_lineage_edge WHERE child_dataset_id = :d",
               {"d": child})[0]["n"] == 0
