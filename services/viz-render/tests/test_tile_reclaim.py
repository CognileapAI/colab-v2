"""지도 타일 **회수** — 판독기의 지목을 배경 루프가 집행한다 (`TL-1` ⑷ 후단·⑹).

Ted 판정(2026-09-05) — **「도는 배경 루프에 얹는다」**. 대장 `TL-1` 이 열어 둔 두 자리가
그것으로 닫힌다: ⑷ **후단** = 판독기가 회수와 결선된다 · ⑹ **회수 주체·주기** = `#60` 이
세운 그 주기 배경 루프(`app/trigger_loop.TriggerDrainLoop`)다.

**이 파일이 잠그는 것은 「지운다」가 아니라 「무엇을 못 지우는가」다.**
  ⑴ 지우는 것은 **고아(못 닿는다)** 뿐이다 — 계산 불가·살아 있다·판정 불가·`tile-` 아닌 키는
     한 벌도 손대지 않는다
  ⑵ **fail-closed** — 주체를 못 모으거나(0건) 못 연 주체가 있으면 **판정을 시작하지 않는다**
     (`ReaderNotReady`). 못 센 것을 「고아」로 세면 그것이 오삭제의 근거가 된다
     (`DATA-REFERENCE §0 M-9`)
  ⑶ **상한** — 한 바퀴가 지울 수 있는 벌 수에 뚜껑이 있다. 넘으면 **지우지 않고 멈춘다**
  ⑷ **기본은 관측 전용** — 배포가 명시로 켜기 전에는 세기만 하고 0건 지운다
  ⑸ **계획기는 셋이 아니다** — `invalidation.plan()` 하나를 `keep_keys` 로 부르고
     (`reclaim_plan`·`supersede_plan` 과 같은 모양) 지우는 문은 `invalidation.apply()` 하나다
  ⑹ **한 바퀴가 실패해도 루프는 죽지 않는다**(`#60` 의 규칙 그대로)
"""
from __future__ import annotations

import time

import pytest

from colab_viz.domains.d7_visualization import (invalidation, ownership, tile_liveness,
                                               tile_reclaim, value_lookup)
from colab_viz.kernel import storage_layout


# ── 픽스처 재료 (판독기 시험과 같은 수법 — 이름은 **계약이 낳는다**) ──────────────
def _body(root, target_id: str, file_id: str, payload: bytes):
    d = root / storage_layout.UPLOADS_PREFIX / target_id
    d.mkdir(parents=True, exist_ok=True)
    p = d / file_id
    p.write_bytes(payload)
    return p


def _bake_tile(previews_root, source):
    key = value_lookup.candidate_tile_keys(source, grid_dir=None)[0][0]
    out = storage_layout.preview_path(previews_root, key, ".tif")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(b"COG")
    return key, out


def _orphan_tile(previews_root, seed: str, *, age_days: float = 30.0):
    """**어느 주체도 낳을 수 없는 이름** — 자리를 뒤져 지어낸 것이 아니라 접두사만 맞춘 벌이다."""
    key = storage_layout.MAP_TILE_KEY_PREFIX + (seed * 64)[:64]
    p = storage_layout.preview_path(previews_root, key, ".tif")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"OLD-COG")
    old = time.time() - 86400 * age_days
    import os
    os.utime(p, (old, old))
    return key, p


@pytest.fixture()
def 자리(tmp_path):
    """살아 있는 주체 하나 ＋ 그 주체가 낳는 타일 하나 ＋ 못 닿는 타일 하나."""
    up, pv = tmp_path / "storage", tmp_path / "previews"
    src = _body(up, "01M0DATASETA00000000000000", "01M0FILEA000000000000000A",
                b"\x00live-bytes\x01" * 8)
    live_key, live_path = _bake_tile(pv, src)
    dead_key, dead_path = _orphan_tile(pv, "a")
    return {"storage": up, "previews": pv, "source": src,
            "live_key": live_key, "live_path": live_path,
            "dead_key": dead_key, "dead_path": dead_path}


