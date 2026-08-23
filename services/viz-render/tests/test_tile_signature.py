"""타일 경로 인증 — 서비스 토큰 **또는** 렌더에 묶인 단명 서명 (`PLAN-SoT §9-〈68〉`).

**왜 이 파일이 있는가** — `getRenderTile` 은 계약이 「core-api 를 통과하지 않는 유일한
경로」라 못박은 자리이고, 부르는 것은 **브라우저 지도 위젯**이다. 위젯은 서비스 토큰을
가질 수 없고 가져서도 안 된다. 라우터 전체에 서비스 토큰 `Depends` 가 걸려 있으면
구현은 계약대로인데 **실배포에서 타일이 전량 401** 이다 — 시험이 헤더를 스스로 넣어
green 이었을 뿐이다.

**행복 경로만 보는 시험은 여기서 오라클이 아니다.** 다섯을 다 본다:
유효 서명 통과 · **만료 서명 거절** · **렌더 A 서명이 렌더 B 에서 안 통함** ·
변조 서명 거절 · 서비스 토큰 여전히 통함.
"""
from __future__ import annotations

import time

from conftest import AUTH, SIGNING_SECRET, make_client

TILE = "/tiles/6/54/24.png"


def _rendered(client, put_target, tiny_geotiff) -> dict:
    tid = put_target(copy_from=[tiny_geotiff])
    r = client.post("/viz/v1/renders",
                    json={"target": {"datasetId": tid}, "style": {"palette": "단색-파랑"}},
                    headers=AUTH)
    assert r.status_code == 202, r.text
    job = r.json()
    assert job["status"] == "완료", job
    return job


def _tile_path(job: dict) -> str:
    """템플릿을 **FE 가 하는 그대로** 쓴다 — `{z}`·`{x}`·`{y}` 치환 말고는 손대지 않는다."""
    return (job["result"]["tileUrlTemplate"]
            .replace("{z}", "6").replace("{x}", "54").replace("{y}", "24"))


# ── ① 유효한 서명은 토큰 없이 통과한다 ──────────────────────────────────────
def test_템플릿의_서명만으로_타일을_받는다_토큰_없이(client, put_target, tiny_geotiff):
    job = _rendered(client, put_target, tiny_geotiff)
    url = _tile_path(job)
    assert "sig=" in url and "exp=" in url, url
    r = client.get(url)                                    # Authorization 헤더 없음
    assert r.status_code == 200, r.text
    assert r.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_서명이_아예_없으면_401_이다(client, put_target, tiny_geotiff):
    """서명 도입이 「타일은 아무나」가 되지 않는다 — 이것이 없으면 위 시험은 무의미하다."""
    job = _rendered(client, put_target, tiny_geotiff)
    bare = _tile_path(job).split("?")[0]
    assert client.get(bare).status_code == 401


# ── ② 만료된 서명은 거절된다 ────────────────────────────────────────────────
def test_만료된_서명은_거절된다(source_root, put_target, tiny_geotiff):
    """수명이 지난 서명이 계속 먹히면 「단명」이 아니다.

    **시계를 흉내내지 않는다** — 서명 수명을 0초로 배선한 인스턴스에서 실제로 만료시킨다.
    """
    c = make_client(source_root, "inline", tile_signature_ttl_seconds=0)
    job = _rendered(c, put_target, tiny_geotiff)
    time.sleep(1.1)                                        # exp(초 단위)를 실제로 넘긴다
    r = c.get(_tile_path(job))
    assert r.status_code == 401
    assert "만료" in r.json()["message"]


# ── ③ 렌더 A 의 서명은 렌더 B 에서 안 통한다 ────────────────────────────────
def test_다른_렌더의_서명은_통하지_않는다(client, put_target, tiny_geotiff):
    """서명이 렌더에 묶여 있지 않으면 서명 하나로 남의 미리보기를 다 볼 수 있다."""
    a = _rendered(client, put_target, tiny_geotiff)
    b = _rendered(client, put_target, tiny_geotiff)
    assert a["renderId"] != b["renderId"]

    a_query = _tile_path(a).split("?", 1)[1]
    borrowed = f"/viz/v1/renders/{b['renderId']}{TILE}?{a_query}"
    assert client.get(_tile_path(b)).status_code == 200    # B 자기 서명은 통한다 (대조군)
    assert client.get(borrowed).status_code == 401


