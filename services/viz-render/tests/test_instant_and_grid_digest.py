"""`instant` 를 실제로 존중한다 · 격자 digest 를 값으로 잰다.

⭑ ⟨2026-09-03 · 코드리뷰 `CODE-REVIEW-20260903.md` #3⟩ 두 결함이 한 자리에 있었다.

⑴ `_read_netcdf(path, variable, instant, max_side)` 가 `instant` 를 **받기만 하고 본문에서
   한 번도 쓰지 않은 채** `while raw.ndim > 2: raw = raw[0]` 로 늘 첫 시각을 그렸다.
   계약(`core-viz.yaml#RenderRequest.instant`)은 「그릴 시각. **층마다 따로 고른다** …
   생략하면 첫 시각이다」인데, **지정해도 첫 시각**이었다. 게다가 `render_cache_key` 에
   `instant` 가 없어 T1·T2 요청이 **같은 키·같은 PNG** 를 받았다 — 즉 시각을 바꿔도
   그림이 안 바뀌는 것이 캐시로 굳었다.

⑵ `_grid_digest` 가 lat 의 shape · `nanmin(lat)` · `nanmax(lon)` **세 값만** 해시했다.
   그 셋이 같은 다른 격자로 갈아 끼우면 키가 같아지고, `invalidation` 의 `keep_keys` 가
   구 산출물을 「신선」으로 보존한다 — **격자를 바꿨는데 옛 그림이 남는다.**
"""
from __future__ import annotations

import warnings
from contextlib import contextmanager

import numpy as np
import pytest

from colab_viz.domains.d7_visualization import cache, jobs, readers, scale

pytest.importorskip("netCDF4")


@contextmanager
def _quiet_netcdf_write():
    """netCDF4 가 쓰기 경로에서 numpy 2.5 의 `shape` 대입 경고를 낸다 — **라이브러리
    안쪽**이라 이 레인이 고칠 자리가 아니고, 시험 리포트의 잡음만 막는다."""
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning,
                                message=".*[Ss]hape.*")
        yield


# ── 픽스처 — 시각 3개짜리 실제 NetCDF ────────────────────────────────────────
_INSTANTS = ("2026-06-01T00:00:00Z", "2026-06-01T12:00:00Z", "2026-06-02T00:00:00Z")


@pytest.fixture
def nc_3instants(tmp_path):
    """시각마다 **값이 다른** NetCDF. 값이 같으면 시험이 아무것도 못 가른다."""
    from netCDF4 import Dataset

    path = tmp_path / "three.nc"
    ds = Dataset(str(path), "w", format="NETCDF4")
    ds.createDimension("time", 3)
    ds.createDimension("lat", 4)
    ds.createDimension("lon", 5)
    t = ds.createVariable("time", "f8", ("time",))
    t.units = "hours since 2026-06-01 00:00:00"
    t.calendar = "standard"
    t[:] = [0.0, 12.0, 24.0]
    la = ds.createVariable("lat", "f8", ("lat",))
    la[:] = np.linspace(38.0, 36.0, 4)
    lo = ds.createVariable("lon", "f8", ("lon",))
    lo[:] = np.linspace(126.0, 128.0, 5)
    v = ds.createVariable("precip", "f4", ("time", "lat", "lon"))
    v.units = "mm"
    # 시각 k 의 값은 전부 (k+1)*100 이다 — 어느 시각을 그렸는지 값 하나로 갈린다.
    with _quiet_netcdf_write():
        v[:] = np.stack([np.full((4, 5), (k + 1) * 100.0, dtype="f4") for k in range(3)])
    ds.close()
    return path


def _read(path, instant):
    _fmt, field = readers.read_field(path, instant=instant, max_side=64)
    return field


# ── ① `instant` 를 존중한다 ──────────────────────────────────────────────────
def test_생략하면_첫_시각이다(nc_3instants):
    """계약 축자 — 「생략하면 첫 시각이다」. **바꾸지 않는다.**"""
    assert float(np.nanmax(_read(nc_3instants, None).values)) == pytest.approx(100.0)


@pytest.mark.parametrize("index,instant", list(enumerate(_INSTANTS)))
def test_지정한_시각을_실제로_그린다(nc_3instants, index, instant):
    got = float(np.nanmax(_read(nc_3instants, instant).values))
    assert got == pytest.approx((index + 1) * 100.0), \
        f"{instant} 를 달라고 했는데 다른 시각을 그렸다"


