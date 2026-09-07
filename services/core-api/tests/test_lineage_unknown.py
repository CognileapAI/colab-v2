"""WU-B8 · PRD-27 — 계보 상태 6항 판정식 ＋ 「기록 없음」 선언(`lineageUnknown`).

여기서 재는 것 (`dev-package/prd/rounds/R-B-2-server.md` §2 WU-B8 수용 기준 축자)

  ⑴ 부모 0 · 체크 안 함 · 사람 Lv=`Lv1` ⟹ `확인 필요`   ← **이 요구가 새로 만드는 값**
  ⑵ 부모 0 · 체크함                    ⟹ `기록 없음`
  ⑶ 부모 0 · 체크 안 함 · 사람 Lv=`Lv0` ⟹ `원천`        ← ⑷ Lv0 제외 조항
  ⑷ 사람 Lv NULL ∧ `d4_lineage_unknown` 행 있음 ⟹ `기록 없음` (회귀)
  ⑸ 부모 ≥1 경로의 판정이 **종전과 같다** (회귀 증명)
  ⑹ 부모 ≥1 ∧ `lineageUnknown=true` 를 API 로 직접 전송 ⟹ **400**
  ⑺ 자동 `mark_unknown` 이 걷혔다 — 부모 0 · 체크 안 함이면 `d4_lineage_unknown` 행이 **안 선다**

⚠ **판정 순서가 뜻이다** — 위에서부터 먼저 맞는 항이 이긴다. ⑶ 이 ⑷ 보다 위라
   「선언했다」가 「Lv0 이다」를 이긴다.

⚠ **⑷ 는 사람이 고른 Lv 만 본다.** 파생 Lv 는 부모가 없으면 `0` 이라, 파생값으로 판정하면
   부모 0건 행이 **전부** Lv0 이 되어 조항 자체가 무의미해진다. 사람 Lv NULL 은 ⑷ 를 지나간다.

⚠ **여기서 재지 않는 것 — 다른 층**
  · ③ 연결 단계의 체크박스 표시·비활성·라벨 축자 → `frontend/test/lineage-unknown-20260907.test.tsx`.
  · 홈 타일 숫자 ↔ 링크 목록 모수 → 같은 프런트 시험.
  · 스키마는 **변경 0** 이다 — `d4_lineage_unknown` 은 이미 있고 바뀌는 것은 **언제 쓰는가**뿐이다.
"""
from __future__ import annotations

from conftest import DS_A1, TOKEN_RES, auth
from test_dataset_registration import make_upload, register

from colab_core.app.main import API_PREFIX


def _make(client, **extra):
    return register(client, make_upload(client), **extra)


def _created(client, **extra) -> dict:
    r = _make(client, **extra)
    assert r.status_code == 201, r.text
    return r.json()


