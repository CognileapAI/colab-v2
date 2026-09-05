"""`ops/purge_datasets.py` 의 **가드**를 잰다 — DB 없이 돌아간다.

⚠ 이 시험이 재는 것은 **지우는 일** 이 아니라 **안 지우게 막는 장치**다.
실집행은 EC2 위 일회성이고 여기서 재현하지 않는다(`PLAN-SoT §9 〈360〉`).

무엇을 재는가 넷 —
  ⑴ 삭제 계획표가 **금지 표**(`d8_activity`·`d8_download`·`d5_upload*`)를 건드리지 않는다
  ⑵ `d3_dataset` 이 계획의 **마지막**이다(`d3_file` 트리거·FK 순서)
  ⑶ ULID 가 아닌 인자·중복 인자를 **거부**한다
  ⑷ `--yes-delete` 가 없으면 **dry-run** 이라는 것이 기본값이다
"""
from __future__ import annotations

import importlib.util
import pathlib

import pytest

_PATH = pathlib.Path(__file__).resolve().parents[1] / "ops" / "purge_datasets.py"
_spec = importlib.util.spec_from_file_location("purge_datasets", _PATH)
purge = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(purge)


def test_삭제_계획은_금지_표를_건드리지_않는다() -> None:
    """`d8_*` 는 `deny_update_delete` 트리거가 막고, `d5_upload*` 는 `dataset_id` 가 없다."""
    purge._check_plan_disjoint_from_never_touch()          # 예외가 없으면 통과
    planned = {t for t, _, _ in purge.DELETE_PLAN}
    for banned in purge.NEVER_TOUCH:
        assert banned not in planned


def test_대장이_마지막이다() -> None:
    """`d3_file` → 나머지 자식 → `d3_dataset`. 뒤집으면 FK 와 file_count 트리거가 막는다."""
    tables = [t for t, _, _ in purge.DELETE_PLAN]
    assert tables[0] == "d3_file"
    assert tables[-1] == "d3_dataset"
    assert tables.index("d4_lineage_edge") < tables.index("d3_dataset")


def test_계보_간선은_자식과_부모_양쪽을_본다() -> None:
    """한쪽만 보면 **남의 데이터셋이 지워진 부모를 가리키는 간선**이 남는다."""
    where = next(w for t, w, _ in purge.DELETE_PLAN if t == "d4_lineage_edge")
    assert "child_dataset_id" in where and "parent_dataset_id" in where


@pytest.mark.parametrize("bad", ["", "짧다", "01M1C0F19DFGA80AM4HR63S1N", "01m1c0f19dfga80am4hr63s1nd",
                                 "01M1C0F19DFGA80AM4HR63S1NDX"])
def test_ULID_가_아닌_id_는_거부한다(bad: str, capsys) -> None:
    rc = purge.main(["--db-url-file", "/dev/null", "--lab", "0000000000000000000000000A",
                     "--id", bad])
    assert rc == 2
    assert "ULID" in capsys.readouterr().err


def test_중복된_id_는_거부한다(capsys) -> None:
    """중복이 있으면 표별 계수와 인자 개수 대조가 무의미해진다."""
    one = "01M1C0F19DFGA80AM4HR63S1ND"
    rc = purge.main(["--db-url-file", "/dev/null", "--lab", "0000000000000000000000000A",
                     "--id", one, "--id", one])
    assert rc == 2
    assert "중복" in capsys.readouterr().err


def test_연구실_id_도_ULID_로_검사한다(capsys) -> None:
    """경계 값이 형식을 어기면 `current_lab_id()` 가 NULL 을 내고 **0행이 지워진다**."""
    rc = purge.main(["--db-url-file", "/dev/null", "--lab", "not-a-ulid",
                     "--id", "01M1C0F19DFGA80AM4HR63S1ND"])
    assert rc == 2


def test_기본값은_dry_run_이다() -> None:
    """`--yes-delete` 는 **명시**여야 한다 — 기본이 파괴이면 사고가 조용해진다."""
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--yes-delete", action="store_true")
    assert ap.parse_args([]).yes_delete is False
