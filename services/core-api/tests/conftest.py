from __future__ import annotations

import pathlib
import sys

SRC = pathlib.Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

REPO = pathlib.Path(__file__).resolve().parents[3]
CONTRACT = REPO / "contracts" / "seams" / "fe-core.yaml"


# ─────────────────────────────────────────────────────────────────────────────
# A2 — 음성·실효 증명이 함께 쓰는 재료 (WU-P0 산출물 #2 · sessions/P0-rls-proof.md)
#
# 시드는 `tests/fixtures/seed.sql`, 주체 표는 `tests/fixtures/subjects.json` 이다.
# DB 가 없으면 **skip 이 아니라 fail** 이다 — 그 skip 이 정확히 v1 의 실패였다 (P0.md §6).
# ─────────────────────────────────────────────────────────────────────────────
import contextlib  # noqa: E402
import os  # noqa: E402

import pytest  # noqa: E402

FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"

LAB_A = "0000000000000000000000000A"
LAB_B = "0000000000000000000000000B"
ACC_A_PROF = "00000000000000000000000AP1"
ACC_A_RES = "000000000000000000000000A1"
ACC_B_PROF = "00000000000000000000000BP1"
#: ⭑ **⟨2026-09-18 develop 동기화⟩ 「A 연구실 안에서 접근 권한이 없는 주체」.**
#: 종전에는 `ACC_A_PROF` 가 그 자리였다. `0033_admin_body_access` 이후 교수는 자기 연구실의
#: **관리자**라 다른 구성원의 비공개 자료까지 본다(intent `2026-09-16-admin-full-access` Q7 ·
#: Ted 승인). 시드의 A 연구실은 관리자(`ACC_A_PROF`)와 소유자(`ACC_A_RES`) 둘뿐이라
#: 「둘 다 아닌 구성원」이 없다. **등록하지 않은 주체**를 쓴다 — 시드를 늘리면 develop 이
#: 이슈 #47 로 세운 계정 수 오라클이 흔들리고, 행을 만들면 되돌리기의 행위자 위험이 생긴다.
ACC_A_OUTSIDER = "0000000000000000000000000X"
DS_A1 = "0000000000000000000000DSA1"   # 열림 · 파일 2
DS_A2 = "0000000000000000000000DSA2"   # 잠김 · 파일 1 · DSA1 의 자식
DS_B1 = "0000000000000000000000DSB1"   # 다른 연구실
FILE_B1 = "00000000000000000000000FB1"
PRJ_B = "0000000000000000000000PRJB"


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        pytest.fail(f"{name} 이 없다. DB 를 못 붙인 것은 통과가 아니다 (CLAUDE.md §4).")
    return value


@pytest.fixture(scope="session")
def app_db_url() -> str:
    """앱 롤(NOBYPASSRLS·비소유자)로 접속하는 URL."""
    return _require("COLAB_CORE_TEST_DATABASE_URL")

@pytest.fixture(scope="session")
def admin_db_url() -> str:
    return _require("COLAB_CORE_TEST_ADMIN_DATABASE_URL")


@pytest.fixture(scope="session")
def subjects_file() -> str:
    return os.environ.get("COLAB_CORE_TEST_SUBJECTS_FILE") or str(FIXTURES / "subjects.json")


@pytest.fixture(scope="session")
def session_factory(app_db_url: str):
    from colab_core.kernel.db import make_engine, make_session_factory
    return make_session_factory(make_engine(app_db_url))


