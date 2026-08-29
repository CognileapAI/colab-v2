"""stage 2 스위치가 **코드가 아니라 선언**이라는 것 — 세 상태를 코드가 가른다.

예전에는 `service.process_upload(…, stage1=True)` 가 호출부에 박혀 있었다. 스위치가
코드였으므로 배포 설정으로 열 자리가 없었고, 「켜 두었다」와 「안 켰다」를 실물에서
구분할 방법도 없었다.

세 상태 (`CLAUDE.md §4`):
  · `on` **선언** → 돈다. 이때 산출물 자리(미리보기 루트)가 없으면 **뜨지 않는다.**
  · `off` **명시 면제** → 안 돈다. 그 사실을 한 줄로 **드러낸다.**
  · **무언** → 면제로 세지 않는다. 동작은 `off` 와 같되 「선언되지 않았다」로 드러내고,
    그 상태에서 값이 안 채워지는 것은 유실 감지 게이트가 red 로 받는다.
"""
from __future__ import annotations

import pytest
from colab_pipeline.app import worker


@pytest.mark.stage2
def test_declared_on_runs_stage2():
    on, note = worker.stage2_declaration({worker.ENV_STAGE2: "on"})
    assert on is True
    assert "on" in note


@pytest.mark.stage2
def test_explicit_exemption_surfaces_itself():
    off, note = worker.stage2_declaration({worker.ENV_STAGE2: "off"})
    assert off is False
    assert "면제" in note                      # 건수를 드러낸 채 넘어간다


@pytest.mark.stage2
def test_silence_is_not_counted_as_exemption():
    off, note = worker.stage2_declaration({})
    assert off is False
    assert "미선언" in note and "면제 선언 아님" in note


@pytest.mark.stage2
def test_a_value_outside_the_set_does_not_fall_to_a_lenient_default():
    """`true`·`1` 같은 값을 관대하게 받아 주지 않는다 — 지어내지 않는다."""
    for raw in ("true", "1", "yes", "ON!"):
        with pytest.raises(RuntimeError):
            worker.stage2_declaration({worker.ENV_STAGE2: raw})


@pytest.mark.stage2
def test_stage1_is_no_longer_hardcoded_at_the_call_site():
    """호출부가 인자를 **받는다** — 스위치가 코드에 박혀 있지 않다는 것의 실물 단언."""
    import inspect

    sig = inspect.signature(worker.drive_uploads)
    assert "stage1" in sig.parameters
    assert "previews_root" in sig.parameters
    src = inspect.getsource(worker.drive_uploads)
    assert "stage1=True" not in src, "stage 1 이 호출부에 다시 박혔다"
