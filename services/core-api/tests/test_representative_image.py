"""사용자가 고른 대표 그림의 저장·재조회·권한 계약."""
from __future__ import annotations

import io
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from PIL import Image

from conftest import DS_A2, DS_B1, TOKEN_PROF, TOKEN_RES, auth
from test_dataset_registration import make_upload, register

from colab_core.app.main import API_PREFIX

def _actual_image(format_: str, color: tuple[int, int, int]) -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (2, 2), color).save(output, format=format_)
    return output.getvalue()


# Pillow가 픽셀까지 해제하는 실제 파일이다. 성공 fixture가 헤더 몇 바이트뿐이면
# 서버가 헤더만 믿는 구현으로도 시험이 green이 되어 손상 파일을 저장한다.
PNG = _actual_image("PNG", (20, 30, 40))
JPEG = _actual_image("JPEG", (50, 60, 70))
WEBP = _actual_image("WEBP", (80, 90, 100))


def _put(client, dataset_id: str, payload: bytes = PNG, *, name: str = "대표.png",
         content_type: str = "image/png", token: str = TOKEN_RES):
    return client.put(
        f"{API_PREFIX}/datasets/{dataset_id}/representative-image",
        files={"image": (name, payload, content_type)}, headers=auth(token))


def _registered(client) -> str:
    response = register(client, make_upload(client))
    assert response.status_code == 201, response.text
    return response.json()["datasetId"]


def test_uploaded_image_survives_detail_reload_and_bearer_byte_fetch(p2_client, sql) -> None:
    """저장 뒤 메타만 남거나 URL을 직접 노출해 재접속 그림이 깨지는 회귀를 잡는다."""
    client = p2_client()
    dataset_id = _registered(client)
    saved = _put(client, dataset_id)
    assert saved.status_code == 200, saved.text
    assert saved.json() == {"custom": True, "fileName": "대표.png",
                            "contentType": "image/png", "sizeBytes": len(PNG)}

    detail = client.get(f"{API_PREFIX}/datasets/{dataset_id}", headers=auth(TOKEN_RES))
    assert detail.status_code == 200, detail.text
    assert detail.json()["representativeImage"] == saved.json()
    assert "url" not in detail.json()["representativeImage"]

    fetched = client.get(
        f"{API_PREFIX}/datasets/{dataset_id}/representative-image", headers=auth(TOKEN_RES))
    assert fetched.status_code == 200, fetched.text
    assert fetched.content == PNG
    assert fetched.headers["content-type"].startswith("image/png")

    row = sql("SELECT file_name, content_type, size_bytes, storage_key"
              " FROM d3_dataset_representative_image WHERE dataset_id = :d", {"d": dataset_id})
    assert [(r["file_name"], r["content_type"], r["size_bytes"]) for r in row] == [
        ("대표.png", "image/png", len(PNG))]
    assert row[0]["storage_key"].startswith(f"representative-images/{dataset_id}/")


def test_actual_signature_size_and_declared_content_type_are_all_enforced(p2_client, sql) -> None:
    """확장자만 믿거나 Content-Type 불일치·10MiB 경계를 빠뜨리는 회귀를 잡는다."""
    client = p2_client()
    dataset_id = _registered(client)
    assert _put(client, dataset_id, b"not-a-png", name="fake.png").status_code == 415
    assert _put(client, dataset_id, JPEG, name="photo.jpg", content_type="image/png").status_code == 415
    assert _put(client, dataset_id, PNG[:24], name="truncated.png").status_code == 415
    assert _put(client, dataset_id, JPEG[:-12], name="truncated.jpg",
                content_type="image/jpeg").status_code == 415
    assert _put(client, dataset_id, WEBP[:-5], name="truncated.webp",
                content_type="image/webp").status_code == 415
    broken_entropy = JPEG[:-40] + b"\x00" * 38 + b"\xff\xd9"
    assert _put(client, dataset_id, broken_entropy, name="broken.jpg",
                content_type="image/jpeg").status_code == 415
    oversized = _put(client, dataset_id, PNG + b"x" * (10 * 1024 * 1024), name="large.png")
    assert oversized.status_code == 413, oversized.text
    assert sql("SELECT count(*) AS n FROM d3_dataset_representative_image"
               " WHERE dataset_id = :d", {"d": dataset_id})[0]["n"] == 0