# ── ⑴ 지우는 것은 고아뿐이다 ────────────────────────────────────────────────────
def test_못_닿는_타일_한_벌만_지운다(자리):
    r = tile_reclaim.run_pass(previews_root=자리["previews"], storage_root=자리["storage"],
                              apply=True)
    assert r.ready is True, r.reason
    assert r.unreachable == 1 and r.reachable == 1
    assert [p.name for p in r.removed] == [자리["dead_path"].name]
    assert not 자리["dead_path"].exists(), "고아를 안 지웠다"
    assert 자리["live_path"].exists(), "살아 있는 벌을 지웠다 — 오삭제다"


def test_지운_키마다_등급과_나이가_남는다(자리):
    r = tile_reclaim.run_pass(previews_root=자리["previews"], storage_root=자리["storage"],
                              apply=True)
    assert len(r.rows) == 1
    row = r.rows[0]
    assert row["cache_key"] == 자리["dead_key"]
    assert row["grade"] == ownership.GRADE_ORPHAN
    assert row["age_days"] >= 29


def test_타일이_아닌_벌은_후보에도_안_든다(자리):
    """`tile-` 이 아닌 키는 **다른 규칙(`render_cache_key`)의 산출물**이다 — 이 문 밖이다."""
    render = 자리["previews"] / ("f" * 64 + ".png")
    render.write_bytes(b"PNG")
    sidecar = 자리["previews"] / ("f" * 64 + ".json")
    sidecar.write_bytes(b"{}")

    r = tile_reclaim.run_pass(previews_root=자리["previews"], storage_root=자리["storage"],
                              apply=True)
    assert render.exists() and sidecar.exists(), "타일 판독기가 렌더 산출물을 지웠다"
    assert all(row["cache_key"].startswith(storage_layout.MAP_TILE_KEY_PREFIX)
               for row in r.rows)
    assert all(p.name.startswith(storage_layout.MAP_TILE_KEY_PREFIX) for p in r.removed)


def test_판정_불가_구판_벌도_손대지_않는다(자리):
    """`ownership` 이 **판정 불가**로 두는 구판 사이드카 벌 — 회수 대상이 아니다(덫 ②)."""
    key = "e" * 64
    (자리["previews"] / f"{key}.png").write_bytes(b"PNG")
    (자리["previews"] / f"{key}.json").write_text('{"sidecarVersion": 1}', encoding="utf-8")

    groups = [g for g in ownership.scan(자리["previews"]) if g.cache_key == key]
    led = ownership.Ledger(dataset_files=frozenset({"01M0FILEA000000000000000A"}),
                           upload_files=frozenset())
    assert groups and ownership.grade(groups[0], led).grade == ownership.GRADE_UNDECIDABLE

    tile_reclaim.run_pass(previews_root=자리["previews"], storage_root=자리["storage"],
                          apply=True)
    assert (자리["previews"] / f"{key}.png").exists()
    assert (자리["previews"] / f"{key}.json").exists()


# ── ⑵ fail-closed ──────────────────────────────────────────────────────────────
def test_주체가_0건이면_한_벌도_안_지운다(tmp_path):
    """**빈 자리를 「없다」로 읽지 않는다** — 주체 0 이면 전건이 고아로 뜬다."""
    pv = tmp_path / "previews"
    dead_key, dead_path = _orphan_tile(pv, "b")
    empty = tmp_path / "storage"
    (empty / storage_layout.UPLOADS_PREFIX).mkdir(parents=True)

    r = tile_reclaim.run_pass(previews_root=pv, storage_root=empty, apply=True)
    assert r.ready is False
    assert r.removed == ()
    assert r.unreachable == 0, "판정을 못 한 회차의 고아 수를 세지 않는다"
    assert dead_path.exists()
    assert "주체" in r.reason


