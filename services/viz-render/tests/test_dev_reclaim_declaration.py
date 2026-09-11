"""dev 배포가 BF-12 회수 루프의 이벤트 버스를 실제로 공유하는가."""
from __future__ import annotations

import re
from pathlib import Path

COMPOSE = Path(__file__).resolve().parents[3] / "infra" / "dev" / "compose.yml"


def _service(name: str) -> str:
    raw = COMPOSE.read_text(encoding="utf-8")
    found = re.search(rf"^  {re.escape(name)}:\n(.*?)(?=^  \S|^volumes:)", raw, re.S | re.M)
    assert found is not None
    return found.group(1)


def _env(block: str, key: str) -> str | None:
    found = re.search(rf"^\s+{re.escape(key)}:\s*(.+?)\s*$", block, re.M)
    return found.group(1).strip() if found else None


def _mounts(block: str) -> list[str]:
    return re.findall(r"^\s+- (\S+)\s*$", block, re.M)


def test_dev의_발행자와_구독자가_쓰기_가능한_버스_하나를_공유한다():
    worker = _service("pipeline-worker")
    viz = _service("viz-render")
    pub = _env(worker, "COLAB_WORKER_EVENT_SPOOL")
    sub = _env(viz, "COLAB_VIZ_TRIGGER_SPOOL")
    assert pub == sub != None  # noqa: E711
    for block in (worker, viz):
        matches = [m for m in _mounts(block) if m.split(":")[1:2] == [pub]]
        assert matches, f"공유 버스 {pub}가 컨테이너에 마운트되지 않았다"
        assert not matches[0].endswith(":ro"), "ack를 위해 양쪽 모두 쓰기 가능해야 한다"


def test_dev의_공유_버스_volume이_선언돼_있고_S3_apply는_켜지_않는다():
    raw = COMPOSE.read_text(encoding="utf-8")
    assert re.search(r"^  events:\s*\{\}\s*$", raw, re.M)
    assert "COLAB_VIZ_TILE_RECLAIM_APPLY:" not in _service("viz-render")