def _read(client, dataset_id: str) -> dict:
    r = client.get(f"{API_PREFIX}/datasets/{dataset_id}", headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    return r.json()


def _parent(dataset_id: str) -> list[dict]:
    return [{"parentDatasetId": dataset_id, "origin": "manual"}]


# ═══════════ 부모 0 세 갈래 — 이 판정식이 가르는 자리 ═══════════
def test_no_parents_unchecked_with_a_human_level_is_needs_check(p2_client) -> None:
    """⑴ 판정 ⑹ — 「아직 안 골랐다」가 처음으로 `기록 없음` 과 갈린다."""
    made = _created(p2_client(), processingLevelUserSet="Lv1")
    assert made["lineageState"] == "확인 필요"


def test_no_parents_checked_is_no_record(p2_client) -> None:
    """⑵ 판정 ⑶ — 사람이 **선언한** 것만 `기록 없음` 이다."""
    made = _created(p2_client(), processingLevelUserSet="Lv1", lineageUnknown=True)
    assert made["lineageState"] == "기록 없음"


def test_no_parents_unchecked_at_lv0_is_origin(p2_client) -> None:
    """⑶ 판정 ⑷ — Lv0 제외 조항. 이 조항이 없으면 Lv0 전부가 `확인 필요` 로 뜬다."""
    made = _created(p2_client(), processingLevelUserSet="Lv0")
    assert made["lineageState"] == "원천"


def test_a_declaration_beats_lv0(p2_client) -> None:
    """판정 순서 — ⑶ 이 ⑷ 보다 위다. Lv0 이어도 선언했으면 `기록 없음` 이다."""
    made = _created(p2_client(), processingLevelUserSet="Lv0", lineageUnknown=True)
    assert made["lineageState"] == "기록 없음"


def test_lineage_unknown_false_is_the_same_as_absent(p2_client) -> None:
    """`false` 는 「선언하지 않았다」이고 **아무것도 붙이지 않는다** — 자동 표시가 걷혔다."""
    made = _created(p2_client(), processingLevelUserSet="Lv2", lineageUnknown=False)
    assert made["lineageState"] == "확인 필요"


def test_source_label_without_a_human_level_is_still_origin(p2_client) -> None:
    """판정 ⑸ — 사람 Lv 가 NULL 이면 ⑷ 를 지나 원천 표기로 간다(종전 그대로)."""
    made = _created(p2_client(), sourceLabel="기상청")
    assert made["lineageState"] == "원천"


def test_whitespace_only_source_label_is_not_origin(p2_client) -> None:
    """advisor ② — 공백뿐인 `sourceLabel` 은 표기가 **없는 것**이다.

    ⛔ 종전에는 `"  "` 도 truthy 라 ⑸ 에 걸려 `원천` 이 됐다 — 공백은 표기가 아니다.
    사람 Lv `Lv1` ∧ 부모 0 ∧ 선언 없음이면 판정은 ⑹ 로 떨어져 `확인 필요` 다.
    """
    made = _created(p2_client(), processingLevelUserSet="Lv1", sourceLabel="  ")
    assert made["lineageState"] == "확인 필요"


def test_nothing_declared_and_no_human_level_is_needs_check(p2_client) -> None:
    """판정 ⑹ — 사람 Lv 도 원천 표기도 선언도 없으면 `확인 필요` 다.

    ⛔ **종전에는 이 자리가 `기록 없음` 이었다** — 자동 `mark_unknown` 이 그렇게 만들었다.
    """
    made = _created(p2_client())
    assert made["lineageState"] == "확인 필요"


# ═══════════ 자동 표시가 걷혔다 — 행 자체를 확인한다 ═══════════
def test_the_automatic_mark_unknown_row_is_gone(p2_client, sql) -> None:
    """⑺ 부모 0 · 체크 안 함이면 `d4_lineage_unknown` **행이 서지 않는다.**

    화면 값만 보면 판정식 개정으로도 같은 결과가 나올 수 있어, **저장 자리**를 직접 센다.
    """
    client = p2_client()
    made = _created(client, processingLevelUserSet="Lv1")
    rows = sql("SELECT 1 FROM d4_lineage_unknown WHERE dataset_id = :d",
               {"d": made["datasetId"]})
    assert rows == [], "선언하지 않았는데 「기록 없음」 행이 섰다 — 자동 호출이 남아 있다."


def test_a_declaration_writes_the_row(p2_client, sql) -> None:
    """`true` 면 그때 `d4_lineage_unknown` 행이 선다 — 저장 자리는 종전 그대로다(스키마 0)."""
    client = p2_client()
    made = _created(client, processingLevelUserSet="Lv1", lineageUnknown=True)
    rows = sql("SELECT 1 FROM d4_lineage_unknown WHERE dataset_id = :d",
               {"d": made["datasetId"]})
    assert len(rows) == 1


def test_a_human_level_of_null_with_an_unknown_row_stays_no_record(p2_client) -> None:
    """⑷ 회귀 — 사람 Lv 가 NULL 인 행에 표시가 있으면 **종전과 같이** `기록 없음` 이다."""
    client = p2_client()
    made = _created(client, lineageUnknown=True)
    assert made["lineageState"] == "기록 없음"
    assert _read(client, made["datasetId"])["lineageState"] == "기록 없음"


# ═══════════ 부모 ≥1 경로 — 이 개정이 건드리지 않았다 ═══════════
def test_the_parent_path_is_unchanged(p2_client) -> None:
    """⑸ 회귀 — 부모를 붙여 등록하면 판정 ①② 를 타고 종전과 같은 값이 나온다."""
    made = _created(p2_client(), processingLevelUserSet="Lv2",
                    lineageParents=_parent(DS_A1))
    assert made["lineageState"] == "확정"


def test_the_parent_path_ignores_lv0_and_the_source_label(p2_client) -> None:
    """부모가 있으면 ⑷⑸ 는 아예 닿지 않는다 — 위 두 항이 먼저 이긴다."""
    made = _created(p2_client(), processingLevelUserSet="Lv0", sourceLabel="기상청",
                    lineageParents=_parent(DS_A1))
    assert made["lineageState"] == "확정"


def test_a_parent_plus_lineage_unknown_true_is_a_400(p2_client) -> None:
    """⑹ 「모른다」와 「이것이 부모다」를 같은 요청에 담을 수 없다 — **400**."""
    r = _make(p2_client(), processingLevelUserSet="Lv2",
              lineageUnknown=True, lineageParents=_parent(DS_A1))
    assert r.status_code == 400, r.text


def test_lineage_unknown_is_in_the_server_accept_list(p2_client) -> None:
    """계약만 열고 서버 수용 목록을 다음 회차로 미루지 않는다(X2 §5-㉰-4)."""
    r = _make(p2_client(), lineageUnknown=False)
    assert r.status_code == 201, r.text
    assert "계약에 없는 필드다" not in r.text


# ═══ ⭑ ⟨21차 해제 · R-B §5 판정 42⟩ 사후 「기록 없음」 선언 (`declareLineageUnknown`) ═══
#
# **없어서 무엇이 막혀 있었나** — 이 표시를 세울 수 있는 자리가 **등록 순간 하나뿐**이었다
# (`registerDataset.lineageUnknown`). 등록 뒤에 「알아보니 기록이 없더라」를 말할 방법이
# 계약에 0건이라, 그런 데이터셋은 `확인 필요` 에 **영원히** 남았다 — 닫을 수 없는 할 일이다.
_DECLARE = "/datasets/{}/lineage/unknown-declaration"


def _declare(client, dataset_id: str, token: str = TOKEN_RES):
    return client.post(API_PREFIX + _DECLARE.format(dataset_id), headers=auth(token))


def test_declaring_afterwards_turns_the_state_into_no_record(p2_client) -> None:
    """⑴ 부모 0 · 등록 때 체크 안 함 → `확인 필요` 였던 것이 선언으로 `기록 없음` 이 된다."""
    client = p2_client()
    made = _created(client, processingLevelUserSet="Lv1")
    assert made["lineageState"] == "확인 필요"

    r = _declare(client, made["datasetId"])
    assert r.status_code == 200, r.text
    assert r.json()["unknownParents"] is True
    assert _read(client, made["datasetId"])["lineageState"] == "기록 없음"


def test_declaring_with_a_confirmed_parent_is_400(p2_client) -> None:
    """⑵ **확정 부모가 1건이라도 있으면 400 이다** — 등록 경로(⑹)와 **같은 규칙**이다.

    「모른다」와 「이것이 부모다」를 같이 둘 수 없다. 화면도 확정 부모가 있으면 체크박스를
    비활성으로 두지만 **서버 400 이 최종 방어선**이다.
    """
    client = p2_client()
    parent = _created(client)["datasetId"]
    child = _created(client)["datasetId"]
    r = client.post(f"{API_PREFIX}/datasets/{child}/lineage/parents",
                    json={"parentDatasetId": parent}, headers=auth(TOKEN_RES))
    assert r.status_code == 201, r.text

    r = _declare(client, child)
    assert r.status_code == 400, r.text
    assert _read(client, child)["lineageState"] != "기록 없음", "400 인데 표시가 붙었다."


def test_attaching_a_parent_undoes_the_declaration(p2_client) -> None:
    """⑶ **되돌림은 부모를 붙이는 것이다** — 표시는 관계가 붙으면 사라진다
    (`DataModel §4.2`). 「선언 취소」 op 을 만들지 않은 이유가 이것이다."""
    client = p2_client()
    parent = _created(client)["datasetId"]
    child = _created(client)["datasetId"]
    assert _declare(client, child).json()["unknownParents"] is True

    r = client.post(f"{API_PREFIX}/datasets/{child}/lineage/parents",
                    json={"parentDatasetId": parent}, headers=auth(TOKEN_RES))
    assert r.status_code == 201, r.text
    assert r.json()["unknownParents"] is False


def test_declaring_twice_is_the_same_fact(p2_client) -> None:
    """⑷ **멱등이다** — 두 번 눌러도 사실은 하나이고 409 가 아니다."""
    client = p2_client()
    dataset_id = _created(client)["datasetId"]
    assert _declare(client, dataset_id).status_code == 200
    r = _declare(client, dataset_id)
    assert r.status_code == 200 and r.json()["unknownParents"] is True


def test_declaring_needs_the_edit_permission(p2_client, sql) -> None:
    """⑸ 권한은 `addLineageParent` 와 **같다** — 화면에서 숨긴 것은 서버도 막는다
    (`test_lineage_confirm.py::test_lineage_edits_need_the_upload_edit_switch` 와 같은 자리)."""
    client = p2_client()
    dataset_id = _created(client)["datasetId"]
    sql("UPDATE d2_permission_switch SET enabled = false"
        " WHERE account_id = :a AND switch = '업로드·편집'", {"a": "000000000000000000000000A1"},
        account_id="00000000000000000000000AP1")
    try:
        assert _declare(client, dataset_id).status_code == 403
    finally:
        sql("UPDATE d2_permission_switch SET enabled = true"
            " WHERE account_id = :a AND switch = '업로드·편집'",
            {"a": "000000000000000000000000A1"}, account_id="00000000000000000000000AP1")


def test_declaring_on_a_missing_dataset_is_404(p2_client) -> None:
    """⑹ 경계 밖도 404 다 — 존재를 알리지 않는다."""
    assert _declare(p2_client(), "00000000000000000000000000").status_code == 404