def test_locked_body_and_cross_lab_dataset_do_not_expose_or_accept_image_bytes(p2_client) -> None:
    """메타 RLS만 보고 본체 접근 검사를 빼는 회귀를 잡는다."""
    client = p2_client()
    locked_get = client.get(
        f"{API_PREFIX}/datasets/{DS_A2}/representative-image", headers=auth(TOKEN_PROF))
    assert _put(client, DS_A2, token=TOKEN_PROF).status_code == 403
    assert locked_get.status_code == 403, locked_get.text
    foreign_get = client.get(
        f"{API_PREFIX}/datasets/{DS_B1}/representative-image", headers=auth(TOKEN_PROF))
    assert _put(client, DS_B1, token=TOKEN_PROF).status_code == 404
    assert foreign_get.status_code == 404, foreign_get.text


def test_delete_removes_only_custom_image_and_detail_returns_to_automatic(p2_client, sql) -> None:
    """삭제가 본체/자동 그림까지 지우거나 사용자 그림 메타를 남기는 회귀를 잡는다."""
    client = p2_client()
    dataset_id = _registered(client)
    assert _put(client, dataset_id).status_code == 200
    removed = client.delete(
        f"{API_PREFIX}/datasets/{dataset_id}/representative-image", headers=auth(TOKEN_RES))
    assert removed.status_code == 204, removed.text
    detail = client.get(f"{API_PREFIX}/datasets/{dataset_id}", headers=auth(TOKEN_RES)).json()
    assert detail["representativeImage"] == {
        "custom": False, "fileName": None, "contentType": None, "sizeBytes": None}
    assert sql("SELECT count(*) AS n FROM d3_dataset_representative_image"
               " WHERE dataset_id = :d", {"d": dataset_id})[0]["n"] == 0
    assert client.get(f"{API_PREFIX}/datasets/{dataset_id}/representative-image",
                      headers=auth(TOKEN_RES)).status_code == 404


def test_replacement_commits_new_reference_then_removes_old_bytes(p2_client, tmp_path, sql) -> None:
    """교체 뒤 이전 바이트를 orphan으로 남기거나 새 참조 전에 지우는 회귀를 잡는다."""
    client = p2_client()
    dataset_id = _registered(client)
    assert _put(client, dataset_id).status_code == 200
    old_key = sql("SELECT storage_key FROM d3_dataset_representative_image WHERE dataset_id = :d",
                  {"d": dataset_id})[0]["storage_key"]
    replaced = _put(client, dataset_id, JPEG, name="둘째.jpg", content_type="image/jpeg")
    assert replaced.status_code == 200, replaced.text
    new_key = sql("SELECT storage_key FROM d3_dataset_representative_image WHERE dataset_id = :d",
                  {"d": dataset_id})[0]["storage_key"]
    root = tmp_path / "uploads"
    assert new_key != old_key and (root / new_key).is_file()
    assert not (root / old_key).exists()
    fetched = client.get(f"{API_PREFIX}/datasets/{dataset_id}/representative-image",
                         headers=auth(TOKEN_RES))
    assert fetched.content == JPEG and fetched.headers["content-type"].startswith("image/jpeg")


def test_db_failure_discards_new_orphan_and_preserves_previous_image(
        p2_client, tmp_path, monkeypatch) -> None:
    """새 바이트 뒤 DB 실패가 이전 참조를 깨거나 orphan을 남기는 회귀를 잡는다."""
    from colab_core.domains import d3_catalog

    client = p2_client()
    dataset_id = _registered(client)
    assert _put(client, dataset_id).status_code == 200
    image_dir = tmp_path / "uploads" / "representative-images" / dataset_id
    assert len(list(image_dir.iterdir())) == 1

    def fail_upsert(*args, **kwargs):
        raise RuntimeError("injected database failure")

    monkeypatch.setattr(d3_catalog, "upsert_representative_image", fail_upsert)
    failed = _put(client, dataset_id, JPEG, name="실패.jpg", content_type="image/jpeg")
    assert failed.status_code == 500
    assert len(list(image_dir.iterdir())) == 1, "DB 실패 뒤 새 저장 바이트가 orphan으로 남았다."
    fetched = client.get(f"{API_PREFIX}/datasets/{dataset_id}/representative-image",
                         headers=auth(TOKEN_RES))
    assert fetched.status_code == 200 and fetched.content == PNG


