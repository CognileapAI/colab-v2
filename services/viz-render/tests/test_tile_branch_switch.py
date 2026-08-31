"""**갈래 스위치** — 「한 장」과 「타일」 중 무엇으로 나가는가를 선언으로 고른다.

**근거** = Ted 판정 ⑬ (2026-08-31 · `PLAN-SoT §9 〈240〉`) · 정본 개정
`Policy_데이터셋_상세` **v2.7 §8** 「미리보기 뷰어의 두 갈래 — 무엇이 기본인가」.

**왜 스위치가 필요한가.** 정본 260826 델타는 축자로 「**타일 서버도 바탕 지도도 쓰지
않는다**」(POL-021)·「미리보기 뷰어 = 타일 서버·바탕 지도 없이 **PNG 한 장 + 경계 좌표
4값**」이라고 적었다. 타일 전환(`〈238〉`)은 그 문면이 아니라 **대장의 「타일 서빙」 문구**를
근거로 삼았고, 그 문구의 소급 근거(`〈74〉-㉳`)는 「stage 1 밖이다」는 **배치 결정**이지
요구가 아니었다. 판정 ⑬ 은 되돌리는 대신 **두 갈래를 다 두고 A/B 로 비교**하기로 했다.

**오라클은 정본과 계약 둘뿐이다.**
  · 정본 v2.7 `§8` — **기본값은 「한 장」**(`imageUrl`)이고 타일은 **명시로 켰을 때만**이다.
  · `contracts/seams/core-viz.yaml#RenderResult` — `oneOf: [imageUrl] | [tileUrlTemplate]`.
    **계약은 고치지 않는다** — 두 갈래가 이미 다 있다. 바뀌는 것은 어느 갈래를 내는가다.

**스위치 = `COLAB_VIZ_TILE_BRANCH`**(`kernel/config.Settings.tile_branch_enabled`).
값은 홈 env 에서 온다 — 레포에 절대경로도 비밀도 적지 않는다. **기본값은 꺼짐이다.**
"""
from __future__ import annotations

from conftest import AUTH


def _render(client, target: dict) -> dict:
    r = client.post("/viz/v1/renders",
                    json={"target": target, "style": {"palette": "단색-파랑"}},
                    headers=AUTH)
    assert r.status_code == 202, r.text
    job = r.json()
    assert job["status"] == "완료", job.get("failure")
    return job


# ── ㉮ 기본값 — 「한 장」 (정본 문면) ──────────────────────────────────────────

def test_기본값은_한_장이다_등록_지도형도_imageUrl_로_나간다(client, put_target, tiny_geotiff):
    """정본 v2.7 `§8` — **기본은 「PNG 한 장 + 경계 좌표 4값」이다.**

    등록된 데이터셋의 지도형이라도 **스위치를 켜지 않으면** 타일로 가지 않는다.
    `〈238〉` 이전의 그 문면으로 되돌아가는 것이 아니라, **그 문면이 기본값이 된 것**이다.
    """
    tid = put_target(copy_from=[tiny_geotiff])
    res = _render(client, {"datasetId": tid})["result"]
    assert "imageUrl" in res, "스위치가 꺼졌는데 한 장 갈래로 나가지 않았다"
    assert "tileUrlTemplate" not in res, "`oneOf` 다 — 꺼진 스위치가 타일을 실었다"
    assert set(res["bounds"]) == {"west", "south", "east", "north"}, "경계 4값은 두 갈래 공통이다"


def test_꺼진_갈래에서도_동반_산출물은_그대로_간다(client, put_target, tiny_geotiff):
    """썸네일·값 미리보기·사이드카·월드파일은 갈래와 무관하다 — 스위치가 층을 지우지 않는다."""
    tid = put_target(copy_from=[tiny_geotiff])
    res = _render(client, {"datasetId": tid})["result"]
    assert res["thumbnailUrl"] and res["valuePreviewUrl"]
    assert res["sidecarUrl"].endswith(".json") and res["worldFileUrl"].endswith(".pgw")


# ── ㉯ 켠 갈래 — 「타일」 ────────────────────────────────────────────────────

def test_스위치를_켜면_등록_지도형이_타일로_나간다(tile_client, put_target, tiny_geotiff):
    """A/B 의 다른 쪽 — 명시로 켰을 때만 `tileUrlTemplate` 이 실린다."""
    tid = put_target(copy_from=[tiny_geotiff])
    res = _render(tile_client, {"datasetId": tid})["result"]
    assert "tileUrlTemplate" in res, "스위치를 켰는데 타일 갈래로 나가지 않았다"
    assert "imageUrl" not in res, "`oneOf` 다 — 둘을 함께 내지 않는다"


# ── ㉰ 스위치를 켜도 넘지 않는 경계 — **음성으로 잠근다** ──────────────────────

