"""K3 J1 — **후보 포함률만** 잰다. 모델 호출 0회 · 계약 0건 · 제품 코드 0건.

`R-K3-RESUME.md` 「게이트 ① 판정」의 WU4a 다. 재는 것은 하나뿐이다 — core-api 가 고른 후보 k건
안에 **사람이 실제로 등록한 부모**가 들어 있는가. 순위·근거·확신도는 모델의 몫이고 여기 없다.

코퍼스 = K4 검색 절반과 같은 일회용 Postgres + 고정 ID(`test_search_reference_evidence.seed_reference_corpus`).
dev 접속·재시드·승인 0건. 판정 게이트가 아니라 **측정**이다 — 표식 `k3_probe` 는 게이트 선택자에서 빠진다.
`COLAB_K3_PROBE_OUT` 이 없으면 skip 이 아니라 error 다(K4 규율 · `test_k4_interpreter_probe.py:1-9`).

⚠ 표식은 **측정 함수에만** 붙인다. 정답 파일의 ID 무결성은 환경변수 없이도 매 게이트에서 돌아야 한다 —
K4 가 「없는 골든 데이터셋」을 실측 직전의 준비 실패로 처음 알았던 자리를 앞으로 당긴다.
"""
import json
import os
import re
from pathlib import Path

import pytest

from conftest import ACC_A_RES, LAB_A, scoped_ro
from test_search_relay import fake_ai  # noqa: F401 — 실제 HTTP 시험 전송을 재사용한다
from test_search_reference_evidence import ROOT, seed_reference_corpus
from colab_core.domains import d3_catalog, d4_lineage

#: 제품 권고 상한은 20(미해결 질문 ④)이고, 5·10 은 **연구실이 커질 때의 민감도**를 보려고 함께 잰다.
K_VALUES = (5, 10, 20)
STRATEGIES = ("recent", "filtered")

CASES_PATH = ROOT / "eval/k3-lineage/lineage-cases.json"
SNAPSHOT_PATH = ROOT / "eval/k4-search/fixtures/reference/dev-data-snapshot.json"


def _cases() -> dict:
    return json.loads(CASES_PATH.read_text())


def _snapshot() -> dict:
    return json.loads(SNAPSHOT_PATH.read_text())


#: ⭑ ⟨K3 `WU-S6` 2026-09-24⟩ **가공 단계의 정본은 이름의 「(Lv.n)」 이다.**
#: 참조 스냅샷의 데이터셋 항목에는 가공 단계 열이 없고(`processing_level` 열쇠 부재)
#: 일회용 DB 의 `processing_level_user_set` 도 비어 있다 — 그러므로 사람이 등록 폼 ①에서
#: 고를 값을 이름에서 읽는 수밖에 없고, **읽는 규칙을 한 곳에 못 박는다.**
#: ⚠ 괄호 안만 본다. 「식생 — Lv.2 모델 보조입력·검증자료 (Lv.1 형제)」 처럼 본문에 다른
#: 단계가 적힌 이름이 실재한다 — 앞에서부터 찾으면 그 이름이 Lv.2 로 읽힌다.
_LEVEL_IN_NAME = re.compile(r"\(Lv\.(\d)")


def snapshot_level(dataset: dict) -> int:
    """스냅샷 데이터셋 한 건의 가공 단계. **못 읽으면 터진다 — 0 으로 떨어지지 않는다.**"""
    assert "processing_level" not in dataset, \
        "스냅샷에 가공 단계 열이 생겼다 — 이름 파싱을 그 열로 바꾼다(두 벌로 두지 않는다)."
    found = _LEVEL_IN_NAME.search(dataset["name"])
    assert found is not None, f"이름에서 가공 단계를 못 읽었다: {dataset['name']}"
    return int(found.group(1))


