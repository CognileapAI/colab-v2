"""워커의 **건별 스코프** — 한 바퀴가 연구실 하나에 묶이지 않는다 (Ted 판정 2026-08-26 ㈑).

**무엇이 틀려 있었나** — `run_once` 가 `COLAB_WORKER_LAB_ID` 하나로 트랜잭션 스코프를 세우고
그 안에서 처리·릴레이·reaper 를 돌았다. 그래서 그 환경변수가 가리키지 않는 연구실의 접수분은
**한 건도 감지되지 않았고**, 아웃박스가 배수되지 않았다 (`03-HANDOFF §4 #32`).

**무엇으로 바꾸는가** — 대상 연구실을 **원장에서 읽고**, 연구실마다 **제 트랜잭션 · 제 스코프**로
한 바퀴를 돈다. 워커는 한 번에 **하나의 연구실 스코프만** 갖는다. 사고가 나도 범위가 그 한 바퀴다.

**왜 시스템 롤을 새로 만들지 않는가** — 대상 목록의 출처가 `d1_lab` 이고, 그 표는 **테넌트 루트
그 자체라 RLS 대상이 아니다**(`gates/config/rls-allowlist.toml` `allow_no_rls`). 이벤트 표를 여는
면제도, BYPASSRLS 롤도, 마이그레이션도 필요하지 않다 — 접속 주체는 그대로 비소유자 ·
NOBYPASSRLS 앱 롤이다.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest
from sqlalchemy import text

from colab_pipeline.app.worker import ENV_ACCOUNT, ENV_LAB, ENV_UPLOAD_DIR, run_once
from colab_pipeline.domains.d5_ingestion import SqlLedger
from colab_pipeline.kernel import storage_layout
from colab_pipeline.kernel.db import apply_scope, clear_scope, make_engine, make_session_factory
from fixture_builders import make_readable_geotiff

pytestmark = pytest.mark.dbint

_ENV = "COLAB_PIPELINE_DB_URL"

# 시드(`services/core-api/tests/fixtures/seed.sql`)의 두 연구실. D1 은 shared kernel 이라
# `d5_*` 의 FK 가 이 값을 요구한다 — 지어낸 ID 를 넣으면 FK 가 죽는다.
_LAB_A, _ACC_A = "0000000000000000000000000A", "000000000000000000000000A1"
_LAB_B, _ACC_B = "0000000000000000000000000B", "00000000000000000000000BP1"


def _url() -> str:
    url = os.environ.get(_ENV)
    if not url:
        pytest.fail(f"{_ENV} 가 없다 — DB 시험을 DB 없이 green 으로 세지 않는다 (CLAUDE.md §4)")
    return url


@pytest.fixture()
def factory():
    engine = make_engine(_url())
    yield make_session_factory(engine)
    engine.dispose()


def _ulid(tail: str) -> str:
    return ("01JQ" + "0" * 22)[: 26 - len(tail)] + tail


def _cleanup(factory, lab: str, acc: str, upload_id: str) -> None:
    s = factory()
    try:
        s.begin()
        apply_scope(s, lab_id=lab, account_id=acc)
        s.execute(text("DELETE FROM d5_upload WHERE id = :u"), {"u": upload_id})
        s.commit()
    finally:
        s.close()


def _seed_upload(factory, *, lab: str, acc: str, upload_id: str, file_id: str,
                 upload_dir: Path, tmp_path: Path) -> None:
    """접수 사실을 세우고 바이트를 제 자리에 둔다 — core-api 가 하는 일의 최소판."""
    src = make_readable_geotiff(tmp_path / f"{file_id}.tif")
    blob = storage_layout.storage_path(upload_dir, upload_id, file_id=file_id,
                                       kind=storage_layout.BODY_KIND, file_name=src.name)
    blob.parent.mkdir(parents=True, exist_ok=True)
    blob.write_bytes(src.read_bytes())

    s = factory()
    try:
        s.begin()
        apply_scope(s, lab_id=lab, account_id=acc)
        s.execute(text("""
            INSERT INTO d5_upload (id, lab_id, uploader_account_id, expires_at)
            VALUES (:id, :lab, :acc, now() + interval '24 hours')
        """), {"id": upload_id, "lab": lab, "acc": acc})
        s.execute(text("""
            INSERT INTO d5_pipeline_event
              (id, lab_id, actor_account_id, upload_id, event_type, schema_version, source,
               idempotency_key, payload)
            VALUES (:eid, :lab, :acc, :uid, 'upload.accepted', '1.0', 'core-api', :key,
                    CAST(:payload AS jsonb))
        """), {"eid": _ulid(file_id[-4:] + "A"), "lab": lab, "acc": acc, "uid": upload_id,
               "key": f"upload.accepted:{upload_id}",
               "payload": ('{"files": [{"fileId": "%s", "kind": "본체", "fileName": "%s"}]}'
                           % (file_id, src.name))})
        s.commit()
    finally:
        s.close()


def _ready(factory, *, lab: str, acc: str, upload_id: str) -> bool:
    s = factory()
    try:
        s.begin()
        apply_scope(s, lab_id=lab, account_id=acc)
        return bool(s.execute(text("SELECT ready FROM d5_upload WHERE id = :u"),
                              {"u": upload_id}).scalar_one())
    finally:
        s.rollback()
        s.close()


def test_run_once_covers_every_lab_not_just_one(factory, tmp_path, monkeypatch):
    """**#32 의 본체.** 두 연구실의 접수분이 **한 바퀴에 각각** 처리된다."""
    up_a, up_b = _ulid("SCA1"), _ulid("SCB1")
    upload_dir = tmp_path / "store"
    try:
        _seed_upload(factory, lab=_LAB_A, acc=_ACC_A, upload_id=up_a,
                     file_id=_ulid("FA01"), upload_dir=upload_dir, tmp_path=tmp_path)
        _seed_upload(factory, lab=_LAB_B, acc=_ACC_B, upload_id=up_b,
                     file_id=_ulid("FB01"), upload_dir=upload_dir, tmp_path=tmp_path)

        monkeypatch.delenv(ENV_LAB, raising=False)
        monkeypatch.delenv(ENV_ACCOUNT, raising=False)
        monkeypatch.setenv(ENV_UPLOAD_DIR, str(upload_dir))

        sent: list[dict] = []
        processed, n, _reaped = run_once(publish=sent.append)

        assert up_a in processed and up_b in processed
        assert _ready(factory, lab=_LAB_A, acc=_ACC_A, upload_id=up_a) is True
        assert _ready(factory, lab=_LAB_B, acc=_ACC_B, upload_id=up_b) is True
        # 아웃박스가 두 연구실 모두 배수된다 — #32 의 실측 증상이 「전건 published_at NULL」이었다.
        labs = {e["labId"] for e in sent}
        assert {_LAB_A, _LAB_B} <= labs
        assert n == len(sent)
    finally:
        _cleanup(factory, _LAB_A, _ACC_A, up_a)
        _cleanup(factory, _LAB_B, _ACC_B, up_b)


