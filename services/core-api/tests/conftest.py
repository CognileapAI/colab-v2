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
def subjects_file() -> str:
    return os.environ.get("COLAB_CORE_TEST_SUBJECTS_FILE") or str(FIXTURES / "subjects.json")


@pytest.fixture(scope="session")
def session_factory(app_db_url: str):
    from colab_core.kernel.db import make_engine, make_session_factory
    return make_session_factory(make_engine(app_db_url))


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

    return TestClient(create_app(Settings(database_url=app_db_url, subjects_file=subjects_file)))


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

#: 시험이 만든 행을 되돌릴 때 훑는 표와 그 시각 열. 자식부터 지운다(FK 순서).
#: **`d8_activity` 는 없다** — append-only 트리거가 DELETE 를 거부한다(그것이 그 표의 요점이다).
#: 그래서 활동 시험은 절대 개수가 아니라 **자기가 부르기 전후의 차이**를 센다.
#: 세 번째 칸은 **시드 행을 지키는 조건**이다. 시드 행도 시험이 만지면 `updated_at` 이
#: 밀리므로, 시각만 보고 지우면 **시드가 시험 도중에 사라진다**(실제로 그렇게 깨졌다).
_SEED_DATASETS = ("'0000000000000000000000DSA1'", "'0000000000000000000000DSA2'",
                  "'0000000000000000000000DSB1'")
