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
SNAPSHOT_PATH = ROOT / "eval/k4-search/fixtures/reference/dev-data-snapshot-v2.json"
#: ⭑ ⟨2026-09-25 사용자 서명 ①ⓑ⟩ 제안 시점 보류 자동 메타의 고정본(dev 읽기 전용 1회).
HELD_PATH = ROOT / "eval/k3-lineage/fixtures/held-upload-meta-2026-09-25.json"
#: 상한 민감도 실행의 입력(ⓐ = 등록 후 스냅샷 `autometa`). 정답이 아니다 — 러너 `--upload-meta-override`.
SNAPSHOT_META_PATH = ROOT / "eval/k3-lineage/fixtures/snapshot-autometa-upload-meta-2026-09-25.json"


def _cases() -> dict:
    return json.loads(CASES_PATH.read_text())


def _snapshot() -> dict:
    return json.loads(SNAPSHOT_PATH.read_text())


def _held() -> dict:
    return json.loads(HELD_PATH.read_text())


#: ⭑ ⟨WU4 2026-09-25⟩ **가공 단계의 정본은 스냅샷 v2 의 `processing_level` 열이다**
#: (dev `d3_dataset.processing_level_user_set` · `recapture_snapshot.py`). 종전 v1 에는 그 열이
#: 없어 이름의 「(Lv.n)」 을 읽었지만 새 이름에는 그 표기가 없다 — 이름 파싱은 지웠다(두 벌 금지).
_LEVEL_VALUE = re.compile(r"Lv(\d)")


def snapshot_level(dataset: dict) -> int:
    """스냅샷 데이터셋 한 건의 가공 단계. **못 읽으면 터진다 — 0 으로 떨어지지 않는다.**"""
    found = _LEVEL_VALUE.fullmatch(dataset.get("processing_level") or "")
    assert found is not None, f"가공 단계 열을 못 읽었다: {dataset['name']}"
    return int(found.group(1))


def _upload_meta(case: dict) -> dict:
    """케이스 한 건의 **업로드 시점 입력** — 정답 파일의 `upload_meta` 를 그대로 쓴다.

    ⭑ ⟨2026-09-25 사용자 서명 ①ⓑ⟩ 값의 출처는 **제품이 제안 시점에 가진 보류 자동 메타**
    (`HELD_PATH`)다. 정답 파일에 적힌 사본이 그 고정본을 제품 `_uploaded_file_meta` 에 통과시킨
    값과 한 글자도 다르지 않다는 것은 표식 없는 시험
    (`test_계보_정답의_업로드_메타가_보류_자동_메타와_같다`)이 매 게이트에서 지킨다.
    종전(①ⓐ)에는 등록 후 스냅샷 `autometa` 사본이었다 — 그 값은 민감도 입력(`SNAPSHOT_META_PATH`)에만 남는다.
    """
    return json.loads(json.dumps(case["upload_meta"]))


class _HeldEventRows:
    """제품 `UploadLedgerAdapter.held_auto_metadata` 가 읽는 질의 결과 한 벌 — 고정본의 사건 행을 돌려준다.

    파싱은 **제품 메서드 그대로**다(열쇠 선택·`uniform` 규율·기간 풀기). 여기서 값을 따로 뽑지 않는다.
    """

    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows

    def execute(self, *_args, **_kwargs):
        return self

    def mappings(self):
        return self

    def all(self) -> list[dict]:
        return [dict(event_type=r["event_type"], payload=json.dumps(r["payload"]))
                for r in self._rows]


def held_upload_meta(child: dict, held_child: dict) -> dict:
    """스냅샷 자식 + 보류 고정본 → 제품 `_uploaded_file_meta` 가 **제안 시점에** 만들 업로드 메타.

    축 값(format·variables·crs·grid·period)은 고정본의 보류 사건에서만 온다 — 제품 파서
    (`held_auto_metadata`)와 제품 조립기(`_uploaded_file_meta`)를 그대로 통과시킨다.
    ⚠ 파일 목록은 **본체를 앞세운다**(`fileName` 축의 비교 대상은 서명 ① 범위표대로 바꾸지 않는다).
    dev 에서 같은 `_FILES` 정렬이 기준 격자 파일을 앞세운 사실은 고정본 `ledger_files.dev_order_head`
    에 기록만 한다(사전 등록 교란 · 제품 코드 범위 밖).
    """
    from types import SimpleNamespace

    from colab_core.app.routes.ingestion import _uploaded_file_meta
    from colab_core.domains.d5_ingestion import UploadLedgerAdapter

    body = [f for f in child["files"] if f["kind"] == "본체"]
    rest = [f for f in child["files"] if f["kind"] != "본체"]
    files = [SimpleNamespace(file_name=f["file_name"], kind=f["kind"], detected_format=None)
             for f in body + rest]
    adapter = UploadLedgerAdapter(_HeldEventRows(held_child["held_events"]))
    ledger = SimpleNamespace(files=lambda _upload_id: files,
                             held_auto_metadata=adapter.held_auto_metadata)
    meta = {"datasetNameDraft": child["name"], "file": _uploaded_file_meta(ledger, "held")}
    if child["topic"]:
        meta["subject"] = child["topic"]
    return meta


