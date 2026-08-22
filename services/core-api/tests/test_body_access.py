"""`body_access` 실효 2종 — 음성(허용자 아님·만료됨) · 양성(잠긴 메타는 보인다).

`PLAN-SoT §9-㉖` 과 `PERMISSION-PRINCIPLES §D3 게이트 2종` 이 요구한 두 시험이다.
`P0-schema.md §4` 가 「P0 의 다음 조각」으로 남긴 자리를 여기서 닫는다.

**양성 쪽이 위험한 방향이다.** 본체 정책을 메타 테이블까지 넓히면 테스트는 여전히 통과하는데
잠긴 데이터셋이 카탈로그에서 사라지고 `P-13` 이 깨져 E-06 접근 요청 흐름이 죽는다 —
없는 데이터는 요청할 수 없다. 그래서 양성을 **명시적으로** 시험한다.
"""
from __future__ import annotations

from sqlalchemy import text

from conftest import ACC_A_PROF, ACC_A_RES, DS_A1, DS_A2, LAB_A, scoped_ro

_GRANT = text("""
    INSERT INTO d2_dataset_access_grant
      (id, lab_id, dataset_id, grantee_account_id, approver_account_id, approved_at, expires_at)
    VALUES (:id, :lab, :ds, :grantee, :approver, :approved_at, :expires_at)
""")
_FILES_OF = text("SELECT count(*) FROM d3_file WHERE dataset_id = :d")


# ── 음성 ──────────────────────────────────────────────────────────────────────

def test_a_non_grantee_gets_zero_body_rows(session_factory) -> None:
    """허용자 목록에 없는 사람은 잠긴 데이터셋의 **본체가 DB 층에서 0행**이다.

    red 만드는 법 — `DROP POLICY body_access ON d3_file`
    (경계 정책만 남으면 같은 연구실이라는 이유로 본체가 열린다).
    """
    with scoped_ro(session_factory, ACC_A_PROF, LAB_A) as db:
        assert db.execute(_FILES_OF, {"d": DS_A2}).scalar_one() == 0
        # 잠금이 통째로 막는 것이 아니라는 대조 — 열린 데이터셋은 그대로 보인다.
        assert db.execute(_FILES_OF, {"d": DS_A1}).scalar_one() == 2


def test_an_expired_grant_is_the_same_as_no_grant(session_factory) -> None:
    """**만료된** 허용 줄은 있으나 마나다 — 만료를 애플리케이션이 지우러 다니지 않아도 DB 가 거부한다 (P-25).

    같은 트랜잭션에서 **유효한 줄**을 하나 더 넣어 1행이 되는 것까지 본다 —
    그래야 위의 0 이 「원래 0이라 0」이 아니라 **정책이 만든 0**임이 증명된다.

    red 만드는 법 — `body_access` 의 `g.expires_at > now()` 를 지운다
    (= 만료 검사만 빠뜨린 형태. 목록 테스트로는 전혀 안 잡힌다).
    """
    with scoped_ro(session_factory, ACC_A_RES, LAB_A) as db:
        assert db.execute(_FILES_OF, {"d": DS_A2}).scalar_one() == 0

        db.execute(_GRANT, {"id": "0000000000000000000000GRN1", "lab": LAB_A, "ds": DS_A2,
                            "grantee": ACC_A_RES, "approver": ACC_A_PROF,
                            "approved_at": "2025-01-01T00:00:00Z",
                            "expires_at": "2025-07-01T00:00:00Z"})   # 승인일 + 6개월, 이미 지났다
        assert db.execute(_FILES_OF, {"d": DS_A2}).scalar_one() == 0, \
            "만료된 허용 줄이 본체를 열었다 (P-25)."

        db.execute(_GRANT, {"id": "0000000000000000000000GRN2", "lab": LAB_A, "ds": DS_A2,
                            "grantee": ACC_A_RES, "approver": ACC_A_PROF,
                            "approved_at": "2026-08-01T00:00:00Z",
                            "expires_at": "2027-02-01T00:00:00Z"})
        assert db.execute(_FILES_OF, {"d": DS_A2}).scalar_one() == 1, \
            "유효한 허용 줄인데도 본체가 안 보인다 — 정책이 과하게 닫혔다."

        # 허용은 **사람마다** 다르다. 같은 트랜잭션의 다른 주체에게는 여전히 0 이다.
        db.execute(text("SELECT set_config('app.current_account', :a, true)"), {"a": ACC_A_PROF})
        assert db.execute(_FILES_OF, {"d": DS_A2}).scalar_one() == 0


