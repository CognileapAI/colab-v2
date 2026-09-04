"""지도 타일 **생존 판독** — `TL-1` 완료 정의가 잠그는 것을 시험이 못 박는다.

대장 `dev-package/work-items.yaml` `TL-1` `completion_def` 축자 —
  ⑴ **판정 규칙** = 「살아 있는 데이터셋 파일 또는 보류 업로드가 **하나라도** 가리키면 산다」
     ⟹ **첫 주체가 지워져도 타일은 살고, 마지막 주체가 사라질 때만 고아다.**
  ⑵ **입력을 다시 계산한다** — `〈294〉` 가 읽는 쪽에 세운 키 계산을 판독기도 **그대로** 부른다
     (규칙을 두 곳에 적지 않는다 · `CLAUDE.md §3` 불변규칙 1).
  ⑶ **네 등급을 그대로 쓴다** — 타일은 사이드카가 0건이라 **`판정 불가` 로 떨어지지 않아야 한다.**
  ⑷ `ownership.scan()`·`grade()` 는 **고치지 않는다** — 판독기는 별도 진입점이다.
  ⑸ **자기 증명** = **3 주체 공유 표본**을 픽스처로 고정해 「주체 둘을 지워도 살고 셋을 다
     지우면 고아」를 시험이 못 박는다.

⚠ **판독기는 아무것도 지우지 않는다.** 회수는 `invalidation.apply()` 한 자리이고 그 결선은
  대장이 판정한다 — 이 파일에도 지우는 시험이 없다(음성 증명).

⚠ **자리 이름을 시험이 지어내지 않는다** — 굽는 쪽과 같은 규칙(`map_tile_content_key` ＋
  승격된 변환 설정)이 낳은 이름만 쓴다. 시험이 자기 자리를 쓰면 배치는 아무도 안 본다.
"""
from __future__ import annotations

import pytest

from colab_viz.domains.d7_visualization import ownership, tile_liveness, value_lookup
from colab_viz.kernel import storage_layout


# ── 픽스처 재료 ────────────────────────────────────────────────────────────
def _body(root, target_id: str, file_id: str, payload: bytes):
    """접수분 루트의 **본체 한 조각** — 배치는 `layout.json` `keys.본체` 그대로다."""
    d = root / storage_layout.UPLOADS_PREFIX / target_id
    d.mkdir(parents=True, exist_ok=True)
    p = d / file_id
    p.write_bytes(payload)
    return p


def _subject(root, target_id: str, file_id: str, origin: str):
    return tile_liveness.Subject(
        file_id=file_id, origin=origin,
        source=root / storage_layout.UPLOADS_PREFIX / target_id / file_id,
        grid_dir=None)


def _bake_tile(previews_root, source):
    """굽는 쪽이 놓는 그 자리에 그 이름으로 놓는다 — 이름은 **계약이 낳는다.**"""
    key = value_lookup.candidate_tile_keys(source, grid_dir=None)[0][0]
    out = storage_layout.preview_path(previews_root, key, ".tif")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(b"COG")
    return key, out


@pytest.fixture()
def shared_tile(tmp_path):
    """⑸ **3 주체 공유 표본** — 같은 타일 키를 **살아 있는 데이터셋 2개 ＋ 미등록 업로드 1개**가
    가리킨다(`ARTIFACT-OWNER-DESIGN §㉯` 의 실표본 모양).

    같은 바이트이므로 내용 주소가 같다 — **한 자리에 세 주체가 선다.**
    """
    up = tmp_path / "uploads-root"
    pv = tmp_path / "previews"
    payload = b"\x00same-bytes-three-subjects\x01" * 8
    a = _body(up, "01M0DATASETA00000000000000", "01M0FILEA000000000000000A", payload)
    _body(up, "01M0DATASETB00000000000000", "01M0FILEB000000000000000B", payload)
    _body(up, "01M0UPLOADC000000000000000", "01M0FILEC000000000000000C", payload)
    key, _ = _bake_tile(pv, a)
    subjects = [
        _subject(up, "01M0DATASETA00000000000000", "01M0FILEA000000000000000A",
                 tile_liveness.ORIGIN_DATASET),
        _subject(up, "01M0DATASETB00000000000000", "01M0FILEB000000000000000B",
                 tile_liveness.ORIGIN_DATASET),
        _subject(up, "01M0UPLOADC000000000000000", "01M0FILEC000000000000000C",
                 tile_liveness.ORIGIN_UPLOAD),
    ]
    return {"uploads": up, "previews": pv, "key": key, "subjects": subjects}