def test_저장소_루트가_없으면_판정을_시작하지_않는다(자리, tmp_path):
    r = tile_reclaim.run_pass(previews_root=자리["previews"],
                              storage_root=tmp_path / "없는-자리", apply=True)
    assert r.ready is False and r.removed == ()
    assert 자리["dead_path"].exists(), "자리를 못 읽은 회차가 지웠다"


def test_계산_불가가_있으면_한_벌도_안_지우고_고아로_세지_않는다(자리, monkeypatch):
    """**제3의 상태** — 못 연 주체가 가리키던 타일이 고아로 둔갑하는 것을 막는다."""
    def 못_연다(path):
        raise OSError("Permission denied")

    monkeypatch.setattr(tile_liveness, "file_digest", 못_연다)
    r = tile_reclaim.run_pass(previews_root=자리["previews"], storage_root=자리["storage"],
                              apply=True)
    assert r.ready is False
    assert r.removed == () and r.unreachable == 0
    assert 자리["dead_path"].exists() and 자리["live_path"].exists()
    assert "계산 불가" in r.reason


# ── ⑶ 상한 — 넘으면 지우지 않고 멈춘다 ──────────────────────────────────────────
def test_상한을_넘으면_지우지_않고_멈춘다(자리):
    for seed in ("c", "d", "e"):
        _orphan_tile(자리["previews"], seed)
    r = tile_reclaim.run_pass(previews_root=자리["previews"], storage_root=자리["storage"],
                              apply=True, max_keys=2)
    assert r.capped is True
    assert r.removed == (), "상한을 넘었는데 지웠다"
    assert r.unreachable == 4
    assert list(자리["previews"].glob("tile-*")) != []


def test_상한_안이면_그대로_집행한다(자리):
    r = tile_reclaim.run_pass(previews_root=자리["previews"], storage_root=자리["storage"],
                              apply=True, max_keys=1)
    assert r.capped is False and len(r.removed) == 1


# ── ⑷ 기본은 관측 전용 ──────────────────────────────────────────────────────────
def test_기본은_관측_전용이라_0건_지운다(자리):
    r = tile_reclaim.run_pass(previews_root=자리["previews"], storage_root=자리["storage"])
    assert r.applied is False
    assert r.removed == ()
    assert r.unreachable == 1, "관측 전용이어도 **세기는 한다**"
    assert 자리["dead_path"].exists()


def test_설정_기본값이_관측_전용이고_상한과_주기가_박혀_있다(monkeypatch):
    from colab_viz.kernel import config as cfg

    for name in ("COLAB_VIZ_TILE_RECLAIM_APPLY", "COLAB_VIZ_TILE_RECLAIM_MAX_KEYS",
                 "COLAB_VIZ_TILE_RECLAIM_INTERVAL_SECONDS"):
        monkeypatch.delenv(name, raising=False)
    s = cfg.load_settings()
    assert s.tile_reclaim_apply is False, "선언이 없으면 지우지 않는다"
    assert s.tile_reclaim_max_keys == cfg.DEFAULT_TILE_RECLAIM_MAX_KEYS
    assert s.tile_reclaim_interval_seconds == cfg.DEFAULT_TILE_RECLAIM_INTERVAL_SECONDS

    monkeypatch.setenv("COLAB_VIZ_TILE_RECLAIM_APPLY", "true")
    assert cfg.load_settings().tile_reclaim_apply is True
    monkeypatch.setenv("COLAB_VIZ_TILE_RECLAIM_APPLY", "아마도")
    assert cfg.load_settings().tile_reclaim_apply is False, "모르는 값은 꺼짐이다"
    monkeypatch.setenv("COLAB_VIZ_TILE_RECLAIM_MAX_KEYS", "0")
    assert cfg.load_settings().tile_reclaim_max_keys == cfg.DEFAULT_TILE_RECLAIM_MAX_KEYS


