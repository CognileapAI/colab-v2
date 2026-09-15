"""`DL-1` 데이터셋 삭제(묘비) — `deleteDataset` · `getDatasetDeletionImpact` 실동작.

오라클은 계약 산문 축자다 (`contracts/seams/fe-core.yaml`) —

  `deleteDataset`  「**소유자 또는 교수만.** 파일·미리보기만 지우고 이름·주제·Lv·계보 관계·
                   프로젝트 연결·Verified 는 남긴다. 되돌리는 전이가 없다.
                   **대기 중인 접근 요청은 자동으로 닫힌다** (§9).」
  `DeletionImpact` `derivedDatasetCount` 「이 데이터로 만든 데이터 N건의 계보에 자리가 남아요」 ·
                   `verified` 「교수 승인이 붙은 데이터예요」 ·
                   `pendingAccessRequestCount` 「대기 중인 접근 요청 N건이 자동으로 닫혀요」

이 파일이 501 표에서 빼 온 두 op — `tests/test_not_implemented.py` 의 `DL_REAL` 이
이 이름들을 여기서 찾는다. **뺀 자리마다 실동작 시험이 있다**는 규칙의 실물이다.

⭑ **픽스처 규율 — 시드 `DSA1`/`DSA2` 를 실삭제하지 않는다.** `conftest._RESTORE` 는
`deleted_at` 을 되돌리지 않고 정리 스코프도 그 자리를 모른다. 시드를 한 번 지우면 그 뒤
모든 회차가 묘비 위에서 돈다. 그래서 시험마다 `_plant(...)` 로 심는다.

⭑ **`d2_verified`·`d2_dataset_access` 는 `conftest._CLEANUP` 에 없다** (D2 는 D3 를 FK 하지
않아 데이터셋을 지워도 남는다). 그래서 아래 `planted` 픽스처가 **자기가 심은 두 표의 행을
자기가 지운다.**

⭑ **잠긴 데이터셋은 「파일 심기 → 잠그기」 순서 고정** — `body_access` RESTRICTIVE 의
`WITH CHECK` 가 잠긴 뒤의 INSERT 를 막는다. 그리고 잠긴 것으로는 **204 경로만** 잰다
(403·500 경로는 열린 것으로) — 잠금과 권한을 한 시험에 섞으면 어느 쪽이 막았는지 못 가른다.
"""
from __future__ import annotations

import pathlib

import pytest

from colab_core.kernel.ids import Ulid
from conftest import (ACC_A_PROF, ACC_A_RES, DS_A1, TOKEN_B, TOKEN_PROF,
                      TOKEN_RES, auth)

PREFIX = "/api/v1"

#: 대기 접근 요청이 닫힐 때 남는 고정 사유. **`[정본 무근거]`** — Ted 판정 ⓕ 대기.
CLOSED_REASON = "데이터가 지워져서 요청이 닫혔어요."
#: 활동 문자열. 선례 = `ACTION_PROJECT_DELETED = "프로젝트 지움"`.
ACTION_DELETED = "데이터셋 지움"
#: 운영자 감사 행위 문자열. **물리 삭제(`ops/purge_datasets.py` 의 `dataset.deleted`)와 다른 값**이다 —
#: 한 데이터셋이 묘비가 된 뒤 물리 삭제되면 같은 대상에 두 행이 쌓이고, 그 둘은 구별돼야 한다.
AUDIT_ACTION_TOMBSTONED = "dataset.tombstoned"


# ════════════════════════════════════════════════════════════════════════════
# 심기 · 치우기
# ════════════════════════════════════════════════════════════════════════════

@pytest.fixture()
def planted(sql):
    """데이터셋을 심는 팩토리 ＋ **자기가 심은 D2 행을 자기가 지우는** 뒷정리.

    돌려주는 것은 `(dataset_id, [storage_key…])` 다. 키는 **원장이 들고 있는 값**이고
    시험은 그 자리에 파일을 써 두었다가 삭제 뒤 부재를 잰다 — 접두 스캔이 아니다.
    """
    made: list[str] = []

    def plant(*, owner: str = ACC_A_PROF, files: int = 1, locked: bool = False,
              verified: bool = False, name: str = "심은 데이터",
              topic: str | None = "강우·강수", source_label: str | None = None) -> tuple[str, list[str]]:
        dataset_id = str(Ulid.generate())
        sql("""INSERT INTO d3_dataset (id, lab_id, owner_account_id, uploader_account_id,
                                       source_label)
               VALUES (:id, current_lab_id(), :owner, :owner, :source)""",
            {"id": dataset_id, "owner": owner, "source": source_label})
        sql("""INSERT INTO d3_dataset_description (dataset_id, lab_id, name, topic, summary)
               VALUES (:id, current_lab_id(), :name, :topic, '심은 요약')""",
            {"id": dataset_id, "name": name, "topic": topic})
        # autometa 행이 **파일보다 앞**에 서야 용량 합계 트리거가 더할 자리가 있다 (seed.sql 주석).
        sql("""INSERT INTO d3_dataset_autometa (dataset_id, lab_id, format, variables, crs,
                                                total_size_bytes)
               VALUES (:id, current_lab_id(), 'CSV', '{강우량}', 'EPSG:5179', 0)""",
            {"id": dataset_id})
        keys: list[str] = []
        # ⚠ **파일 먼저, 잠금 나중** — `body_access` WITH CHECK 가 잠긴 뒤 INSERT 를 막는다.
        for i in range(files):
            file_id = str(Ulid.generate())
            key = f"uploads/{dataset_id}/{file_id}"
            sql("""INSERT INTO d3_file (id, lab_id, dataset_id, kind, file_name, size_bytes,
                                        storage_key, carries_lat, carries_lon)
                   VALUES (:fid, current_lab_id(), :id, '본체', :fname, 7, :key, false, false)""",
                {"fid": file_id, "id": dataset_id, "fname": f"body-{i}.csv", "key": key})
            keys.append(key)
        if locked:
            sql("""INSERT INTO d2_dataset_access (dataset_id, lab_id, state)
                   VALUES (:id, current_lab_id(), '잠김')""", {"id": dataset_id})
        if verified:
            sql("""INSERT INTO d2_verified (dataset_id, lab_id, verified,
                                            approver_account_id, approved_at)
                   VALUES (:id, current_lab_id(), true, :approver, now())""",
                {"id": dataset_id, "approver": ACC_A_PROF})
        made.append(dataset_id)
        return dataset_id, keys

    yield plant

    for dataset_id in made:
        sql("DELETE FROM d2_dataset_access WHERE dataset_id = :id", {"id": dataset_id},
            account_id=ACC_A_PROF)
        sql("DELETE FROM d2_verified WHERE dataset_id = :id", {"id": dataset_id},
            account_id=ACC_A_PROF)


def _root(tmp_path: pathlib.Path) -> pathlib.Path:
    """`p2_client` 가 쓰는 로컬 저장 루트. 키가 곧 경로다 (`LocalFilesystemStorage`)."""
    return tmp_path / "uploads"


