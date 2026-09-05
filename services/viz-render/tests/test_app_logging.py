"""앱 로그 설정 — **관측 전용의 관측이 되게 한다** (`BF-12` · `PLAN-SoT §9 〈324〉`).

`services/viz-render/src` 전수에 `basicConfig`·`dictConfig`·`setLevel` 이 **0건**이었다.
루트 로거에 처리기가 없으면 `logging.lastResort` 가 **WARNING 이상만** stderr 로 흘리고,
uvicorn 기본 설정은 `uvicorn.*` 로거만 건드린다 ⟹ `colab_viz.*` 의 INFO 는 **버려진다.**
그래서 회수 루프가 실제로 돌아도 `docker logs` 에는 한 줄도 안 나왔다(staging 실측 98분).

**이 파일이 잠그는 것 넷** —
  ⑴ 앱을 세우면 `colab_viz.*` 의 INFO 가 **stdout** 으로 나온다
  ⑵ **형제 자리** — 회수 요약(`지도 타일 회수 …`)과 트리거 집행 줄(`트리거 집행 N건`)이
     **둘 다** 나온다. 하나만 고치면 절반만 고친 것이다(`〈324〉`-㉰)
  ⑶ **멱등** — 앱을 여러 번 세워도 처리기가 겹치지 않는다(시험이 앱을 수십 번 만든다)
  ⑷ **비밀을 싣지 않는다** — 서비스 토큰·타일 서명 비밀이 로그 어디에도 안 나온다

⚠ **`caplog` 를 쓰지 않는다.** pytest 는 자기 처리기를 루트에 달아 두므로 caplog 로 재면
  「로그 설정이 없어도 잡힌다」가 되고, 그것이 바로 이 결함이 시험을 통과했던 이유다.
  여기서는 루트를 **미설정 상태로 되돌린 뒤** 진짜 stdout 을 잡는다.
"""
from __future__ import annotations

import contextlib
import io
import logging
from pathlib import Path

import pytest

from colab_viz.app.main import create_app
from colab_viz.kernel.config import Settings

TOKEN = "bf12-service-token-비밀"
SECRET = "bf12-tile-signing-secret-비밀"


@pytest.fixture()
def 미설정_루트():
    """**로깅이 아무것도 안 된 상태**를 만든다 — 컨테이너의 실제 출발점이다."""
    root = logging.getLogger()
    saved_handlers, saved_level = root.handlers[:], root.level
    colab = logging.getLogger("colab_viz")
    saved_colab, saved_colab_level = colab.handlers[:], colab.level
    root.handlers = []
    root.setLevel(logging.WARNING)
    colab.handlers = []
    colab.setLevel(logging.NOTSET)
    try:
        yield
    finally:
        root.handlers, colab.handlers = saved_handlers, saved_colab
        root.setLevel(saved_level)
        colab.setLevel(saved_colab_level)


def _settings(tmp_path: Path) -> Settings:
    return Settings(source_root=tmp_path / "sources", service_token=TOKEN,
                    tile_signing_secret=SECRET, execution="inline",
                    preview_dir=tmp_path / "previews")


@contextlib.contextmanager
def _stdout():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        yield buf


def test_앱을_세우면_INFO_가_stdout_으로_나온다(미설정_루트, tmp_path):
    with _stdout() as out:
        create_app(_settings(tmp_path))
        logging.getLogger("colab_viz.trigger_loop").info("관측 한 줄")
    assert "관측 한 줄" in out.getvalue()


def test_회수_요약과_트리거_집행_줄이_둘_다_나온다(미설정_루트, tmp_path):
    """**형제 자리** — 회수만 나오고 집행이 안 나오면 절반만 고친 것이다(`〈324〉`-㉰)."""
    from colab_viz.app import trigger_loop

    class 한_건_버스:
        def __init__(self):
            self.acked = []

        def poll(self):
            return []

        def ack(self, event):      # pragma: no cover - 이 시험은 봉투를 안 만든다
            self.acked.append(event)

    class 요약을_내는_회수:
        def run_due(self, now=None):
            class _R:
                def summary(self):
                    return ("지도 타일 회수 — 주체 3 · 자리의 타일 2벌 · 닿는다 2 · "
                            "못 닿는다 0 · 상한 20 · 관측 전용(0건 지웠다) 0파일")
            return _R()

    with _stdout() as out:
        create_app(_settings(tmp_path))
        loop = trigger_loop.TriggerDrainLoop(한_건_버스(), jobs=None, source=None,
                                             interval_seconds=1.0,
                                             reclaim=요약을_내는_회수())
        loop.tick()
        # 집행 줄은 `drain` 의 결과가 있을 때만 난다 — 로거를 같은 이름으로 직접 부른다.
        trigger_loop.log.info("트리거 집행 %d건 — 미리보기를 다시 만들었다", 1)
    text = out.getvalue()
    assert "지도 타일 회수 — 주체 3" in text, "회수 요약이 stdout 에 없다"
    assert "트리거 집행 1건" in text, "트리거 집행 줄이 stdout 에 없다"


def test_앱을_두_번_세워도_줄이_겹치지_않는다(미설정_루트, tmp_path):
    with _stdout() as out:
        create_app(_settings(tmp_path))
        create_app(_settings(tmp_path))
        create_app(_settings(tmp_path))
        logging.getLogger("colab_viz.trigger_loop").info("한 번만")
    assert out.getvalue().count("한 번만") == 1


def test_로그에_비밀값이_실리지_않는다(미설정_루트, tmp_path):
    """⑷ **비밀값 미출력** — 요약 줄에도, 기동 줄에도 토큰·서명 비밀이 없다."""
    from colab_viz.app import trigger_loop

    class 빈_버스:
        def poll(self):
            return []

    class 요약을_내는_회수:
        def run_due(self, now=None):
            class _R:
                def summary(self):
                    return "지도 타일 회수 — 주체 0 · 자리의 타일 0벌"
            return _R()

    with _stdout() as out:
        create_app(_settings(tmp_path))
        loop = trigger_loop.TriggerDrainLoop(빈_버스(), jobs=None, source=None,
                                             interval_seconds=1.0,
                                             reclaim=요약을_내는_회수())
        loop.tick()
    text = out.getvalue()
    assert "지도 타일 회수" in text
    for 비밀 in (TOKEN, SECRET):
        assert 비밀 not in text