# ── ⑸ 3 주체 공유 — 「둘을 지워도 살고 셋을 다 지우면 고아」 ─────────────────────
def test_세_주체가_같은_타일을_가리킨다(shared_tile):
    r = tile_liveness.reach(shared_tile["subjects"])
    assert r.reached_by(shared_tile["key"]) == 3, "같은 바이트는 같은 내용 키다"
    assert tile_liveness.grade(shared_tile["key"], r).grade == ownership.GRADE_LIVE


def test_주체_둘을_지워도_타일은_산다(shared_tile):
    """⑴ 축자 — **첫 주체가 지워져도 타일은 산다.**"""
    key = shared_tile["key"]
    # 데이터셋 A 를 뺀다 — B 가 남았다
    r = tile_liveness.reach(shared_tile["subjects"][1:])
    assert tile_liveness.grade(key, r).grade == ownership.GRADE_LIVE
    # 데이터셋 둘 다 뺀다 — 미등록 업로드 하나만 남았다. **고아가 아니다**
    r = tile_liveness.reach(shared_tile["subjects"][2:])
    assert tile_liveness.grade(key, r).grade == ownership.GRADE_UPLOAD_ONLY


def test_주체_셋을_다_지우면_고아다(shared_tile):
    """⑴ 축자 — **마지막 주체가 사라질 때만 고아다.**"""
    other = shared_tile["uploads"] / storage_layout.UPLOADS_PREFIX / "01M0OTHER00000000000000000"
    other.mkdir(parents=True, exist_ok=True)
    (other / "01M0FILEZ000000000000000Z").write_bytes(b"quite-different-bytes")
    r = tile_liveness.reach([_subject(shared_tile["uploads"], "01M0OTHER00000000000000000",
                                      "01M0FILEZ000000000000000Z",
                                      tile_liveness.ORIGIN_DATASET)])
    v = tile_liveness.grade(shared_tile["key"], r)
    assert v.grade == ownership.GRADE_ORPHAN


# ── ⑵ 키를 다시 계산한다 — 규칙을 두 곳에 적지 않는다 ────────────────────────────
def test_판독기와_값조회가_같은_키_계산을_쓴다(tmp_path):
    src = _body(tmp_path, "01M0DATASETA00000000000000", "01M0FILEA000000000000000A", b"bytes")
    assert value_lookup.candidate_tile_keys(src, grid_dir=None) == \
        tile_liveness.candidate_tile_keys(src, grid_dir=None)
    assert value_lookup.candidate_tile_keys.__module__ == tile_liveness.__name__, \
        "값 조회가 판독기의 계산을 **그대로** 부른다 — 사본을 들면 그것이 세 번째 규칙이다"


def test_변환_설정이_갈리면_옛_키는_닿지_않는다(tmp_path):
    """캐시 키가 갈린 자리 = `〈312〉` 가 실측한 그 무늬. **옛 키는 고아로 뜬다.**"""
    up, pv = tmp_path / "u", tmp_path / "p"
    src = _body(up, "01M0DATASETA00000000000000", "01M0FILEA000000000000000A", b"bytes")
    old = storage_layout.map_tile_content_key(
        sourceDigest=value_lookup.file_digest(src), sourceByteSize=src.stat().st_size,
        gridDigest=storage_layout.GRID_DIGEST_EMBEDDED, conversionKind="continuous",
        overviewResampling="blockavg",   # ⚠ 옛 설정 — 지금 규약이 낳지 않는 이름이다
        compression=storage_layout.MAP_TILE_COMPRESSION)
    storage_layout.preview_path(pv, old, ".tif").parent.mkdir(parents=True, exist_ok=True)
    storage_layout.preview_path(pv, old, ".tif").write_bytes(b"COG")
    new, _ = _bake_tile(pv, src)
    assert old != new

    r = tile_liveness.reach([_subject(up, "01M0DATASETA00000000000000",
                                      "01M0FILEA000000000000000A",
                                      tile_liveness.ORIGIN_DATASET)])
    tiles = tile_liveness.scan_tiles(pv)
    t = tile_liveness.tally(tiles, r)
    assert t.counts[ownership.GRADE_LIVE] == 1
    assert t.counts[ownership.GRADE_ORPHAN] == 1
    assert tile_liveness.unreachable_keys(tiles, r) == (old,)