def test_없는_시각은_사유와_함께_거절한다(nc_3instants):
    """**지어내지 않는다** — 가장 가까운 시각으로 바꿔 그리면 사용자는 그 사실을 모른다.
    「그럴 값이 없다」(`variable`)와 **같은 자세**이고 같은 예외형이다."""
    with pytest.raises(readers.FieldReadError) as e:
        _read(nc_3instants, "2026-07-01T00:00:00Z")
    assert "2026-07-01T00:00:00Z" in str(e.value), "무엇을 요청했는지가 사유에 없다"
    assert "2026-06-01T12:00:00Z" in str(e.value), "있는 시각이 사유에 없다"


def test_시각_축이_없는_파일에_시각을_지정하면_거절한다(tmp_path):
    """**음성.** 2차원 파일에 `instant` 를 실어 보내면 그것은 요청이 틀린 것이다 —
    조용히 무시하면 「지정했는데 무시됐다」가 다시 생긴다."""
    from netCDF4 import Dataset

    path = tmp_path / "flat.nc"
    ds = Dataset(str(path), "w", format="NETCDF4")
    ds.createDimension("lat", 3)
    ds.createDimension("lon", 3)
    with _quiet_netcdf_write():
        ds.createVariable("v", "f4", ("lat", "lon"))[:] = np.ones((3, 3), dtype="f4")
    ds.close()
    assert _read(path, None).values.shape == (3, 3)
    with pytest.raises(readers.FieldReadError):
        _read(path, "2026-06-01T00:00:00Z")


# ── ② 캐시 키가 시각을 접는다 ────────────────────────────────────────────────
def _key(**kw):
    params = dict(source_digest="deadbeef", long_side=1024, downsample="blockavg",
                  fills=(), palette="단색-파랑", crs=cache.NO_CRS, selection="precip",
                  color_range=scale.ColorRange(vmin=0.0, vmax=1.0,
                                               stage=scale.STAGE_FINAL, scope="dataset",
                                               scope_id="01ARZ3NDEKTSV4RRFFQ69G5FAV"))
    params.update(kw)
    return cache.render_cache_key(**params)


def test_시각이_다르면_키가_다르다():
    """종전에는 24시각 파일의 24개 요청이 **같은 키 하나**를 나눠 썼다."""
    assert _key(instant=_INSTANTS[0]) != _key(instant=_INSTANTS[1])
    assert _key(instant=None) != _key(instant=_INSTANTS[0])
    assert _key(instant=_INSTANTS[1]) == _key(instant=_INSTANTS[1])


def test_렌더_요청의_시각이_키까지_내려간다(client, put_target, source_root, nc_3instants):
    """단위 시험만으로는 **부르는 자리가 안 넘겨 주는 것**을 못 잡는다."""
    from conftest import AUTH

    tid = put_target(copy_from=[nc_3instants])

    def _paths(instant):
        r = client.post("/viz/v1/renders", headers=AUTH, json={
            "target": {"datasetId": tid}, "instant": instant,
            "style": {"palette": "단색-파랑"}})
        assert r.status_code == 202, r.text
        job = client.app.state.jobs.get(r.json()["renderId"])
        assert job.status == "완료", job.failure
        return {a.path.name for a in job.artifacts.all()}

    first, second = _paths(_INSTANTS[0]), _paths(_INSTANTS[1])
    assert first and not (first & second), \
        "시각이 다른 두 렌더가 같은 파일을 나눠 썼다"


# ── ③ 격자 digest 가 값을 본다 ───────────────────────────────────────────────
class _FakeRead:
    """`_grid_digest` 가 보는 것만 흉내 낸다 — `from_uploaded_grid` 와 `reference`."""

    def __init__(self, lat, lon):
        self.from_uploaded_grid = True
        self.reference = (np.asarray(lat, dtype="f8"), np.asarray(lon, dtype="f8"))