def expected_upload_meta(child: dict) -> dict:
    """스냅샷 자식 한 건 → 제품 `_uploaded_file_meta` 와 **같은 열쇠·같은 생략 규율**의 업로드 메타.

    ⭑ ⟨2026-09-25 서명 ①ⓑ 뒤⟩ 이 값은 정답이 아니라 **상한 민감도 입력(ⓐ)** 의 기준이다.

    중계가 실제로 실어 보내는 값과 같은 모양이다 — `datasetNameDraft`(폼 초안) ·
    `subject`(고정 목록에서 고른 주제) · `file`(`UploadedFileMeta` 한 벌).
    ⚠ `UploadedFileMeta` 는 **파일 이름을 하나만** 나른다(`ingestion.py:499-533` 의 「본체 우선」
    + `partCount`). 여기서 파일 목록 전체를 실으면 제품이 못 가진 신호로 수치를 부풀린다.
    ⚠ 축 값은 자식의 스냅샷 `autometa` 에서만 온다 — 없는 값은 열쇠째 만들지 않는다(빈 배열 포함).
    """
    body = [f for f in child["files"] if f["kind"] == "본체"] or child["files"]
    auto = child.get("autometa") or {}
    file_meta = {"fileName": body[0]["file_name"], "kind": body[0]["kind"]}
    for src, key in (("format", "format"), ("variables", "variables"), ("crs", "crs"),
                     ("grid", "gridDescription"), ("period_start", "periodStart"),
                     ("period_end", "periodEnd")):
        if auto.get(src):
            file_meta[key] = auto[src]
    if len(child["files"]) > 1:
        file_meta["partCount"] = len(child["files"])
    meta = {"datasetNameDraft": child["name"], "file": file_meta}
    if child["topic"]:
        meta["subject"] = child["topic"]
    return meta


def test_계보_정답이_참조_스냅샷과_한_글자도_어긋나지_않는다():
    snapshot, cases = _snapshot(), _cases()
    by_id = {d["id"]: d for d in snapshot["datasets"]}
    assert cases["corpus"] == "eval/k4-search/fixtures/reference/dev-data-snapshot-v2.json"

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
            f"업로드 Lv 가 스냅샷 가공 단계 열과 다르다: {case['id']}"

    # 표본 한계는 **정답 파일이 아니라 스냅샷 쪽에서도** 센다 — 두 수가 갈리면 정답이 낡은 것이다.
    # ⟨WU4⟩ 케이스는 스냅샷 계보의 부분집합이다. 스냅샷 전체 계수(부모 있는
    # 자식 13 · 간선 18)도 따로 박아 두어 스냅샷이 바뀌면 여기서 먼저 red 가 된다(드리프트 검출).
    # ⭑ ⟨2026-09-25 서명 ②⟩ 부모 0 인 DEM(K3-LIN-006)을 더해 자식 6 · 간선 10(간선 불변).
    assert len(cases["cases"]) == 6 and edges == 10
    assert sum(1 for d in snapshot["datasets"] if d["parents"]) == 13
    assert sum(len(d["parents"]) for d in snapshot["datasets"]) == 18
    assert cases["sample_limits"] == {"children": 6, "edges": 10,
                                      "candidate_population": len(snapshot["datasets"]),
                                      "visible_datasets_in_dev": snapshot["visible_datasets"],
                                      "snapshot_children_with_parents": 13,
                                      "snapshot_edges": 18}