@pytest.fixture(scope="session")
def purge_session_factory(admin_db_url: str):
    """되돌리기 전용 접속 — **superuser(`postgres`)** 다. 시험 본문은 이 팩토리를 쓰지 않는다.

    ⭑ **⟨2026-09-18 · 이슈 #47⟩ 되돌리기가 앱 롤이면 다른 연구실 행을 못 줍는다.**
    스냅숏·삭제를 앱 롤(`session_factory`)로 돌리던 때에는 경계가 A 연구실이라 RLS 가 B·C
    연구실 행을 **아예 안 보여 줬고**, 시험이 만들어 커밋한 그 행들이(`test_admin_actor_visibility.py`
    가 한 회차에 LAB_B 데이터셋 3건) 같은 xdist worker 의 **다음 시험**까지 살아남아 절대 집합을
    오라클로 삼는 자리를 틀리게 했다(`tests/test_pool_no_leak.py:48`·`:99`·`:106`).
    보이지 않는 행은 못 지운다 — 그래서 되돌리기만 경계 **밖**에 세운다.

    ⚠ `admin_db_url` 의 롤(`colab_account_admin`)로는 부족하다 — BYPASSRLS 는 있지만
    public 표에 DELETE 권한이 없다(`services/core-api/ops/account-admin-role.sql:49-56`).
    그래서 같은 접속처의 **사용자만** `postgres` 로 갈아끼운다. 선례는
    `tests/test_admin_role_scope.py:17`·`:29` 와 `tests/test_operator_designation.py` 의
    `_remove_created_accounts` 다 — 이 레포에서 이미 쓰는 자리다.

    ⚠ **worker 를 넘지 않는다.** `gates/tools/xdist_core_db.py:27,:40` 이 worker 마다
    앱 URL 과 admin URL 을 **둘 다** 다시 써 넣으므로, 여기서 만든 접속처도 그 worker 의
    일회용 DB 하나다. 경계를 지나칠 뿐 DB 를 넘나들지 않는다.

    ⚠ **풀을 두지 않는다(`NullPool`) — `make_engine` 을 쓰지 않는다.** 그 helper 는 운영
    동시성에 맞춘 20＋20 = 40 이고(`src/colab_core/kernel/db.py:19-20`), 게이트의 일회용
    postgres 는 `max_connections` **기본 100** 인 컨테이너 하나를 worker 12 개가 나눠 쓴다
    (`gates/tools/_pg.sh:177-180` — 별도 설정을 주지 않는다). 실측(2026-09-18 ·
    `COLAB_SERVICE_TEST_JOBS=12`)에서 그 컨테이너의 `pg_stat_activity` 최고치가 **93/100** 이라,
    worker 마다 커넥션을 **하나라도 상주**시키면 천장에 닿아 회차마다 자리를 옮겨 다니는
    `500 Internal Server Error`·`psycopg.OperationalError: connection failed` 가 1~10건 났다.
    되돌리기는 시험 하나당 짧은 트랜잭션 둘(스냅숏 · 삭제)을 차례로 여는 자리라 **쓸 때만 붙고
    닫으면 바로 놓는** 것이 맞다. `pool_pre_ping` 도 필요 없다 — 매번 새 커넥션이다.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.engine import make_url
    from sqlalchemy.pool import NullPool

    from colab_core.kernel.db import make_session_factory

    engine = create_engine(make_url(admin_db_url).set(username="postgres", password=None),
                           future=True, poolclass=NullPool)
    try:
        yield make_session_factory(engine)
    finally:
        engine.dispose()


@contextlib.contextmanager
def scoped_ro(factory, account_id: str, lab_id: str):
    """경계를 심고 **반드시 rollback** 하는 트랜잭션.

    증명용 쓰기(허용 줄 추가 등)를 시드에 남기지 않기 위해서다 —
    시드가 테스트 순서에 따라 달라지면 그 오라클은 오라클이 아니다.
    """
    from colab_core.kernel.auth import Subject
    from colab_core.kernel.ids import Ulid
    from colab_core.kernel.scope import apply_scope

    session = factory()
    try:
        session.begin()
        apply_scope(session, Subject(account_id=Ulid(account_id), lab_id=Ulid(lab_id)))
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="session")
def live_client(app_db_url: str, subjects_file: str):
    """HTTP 층 증명용. DB 층과 **같은 앱 롤**로 붙는다 — 층만 다르고 경계는 하나다."""
    from fastapi.testclient import TestClient

    from colab_core.app.main import create_app
    from colab_core.kernel.config import Settings

    return TestClient(create_app(
        Settings(database_url=app_db_url, subjects_file=subjects_file),
        test_static_subjects=True,
    ))


# ─────────────────────────────────────────────────────────────────────────────
# P2 — 업로드 · 등록 전환 · 계보 확정이 쓰는 재료 (sessions/P2-api-report.md)
#
# **이 WU 가 처음 되돌릴 수 없는 것을 만든다.** 그래서 시험은 성공 경로보다 음성 경로가
# 많고, 매 시험이 자기가 만든 행을 되돌린다 — 시드가 시험 순서에 따라 달라지면 그 오라클은
# 오라클이 아니다 (위 `scoped_ro` 주석과 같은 이유).
# ─────────────────────────────────────────────────────────────────────────────
import datetime as dt  # noqa: E402

#: 연구원은 `업로드·편집` 이 켜져 있고(seed.sql:33) 교수는 판정으로 켜진다(P-5).
TOKEN_RES = "a1-res-token"
TOKEN_PROF = "a1-prof-token"
TOKEN_B = "b1-prof-token"

#: 시험이 만든 행을 되돌릴 때 훑는 표. 자식부터 지운다(FK 순서).
#: **`d8_activity` 는 없다** — append-only 트리거가 DELETE 를 거부한다(그것이 그 표의 요점이다).
#: 그래서 활동 시험은 절대 개수가 아니라 **자기가 부르기 전후의 차이**를 센다.
#:
#: ⭑ **⟨2026-09-13 · 시계 의존 제거⟩ 시각 열로 가르지 않는다.** 종전에는 표마다 시각 열을
#: 적어 두고 「기준 시각 이후 행만 지운다」로 골랐는데, 호스트(WSL2)의 실시간 시계가 이따금
#: **뒤로 점프해서**(실측 151 ms · `tests/test_cleanup_purge.py` 머리글) 점프 뒤에 만들어진
#: 행이 기준 시각보다 앞선 시각을 달고 태어나 삭제에서 빠졌다. 그래서 **시험 전 기본키 집합**
#: 을 떠 두고 **그 집합에 없는 행**을 지운다 — 시계가 어느 방향으로 흔들려도 같은 답이 나온다.
#: 시드 행을 지키는 조건도 이제 필요 없다(시드 키는 스냅숏 안에 있다).
_SEED_DATASETS = ("'0000000000000000000000DSA1'", "'0000000000000000000000DSA2'",
                  "'0000000000000000000000DSB1'")
#: ⭑ **⟨WU-B2 · PRD-16⟩ 변수 행에는 시각 열이 없다** — 아래 `_CLEANUP` 루프가 쓰는
#: 「시각 이후 행만 지운다」를 쓸 수 없어 **문장 하나로 뺀다**. 데이터셋에 딸린 행이라
#: 시드 데이터셋 것만 남기면 그것으로 충분하고, 시드 세 데이터셋의 행은 아래 `_RESTORE` 가
#: 되돌린다. ⚠ **`d3_dataset` DELETE 보다 먼저 돌아야 한다**(FK).
_CLEANUP_VARIABLES = (
    f"DELETE FROM d3_dataset_variable WHERE dataset_id NOT IN ({', '.join(_SEED_DATASETS)})"
)

_CLEANUP: tuple[str, ...] = (
    # **WU-P6 가 더한 셋.** 승인 시험은 요청 행과 **그 요청이 만든 허용 줄**을 함께 남긴다 —
    # 허용 줄을 안 지우면 다음 회차에서 `DSA2` 가 이미 열린 채로 시작해 잠금 시험이 통째로
    # 거짓 green 이 된다(`test_body_access.py` 가 제일 먼저 무너진다).
    "d2_dataset_access_request",
    # ⭑ **⟨WU-B4 · PRD-11⟩ 등록이 공개 범위를 쓰면서 이 표에 시험 행이 생긴다.**
    # 안 지우면 `d3_dataset` DELETE 가 FK 로 막히는 것이 아니라(bare 컬럼이다) **행이
    # 쌓여** cross-tenant 셈이 회차마다 는다. 시드 두 행은 아래 `_RESTORE` 가 되돌린다.
    "d2_dataset_access",
    "d2_verification_request",
    "d2_dataset_access_grant",
    "d6_project_dataset",
    # **`d6_project` 는 WU-P5 에서 들어왔다.** `listProjects` 가 생기기 전에는 시험이 만든
    # 프로젝트가 남아도 아무도 세지 않아 드러나지 않았다 — `createProject` 시험이 회차마다
    # 한 건씩 쌓아 두고 있었고, 목록 op 이 열리자마자 그 누적이 셈을 틀리게 했다(실측).
    # 자식(`d6_project_dataset`)을 먼저 지우므로 FK 순서는 위 줄이 지킨다.
    "d6_project",
    "d4_lineage_edge",
    "d4_lineage_unknown",
    "d5_pipeline_event",
    "d5_upload_grid_profile",
    "d5_upload_file",
    "d5_upload",
    "d3_search_evidence",
    # **`d3_file` 은 시험이 시드 데이터셋에 더한 조각까지 지운다** — 그 행을 남기면
    # `d3_dataset.file_count`(메타 열)가 시험마다 1씩 늘어난다. 시드 두 행은 스냅숏에 있어
    # 남고, 시험이 값만 바꿨다면 아래 `_RESTORE` 가 되돌리므로 셈이 제자리로 온다.
    "d3_file",
    "d3_representative_image_cleanup",
    "d3_dataset_representative_image",
    "d3_lab_default_grid",
    "d3_dataset_grid_profile",
    "d3_dataset_autometa",
    "d3_dataset_description",
    "d3_dataset",
    # ⭑ **⟨2026-09-18 · 이슈 #47⟩ 아래 셋만 A 연구실 안에서 지운다** — 사유는 `_ACCOUNT_TABLES`.
    # ⭑ **⟨2026-09-17 · 이슈 #47⟩ 계정 계열은 여기서 끝이어야 한다.** 계정을 만드는 시험이
    # 되돌리기를 `try/finally` 로 손수 적고 있었고(`test_lab_members.py` 의 `_purge_member`),
    # 생성이 중간에 실패하면 그 `finally` 가 아예 서지 않아 A 연구실에 계정이 영구히 남았다.
    # 남은 한 행은 `memberCount`(= `count(*) FROM d1_account`) 를 세는 **다음 파일**의 오라클을
    # 틀리게 하고, 내부 worker 수가 바뀌면 오염원과 피해자의 동거 여부가 바뀌어 판정이 흔들린다.
    #
    # ⚠ **순서가 전부다.** `d2_permission_switch`·`d2_member_role` 은 `d1_account` 를 CASCADE
    # 없이 참조하므로(`db/platform/schema.sql` 앵커 `CREATE TABLE d2_permission_switch`) 먼저
    # 지워야 하고, `d1_account` 를 참조하는 다른 표(`d3_dataset`·`d4_lineage_edge`·`d5_upload`
    # …)는 전부 위에 있으므로 **`d1_account` 가 이 튜플의 마지막 원소여야 한다.** 한 건이라도
    # 막히면 되돌리기 **트랜잭션 전체**가 무효가 된다 — 삭제도 `_RESTORE` 도 함께 사라진다.
    #
    # 여기 없는 표가 A 연구실 안에서 **새 계정을 행위자로 남기면** 그날부터 되돌리기가 통째로
    # 죽는다 — `d2_permission_change`(append-only 트리거가 DELETE 를 거부한다)·`d2_verified`·
    # `d5_upload_transfer`·`d8_activity`·`d8_download` 다. 게이트 요약의 `errors` 계수가 그 신호다.
    "d2_permission_switch",
    "d2_member_role",
    "d1_account",
)

#: 표의 **기본키 열은 DB 에게 묻는다.** 여기에 손으로 적어 두면 스키마가 바뀔 때 조용히
#: 갈라지고, 갈라진 쪽은 「지웠다고 보고했는데 아무것도 안 지운」 자리가 된다.
_PK_SQL = f"""
SELECT c.relname AS table_name, a.attname AS column_name
  FROM pg_constraint con
  JOIN pg_class c ON c.oid = con.conrelid
  JOIN unnest(con.conkey) WITH ORDINALITY AS k(attnum, ord) ON true
  JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = k.attnum
 WHERE con.contype = 'p'
   AND c.relname IN ({', '.join(f"'{t}'" for t in _CLEANUP)})
 ORDER BY c.relname, k.ord
