"""WU-B2 · PRD-16 — 변수를 **행**으로 받는다 (`d3_dataset_variable`).

수용 기준 6건(`R-B-1-db.md §2` WU-B2) 중 **서버가 잴 수 있는 다섯**이 여기 있다 —
나머지 하나(마지막 행 삭제가 화면에서 막힌다)는 프런트 시험이고, 이관 오라클은
`db/platform/tests/0016-drift.sh` 다.

  ㈎ 변수 3행에 각각 다른 단위 → 상세가 **세 행을 각자의 단위와 함께** 낸다
  ㈏ 대표를 안 고르면 → **첫 행**이 대표다 (자동 보정)
  ㈐ 변수 행 0개로 저장 시도 → **400** ＋ 「변수는 하나 이상 있어야 해요」
  ㈑ 대표를 둘 고르면 → **400** (부분 UNIQUE 색인이 500 으로 새지 않는다)
  ㈒ 다른 연구실 계정 → 변수 행 **0건** (cross-tenant 음성)

⛔ **등록·수정 경로가 `d3_dataset_autometa.variables` 를 직접 쓰지 않는다**(PRD-16 축자).
   그 열을 행 표의 미러로 유지하는 트리거는 `M-10` 이고 이 회차 밖이다 — 그래서
   「새로 쓴 변수 행이 그 배열에 안 들어간다」가 **지금은 정상**이고, 아래 시험 하나가
   그 사실 자체를 붙잡아 둔다(다음 회차가 뒤집을 때 이 시험이 먼저 말한다).
"""
from __future__ import annotations

from conftest import ACC_B_PROF, DS_A1, LAB_B, TOKEN_RES, auth, scoped_ro
from sqlalchemy import text
from test_dataset_registration import make_upload, register

from colab_core.app.main import API_PREFIX

THREE = [
    {"name": "precipitation", "unit": "mm", "valueRange": "0~350",
     "missingRate": "0.2%", "representative": True},
    {"name": "temperature", "unit": "℃", "valueRange": "-30~40", "missingRate": None},
    {"name": "runoff", "unit": "m3/s"},
]


def _register_with(client, **extra):
    return register(client, make_upload(client), **extra)


# ═══════ ㈎ 세 행이 각자의 단위와 함께 보인다 ══════════════════════════════
def test_three_rows_keep_their_own_units(p2_client, sql) -> None:
    """PRD-16 이 여는 문장 — 「변수 3개에 단위 1개면 어느 변수 것인지 알 수 없다.」"""
    client = p2_client()
    r = _register_with(client, variables=THREE)
    assert r.status_code == 201, r.text
    got = r.json()["basicInfo"]["variables"]
    assert [v["name"] for v in got] == ["precipitation", "temperature", "runoff"]
    assert [v["unit"] for v in got] == ["mm", "℃", "m3/s"]
    assert [v["valueRange"] for v in got] == ["0~350", "-30~40", None]
    assert [v["missingRate"] for v in got] == ["0.2%", None, None]

    rows = sql("SELECT ordinal, name, unit FROM d3_dataset_variable"
               "  WHERE dataset_id = :d ORDER BY ordinal", {"d": r.json()["datasetId"]})
    assert [(x["ordinal"], x["name"], x["unit"]) for x in rows] == [
        (1, "precipitation", "mm"), (2, "temperature", "℃"), (3, "runoff", "m3/s")]


def test_detail_read_path_returns_the_rows(p2_client) -> None:
    """상세 조회도 **같은 객체 배열**이다 — 등록 응답만 맞고 상세가 다르면 화면이 갈린다."""
    client = p2_client()
    dataset_id = _register_with(client, variables=THREE).json()["datasetId"]
    detail = client.get(f"{API_PREFIX}/datasets/{dataset_id}", headers=auth(TOKEN_RES))
    assert detail.status_code == 200, detail.text
    got = detail.json()["basicInfo"]["variables"]
    assert [v["name"] for v in got] == ["precipitation", "temperature", "runoff"]
    assert [v["representative"] for v in got] == [True, False, False]


