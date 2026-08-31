"""`RenderResult` 의 **타일 갈래** — 지도 화면을 타일 방식으로 전환한다.

**근거** = Ted 판정 ⑩ (2026-08-31 · `PLAN-SoT §9 〈238〉`). 종전에는 `jobs.py` 가
「stage 1 은 이미지 갈래만 낸다」를 코드로 못 박아 **타일이 이음매에는 있고 화면에는 못
갔다**(`03-HANDOFF §4` `#48`). 그 문장을 판정이 갈았다.

**오라클의 출처는 계약과 정본 둘뿐이다 — 추정으로 쓰지 않는다.**
  · `contracts/seams/core-viz.yaml#RenderResult` — `oneOf: [imageUrl] | [tileUrlTemplate]`
    (택일이다 · 둘을 함께 실으면 「무엇을 그릴지 두 번 적힌 완료」) ·
    `dependentRequired: {tileUrlTemplate: [bounds]}` · `tileUrlTemplate` = 「지도 위젯이
    그대로 쓰는 타일 URL 틀(`{z}`·`{x}`·`{y}` 치환)」
  · `Policy_데이터셋_상세` v2.6 `§8` 확대 조건 ⑷ — 「데이터가 가진 해상도가 한계다 …
    없는 값을 만들어 그리지 않는다」. 좌표가 없는 자료에 **경계를 지어내지 않는다**
    (`CLAUDE.md §3` · `DR-9`) — 그래서 ②비지도형은 타일 갈래로 가지 않는다.

**전환의 경계 — 등록된 데이터셋의 지도형 렌더 하나다.** 미등록 업로드(S-04·S-08)는
그대로 단일 이미지다. `#48` 이 `P3` 소유로 남긴 것이 「데이터셋 상세의 지도 화면」이고,
**범위를 늘리지 않는다**(`CLAUDE.md §5`).
"""
from __future__ import annotations

from conftest import AUTH


def _render(client, target: dict) -> dict:
    r = client.post("/viz/v1/renders",
                    json={"target": target, "style": {"palette": "단색-파랑"}},
                    headers=AUTH)
    assert r.status_code == 202, r.text
    return r.json()


def test_등록_데이터셋의_지도형_결과는_타일_갈래다(client, put_target, tiny_geotiff):
    """`oneOf` 의 다른 쪽으로 넘어간다 — `tileUrlTemplate` 이 있고 `imageUrl` 이 없다."""
    tid = put_target(copy_from=[tiny_geotiff])
    job = _render(client, {"datasetId": tid})
    assert job["status"] == "완료", job.get("failure")
    res = job["result"]

    assert "tileUrlTemplate" in res, "타일 갈래가 결과에 실리지 않았다 (`#48`)"
    assert "imageUrl" not in res, "`oneOf` 다 — 둘을 함께 내지 않는다"


def test_타일_틀은_치환_자리_셋을_그대로_가진다(client, put_target, tiny_geotiff):
    """계약 축자 — 「`{z}`·`{x}`·`{y}` 치환」. 화면은 이 셋만 바꾼다."""
    tid = put_target(copy_from=[tiny_geotiff])
    tpl = _render(client, {"datasetId": tid})["result"]["tileUrlTemplate"]
    assert "{z}" in tpl and "{x}" in tpl and "{y}" in tpl


def test_타일_갈래에도_경계와_동반파일이_함께_간다(client, put_target, tiny_geotiff):
    """`dependentRequired: {tileUrlTemplate: [bounds]}` — 경계 없는 타일 결과는 계약 위반이다.

    사이드카·월드파일은 **버려지지 않는다** — ③이 실제로 구워졌고, 화면이 원본 해상도를
    아는 자리가 사이드카다(확대 조건 ⑷).
    """
    tid = put_target(copy_from=[tiny_geotiff])
    res = _render(client, {"datasetId": tid})["result"]
    assert set(res["bounds"]) == {"west", "south", "east", "north"}
    assert res["sidecarUrl"].endswith(".json")
    assert res["worldFileUrl"].endswith(".pgw")
    assert res["thumbnailUrl"] and res["valuePreviewUrl"]


def test_타일_틀이_가리키는_주소가_실제로_타일을_낸다(client, put_target, tiny_geotiff):
    """**이음매에 있고 화면에 못 가던** 것이 `#48` 이었다 — 이제 같은 문자열로 닿는다."""
    tid = put_target(copy_from=[tiny_geotiff])
    tpl = _render(client, {"datasetId": tid})["result"]["tileUrlTemplate"]
    path = tpl.replace("{z}", "6").replace("{x}", "54").replace("{y}", "25")
    r = client.get(path[path.index("/viz/v1"):], headers=AUTH)
    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "image/png"


def test_비지도형은_타일_갈래로_가지_않는다(client, put_target):
    """좌표가 없는 자료 — **없는 경계를 지어내지 않는다**(`DR-9` · `CLAUDE.md §3`).

    타일은 웹 메르카토르 `z/x/y` 라 경계 없이는 낼 자리가 없다. ②비지도형은 그대로
    `imageUrl` 하나이고 그것이 **완료**다(`〈85〉`).
    """
    tid = put_target({"plain.npy": _npy_bytes()})
    res = _render(client, {"datasetId": tid})["result"]
    assert "tileUrlTemplate" not in res
    assert res["imageUrl"] == res["valuePreviewUrl"]
    assert "bounds" not in res


def test_미등록_업로드는_그대로_단일_이미지다(client, put_target, tiny_geotiff):
    """전환의 경계 — `#48` 이 `P3` 소유로 남긴 것은 **데이터셋 상세의 지도 화면**이다.

    S-04·S-08 의 미등록 미리보기는 이 회차의 범위가 아니다(`CLAUDE.md §5` 범위 늘리기 금지).
    """
    tid = put_target(copy_from=[tiny_geotiff])
    res = _render(client, {"uploadId": tid})["result"]
    assert "tileUrlTemplate" not in res
    assert res["imageUrl"] and res["sidecarUrl"] and res["worldFileUrl"]


def _npy_bytes() -> bytes:
    import io

    import numpy as np

    buf = io.BytesIO()
    np.save(buf, np.arange(64, dtype="float32").reshape(8, 8))
    return buf.getvalue()