"""

#: 기본키 열 → 한 줄짜리 키 식. 복합키도 한 값으로 접는다(`d3_dataset_variable` 같은 자리).
_KEY_EXPR: dict[str, str] = {}

#: 시드 행 되돌리기. **시각으로 지우는 것만으로는 부족하다** — 교체·삭제·확인 시험은
#: 시드 행 자체를 바꾸거나 지우므로, 그 상태가 다음 시험으로 새면 오라클이 오라클이 아니게 된다
#: (`test_live_endpoints.py::test_list_files_open_and_locked` 가 실제로 그렇게 깨졌다).
#: 값은 `tests/fixtures/seed.sql` 의 것을 그대로 옮겨 적었다.
_RESTORE: tuple[str, ...] = (
    """INSERT INTO d3_file (id, lab_id, dataset_id, kind, file_name, size_bytes,
                            storage_key, carries_lat, carries_lon) VALUES
         ('00000000000000000000000FA1', current_lab_id(), '0000000000000000000000DSA1',
          '본체', 'a1-body.csv', 50, 'k/a1', false, false),
         ('00000000000000000000000FA2', current_lab_id(), '0000000000000000000000DSA1',
          '기준 격자 파일', 'a1-grid.nc', 50, 'k/a1g', true, true),
         ('00000000000000000000000FA3', current_lab_id(), '0000000000000000000000DSA2',
          '본체', 'a2-body.nc', 200, 'k/a2', false, false)
       -- `0032_private_owner_access` 이후 이 복구 주체(A 교수)는 DSA2 소유자라 잠긴 본체도
       -- 읽고 쓸 수 있다. 따라서 잠긴 시드 파일도 같은 스냅숏/복구 규율로 되돌린다.
       ON CONFLICT (id) DO UPDATE
         SET file_name = EXCLUDED.file_name, size_bytes = EXCLUDED.size_bytes,
             storage_key = EXCLUDED.storage_key""",
    # `total_size_bytes` 는 **0** — 시드와 같은 규율이다(`seed.sql` autometa 주석). 합계는 트리거
    # (`0009`)가 `d3_file` 의 INSERT/UPDATE/DELETE 차분으로 유지하므로, 위 `d3_file` 복원(재삽입·
    # 크기 되돌림)이 곧 합계 복원이다. ON CONFLICT 가 이 열을 안 건드리는 것도 같은 이유 —
    # 여기서 100 을 다시 쓰면 트리거 차분과 두 번 센다. **다시 세지도 않는다** — 앱 롤로 잠긴
    # DSA2 의 파일을 세면 0 이 나온다(`body_access`).
    """INSERT INTO d3_dataset_autometa (dataset_id, lab_id, format, variables, crs,
                                        total_size_bytes) VALUES
         ('0000000000000000000000DSA1', current_lab_id(), 'CSV',    '{강우량}', 'EPSG:5179', 0),
         ('0000000000000000000000DSA2', current_lab_id(), 'NetCDF', '{강우량}', 'EPSG:5179', 0)
       ON CONFLICT (dataset_id) DO UPDATE
         SET crs = EXCLUDED.crs, grid = NULL, format = EXCLUDED.format""",
    # ⭑ **⟨WU-B2 · PRD-16⟩ 시드 변수 행.** 수정 시험이 행 집합을 통째로 교체하므로
    # (delete-then-insert) 되돌리지 않으면 「DSA1 은 단위가 셋 다른 3행」을 오라클로 삼는
    # 시험이 순서에 따라 갈린다. 값은 `tests/fixtures/seed.sql` 그대로다.
    # ⚠ **DSB1 은 여기 없다** — 이 세션의 스코프가 A 연구실이라 그 행에 닿지 못한다(경계 정책).
    """DELETE FROM d3_dataset_variable
        WHERE dataset_id IN ('0000000000000000000000DSA1', '0000000000000000000000DSA2')""",
    """INSERT INTO d3_dataset_variable
         (dataset_id, lab_id, ordinal, name, unit, value_range, missing_rate, is_representative)
       VALUES
         ('0000000000000000000000DSA1', current_lab_id(), 1, '강우량', 'mm',   '0~350',  '0.2%', true),
         ('0000000000000000000000DSA1', current_lab_id(), 2, '기온',   '℃',   '-30~40', NULL,   false),
         ('0000000000000000000000DSA1', current_lab_id(), 3, '유출량', 'm3/s', NULL,     NULL,   false),
         ('0000000000000000000000DSA2', current_lab_id(), 1, '강우량', 'mm',   NULL,     NULL,   true)""",
    # ⭑ **⟨WU-B4 · PRD-11⟩ 공개 범위 시험이 시드 상태를 바꾼다**(잠김 → 지정 공개 → 잠김).
    # 되돌리지 않으면 「DSA2 는 잠김」을 오라클로 삼는 시험 전부가 순서에 따라 갈린다
    # (`test_body_access.py` 가 제일 먼저 무너진다). 값은 `tests/fixtures/seed.sql` 그대로다.
    """INSERT INTO d2_dataset_access (dataset_id, lab_id, state) VALUES
         ('0000000000000000000000DSA1', current_lab_id(), '열림'),
         ('0000000000000000000000DSA2', current_lab_id(), '잠김')
       ON CONFLICT (dataset_id) DO UPDATE SET state = EXCLUDED.state""",
    """UPDATE d3_dataset SET lineage_confirmed_at = NULL
        WHERE id = '0000000000000000000000DSA1'""",
    """UPDATE d3_dataset SET lineage_confirmed_at = '2026-02-03T00:00:00Z'
        WHERE id = '0000000000000000000000DSA2'""",
    """UPDATE d3_dataset
          SET source_url = NULL, source_downloaded_on = NULL,
              processing_level_user_set = NULL,
              last_modified_at = CASE id
                WHEN '0000000000000000000000DSA1' THEN '2026-01-02T00:00:00Z'::timestamptz
                WHEN '0000000000000000000000DSA2' THEN '2026-02-02T00:00:00Z'::timestamptz
              END
        WHERE id IN ('0000000000000000000000DSA1', '0000000000000000000000DSA2')""",
    """UPDATE d3_dataset_description
          SET category = NULL, data_type = NULL, human_grid_description = NULL,
              topic = CASE dataset_id
                        WHEN '0000000000000000000000DSA1' THEN '강우·강수'
                        WHEN '0000000000000000000000DSA2' THEN '강우·강수'
                      END
        WHERE dataset_id IN ('0000000000000000000000DSA1', '0000000000000000000000DSA2')""",
    """UPDATE d3_dataset_autometa SET period_start = NULL, period_end = NULL
        WHERE dataset_id IN ('0000000000000000000000DSA1', '0000000000000000000000DSA2')""",
    # **UPDATE 가 아니라 INSERT ... ON CONFLICT 다** (WU-A1). 기본값 시험은 「행이 없는 계정」을
    # 만들려고 스위치 행을 **지운다** — UPDATE 로 되돌리면 0 행을 고치고 조용히 지나가서,
    # 다음 시험이 시드 대신 기본값을 오라클로 삼게 된다. 값은 `seed.sql:33-36` 그대로다.
    # **위임 성격 둘은 꺼진 채로 되돌린다** (seed.sql:35-36). WU-P6 의 음성 ⑤ 가 `승인 위임` 을
    # 켜 보고 막히는지를 재는데, 켠 채로 새면 그 다음 회차의 「권한 없는 사람은 승인 불가」가
    # 조용히 거짓 green 이 된다.
    """INSERT INTO d2_permission_switch (account_id, lab_id, switch, enabled) VALUES
         ('000000000000000000000000A1', current_lab_id(), '업로드·편집',  true),
         ('000000000000000000000000A1', current_lab_id(), '프로젝트 생성', true),
         ('000000000000000000000000A1', current_lab_id(), '승인 위임',    false),
         ('000000000000000000000000A1', current_lab_id(), '연구실 설정',  false)
       ON CONFLICT (account_id, switch) DO UPDATE SET enabled = EXCLUDED.enabled""",
    # Verified 왕복 시험은 시드 배지를 껐다 켠다. 시각 기준 삭제로는 못 되돌린다.
    """UPDATE d2_verified
          SET verified = true, approver_account_id = '00000000000000000000000AP1',
              approved_at = '2026-01-03T00:00:00Z',
              cancelled_by_account_id = NULL, cancelled_at = NULL, cancellation_reason = NULL
        WHERE dataset_id = '0000000000000000000000DSA1'""",
    """UPDATE d2_verified
          SET verified = false, approver_account_id = NULL, approved_at = NULL,
              cancelled_by_account_id = NULL, cancelled_at = NULL, cancellation_reason = NULL
        WHERE dataset_id = '0000000000000000000000DSA2'""",
    # **`P5` 잔여 셋이 시드 행 자체를 바꾼다** — 닫기(`setProjectStatus`)는 `status` 를,
    # 소속 해제(`unlinkProjectDataset`)는 연결 행을 지운다. 시각 기준 삭제로는 못 되돌린다.
    # 되돌리지 않으면 「PRJA 에 데이터셋 1건」을 오라클로 삼는 시험이 순서에 따라 갈린다
    # (`test_delete_project_with_a_linked_dataset_is_a_409` 가 실제로 그렇게 깨졌다).
    """UPDATE d6_project SET status = '진행 중'
        WHERE id = '0000000000000000000000PRJA'""",
    """INSERT INTO d6_project_dataset (id, lab_id, project_id, dataset_id, usage_note) VALUES
         ('0000000000000000000000PDA1', current_lab_id(), '0000000000000000000000PRJA',
          '0000000000000000000000DSA2', '격자 입력으로 썼다')
       ON CONFLICT (id) DO UPDATE SET usage_note = EXCLUDED.usage_note""",
)


def _cleanup_scope(session) -> None:
    """되돌리기 세션에 A 연구실 교수의 GUC 를 심는다.

    ⭑ **⟨2026-09-18 · 이슈 #47⟩ 이제 이것은 「경계」가 아니라 `_RESTORE` 의 재료다.**
    종전 주석은 「스냅숏과 삭제가 같은 경계여야 한다」였는데, 되돌리기가 superuser 로 서면서
    이 세션에는 RLS 가 걸리지 않는다 — 스냅숏도 삭제도 **전 연구실**을 본다. 그래도 GUC 를
    심는 이유는 하나다: `_RESTORE` 의 문장들이 `current_lab_id()` 로 A 연구실을 적어 넣는다
    (`app.current_lab` 를 안 심으면 NULL 이 들어가 시드 복구가 통째로 어긋난다).
    `apply_scope` 는 롤을 보지 않으므로(`src/colab_core/kernel/scope.py` `apply_scope`)
    superuser 접속에서도 그대로 선다.
    """
    from colab_core.kernel.auth import Subject
    from colab_core.kernel.ids import Ulid
    from colab_core.kernel.scope import apply_scope

    apply_scope(session, Subject(account_id=Ulid(ACC_A_PROF), lab_id=Ulid(LAB_A)))


def _key_exprs(session) -> dict[str, str]:
    """표별 기본키 식. 한 번 읽어 두고 재사용한다 — 스키마는 한 회차 안에서 바뀌지 않는다."""
    from sqlalchemy import text

    if not _KEY_EXPR:
        columns: dict[str, list[str]] = {}
        for table, column in session.execute(text(_PK_SQL)).all():
            columns.setdefault(table, []).append(column)
        missing = [t for t in _CLEANUP if t not in columns]
        if missing:
            raise AssertionError(
                f"기본키를 못 읽은 표가 있다: {missing}. 키를 모르는 표는 되돌릴 수 없고, "
                "되돌리지 못한 행은 다음 시험의 개수 오라클을 틀리게 한다.")
        for table, names in columns.items():
            _KEY_EXPR[table] = " || '\\x1f' || ".join(f"{name}::text" for name in names)
    return _KEY_EXPR


def snapshot_test_rows(session) -> dict[str, list[str]]:
    """시험 전 **기본키 집합**을 뜬다. `purge_test_rows` 와 짝이다.

    ⚠ 스냅숏과 삭제는 **같은 접속**에서 떠야 한다 — 보이지 않는 행은 스냅숏에도 없고
    DELETE 에도 안 걸리므로, 둘이 보는 범위가 다르면 남을 행을 지우게 된다.

    ⭑ **⟨2026-09-18 · 이슈 #47⟩ 그 접속이 이제 superuser 다**(`purge_session_factory`).
    앱 롤로 뜨던 때에는 A 연구실 밖 시드(B 의 데이터셋·파일·프로젝트, C 의 계정)가 스냅숏에
    **없었고**, 그래서 삭제도 그 행들에 닿지 못했다 — 시험이 만든 B·C 행이 그대로 새어
    다음 시험의 절대 집합 오라클을 틀리게 했다. superuser 로 뜨면 시드 B·C 행은 스냅숏
    **안**에 들어오므로 삭제 대상에서 자동으로 빠진다. 「시험 전에 있던 키는 남는다」는
    규율은 그대로이고, 그 규율이 닿는 범위만 전 연구실로 넓어졌다.
    """
    from sqlalchemy import text

    exprs = _key_exprs(session)
    union = " UNION ALL ".join(
        f"SELECT '{table}' AS t, ({exprs[table]}) AS k FROM {table}" for table in _CLEANUP)
    snapshot: dict[str, list[str]] = {table: [] for table in _CLEANUP}
    for table, key in session.execute(text(union)).all():
        snapshot[table].append(key)
    return snapshot


#: ⭑ **⟨2026-09-18 · 이슈 #47⟩ 계정 계열만 A 연구실 안에서 지운다.**
#: 나머지 표는 superuser 접속이라 전 연구실을 지우지만, 이 셋은 그러면 안 된다 —
#: `d8_activity.actor_account_id` 가 `d1_account(id)` 를 **ON DELETE 없이** 참조하고
#: (`db/platform/versions/0001_p0_platform.py:387`), 그 표는 `d8_activity_append_only`
#: 트리거가 DELETE 를 거부한다(`:394-396`). 즉 **한 번이라도 행위한 계정은 영영 못 지운다.**
#: 그런 계정을 지우려 들면 되돌리기 **트랜잭션 전체**가 무효가 되고(삭제도 `_RESTORE` 도 함께
#: 사라진다), 백오피스 시험 30여 건이 LAB_C 에 계정을 **일부러 남기므로**
#: (`tests/test_admin_role_scope.py:13-14`) 그 자리는 매 회차 터진다.
#: 소속 없는 계정(`lab_id IS NULL`)도 이 조건에 안 걸린다 — 같은 이유로 그대로 둔다.
_ACCOUNT_TABLES: frozenset[str] = frozenset({"d2_permission_switch", "d2_member_role",
                                             "d1_account"})


def purge_test_rows(session, snapshot: dict[str, list[str]]) -> dict[str, int]:
    """스냅숏에 **없는** 행을 지우고 시드를 되돌린다. FK 순서는 `_CLEANUP` 이 쥔다.

    돌려주는 값은 **A 연구실 밖에서 지운 행 수**(표 이름 → 건수)다. 그 자체가 red 는 아니지만
    「어느 시험이 경계 밖에 행을 남겼나」를 세는 유일한 자리라 호출자가 기록으로 남긴다.
    """
    from sqlalchemy import text

    exprs = _key_exprs(session)
    outside: dict[str, int] = {}
    session.execute(text(_CLEANUP_VARIABLES))
    for table in _CLEANUP:
        where = f"({exprs[table]}) <> ALL(:keys)"
        if table in _ACCOUNT_TABLES:
            where += " AND lab_id = current_lab_id()"
        # `RETURNING lab_id` — `_CLEANUP` 의 24 표는 전부 `lab_id` 를 갖는다(스키마 확인).
        # 미리 세지 않고 지우면서 세는 이유: 사이에 다른 트랜잭션이 끼면 셈과 삭제가 갈라진다.
        labs = session.execute(
            text(f"DELETE FROM {table} WHERE {where} RETURNING lab_id"),
            {"keys": list(snapshot.get(table, ()))}).scalars().all()
        n = sum(1 for lab in labs if lab != LAB_A)
        if n:
            outside[table] = n
    for statement in _RESTORE:
        session.execute(text(statement))
    return outside


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def p2_client(app_db_url: str, admin_db_url: str, subjects_file: str, tmp_path):
    """P2 op 을 부르는 클라이언트를 만드는 **팩토리**.

    수명(`upload_ttl_hours`)은 **운영 설정**이라 시험이 설정으로 바꾼다 —
    코드에 박힌 숫자를 시험이 흉내 내지 않는다 (`PLAN-SoT §9 〈67〉-ⓐ`).
    """
    from fastapi.testclient import TestClient

    from colab_core.app.main import create_app
    from colab_core.kernel.config import Settings

    def build(*, ttl_hours: int = 24, viz_base_url: str | None = None,
              ai_base_url: str | None = None,
              session_secret: str | None = None,
              credentials_file: str | None = None,
              subjects_file_override: str | None = None,
              account_admin_database_url: str | None = None,
              login_max_failures: int = 5,
              viz_service_token: str | None = "test-viz-service-token",
              allow_test_static_subjects: bool = True) -> TestClient:
        settings = Settings(database_url=app_db_url,
                            subjects_file=subjects_file_override or subjects_file,
                            session_secret=session_secret,
                            credentials_file=credentials_file,
                            account_admin_database_url=(
                                admin_db_url if account_admin_database_url is None
                                else account_admin_database_url),
                            login_max_failures=login_max_failures,
                            upload_ttl_hours=ttl_hours,
                            upload_storage_dir=str(tmp_path / "uploads"),
                            viz_base_url=viz_base_url, ai_base_url=ai_base_url,
                            viz_service_token=viz_service_token)
        app = create_app(settings, test_static_subjects=allow_test_static_subjects)
        return TestClient(app, raise_server_exceptions=False)

    return build


@pytest.fixture()
def sql(session_factory):
    """앱 롤로 임의 SQL 을 도는 자리. **경계는 그대로 걸려 있다** — 우회 롤이 아니다.

    시험이 DB 를 직접 보는 이유: 「응답이 그럴듯한가」와 「행이 남았는가」는 다른 질문이고,
    이 프로젝트가 반복해 저지른 실수는 **전부 전자만 보고 생겼다** (`DATA-REFERENCE §0` —
    일곱 중 여섯이 에러 없이 그럴듯한 값이었다).
    """
    from sqlalchemy import text

    from colab_core.kernel.auth import Subject
    from colab_core.kernel.ids import Ulid
    from colab_core.kernel.scope import apply_scope

    opened: list = []

    def run(statement: str, params: dict | None = None, *,
            account_id: str = ACC_A_RES, lab_id: str = LAB_A) -> list:
        session = session_factory()
        opened.append(session)
        session.begin()
        apply_scope(session, Subject(account_id=Ulid(account_id), lab_id=Ulid(lab_id)))
        result = session.execute(text(statement), params or {})
        rows = [dict(r) for r in result.mappings()] if result.returns_rows else []
        session.commit()
        return rows

    yield run
    for s in opened:
        s.close()


@pytest.fixture
def outsider_account(sql):
    """`ACC_A_OUTSIDER` 를 **실재하는** A 연구실 연구원으로 세운다.

    읽기만 하는 시험은 상수만 써도 된다(등록되지 않은 주체도 RLS 는 그대로 거절한다).
    행을 **쓰는** 시험은 FK 때문에 실재 계정이 필요하다 — `d3_knowledge_grant.account_id` 처럼.
    되돌리기 안전: 이 계정이 행위자로 남는 `d3_knowledge_*` 는 `d3_dataset` 에서
    `ON DELETE CASCADE` 로 달려 있고 `_CLEANUP` 이 `d3_dataset` 을 `d1_account` **앞에서**
    지운다. 그래서 계정 DELETE 가 FK 로 막히지 않는다 (이슈 #47 의 경고 자리).
    """
    sql("""INSERT INTO d1_account (id, lab_id, name, email)
             VALUES (:id, current_lab_id(), 'A 다른 연구원', 'outsider@a.example')
           ON CONFLICT (id) DO NOTHING""",
        {"id": ACC_A_OUTSIDER}, account_id=ACC_A_PROF, lab_id=LAB_A)
    sql("""INSERT INTO d2_member_role (account_id, lab_id, role)
             VALUES (:id, current_lab_id(), '연구원')
           ON CONFLICT (account_id) DO NOTHING""",
        {"id": ACC_A_OUTSIDER}, account_id=ACC_A_PROF, lab_id=LAB_A)
    return ACC_A_OUTSIDER


@pytest.fixture(autouse=True)
def _rollback_p2_rows(request, purge_session_factory):
    """시험이 만든 행을 **시험이 끝날 때 되돌린다.**

    **기본키 집합 기준으로 지운다** — 시험 전에 있던 키는 남고, 그 사이에 생긴 행만 사라진다.
    (ID 접두사로 가르려 했으나 시드 ULID 와 생성 ULID 가 **둘 다 `0` 으로 시작한다** — 확인하고
    버린 방법이다. 확장자로 역할을 가르려다 실파일 14건을 삼킨 `M-1` 과 같은 무늬라서 안 쓴다.)

    ⭑ **⟨2026-09-13⟩ 종전에는 시각 기준이었다** — 「기준 시각 이후 행만 지운다」. 호스트 시계가
    뒤로 점프하면 그 뒤에 태어난 행이 기준보다 앞선 시각을 달아 삭제에서 빠졌고, 남은
    `d4_lineage_edge` 한 줄이 `d3_dataset` DELETE 를 FK 로 막아 **되돌리기 트랜잭션 전체**가
    무효가 됐다(삭제도 `_RESTORE` 도 함께 사라진다). 오라클은 `tests/test_cleanup_purge.py`.

    ⭑ **⟨2026-09-18 · 이슈 #47⟩ 스냅숏과 삭제를 superuser 로 돌린다**(`purge_session_factory`).
    앱 롤로 돌던 때에는 경계가 A 연구실이라 RLS 가 다른 연구실 행을 숨겼고, 시험이 커밋한
    LAB_B·LAB_C 행은(`tests/test_admin_actor_visibility.py:38` 은 매개변수 2회 · `:62` 까지
    합쳐 한 회차에 LAB_B 데이터셋 3벌을 만든다) **한 번도 회수되지 않은 채** 같은 xdist worker
    의 다음 시험으로 샜다. 절대 집합을 오라클로 삼는 자리가 그때 무너진다
    (`tests/test_pool_no_leak.py:48`·`:99`·`:106` — `COLAB_SERVICE_TEST_JOBS=12` 에서 간헐 red).
    이제 다른 연구실 행도 회수하므로 **새는 시험 쪽을 고치지 않는다** — 하네스가 줍는 것이
    이 결정의 요점이다. 예외는 계정 계열 셋뿐이고 그 사유는 `_ACCOUNT_TABLES` 에 적었다.

    ⚠ **경계 증명이 약해지는 것이 아니다.** 경계를 증명하는 것은 시험 **본문의 assert** 이지
    뒷정리 경로가 아니다 — `tests/test_admin_role_scope.py:29-36` 이 이미 LAB_B 행을
    postgres 로 되돌리고 있고, 그 파일의 경계 증명은 그대로 서 있다.
    """
    # `live_client` 도 훑는다 — `test_cross_tenant.py` 의 쓰기 경계 증명이 `createProject` 로
    # 실제 행을 만들고 되돌리지 않았다. 목록 op 이 열리기 전에는 보이지 않던 누출이다 (WU-P5).
    if not {"p2_client", "sql", "live_client"} & set(request.fixturenames):
        yield
        return
    marker = purge_session_factory()
    try:
        marker.begin()
        _cleanup_scope(marker)
        snapshot = snapshot_test_rows(marker)
    finally:
        marker.rollback()
        marker.close()
    yield

    session = purge_session_factory()
    try:
        session.begin()
        _cleanup_scope(session)
        outside = purge_test_rows(session, snapshot)
        session.commit()
    finally:
        session.close()
    # A 연구실 밖에서 회수한 행은 **말없이 지나가지 않는다.** red 로 만들지도 않는다 —
    # 지금은 그 누출이 정상 동작(관리자가 다른 연구실에 등록하는 시험)이라 판정 대상이 아니고,
    # 대신 어느 시험이 얼마나 남겼는지가 `-rA`·junit 속성에 그대로 찍혀 나중에 셀 수 있다.
    if outside:
        detail = ",".join(f"{table}={n}" for table, n in sorted(outside.items()))
        request.node.user_properties.append(("purged_outside_lab_a", detail))
        print("# 되돌리기: LAB_A 밖 행 회수 " + detail.replace(",", " "))
