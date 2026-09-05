"""`V-1` 팔레트 선택 재렌더 — 완료 정의 ⑴~⑺ 축자(`work-items.yaml` · `PLAN-SoT §9 〈289〉`-㉰).

오라클은 **조항 문면 그대로**다. 조항을 새로 만들거나 넓히지 않는다 —
  ⑴ 팔레트를 바꾸면 같은 데이터·같은 색범위·같은 구간 수에서 **색만 바뀐 그림**이 나온다.
     범례 구간 경계(`classes[].min/max`)와 `bounds` 가 바뀌지 않는다
  ⑵ 고를 수 있는 것은 `listPalettes` 가 준 것뿐이다 — 목록 밖 이름은 거절(음성 1건)
  ⑶ 옛 색이 섞이지 않는다 — 재렌더 뒤 **화면에 도달한 산출물의 키가 새 키**임을 대조한다
  ⑷ 기본 갈래(한 장 · `〈240〉`) = 새 `.png`(＋`.json`·`.pgw`)가 새 키로 서고 화면이 그 키를
     가리키며 **옛 산출물은 지운다**(`〈259〉`)
  ⑷-b **새 것이 선 뒤에 옛 것을 지운다** — 볼 그림이 하나도 없는 순간이 없다
  ⑷-c **음성 — 지우는 대상은 렌더 산출물뿐**이다(원본·기준 격자·데이터셋·`tile-` 무접촉)
  ⑸ 켠 갈래(타일) = **「무효화할 것이 없음이 유지된다」** — 서버에 구워 두는 조각이 0건
  ⑺ 범위 밖 = 고르는 UI 는 `J-6` 소유. 이 파일에 UI 시험이 없다

⛔ **값 재사용은 요구가 아니다**(`〈289〉`-㉰ⓐ) — 성능 합격선은 `〈233〉`(p95 2.081 s ≪ 10 s)
   가 이미 잡았고 이 파일이 새 눈금을 세우지 않는다.
⛔ **이미 쌓인 옛 키 파일 청소는 `RC-1`** 이다 — 이 파일이 재고를 세지 않는다.
"""
from __future__ import annotations

import time
from pathlib import Path

import numpy as np

from colab_viz.domains.d7_visualization import invalidation, jobs, palettes
from colab_viz.kernel import storage_layout

from conftest import AUTH, make_client

_OTHER = "다색-무지개"
_BASE = "단색-파랑"


