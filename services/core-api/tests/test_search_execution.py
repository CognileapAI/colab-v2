"""`tsvector` 질의 실행기 — **실물 DB 로만 증명한다**.

`K4-a` 가 `services/ai-service/tests/test_search_db.py` 에 세운 열두 오라클을 그대로 옮겼다.
**옮긴 이유는 자리이지 내용이 아니다** — 실행기가 D10 에서 D3 의 주인(core-api)으로 왔다
(`CLAUDE.md §3-1` · Ted 판정 2026-08-25 ㈎). 오라클은 한 줄도 약해지지 않는다.

여기서 증명하는 것 여섯
  ① **연구실 경계는 Postgres 층에 남는다** — 같은 질의를 다른 연구실 주체로 던지면
     RLS 가 행을 지운다. 그리고 **그 음성이 공허하지 않다** — B 는 자기 것을 1건 본다.
  ② **잠긴 데이터가 결과에서 사라지지 않는다** (`P-13`·`P-34` · `Policy_데이터_찾기 §1.3-6`).
  ③ **순위가 재현된다** — 같은 질의가 같은 순서를 낸다 (`〈72〉-㉮`).
  ④ **뒤진 개수는 그 연구실의 실제 개수**다.
  ⑤ **`ts_config='simple'` 의 한계를 감추지 않는다** (`〈81〉-㉲`).
  ⑥ **실행기는 읽기만 한다** — `READ ONLY` 트랜잭션이라 쓰기를 Postgres 가 거절한다.
"""
from __future__ import annotations

import pytest
from conftest import ACC_A_RES, ACC_B_PROF, DS_A1, DS_A2, DS_B1, LAB_A, LAB_B
from sqlalchemy import text
from sqlalchemy.exc import DatabaseError

from colab_core.domains import d3_catalog
from colab_core.kernel.auth import Subject
from colab_core.kernel.ids import Ulid
from colab_core.kernel.scope import read_only_scope


def _subject(account_id: str, lab_id: str) -> Subject:
    return Subject(account_id=Ulid(account_id), lab_id=Ulid(lab_id))


def _match(session_factory, *, lab_id, account_id, terms, topic=None, limit=20):
    with read_only_scope(session_factory, _subject(account_id, lab_id)) as session:
        rows, total = d3_catalog.search_datasets(
            session, terms=tuple(terms), topic=topic, limit=limit, offset=0)
    return rows, total


def _ids(session_factory, **kw):
    rows, total = _match(session_factory, **kw)
    return [r.dataset_id for r in rows], total


def test_강우로_두_건이_잡힌다(session_factory) -> None:
    ids, total = _ids(session_factory, lab_id=LAB_A, account_id=ACC_A_RES, terms=["강우"])
    assert set(ids) == {DS_A1, DS_A2} and total == 2


def test_잠긴_데이터가_결과에서_사라지지_않는다(session_factory) -> None:
    """`DS_A2` 는 시드에서 **잠김**이다. 그래도 온다 — 빼면 요청할 상대조차 사라진다."""
    ids, _ = _ids(session_factory, lab_id=LAB_A, account_id=ACC_A_RES, terms=["강우"])
    assert DS_A2 in ids


def test_다른_연구실_데이터가_한_건도_안_보인다(session_factory) -> None:
    """cross-tenant 음성. **경계를 코드가 아니라 RLS 가 지운다.**"""
    ids, total = _ids(session_factory, lab_id=LAB_B, account_id=ACC_B_PROF, terms=["강우"])
    assert ids == [] and total == 0


def test_자기_연구실_것은_보인다_음성이_공허하지_않다(session_factory) -> None:
    """위 음성이 「질의가 원래 0건」이 아님을 같은 주체로 증명한다."""
    ids, _ = _ids(session_factory, lab_id=LAB_B, account_id=ACC_B_PROF, terms=["토지피복"])
    assert ids == [DS_B1]


def test_뒤진_개수가_그_연구실_개수다(session_factory) -> None:
    with read_only_scope(session_factory, _subject(ACC_A_RES, LAB_A)) as s:
        assert d3_catalog.count_datasets(s) == 2
    with read_only_scope(session_factory, _subject(ACC_B_PROF, LAB_B)) as s:
        assert d3_catalog.count_datasets(s) == 1


def test_순위가_재현된다(session_factory) -> None:
    first, _ = _ids(session_factory, lab_id=LAB_A, account_id=ACC_A_RES, terms=["강우", "격자화"])
    for _ in range(3):
        again, _ = _ids(session_factory, lab_id=LAB_A, account_id=ACC_A_RES,
                        terms=["강우", "격자화"])
        assert again == first


