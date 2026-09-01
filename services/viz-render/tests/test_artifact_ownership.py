"""소유 대조 — **사이드카 `sources`(fileId) → 원장**. `A-1` 갈래 B(게이트 대조) 단계 4~7.

이 파일이 못 박는 것 넷.
1. **네 등급**(살아 있다 / 접수분에만 닿는다 / 고아 / 판정 불가)의 판정 규칙 하나.
2. ⚠ **덫 ①** — `baked_for` 를 「현재 소유」로 읽지 않는다. 등록 전환 뒤 낡는 값이라
   그것으로 판정하면 **등록된 대상이 전부 불일치로 뜬다**(대장 `A-1` `note` 축자).
   판정 입력은 `sources` 와 원장뿐이고, 이 파일이 그것을 **변이로** 증명한다.
3. ⚠ **덫 ②** — `sidecarVersion`·`baked_for` 가 없는 구판은 **「구판 · 판정 보류」**이지
   「고아」가 아니다. **없는 필드를 근거로 지우면 그것이 오삭제다.**
4. **회수는 고아 등급만** 지우고 집행은 `invalidation.apply()` 한 자리다(완료 정의 ⑶⑸).
   접수분 루트·`tile-` 키는 손대지 않는다(⑷ · 음성 시험).
"""
from __future__ import annotations

import json

import pytest

from colab_viz.domains.d7_visualization import invalidation, ownership

_FID_REG = "01M0Y1WK2J4E8JPFTXDMN1C37X"   # 원장 d3_file 에 있다 = 등록된 데이터셋의 파일
_FID_UP = "01M0Y1WK77ZM3FRYDWTJ9451XY"    # d5_upload_file 에만 있다 = 접수분
_FID_GONE = "01M0Y1WKZZZZZZZZZZZZZZZZZZ"  # 어느 표에도 없다

LEDGER = ownership.Ledger(dataset_files=frozenset({_FID_REG}),
                          upload_files=frozenset({_FID_REG, _FID_UP}))


def _doc(**over) -> dict:
    doc = {"sidecarVersion": 2, "name": "k.png", "layer": "지도형",
           "source": _FID_REG, "sources": [_FID_REG],
           "baked_for": {"target_id": "01J0UPLOAD00000000000000", "is_upload": True}}
    doc.update(over)
    return doc


def _group(tmp_path, key: str, doc: dict | None, *, suffixes=(".png", ".json")):
    paths = []
    for s in suffixes:
        p = tmp_path / f"{key}{s}"
        p.write_bytes(json.dumps(doc, ensure_ascii=False).encode() if s == ".json" else b"\x89PNG")
        paths.append(p)
    return ownership.ArtifactGroup(cache_key=key, paths=tuple(paths), sidecar=doc)


# ── 네 등급 ────────────────────────────────────────────────────────────────
def test_등록된_데이터셋의_파일이면_살아_있다(tmp_path):
    g = _group(tmp_path, "k1", _doc())
    assert ownership.grade(g, LEDGER).grade == ownership.GRADE_LIVE


def test_접수분에만_있으면_고아가_아니라_접수분_등급이다(tmp_path):
    g = _group(tmp_path, "k2", _doc(source=_FID_UP, sources=[_FID_UP]))
    assert ownership.grade(g, LEDGER).grade == ownership.GRADE_UPLOAD_ONLY


def test_어느_표에도_없으면_고아다(tmp_path):
    g = _group(tmp_path, "k3", _doc(source=_FID_GONE, sources=[_FID_GONE]))
    assert ownership.grade(g, LEDGER).grade == ownership.GRADE_ORPHAN


def test_조각_하나라도_살아_있으면_그_벌은_살아_있다(tmp_path):
    """한 렌더가 조각 여럿을 병합한다 — `sources` 배열을 실은 이유다."""
    g = _group(tmp_path, "k4", _doc(source=_FID_GONE, sources=[_FID_GONE, _FID_REG]))
    assert ownership.grade(g, LEDGER).grade == ownership.GRADE_LIVE


# ── ⚠ 덫 ② — 구판은 「고아」가 아니라 「판정 보류」다 ────────────────────────
@pytest.mark.parametrize("doc", [
    None,                                                   # 사이드카 자체가 없다
    {"name": "k.png", "source": "01M0Y1WKZZZZZZZZZZZZZZZZZZ"},   # 구판(판 번호 없음)
    {"sidecarVersion": 2, "name": "k.png", "source": _FID_GONE},  # baked_for 없음
])
def test_구판은_고아로_세지_않는다(tmp_path, doc):
    g = _group(tmp_path, "k5", doc, suffixes=(".png",) if doc is None else (".png", ".json"))
    r = ownership.grade(g, LEDGER)
    assert r.grade == ownership.GRADE_UNDECIDABLE
    # **없는 필드를 근거로 지우면 그것이 오삭제다** — 위 셋은 fileId 가 원장에 없는데도 고아가 아니다
    assert r.grade != ownership.GRADE_ORPHAN


# ── ⚠ 덫 ① — `baked_for` 는 판정 입력이 아니다 ──────────────────────────────
def test_등록_전환된_대상이_불일치로_뜨지_않는다(tmp_path):
    """`baked_for` 는 **구울 때의** 대상(uploadId)이고 지금 소유는 datasetId 다.
    그 둘이 갈린 상태가 등록 전환 뒤의 **정상**이다 — 여기서 불일치를 내면 전건이 뜬다."""
    g = _group(tmp_path, "k6", _doc(baked_for={"target_id": "01J0UPLOAD00000000000000",
                                               "is_upload": True}))
    assert ownership.grade(g, LEDGER).grade == ownership.GRADE_LIVE


