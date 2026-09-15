import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("dev_seed_runner_preview", ROOT / "runner.py")
runner = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(runner)


def test_done_slot_requires_a_decoded_main_image():
    assert runner.classify_preview_measurement("done", 1, 0, 0) == (
        "안 그려짐", "완료 슬롯의 주 이미지가 아직 decode되지 않음")
    assert runner.classify_preview_measurement("done", 1, 1, 0) == ("그려짐", "")


def test_failed_and_empty_states_are_not_reported_as_rendered():
    assert runner.classify_preview_measurement("failed", 0, 0, 1) == (
        "안 그려짐", "미리보기 실패")
    assert runner.classify_preview_measurement("idle", 0, 0, 0) == (
        "미확인", "terminal 상태에 도달하지 않음")
