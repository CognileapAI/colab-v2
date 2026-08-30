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


# ── ⭑ ⟨증보 2026-08-31 · `#49` · Ted 판정 `PLAN-SoT §9 〈235〉`⟩ ─────────────────
# 자리가 **배포 안에만 있으면 아무도 그것을 검사할 수 없다.**
# 실측(`sessions/PV-1-DEPLOY-WIRING-20260830.md §4-㈏`) = named volume 의 마운트 지점이
# 게이트를 돌리는 사용자에게 `Permission denied` 였다. 그래서 게이트 `preview-tile-slot` 은
# 「자리를 못 봐서 검사를 못 했다」로 red(준비) 였고, 그것을 통과로 세는 것이 이 레포의
# 대표 실패다(`CLAUDE.md §4`). 아래 셋은 **자리가 호스트에서 보이는가**를 잰다.


def _volumes_block() -> str:
    raw = COMPOSE.read_text(encoding="utf-8")
    m = re.search(r"^volumes:\n(.*)\Z", raw, re.S | re.M)
    assert m is not None, "compose 에 volumes 선언이 없다"
    return m.group(1)


def _named_volume(name: str) -> str:
    m = re.search(rf"^  {re.escape(name)}:(.*?)(?=^  \S|\Z)", _volumes_block(), re.S | re.M)
    assert m is not None, f"volumes 에 `{name}` 이 없다"
    return m.group(1)


@pytest.mark.stage2
def test_preview_volume_is_backed_by_a_host_path():
    """미리보기 루트는 **호스트에서 보여야 한다** — 도커 안에만 있으면 검사가 불가능하다."""
    block = _named_volume("previews")
    assert re.search(r"^\s+type:\s*none\s*$", block, re.M), "바인드 선언(type: none)이 없다"
    assert re.search(r"^\s+o:\s*bind\s*$", block, re.M), "바인드 선언(o: bind)이 없다"
    assert re.search(r"^\s+device:\s*\$\{COLAB_STAGING_PREVIEWS_DIR", block, re.M), \
        "호스트 경로를 env 로 받지 않는다"


@pytest.mark.stage2
def test_the_host_path_is_required_and_never_written_in_the_repo():
    """경로는 `:?` 로 **요구**하고 값은 홈의 env 파일에만 둔다(`CLAUDE.md §3-8`)."""
    block = _named_volume("previews")
    assert "${COLAB_STAGING_PREVIEWS_DIR:?" in block, \
        "값이 없어도 조용히 뜨면 자리가 어디인지 아무도 모른다 — `:?` 로 요구한다"
    assert not re.search(r"device:\s*/(home|mnt|srv|var)/", block), \
        "compose 에 호스트 절대경로를 적지 않는다"


@pytest.mark.stage2
def test_the_preview_root_is_still_one_root():
    """루트를 **가르지 않았다** — 규약은 루트가 하나라고 못 박는다(`previewsRoot`).

    붙는 곳이 넷(nginx·worker·viz-render·volume-init)인데 전부 같은 볼륨 이름이어야 한다.
    """
    raw = COMPOSE.read_text(encoding="utf-8")
    mounts = re.findall(r"^\s+- (previews:\S+)\s*$", raw, re.M)
    assert len(mounts) == 4, f"미리보기 볼륨을 무는 자리가 넷이 아니다: {mounts}"
    roots = {m.split(":")[1] for m in mounts}
    assert roots == {"/srv/viz-previews"}, f"루트가 갈렸다: {roots}"
