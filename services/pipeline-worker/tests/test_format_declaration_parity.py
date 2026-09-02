"""**선언과 처리가 갈리는 것을 기계가 막는다** — `#58` 의 항구 픽스.

`#58` 의 실체는 「NumPy 를 못 판다」가 아니었다. **선언 여섯 · 처리 넷**이었고,
그 어긋남이 사용자에게는 「지원 목록 밖」이라는 **거짓 정책 문면**으로 나왔다
(`03-HANDOFF §4 #58` · `PLAN-SoT §9 〈271〉-㉯` · `〈267〉` 상신 원문).

파서를 채우는 것만으로는 다시 갈라진다 — **다음에 포맷이 하나 더 선언되면
아무도 모르게 같은 자리가 다시 열린다.** 그래서 이 파일이 네 자리를 못 박는다.

  ① `d5/parse.py` 의 분기 표  == `formats.SUPPORTED_FORMATS`      (선언 ⊆ 처리)
  ② `d5/pipeline.py` 의 COG 표 == `renderable.RENDERABLE_FORMATS`  (그릴 것 ⊆ 구울 것)
  ③ `viz-render` 의 `readers.SUPPORTED_FORMATS` == `RENDERABLE_FORMATS`
  ④ 게이트 정본 `gates/config/e2e-format-coverage.toml` 의
     `[required] ∪ [면제]` == `RENDERABLE_FORMATS`

**세지 않는다 — 목록으로 읽는다**(`〈51〉`·`〈77〉`·`〈134〉`). 수를 단언하면
구성이 바뀌어도 초록이다. 여기서 이미 한 번 그렇게 틀렸다.
"""
from __future__ import annotations

import re
import tomllib

import pytest

from colab_pipeline.d5 import parse, pipeline
from colab_pipeline.d5.detect import DetectionResult
from colab_pipeline.d5.formats import SUPPORTED_FORMATS
from colab_pipeline.d5.renderable import RENDERABLE_FORMATS

pytestmark = pytest.mark.stage2


# ═════════ ① 선언 ⊆ 처리 — `#58` 이 난 자리 ═════════
def test_every_declared_format_has_a_parser():
    """**선언이 처리를 앞지르면 red.** `#58` 은 정확히 이 상태였다(여섯 대 넷)."""
    missing = [f for f in SUPPORTED_FORMATS if f not in parse.PARSERS]
    assert missing == [], (
        f"선언은 하는데 파서가 없다: {missing}. "
        "선언을 줄이지 말고 파서를 채운다(〈271〉-㉯ — 채우는 쪽으로 정했다).")


def test_no_parser_for_an_undeclared_format():
    """반대 방향도 막는다 — 선언에 없는 것을 처리하면 목록이 거짓이 된다."""
    extra = [f for f in parse.PARSERS if f not in SUPPORTED_FORMATS]
    assert extra == [], f"선언에 없는데 파서가 있다: {extra}"


def test_undeclared_format_still_says_out_of_list(tmp_path):
    """**음성** — 진짜 목록 밖(순수 HDF5)에서는 그 문면이 여전히 옳다."""
    f = tmp_path / "x"
    f.write_bytes(b"\x00" * 8)
    det = DetectionResult("HDF5", None, None, False, "")
    with pytest.raises(parse.ParseError, match="지원 목록 밖"):
        parse.parse_metadata(f, det)


def test_a_declared_but_unhandled_format_is_never_called_out_of_list(tmp_path, monkeypatch):
    """**`#58` 의 거짓 문면을 못 박는다.**

    선언돼 있는데 파서가 없는 상태를 인위로 만들면, 메시지는 **「목록 밖」이
    아니라 「구현」**이라고 말해야 한다. 이 둘을 뒤바꿔 말한 것이 `#58` 이고,
    읽는 사람이 구현 결함을 정책으로 착각하게 만든 자리다.
    """
    monkeypatch.setattr(parse, "SUPPORTED_FORMATS", SUPPORTED_FORMATS + ["새포맷"])
    f = tmp_path / "x"
    f.write_bytes(b"\x00" * 8)
    det = DetectionResult("새포맷", None, None, False, "")
    with pytest.raises(parse.ParseError) as ei:
        parse.parse_metadata(f, det)
    assert "지원 목록 밖" not in str(ei.value)
    assert "구현" in str(ei.value)


# ═════════ ② 그릴 것 ⊆ 구울 것 ═════════
def test_every_renderable_format_has_a_cog_builder():
    missing = [f for f in RENDERABLE_FORMATS if f not in pipeline.COG_BUILDERS]
    assert missing == [], f"그릴 수 있다고 선언했는데 COG 경로가 없다: {missing}"


def test_not_renderable_formats_have_no_cog_builder():
    extra = [f for f in pipeline.COG_BUILDERS if f not in RENDERABLE_FORMATS]
    assert extra == [], f"그릴 수 없는데 COG 경로가 있다: {extra}"


# ═════════ ③ 두 서비스의 목록 ═════════
def test_viz_render_list_equals_renderable_formats(repo_root):
    """**두 곳에 적혀 있는 목록이 갈리는 것을 기계가 본다.**

    `readers.py` 주석 축자 — 「맞춰야 할 상대는 `SUPPORTED_FORMATS` 가 아니라
    **`RENDERABLE_FORMATS`** 다」. 주석은 지키지 못한다 — 시험이 지킨다.
    """
    src = (repo_root / "services" / "viz-render" / "src" / "colab_viz" / "domains"
           / "d7_visualization" / "readers.py").read_text("utf-8")
    m = re.search(r"^SUPPORTED_FORMATS: list\[str\] = \[(.*?)\]", src, re.M | re.S)
    assert m, "readers.py 의 SUPPORTED_FORMATS 선언을 찾지 못했다"
    theirs = re.findall(r'"([^"]+)"', m.group(1))
    assert theirs == RENDERABLE_FORMATS, (
        f"viz-render={theirs} · pipeline-worker RENDERABLE={RENDERABLE_FORMATS}")


# ═════════ ④ 게이트 정본 ═════════
def test_gate_canon_covers_exactly_the_renderable_formats(repo_root):
    """`e2e-format-coverage.toml` 은 **그릴 수 있는 목록**을 따른다 — 지원 목록이 아니다.

    GRIB 은 지원하되 그릴 수 없으므로(`〈134〉` 결정 2-3) 실데이터 렌더 커버리지의
    대상이 아니다. **`#58` 이 파서를 여섯으로 채워도 이 정본은 다섯 그대로다** —
    그 사실을 기계가 지킨다(다음 회차가 「여섯으로 맞춰야 하나」를 다시 묻지 않게).
    """
    cfg = tomllib.loads(
        (repo_root / "gates" / "config" / "e2e-format-coverage.toml").read_text("utf-8"))
    declared = cfg["required"]["formats"] + cfg["면제"]["formats"]
    assert sorted(declared) == sorted(RENDERABLE_FORMATS), (
        f"게이트 정본={sorted(declared)} · RENDERABLE={sorted(RENDERABLE_FORMATS)}")
