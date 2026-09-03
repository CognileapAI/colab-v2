"""자료 블록이 하나도 없는 HSR 은 **판독 실패다** (코드리뷰 20260903 #13).

`parse_hsr` 이 0 블록을 정상 반환하고 있어, 소비자가 그 사실을 각자 확인해야 했다.
확인하지 않는 소비자가 실제로 있었다 — `pipeline._cog_binary` 의 `hsr.blocks[0]` 이
`IndexError` 로 터진다. 쌍둥이인 D7 `d7_visualization/hsr.py` 는 같은 자리에서
`HsrParseError("자료 블록이 하나도 없다")` 를 낸다. **거절 기준을 맞춘다.**

⚠ 헤더가 `num_data` 를 3 이라 말하고 실물이 1 블록인 것은 **정상**이다(배포본 축소,
`block_count_mismatch` 로 기록한다). 여기서 막는 것은 **0 블록**뿐이다.
"""
from __future__ import annotations

import pytest

from colab_pipeline.d5.hsr import HsrParseError, parse_hsr
from colab_pipeline.d5.pipeline import run_file

from fixture_builders import make_hsr_bin_gz

pytestmark = pytest.mark.stage2


def test_헤더만_있는_HSR_은_판독_실패다(tmp_path):
    p = make_hsr_bin_gz(tmp_path / "hsr0.bin.gz", blocks=[], declared_num_data=3)
    with pytest.raises(HsrParseError):
        parse_hsr(p)


def test_블록_수_불일치는_여전히_정상이다(tmp_path):
    """회귀 방지 — 「선언 3 · 실물 1」은 실측된 배포본 무늬이고 실패가 아니다."""
    p = make_hsr_bin_gz(tmp_path / "hsr1.bin.gz", blocks=[[100] * 48], declared_num_data=3)
    r = parse_hsr(p)
    assert r.blocks_present == 1 and r.block_count_mismatch is True


def test_0블록_HSR_은_IndexError_가_아니라_분류된_실패로_끝난다(tmp_path):
    """`run_file` 은 실패를 **문구로** 남기고, `d5_ingestion._classify_failure` 가
    그 문구를 계약의 사유로 옮긴다. 날것 `IndexError` 는 그 표를 통과하지 못한다."""
    p = make_hsr_bin_gz(tmp_path / "hsr_run.bin.gz", blocks=[], declared_num_data=3)
    res = run_file(p, workdir=tmp_path / "work", grid_dir=None)
    assert res.status == "FAILURE"
    assert any(m.startswith("파싱 실패") for m in res.failures), (
        f"분류표가 읽을 수 있는 문구가 아니다: {res.failures}")