def test_켠_상태에서도_비지도형은_언제나_한_장이다(tile_client, put_target):
    """좌표가 없으면 **없는 경계를 지어내지 않는다**(`DR-9` · `CLAUDE.md §3`).

    타일은 웹 메르카토르 `z/x/y` 라 경계 없이 낼 자리가 없다. 스위치는 이 성질을
    켜지 못한다 — 스위치가 넓힐 수 있는 것은 **지도형 안**뿐이다.
    """
    tid = put_target({"plain.npy": _npy_bytes()})
    res = _render(tile_client, {"datasetId": tid})["result"]
    assert "tileUrlTemplate" not in res
    assert res["imageUrl"] == res["valuePreviewUrl"]
    assert "bounds" not in res


def test_켠_상태에서도_미등록_업로드는_언제나_한_장이다(tile_client, put_target, tiny_geotiff):
    """S-04·S-08 미등록 미리보기는 갈래 전환의 대상이 아니다 — 범위를 늘리지 않는다."""
    tid = put_target(copy_from=[tiny_geotiff])
    res = _render(tile_client, {"uploadId": tid})["result"]
    assert "tileUrlTemplate" not in res
    assert res["imageUrl"] and res["sidecarUrl"] and res["worldFileUrl"]


def test_서명_비밀이_없으면_스위치를_켜도_렌더_표면이_열리지_않는다(source_root, put_target,
                                                    tiny_geotiff):
    """서명 없는 타일 주소를 **조용히 발급하지 않는다**(`〈68〉` · `config.py`).

    ⚠ **실측해 보니 갈래보다 앞에서 막힌다** — 비밀이 없으면 `createRender` 표면 자체가
    **503**(`TILE_SIGNING_UNCONFIGURED`)이라 결과가 만들어지지도 않는다. 「꺼진 갈래로
    떨어진다」가 아니라 **아예 그리지 않는다**가 실물이고, 그것을 그대로 적는다 —
    스위치는 「타일을 내라」는 선언이지 「검증을 건너뛰라」는 선언이 아니다.
    """
    from conftest import make_client
    c = make_client(source_root, "inline", tile_signing_secret=None,
                    tile_branch_enabled=True)
    tid = put_target(copy_from=[tiny_geotiff])
    r = c.post("/viz/v1/renders",
               json={"target": {"datasetId": tid}, "style": {"palette": "단색-파랑"}},
               headers=AUTH)
    assert r.status_code == 503, r.text
    assert r.json()["code"] == "TILE_SIGNING_UNCONFIGURED"


# ── ㉱ 관측 — **어느 갈래로 나갔는지 배포 밖에서 읽을 수 있다** ────────────────

def test_헬스_본문이_지금_어느_갈래인지_말한다_꺼짐(client):
    """A/B 를 비교하려면 **도는 스택이 어느 쪽인지**를 물어볼 자리가 있어야 한다.

    이 레포의 배포 판정은 이미 **헬스 본문 대조**다(`verify/verify-deploy.sh` — 「루트 200
    으로 판정하지 않는다」). 같은 자리에 갈래를 싣는다. **계약 표면이 아니다**
    (`/healthz` 는 `include_in_schema=False` · 계약 개정 0건).
    """
    body = client.get("/healthz").json()
    assert body["unit"] == "viz-render"
    assert body["tileBranch"] == "꺼짐"


def test_헬스_본문이_지금_어느_갈래인지_말한다_켜짐(tile_client):
    body = tile_client.get("/healthz").json()
    assert body["tileBranch"] == "켜짐"


def test_환경변수가_스위치의_선언_자리다(monkeypatch):
    """값은 **홈 env** 에서 온다 — 레포에 박지 않는다. 그리고 **기본값은 꺼짐**이다."""
    from colab_viz.kernel.config import load_settings

    monkeypatch.delenv("COLAB_VIZ_TILE_BRANCH", raising=False)
    assert load_settings().tile_branch_enabled is False, "선언이 없으면 한 장이다"

    for on in ("1", "true", "TRUE", "on", "yes"):
        monkeypatch.setenv("COLAB_VIZ_TILE_BRANCH", on)
        assert load_settings().tile_branch_enabled is True, f"{on!r} 이 켜짐으로 읽히지 않았다"

    for off in ("0", "false", "off", "no", ""):
        monkeypatch.setenv("COLAB_VIZ_TILE_BRANCH", off)
        assert load_settings().tile_branch_enabled is False, f"{off!r} 이 꺼짐으로 읽히지 않았다"


def _npy_bytes() -> bytes:
    import io

    import numpy as np

    buf = io.BytesIO()
    np.save(buf, np.arange(64, dtype="float32").reshape(8, 8))
    return buf.getvalue()