def _upload_meta(child: dict) -> dict:
    """자식 데이터셋을 **업로드 시점의 입력**으로 되돌린다.

    중계가 실제로 실어 보내는 값과 같은 모양이다 — `datasetNameDraft`(폼 초안) ·
    `subject`(고정 목록에서 고른 주제) · `file`(`UploadedFileMeta` 한 벌).
    ⚠ `UploadedFileMeta` 는 **파일 이름을 하나만** 나른다(`ingestion.py:496-533` 의 「본체 우선」
    + `partCount`). 여기서 파일 목록 전체를 실으면 제품이 못 가진 신호로 수치를 부풀린다.
    """
    body = [f for f in child["files"] if f["kind"] == "본체"] or child["files"]
    meta = {"datasetNameDraft": child["name"],
            "file": {"fileName": body[0]["file_name"], "kind": body[0]["kind"]}}
    if child["topic"]:
        meta["subject"] = child["topic"]
    if len(child["files"]) > 1:
        meta["file"]["partCount"] = len(child["files"])
    return meta


def test_계보_정답이_참조_스냅샷과_한_글자도_어긋나지_않는다():
    snapshot, cases = _snapshot(), _cases()
    by_id = {d["id"]: d for d in snapshot["datasets"]}
    assert cases["corpus"] == "eval/k4-search/fixtures/reference/dev-data-snapshot.json"

    edges = 0
    for case in cases["cases"]:
        child = by_id.get(case["child_dataset_id"])
        assert child is not None, f"자식 ID 가 스냅샷에 없다: {case['child_dataset_id']}"
        assert case["child_name"] == child["name"]
        assert case["topic"] == child["topic"]
        assert len(case["parents"]) == len(child["parents"])
        for got, want in zip(case["parents"], child["parents"], strict=True):
            assert got["parent_dataset_id"] == want["parent_dataset_id"]
            assert got["parent_role"] == want["parent_role"]
            assert got["parent_dataset_id"] in by_id, "부모 ID 가 코퍼스 밖이다"
            assert got["parent_name"] == by_id[got["parent_dataset_id"]]["name"]
        edges += len(case["parents"])

    # ⭑ ⟨K3 `WU-S6`⟩ **업로드 Lv 가 스냅샷과 한 글자도 다르지 않다.** 이 검사는 표식이
    #   없어 매 게이트에서 돈다 — 오타가 실측 직전의 준비 실패로 처음 드러나지 않게 한다
    #   (K4 가 「없는 골든 데이터셋」으로 배운 자리와 같은 규율).
    for case in cases["cases"]:
        assert case["upload_level"] == snapshot_level(by_id[case["child_dataset_id"]]), \
            f"업로드 Lv 가 스냅샷 이름과 다르다: {case['id']}"

    # 표본 한계는 **정답 파일이 아니라 스냅샷 쪽에서도** 센다 — 두 수가 갈리면 정답이 낡은 것이다.
    assert len(cases["cases"]) == 4 and edges == 6
    assert sum(1 for d in snapshot["datasets"] if d["parents"]) == 4
    assert sum(len(d["parents"]) for d in snapshot["datasets"]) == 6
    assert cases["sample_limits"] == {"children": 4, "edges": 6,
                                      "candidate_population": len(snapshot["datasets"]),
                                      "visible_datasets_in_dev": snapshot["visible_datasets"]}


