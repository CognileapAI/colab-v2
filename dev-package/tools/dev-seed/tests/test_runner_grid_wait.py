"""「격자 판정」 대기 — 전체 파일 렌더가 끝내 실패하는 대용량 대상(dev 4회차 seq 18).

화면 사실(배포 트리 ea21d8c2aa54):
- 서버가 격자 쌍을 받아들이면 grid-options 의 currentGrid 로 「예상 영역」
  (`up-grid-expected-bounds`)이 선다 — `status.ready` 에만 의존한다.
- 「맞습니다」(`up-grid-accept`)는 전체 파일 렌더가 성공해야만 선다. 렌더가
  RENDER_TIMEOUT 으로 실패하면 `up-preview-error` 만 남고 판정 표시는 끝내 오지 않는다.
"""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("dev_seed_runner_grid", ROOT / "runner.py")
runner = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(runner)


class Clock:
    def __init__(self):
        self.t = 0.0

    def time(self):
        return self.t

    def sleep(self, s):
        self.t += s


def tid(name):
    return '[data-testid="' + name + '"]'


def install(monkeypatch, timeline):
    """timeline = [(시각 s, 그때부터 보이는 testid 집합)] — 마지막으로 지난 행이 화면이다."""
    clock = Clock()
    clicks = []
    monkeypatch.setattr(runner, "CFG", SimpleNamespace(dry_run=False))
    monkeypatch.setattr(runner, "time", clock)
    monkeypatch.setattr(runner, "save_state", lambda st: None)
    monkeypatch.setattr(runner, "log", lambda *a, **k: None)
    monkeypatch.setattr(runner, "ab", lambda args, **k: (0, {}, ""))
    monkeypatch.setattr(runner, "dump_failure", lambda tag, reason: None)
    monkeypatch.setattr(runner, "spot", lambda st, key, cands, **k: clicks.append(key))

    def visible():
        shown = set()
        for at, names in timeline:
            if clock.t >= at:
                shown = names
        return shown

    def count(css):
        shown = visible()
        return sum(1 for part in css.split(",") if part.strip() in {tid(n) for n in shown})

    monkeypatch.setattr(runner, "count", count)
    return clock, clicks


def seq18(preview_expected="미판정 대상"):
    return {
        "seq": 18,
        "file_count": 143,
        "grid_files": ["/ref/lat2d.npy", "/ref/lon2d.npy"],
        "grid_bytes": 6480256,
        "preview_expected": preview_expected,
    }


# 격자 올리기 전(좌표 없음) → 올린 뒤 서버 격자 수용 → 렌더 실패. 판정 표시는 오지 않는다.
STALL = [
    (0, {"up-grid-block", "up-grid-input"}),
    (1, {"up-grid-block"}),
    (20, {"up-grid-block", "up-grid-expected-bounds", "up-preview-stage"}),
    (160, {"up-grid-block", "up-grid-expected-bounds", "up-preview-error"}),
]


def test_render_failure_after_grid_acceptance_registers_without_preview(monkeypatch):
    clock, clicks = install(monkeypatch, STALL)
    st = dict()

    reason = runner.do_grid(st, seq18())

    assert reason and "렌더" in reason
    assert st["grid_render_unverified"] == [18]
    assert "grid-accept" not in clicks
    # 렌더 실패가 보인 뒤 곧 나아간다 — 846 s 상한까지 기다리지 않는다.
    assert clock.t < 200


def test_render_never_resolves_is_bounded_for_tolerant_rows(monkeypatch):
    timeline = [
        (0, {"up-grid-block", "up-grid-input"}),
        (5, {"up-grid-block", "up-grid-expected-bounds", "up-preview-stage"}),
    ]
    clock, _ = install(monkeypatch, timeline)
    st = dict()

    reason = runner.do_grid(st, seq18())

    assert reason
    assert st["grid_render_unverified"] == [18]
    assert clock.t <= 5 + runner.GRID_RENDER_WAIT_S + 2


def test_rows_that_require_a_preview_stay_strict(monkeypatch):
    install(monkeypatch, STALL)

    with pytest.raises(runner.Fail):
        runner.do_grid(dict(), seq18("렌더 성립(3패스 중 1회)"))


def test_render_verdict_still_wins_when_it_arrives(monkeypatch):
    timeline = [
        (0, {"up-grid-block", "up-grid-input"}),
        (5, {"up-grid-block", "up-grid-expected-bounds", "up-preview-stage"}),
        (90, {"up-grid-block", "up-grid-expected-bounds", "up-grid-accept"}),
    ]
    _, clicks = install(monkeypatch, timeline)
    st = dict()

    assert runner.do_grid(st, seq18()) is None
    assert clicks == ["grid-accept"]
    assert "grid_render_unverified" not in st


def test_mismatch_is_never_waved_through(monkeypatch):
    timeline = [
        (0, {"up-grid-block", "up-grid-input"}),
        (5, {"up-grid-block", "up-grid-expected-bounds", "up-grid-mismatch", "up-preview-error"}),
    ]
    install(monkeypatch, timeline)

    with pytest.raises(runner.Fail):
        runner.do_grid(dict(), seq18())


def test_grid_not_accepted_by_server_still_fails(monkeypatch):
    timeline = [
        (0, {"up-grid-block", "up-grid-input"}),
        (5, {"up-grid-block", "up-preview-error"}),
    ]
    install(monkeypatch, timeline)

    with pytest.raises(runner.Fail):
        runner.do_grid(dict(), seq18())
