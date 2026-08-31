"""`Y-1` 트리거 **발신** — D5 가 「미리보기 재료가 바뀌었다」를 내보낸다.

⭑ **⟨2026-08-31 · 12차 동결 해제 · `PLAN-SoT §9 〈253〉` · Ted RULING ㉗⟩**
받는 자리(`viz-render` 의 `TriggerPort`)는 `〈247〉` 회차에 이미 섰고, **없던 것은 보내는
쪽**이었다(`03-HANDOFF §4 #55`). 우회로 둘이 막혀 있어서(D7 이 D5 표를 직접 읽으면
불변규칙 1 위반 · 이벤트 계약은 종류 추가가 곧 계약 개정) **계약을 늘려서** 열었다.

오라클은 **계약 축자**다 — 이 파일은 값 집합을 다시 적지 않고 `contracts/events/**` 를
읽어 대조하고, 봉투는 `event_validator`(`conftest.py`)가 계약으로 검증한다.

**경계**(`Y-1` 완료 정의 ⓔ) — 발신은 D5, 무효화·재생성은 D7 이다. 이 파일이 단언하는
것은 **발신뿐**이고, D5 는 어느 산출물을 지울지 말하지 않는다.
"""
from __future__ import annotations

import json

import numpy as np
import pytest

from colab_pipeline.d5 import events as ev
from colab_pipeline.domains.d5_ingestion import (
    IngestionService,
    UploadFileWork,
    UploadWork,
)
from fixture_builders import make_readable_geotiff
from memory_ledger import MemoryLedger

_LAB = "01JQ0000000000000000000001"
_ACC = "01JQ0000000000000000000002"
_UPL = "01JQ0000000000000000000003"
_F1 = "01JQ00000000000000000000F1"
_F2 = "01JQ00000000000000000000F2"
_G1 = "01JQ00000000000000000000G1"
_G2 = "01JQ00000000000000000000G2"

#: 대장 축자 — `WORK-UNITS §10.2-b` `Y-1` 행(첫째 이름은 `〈206〉`-㉮ 로 바뀌었다).
_TRIGGERS = ("미리보기 뒷단 재실행", "격자 변경", "파일 추가")
_TYPES = ("preview.backend-rerun", "preview.grid-changed", "preview.file-added")


# ── 도우미 ───────────────────────────────────────────────────────────────────
def _ledger_with_ready_upload() -> MemoryLedger:
    """**이미 한 번 준비를 마친 업로드.** 트리거 3종은 전부 「이미 선 미리보기가 낡았다」
    는 뜻이라, 첫 접수 처리에는 나가지 않는다(아래 음성 시험)."""
    ledger = MemoryLedger()
    ledger.accept(upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC)
    ledger.record_status(_UPL, ready=True)
    return ledger


def _work(tmp_path, files, sub="work") -> UploadWork:
    return UploadWork(upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC,
                      workdir=tmp_path / sub, files=files)


def _grid_pair(tmp_path):
    lat, lon = tmp_path / "lat2d.npy", tmp_path / "lon2d.npy"
    np.save(lat, np.zeros((2, 2), dtype="float64"))
    np.save(lon, np.ones((2, 2), dtype="float64"))
    return [UploadFileWork(file_id=_G1, path=lat, kind="기준 격자 파일", file_name=lat.name),
            UploadFileWork(file_id=_G2, path=lon, kind="기준 격자 파일", file_name=lon.name)]


def _stale(res) -> list[str]:
    return [e["payload"]["trigger"] for e in res.events if e["type"] in _TYPES]


# ── ① 계약 축자 ──────────────────────────────────────────────────────────────
def test_이벤트_종류는_계약이_정하고_코드는_옮겨_적지_않는다(repo_root):
    """`EVENT_TYPES` 가 계약의 `EventType` 열거와 **집합으로도 순서로도** 같다."""
    envelope = json.loads((repo_root / "contracts/events/envelope.json").read_text("utf-8"))
    assert list(ev.EVENT_TYPES) == envelope["$defs"]["EventType"]["enum"]
    assert len(ev.EVENT_TYPES) == 10, "7종(E-04) ＋ 3종(D5→D7) 이다"