def test_baked_for_를_아무_값으로_바꿔도_등급이_변하지_않는다(tmp_path):
    """변이 증명 — 판정 입력이 `sources` ＋ 원장뿐임을 값으로 보인다."""
    base = ownership.grade(_group(tmp_path, "k7", _doc()), LEDGER).grade
    for bogus in ({"target_id": "01ZZZZZZZZZZZZZZZZZZZZZZZZ", "is_upload": False},
                  {"target_id": "", "is_upload": True}, {}):
        g = _group(tmp_path, "k7b", _doc(baked_for=bogus))
        assert ownership.grade(g, LEDGER).grade == base


# ── 규약 위반은 조용히 넘기지 않는다 ────────────────────────────────────────
def test_판_번호는_2_인데_sources_가_비면_예외다(tmp_path):
    g = _group(tmp_path, "k8", _doc(sources=[], source=""))
    with pytest.raises(ownership.SidecarContractViolation):
        ownership.grade(g, LEDGER)


def test_원장이_구조적으로_비면_판정을_시작하지_않는다():
    """0 을 「없다」로 읽어 전건을 고아로 세는 것이 이 레포가 이미 겪은 파괴적 오판이다."""
    empty = ownership.Ledger(dataset_files=frozenset(), upload_files=frozenset())
    assert empty.is_structurally_empty()
    assert not LEDGER.is_structurally_empty()


# ── 계수 ────────────────────────────────────────────────────────────────────
def test_네_등급_계수가_회차마다_같다(tmp_path):
    groups = [_group(tmp_path, "c1", _doc()),
              _group(tmp_path, "c2", _doc(source=_FID_UP, sources=[_FID_UP])),
              _group(tmp_path, "c3", _doc(source=_FID_GONE, sources=[_FID_GONE])),
              _group(tmp_path, "c4", None, suffixes=(".png",))]
    a = ownership.tally(groups, LEDGER)
    b = ownership.tally(groups, LEDGER)
    assert a.counts == b.counts
    assert a.counts == {ownership.GRADE_LIVE: 1, ownership.GRADE_UPLOAD_ONLY: 1,
                        ownership.GRADE_ORPHAN: 1, ownership.GRADE_UNDECIDABLE: 1}
    # 회수 전 전수 스냅숏 — 키·확장자·크기·사이드카 source (완료 정의 ⑸)
    snap = ownership.snapshot_rows(groups, LEDGER)
    assert len(snap) == 7   # c1~c3 두 파일씩 + c4 한 파일
    assert set(snap[0]) == {"cache_key", "extension", "size_bytes", "source", "grade"}


# ── ⑶⑸ 회수는 고아만 · 집행은 invalidation.apply() 한 자리 ──────────────────
def test_회수_계획은_고아만_치우고_나머지는_kept_다(tmp_path):
    root = tmp_path
    groups = [_group(root, "r1", _doc()),
              _group(root, "r2", _doc(source=_FID_GONE, sources=[_FID_GONE])),
              _group(root, "r3", None, suffixes=(".png",))]
    plan = invalidation.reclaim_plan(groups, LEDGER, previews_root=root)
    assert plan.trigger is None and plan.regenerate is False
    assert {p.name for p in plan.stale} == {"r2.png", "r2.json"}
    assert {p.name for p in plan.kept} == {"r1.png", "r1.json", "r3.png"}
    removed = invalidation.apply(plan, previews_root=root)
    assert {p.name for p in removed} == {"r2.png", "r2.json"}
    assert (root / "r1.png").exists() and (root / "r3.png").exists()


# ── ⑷ 음성 시험 — 접수분 루트·데이터셋 무접촉 · `tile-` 은 kept ──────────────
def test_지도_타일은_고아_모양이어도_kept_다(tmp_path):
    """`tile-` 은 D5 가 구운 것이다 — 사이드카가 없다고 지우면 남의 산출물을 지운다."""
    g = _group(tmp_path, "tile-abc", None, suffixes=(".tif",))
    plan = invalidation.reclaim_plan([g], LEDGER, previews_root=tmp_path)
    assert plan.stale == () and [p.name for p in plan.kept] == ["tile-abc.tif"]


def test_접수분_루트의_파일은_회수_계획에_들어가지_못한다(tmp_path):
    """`〈247〉` 경계 — 원본·기준 격자·데이터셋은 어떤 트리거로도 지우지 않는다."""
    previews = tmp_path / "previews"; previews.mkdir()
    uploads = tmp_path / "uploads" / "01J0TARGET00000000000000"; uploads.mkdir(parents=True)
    g = _group(uploads, "u1", _doc(source=_FID_GONE, sources=[_FID_GONE]))
    with pytest.raises(invalidation.OutOfScope):
        invalidation.reclaim_plan([g], LEDGER, previews_root=previews)
    assert (uploads / "u1.png").exists(), "거절 뒤에도 접수분은 그대로여야 한다"


def test_회수_집행은_미리보기_루트_밖을_거절한다(tmp_path):
    previews = tmp_path / "previews"; previews.mkdir()
    outside = tmp_path / "uploads"; outside.mkdir()
    (outside / "x.png").write_bytes(b"x")
    bad = invalidation.InvalidationPlan(trigger=None, target_id="",
                                        stale=(outside / "x.png",), kept=(), regenerate=False)
    with pytest.raises(invalidation.OutOfScope):
        invalidation.apply(bad, previews_root=previews)
    assert (outside / "x.png").exists()