def _wait(predicate, timeout: float = 20.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return predicate()


def _render(client, tid: str, palette: str = _BASE) -> dict:
    r = client.post("/viz/v1/renders", headers=AUTH, json={
        "target": {"datasetId": tid}, "style": {"palette": palette}})
    assert r.status_code == 202, r.text
    rid = r.json()["renderId"]
    assert _wait(lambda: client.get(f"/viz/v1/renders/{rid}",
                                    headers=AUTH).json()["status"] != "그리는 중")
    return client.get(f"/viz/v1/renders/{rid}", headers=AUTH).json()


def _keys(body: dict) -> set[str]:
    """**화면에 도달한** 자리에서 키를 읽는다 — 작업 내부가 아니라 응답 본문이다."""
    res = body.get("result") or {}
    out = set()
    for k in ("imageUrl", "thumbnailUrl", "valuePreviewUrl", "sidecarUrl", "worldFileUrl"):
        if res.get(k):
            out.add(Path(res[k].split("?")[0]).stem)
    return out


# ── ⑴ 색만 바뀐 그림 ─────────────────────────────────────────────────────────
def test_팔레트를_바꾸면_구간_경계와_경계상자가_그대로다(source_root, put_target, tiny_geotiff):
    """⑴ 축자. **색만 바뀐다** — `classes[].min/max` 와 `bounds` 는 같은 값이다."""
    client = make_client(source_root, "inline")
    tid = put_target(copy_from=[tiny_geotiff])
    a = _render(client, tid, _BASE)
    b = _render(client, tid, _OTHER)
    assert a["status"] == b["status"] == "완료"
    ba, bb = a["result"]["legend"]["classes"], b["result"]["legend"]["classes"]
    assert [(c["min"], c["max"]) for c in ba] == [(c["min"], c["max"]) for c in bb], \
        "팔레트를 바꿨더니 범례 구간 경계가 움직였다"
    assert len(ba) == len(bb) == palettes.DEFAULT_CLASS_COUNT
    assert a["result"]["bounds"] == b["result"]["bounds"], \
        "팔레트를 바꿨더니 경계상자가 움직였다"
    assert a["result"]["legend"]["palette"] == _BASE
    assert b["result"]["legend"]["palette"] == _OTHER
    assert [c["color"] for c in ba] != [c["color"] for c in bb], "색이 안 바뀌었다"


# ── ⑵ 목록 밖은 거절 (음성 1건) ──────────────────────────────────────────────
def test_목록_밖의_팔레트는_거절한다(source_root, put_target, tiny_geotiff):
    """⑵ **음성.** 고를 수 있는 것은 `listPalettes` 가 준 것뿐이다."""
    client = make_client(source_root, "inline")
    tid = put_target(copy_from=[tiny_geotiff])
    served = {it["palette"] for it in
              client.get("/viz/v1/palettes", headers=AUTH).json()["items"]}
    assert served, "목록이 비면 이 시험은 아무것도 안 잰다"
    r = client.post("/viz/v1/renders", headers=AUTH, json={
        "target": {"datasetId": tid}, "style": {"palette": "없는-팔레트"}})
    assert r.status_code == 400, r.text
    for key in served:
        assert _render(client, tid, key)["status"] == "완료", f"목록이 준 값이 거절됐다: {key}"


# ── ⑶⑷ 새 키가 서고 옛 벌은 지워진다 ────────────────────────────────────────
def test_팔레트_재렌더는_새_키를_세우고_옛_벌을_지운다(source_root, put_target, tiny_geotiff):
    """⑶＋⑷ 축자. **운영 기본 실행기(`thread`)로 잰다** — 집행이 완료 경로에 있는지가
    요점이라 `inline` 으로만 재면 `〈코드리뷰 #2〉` 와 같은 착시가 다시 선다."""
    client = make_client(source_root, "thread")
    tid = put_target(copy_from=[tiny_geotiff])
    first = _render(client, tid, _BASE)
    store = client.app.state.jobs
    old_job = store.get(first["renderId"])
    old_paths = [a.path for a in old_job.artifacts.all()]
    old_keys = {a.cache_key for a in old_job.artifacts.all()}
    assert old_paths and all(p.exists() for p in old_paths)

    second = _render(client, tid, _OTHER)
    new_job = store.get(second["renderId"])
    new_paths = [a.path for a in new_job.artifacts.all()]
    new_keys = {a.cache_key for a in new_job.artifacts.all()}

    # ⑶ 화면이 가리키는 키가 **새 키**다 — 옛 키는 응답 어디에도 없다.
    assert _keys(second) and _keys(second) <= new_keys
    assert not (_keys(second) & old_keys), "재렌더 응답이 옛 키를 가리킨다"
    assert old_keys != new_keys, "팔레트를 바꿨는데 키가 안 갈렸다"
    # ⑷ 새 `.png`(＋`.json`·`.pgw`)가 서고 **옛 산출물은 지운다**.
    assert {p.suffix for p in new_paths} >= {".png", ".json", ".pgw"}
    assert all(p.exists() for p in new_paths), "새 벌이 서지 않았다"
    assert new_job.invalidation_removed, "팔레트 재렌더가 옛 벌을 하나도 안 지웠다"
    assert not any(p.exists() for p in old_paths), "옛 팔레트 벌이 그대로 남았다"


# ── ⑷ 회귀 가드 — 「완료」의 뜻이 좁아진 채로 있는가 (2026-09-05) ────────────
#: 회수를 늦춰 「완료 표시 ↔ 회수 집행」 창을 **결정론으로** 벌린다. 이 창이 실물에서
#: 15 ms 였고 시험 폴링 주기가 20 ms 라, 원래 red 는 표본 4회 중 3회로만 떴다 —
#: 운에 기대는 시험은 가드가 아니다. 하네스를 시험 안에 두는 이유 = **게이트가 돌아야**
#: 한다(레포 밖 플러그인은 CI 가 못 본다).
_RECLAIM_DELAY_SECONDS = 0.3


def _회수를_늦춘다(monkeypatch, seconds: float = _RECLAIM_DELAY_SECONDS) -> None:
    _orig = invalidation.apply

    def _slow(*args, **kwargs):
        time.sleep(seconds)
        return _orig(*args, **kwargs)

    monkeypatch.setattr(invalidation, "apply", _slow)


def test_화면이_완료를_본_그_순간_옛_벌은_이미_지워져_있다(source_root, put_target,
                                                    tiny_geotiff, monkeypatch):
    """**⑷ 의 순서 가드.** 「완료」는 회수까지 끝난 뒤에만 발행된다.

    ⛔ 이 시험이 잠그는 결함 — `job.status = STATUS_DONE` 이 회수 **앞**에 서면,
    상태를 폴링하는 진짜 클라이언트가 **「완료」인데 옛 벌이 그대로인 자리**를 본다.
    오라클은 작업 내부가 아니라 **화면이 보는 것**이다: HTTP 로 `완료` 를 본 그 순간
    ⑴ 옛 파일이 자리에 없고 ⑵ 집행 결과가 이미 적혀 있다.
    ⚠ 회수를 늦춰 창을 벌리므로, 순서가 뒤집히면 **매번** red 다(간헐이 아니다).
    """
    _회수를_늦춘다(monkeypatch)
    client = make_client(source_root, "thread")
    tid = put_target(copy_from=[tiny_geotiff])
    store = client.app.state.jobs
    first = _render(client, tid, _BASE)
    old_paths = [a.path for a in store.get(first["renderId"]).artifacts.all()]
    assert old_paths and all(p.exists() for p in old_paths)

    r = client.post("/viz/v1/renders", headers=AUTH, json={
        "target": {"datasetId": tid}, "style": {"palette": _OTHER}})
    assert r.status_code == 202, r.text
    rid = r.json()["renderId"]

    # 창이 열려 있는 동안 화면이 보는 것 — **`그리는 중` 하나뿐이고 계약을 벗어나지 않는다.**
    창을_봤다 = False
    body: dict = {}
    deadline = time.monotonic() + 20.0
    while time.monotonic() < deadline:
        body = client.get(f"/viz/v1/renders/{rid}", headers=AUTH).json()
        if body["status"] == "완료":
            break
        assert body["status"] == "그리는 중", f"제3의 상태가 보였다: {body['status']}"
        assert body.get("stage") in (None, *jobs.STAGES), \
            f"계약 밖 단계가 보였다: {body.get('stage')}"
        assert "result" not in body, "`그리는 중` 인데 결과가 실렸다"
        창을_봤다 = True
        time.sleep(0.02)
    assert body.get("status") == "완료", "재렌더가 끝나지 않았다"
    assert 창을_봤다, "창이 아예 안 열렸다 — 이 시험이 순서를 재고 있지 않다"

    job = store.get(rid)
    assert not any(p.exists() for p in old_paths), \
        "화면이 「완료」를 봤는데 옛 벌이 아직 자리에 있다 — 「완료」가 회수보다 먼저 발행됐다"
    assert job.invalidation_removed, \
        "화면이 「완료」를 봤는데 회수 집행이 아직 안 적혔다"


def test_회수가_실패해도_렌더는_완료로_선다(source_root, put_target, tiny_geotiff,
                                        monkeypatch):
    """**음성 · ⑷-b 의 반대 절반.** 옛 벌을 못 지운 것은 **새 그림이 못 선 것이 아니다.**

    지우다 실패했다고 렌더를 `실패` 나 영원한 `그리는 중` 으로 만들면, 볼 그림이
    멀쩡히 서 있는데 화면이 그것을 못 쓴다. **`inline` 실행기로 잰다** — 예외가
    스레드 안에서 조용히 사라지지 않고 접수 표면까지 올라오는 자리가 여기다.
    """
    client = make_client(source_root, "inline")
    tid = put_target(copy_from=[tiny_geotiff])
    store = client.app.state.jobs
    first = _render(client, tid, _BASE)
    old_paths = [a.path for a in store.get(first["renderId"]).artifacts.all()]
    assert old_paths and all(p.exists() for p in old_paths)

    def _못_지운다(*args, **kwargs):
        raise OSError("자리를 지울 수 없다")

    monkeypatch.setattr(invalidation, "apply", _못_지운다)
    second = _render(client, tid, _OTHER)
    assert second["status"] == "완료", "회수가 실패했다고 렌더까지 실패로 만들었다"
    job = store.get(second["renderId"])
    assert job.invalidation_removed == (), "지우지 못했는데 지웠다고 적혔다"
    assert all(p.exists() for p in old_paths), "집행이 실패했는데 파일이 사라졌다"
    assert all(a.path.exists() for a in job.artifacts.all()), "새 벌이 서지 않았다"


def test_새_것이_선_뒤에_옛_것을_지운다(source_root, put_target, tiny_geotiff):
    """⑷-b 축자 — **중간에 볼 그림이 하나도 없는 순간이 없다.** 실패한 재렌더는
    아무것도 지우지 않는 것이 그 문장의 나머지 절반이다."""
    # **`manual` 실행기다** — 접수(202)를 받은 **뒤에** 원본이 망가지는 자리를 만든다.
    # `inline` 으로 하면 POST 가 415 로 막혀 「실패한 재렌더」 자체가 서지 않는다.
    client = make_client(source_root, "manual")
    tid = put_target(copy_from=[tiny_geotiff])
    store = client.app.state.jobs
    first = client.post("/viz/v1/renders", headers=AUTH, json={
        "target": {"datasetId": tid}, "style": {"palette": _BASE}}).json()["renderId"]
    store.run_pending()
    old = [a.path for a in store.get(first).artifacts.all()]
    assert old and all(p.exists() for p in old)
    second = client.post("/viz/v1/renders", headers=AUTH, json={
        "target": {"datasetId": tid}, "style": {"palette": _OTHER}}).json()["renderId"]
    for p in storage_layout.target_dir(source_root, tid).iterdir():
        p.write_bytes(b"\x00" * 64)          # 그릴 수 없는 바이트 → 재렌더가 실패한다
    store.run_pending()
    job = store.get(second)
    assert job.status == "실패", "시험이 「실패한 재렌더」를 못 만들었다"
    assert job.invalidation_removed == (), "실패한 재렌더가 지웠다"
    assert all(p.exists() for p in old), "새 것이 안 섰는데 옛 그림이 사라졌다"


# ── ⑷-c 음성 — 지우는 대상은 렌더 산출물뿐 ──────────────────────────────────
def test_팔레트_재렌더는_원본과_기준_격자를_한_바이트도_안_건드린다(source_root, put_target,
                                                              tiny_geotiff):
    """⑷-c **음성.** 원본 · 기준 격자 파일 · 데이터셋은 어떤 경우에도 지우지 않는다."""
    client = make_client(source_root, "inline")
    tid = put_target(copy_from=[tiny_geotiff],
                     grid={"lat2d.npy": np.zeros((2, 2)), "lon2d.npy": np.zeros((2, 2))})
    _render(client, tid, _BASE)
    base = storage_layout.target_dir(source_root, tid)
    before = {p.relative_to(base).as_posix(): p.read_bytes()
              for p in sorted(base.rglob("*")) if p.is_file()}
    assert before, "대상 디렉터리가 비었다 — 시험이 아무것도 안 재고 있다"
    _render(client, tid, _OTHER)
    after = {p.relative_to(base).as_posix(): p.read_bytes()
             for p in sorted(base.rglob("*")) if p.is_file()}
    assert after == before, "팔레트 재렌더가 원본·기준 격자를 건드렸다"


def test_팔레트_재렌더는_지도_타일을_지우지_않는다(source_root, put_target, tiny_geotiff):
    """⑷-c **음성 · `tile-` 은 D5 소유다.** 같은 자리에 살지만 후보로 들어와도 `kept` 다."""
    client = make_client(source_root, "inline")
    tid = put_target(copy_from=[tiny_geotiff])
    _render(client, tid, _BASE)
    previews = Path(client.app.state.settings.preview_dir)
    tile_key = "tile-" + "c" * 64
    tile = storage_layout.preview_path(previews, tile_key, ".tif")
    tile.parent.mkdir(parents=True, exist_ok=True)
    tile.write_bytes(b"tile")
    store = client.app.state.jobs
    store._produced.setdefault(tid, {})[str(tile)] = invalidation.StaleCandidate(
        cache_key=tile_key, path=tile)
    _render(client, tid, _OTHER)
    assert tile.exists(), "팔레트 재렌더가 지도 타일을 지웠다"


def test_원본이_바뀐_재렌더는_앞의_벌을_지우지_않는다(source_root, put_target, tiny_geotiff):
    """**음성 · 회수는 팔레트 자리에만 선다.** 조각이 늘어 원본 해시가 갈린 재렌더는
    「같은 데이터·같은 색범위」가 아니므로 ⑷ 의 「옛 산출물」이 아니다 —
    `Y-1` 완료 정의 ⓒ 의 「사람이 부른 렌더는 앞의 산출물을 지우지 않는다」가 그대로 선다."""
    client = make_client(source_root, "inline")
    tid = put_target(copy_from=[tiny_geotiff])
    old = [a.path for a in
           client.app.state.jobs.get(_render(client, tid, _BASE)["renderId"]).artifacts.all()]
    (storage_layout.target_dir(source_root, tid) / "두번째.tif").write_bytes(
        tiny_geotiff.read_bytes())
    second = client.app.state.jobs.get(_render(client, tid, _BASE)["renderId"])
    assert second.invalidation_removed == (), "팔레트가 그대로인데 앞의 벌을 지웠다"
    assert all(p.exists() for p in old)


def _fetch_tiles(client, template: str) -> list[bytes]:
    out = []
    for z, x, y in ((0, 0, 0), (1, 1, 0)):
        r = client.get(template.format(z=z, x=x, y=y), headers=AUTH)
        assert r.status_code == 200, r.text
        out.append(r.content)
    return out


# ── ⑸ 켠 갈래 — 무효화할 것이 없음이 유지된다 ───────────────────────────────
def test_타일_갈래는_재렌더_뒤에도_구워_둔_조각이_0건이다(source_root, put_target, tiny_geotiff):
    """⑸ **음성.** 통과 조건은 「무효화를 구현했다」가 아니라 **「무효화할 것이 없음이
    유지된다」** 다 — 서버에 구워 두는 조각이 생기면 이 시험이 red 를 낸다."""
    client = make_client(source_root, "inline", tile_branch_enabled=True)
    tid = put_target(copy_from=[tiny_geotiff])
    first = _render(client, tid, _BASE)["result"]
    previews = Path(client.app.state.settings.preview_dir)
    assert first.get("tileUrlTemplate"), "타일 갈래가 서지 않았다 — 시험이 딴 것을 잰다"
    tiles_before = _fetch_tiles(client, first["tileUrlTemplate"])
    second = _render(client, tid, _OTHER)["result"]
    tiles_after = _fetch_tiles(client, second["tileUrlTemplate"])
    on_disk = {p.name for p in previews.rglob("*") if p.is_file()}
    assert not any(n.endswith(".png") and "/tiles/" in n for n in on_disk)
    assert not any(n.startswith("tile") or n.endswith((".mvt", ".pbf")) for n in on_disk), \
        "타일 갈래가 서버에 조각을 구워 뒀다 — ⑸ 의 전제가 깨졌다"
    # **새 `renderId` 의 틀로 갈아탄다** — 옛 조각과 새 조각이 한 화면에 섞이지 않는다.
    assert second["tileUrlTemplate"] != first["tileUrlTemplate"]
    assert tiles_before and tiles_after and tiles_before != tiles_after, \
        "팔레트를 바꿨는데 타일 픽셀이 그대로다"
