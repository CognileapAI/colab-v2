import importlib.util
from pathlib import Path
import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("dev_seed_runner_preview", ROOT / "runner.py")
runner = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(runner)


def test_done_slot_requires_a_decoded_main_image():
    assert runner.classify_preview_measurement("done", 1, 0, 0, "") == (
        "안 그려짐", "완료 슬롯의 주 이미지가 아직 decode되지 않음")
    assert runner.classify_preview_measurement("done", 2, 1, 0, "총 120ms") == (
        "안 그려짐", "완료 슬롯의 표시 이미지가 모두 decode되지 않음")
    assert runner.classify_preview_measurement("done", 2, 2, 0, "") == (
        "안 그려짐", "화면 표시 시간 관측이 끝나지 않음")
    assert runner.classify_preview_measurement("done", 2, 2, 0, "총 120ms") == ("그려짐", "")


def test_failed_and_empty_states_are_not_reported_as_rendered():
    assert runner.classify_preview_measurement("failed", 0, 0, 1, "") == (
        "안 그려짐", "미리보기 실패")
    assert runner.classify_preview_measurement("idle", 0, 0, 0, "") == (
        "미확인", "terminal 상태에 도달하지 않음")


def test_preview_request_selects_one_file_before_explicit_draw(monkeypatch):
    commands = []
    monkeypatch.setattr(runner, "js", lambda *_args, **_kwargs: {"fileId": "FILE-2", "drawEnabled": True})
    monkeypatch.setattr(
        runner,
        "ab",
        lambda args, **_kwargs: commands.append(args) or (0, {}, ""),
    )

    assert runner.request_selected_preview() == "FILE-2"
    assert commands == [
        ["select", '[data-testid="dt-pick-file"]', "FILE-2"],
        ["click", '[data-testid="dt-preview-draw"]'],
    ]


def test_preview_request_waits_until_file_and_draw_button_are_ready(monkeypatch):
    states = iter([
        {"fileId": "", "drawEnabled": False},
        {"fileId": "FILE-3", "drawEnabled": True},
        {"fileId": "FILE-3", "drawEnabled": True},
    ])
    commands = []
    monkeypatch.setattr(runner, "js", lambda *_args, **_kwargs: next(states))
    monkeypatch.setattr(runner, "time", type("Clock", (), {"time": staticmethod(iter([0, 0.1, 0.2]).__next__), "sleep": staticmethod(lambda _: None)}))
    monkeypatch.setattr(runner, "ab", lambda args, **_kwargs: commands.append(args) or (0, {}, ""))

    assert runner.request_selected_preview() == "FILE-3"
    assert commands[0] == ["select", '[data-testid="dt-pick-file"]', "FILE-3"]


def test_preview_timeout_aborts_before_another_create():
    with pytest.raises(runner.Fail, match="후속 요청을 중단"):
        runner.require_preview_outcome(None)