# ── ④ 변조된 서명은 거절된다 ────────────────────────────────────────────────
def test_변조된_서명은_거절된다(client, put_target, tiny_geotiff):
    job = _rendered(client, put_target, tiny_geotiff)
    url = _tile_path(job)
    base, _, query = url.partition("?")
    parts = dict(kv.split("=", 1) for kv in query.split("&"))

    # ㉠ 서명 한 글자를 바꾼다
    sig = parts["sig"]
    flipped = ("0" if sig[-1] != "0" else "1")
    assert client.get(f"{base}?exp={parts['exp']}&sig={sig[:-1]}{flipped}").status_code == 401

    # ㉡ 서명은 그대로 두고 **만료 시각만 늘린다** — 서명이 exp 를 덮지 않으면 통과해 버린다
    assert client.get(f"{base}?exp={int(parts['exp']) + 86400}&sig={sig}").status_code == 401


# ── ⑤ 서비스 토큰 경로는 그대로 살아 있다 ───────────────────────────────────
def test_서비스_토큰은_서명_없이도_여전히_통한다(client, put_target, tiny_geotiff):
    job = _rendered(client, put_target, tiny_geotiff)
    bare = _tile_path(job).split("?")[0]
    r = client.get(bare, headers=AUTH)
    assert r.status_code == 200 and r.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_틀린_서비스_토큰은_서명이_없으면_401_이다(client, put_target, tiny_geotiff):
    job = _rendered(client, put_target, tiny_geotiff)
    bare = _tile_path(job).split("?")[0]
    assert client.get(bare, headers={"Authorization": "Bearer wrong-token"}).status_code == 401


# ── 수명 — 서명은 렌더 결과 수명 안에 든다 (〈68〉-ⓓ) ────────────────────────
def test_서명_수명은_렌더_결과_수명을_넘지_않는다(source_root, put_target, tiny_geotiff):
    """`uploadId` 대상은 `expiresAt` 가 있다. 서명이 그보다 오래 살면 안 된다."""
    from datetime import datetime

    c = make_client(source_root, "inline", result_ttl_seconds=60,
                    tile_signature_ttl_seconds=86400)
    tid = put_target(copy_from=[tiny_geotiff])
    job = c.post("/viz/v1/renders",
                 json={"target": {"uploadId": tid}, "style": {"palette": "단색-파랑"}},
                 headers=AUTH).json()
    expires = datetime.fromisoformat(job["expiresAt"].replace("Z", "+00:00")).timestamp()
    query = dict(kv.split("=", 1) for kv in _tile_path(job).split("?", 1)[1].split("&"))
    assert int(query["exp"]) <= int(expires) + 1, (query["exp"], expires)


# ── 미배선 — 서명 비밀이 없으면 렌더 표면은 503 이다 (조용히 인증을 끄지 않는다) ──
def test_서명_비밀이_없으면_렌더_표면은_503_이다_통과가_아니다(source_root):
    c = make_client(source_root, "inline", tile_signing_secret=None)
    assert c.get("/healthz").status_code == 200
    assert c.get("/viz/v1/palettes", headers=AUTH).status_code == 503
    r = c.get("/viz/v1/renders/01ARZ3NDEKTSV4RRFFQ69G5FAV/tiles/6/54/24.png")
    assert r.status_code == 503
    assert r.json()["code"] == "TILE_SIGNING_UNCONFIGURED"


def test_비밀이_다르면_서명이_통하지_않는다(source_root, put_target, tiny_geotiff):
    """비밀이 진짜로 서명에 들어가는지 — 상수를 반환하고 있으면 여기서 걸린다."""
    a = make_client(source_root, "inline")
    job = _rendered(a, put_target, tiny_geotiff)
    b = make_client(source_root, "inline", tile_signing_secret=SIGNING_SECRET + "-다른비밀")
    # 서명 검증이 작업 조회보다 먼저다 — b 에는 이 renderId 가 없지만 401 이 나와야 한다
    assert b.get(_tile_path(job)).status_code == 401