# ── ⑸ 계획기는 셋이 아니고 지우는 문은 하나다 ───────────────────────────────────
def test_계획은_같은_계산기_하나를_지난다(자리):
    subjects = tile_liveness.subjects_from_storage(자리["storage"])
    reached = tile_liveness.reach(subjects)
    tiles = tile_liveness.scan_tiles(자리["previews"])
    p = invalidation.tile_reclaim_plan(tiles, reached, previews_root=자리["previews"])
    assert [x.name for x in p.stale] == [자리["dead_path"].name]
    assert [x.name for x in p.kept] == [자리["live_path"].name]
    assert p.regenerate is False and p.trigger is None


def test_계획기의_기본은_여전히_타일을_남긴다(자리):
    """**회귀 방어** — `tile-` 을 남기는 규칙(`〈247〉`)은 명시로 켜지 않는 한 그대로다."""
    produced = [invalidation.StaleCandidate(cache_key=자리["dead_key"],
                                            path=자리["dead_path"])]
    p = invalidation.plan(None, produced=produced, previews_root=자리["previews"])
    assert p.stale == () and len(p.kept) == 1


def test_회수_모듈에_지우는_부름이_없다():
    """음성 — **지우는 문은 `invalidation.apply()` 하나다.**"""
    import ast
    import inspect

    tree = ast.parse(inspect.getsource(tile_reclaim))
    for node in ast.walk(tree):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            node.value.value = ""
    src = ast.unparse(tree)
    for banned in ("unlink(", "rmtree(", "os.remove(", "shutil"):
        assert banned not in src, f"회수 모듈이 스스로 지웠다: {banned}"
    assert "invalidation.apply(" in src


# ── 주체를 원장 없이 모은다 — **디렉터리가 곧 사실이다** ─────────────────────────
def test_자리에서_주체를_모은다_격자는_주체가_아니다(tmp_path):
    up = tmp_path / "storage"
    _body(up, "01M0DATASETA00000000000000", "01M0FILEA000000000000000A", b"x")
    _body(up, "01M0UPLOADB000000000000000", "01M0FILEB000000000000000B", b"y")
    grid = storage_layout.grid_dir(up, "01M0DATASETA00000000000000")
    grid.mkdir(parents=True)
    (grid / "lat.npy").write_bytes(b"g")

    subjects = tile_liveness.subjects_from_storage(up)
    assert sorted(s.file_id for s in subjects) == ["01M0FILEA000000000000000A",
                                                   "01M0FILEB000000000000000B"]
    assert all(s.origin == tile_liveness.ORIGIN_STORAGE for s in subjects)
    a = [s for s in subjects if s.file_id == "01M0FILEA000000000000000A"][0]
    assert a.grid_dir == grid, "격자 자리를 못 물면 후보 키가 하나 줄어 고아가 늘어난다"


def test_자리의_주체가_낳는_키는_고아가_아니다(자리):
    subjects = tile_liveness.subjects_from_storage(자리["storage"])
    r = tile_liveness.reach(subjects)
    v = tile_liveness.grade(자리["live_key"], r)
    assert v.grade != ownership.GRADE_ORPHAN
    assert "등록 여부" in v.reason, "원장 없이 등록 여부를 단정하지 않는다"