def test_the_body_layer_holds_at_the_http_layer(live_client) -> None:
    """HTTP 층 — 잠긴 데이터셋의 파일 목록은 403 이다. 404 가 아니다(존재는 인정한다)."""
    from colab_core.app.main import API_PREFIX
    h = {"Authorization": "Bearer a1-prof-token"}
    assert live_client.get(f"{API_PREFIX}/datasets/{DS_A1}/files", headers=h).status_code == 200
    assert live_client.get(f"{API_PREFIX}/datasets/{DS_A2}/files", headers=h).status_code == 403


# ── 양성 (P-13 회귀 방지) ─────────────────────────────────────────────────────

def test_locked_dataset_metadata_is_always_readable(session_factory) -> None:
    """잠긴 데이터셋의 **메타는 반드시 조회된다.** 허용자가 아니어도 그렇다.

    red 만드는 법 — `d3_dataset` 에 본체와 같은 조건의 RESTRICTIVE 정책을 하나 더 건다
    (= 「잠김을 RLS 로 통째로 얹는」 그 실수. 정확히 `P-34` 가 금지한 형태).
    """
    with scoped_ro(session_factory, ACC_A_PROF, LAB_A) as db:
        assert db.execute(text("SELECT count(*) FROM d3_dataset WHERE id = :d"),
                          {"d": DS_A2}).scalar_one() == 1
        name = db.execute(text("SELECT name FROM d3_dataset_description WHERE dataset_id = :d"),
                          {"d": DS_A2}).scalar_one()
        assert name, "잠긴 데이터셋의 이름이 사라졌다 — 접근 요청 흐름이 죽는다 (P-13)."
        assert db.execute(text("SELECT count(*) FROM d3_dataset_autometa WHERE dataset_id = :d"),
                          {"d": DS_A2}).scalar_one() == 1
        assert db.execute(text("SELECT state FROM d2_dataset_access WHERE dataset_id = :d"),
                          {"d": DS_A2}).scalar_one() == "잠김"
        assert db.execute(text("SELECT count(*) FROM d2_verified WHERE dataset_id = :d"),
                          {"d": DS_A2}).scalar_one() == 1
        assert db.execute(text("SELECT count(*) FROM d4_lineage_edge WHERE child_dataset_id = :d"),
                          {"d": DS_A2}).scalar_one() == 1, "잠긴 데이터의 계보까지 사라졌다."


def test_no_restrictive_policy_leaked_onto_the_metadata_tables(session_factory) -> None:
    """구조로도 못 박는다 — 메타 테이블에 RESTRICTIVE 정책이 **하나도 없어야** 한다.

    행 개수만 보는 시험은 시드가 마침 열려 있으면 통과해 버린다. 여기서는 카탈로그 판정이
    앞으로 어떤 시드를 만나도 `P-13` 을 깨지 않도록 정책 목록 자체를 오라클로 삼는다.
    """
    rows = session_factory().execute(text(
        "SELECT tablename, policyname, permissive FROM pg_policies WHERE schemaname='public'"
    )).mappings().all()
    by_table: dict[str, list] = {}
    for r in rows:
        by_table.setdefault(r["tablename"], []).append((r["policyname"], r["permissive"]))

    for table in ("d3_dataset", "d3_dataset_description", "d3_dataset_autometa"):
        assert by_table[table] == [("lab_boundary", "PERMISSIVE")], \
            f"{table} 에 정책이 더 붙었다 — 잠긴 데이터가 목록에서 사라진다 (P-13·P-34)."
    # 본체 테이블만 두 층이다. 그리고 두 번째 층은 반드시 RESTRICTIVE 여야 한다 —
    # PERMISSIVE 면 OR 로 합쳐져 두 층이 한 층으로 무너진다 (P0-schema §4 설계판단 2).
    assert sorted(by_table["d3_file"]) == [("body_access", "RESTRICTIVE"),
                                           ("lab_boundary", "PERMISSIVE")]


def test_locked_dataset_still_appears_in_the_catalog(live_client) -> None:
    """HTTP 층 — 잠긴 데이터셋도 목록에 서고, 그 자리가 `접근 요청` 버튼이 된다 (P-13)."""
    from colab_core.app.main import API_PREFIX
    rows = {r["datasetId"]: r for r in live_client.get(
        f"{API_PREFIX}/datasets", headers={"Authorization": "Bearer a1-prof-token"}).json()["items"]}
    assert DS_A2 in rows, "잠긴 데이터셋이 목록에서 사라졌다 — E-06 승인 흐름이 죽는다."
    assert rows[DS_A2]["name"] and rows[DS_A2]["topic"]
    assert rows[DS_A2]["accessState"] == "잠김"
    assert rows[DS_A2]["bodyAccessible"] is False