def test_이름이_가장_무겁다(session_factory) -> None:
    """`0005` 가 이름에 A 가중치를 준 것이 순위로 드러난다 — 「격자화」는 A2 의 이름에만 있다."""
    ids, _ = _ids(session_factory, lab_id=LAB_A, account_id=ACC_A_RES, terms=["강우", "격자화"])
    assert ids[0] == DS_A2


def test_동점은_식별자_오름차순이다(session_factory) -> None:
    """`ORDER BY rank DESC, d.id ASC`. 두 행의 점수가 같아도 순서가 재현된다."""
    rows, _ = _match(session_factory, lab_id=LAB_A, account_id=ACC_A_RES, terms=["강우"])
    tied = [r.dataset_id for r in rows if r.rank == rows[0].rank]
    assert tied == sorted(tied)


def test_주제_필터가_실제로_좁힌다(session_factory) -> None:
    ids, _ = _ids(session_factory, lab_id=LAB_A, account_id=ACC_A_RES, terms=["강우"],
                  topic="토지피복·LULC")
    assert ids == []


def test_없는_말은_0건이고_그것이_정상이다(session_factory) -> None:
    ids, total = _ids(session_factory, lab_id=LAB_A, account_id=ACC_A_RES, terms=["염분"])
    assert ids == [] and total == 0


def test_긴_낱말도_통째로는_잡힌다(session_factory) -> None:
    """`ts_config='simple'` 은 형태소를 안 자르므로 **통째로 같은 낱말**은 언제나 맞는다.

    ⚠ 이 시험의 이름이 한때 「강수로는 강수량이 안 잡힌다 — 한계의 고정」이었다.
    **그 한계는 `〈89〉` 가 접두 질의로 풀었다** — 아래 묶음이 그 사실을 잰다.
    남은 것은 여기서 재는 성질 하나뿐이다: 통째로 같으면 맞는다.
    """
    rows, _ = _match(session_factory, lab_id=LAB_A, account_id=ACC_A_RES, terms=["강우량"])
    assert {r.dataset_id for r in rows} == {DS_A1, DS_A2}
    assert all("강우량" in r.matched_terms for r in rows)


# ─────────────────────────────────────────────────────────────────────────────
# 〈89〉 — **한국어 매칭 보강.** ① 접두 질의 ② `pg_trgm` 보조 팔 ③ 순위는 그대로 결정적
#
# 개정 전에는 이 자리에 「한계의 고정」 시험 하나가 있었다. 정본이 바뀌었으므로
# (`PLAN-SoT §9-〈89〉`) 시험도 바뀐다 — **한계를 재던 자리에서 이제 능력을 잰다.**
# 그리고 새 한계를 새로 고정한다: 매칭은 표기를 넘지 못하고, 그 일은 사전·그래프의 것이다.
# ─────────────────────────────────────────────────────────────────────────────

def test_접두_질의가_더_긴_낱말을_잡는다(session_factory) -> None:
    """**「격자」로 「격자화」가 잡힌다.** 개정 전에는 0건이었다 — `0005` 가 스스로 적어 둔 자리."""
    ids, _ = _ids(session_factory, lab_id=LAB_A, account_id=ACC_A_RES, terms=["격자"])
    assert ids == [DS_A2]


def test_접두_질의는_이름_밖의_자리에도_닿는다(session_factory) -> None:
    """「토지」 → `B 토지피복 원자료`. 연구실 B 의 자기 것이다(경계는 그대로 산다)."""
    ids, _ = _ids(session_factory, lab_id=LAB_B, account_id=ACC_B_PROF, terms=["토지"])
    assert ids == [DS_B1]


def test_접두는_앞에서만_먹는다_아무_데나_걸리지_않는다(session_factory) -> None:
    """`:*` 는 **접두**다. 낱말 가운데 조각으로는 안 잡힌다 — 안 그러면 「자화」가 전부를 문다."""
    ids, total = _ids(session_factory, lab_id=LAB_A, account_id=ACC_A_RES, terms=["자화"])
    assert ids == [] and total == 0