def test_storage_failure_does_not_change_previous_reference(p2_client, tmp_path, monkeypatch) -> None:
    """새 저장 실패 때 기존 DB 참조와 바이트를 먼저 지우는 회귀를 잡는다."""
    client = p2_client()
    dataset_id = _registered(client)
    assert _put(client, dataset_id).status_code == 200
    storage = client.app.state.upload_storage

    def fail_put(*, key, payload):
        raise OSError("injected storage failure")

    monkeypatch.setattr(storage, "put", fail_put)
    failed = _put(client, dataset_id, JPEG, name="실패.jpg", content_type="image/jpeg")
    assert failed.status_code == 500
    image_dir = tmp_path / "uploads" / "representative-images" / dataset_id
    assert len(list(image_dir.iterdir())) == 1
    fetched = client.get(f"{API_PREFIX}/datasets/{dataset_id}/representative-image",
                         headers=auth(TOKEN_RES))
    assert fetched.status_code == 200 and fetched.content == PNG


def test_partial_storage_put_failure_best_effort_discards_the_new_key(
        p2_client, tmp_path, monkeypatch) -> None:
    """저장기가 일부 바이트를 쓴 뒤 실패해도 새 키가 orphan으로 남는 회귀를 잡는다."""
    client = p2_client()
    dataset_id = _registered(client)
    assert _put(client, dataset_id).status_code == 200
    storage = client.app.state.upload_storage
    real_put = storage.put

    def partially_put_then_fail(*, key, payload):
        real_put(key=key, payload=payload)
        raise OSError("injected failure after partial write")

    monkeypatch.setattr(storage, "put", partially_put_then_fail)
    failed = _put(client, dataset_id, JPEG, name="부분.jpg", content_type="image/jpeg")
    assert failed.status_code == 500
    image_dir = tmp_path / "uploads" / "representative-images" / dataset_id
    assert len(list(image_dir.iterdir())) == 1, "부분 PUT의 새 키가 orphan으로 남았다."


def test_partial_put_and_discard_double_failure_is_left_in_pending_cleanup(
        p2_client, tmp_path, sql, monkeypatch) -> None:
    """부분 PUT과 즉시 정리가 함께 실패해도 새 키의 재시도 근거를 잃는 회귀를 잡는다."""
    client = p2_client()
    dataset_id = _registered(client)
    assert _put(client, dataset_id).status_code == 200
    storage = client.app.state.upload_storage
    real_put = storage.put
    real_discard = storage.discard

    def partially_put_then_fail(*, key, payload):
        real_put(key=key, payload=payload)
        raise OSError("injected failure after partial write")

    def fail_discard(*, key, keep=None):
        raise OSError("injected cleanup failure")

    monkeypatch.setattr(storage, "put", partially_put_then_fail)
    monkeypatch.setattr(storage, "discard", fail_discard)
    failed = _put(client, dataset_id, JPEG, name="이중실패.jpg", content_type="image/jpeg")
    assert failed.status_code == 500
    pending = sql("SELECT storage_key FROM d3_representative_image_cleanup"
                  " WHERE dataset_id = :d", {"d": dataset_id})
    assert len(pending) == 1
    orphan_key = pending[0]["storage_key"]
    assert (tmp_path / "uploads" / orphan_key).is_file()

    monkeypatch.setattr(storage, "put", real_put)
    monkeypatch.setattr(storage, "discard", real_discard)
    retried = client.delete(
        f"{API_PREFIX}/datasets/{dataset_id}/representative-image", headers=auth(TOKEN_RES))
    assert retried.status_code == 204
    assert sql("SELECT count(*) AS n FROM d3_representative_image_cleanup"
               " WHERE dataset_id = :d", {"d": dataset_id})[0]["n"] == 0
    assert not (tmp_path / "uploads" / orphan_key).exists()


def test_replacement_cleanup_failure_is_pending_and_next_put_retries_it(
        p2_client, tmp_path, sql, monkeypatch) -> None:
    """확정 뒤 이전 키 정리 실패가 PUT을 500으로 뒤집거나 재시도 근거를 잃는 회귀를 잡는다."""
    client = p2_client()
    dataset_id = _registered(client)
    assert _put(client, dataset_id).status_code == 200
    old_key = sql("SELECT storage_key FROM d3_dataset_representative_image WHERE dataset_id = :d",
                  {"d": dataset_id})[0]["storage_key"]
    storage = client.app.state.upload_storage
    real_discard = storage.discard

    def fail_discard(*, key, keep=None):
        raise OSError("injected cleanup failure")

    monkeypatch.setattr(storage, "discard", fail_discard)
    replaced = _put(client, dataset_id, JPEG, name="둘째.jpg", content_type="image/jpeg")
    assert replaced.status_code == 200, replaced.text
    current_key = sql(
        "SELECT storage_key FROM d3_dataset_representative_image WHERE dataset_id = :d",
        {"d": dataset_id})[0]["storage_key"]
    pending = sql("SELECT storage_key FROM d3_representative_image_cleanup"
                  " WHERE dataset_id = :d ORDER BY created_at", {"d": dataset_id})
    assert [row["storage_key"] for row in pending] == [old_key]
    assert (tmp_path / "uploads" / old_key).is_file()

    monkeypatch.setattr(storage, "discard", real_discard)
    retried = _put(client, dataset_id, WEBP, name="셋째.webp", content_type="image/webp")
    assert retried.status_code == 200, retried.text
    assert sql("SELECT count(*) AS n FROM d3_representative_image_cleanup"
               " WHERE dataset_id = :d", {"d": dataset_id})[0]["n"] == 0
    assert not (tmp_path / "uploads" / old_key).exists()
    assert not (tmp_path / "uploads" / current_key).exists()