def test_계보_정답의_업로드_메타가_보류_자동_메타와_같다():
    """⭑ ⟨2026-09-25 사용자 서명 ①ⓑ⟩ 정답 파일 `upload_meta` = 보류 고정본을 제품 조립기에 통과시킨 값.

    표식이 없어 매 게이트에서 돈다 — 사본이 고정본과 갈리면 측정 전에 여기서 red 다
    (`upload_level` 을 지키는 방식과 같은 규율). 비교는 dict 전체 동치다: 열쇠 하나가
    더 있거나 빠져도, 값이 한 글자 달라도 red. 기준은 스냅샷 `autometa` 가 아니다 —
    등록 후 기간은 제안 시점의 제품에 없는 값이다(① 점검 · 고정본 `registration`).
    """
    snapshot, cases, held = _snapshot(), _cases(), _held()
    by_id = {d["id"]: d for d in snapshot["datasets"]}
    held_by_id = {c["child_dataset_id"]: c for c in held["children"]}
    assert set(held_by_id) == {c["child_dataset_id"] for c in cases["cases"]}
    for case in cases["cases"]:
        assert "upload_meta" in case, f"정답 파일에 upload_meta 가 없다: {case['id']}"
        want = held_upload_meta(by_id[case["child_dataset_id"]], held_by_id[case["child_dataset_id"]])
        assert case["upload_meta"] == want, f"upload_meta 가 보류 자동 메타와 다르다: {case['id']}"
        # 측정 성립 조건(O2) — `fileName` 말고도 근거 축이 하나는 있어야 한다.
        axes = {k for k in ("crs", "gridDescription", "periodStart", "periodEnd", "variables")
                if case["upload_meta"]["file"].get(k)}
        assert axes, f"업로드 축이 fileName 뿐이다 — 측정 불성립: {case['id']}"


def test_상한_민감도_입력이_스냅샷_자동_메타와_같다():
    """⭑ ⟨2026-09-25 서명 ①ⓑ · 상한 민감도⟩ ⓐ 입력 파일 = 자식의 스냅샷 v2 `autometa` 사본.

    정답이 아니다 — 러너 `--upload-meta-override` 로 **같은 후보 JSON** 에 모델 절반만 한 번 건다.
    이 값이 스냅샷과 갈리면 민감도 실행이 「등록 후 자동 메타」를 잰 것이 아니게 되므로 매 게이트에서 막는다.
    """
    snapshot, cases = _snapshot(), _cases()
    sensitivity = json.loads(SNAPSHOT_META_PATH.read_text())
    by_id = {d["id"]: d for d in snapshot["datasets"]}
    rows = {c["child_dataset_id"]: c for c in sensitivity["cases"]}
    assert set(rows) == {c["child_dataset_id"] for c in cases["cases"]}
    for child_id, row in rows.items():
        assert row["upload_meta"] == expected_upload_meta(by_id[child_id]), \
            f"민감도 입력이 스냅샷 autometa 와 다르다: {row['id']}"


def test_계보_형제에_자기_부모가_섞이지_않는다():
    """`test_k3_lineage_probe._siblings` 의 graph 형제는 **자식의 부모를 뺀** 집합이다.

    v2 에서 Prediction(공간상세화)의 부모 DEM 은 Aspect 의 부모이기도 하다 — 부모를 빼지
    않으면 Aspect(실제 보조입력 부모)가 「형제만」 군에 섞여 그 군이 오염된다(§5 O10).
    """
    from test_k3_lineage_probe import _parent_map, _siblings

    snapshot, cases = _snapshot(), _cases()
    parents_of = _parent_map(snapshot)
    levels = {d["id"]: snapshot_level(d) for d in snapshot["datasets"]}
    for case in cases["cases"]:
        siblings, _ = _siblings(parents_of, levels, case["child_dataset_id"])
        assert not siblings & {p["parent_dataset_id"] for p in case["parents"]}, case["id"]
        assert case["child_dataset_id"] not in siblings, case["id"]


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
        meta_by_child = {c["child_dataset_id"]: _upload_meta(c)
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
                    # 일회용 DB 에는 참조 코퍼스 **말고도** 시험 시드(DSA1·DSA2)가 같은 연구실에
                    # 서 있다. 그 둘도 진짜 후보라 세지만, 수치를 읽는 사람이 코퍼스 건수를 기대하지
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
        corpus=f"eval/k4-search/fixtures/reference/dev-data-snapshot-v2.json 의 {len(datasets)}건을 일회용 DB 에 재생",
        sample_limits=cases["sample_limits"],
        visible_datasets_note=("스냅샷의 `visible_datasets` 는 목록이 아니라 dev 의 가시 데이터셋 **수**"
                               f"({snapshot['visible_datasets']})다. 모집단을 좁힐 수 있는 값이 아니라"
                               f" 코퍼스 {len(datasets)}건이 그 부분집합임을 말한다."),
        product_cap_note="제품 권고 상한은 k=20(미해결 질문 ④). 여기서는 전 모집단을 읽고 앞에서 잘라 잰다.",
        recent_order_caveat=("참조 코퍼스는 한 번에 적재돼 `last_modified_at` 이 마이크로초 단위로만"
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
    assert all(s["edges"] == cases["sample_limits"]["edges"]
               for s in (summary(rows) for rows in judged.values()))