def _write_bytes(tmp_path: pathlib.Path, keys: list[str]) -> None:
    for key in keys:
        path = _root(tmp_path) / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"seven!!")


def _present(tmp_path: pathlib.Path, keys: list[str]) -> list[str]:
    return [k for k in keys if (_root(tmp_path) / k).exists()]


class _ExplodingDiscard:
    """저장소가 죽은 자리. `discard` 만 터뜨린다 — 나머지는 부르지 않는다."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def discard(self, *, key, keep=None):
        self.calls.append(key)
        raise OSError("저장소가 응답하지 않는다")


# ════════════════════════════════════════════════════════════════════════════
# ① 501 표 이탈
# ════════════════════════════════════════════════════════════════════════════

def test_the_two_delete_ops_are_no_longer_in_the_501_table(p2_client, planted):
    """501 을 200 으로 바꾼 것이 아니라 **표에서 뺐다**는 것을 여기서 한 번 더 못 박는다.

    `test_not_implemented.py` 는 표를 세고, 이 시험은 **실제 호출이 501 이 아님**을 잰다.
    두 자리가 다 있어야 「표만 고치고 라우트는 501」이 안 지나간다.
    """
    from colab_core.app.routes.not_implemented import OPERATIONS

    names = {op.operation_id for op in OPERATIONS}
    assert "deleteDataset" not in names
    assert "getDatasetDeletionImpact" not in names

    client = p2_client()
    dataset_id, _ = planted(owner=ACC_A_PROF, files=0)
    impact = client.get(f"{PREFIX}/datasets/{dataset_id}/deletion-impact", headers=auth(TOKEN_PROF))
    assert impact.status_code == 200, impact.text
    removed = client.delete(f"{PREFIX}/datasets/{dataset_id}", headers=auth(TOKEN_PROF))
    assert removed.status_code == 204, removed.text


# ════════════════════════════════════════════════════════════════════════════
# ② 400 — 모양부터 본다
# ════════════════════════════════════════════════════════════════════════════

def test_a_malformed_id_is_a_400_on_both_ops(p2_client):
    """모양이 틀린 것은 **경계 밖이 아니라 400** 이다 (`routes/access.py::_living_dataset` 축자).

    404 로 접으면 「없다」와 「그런 모양은 없다」가 같은 답이 되어 화면이 오타를 못 고친다.
    """
    client = p2_client()
    for method, url in (("DELETE", f"{PREFIX}/datasets/not-a-ulid"),
                        ("GET", f"{PREFIX}/datasets/not-a-ulid/deletion-impact")):
        r = client.request(method, url, headers=auth(TOKEN_PROF))
        assert r.status_code == 400, f"{method} {url} → {r.status_code}"
        assert r.json()["code"] == "BAD_REQUEST"


# ════════════════════════════════════════════════════════════════════════════
# ③ 404 셋 — 경계 밖 · 무존재 · 묘비가 **본문까지 같다**
# ════════════════════════════════════════════════════════════════════════════

def test_out_of_lab_missing_and_tombstone_are_the_same_404(p2_client, planted):
    """존재를 알리지 않는다 (P-9·P-10). 계약에 410 이 없으므로 묘비도 404 다.

    ⚠ **본문까지 같아야 한다** — 문구가 갈리면 세 경우가 응답에서 구별된다.
    """
    client = p2_client()
    living, _ = planted(owner=ACC_A_PROF, files=0)
    tomb, _ = planted(owner=ACC_A_PROF, files=0)
    assert client.delete(f"{PREFIX}/datasets/{tomb}",
                         headers=auth(TOKEN_PROF)).status_code == 204

    missing = str(Ulid.generate())
    bodies = []
    for token, dataset_id in ((TOKEN_B, living), (TOKEN_PROF, missing), (TOKEN_PROF, tomb)):
        r = client.delete(f"{PREFIX}/datasets/{dataset_id}", headers=auth(token))
        assert r.status_code == 404, f"{dataset_id} → {r.status_code}"
        bodies.append(r.json())
        g = client.get(f"{PREFIX}/datasets/{dataset_id}/deletion-impact", headers=auth(token))
        assert g.status_code == 404
        bodies.append(g.json())
    assert len({str(sorted(b.items())) for b in bodies}) == 1, \
        "404 세 경우의 본문이 갈렸다 — 그 차이가 곧 존재의 누설이다."


def test_a_second_delete_is_a_404(p2_client, planted):
    """되돌리는 전이가 없다 — 두 번째 DELETE 는 **204 가 아니라 404** 다 (관문 안에서 이미 묘비)."""
    client = p2_client()
    dataset_id, _ = planted(owner=ACC_A_PROF, files=0)
    assert client.delete(f"{PREFIX}/datasets/{dataset_id}",
                         headers=auth(TOKEN_PROF)).status_code == 204
    assert client.delete(f"{PREFIX}/datasets/{dataset_id}",
                         headers=auth(TOKEN_PROF)).status_code == 404


# ════════════════════════════════════════════════════════════════════════════
# ④⑤⑥ 권한 축 — 소유자 또는 교수
# ════════════════════════════════════════════════════════════════════════════

def test_a_researcher_who_is_not_the_owner_gets_403_and_nothing_changes(p2_client, planted, sql,
                                                                        tmp_path):
    """계약 산문 「소유자 또는 교수만」. **403 이고 아무것도 안 바뀐다.**

    ⚠ 이 연구원은 `업로드·편집` 이 켜져 있다(seed) — 그래도 못 지운다. 삭제는 그 스위치와
    **다른 축**이다 (`PERMISSION-PRINCIPLES §2` 새 행 · Ted 판정 ⓑ).
    """
    client = p2_client()
    dataset_id, keys = planted(owner=ACC_A_PROF, files=2)
    _write_bytes(tmp_path, keys)

    r = client.delete(f"{PREFIX}/datasets/{dataset_id}", headers=auth(TOKEN_RES))
    assert r.status_code == 403, r.text
    assert "소유자 또는 교수" in r.json()["message"]

    rows = sql("SELECT deleted_at FROM d3_dataset WHERE id = :id", {"id": dataset_id})
    assert rows and rows[0]["deleted_at"] is None, "403 인데 묘비가 됐다."
    assert sql("SELECT count(*) AS n FROM d3_file WHERE dataset_id = :id",
               {"id": dataset_id})[0]["n"] == 2
    assert _present(tmp_path, keys) == keys, "403 인데 바이트가 지워졌다."


def test_the_owner_even_as_a_researcher_can_delete(p2_client, planted):
    """**연구원도 자기가 올린 데이터셋은 지운다** (사용자 결정 ② · 계약 「소유자 또는 교수」)."""
    client = p2_client()
    dataset_id, _ = planted(owner=ACC_A_RES, files=1)
    r = client.delete(f"{PREFIX}/datasets/{dataset_id}", headers=auth(TOKEN_RES))
    assert r.status_code == 204, r.text
    assert r.content == b""


def test_a_professor_can_delete_someone_elses_dataset(p2_client, planted):
    """교수는 소유자가 아니어도 지운다 — **자기 연구실 안에서만**(타 연구실은 위 404 가 잡는다)."""
    client = p2_client()
    dataset_id, _ = planted(owner=ACC_A_RES, files=1)
    assert client.delete(f"{PREFIX}/datasets/{dataset_id}",
                         headers=auth(TOKEN_PROF)).status_code == 204


# ════════════════════════════════════════════════════════════════════════════
# ⑦ `canDelete` ↔ DELETE 일치
# ════════════════════════════════════════════════════════════════════════════

def test_can_delete_flag_agrees_with_the_delete_gate(p2_client, planted):
    """상세가 내려보내는 `actions.canDelete` 와 실제 관문이 **세 주체에서 일치한다.**

    `routes/catalog.py` 의 인라인 식은 이 회차에 손대지 않는다 — 대신 이 시험이 두 자리를
    묶는다. 갈리면 화면이 버튼을 보여 주고 서버가 403 을 내는(또는 그 반대의) 자리가 된다.
    """
    client = p2_client()
    cases = [
        # (소유자, 부르는 사람 토큰, 기대)
        (ACC_A_RES, TOKEN_RES, True),    # 소유자 연구원
        (ACC_A_PROF, TOKEN_RES, False),  # 비소유 연구원
        (ACC_A_PROF, TOKEN_PROF, True),  # 교수
    ]
    assert len(cases) == 3
    for owner, token, expected in cases:
        dataset_id, _ = planted(owner=owner, files=0)
        detail = client.get(f"{PREFIX}/datasets/{dataset_id}", headers=auth(token))
        assert detail.status_code == 200, detail.text
        assert detail.json()["actions"]["canDelete"] is expected
        removed = client.delete(f"{PREFIX}/datasets/{dataset_id}", headers=auth(token))
        assert (removed.status_code == 204) is expected, \
            f"canDelete={expected} 인데 DELETE 가 {removed.status_code} 다."


# ════════════════════════════════════════════════════════════════════════════
# ⑧ 삭제 뒤 — 내 연구실 410 · 타 연구실 404 · 목록·검색·프로젝트 상세 부재
# ════════════════════════════════════════════════════════════════════════════

def test_after_deletion_my_lab_sees_410_and_other_labs_see_404(p2_client, planted):
    """`getDataset` 만 **내 연구실 묘비에 410** 을 낸다 (17차 해제 · Ted 판정 ② · `〈296〉`-㉰).

    그 행은 지워지기 전에 이미 내 목록에 있었으므로 「지워졌다」가 **새로 알리는 사실이 0** 이다.
    남의 연구실에는 그 사실조차 없다 — 404.
    """
    client = p2_client()
    dataset_id, _ = planted(owner=ACC_A_PROF, files=1)
    assert client.delete(f"{PREFIX}/datasets/{dataset_id}",
                         headers=auth(TOKEN_PROF)).status_code == 204

    mine = client.get(f"{PREFIX}/datasets/{dataset_id}", headers=auth(TOKEN_RES))
    assert mine.status_code == 410, mine.text
    theirs = client.get(f"{PREFIX}/datasets/{dataset_id}", headers=auth(TOKEN_B))
    assert theirs.status_code == 404


def test_after_deletion_it_is_gone_from_list_search_and_project_detail(p2_client, planted, sql):
    """목록·검색·프로젝트 상세에서 **조용히 빠진다** — 세 자리 전부 `deleted_at IS NULL` 이다."""
    client = p2_client()
    dataset_id, _ = planted(owner=ACC_A_PROF, files=1, name="지울 강우 자료")
    sql("""INSERT INTO d6_project_dataset (id, lab_id, project_id, dataset_id, usage_note)
           VALUES (:pd, current_lab_id(), '0000000000000000000000PRJA', :id, '삭제 시험')""",
        {"pd": str(Ulid.generate()), "id": dataset_id})

    listed = client.get(f"{PREFIX}/datasets", headers=auth(TOKEN_PROF)).json()
    before_ids = {row["datasetId"] for row in listed["items"]}
    assert dataset_id in before_ids, "심은 데이터가 목록에 없다 — 이 시험은 오라클이 아니다."
    project_before = client.get(f"{PREFIX}/projects/0000000000000000000000PRJA",
                                headers=auth(TOKEN_PROF)).json()
    assert dataset_id in {d["datasetId"] for d in project_before["datasets"]}

    assert client.delete(f"{PREFIX}/datasets/{dataset_id}",
                         headers=auth(TOKEN_PROF)).status_code == 204

    after = client.get(f"{PREFIX}/datasets", headers=auth(TOKEN_PROF)).json()
    assert dataset_id not in {row["datasetId"] for row in after["items"]}
    searched = client.get(f"{PREFIX}/datasets", params={"q": "지울 강우 자료"},
                          headers=auth(TOKEN_PROF)).json()
    assert dataset_id not in {row["datasetId"] for row in searched["items"]}
    project_after = client.get(f"{PREFIX}/projects/0000000000000000000000PRJA",
                               headers=auth(TOKEN_PROF)).json()
    assert dataset_id not in {d["datasetId"] for d in project_after["datasets"]}


# ════════════════════════════════════════════════════════════════════════════
# ⑨ 남는 것 5 · 사라지는 것 2
# ════════════════════════════════════════════════════════════════════════════

def test_what_stays_and_what_goes(p2_client, planted, sql, tmp_path):
    """계약 산문 축자 — 「파일·미리보기만 지우고 **이름·주제·Lv·계보 관계·프로젝트 연결·
    Verified 는 남긴다**」.

    남는 것 5 = `d3_dataset` 행 · `d3_dataset_description.name` · `d4_lineage_edge` ·
                `d6_project_dataset` · `d2_verified`
    사라지는 것 2 = `d3_file` 0행 · **원장이 알던 저장 키 전건**의 저장소 부재
    """
    client = p2_client()
    parent, _ = planted(owner=ACC_A_PROF, files=0, name="부모")
    dataset_id, keys = planted(owner=ACC_A_PROF, files=2, verified=True, name="지울 자료")
    _write_bytes(tmp_path, keys)
    assert _present(tmp_path, keys) == keys and len(keys) == 2

    sql("""INSERT INTO d4_lineage_edge (id, lab_id, child_dataset_id, parent_dataset_id,
                                        parent_role, method, origin, confirmed_by_account_id,
                                        confirmed_at)
           VALUES (:eid, current_lab_id(), :child, :parent, '주입력', '격자화', 'manual',
                   :actor, now())""",
        {"eid": str(Ulid.generate()), "child": dataset_id, "parent": parent,
         "actor": ACC_A_PROF})
    sql("""INSERT INTO d6_project_dataset (id, lab_id, project_id, dataset_id, usage_note)
           VALUES (:pd, current_lab_id(), '0000000000000000000000PRJA', :id, '삭제 시험')""",
        {"pd": str(Ulid.generate()), "id": dataset_id})

    assert client.delete(f"{PREFIX}/datasets/{dataset_id}",
                         headers=auth(TOKEN_PROF)).status_code == 204

    # ── 남는 것 5 ──
    row = sql("""SELECT deleted_at, deleted_by_account_id, file_count
                   FROM d3_dataset WHERE id = :id""", {"id": dataset_id})
    assert len(row) == 1, "행이 사라졌다 — 묘비는 행을 지우지 않는다."
    assert row[0]["deleted_at"] is not None
    assert row[0]["deleted_by_account_id"] == ACC_A_PROF
    assert sql("SELECT name FROM d3_dataset_description WHERE dataset_id = :id",
               {"id": dataset_id})[0]["name"] == "지울 자료"
    assert sql("SELECT count(*) AS n FROM d4_lineage_edge WHERE child_dataset_id = :id",
               {"id": dataset_id})[0]["n"] == 1
    assert sql("SELECT count(*) AS n FROM d6_project_dataset WHERE dataset_id = :id",
               {"id": dataset_id})[0]["n"] == 1
    assert sql("SELECT verified FROM d2_verified WHERE dataset_id = :id",
               {"id": dataset_id})[0]["verified"] is True

    # ── 사라지는 것 2 ──
    assert sql("SELECT count(*) AS n FROM d3_file WHERE dataset_id = :id",
               {"id": dataset_id})[0]["n"] == 0
    assert row[0]["file_count"] == 0, "statement 트리거가 조각 수를 0 으로 안 내렸다."
    assert sql("SELECT total_size_bytes FROM d3_dataset_autometa WHERE dataset_id = :id",
               {"id": dataset_id})[0]["total_size_bytes"] == 0
    assert _present(tmp_path, keys) == [], "원장이 알던 저장 키의 바이트가 남았다."


# ════════════════════════════════════════════════════════════════════════════
# ⑩ 대기 접근 요청 자동 닫힘
# ════════════════════════════════════════════════════════════════════════════

def test_pending_access_requests_are_closed_and_decided_ones_are_untouched(p2_client, planted,
                                                                           sql):
    """계약 산문 「**대기 중인 접근 요청은 자동으로 닫힌다** (§9)」.

    상태 3값(`검토 대기`·`승인됨`·`거절됨`)에 「닫힘」이 없고, `(state='거절됨') =
    (rejection_reason IS NOT NULL)` CHECK 가 사유를 강제한다 — 그래서 **`거절됨` ＋ 고정 사유**다
    (Ted 판정 ⓕ). **이미 처리된 행은 건드리지 않는다.**
    """
    client = p2_client()
    dataset_id, _ = planted(owner=ACC_A_PROF, files=1, locked=True)

    pending_id = str(Ulid.generate())
    sql("""INSERT INTO d2_dataset_access_request
             (id, lab_id, dataset_id, requester_account_id, reason)
           VALUES (:rid, current_lab_id(), :id, :who, '보고 싶다')""",
        {"rid": pending_id, "id": dataset_id, "who": ACC_A_RES})
    decided_id = str(Ulid.generate())
    sql("""INSERT INTO d2_dataset_access_request
             (id, lab_id, dataset_id, requester_account_id, reason, state,
              decided_by_account_id, decided_at, rejection_reason)
           VALUES (:rid, current_lab_id(), :id, :who, '전에 냈다', '거절됨',
                   :actor, now(), '이번엔 아니다')""",
        {"rid": decided_id, "id": dataset_id, "who": ACC_A_PROF, "actor": ACC_A_PROF})

    impact = client.get(f"{PREFIX}/datasets/{dataset_id}/deletion-impact",
                        headers=auth(TOKEN_PROF)).json()
    assert impact["pendingAccessRequestCount"] == 1, "처리된 행까지 셌다."

    assert client.delete(f"{PREFIX}/datasets/{dataset_id}",
                         headers=auth(TOKEN_PROF)).status_code == 204

    closed = sql("""SELECT state, rejection_reason, decided_by_account_id, decided_at
                      FROM d2_dataset_access_request WHERE id = :rid""",
                 {"rid": pending_id})[0]
    assert closed["state"] == "거절됨"
    assert closed["rejection_reason"] == CLOSED_REASON
    assert closed["decided_by_account_id"] == ACC_A_PROF
    assert closed["decided_at"] is not None

    untouched = sql("""SELECT state, rejection_reason FROM d2_dataset_access_request
                        WHERE id = :rid""", {"rid": decided_id})[0]
    assert untouched["rejection_reason"] == "이번엔 아니다", "처리된 행을 다시 썼다."


def test_deletion_impact_reports_the_three_values(p2_client, planted, sql):
    """`DeletionImpact` 세 칸 — 파생 **생존만** · Verified · 대기 요청 수.

    묘비 자식은 계보 화면이 없어 「자리가 남아요」의 대상이 아니다. 그래서 파생 2 중 1 이
    묘비면 **1** 이다.
    """
    client = p2_client()
    parent, _ = planted(owner=ACC_A_PROF, files=0, verified=True, name="부모")
    alive, _ = planted(owner=ACC_A_PROF, files=0, name="살아 있는 자식")
    doomed, _ = planted(owner=ACC_A_PROF, files=0, name="지울 자식")
    for child in (alive, doomed):
        sql("""INSERT INTO d4_lineage_edge (id, lab_id, child_dataset_id, parent_dataset_id,
                                            parent_role, method, origin,
                                            confirmed_by_account_id, confirmed_at)
               VALUES (:eid, current_lab_id(), :child, :parent, '주입력', '격자화', 'manual',
                       :actor, now())""",
            {"eid": str(Ulid.generate()), "child": child, "parent": parent,
             "actor": ACC_A_PROF})
    sql("""INSERT INTO d2_dataset_access_request
             (id, lab_id, dataset_id, requester_account_id)
           VALUES (:rid, current_lab_id(), :id, :who)""",
        {"rid": str(Ulid.generate()), "id": parent, "who": ACC_A_RES})

    both = client.get(f"{PREFIX}/datasets/{parent}/deletion-impact",
                      headers=auth(TOKEN_PROF)).json()
    assert both == {"derivedDatasetCount": 2, "verified": True,
                    "pendingAccessRequestCount": 1}

    assert client.delete(f"{PREFIX}/datasets/{doomed}",
                         headers=auth(TOKEN_PROF)).status_code == 204
    one = client.get(f"{PREFIX}/datasets/{parent}/deletion-impact",
                     headers=auth(TOKEN_PROF)).json()
    assert one["derivedDatasetCount"] == 1, "묘비 자식을 「자리가 남아요」로 셌다."


def test_deletion_impact_is_gated_the_same_way_as_delete(p2_client, planted):
    """파급 조회도 **같은 관문**을 지난다 — 비소유 연구원은 403 이다.

    관문이 갈리면 「지우지는 못하는데 파급은 읽는다」가 되고, 그 값은 접근 요청 건수라
    남의 데이터의 대기줄 길이가 새어 나간다.
    """
    client = p2_client()
    dataset_id, _ = planted(owner=ACC_A_PROF, files=0)
    r = client.get(f"{PREFIX}/datasets/{dataset_id}/deletion-impact", headers=auth(TOKEN_RES))
    assert r.status_code == 403, r.text


# ════════════════════════════════════════════════════════════════════════════
# ⑪ 잠긴 데이터셋 — `body_access` 함정
# ════════════════════════════════════════════════════════════════════════════

def test_a_locked_dataset_loses_its_files_and_bytes_too(p2_client, planted, sql, tmp_path):
    """⭑ **이 시험이 이 회차의 중심이다.**

    `body_access` RESTRICTIVE 정책에는 **소유자·역할 조항이 없다** — 조건은 「접근 상태(없으면
    연구실 기본값)가 `열림`」 또는 「그 계정에 만료 안 된 허용 줄이 있다」뿐이다
    (`db/platform/schema.sql`). 그래서 잠긴 데이터셋의 `d3_file` 은 **소유자에게도 교수에게도
    0행**이고, 잠금 우회 단계를 빼면 삭제가 키를 못 읽고 행도 못 지운 채 **조용히 0건**으로
    성공한다 — 에러 없이 깨지는 자리다.

    그리고 「열림」 창은 **트랜잭션 안에서만** 존재해야 한다 — 끝난 뒤 접근 상태가 종전 값으로
    돌아와 있는지까지 잰다.
    """
    client = p2_client()
    dataset_id, keys = planted(owner=ACC_A_PROF, files=2, locked=True)
    _write_bytes(tmp_path, keys)
    assert len(keys) == 2 and _present(tmp_path, keys) == keys
    # 전제 확인 — 앱 롤에게 이 데이터셋의 파일은 **지금 0행으로 보인다**
    assert sql("SELECT count(*) AS n FROM d3_file WHERE dataset_id = :id",
               {"id": dataset_id})[0]["n"] == 0, \
        "잠긴 데이터셋의 파일이 보인다 — 이 시험의 전제가 깨졌다."

    assert client.delete(f"{PREFIX}/datasets/{dataset_id}",
                         headers=auth(TOKEN_PROF)).status_code == 204

    # 판정은 경계를 연 채로 본다 — 잠긴 채로 세면 지웠든 안 지웠든 0 이다.
    sql("UPDATE d2_dataset_access SET state = '열림' WHERE dataset_id = :id",
        {"id": dataset_id}, account_id=ACC_A_PROF)
    assert sql("SELECT count(*) AS n FROM d3_file WHERE dataset_id = :id",
               {"id": dataset_id})[0]["n"] == 0, "잠겨 있어서 행을 못 지웠다 (green-by-skip)."
    sql("UPDATE d2_dataset_access SET state = '잠김' WHERE dataset_id = :id",
        {"id": dataset_id}, account_id=ACC_A_PROF)

    assert _present(tmp_path, keys) == [], "잠겨 있어서 키를 못 읽었다 — 바이트가 남았다."
    state = sql("SELECT state FROM d2_dataset_access WHERE dataset_id = :id",
                {"id": dataset_id})
    assert state and state[0]["state"] == "잠김", \
        "「열림」 창이 트랜잭션 밖으로 샜다 — 잠긴 데이터가 열린 채로 남는다."


def test_a_designated_dataset_is_restored_with_its_grant_intact(p2_client, planted, sql,
                                                                tmp_path):
    """⑪-b ⟨리베이스 2026-09-08 · `0017_rb4_access_state_3`⟩ 3값의 세 번째 — `지정 공개`.

    `0032_private_owner_access` 이후 소유자는 `지정 공개` 상태에서도 자기 파일을 볼 수 있다.
    「열림」 창을 지난 뒤 **`지정 공개` 그대로 · `updated_at` 그대로 · 허용 줄 유효** 셋이 다
    돌아와야 한다. 원복이 `잠김` 으로 뭉개면 `set_access_state` 의 만료 갈래처럼 허용자가
    끊기고, `updated_at` 이 밀리면 사람이 바꾼 이력과 구별되지 않는다.
    """
    client = p2_client()
    dataset_id, keys = planted(owner=ACC_A_PROF, files=1, locked=False)
    _write_bytes(tmp_path, keys)
    sql("""INSERT INTO d2_dataset_access (dataset_id, lab_id, state, updated_at)
           VALUES (:id, current_lab_id(), '지정 공개', now() - interval '1 day')""",
        {"id": dataset_id}, account_id=ACC_A_PROF)
    sql("""INSERT INTO d2_dataset_access_grant
             (id, lab_id, dataset_id, grantee_account_id, approver_account_id, expires_at)
           VALUES (:gid, current_lab_id(), :id, :grantee, :approver, now() + interval '6 months')""",
        {"gid": str(Ulid.generate()), "id": dataset_id, "grantee": ACC_A_RES,
         "approver": ACC_A_PROF}, account_id=ACC_A_PROF)
    before = sql("SELECT state, updated_at FROM d2_dataset_access WHERE dataset_id = :id",
                 {"id": dataset_id})[0]
    assert before["state"] == "지정 공개"
    # 전제 — 소유자는 비공개 상태에서도 자기 파일을 볼 수 있다(`0032_private_owner_access`).
    assert sql("SELECT count(*) AS n FROM d3_file WHERE dataset_id = :id",
               {"id": dataset_id}, account_id=ACC_A_PROF)[0]["n"] == 1

    assert client.delete(f"{PREFIX}/datasets/{dataset_id}",
                         headers=auth(TOKEN_PROF)).status_code == 204

    after = sql("SELECT state, updated_at FROM d2_dataset_access WHERE dataset_id = :id",
                {"id": dataset_id})[0]
    assert after["state"] == "지정 공개", "원복이 `지정 공개` 를 다른 값으로 뭉갰다."
    assert after["updated_at"] == before["updated_at"], "원복이 `updated_at` 을 밀었다."
    assert sql("""SELECT count(*) AS n FROM d2_dataset_access_grant
                   WHERE dataset_id = :id AND expires_at > now()""",
               {"id": dataset_id})[0]["n"] == 1, "「열림」 창이 허용 줄을 만료시켰다."
    # 허용자(연구원)에게는 파일이 보이는 경로인데 — 행이 지워졌으니 0 이어야 한다.
    assert sql("SELECT count(*) AS n FROM d3_file WHERE dataset_id = :id",
               {"id": dataset_id}, account_id=ACC_A_RES)[0]["n"] == 0
    assert _present(tmp_path, keys) == []


def test_an_open_dataset_without_an_access_row_stays_without_one(p2_client, planted, sql):
    """접근 상태 행이 **없던** 데이터셋은 삭제 뒤에도 없어야 한다 (`restore` 는 부재도 되돌린다).

    행을 남겨 두면 연구실 기본값을 따르던 데이터가 조용히 명시값으로 바뀐다.
    """
    client = p2_client()
    dataset_id, _ = planted(owner=ACC_A_PROF, files=1, locked=False)
    assert sql("SELECT count(*) AS n FROM d2_dataset_access WHERE dataset_id = :id",
               {"id": dataset_id})[0]["n"] == 0
    assert client.delete(f"{PREFIX}/datasets/{dataset_id}",
                         headers=auth(TOKEN_PROF)).status_code == 204
    assert sql("SELECT count(*) AS n FROM d2_dataset_access WHERE dataset_id = :id",
               {"id": dataset_id})[0]["n"] == 0, "삭제가 접근 상태 행을 남겼다."


# ════════════════════════════════════════════════════════════════════════════
# ⑫ 저장소 실패 = 전체 롤백
# ════════════════════════════════════════════════════════════════════════════

def test_storage_failure_rolls_everything_back_and_a_retry_succeeds(p2_client, planted, sql,
                                                                    tmp_path):
    """바이트를 못 지웠으면 **행도 남는다** — 500 이고 DB 는 무변경이다.

    선례 `delete_dataset_grid_file` 과 같은 태도이고 `U-2` ⓑ(「실패하면 행이 남는다 — 재시도」)와
    같은 성질이다. `discard` 는 없는 키에 조용하므로 재호출이 멱등이다.
    """
    client = p2_client()
    dataset_id, keys = planted(owner=ACC_A_PROF, files=2)
    _write_bytes(tmp_path, keys)
    pending_id = str(Ulid.generate())
    sql("""INSERT INTO d2_dataset_access_request
             (id, lab_id, dataset_id, requester_account_id)
           VALUES (:rid, current_lab_id(), :id, :who)""",
        {"rid": pending_id, "id": dataset_id, "who": ACC_A_RES})

    exploding = _ExplodingDiscard()
    client.app.state.upload_storage = exploding
    boom = client.delete(f"{PREFIX}/datasets/{dataset_id}", headers=auth(TOKEN_PROF))
    assert boom.status_code == 500, boom.text
    assert exploding.calls, "저장소를 아예 안 불렀다 — 이 시험은 오라클이 아니다."

    assert sql("SELECT deleted_at FROM d3_dataset WHERE id = :id",
               {"id": dataset_id})[0]["deleted_at"] is None, "500 인데 묘비가 됐다."
    assert sql("SELECT count(*) AS n FROM d3_file WHERE dataset_id = :id",
               {"id": dataset_id})[0]["n"] == 2, "500 인데 파일 행이 사라졌다."
    assert sql("SELECT state FROM d2_dataset_access_request WHERE id = :rid",
               {"rid": pending_id})[0]["state"] == "검토 대기", "500 인데 요청이 닫혔다."

    # 재호출 — 저장소가 돌아오면 그대로 지나간다
    del client.app.state.upload_storage
    again = client.delete(f"{PREFIX}/datasets/{dataset_id}", headers=auth(TOKEN_PROF))
    assert again.status_code == 204, again.text
    assert _present(tmp_path, keys) == []


# ════════════════════════════════════════════════════════════════════════════
# ⑬ 계보 — 지워진 이웃은 **묘비 노드**다
# ════════════════════════════════════════════════════════════════════════════

def test_a_childs_lineage_shows_the_deleted_parent_as_a_tombstone_node(p2_client, planted, sql):
    """계약 `LineageNode.kind` enum 의 `묘비` 를 서버가 **실제로 낸다.**

    화면(`LineageSection.columnOf`)은 그 값을 처음부터 받고 있었는데 서버가 한 번도 내지
    않았다 — `deletedAt` 도 `None` 하드코딩이었다. 제품 쓰기가 0건이던 동안에는 드러날 수
    없던 결함이고, 이 회차가 그 쓰기를 열면서 드러났다.

    ⚠ 묘비 노드는 **눌리지 않고**(`navigable false`) **본체도 없다**
    (`bodyAccessible false` — 파일 행을 지웠다).
    """
    client = p2_client()
    parent, _ = planted(owner=ACC_A_PROF, files=1, name="지울 부모")
    child, _ = planted(owner=ACC_A_PROF, files=1, name="남는 자식")
    sql("""INSERT INTO d4_lineage_edge (id, lab_id, child_dataset_id, parent_dataset_id,
                                        parent_role, method, origin, confirmed_by_account_id,
                                        confirmed_at)
           VALUES (:eid, current_lab_id(), :child, :parent, '주입력', '격자화', 'manual',
                   :actor, now())""",
        {"eid": str(Ulid.generate()), "child": child, "parent": parent, "actor": ACC_A_PROF})

    before = client.get(f"{PREFIX}/datasets/{child}/lineage", headers=auth(TOKEN_PROF)).json()
    live = [n for n in before["nodes"] if n["datasetId"] == parent]
    assert len(live) == 1 and live[0]["kind"] == "가공 전", \
        "심은 부모가 계보에 안 섰다 — 이 시험은 오라클이 아니다."

    assert client.delete(f"{PREFIX}/datasets/{parent}",
                         headers=auth(TOKEN_PROF)).status_code == 204

    after = client.get(f"{PREFIX}/datasets/{child}/lineage", headers=auth(TOKEN_PROF)).json()
    marks = [n for n in after["nodes"] if n["datasetId"] == parent]
    assert len(marks) == 1, "묘비 노드가 사라졌다 — 지운 데이터가 부모면 자식의 출처가 끊긴다."
    mark = marks[0]
    assert mark["kind"] == "묘비"
    assert mark["name"] == "(지워진 데이터)"
    assert mark["navigable"] is False
    assert mark["bodyAccessible"] is False
    assert mark["deletedAt"] is not None, "지운 날짜가 없다 — hover 문구가 날짜를 못 말한다."

    # 관계 자체는 남는다 (계약 산문 「계보 관계는 남긴다」).
    assert any(e["parentDatasetId"] == parent and e["childDatasetId"] == child
               for e in after["edges"])


def test_a_neighbour_outside_the_lab_keeps_a_null_deleted_at(p2_client, planted, sql):
    """경계 밖 이웃도 `find_dataset_core` 가 `None` 을 낸다 — 그때 **날짜를 지어내지 않는다.**

    묘비와 경계 밖은 화면에서 같은 얼굴이어야 하고(P-9·P-10), 다른 것은 **아는 값이 있는가**
    하나다. 없는 날짜를 채우면 그 자리가 「우리 연구실에서 지웠다」를 알리게 된다.
    """
    client = p2_client()
    child, _ = planted(owner=ACC_A_PROF, files=0, name="남의 것을 부모로 둔 자식")
    # 경계를 넘는 관계는 앱 경로로 만들 수 없다 — 시드 B 연구실 데이터셋을 부모로 심는다.
    sql("""INSERT INTO d4_lineage_edge (id, lab_id, child_dataset_id, parent_dataset_id,
                                        parent_role, method, origin, confirmed_by_account_id,
                                        confirmed_at)
           VALUES (:eid, current_lab_id(), :child, '0000000000000000000000DSB1',
                   '주입력', '격자화', 'manual', :actor, now())""",
        {"eid": str(Ulid.generate()), "child": child, "actor": ACC_A_PROF})

    graph = client.get(f"{PREFIX}/datasets/{child}/lineage", headers=auth(TOKEN_PROF)).json()
    outside = [n for n in graph["nodes"] if n["datasetId"] == "0000000000000000000000DSB1"]
    assert len(outside) == 1
    assert outside[0]["kind"] == "묘비", "경계 밖 이웃도 화면에서는 같은 얼굴이다 (P-9·P-10)."
    assert outside[0]["deletedAt"] is None, "모르는 날짜를 지어냈다."


# ════════════════════════════════════════════════════════════════════════════
# ⑮ 활동 기록
# ════════════════════════════════════════════════════════════════════════════

def test_deleting_records_one_activity_row(p2_client, planted, sql):
    """지운 일도 활동이다 (계약 `listActivities` 산문 · 선례 `프로젝트 지움`).

    `d8_activity` 는 append-only 트리거가 걸려 있어 정리가 안 된다 — 그래서 **절대 개수가
    아니라 자기가 부르기 전후의 차이**를 센다 (`conftest._CLEANUP` 주석).
    """
    client = p2_client()
    dataset_id, _ = planted(owner=ACC_A_PROF, files=1)
    before = sql("SELECT count(*) AS n FROM d8_activity WHERE action = :a",
                 {"a": ACTION_DELETED})[0]["n"]

    assert client.delete(f"{PREFIX}/datasets/{dataset_id}",
                         headers=auth(TOKEN_PROF)).status_code == 204

    after = sql("""SELECT actor_account_id, target_kind, target_id FROM d8_activity
                    WHERE action = :a AND target_id = :id""",
                {"a": ACTION_DELETED, "id": dataset_id})
    assert len(after) == 1, f"「{ACTION_DELETED}」 활동이 1행이 아니다 (직전 계수 {before})."
    assert after[0]["actor_account_id"] == ACC_A_PROF
    assert after[0]["target_kind"] == "데이터셋"


# ════════════════════════════════════════════════════════════════════════════
# ⑯ 운영자 감사 스냅샷 (`0027` 규약)
# ════════════════════════════════════════════════════════════════════════════

def test_deleting_appends_one_operator_audit_snapshot(p2_client, planted, sql):
    """데이터셋 쓰기는 `d3_operator_audit` 에 스냅샷을 남긴다 (`0027` · 선례
    `d3_catalog.update_dataset` 의 `dataset.updated`). 삭제도 데이터셋 쓰기다 —
    남기지 않으면 **무엇이 지워졌는지가 감사 기록에 0건**이고, 활동 한 줄(`d8_activity`)은
    이름·요약을 들지 않아 그 자리를 대신하지 못한다.

    `d3_operator_audit` 는 append-only 트리거가 걸려 정리가 안 된다 — `d8_activity` 와 같은
    규칙으로 **자기가 심은 `target_id` 로만** 센다.
    """
    client = p2_client()
    dataset_id, _ = planted(owner=ACC_A_PROF, files=1, name="감사 대상")

    assert client.delete(f"{PREFIX}/datasets/{dataset_id}",
                         headers=auth(TOKEN_PROF)).status_code == 204

    rows = sql("""SELECT actor_id, action, before_snapshot, after_snapshot
                    FROM d3_operator_audit WHERE target_id = :id""",
               {"id": dataset_id})
    assert len(rows) == 1, "삭제가 운영자 감사 스냅샷을 1행 남기지 않았다."
    assert rows[0]["actor_id"] == ACC_A_PROF
    assert rows[0]["action"] == AUDIT_ACTION_TOMBSTONED
    assert rows[0]["before_snapshot"]["name"] == "감사 대상"
    assert rows[0]["after_snapshot"] is None, "묘비 뒤에는 남는 상태가 없다 — `after` 는 null 이다."


# ════════════════════════════════════════════════════════════════════════════
# ⑯ 미리보기 회수 — **삭제가 그 산출물까지 지운다** (`DL-2` · 22차 ㉯)
#
# 계약 산문 축자는 「파일과 **미리보기**만 지워져요」인데 `DL-1` 까지의 실물은 파일만
# 지웠다. 여기서 재는 것은 **부르는가·언제 부르는가·못 부르면 어떻게 되는가** 셋이고,
# 무엇을 지울지의 판정은 viz 쪽(`tests/test_reclaim_on_delete.py`)이 잰다 — core 는
# 해석하지 않는다.
# ════════════════════════════════════════════════════════════════════════════

class _RecordingPreviews:
    """`app.state.previews` 자리의 기록 대역. `reclaim_previews` 만 쓴다."""

    def __init__(self, *, explode: bool = False, refuse: int | None = None) -> None:
        self.calls: list[dict] = []
        self.explode = explode
        #: viz 가 **읽어 보고 물리친** 상태코드. 못 닿은 것(`explode`)과 **다른 사실**이다.
        self.refuse = refuse

    def reclaim_previews(self, *, lab_id, account_id, target_id, file_ids) -> dict:
        self.calls.append({"lab_id": lab_id, "account_id": account_id,
                           "target_id": target_id, "file_ids": list(file_ids)})
        if self.refuse is not None:
            from colab_core.app.relay import RelayRefused

            raise RelayRefused(self.refuse, {"code": "BAD_REQUEST",
                                             "message": "요청 값이 규칙에 맞지 않는다."})
        if self.explode:
            from colab_core.app.relay import RelayUnavailable

            raise RelayUnavailable("viz-render 에 못 닿았다")
        return {"targetId": target_id, "stale": len(self.calls), "kept": 0,
                "unindexed": 0, "removed": []}


def test_deleting_calls_reclaim_once_with_exactly_the_deleted_file_ids(p2_client, planted, sql,
                                                                       tmp_path):
    """ⓐ **한 번** 부르고, `fileIds` 는 ③ 이 읽은 원장 행의 id 집합 **그대로**다.

    ⚠ 순서는 무관하다 — 집합이 같은가만 본다. 여기서 순서를 잠그면 `files_for_download`
    의 `ORDER BY` 가 이 시험의 오라클이 되고, 그것은 이 op 이 약속한 것이 아니다.
    """
    client = p2_client()
    dataset_id, keys = planted(owner=ACC_A_PROF, files=3)
    _write_bytes(tmp_path, keys)
    expected = {r["id"] for r in sql("SELECT id FROM d3_file WHERE dataset_id = :id",
                                     {"id": dataset_id})}
    assert len(expected) == 3

    previews = _RecordingPreviews()
    client.app.state.previews = previews
    r = client.delete(f"{PREFIX}/datasets/{dataset_id}", headers=auth(TOKEN_PROF))
    assert r.status_code == 204, r.text
    assert len(previews.calls) == 1, previews.calls
    call = previews.calls[0]
    assert call["target_id"] == dataset_id
    assert set(call["file_ids"]) == expected, "지워진 파일 집합과 회수 입력이 갈렸다."


def test_a_failed_reclaim_is_a_500_that_rolls_everything_back_and_a_retry_succeeds(
        p2_client, planted, sql, tmp_path):
    """ⓑ 회수가 못 돌면 **삭제 전체가 되돌아간다** — 묘비도, 파일 행도, 바이트도 그대로다.

    ⑨(바이트 삭제)가 **회수 뒤**라는 것도 여기서 증명된다 — 회수가 터졌을 때 저장소 키가
    남아 있다면 그 루프는 아직 돌지 않은 것이다.
    """
    client = p2_client()
    dataset_id, keys = planted(owner=ACC_A_PROF, files=2)
    _write_bytes(tmp_path, keys)

    client.app.state.previews = _RecordingPreviews(explode=True)
    boom = client.delete(f"{PREFIX}/datasets/{dataset_id}", headers=auth(TOKEN_PROF))
    assert boom.status_code == 500, boom.text
    assert boom.json()["code"] == "PREVIEW_RECLAIM_FAILED", boom.text

    assert sql("SELECT deleted_at FROM d3_dataset WHERE id = :id",
               {"id": dataset_id})[0]["deleted_at"] is None, "500 인데 묘비가 됐다."
    assert sql("SELECT count(*) AS n FROM d3_file WHERE dataset_id = :id",
               {"id": dataset_id})[0]["n"] == 2, "500 인데 파일 행이 사라졌다."
    # ⓓ **릴레이가 ⑨ 앞이다** — 뒤였다면 바이트가 먼저 사라졌을 것이다.
    assert sorted(_present(tmp_path, keys)) == sorted(keys), \
        "회수 실패인데 바이트가 지워졌다 — 릴레이 호출이 저장소 삭제 뒤에 있다."

    client.app.state.previews = _RecordingPreviews()
    again = client.delete(f"{PREFIX}/datasets/{dataset_id}", headers=auth(TOKEN_PROF))
    assert again.status_code == 204, again.text
    assert _present(tmp_path, keys) == []


def test_a_refused_reclaim_is_a_500_that_does_not_tell_the_user_to_retry(p2_client, planted,
                                                                          sql, tmp_path):
    """ⓔ **거절과 장애를 가른다** — viz 가 **읽어 보고 물리친** 4xx 는 재시도해도 같은 답이다.

    「잠시 뒤 다시 시도해 주세요」를 이 갈래에 붙이면 사용자가 고칠 수 없는 것을 반복하게
    만든다. 고칠 사람은 우리이고, 그 단서는 `details.reason` 의 저쪽 상태·본문이다.
    ⚠ **롤백은 같다** — 미리보기를 남긴 채 삭제가 성공하는 자리를 만들지 않는다.
    """
    client = p2_client()
    dataset_id, keys = planted(owner=ACC_A_PROF, files=2)
    _write_bytes(tmp_path, keys)

    client.app.state.previews = _RecordingPreviews(refuse=400)
    r = client.delete(f"{PREFIX}/datasets/{dataset_id}", headers=auth(TOKEN_PROF))
    assert r.status_code == 500, r.text
    body = r.json()
    assert body["code"] == "PREVIEW_RECLAIM_FAILED", body
    assert body["message"] == "미리보기 산출물 회수 요청이 거절되어 삭제를 되돌렸어요."
    assert "다시 시도" not in body["message"], "거절 갈래에 재시도 유도가 붙었다."
    # **단서를 남긴다** — 저쪽이 낸 상태와 본문 요지가 없으면 고칠 사람이 아무것도 못 본다.
    assert "400" in str(body["details"]["reason"]), body["details"]
    assert "BAD_REQUEST" in str(body["details"]["reason"]), body["details"]

    assert sql("SELECT deleted_at FROM d3_dataset WHERE id = :id",
               {"id": dataset_id})[0]["deleted_at"] is None, "500 인데 묘비가 됐다."
    assert sql("SELECT count(*) AS n FROM d3_file WHERE dataset_id = :id",
               {"id": dataset_id})[0]["n"] == 2, "500 인데 파일 행이 사라졌다."
    assert sorted(_present(tmp_path, keys)) == sorted(keys), "500 인데 바이트가 지워졌다."


def test_without_a_viz_relay_the_delete_still_succeeds_and_logs_one_line(p2_client, planted,
                                                                        tmp_path, caplog,
                                                                        capsys):
    """ⓒ viz 가 배선되지 않은 배포(로컬 개발·시험)는 **건너뛰고 한 줄 남긴다.**

    500 으로 내면 싱크가 없는 곳에서 삭제 자체가 불가능해진다 — 그런 배포에는 지울
    산출물도 없다. 다만 **조용히 넘어가지 않는다**: 건너뛴 사실이 로그에 남는다.
    """
    import logging

    client = p2_client()
    assert client.app.state.previews is None, "이 시험은 중계가 없는 앱을 전제한다."
    dataset_id, keys = planted(owner=ACC_A_PROF, files=1)
    _write_bytes(tmp_path, keys)

    with caplog.at_level(logging.INFO):
        r = client.delete(f"{PREFIX}/datasets/{dataset_id}", headers=auth(TOKEN_PROF))
    assert r.status_code == 204, r.text
    skipped = [rec for rec in caplog.records
               if "PREVIEWS_UNCONFIGURED" in rec.getMessage()]
    assert len(skipped) == 1, [rec.getMessage() for rec in caplog.records]
    assert dataset_id in skipped[0].getMessage()

    # ⭑ ⟨2026-09-13 · D9⟩ **표준 로거만으로는 컨테이너 로그에 안 나온다.** core-api 는
    #   `colab_core.*` 로거에 처리기를 달지 않아 그 줄이 루트에서 버려진다 — prod 임시 검증에서
    #   회수 계수가 로그에 한 줄도 없었던 원인이다. 배포가 읽는 자리는 stdout JSON 이다.
    import json as _json

    lines = [_json.loads(ln) for ln in capsys.readouterr().out.splitlines()
             if ln.startswith("{")]
    emitted = [ln for ln in lines if ln.get("event") == "dataset.previews_skipped"]
    assert len(emitted) == 1, [ln.get("event") for ln in lines]
    assert emitted[0]["code"] == "PREVIEWS_UNCONFIGURED"
    assert emitted[0]["datasetId"] == dataset_id
    assert emitted[0]["service"] == "core-api"


# ════════════════════════════════════════════════════════════════════════════
# 시드 보호 — 이 파일이 시드를 만지지 않았음을 스스로 잰다
# ════════════════════════════════════════════════════════════════════════════

def test_the_seed_datasets_are_never_tombstoned_by_this_file(sql):
    """`conftest._RESTORE` 는 `deleted_at` 을 되돌리지 않는다. 한 번 지우면 그 뒤 모든 회차가
    묘비 위에서 돈다 — 그 사고를 이 시험이 상시 감시한다."""
    rows = sql("SELECT id, deleted_at FROM d3_dataset WHERE id IN (:a1, :a2)",
               {"a1": DS_A1, "a2": "0000000000000000000000DSA2"})
    assert len(rows) == 2
    assert all(r["deleted_at"] is None for r in rows), "시드 데이터셋이 묘비가 됐다."