# ── ⑹ 루프에 얹는다 — 한 바퀴가 실패해도 죽지 않는다 ────────────────────────────
def _wait(predicate, timeout: float = 10.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return predicate()


def test_루프가_회수를_얹고_주기로_부른다(자리):
    from colab_viz.app import trigger_loop

    class 빈_버스:
        def poll(self):
            return []

        def ack(self, event):      # pragma: no cover - 부를 일이 없다
            raise AssertionError

    job = tile_reclaim.ReclaimJob(previews_root=자리["previews"],
                                  storage_root=자리["storage"],
                                  apply=True, max_keys=10, interval_seconds=0.0)
    loop = trigger_loop.TriggerDrainLoop(빈_버스(), jobs=None, source=None,
                                         interval_seconds=0.01, reclaim=job)
    loop.start()
    try:
        assert _wait(lambda: not 자리["dead_path"].exists()), "루프가 회수를 안 불렀다"
    finally:
        loop.stop()
    assert 자리["live_path"].exists()
    assert job.last_result is not None and job.last_result.ready


def test_회수_한_바퀴가_실패해도_루프는_죽지_않는다():
    from colab_viz.app import trigger_loop

    class 빈_버스:
        def poll(self):
            return []

    class 터지는_회수:
        def __init__(self):
            self.calls = 0

        def run_due(self, now=None):
            self.calls += 1
            raise RuntimeError("회수가 터졌다")

    job = 터지는_회수()
    loop = trigger_loop.TriggerDrainLoop(빈_버스(), jobs=None, source=None,
                                         interval_seconds=0.01, reclaim=job)
    loop.start()
    try:
        assert _wait(lambda: job.calls >= 3), "회수 예외 한 건이 루프를 죽였다"
    finally:
        loop.stop()


def test_주기_전에는_다시_돌지_않는다(자리):
    job = tile_reclaim.ReclaimJob(previews_root=자리["previews"],
                                  storage_root=자리["storage"],
                                  apply=False, max_keys=10, interval_seconds=3600.0)
    assert job.run_due(now=1000.0) is not None
    assert job.run_due(now=1001.0) is None, "매 바퀴 전수 다이제스트를 다시 뜨지 않는다"
    assert job.run_due(now=1000.0 + 3600.0) is not None


# ── 배포가 스위치를 실어 주는가 — 코드에만 있는 스위치는 아무것도 켜지 못한다 ────
def test_배포가_회수_스위치를_실어_준다_그리고_켜진_값을_박지_않는다():
    """`#20`·`#49`·`COLAB_VIZ_TILE_BRANCH` 와 같은 무늬다 — **선언은 코드에, 배선은 배포에.**

    ⚠ **레포에 켜진 값을 박지 않는다** — 셋 다 `${...}` 치환꼴이라 정본은 홈 env 이고,
      비면 관측 전용 · 상한 20 · 주기 3600초(코드 기본값)로 떨어진다.
    """
    import re
    from pathlib import Path

    compose = Path(__file__).resolve().parents[3] / "infra" / "staging" / "compose.i2.yml"
    raw = compose.read_text(encoding="utf-8")
    block = re.search(r"^  viz-render:\n(.*?)(?=^  \S|^volumes:)", raw, re.S | re.M)
    assert block is not None
    for key in ("COLAB_VIZ_TILE_RECLAIM_APPLY", "COLAB_VIZ_TILE_RECLAIM_MAX_KEYS",
                "COLAB_VIZ_TILE_RECLAIM_INTERVAL_SECONDS"):
        m = re.search(rf"^\s+{key}:\s*(.+?)\s*$", block.group(1), re.M)
        assert m is not None, f"compose 의 viz-render 에 {key} 가 없다 — 영영 꺼짐이다"
        assert m.group(1).startswith("${" + key), f"홈 env 를 통과시키지 않는다: {m.group(1)!r}"
        assert m.group(1).endswith(":-}"), f"레포가 켜진 값을 박았다: {m.group(1)!r}"


def test_트리거_집행이_터져도_회수는_돈다():
    """**격리** — 한쪽의 예외가 다른 쪽을 인질로 잡지 않는다."""
    from colab_viz.app import trigger_loop

    class 터지는_버스:
        def poll(self):
            raise RuntimeError("버스가 터졌다")

    class 세는_회수:
        def __init__(self):
            self.calls = 0

        def run_due(self, now=None):
            self.calls += 1
            return None

    job = 세는_회수()
    loop = trigger_loop.TriggerDrainLoop(터지는_버스(), jobs=None, source=None,
                                         interval_seconds=0.01, reclaim=job)
    assert loop.tick() == 0
    assert job.calls == 1, "집행이 터졌다고 회수까지 굶었다"