# ═══════ ㈏ 대표를 안 고르면 첫 행이 대표다 ════════════════════════════════
def test_first_row_becomes_representative_when_nobody_is_chosen(p2_client, sql) -> None:
    """**대표 없는 저장이 성립하지 않는다**(PRD-16 축자). 서버가 자동 보정한다."""
    client = p2_client()
    r = _register_with(client, variables=[{"name": "가"}, {"name": "나"}, {"name": "다"}])
    assert r.status_code == 201, r.text
    assert [v["representative"] for v in r.json()["basicInfo"]["variables"]] == [True, False, False]
    rows = sql("SELECT ordinal FROM d3_dataset_variable"
               "  WHERE dataset_id = :d AND is_representative", {"d": r.json()["datasetId"]})
    assert [x["ordinal"] for x in rows] == [1]


# ═══════ ㈐ 0행은 400 ＋ 정해진 문면 ═══════════════════════════════════════
def test_empty_variable_list_is_rejected_with_the_copy(p2_client) -> None:
    """마지막 행 삭제를 화면이 막고, **서버가 뒷문**이다 (PRD-16 「행이 0개인 데이터셋은
    허용하지 않는다」). 문면은 rev1 축자 그대로다."""
    client = p2_client()
    created = _register_with(client, variables=[])
    assert created.status_code == 400, created.text
    assert created.json()["message"] == "변수는 하나 이상 있어야 해요"

    dataset_id = _register_with(client, variables=THREE).json()["datasetId"]
    patched = client.patch(f"{API_PREFIX}/datasets/{dataset_id}", json={"variables": []},
                           headers=auth(TOKEN_RES))
    assert patched.status_code == 400, patched.text
    assert patched.json()["message"] == created.json()["message"], \
        "생성과 수정이 다른 문면을 낸다 — 검사기가 두 벌이다."


def test_null_variable_list_is_rejected_like_the_empty_one(p2_client) -> None:
    """`variables: null` 도 **400** 이다 — 계약이 `null` 을 안 받는다(`DatasetCreate`).
    생성이 조용히 버리면 같은 「행 0개」가 생성에서만 통과해 수정과 응답이 갈린다."""
    client = p2_client()
    created = _register_with(client, variables=None)
    assert created.status_code == 400, created.text

    dataset_id = _register_with(client, variables=THREE).json()["datasetId"]
    patched = client.patch(f"{API_PREFIX}/datasets/{dataset_id}", json={"variables": None},
                           headers=auth(TOKEN_RES))
    assert patched.status_code == 400, patched.text


# ═══════ ㈑ 대표 둘은 400 (500 이 아니다) ═════════════════════════════════
def test_two_representatives_are_a_400_not_a_500(p2_client) -> None:
    """부분 UNIQUE 색인이 뒷문이고 **앞문이 400** 이다. 앞문이 없으면 IntegrityError 가
    500 으로 나가 사용자의 선택이 서버 잘못이 된다 (`CODE-REVIEW-20260903` #12 와 같은 자리)."""
    client = p2_client()
    r = _register_with(client, variables=[
        {"name": "가", "representative": True}, {"name": "나", "representative": True}])
    assert r.status_code == 400, r.text


def test_blank_variable_name_is_a_400(p2_client) -> None:
    """이름은 **빈 문자열이 아니다** — DB CHECK 가 뒷문이고 여기가 앞문이다."""
    client = p2_client()
    assert _register_with(client, variables=[{"name": "  "}]).status_code == 400