def test_delete_cleanup_failure_is_pending_and_later_delete_retries_it(
        p2_client, tmp_path, sql, monkeypatch) -> None:
    """삭제 확정 뒤 바이트 정리 실패가 204를 깨거나 재시도 없이 orphan을 남기는 회귀를 잡는다."""
    client = p2_client()
    dataset_id = _registered(client)
    assert _put(client, dataset_id).status_code == 200
    removed_key = sql(
        "SELECT storage_key FROM d3_dataset_representative_image WHERE dataset_id = :d",
        {"d": dataset_id})[0]["storage_key"]
    storage = client.app.state.upload_storage
    real_discard = storage.discard

    def fail_discard(*, key, keep=None):
        raise OSError("injected cleanup failure")

    monkeypatch.setattr(storage, "discard", fail_discard)
    removed = client.delete(
        f"{API_PREFIX}/datasets/{dataset_id}/representative-image", headers=auth(TOKEN_RES))
    assert removed.status_code == 204, removed.text
    assert sql("SELECT storage_key FROM d3_representative_image_cleanup WHERE dataset_id = :d",
               {"d": dataset_id}) == [{"storage_key": removed_key}]
    assert (tmp_path / "uploads" / removed_key).is_file()

    monkeypatch.setattr(storage, "discard", real_discard)
    retried = client.delete(
        f"{API_PREFIX}/datasets/{dataset_id}/representative-image", headers=auth(TOKEN_RES))
    assert retried.status_code == 204, retried.text
    assert sql("SELECT count(*) AS n FROM d3_representative_image_cleanup"
               " WHERE dataset_id = :d", {"d": dataset_id})[0]["n"] == 0
    assert not (tmp_path / "uploads" / removed_key).exists()


def test_dataset_row_lock_serializes_competing_replacements(session_factory) -> None:
    """동시 PUT 둘이 같은 previous를 읽어 중간 이미지를 orphan으로 만드는 회귀를 잡는다."""
    import pytest
    from sqlalchemy import text
    from sqlalchemy.exc import OperationalError

    from colab_core.domains import d3_catalog
    from colab_core.kernel.auth import Subject
    from colab_core.kernel.ids import Ulid
    from colab_core.kernel.scope import apply_scope
    from conftest import ACC_A_RES, LAB_A, DS_A1

    first, second = session_factory(), session_factory()
    try:
        first.begin()
        second.begin()
        subject = Subject(account_id=Ulid(ACC_A_RES), lab_id=Ulid(LAB_A))
        apply_scope(first, subject)
        apply_scope(second, subject)
        d3_catalog.lock_dataset_for_representative_image(first, Ulid(DS_A1))
        second.execute(text("SET LOCAL statement_timeout = '100ms'"))
        with pytest.raises(OperationalError):
            d3_catalog.lock_dataset_for_representative_image(second, Ulid(DS_A1))
    finally:
        first.rollback()
        second.rollback()
        first.close()
        second.close()