def test_a_lab_pass_reads_no_other_lab_row(factory, tmp_path):
    """음성 — 한 연구실 스코프 안에서 **다른 연구실 행이 한 건도 조회되지 않는다.**"""
    up_a, up_b = _ulid("SCA2"), _ulid("SCB2")
    upload_dir = tmp_path / "store"
    try:
        _seed_upload(factory, lab=_LAB_A, acc=_ACC_A, upload_id=up_a,
                     file_id=_ulid("FA02"), upload_dir=upload_dir, tmp_path=tmp_path)
        _seed_upload(factory, lab=_LAB_B, acc=_ACC_B, upload_id=up_b,
                     file_id=_ulid("FB02"), upload_dir=upload_dir, tmp_path=tmp_path)

        s = factory()
        try:
            s.begin()
            apply_scope(s, lab_id=_LAB_A, account_id=_ACC_A)
            ledger = SqlLedger(s)
            assert {r["lab_id"] for r in ledger.pending_uploads(limit=100)} == {_LAB_A}
            assert up_b not in {r["id"] for r in ledger.pending_uploads(limit=100)}
            assert {e["labId"] for e in ledger.unpublished(limit=100)} == {_LAB_A}
        finally:
            s.rollback()
            s.close()
    finally:
        _cleanup(factory, _LAB_A, _ACC_A, up_a)
        _cleanup(factory, _LAB_B, _ACC_B, up_b)