def test_세_통계가_같아도_값이_다르면_digest_가_다르다():
    """**종전 결함의 오라클** — shape · `nanmin(lat)` · `nanmax(lon)` 셋을 그대로 두고
    나머지 값만 갈아 끼운다. 종전 구현은 여기서 **같은 문자열**을 냈다."""
    lat_a = np.array([[36.0, 37.0], [38.0, 39.0]])
    lat_b = np.array([[36.0, 37.5], [38.5, 39.5]])          # nanmin·shape 동일
    lon_a = np.array([[126.0, 127.0], [128.0, 129.0]])
    lon_b = np.array([[126.5, 127.5], [128.5, 129.0]])       # nanmax·shape 동일

    assert lat_a.shape == lat_b.shape
    assert np.nanmin(lat_a) == np.nanmin(lat_b)
    assert np.nanmax(lon_a) == np.nanmax(lon_b)
    assert jobs._grid_digest([_FakeRead(lat_a, lon_a)]) \
        != jobs._grid_digest([_FakeRead(lat_b, lon_b)])


def test_같은_격자는_같은_digest_다():
    """**결정적이어야 한다** — 아니면 갈지도 않은 격자가 매번 무효화된다."""
    lat = np.linspace(36.0, 38.0, 40).reshape(8, 5)
    lon = np.linspace(126.0, 128.0, 40).reshape(8, 5)
    assert jobs._grid_digest([_FakeRead(lat, lon)]) \
        == jobs._grid_digest([_FakeRead(lat.copy(), lon.copy())])


def test_NaN_이_섞여도_결정적이다():
    """결측이 든 격자에서도 같은 값이 나와야 한다 — NaN 의 비트 표현에 기대지 않는다."""
    lat = np.array([[36.0, np.nan], [38.0, 39.0]])
    lon = np.array([[126.0, 127.0], [np.nan, 129.0]])
    assert jobs._grid_digest([_FakeRead(lat, lon)]) \
        == jobs._grid_digest([_FakeRead(lat.copy(), lon.copy())])


def test_작은_격자는_한_점만_바뀌어도_digest_가_바뀐다():
    """작은 격자는 **전량**을 해시한다 — 표본의 틈이 없다.

    ⚠ 건드리는 자리는 **최솟값도 최댓값도 아닌 안쪽 한 점**이다. 종전 구현이 보던 세
    통계(shape·`nanmin(lat)`·`nanmax(lon)`)는 그대로 두고 값만 갈린다.
    """
    lat = np.linspace(36.0, 38.0, 4096).reshape(64, 64)
    lon = np.linspace(126.0, 128.0, 4096).reshape(64, 64)
    changed = lat.copy()
    changed[13, 27] += 1e-6
    assert lat.size <= jobs._DIGEST_FULL_MAX_ELEMENTS, "전량 해시 구간이 아니다"
    assert np.nanmin(changed) == np.nanmin(lat) and np.nanmax(lon) == np.nanmax(lon)
    assert jobs._grid_digest([_FakeRead(lat, lon)]) \
        != jobs._grid_digest([_FakeRead(changed, lon)])


def test_큰_격자는_한_줄만_갈려도_digest_가_바뀐다():
    """전량 해시 구간을 넘어서면 **균등 보폭 표본**이다 — 격자 교체는 값이 줄 단위로
    갈리므로 표본에 반드시 걸린다.

    ⚠ **한계를 적어 둔다** — 표본 구간에서 「표본에 안 걸린 한 점」은 잡지 못한다.
    이것은 검사합(checksum)이 아니라 digest 이고, 막으려는 것은 **격자 교체가 같은 키를
    내는 것**이다. 종전 세 통계는 격자를 통째로 갈아도 같은 키를 냈다.
    """
    n = jobs._DIGEST_FULL_MAX_ELEMENTS * 4
    side = int(np.sqrt(n))
    lat = np.linspace(36.0, 38.0, side * side).reshape(side, side)
    lon = np.linspace(126.0, 128.0, side * side).reshape(side, side)
    assert lat.size > jobs._DIGEST_FULL_MAX_ELEMENTS, "표본 구간이 아니다"
    changed = lat.copy()
    changed[side // 2, :] += 1e-3
    assert np.nanmin(changed) == np.nanmin(lat), "세 통계 중 lat 최솟값이 갈렸다"
    assert jobs._grid_digest([_FakeRead(lat, lon)]) \
        != jobs._grid_digest([_FakeRead(changed, lon)])


def test_붙인_격자가_없으면_digest_도_없다():
    """**음성 · 「지도형만 무효화」의 절반.** 파일이 스스로 좌표를 아는 자료형은
    격자 해시를 갖지 않는다 — 지어내면 격자와 무관한 재굽기가 생긴다."""
    class _Own:
        from_uploaded_grid = False
        reference = None

    assert jobs._grid_digest([_Own()]) is None
