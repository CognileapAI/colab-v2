"""공통 스케일 2단계와 캐시 키 — `S1-PLAN-REFOUND §D.4-⑶` · `PREVIEW-IMPLEMENTATION §6.2·§7.2`.

**게이트 ① 이 짚은 구멍이 여기다.** 「등록 확정 뒤 1회 산출」과 「범위가 없으면 안 그린다」를
겹치면 **0번째 업로드의 미리보기가 영원히 안 나온다.** 그래서 범위를 두 단계로 두고,
**둘을 캐시 키로 구분하고, 산출물이 어느 쪽인지 라벨로 말한다.**

⚠ **파일이 1장이면 잠정 범위는 프레임별 스트레치와 수학적으로 같다.** 금지(`§10-7`)와
갈리는 근거는 셋뿐이다 — ⓐ 출고되지 않는다(업로드 범위 전용) ⓑ 라벨이 붙는다
ⓒ 등록 시 반드시 다시 잡힌다. **이 파일이 그 셋을 각각 시험한다.**
"""
from __future__ import annotations

import numpy as np
import pytest

from colab_viz.domains.d7_visualization import cache, scale


def _ramp(lo: float, hi: float, n: int = 1000) -> np.ndarray:
    return np.linspace(lo, hi, n, dtype="f4").reshape(-1, 1)


# ── 범위 산출 ────────────────────────────────────────────────────────────────
def test_공통_범위는_2_98_백분위이고_바깥_2퍼센트를_버린다():
    arr = _ramp(0.0, 100.0)
    lo, hi = scale.percentile_range([arr])
    assert 1.5 <= lo <= 2.5 and 97.5 <= hi <= 98.5


def test_범위는_512px_축약본에서_잡는다():
    """전 해상도로 재지 마라(`§6.2` 산출 비용 행) — 축약 뒤 형상이 상한 아래여야 한다."""
    big = np.random.default_rng(0).normal(size=(2000, 2000)).astype("f4")
    seen = scale.sample_for_range(big)
    assert max(seen.shape) <= scale.SAMPLE_SIDE


def test_결측만_있는_집합은_범위를_지어내지_않는다():
    with pytest.raises(scale.RangeUnavailableError):
        scale.percentile_range([np.full((4, 4), np.nan, dtype="f4")])


def test_여러_파일을_함께_보면_한_장만_볼_때와_다른_범위가_나온다():
    a, b = _ramp(0.0, 10.0), _ramp(0.0, 1000.0)
    one = scale.for_upload("01ARZ3NDEKTSV4RRFFQ69G5FAV", [a])
    both = scale.for_dataset("01ARZ3NDEKTSV4RRFFQ69G5FAW", [a, b])
    assert both.vmax > one.vmax * 10


# ── ⓐ 잠정은 출고되지 않는다 ────────────────────────────────────────────────
def test_잠정_범위는_업로드_범위에서만_만들어진다():
    r = scale.for_upload("01ARZ3NDEKTSV4RRFFQ69G5FAV", [_ramp(0.0, 10.0)])
    assert r.stage == scale.STAGE_PROVISIONAL
    assert scale.for_dataset("01ARZ3NDEKTSV4RRFFQ69G5FAW",
                             [_ramp(0.0, 10.0)]).stage == scale.STAGE_FINAL

    # 데이터셋 산출물에 잠정 라벨을 붙이는 경로가 **없다**
    with pytest.raises(ValueError):
        scale.ColorRange(vmin=0.0, vmax=1.0, stage=scale.STAGE_PROVISIONAL,
                         scope="dataset", scope_id="01ARZ3NDEKTSV4RRFFQ69G5FAW")


# ── ⓑ 라벨 ──────────────────────────────────────────────────────────────────
def test_범위에는_언제나_단계_라벨이_붙는다():
    r = scale.for_upload("01ARZ3NDEKTSV4RRFFQ69G5FAV", [_ramp(0.0, 10.0)])
    assert r.stage in ("잠정", "확정")             # 계약 `ColorRangeStage` enum 그대로
    assert r.token() == "잠정(upload:01ARZ3NDEKTSV4RRFFQ69G5FAV)"


def test_파일이_한_장이면_잠정_범위는_프레임별_스트레치와_같은_수다():
    """**숨기지 않는다.** 같은 수가 나온다는 사실을 시험이 적어 둔다 — 갈리는 것은 수가
    아니라 ⓐ 출고 ⓑ 라벨 ⓒ 재산출 셋이다(`§D.4-⑶ⓑ`)."""
    one = _ramp(0.0, 10.0)
    per_frame = scale.percentile_range([one])
    provisional = scale.for_upload("01ARZ3NDEKTSV4RRFFQ69G5FAV", [one])
    assert (provisional.vmin, provisional.vmax) == per_frame


# ── ⓒ 캐시 키가 승격을 막는다 ───────────────────────────────────────────────
def _key(color_range, **kw):
    params = dict(source_digest="deadbeef", long_side=1024, downsample="blockavg",
                  fills=(-25000.0, -30000.0), palette="단색-파랑", crs="none",
                  selection="블록1", color_range=color_range)
    params.update(kw)
    return cache.render_cache_key(**params)


def test_값이_우연히_같아도_잠정_산출물이_확정으로_승격되지_않는다():
    """**단계 토큰이 없으면 여기서 키가 같아진다** — `§D.4-⑶ⓒ` 가 막으려던 그것이다."""
    same = dict(vmin=0.0, vmax=10.0)
    prov = scale.ColorRange(**same, stage=scale.STAGE_PROVISIONAL,
                            scope="upload", scope_id="01ARZ3NDEKTSV4RRFFQ69G5FAV")
    final = scale.ColorRange(**same, stage=scale.STAGE_FINAL,
                             scope="dataset", scope_id="01ARZ3NDEKTSV4RRFFQ69G5FAW")
    assert (prov.vmin, prov.vmax) == (final.vmin, final.vmax)
    assert _key(prov) != _key(final)


def test_격자_해시는_지도형_키에만_들어간다():
    """격자 교체가 **지도형만** 무효화하고 썸네일·비지도형을 살린다 — 무효화 규칙을
    따로 코딩하지 않는다. **키가 하게 한다**(`§7.2`)."""
    r = scale.for_dataset("01ARZ3NDEKTSV4RRFFQ69G5FAW", [_ramp(0.0, 10.0)])
    detail_a = _key(r, crs="none", grid_digest=None)
    detail_b = _key(r, crs="none", grid_digest="격자해시B")
    map_a = _key(r, crs="EPSG:3857", downsample="warp+blockavg", grid_digest="격자해시A")
    map_b = _key(r, crs="EPSG:3857", downsample="warp+blockavg", grid_digest="격자해시B")
    assert detail_a == detail_b, "비지도형 키는 격자를 물지 않는다"
    assert map_a != map_b, "지도형 키는 격자를 문다"


def test_같은_파라미터는_같은_키다():
    r = scale.for_dataset("01ARZ3NDEKTSV4RRFFQ69G5FAW", [_ramp(0.0, 10.0)])
    assert _key(r) == _key(r)
    assert _key(r, long_side=128, downsample="stride") != _key(r)