def test_scope_is_released_and_the_release_is_default_deny(factory):
    """스코프 해제 — 해제 뒤에는 `current_lab_id()` 가 NULL 이고 **한 행도 보이지 않는다.**"""
    s = factory()
    try:
        s.begin()
        apply_scope(s, lab_id=_LAB_A, account_id=_ACC_A)
        assert s.execute(text("SELECT current_lab_id()")).scalar_one() == _LAB_A
        clear_scope(s)
        assert s.execute(text("SELECT current_lab_id()")).scalar_one() is None
        assert s.execute(text("SELECT current_account_id()")).scalar_one() is None
        for table in ("d5_pipeline_event", "d5_upload", "d5_upload_file"):
            assert s.execute(text(f"SELECT count(*) FROM {table}")).scalar_one() == 0
    finally:
        s.rollback()
        s.close()


def test_worker_role_holds_no_blanket_exemption(factory):
    """음성 — 워커의 접속 주체는 **면제를 갖지 않는다.** 이벤트 표도 예외가 아니다."""
    s = factory()
    try:
        s.begin()
        attrs = s.execute(text("""
            SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user
        """)).one()
        assert attrs.rolsuper is False and attrs.rolbypassrls is False
        owned = s.execute(text("""
            SELECT count(*) FROM pg_tables
             WHERE schemaname = 'public' AND tableowner = current_user
        """)).scalar_one()
        assert owned == 0
        # 스코프를 세우지 않은 채로는 이벤트 표가 **기본 거부**다.
        assert s.execute(text("SELECT count(*) FROM d5_pipeline_event")).scalar_one() == 0
    finally:
        s.rollback()
        s.close()


def test_an_exception_in_one_lab_pass_leaks_no_scope_to_the_next(factory, tmp_path,
                                                                 monkeypatch):
    """음성 — 한 연구실 바퀴가 **예외로 끝나도** 다음 접속에 스코프가 새지 않는다.

    `SET LOCAL` 이 트랜잭션 끝에 사라지는 것은 맞지만, **커넥션 풀 재사용 경로에서**
    그것을 값으로 확인한다. 스코프가 새면 다음 연구실 바퀴가 앞 연구실의 행을 본다.
    """
    from colab_pipeline.app import worker as worker_mod

    def _boom(*_a, **_k):
        raise RuntimeError("배관이 깨졌다")

    monkeypatch.setattr(worker_mod, "drive_uploads", _boom)
    with pytest.raises(RuntimeError):
        worker_mod._lab_pass(factory, _LAB_A, worker_account=_ACC_A,
                             upload_dir=tmp_path / "store", workdir=tmp_path / "w",
                             publish=lambda _e: None)

    s = factory()          # 풀에서 같은 커넥션이 돌아온다
    try:
        s.begin()
        assert s.execute(text("SELECT current_lab_id()")).scalar_one() is None
        assert s.execute(text("SELECT count(*) FROM d5_pipeline_event")).scalar_one() == 0
        assert s.execute(text("SELECT count(*) FROM d5_upload")).scalar_one() == 0
    finally:
        s.rollback()
        s.close()


def test_unscoped_reach_is_the_allowlist_and_nothing_more(factory):
    """음성 — 스코프 없이 보이는 표가 **면제 목록 그대로**다. 이벤트 표는 거기 없다.

    「이벤트 표 하나만 여는 시스템 권한」 대신 이 배선이 쓰는 것은 **이미 면제인 `d1_lab`**
    하나다(`gates/config/rls-allowlist.toml` `[platform].allow_no_rls`). 그 사실을 목록이
    아니라 **행 수**로 확인한다 — 면제가 하나라도 더 열리면 여기서 red 다.
    """
    exempt = {"d1_lab", "alembic_version_platform"}
    s = factory()
    try:
        s.begin()
        tables = [r[0] for r in s.execute(text("""
            SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY 1
        """))]
        assert "d5_pipeline_event" in tables and "d1_lab" in tables
        visible = {t for t in tables
                   if s.execute(text(f"SELECT count(*) FROM {t}")).scalar_one() > 0}
        assert visible <= exempt
        # 그리고 그 하나는 실제로 보인다 — 「전부 0」이 시험을 거짓 green 으로 만들지 않는다.
        assert s.execute(text("SELECT count(*) FROM d1_lab")).scalar_one() >= 2
    finally:
        s.rollback()
        s.close()