@pytest.mark.k3_probe
def test_k3_후보_포함률을_참조_코퍼스에서_잰다(p2_client, sql, fake_ai, session_factory):
    out_path = Path(os.environ["COLAB_K3_PROBE_OUT"])
    assert not out_path.exists(), "출력이 이미 있다 — 새 실행 경로를 고른다(준비 실패)"
    cases = _cases()
    snapshot = _snapshot()
    _, datasets = seed_reference_corpus(p2_client, sql, fake_ai)
    by_id = {d["id"]: d for d in datasets}
    assert {c["child_dataset_id"] for c in cases["cases"]} <= set(by_id)

    judged = {name: [] for name in STRATEGIES}
    with scoped_ro(session_factory, ACC_A_RES, LAB_A) as session:
        summaries = d4_lineage.LineageSummaryAdapter(session)
        meta_by_child = {c["child_dataset_id"]: _upload_meta(by_id[c["child_dataset_id"]])
                         for c in cases["cases"]}
        for strategy in STRATEGIES:
            for case in cases["cases"]:
                child_id = case["child_dataset_id"]
                # k 를 코퍼스보다 크게 잡아 **모집단 전체의 순서**를 한 번에 읽는다.
                # 상위 k 는 그 앞쪽을 자르면 되고(정렬이 같다), 그래야 필터가 얼마나 좁혔는지도 보인다.
                selected = d3_catalog.select_lineage_candidates(
                    session, lab_id=LAB_A, upload_meta=meta_by_child[child_id],
                    strategy=strategy, k=100, lineage_summaries=summaries)
                order = [c.core.dataset_id for c in selected]
                matched = {c.core.dataset_id: list(c.matched_by) for c in selected}
                judged[strategy].append(dict(
                    child_dataset_id=child_id, child_name=case["child_name"],
                    upload_meta=meta_by_child[child_id],
                    tokens=d3_catalog.lineage_candidate_tokens(meta_by_child[child_id]),
                    population=len(order),
                    # 일회용 DB 에는 참조 9건 **말고도** 시험 시드(DSA1·DSA2)가 같은 연구실에
                    # 서 있다. 그 둘도 진짜 후보라 세지만, 수치를 읽는 사람이 9 를 기대하지
                    # 않도록 **몇 건이 코퍼스 밖인지** 적어 둔다.
                    population_outside_corpus=[i for i in order if i not in by_id],
                    child_itself_in_population=child_id in order,
                    parents=[dict(
                        parent_dataset_id=p["parent_dataset_id"],
                        parent_name=p["parent_name"], parent_role=p["parent_role"],
                        rank=(order.index(p["parent_dataset_id"]) + 1
                              if p["parent_dataset_id"] in order else None),
                        matched_by=matched.get(p["parent_dataset_id"], []),
                        hit={str(k): p["parent_dataset_id"] in order[:k] for k in K_VALUES},
                    ) for p in case["parents"]],
                ))

    def summary(rows):
        edges = [p for row in rows for p in row["parents"]]
        return dict(
            edges=len(edges),
            recall={str(k): sum(1 for p in edges if p["hit"][str(k)]) for k in K_VALUES},
            missed_at_20=[p["parent_dataset_id"] for p in edges if not p["hit"]["20"]],
            population=[row["population"] for row in rows])

    report = dict(
        kind="K3 J1 — core-api 후보 선정의 포함률만. 모델 호출 0회 · 계약 변경 0건 · 판정 게이트 아님",
        corpus="eval/k4-search/fixtures/reference/dev-data-snapshot.json 의 9건을 일회용 DB 에 재생",
        sample_limits=cases["sample_limits"],
        visible_datasets_note=("스냅샷의 `visible_datasets` 는 목록이 아니라 dev 의 가시 데이터셋 **수**"
                               f"({snapshot['visible_datasets']})다. 모집단을 좁힐 수 있는 값이 아니라"
                               f" 코퍼스 {len(datasets)}건이 그 부분집합임을 말한다 — distractor 가 없다."),
        product_cap_note="제품 권고 상한은 k=20(미해결 질문 ④). 여기서는 전 모집단을 읽고 앞에서 잘라 잰다.",
        recent_order_caveat=("참조 9건은 한 번에 적재돼 `last_modified_at` 이 마이크로초 단위로만"
                             " 갈린다. 그래서 `recent` 의 순서는 실제 최신성이 아니라 **적재 역순**이고,"
                             " 그 전략의 recall@5·@10 은 이 코퍼스에서 신호가 아니라 배치의 산물이다."
                             " recall@20(=모집단 전체)만 전략과 무관하게 읽을 수 있다."),
        seed_rows_note=("일회용 DB 에는 시험 시드(DSA1·DSA2)가 같은 연구실에 함께 서 있다."
                        " 그 둘도 사람이 고를 수 있는 진짜 후보라 모집단에 세고, 케이스마다"
                        " `population_outside_corpus` 로 몇 건인지 드러낸다."),
        k_values=list(K_VALUES),
        strategies={name: dict(summary=summary(rows), cases=rows) for name, rows in judged.items()})
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")

    # 측정 자체가 산출물이다 — 구조 무결성만 단언한다. 수치로 합격/불합격을 가르지 않는다.
    assert all(len(rows) == len(cases["cases"]) for rows in judged.values())
    assert all(s["edges"] == 6 for s in (summary(rows) for rows in judged.values()))