def test_older_post_commit_drain_preserves_cleanup_queued_by_newer_put(
        p2_client, tmp_path, sql, monkeypatch) -> None:
    """이전 PUT의 keep drain이 뒤 PUT이 남긴 같은 키 원장을 지워 orphan을 만드는 회귀를 잡는다."""
    from colab_core.app.routes import representative_image

    first_client, second_client = p2_client(), p2_client()
    dataset_id = _registered(first_client)
    real_drain = representative_image._drain_cleanups
    first_drain_entered = threading.Event()
    release_first_drain = threading.Event()
    first_drain_finished = threading.Event()
    call_lock = threading.Lock()
    drain_calls = 0

    def interleave_committed_drains(storage, db, subject, current_dataset_id, *, keep=None):
        nonlocal drain_calls
        with call_lock:
            drain_calls += 1
            ordinal = drain_calls
        if ordinal == 1:
            # 첫 PUT은 이미 commit하고 dataset lock을 놓았다. 두 번째 PUT이 그 키를
            # cleanup 원장에 넣을 때까지 첫 drain을 멈춘다.
            first_drain_entered.set()
            assert release_first_drain.wait(3), "두 번째 PUT이 commit 뒤 drain에 닿지 않았다."
            real_drain(storage, db, subject, current_dataset_id, keep=keep)
            first_drain_finished.set()
            return
        release_first_drain.set()
        assert first_drain_finished.wait(3), "첫 drain이 같은 keep 키 원장을 검사하지 못했다."
        real_drain(storage, db, subject, current_dataset_id, keep=keep)

    monkeypatch.setattr(representative_image, "_drain_cleanups", interleave_committed_drains)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(_put, first_client, dataset_id, PNG,
                            name="교차1.png", content_type="image/png")
        assert first_drain_entered.wait(3), "첫 PUT이 commit 뒤 drain에 닿지 않았다."
        second = pool.submit(_put, second_client, dataset_id, JPEG,
                             name="교차2.jpg", content_type="image/jpeg")
        assert first.result(timeout=5).status_code == 200
        assert second.result(timeout=5).status_code == 200

    rows = sql("SELECT storage_key FROM d3_dataset_representative_image WHERE dataset_id = :d",
               {"d": dataset_id})
    assert len(rows) == 1
    image_dir = tmp_path / "uploads" / "representative-images" / dataset_id
    assert [path.name for path in image_dir.iterdir()] == [rows[0]["storage_key"].rsplit("/", 1)[1]]
    assert sql("SELECT count(*) AS n FROM d3_representative_image_cleanup"
               " WHERE dataset_id = :d", {"d": dataset_id})[0]["n"] == 0


def test_two_real_puts_leave_one_reference_one_byte_key_and_no_pending_cleanup(
        p2_client, tmp_path, sql, monkeypatch) -> None:
    """동시 HTTP 교체가 최종 참조 밖의 바이트나 처리 대기 행을 남기는 회귀를 잡는다."""
    first_client, second_client = p2_client(), p2_client()
    dataset_id = _registered(first_client)
    storage = first_client.app.state.upload_storage
    real_put = storage.put
    first_inside_put = threading.Event()
    release_first = threading.Event()
    call_lock = threading.Lock()
    put_calls = 0

    def block_first_put(*, key, payload):
        nonlocal put_calls
        with call_lock:
            put_calls += 1
            ordinal = put_calls
        if ordinal == 1:
            first_inside_put.set()
            assert release_first.wait(3), "첫 PUT 해제 신호가 오지 않았다."
        real_put(key=key, payload=payload)

    monkeypatch.setattr(storage, "put", block_first_put)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(_put, first_client, dataset_id, PNG,
                            name="동시1.png", content_type="image/png")
        assert first_inside_put.wait(3), "첫 요청이 dataset lock 안의 storage.put에 닿지 않았다."
        second = pool.submit(_put, second_client, dataset_id, JPEG,
                             name="동시2.jpg", content_type="image/jpeg")
        time.sleep(0.15)
        assert not second.done(), "두 번째 PUT이 첫 dataset lock을 건너뛰었다."
        release_first.set()
        assert first.result(timeout=5).status_code == 200
        assert second.result(timeout=5).status_code == 200

    rows = sql("SELECT storage_key FROM d3_dataset_representative_image WHERE dataset_id = :d",
               {"d": dataset_id})
    assert len(rows) == 1
    image_dir = tmp_path / "uploads" / "representative-images" / dataset_id
    assert [path.name for path in image_dir.iterdir()] == [rows[0]["storage_key"].rsplit("/", 1)[1]]
    assert sql("SELECT count(*) AS n FROM d3_representative_image_cleanup"
               " WHERE dataset_id = :d", {"d": dataset_id})[0]["n"] == 0


def test_upload_needs_the_existing_edit_permission(p2_client, sql) -> None:
    """화면에서 숨긴 편집 기능을 서버 권한 없이 호출하는 회귀를 잡는다."""
    client = p2_client()
    dataset_id = _registered(client)
    sql("UPDATE d2_permission_switch SET enabled = false"
        " WHERE account_id = '000000000000000000000000A1' AND switch = '업로드·편집'")
    assert _put(client, dataset_id).status_code == 403
