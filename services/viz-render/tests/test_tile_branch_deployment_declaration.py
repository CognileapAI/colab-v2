"""갈래 스위치가 **배포에 도달하는가** — 코드에만 있는 스위치는 아무것도 켜지 못한다.

`test_tile_branch_switch.py` 는 **코드가 스위치를 읽는가**를 잰다. 이 파일은 그 다음 칸이다 —
**배포가 그 스위치를 컨테이너까지 실어 주는가.**

앞의 것만 green 인 상태가 실제로 있었다(2026-08-31 실측). `〈240〉`-㉲ 가 스위치를
`COLAB_VIZ_TILE_BRANCH` 로 세우고 문서가 「홈 env 에 한 줄 넣고 다시 띄운다」라고 적었는데,
`infra/staging/compose.i2.yml` 의 `viz-render` 블록에는 그 키가 **없었다.** `--env-file` 은
compose 파일의 `${...}` 치환에만 쓰이고 컨테이너 환경으로 저절로 흘러가지 않는다 —
그래서 홈 env 에 무엇을 적어도 도는 컨테이너는 **영영 꺼짐**이었다(`docker inspect` 실측 = 0건).
`#20`(접수분 루트)·`#49`(미리보기 자리)와 같은 무늬다: **선언은 코드에, 배선은 배포에.**

오라클은 지어낸 것이 아니라 이 레포가 이미 적어 둔 둘이다.
  ⑴ `kernel/config.py` — 스위치의 이름은 `COLAB_VIZ_TILE_BRANCH` 하나다.
  ⑵ `〈240〉`-㉰ — **기본값은 「한 장」**이다. 레포에 켜진 값을 박지 않는다.
"""
from __future__ import annotations

import re
from pathlib import Path

from colab_viz.kernel.config import TILE_BRANCH_ON_VALUES

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


def test_deployment_carries_the_tile_branch_switch():
    """배포가 스위치를 실어야 홈 env 의 한 줄이 컨테이너에 닿는다."""
    assert _env(_service_block("viz-render"), "COLAB_VIZ_TILE_BRANCH") is not None, (
        "compose 의 viz-render 에 COLAB_VIZ_TILE_BRANCH 가 없다 — "
        "홈 env 에 무엇을 적어도 도는 컨테이너는 영영 꺼짐이다"
    )


def test_the_switch_is_passed_through_from_the_host_env():
    """값을 compose 가 정하지 않는다 — **홈 env 가 정본**이다(`${...}` 치환꼴)."""
    declared = _env(_service_block("viz-render"), "COLAB_VIZ_TILE_BRANCH")
    assert declared is not None
    assert declared.startswith("${COLAB_VIZ_TILE_BRANCH"), (
        f"홈 env 를 통과시키지 않는다: {declared!r}"
    )


def test_the_repo_does_not_ship_the_switch_turned_on():
    """**기본값은 「한 장」**이다(`〈240〉`-㉰). 선언이 없으면 정본 문면대로 나가야 한다."""
    declared = _env(_service_block("viz-render"), "COLAB_VIZ_TILE_BRANCH")
    assert declared is not None
    fallback = declared.partition(":-")[2].rstrip("}").strip().lower()
    assert fallback not in TILE_BRANCH_ON_VALUES, (
        f"레포가 켜진 기본값을 박고 있다: {declared!r}"
    )
