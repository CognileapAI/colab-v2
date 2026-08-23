"""`§6-2` 음성 시험 3부류를 **파이프라인 경로에** 문다 (실물 62건 전수).

부류 ①(진짜 COG 6건)만으로 세운 시험은 **타일링 단독 판정으로도 green** 이라 규칙을 작동시키지
못한다. 그래서 세 부류를 다 쓴다 — 진짜 COG 6 · 타일만 16 · 스트립 40 (`DATA-REFERENCE §4`).

  음성 ①-㉮  진짜 COG 6건이 **우리 산출물로 기록되지 않는다** (`DR-2`)
  음성 ①-㉯  타일만 16건 — **타일링 단독 판정이 red** (`〈63〉-㉯`: 정상 입력이다)
  양성 ①-㉰  스트립 40건이 정상 통과하고 **우리 산출물이 생긴다**
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from colab_pipeline.d5.tiff_probe import classify_tiff
from colab_pipeline.domains.d5_ingestion import (
    IngestionService,
    UploadFileWork,
    UploadWork,
)
from memory_ledger import MemoryLedger

pytestmark = pytest.mark.e2e

_ENV = "COLAB_REFERENCE_DATA"
_LAB = "01JQ0000000000000000000001"
_ACC = "01JQ0000000000000000000002"
_UPL = "01JQ0000000000000000000003"
_FID = "01JQ00000000000000000000F1"


def _root() -> Path:
    v = os.environ.get(_ENV)
    if not v or not Path(v).is_dir():
        pytest.fail(f"{_ENV} 가 원천 디렉터리를 가리키지 않는다 — E2E 는 skip 하지 않는다")
    return Path(v)


def _all_tifs() -> list[Path]:
    return sorted(p for p in _root().rglob("*.tif") if p.is_file())


def _cohorts() -> dict[str, list[Path]]:
    out: dict[str, list[Path]] = {"cog": [], "tiled-only": [], "stripped": []}
    for p in _all_tifs():
        out[classify_tiff(p)].append(p)
    return out


def _naive_tiling_alone(path: Path) -> str:
    """반례용 — 「타일링 있으면 COG」. 이 규칙이 무엇을 틀리는지 실물로 보인다."""
    from colab_pipeline.d5.tiff_probe import _read_ifds
    return "cog" if _read_ifds(path).main_tiled else "stripped"


def test_source_corpus_splits_into_the_three_measured_cohorts():
    c = _cohorts()
    assert (len(c["cog"]), len(c["tiled-only"]), len(c["stripped"])) == (6, 16, 40)


def test_tiling_alone_rule_disagrees_on_exactly_the_sixteen():
    """부류 ① 만으로 세운 시험이 왜 규칙을 못 지키는지 — 급소는 부류 ② 에 있다."""
    c = _cohorts()
    disagree = [p for p in _all_tifs() if _naive_tiling_alone(p) != classify_tiff(p)]
    assert sorted(disagree) == sorted(c["tiled-only"])
    assert len(disagree) == 16


def _run(path: Path, tmp_path: Path):
    ledger = MemoryLedger()
    ledger.accept(upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC)
    svc = IngestionService(ledger)
    return svc.process_upload(UploadWork(
        upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC, workdir=tmp_path,
        files=[UploadFileWork(file_id=_FID, path=path, kind="본체", file_name=path.name)],
    ))


def test_negative_real_cog_six_are_never_recorded_as_our_artifact(tmp_path):
    """음성 ①-㉮ — 사람이 올린 COG 6건. 파이프라인 경로에서 산출물이 생기지 않는다."""
    cogs = _cohorts()["cog"]
    assert len(cogs) == 6
    for i, p in enumerate(cogs):
        res = _run(p, tmp_path / f"cog{i}")
        assert res.artifacts == [], (p.name, res.artifacts)
        assert res.files[_FID].input_cog_class == "cog"
        built = [e for e in res.events if e["type"] == "preview.cog-built"]
        assert built and built[0]["payload"]["fileIds"] == [_FID]
        assert [e["type"] for e in res.events][-1] == "upload.ready"


def test_negative_tiled_only_sixteen_are_normal_input_not_our_product(tmp_path):
    """음성 ①-㉯ — 타일만 16건. 타일링 단독 판정이면 여기서 red 다 (`〈63〉-㉯`)."""
    tiled = _cohorts()["tiled-only"]
    assert len(tiled) == 16
    for i, p in enumerate(tiled):
        assert _naive_tiling_alone(p) == "cog"          # 순진한 규칙은 「우리 산출물」이라 말한다
        res = _run(p, tmp_path / f"t{i}")
        assert res.files[_FID].input_cog_class == "tiled-only", p.name
        # 정상 입력이므로 우리가 COG 를 **만든다** — 이미-COG 로 오인하면 안 만든다
        assert len(res.artifacts) == 1, (p.name, res.artifacts)
        assert str(res.artifacts[0].path) != str(p)
        assert [e["type"] for e in res.events][-1] == "upload.ready"


def test_positive_stripped_forty_pass_and_produce_our_artifact(tmp_path):
    """양성 ①-㉰ — 스트립 40건."""
    stripped = _cohorts()["stripped"]
    assert len(stripped) == 40
    for i, p in enumerate(stripped):
        res = _run(p, tmp_path / f"s{i}")
        assert res.files[_FID].input_cog_class == "stripped", p.name
        assert len(res.artifacts) == 1, p.name
        assert [e["type"] for e in res.events][-1] == "upload.ready"