_KEEP_DATASETS = f" AND dataset_id NOT IN ({', '.join(_SEED_DATASETS)})"
_CLEANUP: tuple[tuple[str, str, str], ...] = (
    ("d6_project_dataset", "created_at", ""),
    # **`d6_project` 는 WU-P5 에서 들어왔다.** `listProjects` 가 생기기 전에는 시험이 만든
    # 프로젝트가 남아도 아무도 세지 않아 드러나지 않았다 — `createProject` 시험이 회차마다
    # 한 건씩 쌓아 두고 있었고, 목록 op 이 열리자마자 그 누적이 셈을 틀리게 했다(실측).
    # 자식(`d6_project_dataset`)을 먼저 지우므로 FK 순서는 위 줄이 지킨다.
    ("d6_project", "created_at", ""),
    ("d4_lineage_edge", "confirmed_at", ""),
    ("d4_lineage_unknown", "marked_at", ""),
    ("d5_pipeline_event", "occurred_at", ""),
    ("d5_upload_file", "created_at", ""),
    ("d5_upload", "created_at", ""),
    # **`d3_file` 만은 시드 데이터셋의 행도 지운다** — 후주입 시험이 시드 데이터셋에 조각을
    # 더하고, 그 행을 남기면 `d3_dataset.file_count`(메타 열)가 시험마다 1씩 늘어난다.
    # 지운 뒤 아래 `_RESTORE` 가 시드 두 행을 되돌리므로 셈이 제자리로 온다.
    ("d3_file", "created_at", ""),
    ("d3_dataset_autometa", "updated_at", _KEEP_DATASETS),
    ("d3_dataset_description", "updated_at", _KEEP_DATASETS),
    ("d3_dataset", "uploaded_at", f" AND id NOT IN ({', '.join(_SEED_DATASETS)})"),
)

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
          '기준 격자 파일', 'a1-grid.nc', 50, 'k/a1g', true, true)
       -- **`DSA2`(잠김)의 파일은 여기서 되돌리지 않는다** — `body_access` RESTRICTIVE 가
       -- 앱 롤의 INSERT 를 막는다(그게 그 정책의 요점이다). 시험도 그 행을 건드리지 않는다.
       ON CONFLICT (id) DO UPDATE
         SET file_name = EXCLUDED.file_name, size_bytes = EXCLUDED.size_bytes,
             storage_key = EXCLUDED.storage_key""",
    """INSERT INTO d3_dataset_autometa (dataset_id, lab_id, format, variables, crs,
                                        total_size_bytes) VALUES
         ('0000000000000000000000DSA1', current_lab_id(), 'CSV',    '{강우량}', 'EPSG:5179', 100),
         ('0000000000000000000000DSA2', current_lab_id(), 'NetCDF', '{강우량}', 'EPSG:5179', 200)
       ON CONFLICT (dataset_id) DO UPDATE
         SET crs = EXCLUDED.crs, grid = NULL, format = EXCLUDED.format""",
    """UPDATE d3_dataset SET lineage_confirmed_at = NULL
        WHERE id = '0000000000000000000000DSA1'""",
    """UPDATE d3_dataset SET lineage_confirmed_at = '2026-02-03T00:00:00Z'
        WHERE id = '0000000000000000000000DSA2'""",
    """UPDATE d2_permission_switch SET enabled = true
        WHERE account_id = '000000000000000000000000A1'
          AND switch IN ('업로드·편집', '프로젝트 생성')""",
)


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def p2_client(app_db_url: str, subjects_file: str, tmp_path):
    """P2 op 을 부르는 클라이언트를 만드는 **팩토리**.

    수명(`upload_ttl_hours`)은 **운영 설정**이라 시험이 설정으로 바꾼다 —
    코드에 박힌 숫자를 시험이 흉내 내지 않는다 (`PLAN-SoT §9 〈67〉-ⓐ`).
    """
    from fastapi.testclient import TestClient

    from colab_core.app.main import create_app
    from colab_core.kernel.config import Settings

    def build(*, ttl_hours: int = 24, viz_base_url: str | None = None,
              ai_base_url: str | None = None) -> TestClient:
        settings = Settings(database_url=app_db_url, subjects_file=subjects_file,
                            upload_ttl_hours=ttl_hours,
                            upload_storage_dir=str(tmp_path / "uploads"),
                            viz_base_url=viz_base_url, ai_base_url=ai_base_url)
        return TestClient(create_app(settings), raise_server_exceptions=False)

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


@pytest.fixture(autouse=True)
def _rollback_p2_rows(request, session_factory):
    """시험이 만든 행을 **시험이 끝날 때 되돌린다.**

    시각 기준으로 지운다 — 시드 행은 전부 이 시각보다 앞이라 남고, 시험이 만든 행만 사라진다.
    (ID 접두사로 가르려 했으나 시드 ULID 와 생성 ULID 가 **둘 다 `0` 으로 시작한다** — 확인하고
    버린 방법이다. 확장자로 역할을 가르려다 실파일 14건을 삼킨 `M-1` 과 같은 무늬라서 안 쓴다.)
    """
    # `live_client` 도 훑는다 — `test_cross_tenant.py` 의 쓰기 경계 증명이 `createProject` 로
    # 실제 행을 만들고 되돌리지 않았다. 목록 op 이 열리기 전에는 보이지 않던 누출이다 (WU-P5).
    if not {"p2_client", "sql", "live_client"} & set(request.fixturenames):
        yield
        return
    from sqlalchemy import text

    from colab_core.kernel.auth import Subject
    from colab_core.kernel.ids import Ulid
    from colab_core.kernel.scope import apply_scope

    # **시각은 DB 에게 묻는다** — 호스트 시계와 DB 시계를 섞으면 몇 밀리초 차이로 시험이
    # 자기가 만든 행을 못 지운다. 그 실패는 다음 시험에서야 드러나서 원인을 못 찾는다.
    marker = session_factory()
    try:
        started = marker.execute(text("SELECT now()")).scalar_one()
    finally:
        marker.close()
    yield

    session = session_factory()
    try:
        session.begin()
        apply_scope(session, Subject(account_id=Ulid(ACC_A_PROF), lab_id=Ulid(LAB_A)))
        for table, column, keep in _CLEANUP:
            session.execute(text(f"DELETE FROM {table} WHERE {column} >= :t{keep}"),
                            {"t": started})
        for statement in _RESTORE:
            session.execute(text(statement))
        session.commit()
    finally:
        session.close()
