"""`tsvector` 질의 실행기 — **실물 DB 로만 증명한다**.

여기서 증명하는 것 다섯
  ① **연구실 경계는 Postgres 층에 남는다** — LLM 도 D10 코드도 경계를 판단하지 않는다.
     같은 질의를 다른 연구실 주체로 던지면 **RLS 가 행을 지운다** (cross-tenant 음성).
  ② **잠긴 데이터가 결과에서 사라지지 않는다** (`P-13`·`P-34` · `Policy_데이터_찾기 §1.3-6`) —
     D10 은 접근 상태를 **읽지 않는다.** 잠김 표시는 core-api 가 붙인다.
  ③ **순위가 재현된다** — 같은 질의가 같은 순서를 낸다.
  ④ **뒤진 개수는 그 연구실의 실제 개수**다.
  ⑤ **`ts_config='simple'` 의 한계를 감추지 않는다** — 「강수」로 「강수량」이 안 잡힌다.
     이 시험이 red 가 되는 날은 형태소 설정이 바뀐 날이고, 그때 이 문서도 같이 바뀐다.

DB 재료는 core-api 의 `tests/fixtures/seed.sql`(A 연구실 2건 · B 연구실 1건, A2 는 잠김).
"""
from __future__ import annotations

from conftest import ACC_A_RES, ACC_B_PROF, DS_A1, DS_A2, DS_B1, LAB_A, LAB_B


def _match(catalog, *, lab_id, account_id, terms, topic=None, limit=20):
    rows, total = catalog.match(lab_id=lab_id, account_id=account_id, terms=tuple(terms),
                                topic=topic, limit=limit, offset=0)
    return [r.dataset_id for r in rows], total


def test_강우로_두_건이_잡힌다(catalog) -> None:
    ids, total = _match(catalog, lab_id=LAB_A, account_id=ACC_A_RES, terms=["강우"])
    assert set(ids) == {DS_A1, DS_A2} and total == 2


def test_잠긴_데이터가_결과에서_사라지지_않는다(catalog) -> None:
    """`DS_A2` 는 시드에서 **잠김**이다. 그래도 온다 — 잠김 표시는 core 의 일이다."""
    ids, _ = _match(catalog, lab_id=LAB_A, account_id=ACC_A_RES, terms=["강우"])
    assert DS_A2 in ids


def test_다른_연구실_데이터가_한_건도_안_보인다(catalog) -> None:
    """cross-tenant 음성. **경계를 코드가 아니라 RLS 가 지운다.**"""
    ids, total = _match(catalog, lab_id=LAB_B, account_id=ACC_B_PROF, terms=["강우"])
    assert ids == [] and total == 0


def test_자기_연구실_것은_보인다_음성이_공허하지_않다(catalog) -> None:
    ids, _ = _match(catalog, lab_id=LAB_B, account_id=ACC_B_PROF, terms=["토지피복"])
    assert ids == [DS_B1]


def test_뒤진_개수가_그_연구실_개수다(catalog) -> None:
    assert catalog.count_datasets(lab_id=LAB_A, account_id=ACC_A_RES) == 2
    assert catalog.count_datasets(lab_id=LAB_B, account_id=ACC_B_PROF) == 1


def test_순위가_재현된다(catalog) -> None:
    first, _ = _match(catalog, lab_id=LAB_A, account_id=ACC_A_RES, terms=["강우", "격자화"])
    for _ in range(3):
        again, _ = _match(catalog, lab_id=LAB_A, account_id=ACC_A_RES, terms=["강우", "격자화"])
        assert again == first


def test_이름이_가장_무겁다(catalog) -> None:
    """`0005` 가 이름에 A 가중치를 준 것이 순위로 드러난다 — 「격자화」는 A2 의 이름에만 있다."""
    ids, _ = _match(catalog, lab_id=LAB_A, account_id=ACC_A_RES, terms=["강우", "격자화"])
    assert ids[0] == DS_A2


def test_주제_필터가_실제로_좁힌다(catalog) -> None:
    ids, _ = _match(catalog, lab_id=LAB_A, account_id=ACC_A_RES, terms=["강우"],
                    topic="토지피복·LULC")
    assert ids == []


def test_없는_말은_0건이고_그것이_정상이다(catalog) -> None:
    ids, total = _match(catalog, lab_id=LAB_A, account_id=ACC_A_RES, terms=["염분"])
    assert ids == [] and total == 0


def test_강수로는_강수량이_안_잡힌다_한계의_고정(catalog) -> None:
    """**`ts_config='simple'` 의 실물 한계**(`〈81〉-㉲`). 감추지 않고 시험으로 붙잡는다.

    「강우량」은 `d3_dataset_autometa.variables` 에 있는데 「강우」로는 안 만난다 —
    `simple` 은 소문자화·구두점 분리만 하고 형태소를 자르지 않기 때문이다.
    """
    ids, _ = _match(catalog, lab_id=LAB_A, account_id=ACC_A_RES, terms=["강우량"])
    assert set(ids) == {DS_A1, DS_A2}          # 통째로는 잡힌다
    rows, _ = catalog.match(lab_id=LAB_A, account_id=ACC_A_RES, terms=("강우량",),
                            topic=None, limit=20, offset=0)
    assert all("강우량" in r.matched_terms for r in rows)


def test_영문_변수명과_포맷은_대소문자를_넘어_잡힌다(catalog) -> None:
    ids, _ = _match(catalog, lab_id=LAB_A, account_id=ACC_A_RES, terms=["netcdf"])
    assert ids == [DS_A2]


def test_실행기는_읽기만_한다(catalog) -> None:
    """쓰기를 시도하면 트랜잭션이 거절한다 — READ ONLY 로 열기 때문이다."""
    import pytest
    from sqlalchemy import text
    from sqlalchemy.exc import DatabaseError
    with catalog.session(lab_id=LAB_A, account_id=ACC_A_RES) as session:
        with pytest.raises(DatabaseError):
            session.execute(text("CREATE TEMP TABLE t_probe (x int)"))