def test_비슷한_말은_tsvector_가_0건일_때만_받는다(session_factory) -> None:
    """**띄어쓰기를 안 한 질의.** 「강우격자화」는 한 낱말이라 접두로도 못 넘고, 유사도가 받는다."""
    rows, total = _match(session_factory, lab_id=LAB_A, account_id=ACC_A_RES,
                         terms=["강우격자화"])
    assert [r.dataset_id for r in rows] == [DS_A2] and total == 1
    assert rows[0].where == ("이름(비슷한 말)",), \
        "정확히 맞은 것과 비슷한 것을 같은 말로 적으면 근거가 과장이 된다."


def test_비슷한_말도_연구실_경계를_못_넘는다(session_factory) -> None:
    """보조 팔이 생겼다고 경계가 얇아지지 않는다 — 같은 RLS 아래에서 돈다."""
    ids, total = _ids(session_factory, lab_id=LAB_A, account_id=ACC_A_RES,
                      terms=["토지피복원자료"])
    assert ids == [] and total == 0
    ids, _ = _ids(session_factory, lab_id=LAB_B, account_id=ACC_B_PROF,
                  terms=["토지피복원자료"])
    assert ids == [DS_B1], "음성이 공허하지 않다 — 자기 연구실에서는 잡힌다."


def test_tsvector_가_잡으면_유사도가_결과를_건드리지_않는다(session_factory) -> None:
    """**보조 팔이지 대체가 아니다** (`〈89〉-㉮②`). 「강우」는 tsvector 가 잡으므로 2건 그대로다."""
    ids, total = _ids(session_factory, lab_id=LAB_A, account_id=ACC_A_RES, terms=["강우"])
    assert set(ids) == {DS_A1, DS_A2} and total == 2


def test_안_닮은_말은_여전히_0건이고_그것이_정상이다(session_factory) -> None:
    """유사도가 **아무 말이나 받아 주지 않는다.** 문턱 아래는 없는 것이다."""
    ids, total = _ids(session_factory, lab_id=LAB_A, account_id=ACC_A_RES, terms=["염분측정"])
    assert ids == [] and total == 0


def test_비슷한_말_순위도_재현된다(session_factory) -> None:
    """`유사도 DESC, 식별자 ASC` — 둘 다 DB 가 낸 값이라 같은 질의가 같은 순서를 낸다."""
    first, _ = _ids(session_factory, lab_id=LAB_A, account_id=ACC_A_RES, terms=["강우격자화"])
    for _ in range(3):
        again, _ = _ids(session_factory, lab_id=LAB_A, account_id=ACC_A_RES,
                        terms=["강우격자화"])
        assert again == first


def test_매칭은_표기를_넘지_못한다_새_한계의_고정(session_factory) -> None:
    """**「강우량」으로 「강수」를 부를 수 없다.** 접두도 유사도도 그 일을 못 한다.

    감추지 않고 붙잡아 둔다 — 그 일은 사전(D9)과 그래프(`K4-b`)의 몫이고, 매칭을 더 늘려
    풀려고 하면 관련도 막대가 전부 같은 길이가 되는 자리로 간다 (`§D-6` 과 같은 실패 모양).
    """
    rows, _ = _match(session_factory, lab_id=LAB_A, account_id=ACC_A_RES, terms=["강우량"])
    assert all(r.where != ("이름(비슷한 말)",) for r in rows), \
        "이름에 「강우량」이 없는데 유사도로 걸렸다면 문턱이 너무 낮다."


def test_영문_변수명과_포맷은_대소문자를_넘어_잡힌다(session_factory) -> None:
    ids, _ = _ids(session_factory, lab_id=LAB_A, account_id=ACC_A_RES, terms=["netcdf"])
    assert ids == [DS_A2]


def test_맞은_자리를_행마다_돌려준다(session_factory) -> None:
    """근거 한 줄의 재료다 — **안 맞은 말·안 맞은 자리를 적지 않으려고** 행마다 받는다."""
    rows, _ = _match(session_factory, lab_id=LAB_A, account_id=ACC_A_RES, terms=["netcdf"])
    assert rows[0].where and all(w for w in rows[0].where)


def test_검색어가_비면_질의를_던지지_않는다(session_factory) -> None:
    ids, total = _ids(session_factory, lab_id=LAB_A, account_id=ACC_A_RES, terms=[" "])
    assert ids == [] and total == 0


def test_실행기는_읽기만_한다(session_factory) -> None:
    """쓰기를 시도하면 트랜잭션이 거절한다 — `READ ONLY` 로 열기 때문이다."""
    with read_only_scope(session_factory, _subject(ACC_A_RES, LAB_A)) as session:
        with pytest.raises(DatabaseError):
            session.execute(text("CREATE TEMP TABLE t_probe (x int)"))
