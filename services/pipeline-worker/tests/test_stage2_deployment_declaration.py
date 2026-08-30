"""stage 2 를 **배포가 선언하는가** — 선언이 코드에 있고 배포에 없으면 아무 일도 안 난다.

`test_stage2_declaration.py` 는 **코드가 세 상태를 가르는가**를 잰다. 이 파일은 그 다음
칸이다 — **배포가 그 셋 중 무엇을 골랐는가.** 둘은 다른 질문이고, 앞의 것만 green 인
상태가 실제로 오래 서 있었다: 워커에 `COLAB_WORKER_STAGE2` 도 `COLAB_WORKER_PREVIEW_DIR`
도 **둘 다 없어**(`dev-package/RESTART.md §2-④-㉯` 실측) `file.header-parsed` 가 한 건도
발행되지 않았고, 그 침묵을 게이트 `autometa-loss`(대조 대상 0건)와 `preview-tile-slot`
(자리 미선언)이 red 로 받고 있었다.

오라클은 지어낸 것이 아니라 **이 레포가 이미 적어 둔 셋**이다:
  ⑴ `app/worker.py` — `on` 이 아니면 stage 2 를 돌지 않는다(무언은 면제가 아니다).
  ⑵ 같은 파일 — `on` 인데 미리보기 루트가 없으면 **뜨지 않는다**(자리를 모른 채 굽지 않는다).
  ⑶ `contracts/storage/layout.json` `previewsRoot` — 미리보기 루트는 **하나**이고 실제
     경로는 배포가 준다. 워커와 렌더가 다른 자리를 보면 렌더는 영영 못 찾는다
     (`03-HANDOFF §4 #20` 이 접수분 루트에서 한 번 일어난 그 무늬다).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

COMPOSE = Path(__file__).resolve().parents[3] / "infra" / "staging" / "compose.i2.yml"


def _service_block(name: str) -> str:
    """`docker compose` 파서를 들이지 않는다 — 두 칸 들여쓴 서비스 블록을 그대로 뜬다."""
    raw = COMPOSE.read_text(encoding="utf-8")
    m = re.search(rf"^  {re.escape(name)}:\n(.*?)(?=^  \S|^volumes:)", raw, re.S | re.M)
    assert m is not None, f"compose 에 `{name}` 블록이 없다"
    return m.group(1)


def _env(block: str, key: str) -> str | None:
    m = re.search(rf"^\s+{re.escape(key)}:\s*(.+?)\s*$", block, re.M)
    return None if m is None else m.group(1).strip().strip('"').strip("'")


@pytest.mark.stage2
def test_deployment_declares_stage2_on():
    """무언은 면제가 아니다 — 배포가 `on` 을 **말해야** stage 2 가 돈다."""
    assert _env(_service_block("pipeline-worker"), "COLAB_WORKER_STAGE2") == "on"


@pytest.mark.stage2
def test_deployment_gives_the_worker_a_preview_root():
    """`on` 인데 자리가 없으면 워커는 **뜨지 않는다**(`app/worker.py`). 자리를 준다."""
    assert _env(_service_block("pipeline-worker"), "COLAB_WORKER_PREVIEW_DIR")


@pytest.mark.stage2
def test_worker_and_renderer_look_at_the_same_preview_root():
    """미리보기 루트는 **하나**다(`contracts/storage/layout.json` `previewsRoot`).

    굽는 쪽(D5)과 찾아 쓰는 쪽(D7)이 다른 자리를 보면 재사용이 영원히 성립하지 않고,
    그 실패는 에러가 아니라 「매번 다시 굽는다」로 조용히 나온다.
    """
    worker_root = _env(_service_block("pipeline-worker"), "COLAB_WORKER_PREVIEW_DIR")
    viz_root = _env(_service_block("viz-render"), "COLAB_VIZ_PREVIEW_DIR")
    assert worker_root == viz_root != None                        # noqa: E711


@pytest.mark.stage2
def test_the_declared_root_is_actually_mounted_on_the_worker():
    """선언만 있고 볼륨이 없으면 컨테이너 안 임시 자리에 굽고 다음 바퀴에 사라진다."""
    block = _service_block("pipeline-worker")
    root = _env(block, "COLAB_WORKER_PREVIEW_DIR")
    assert root, "자리 선언이 없다"
    mounts = re.findall(r"^\s+- (\S+)\s*$", block, re.M)
    assert any(m.startswith("previews:") and m.split(":")[1] == root for m in mounts), \
        f"미리보기 볼륨이 {root} 에 붙어 있지 않다 — 선언과 실물이 갈렸다: {mounts}"


@pytest.mark.stage2
def test_the_preview_root_owner_is_fixed_before_the_worker_starts():
    """named volume 은 root 소유로 생긴다 — 워커는 uid 10001 이다(`volume-init` 의 이유)."""
    root = _env(_service_block("pipeline-worker"), "COLAB_WORKER_PREVIEW_DIR")
    init = _service_block("volume-init")
    assert root and root in init, "volume-init 이 미리보기 루트의 주인을 안 맞춘다"