# ── ⑶ 네 등급 · 타일은 「판정 불가」로 떨어지지 않는다 ───────────────────────────
def test_등급_이름과_순서가_소유_판정과_같다():
    assert tile_liveness.GRADES == ownership.GRADES


def test_타일은_판정_불가로_떨어지지_않는다(shared_tile):
    """⑶ 축자 — **키 재계산이 사이드카의 자리를 메운다.**"""
    t = tile_liveness.tally(tile_liveness.scan_tiles(shared_tile["previews"]),
                            tile_liveness.reach(shared_tile["subjects"]))
    assert t.counts[ownership.GRADE_UNDECIDABLE] == 0
    assert sum(t.counts.values()) == 1


# ── fail-closed — 못 센 것을 「고아」로 세지 않는다 ──────────────────────────────
def test_주체가_0건이면_판정하지_않는다(shared_tile):
    """대상이 0 인 green 을 만들지 않는다 — 주체가 없으면 **전건이 고아로 뜬다.**"""
    r = tile_liveness.reach([])
    assert not r.is_decidable()
    with pytest.raises(tile_liveness.ReaderNotReady):
        tile_liveness.grade(shared_tile["key"], r)
    with pytest.raises(tile_liveness.ReaderNotReady):
        tile_liveness.tally(tile_liveness.scan_tiles(shared_tile["previews"]), r)


def test_본체를_못_열면_계산_불가이고_고아가_아니다(shared_tile):
    """**제3의 상태다** — 「고아」도 「판정 불가」도 아니고 **판정을 시작하지 않는다.**

    못 연 주체를 조용히 빼면 그 주체가 가리키던 타일이 **고아로 둔갑한다.**
    """
    subjects = list(shared_tile["subjects"])
    subjects[0].source.unlink()
    r = tile_liveness.reach(subjects)
    assert len(r.uncomputable) == 1
    assert r.uncomputable[0].file_id == subjects[0].file_id
    assert not r.is_decidable()
    with pytest.raises(tile_liveness.ReaderNotReady):
        tile_liveness.grade(shared_tile["key"], r)


# ── ⑷ `ownership` 을 고치지 않았다 (음성 증명) ──────────────────────────────────
def test_소유_판정은_여전히_타일을_보지_않는다(shared_tile):
    """⑷ 축자 — `scan()`·`grade()` 는 넓히지 않았다. 판독기는 **별도 진입점**이다."""
    groups = ownership.scan(shared_tile["previews"])
    assert groups and all(g.is_map_tile() for g in groups)
    led = ownership.Ledger(dataset_files=frozenset({"01M0FILEA000000000000000A"}),
                           upload_files=frozenset())
    assert ownership.tally(groups, led).counts == {g: 0 for g in ownership.GRADES}
    assert ownership.orphan_keys(groups, led) == ()


def test_판독기는_지우지_않는다(shared_tile):
    """음성 증명 — 판독기 모듈의 **집행문 어디에도** 지우는 부름이 없다.

    ⚠ 산문(주석·독스트링)은 빼고 센다 — 이 모듈은 「지우지 않는다」를 **말로도** 적어 두므로
    글자만 세면 자기 경고문에 걸린다. 세는 것은 **부름**이다.
    """
    import ast
    import inspect

    tree = ast.parse(inspect.getsource(tile_liveness))
    for node in ast.walk(tree):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            node.value.value = ""          # 독스트링을 비운다
    src = ast.unparse(tree)
    for banned in ("unlink(", "rmtree(", "os.remove(", "shutil", "reclaim",
                   "apply(", "write_text(", "write_bytes(", "mkdir("):
        assert banned not in src, f"판독기는 회수자가 아니다: {banned}"


