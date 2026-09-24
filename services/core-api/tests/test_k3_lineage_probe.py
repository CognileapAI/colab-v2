"""K3 WU4b — **core-api 가 실제로 실어 보낼 후보를 적어 둔다.** 모델 호출 0회.

실측의 두 절반 중 이쪽이다. 모델 절반(`eval/k3-lineage/llm_lineage_probe.py`)은 DB 에
닿지 않으므로, 후보를 고르는 일은 D3 의 주인인 core-api 가 여기서 **제품 함수 그대로**
하고 그 결과를 `COLAB_K3_CANDIDATES_OUT` 에 적는다. 러너는 그 파일을 읽는다 —
두 절반이 같은 후보를 봤다는 것을 그 파일 하나가 보증한다(K4 선례
`test_k4_interpreter_probe.py:1-9` 의 반대 방향: 거기서는 해석을 받아 재생했다).

고르는 자리는 `routes/ingestion._lineage_candidates` 하나다. 여기서 새 선정을 적으면
**중계가 보내는 후보와 실측이 본 후보가 갈리고, 그 어긋남은 아무도 못 센다.**

코퍼스 = K4 검색 절반과 같은 일회용 Postgres + 고정 ID(`seed_reference_corpus`).
dev 접속·재시드·승인 0건. 판정 게이트가 아니라 **측정**이다 — 표식 `k3_probe` 는 게이트
선택자에서 빠진다. 환경변수가 없으면 skip 이 아니라 **error** 다(K4 규율).
"""
import json
import os
import subprocess
from pathlib import Path

import pytest

from conftest import ACC_A_RES, LAB_A, scoped_ro
from test_search_relay import fake_ai  # noqa: F401 — 실제 HTTP 시험 전송을 재사용한다
from test_search_reference_evidence import ROOT, seed_reference_corpus
from test_k3_candidate_recall import _cases, _snapshot, _upload_meta
from colab_core.app.routes import ingestion as _ing

pytestmark = pytest.mark.k3_probe


def test_k3_계보_제안_요청에_실을_후보를_적어_둔다(p2_client, sql, fake_ai, session_factory):
    out_path = Path(os.environ["COLAB_K3_CANDIDATES_OUT"])
    assert not out_path.exists(), "출력이 이미 있다 — 새 실행 경로를 고른다(준비 실패)"
    cases = _cases()
    snapshot = _snapshot()
    _, datasets = seed_reference_corpus(p2_client, sql, fake_ai)
    by_id = {d["id"]: d for d in datasets}
    assert {c["child_dataset_id"] for c in cases["cases"]} <= set(by_id)

    rows = []
    with scoped_ro(session_factory, ACC_A_RES, LAB_A) as session:
        for case in cases["cases"]:
            child_id = case["child_dataset_id"]
            upload_meta = _upload_meta(by_id[child_id])
            # **제품이 부르는 그 함수.** 전략(`filtered`)·상한(k=20)·계약 필드 집합이
            # 전부 저쪽 상수에서 온다 — 여기서 갈아끼우지 않는다.
            candidates = _ing._lineage_candidates(session, lab_id=LAB_A, upload_meta=upload_meta)
            order = [c["datasetId"] for c in candidates]
            rows.append(dict(
                id=case["id"], child_dataset_id=child_id, child_name=case["child_name"],
                topic=case["topic"], upload_meta=upload_meta,
                # 러너가 생산자에게 그대로 넘길 세 값 — 중계(`list_upload_lineage_suggestions`)가
                # 넘기는 것과 같은 모양이다.
                file_meta=upload_meta["file"],
                dataset_name_draft=upload_meta.get("datasetNameDraft"),
                subject=upload_meta.get("subject"),
                candidates=candidates,
                candidate_count=len(candidates),
                child_itself_in_candidates=child_id in order,
                candidates_outside_corpus=[i for i in order if i not in by_id],
                parents=[dict(
                    parent_dataset_id=p["parent_dataset_id"], parent_name=p["parent_name"],
                    parent_role=p["parent_role"],
                    in_candidates=p["parent_dataset_id"] in order,
                    rank=(order.index(p["parent_dataset_id"]) + 1
                          if p["parent_dataset_id"] in order else None),
                ) for p in case["parents"]]))

    report = dict(
        kind="K3 WU4b — core-api 가 계보 제안 요청에 실을 후보 기록. 모델 호출 0회 · 판정 게이트 아님",
        corpus="eval/k4-search/fixtures/reference/dev-data-snapshot.json 의 9건을 일회용 DB 에 재생",
        sample_limits=cases["sample_limits"],
        strategy=_ing.LINEAGE_CANDIDATE_STRATEGY, k=_ing.LINEAGE_CANDIDATE_LIMIT,
        corpus_size=len(datasets), visible_datasets_in_dev=snapshot["visible_datasets"],
        seed_rows_note=("일회용 DB 에는 시험 시드(DSA1·DSA2)가 같은 연구실에 함께 서 있다."
                        " 그 둘도 사람이 고를 수 있는 진짜 후보라 후보에 세고, 케이스마다"
                        " `candidates_outside_corpus` 로 몇 건인지 드러낸다."),
        child_itself_note=("⭑ 2026-09-24 Ted 결정 ⑦ 뒤 — 업로드의 **이름 초안과 파일명이 둘 다**"
                           " 같은 데이터셋은 후보에서 빠진다(`d3_catalog._self_candidate_ids`)."
                           " 이 코퍼스의 자식은 넷 다 이미 등록돼 있으므로 넷 다 자기 자신이"
                           " 빠진 채로 후보를 받는다 — `child_itself_in_candidates` 가 그 증거다."
                           " 이름만 같은 다른 판본은 남는다."),
        local_sha=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        cases=rows)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")

    # 기록 자체가 산출물이다 — 구조 무결성만 단언한다. 수치로 합격/불합격을 가르지 않는다.
    assert len(rows) == 4 and sum(len(r["parents"]) for r in rows) == 6
    assert all(1 <= r["candidate_count"] <= _ing.LINEAGE_CANDIDATE_LIMIT for r in rows)
    # ⭑ 결정 ⑦ — 업로드 메타는 자식의 **실제 이름·실제 파일명**이라(`_upload_meta`) 자기 자신은
    #   중계가 부르는 그 함수 안에서 빠진다. 여기서 남으면 J5 가 잰 그 자리가 그대로다.
    assert not any(r["child_itself_in_candidates"] for r in rows), \
        "자식 자신이 후보에 남았다 — 정답 부모가 없을 때 모델이 고르는 것이 바로 그것이다."
    assert all(r["upload_meta"]["file"]["fileName"] for r in rows), \
        "파일명 없는 업로드 메타로는 자기 자신을 가릴 수 없다."
