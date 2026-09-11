"""pytest-xdist worker마다 core-api 전용 일회용 DB URL을 주입한다."""
from __future__ import annotations

import os
import pathlib

import pytest


def pytest_configure(config: pytest.Config) -> None:
    worker = getattr(config, "workerinput", None)
    if worker is None:
        return
    worker_id = worker.get("workerid")
    db_dir = os.environ.get("COLAB_CORE_XDIST_DB_DIR")
    if not worker_id or not db_dir:
        raise pytest.UsageError("core-api xdist worker DB 배선이 없다")
    path = pathlib.Path(db_dir) / worker_id
    try:
        url = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise pytest.UsageError(
            f"core-api xdist worker DB 파일을 읽지 못했다: {worker_id} ({type(exc).__name__})"
        ) from None
    if not url:
        raise pytest.UsageError(f"core-api xdist worker DB URL이 비었다: {worker_id}")
    os.environ["COLAB_CORE_TEST_DATABASE_URL"] = url