# ── 나이 — 못 닿는 키는 **언제부터 자리에 있었나** ──────────────────────────────
def test_못_닿는_키에_나이가_붙는다(tmp_path):
    import os
    import time

    up, pv = tmp_path / "u", tmp_path / "p"
    src = _body(up, "01M0DATASETA00000000000000", "01M0FILEA000000000000000A", b"bytes")
    _bake_tile(pv, src)
    stale = storage_layout.preview_path(pv, "tile-" + "0" * 64, ".tif")
    stale.write_bytes(b"COG")
    old = time.time() - 86400 * 30
    os.utime(stale, (old, old))

    r = tile_liveness.reach([_subject(up, "01M0DATASETA00000000000000",
                                      "01M0FILEA000000000000000A",
                                      tile_liveness.ORIGIN_DATASET)])
    rows = tile_liveness.unreachable_rows(tile_liveness.scan_tiles(pv), r)
    assert [x["cache_key"] for x in rows] == ["tile-" + "0" * 64]
    assert rows[0]["age_days"] >= 29


# ── ⑷ 별도 진입점 — 세 상태로 끝난다 ────────────────────────────────────────────
def _run_cli(capsys, previews, storage, subjects_text, monkeypatch):
    import io

    from colab_viz.domains.d7_visualization import tile_liveness_cli as cli

    monkeypatch.setattr("sys.stdin", io.StringIO(subjects_text))
    code = cli.main(["tile-liveness", "--previews", str(previews),
                     "--storage", str(storage), "--subjects", "-"])
    return code, capsys.readouterr()


def _tsv(subjects):
    return "".join(f"{s.origin}\t{s.file_id}\t"
                   f"{storage_layout.UPLOADS_PREFIX}/{s.source.parent.name}/{s.file_id}\n"
                   for s in subjects)


def test_진입점_clean_이면_판정하고_못닿음_0(shared_tile, capsys, monkeypatch):
    code, out = _run_cli(capsys, shared_tile["previews"], shared_tile["uploads"],
                         _tsv(shared_tile["subjects"]), monkeypatch)
    assert code == 0
    assert "::계수::살아 있다\t1" in out.out
    assert "::계수::고아\t0" in out.out
    assert "::못닿음::" not in out.out


def test_진입점_못닿는_타일이_있으면_건수를_드러낸다(shared_tile, capsys, monkeypatch):
    stale = storage_layout.preview_path(shared_tile["previews"], "tile-" + "9" * 64, ".tif")
    stale.write_bytes(b"COG")
    code, out = _run_cli(capsys, shared_tile["previews"], shared_tile["uploads"],
                         _tsv(shared_tile["subjects"]), monkeypatch)
    assert code == 0, "판독이지 판결이 아니다 — 지목하고 끝난다"
    assert "::계수::고아\t1" in out.out
    assert "::못닿음::tile-" + "9" * 64 in out.out


def test_진입점_주체를_못_열면_red_준비다(shared_tile, capsys, monkeypatch):
    """**계산 불가는 green-by-skip 이 아니라 red(준비)다.**"""
    shared_tile["subjects"][0].source.unlink()
    code, out = _run_cli(capsys, shared_tile["previews"], shared_tile["uploads"],
                         _tsv(shared_tile["subjects"]), monkeypatch)
    from colab_viz.domains.d7_visualization import tile_liveness_cli as cli
    assert code == cli.READINESS_EXIT
    assert "red(준비)" in out.err
    assert "::계수::" not in out.out, "판정하지 않은 회차에 계수를 적지 않는다"


def test_진입점_주체_0건도_red_준비다(shared_tile, capsys, monkeypatch):
    code, out = _run_cli(capsys, shared_tile["previews"], shared_tile["uploads"],
                         "# 아무 주체도 없다\n", monkeypatch)
    from colab_viz.domains.d7_visualization import tile_liveness_cli as cli
    assert code == cli.READINESS_EXIT