def test_트리거_이름은_대장_축자이고_계약과_같다(repo_root):
    """**이름을 코드에서 새로 짓지 않는다.** 대장 → 계약 → 코드가 한 값을 본다."""
    envelope = json.loads((repo_root / "contracts/events/envelope.json").read_text("utf-8"))
    assert envelope["$defs"]["InvalidationTrigger"]["enum"] == list(_TRIGGERS)
    assert tuple(ev.TYPE_BY_TRIGGER) == _TRIGGERS
    assert tuple(ev.TYPE_BY_TRIGGER.values()) == _TYPES


@pytest.mark.parametrize("trigger,event_type", list(zip(_TRIGGERS, _TYPES)))
def test_봉투가_계약을_만족한다(event_validator, trigger, event_type):
    """**집행 증명의 1층** — 모의가 아니라 실제로 만든 봉투를 계약으로 검증한다."""
    env = ev.make_envelope(
        event_type=event_type, event_id="01JQ00000000000000000000E1",
        lab_id=_LAB, actor_account_id=_ACC, upload_id=_UPL,
        payload=ev.preview_stale_payload(trigger=trigger))
    event_validator(env)
    assert env["source"] == "pipeline-worker"
    assert env["idempotencyKey"] == f"{event_type}:{_UPL}"


def test_페이로드에_지울_경로나_다른_도메인_식별자를_싣지_않는다():
    """**음성 · 경계.** 알림은 **사실**이지 명령이 아니다 — 발신자가 수신자의 산출물
    배치를 알면 그 순간 D5 가 D7 의 저장소를 아는 것이 된다(`CLAUDE.md §3-1`)."""
    p = ev.preview_stale_payload(trigger="격자 변경")
    assert set(p) == {"trigger"}, f"페이로드가 늘었다: {sorted(p)}"


# ── ② 발신 — 트리거 3종이 각각 실제로 나간다 ────────────────────────────────
def test_뒷단이_다시_돌면_재실행_트리거가_나간다(tmp_path):
    src = make_readable_geotiff(tmp_path / "kwra_output.tif")
    res = IngestionService(_ledger_with_ready_upload()).process_upload(
        _work(tmp_path, [UploadFileWork(file_id=_F1, path=src, kind="본체",
                                        file_name=src.name)]))
    assert "미리보기 뒷단 재실행" in _stale(res)


def test_격자_축이_새로_서면_격자_변경_트리거가_나간다(tmp_path):
    src = make_readable_geotiff(tmp_path / "kwra_output.tif")
    files = [UploadFileWork(file_id=_F1, path=src, kind="본체", file_name=src.name)]
    files += _grid_pair(tmp_path)
    res = IngestionService(_ledger_with_ready_upload()).process_upload(
        _work(tmp_path, files))
    assert "격자 변경" in _stale(res)


def test_처음_보는_본체를_감지하면_파일_추가_트리거가_나간다(tmp_path):
    a = make_readable_geotiff(tmp_path / "a.tif")
    b = make_readable_geotiff(tmp_path / "b.tif")
    ledger = _ledger_with_ready_upload()
    ledger.record_detected_format(_F1, "GeoTIFF")      # 이미 본 조각
    res = IngestionService(ledger).process_upload(_work(tmp_path, [
        UploadFileWork(file_id=_F1, path=a, kind="본체", file_name=a.name),
        UploadFileWork(file_id=_F2, path=b, kind="본체", file_name=b.name),
    ]))
    assert "파일 추가" in _stale(res)


# ── ③ 음성 — 넘지 않는 선 ────────────────────────────────────────────────────
def test_첫_접수_처리에서는_트리거가_하나도_나가지_않는다(tmp_path):
    """**음성 · 이 배선의 뜻이 여기서 갈린다.** 트리거는 「낡았다」는 알림이고,
    아직 아무것도 안 그려진 업로드에는 낡은 것이 없다. 첫 처리에 발신하면 D7 은
    그린 적 없는 대상을 매번 받는다."""
    src = make_readable_geotiff(tmp_path / "kwra_output.tif")
    ledger = MemoryLedger()
    ledger.accept(upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC)
    files = [UploadFileWork(file_id=_F1, path=src, kind="본체", file_name=src.name)]
    files += _grid_pair(tmp_path)
    res = IngestionService(ledger).process_upload(_work(tmp_path, files))
    assert _stale(res) == [], "첫 접수 처리가 트리거를 냈다"


