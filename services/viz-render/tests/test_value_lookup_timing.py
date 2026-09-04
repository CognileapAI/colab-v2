"""값 조회의 **서버 단독 처리 시간**을 응답이 스스로 말한다 (`VL-1` · `PLAN-SoT §9 〈310〉`).

왜 이 파일이 있는가
  `〈304〉` 는 공개 엣지 앞에서 벽시계 하나로만 쟀고, 그 값에는 **Cloudflare ＋ nginx 가
  섞여 있다** — 그래서 **서버 단독 p95 가 `[미확인]`** 으로 남았다(축자: 「`Server-Timing`
  에 처리 구간이 없어 가를 재료가 없다」). `VL-1` ⑴ 은 「측정 방법을 함께 적는다」를
  요구하고 그 방법으로 **`Server-Timing` 에 처리 구간을 싣는 것**을 먼저 이름했다.

⚠ **계약 표면이 아니다** — 몸통(`core-viz.yaml#ValueLookupResult`)은 한 글자도 늘지
  않는다. `Server-Timing` 은 표준 응답 헤더이고(RFC 8942 계열 · W3C Server Timing),
  계약이 정한 모양 밖의 **관측 자리**다. `/healthz` 의 `tileBranch` 와 같은 선이다.
"""
from __future__ import annotations

import re

from colab_viz.domains.d7_visualization import value_lookup

from conftest import AUTH
from test_value_lookup import _bake_tile, _file_id, _spiky_geotiff, _LAT, _LON

#: `Server-Timing` 한 구간 = `이름;dur=밀리초`.
_SPAN = re.compile(r"(?P<name>[A-Za-z0-9_]+);dur=(?P<ms>[0-9.]+)")


def _spans(res) -> dict[str, float]:
    header = res.headers.get("Server-Timing")
    assert header, "값 조회 응답에 Server-Timing 이 없다 — 서버 단독 시간을 가를 재료가 없다."
    return {m.group("name"): float(m.group("ms")) for m in _SPAN.finditer(header)}


def _lookup(client, source_root, put_target, tmp_path):
    from colab_viz.kernel import storage_layout

    src = _spiky_geotiff(tmp_path)
    tid = put_target(copy_from=[src])
    body = storage_layout.target_dir(source_root, tid) / src.name
    _bake_tile(client.app.state.settings.preview_dir, body)
    return client.post("/viz/v1/value-lookups", headers=AUTH, json={
        "datasetId": tid, "fileId": _file_id(client, tid, body.name),
        "point": {"lat": _LAT, "lon": _LON}})


def test_응답이_처리_구간을_밀리초로_말한다(client, source_root, put_target, tmp_path):
    """`〈304〉` 의 `[미확인]`(서버 단독 p95)을 푸는 재료가 응답에 실린다."""
    res = _lookup(client, source_root, put_target, tmp_path)
    assert res.status_code == 200, res.text
    spans = _spans(res)
    # **네 구간을 이름으로 가른다** — 「느리다」가 아니라 「어디가 느리다」를 답해야 한다.
    for name in ("vizResolve", "vizFindTile", "vizReadPoint", "vizTotal"):
        assert name in spans, f"{name} 구간이 없다: {spans}"
        assert spans[name] >= 0.0


def test_총합은_부분들보다_작지_않다(client, source_root, put_target, tmp_path):
    """구간이 총합을 넘으면 계측이 거짓이다 — 그 표를 근거로 쓸 수 없다."""
    spans = _spans(_lookup(client, source_root, put_target, tmp_path))
    parts = spans["vizResolve"] + spans["vizFindTile"] + spans["vizReadPoint"]
    assert spans["vizTotal"] + 1e-6 >= parts


def test_자리에_산출물이_없어도_구간이_실린다(client, source_root, put_target, tiny_geotiff):
    """**가장 느렸던 표본이 「없다」쪽이었다**(`〈304〉` DEM p95 2,111 ms) — 그 경로에
    계측이 없으면 원인을 영영 못 가른다. 읽기 구간은 0 이고 그것이 사실이다."""
    tid = put_target(copy_from=[tiny_geotiff])
    res = client.post("/viz/v1/value-lookups", headers=AUTH, json={
        "datasetId": tid, "fileId": _file_id(client, tid, tiny_geotiff.name),
        "point": {"lat": _LAT, "lon": _LON}})
    assert res.status_code == 200
    assert res.json()["available"] is False
    spans = _spans(res)
    assert spans["vizReadPoint"] == 0.0
    assert spans["vizFindTile"] >= 0.0


def test_lookup_timed_는_lookup_과_같은_답을_낸다(tmp_path):
    """계측이 **답을 바꾸지 않는다** — 바꾸면 계측이 기능이 된다."""
    src = _spiky_geotiff(tmp_path)
    root = tmp_path / "previews"
    plain = value_lookup.lookup(root, src, grid_dir=None, lat=_LAT, lon=_LON)
    timed, spans = value_lookup.lookup_timed(root, src, grid_dir=None, lat=_LAT, lon=_LON)
    assert timed == plain
    assert set(spans) == {"findTile", "readPoint"}