# ═══════ 수정 = 행 집합 통째 교체 ═════════════════════════════════════════
def test_update_replaces_the_whole_row_set(p2_client, sql) -> None:
    """**delete-then-insert 한 트랜잭션.** 부분 갱신이 아니다 — 3행을 2행으로 고치면
    셋째 행이 남지 않는다(남으면 화면과 DB 가 갈린다)."""
    client = p2_client()
    dataset_id = _register_with(client, variables=THREE).json()["datasetId"]
    r = client.patch(f"{API_PREFIX}/datasets/{dataset_id}",
                     json={"variables": [{"name": "runoff", "unit": "m3/s"},
                                         {"name": "swe", "representative": True}]},
                     headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    rows = sql("SELECT ordinal, name, is_representative FROM d3_dataset_variable"
               "  WHERE dataset_id = :d ORDER BY ordinal", {"d": dataset_id})
    assert [(x["ordinal"], x["name"], x["is_representative"]) for x in rows] == [
        (1, "runoff", False), (2, "swe", True)]


# ═══════ ㈒ cross-tenant 음성 ═════════════════════════════════════════════
def test_another_lab_sees_zero_variable_rows(session_factory, sql) -> None:
    """다른 연구실 계정의 스코프에서는 **0건**이다 (`CLAUDE.md §3-5`).

    red 만드는 법 — `ALTER POLICY lab_boundary ON d3_dataset_variable USING (true)`.
    """
    with scoped_ro(session_factory, ACC_B_PROF, LAB_B) as db:
        n = db.execute(text("SELECT count(*) FROM d3_dataset_variable"
                            " WHERE dataset_id = :d"), {"d": DS_A1}).scalar_one()
        assert n == 0, "다른 연구실에서 변수 행이 보였다."
        leaked = db.execute(text("SELECT count(*) FROM d3_dataset_variable"
                                 " WHERE lab_id <> :own"), {"own": LAB_B}).scalar_one()
        assert leaked == 0


# ═══════ M-10 이 섰다 — 배열은 행 표의 **미러**다 ═════════════════════════
def test_registration_does_not_write_autometa_variables(p2_client, sql) -> None:
    """**등록·수정 경로는 `autometa.variables` 를 직접 쓰지 않는다**(PRD-16 축자
    「트리거만 쓴다」). 그 성질은 그대로이고 **기대값만 뒤집혔다.**

    ⭑ **⟨개정 2026-09-07 · `M-10` · WU-B7⟩ 배열은 이제 행 표의 미러다.**
    ／ 종전 ~~「그 배열이 비어 있는 것이 정상이고 검색이 새 변수명을 못 잡는다」~~ —
    그 기대는 **트리거가 없던 동안**의 잔여 위험을 코드로 붙잡아 둔 것이었고(`0016` 모듈
    산문), `0019` 가 트리거를 세우면서 닫혔다.

    ⚠ **여전히 등록 경로가 그 배열을 직접 쓰지 않는다** — 쓰는 것은 **트리거**다.
    그것을 이 시험이 잰다: 배열이 **행 표와 정확히 같고**(순서까지) 등록이 임의로 넣은
    값이 아니다.
    """
    client = p2_client()
    dataset_id = _register_with(client, variables=THREE).json()["datasetId"]
    mirrored = sql("SELECT variables FROM d3_dataset_autometa WHERE dataset_id = :d",
                   {"d": dataset_id})[0]["variables"]
    canon = [r["name"] for r in sql(
        "SELECT name FROM d3_dataset_variable WHERE dataset_id = :d ORDER BY ordinal",
        {"d": dataset_id})]
    assert len(canon) > 0, "행 표가 비었다 — 이 시험의 대상이 없다(빈 집합 통과 금지)."
    assert list(mirrored) == canon, \
        "autometa.variables 가 행 표의 미러가 아니다 — M-10 트리거가 안 돈다(정본은 행 표다)."


# ═══════ ⟨WU-C7 · R-B 판정 9⟩ **0행 읽기 퇴행을 걷었다** ══════════════════
def test_zero_rows_read_as_an_empty_list_not_the_legacy_array(p2_client, sql) -> None:
    """행이 0개면 **빈 목록**이다 — `autometa.variables` 로 퇴행하지 않는다.

    종전에는 0행일 때 그 배열(파이프라인이 헤더에서 읽은 이름)을 읽었다. `0019` 가 그 배열을
    **행 표의 사본**으로 바꾼 뒤로 그것은 다리가 아니라 되먹임이다 — 사람이 변수를 전부 지운
    자리에서 화면이 **지운 변수를 계속 본다**.

    ⚠ 재료를 만드는 순서가 규칙이다 — 행을 **먼저** 지우고(트리거가 배열을 `{}` 로 만든다)
      그 뒤에 배열에 옛 값을 심는다. 순서를 뒤집으면 트리거가 심은 값을 곧바로 지운다.

    red 만드는 법 — `_variables_payload` 에 `if rows:` 퇴행 분기를 되돌린다.
    """
    client = p2_client()
    dataset_id = _register_with(client, variables=THREE).json()["datasetId"]
    sql("DELETE FROM d3_dataset_variable WHERE dataset_id = :d", {"d": dataset_id})
    sql("UPDATE d3_dataset_autometa SET variables = ARRAY['legacy_a', 'legacy_b']"
        " WHERE dataset_id = :d", {"d": dataset_id})

    got = client.get(f"{API_PREFIX}/datasets/{dataset_id}",
                     headers=auth(TOKEN_RES)).json()["basicInfo"]["variables"]
    assert got == [], f"0행인데 옛 배열로 퇴행했다: {got!r}"


# ═══════ ⟨WU-C7 · 질의 36⟩ N행 쓰기에 트리거는 **1회** ═══════════════════
#
# 두 사실이 함께여야 「1회」다 —
#   ㈎ DB 쪽: 미러 트리거가 **문장 단위**다 (`0022`).
#   ㈏ 서버 쪽: `replace_variables` 가 INSERT 를 **한 문장**으로 보낸다.
# 한쪽만 있으면 여전히 N 번 뛴다. 그래서 둘을 따로 잰다.
def test_the_mirror_triggers_are_statement_level(sql) -> None:
    """㈎ — 셋 다 `FOR EACH STATEMENT` 이고 전이 표를 갖는다.

    red 만드는 법 — `0022` 를 downgrade 해 행 단위 한 벌로 되돌린다.
    """
    defs = sql("""
        SELECT tgname, pg_get_triggerdef(oid) AS def
          FROM pg_trigger
         WHERE NOT tgisinternal AND tgrelid = 'd3_dataset_variable'::regclass
         ORDER BY tgname
    """)
    assert [r["tgname"] for r in defs] == [
        "d3_dataset_variable_mirror_del",
        "d3_dataset_variable_mirror_ins",
        "d3_dataset_variable_mirror_upd",
    ], f"변수 표의 트리거가 {[r['tgname'] for r in defs]!r} 다."
    for r in defs:
        assert "FOR EACH STATEMENT" in r["def"], f"{r['tgname']} 가 행 단위다: {r['def']}"
        assert "REFERENCING" in r["def"], f"{r['tgname']} 에 전이 표가 없다: {r['def']}"


def test_replace_variables_sends_exactly_one_insert_statement() -> None:
    """㈏ — 행이 몇이든 INSERT 는 **한 문장**이다 (문장 단위 트리거가 한 번 뛰는 조건).

    DB 없이 잰다 — 이 사실은 「몇 문장을 보내는가」이지 「DB 가 무엇을 하는가」가 아니다.
    red 만드는 법 — `replace_variables` 의 배열 바인딩을 행별 루프로 되돌린다.
    """
    from colab_core.domains import d3_catalog
    from colab_core.kernel.ids import Ulid

    class _Recorder:
        def __init__(self) -> None:
            self.statements: list[str] = []

        def execute(self, statement, params=None):
            self.statements.append(str(statement))
            return None

    rec = _Recorder()
    d3_catalog.replace_variables(rec, Ulid(DS_A1), list(THREE))
    inserts = [s for s in rec.statements if "INSERT INTO d3_dataset_variable" in s]
    assert len(inserts) == 1, f"3행에 INSERT 문이 {len(inserts)}개다 (기대 1) — 트리거가 그만큼 뛴다."
    deletes = [s for s in rec.statements if "DELETE FROM d3_dataset_variable" in s]
    assert len(deletes) == 1, "지우기도 한 문장이어야 한다(delete-then-insert)."


def test_zero_rows_send_no_insert_statement_at_all() -> None:
    """행이 0개면 **빈 INSERT 를 보내지 않는다** — 지우기 한 문장으로 끝이다."""
    from colab_core.domains import d3_catalog
    from colab_core.kernel.ids import Ulid

    seen: list[str] = []

    class _Recorder:
        def execute(self, statement, params=None):
            seen.append(str(statement))
            return None

    d3_catalog.replace_variables(_Recorder(), Ulid(DS_A1), [])
    assert not [s for s in seen if "INSERT INTO d3_dataset_variable" in s]


def test_the_mirror_still_matches_the_rows_after_a_batched_write(p2_client, sql) -> None:
    """회귀 — 한 문장으로 바꾼 뒤에도 미러가 **행 표와 정확히 같다**(순서까지)."""
    client = p2_client()
    dataset_id = _register_with(client, variables=THREE).json()["datasetId"]
    mirrored = sql("SELECT variables FROM d3_dataset_autometa WHERE dataset_id = :d",
                   {"d": dataset_id})[0]["variables"]
    assert list(mirrored) == [v["name"] for v in THREE]