def test_계약에_없는_종류는_봉투가_만들어지지_않는다():
    """**음성.** 종류를 코드로 넓히는 길이 없다 — 넓히려면 계약을 먼저 연다."""
    with pytest.raises(ValueError):
        ev.make_envelope(event_type="preview.palette-changed",
                         event_id="01JQ00000000000000000000E1", lab_id=_LAB,
                         actor_account_id=_ACC, upload_id=_UPL, payload={})


def test_트리거_목록_밖의_이름은_페이로드가_거절한다():
    """**음성.** 「색 범위 확정」은 대장이 트리거로 세지 않았다(`〈74〉`-㉴)."""
    with pytest.raises(ValueError):
        ev.preview_stale_payload(trigger="색 범위 확정")


# ── ④ 전송 — 스풀(이벤트 버스)에 실제로 떨어진다 ────────────────────────────
def test_스풀_발행이_봉투를_파일_하나로_떨어뜨린다(tmp_path, event_validator):
    """**집행 증명의 2층** — 모의가 아니라 디스크에 실물이 남는다."""
    from colab_pipeline.app import worker

    spool = tmp_path / "bus"
    env = ev.make_envelope(
        event_type="preview.grid-changed", event_id="01JQ00000000000000000000E2",
        lab_id=_LAB, actor_account_id=_ACC, upload_id=_UPL,
        payload=ev.preview_stale_payload(trigger="격자 변경"))
    worker.spool_publish(spool)(env)
    dropped = sorted(spool.glob("*.json"))
    assert len(dropped) == 1, f"스풀에 떨어진 것 {len(dropped)}건"
    again = json.loads(dropped[0].read_text("utf-8"))
    event_validator(again)
    assert again == env


def test_스풀에는_D7_종류만_나간다(tmp_path):
    """**음성 · 경계.** 업로드 파이프라인의 내부 진행(7종)은 D7 이 알 일이 아니다 —
    필요 없는 사실을 흘리면 그것이 다음 회차의 결합이 된다."""
    from colab_pipeline.app import worker

    spool = tmp_path / "bus"
    publish = worker.spool_publish(spool)
    for t, payload in (("upload.ready", ev.upload_ready_payload(renderable=True,
                                                               metadata_complete=True)),
                       ("file.crs-normalized", ev.crs_normalized_payload(
                           source_crs=None, target_crs="EPSG:4326",
                           transformed=False, file_ids=[]))):
        publish(ev.make_envelope(event_type=t, event_id="01JQ00000000000000000000E3",
                                 lab_id=_LAB, actor_account_id=_ACC, upload_id=_UPL,
                                 payload=payload))
    assert list(spool.glob("*.json")) == [], "파이프라인 내부 사건이 D7 버스로 샜다"


def test_릴레이가_돌면_스풀과_표준출력_둘_다에_나간다(tmp_path, capsys):
    """**at-least-once 규약은 그대로다** — 스풀이 붙어도 기존 발행자를 대체하지 않는다."""
    from colab_pipeline.app import worker
    from colab_pipeline.domains.d5_ingestion import relay_unpublished

    spool = tmp_path / "bus"
    ledger = _ledger_with_ready_upload()
    src = make_readable_geotiff(tmp_path / "kwra_output.tif")
    IngestionService(ledger).process_upload(_work(tmp_path, [
        UploadFileWork(file_id=_F1, path=src, kind="본체", file_name=src.name)]))
    sent = relay_unpublished(ledger, publish=worker.fan_publish(spool))
    assert sent > 0
    assert len(list(spool.glob("*.json"))) >= 1
    assert "preview.backend-rerun" in capsys.readouterr().out
