"""`Y-1` 트리거 **수신** — D5 가 보낸 사건을 D7 이 받아 자기 산출물만 다시 굽는다.

⭑ **⟨2026-08-31 · 12차 동결 해제 · `PLAN-SoT §9 〈253〉` · Ted RULING ㉗⟩**
`〈247〉` 회차가 세운 것은 **받는 자리(`TriggerPort` Protocol)** 까지였고, 실물 배선이
없어 `Y-1` 이 닫히지 않았다(`03-HANDOFF §4 #55`). 이 파일이 그 자리를 실물로 채운
어댑터(`app/trigger_bus.SpoolTriggerPort`)와 집행(`app/triggers.drain`)을 잰다.

⚠ **자리가 `ports/` 가 아니라 `app/` 인 이유는 게이트가 정했다** — viz-render 의 층은
`app > domains > ports > kernel` 이고, 이 어댑터는 도메인이 선언한 `TriggerPort` 를
만족해야 하므로 **조립 층**에 산다(`import-boundary` red → 이동). 우회가 아니라 자리다.

**경계가 이 파일의 절반이다** —
  · D7 은 D5 의 표·outbox 를 읽지 않는다. 읽는 것은 **발행된 버스**(스풀) 하나다
  · D7 은 트리거를 **발신하지 않는다**(`Y-1` 완료 정의 ⓔ)
  · `〈247〉` — 원본·기준 격자·데이터셋은 **어떤 트리거로도** 다시 만들지 않는다
"""
from __future__ import annotations

import io
import json
import tokenize
from pathlib import Path

import numpy as np
import pytest

from colab_viz.app import triggers as trigger_app
from colab_viz.domains.d7_visualization import invalidation
from colab_viz.kernel import storage_layout
from colab_viz.app import trigger_bus as trigger_port

from conftest import AUTH, make_client

_LAB = "01JQ0000000000000000000001"
_ACC = "01JQ0000000000000000000002"
_TRIGGERS = ("미리보기 뒷단 재실행", "격자 변경", "파일 추가")
_TYPES = ("preview.backend-rerun", "preview.grid-changed", "preview.file-added")


def _repo_root() -> Path:
    for p in Path(__file__).resolve().parents:
        if (p / "contracts" / "events" / "envelope.json").is_file():
            return p
    pytest.fail("레포 루트를 찾지 못했다")


def _envelope(spool: Path, *, event_type: str, trigger: str, upload_id: str,
              event_id: str = "01JQ00000000000000000000E1") -> Path:
    """**D5 가 보낸 것과 같은 모양의 봉투**를 버스에 놓는다 (`contracts/events/**` 축자)."""
    env = {
        "eventId": event_id, "type": event_type, "schemaVersion": "1.0",
        "source": "pipeline-worker", "occurredAt": "2026-08-31T04:20:10.100Z",
        "labId": _LAB, "actorAccountId": _ACC, "uploadId": upload_id,
        "idempotencyKey": f"{event_type}:{upload_id}",
        "delivery": {"attempt": 1, "maxAttempts": 5,
                     "firstPublishedAt": "2026-08-31T04:20:10.200Z",
                     "publishedAt": "2026-08-31T04:20:10.200Z", "redelivery": False},
        "payload": {"trigger": trigger},
    }
    spool.mkdir(parents=True, exist_ok=True)
    p = spool / f"{event_id}.json"
    p.write_text(json.dumps(env, ensure_ascii=False), encoding="utf-8")
    return p


def _render(client, target_id: str) -> dict:
    r = client.post("/viz/v1/renders", headers=AUTH, json={
        "target": {"uploadId": target_id}, "style": {"palette": "단색-파랑"}})
    assert r.status_code == 202, r.text
    return client.get(f"/viz/v1/renders/{r.json()['renderId']}", headers=AUTH).json()


# ── ① 계약 축자 ──────────────────────────────────────────────────────────────
def test_받는_종류와_트리거_이름이_계약_축자다():
    """**오라클은 계약이다** — 소비자가 값 집합을 자기 말로 다시 적지 않는다."""
    events = _repo_root() / "contracts" / "events"
    envelope = json.loads((events / "envelope.json").read_text("utf-8"))
    assert envelope["$defs"]["InvalidationTrigger"]["enum"] == list(_TRIGGERS)
    assert set(_TYPES) <= set(envelope["$defs"]["EventType"]["enum"])
    assert tuple(trigger_port.TRIGGER_BY_EVENT_TYPE) == _TYPES
    assert tuple(trigger_port.TRIGGER_BY_EVENT_TYPE.values()) == _TRIGGERS


# ── ② 수신 ───────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("event_type,trigger", list(zip(_TYPES, _TRIGGERS)))
def test_버스에_놓인_봉투가_트리거_사건이_된다(tmp_path, event_type, trigger):
    port = trigger_port.SpoolTriggerPort(tmp_path / "bus")
    _envelope(tmp_path / "bus", event_type=event_type, trigger=trigger,
              upload_id="01ARZ3NDEKTSV4RRFFQ69G5FAV")
    events = list(port.poll())
    assert [e.trigger for e in events] == [trigger]
    assert events[0].target_id == "01ARZ3NDEKTSV4RRFFQ69G5FAV"


def test_재전달은_한_번만_집행된다(tmp_path):
    """봉투가 두 번 오는 것은 예외가 아니라 정상이다(at-least-once) — **멱등 키가
    거른다.** 소비자가 이것을 안 하면 같은 그림을 두 번 굽는다."""
    bus = tmp_path / "bus"
    port = trigger_port.SpoolTriggerPort(bus)
    _envelope(bus, event_type="preview.file-added", trigger="파일 추가",
              upload_id="01ARZ3NDEKTSV4RRFFQ69G5FAV", event_id="01JQ0000000000000000000AA1")
    first = list(port.poll())
    for e in first:
        port.ack(e)
    _envelope(bus, event_type="preview.file-added", trigger="파일 추가",
              upload_id="01ARZ3NDEKTSV4RRFFQ69G5FAV", event_id="01JQ0000000000000000000AA2")
    assert len(first) == 1
    assert list(port.poll()) == [], "같은 멱등 키의 재전달이 두 번 집행됐다"


def test_ack_하기_전에는_버스에서_사라지지_않는다(tmp_path):
    """**유실 방지.** 처리에 실패한 알림을 먼저 지우면 미리보기가 낡은 채 굳는다."""
    bus = tmp_path / "bus"
    port = trigger_port.SpoolTriggerPort(bus)
    path = _envelope(bus, event_type="preview.grid-changed", trigger="격자 변경",
                     upload_id="01ARZ3NDEKTSV4RRFFQ69G5FAV")
    event = next(iter(port.poll()))
    assert path.exists(), "집행 전에 알림이 사라졌다"
    port.ack(event)
    assert not path.exists()


# ── ③ 집행 — 배선 전체가 실제로 돈다 (㉱-5 집행 증명) ────────────────────────
def test_버스의_봉투_하나가_실제로_재생성을_일으킨다(source_root, put_target, tiny_geotiff,
                                                tmp_path):
    """**모의가 아니다** — 실 파일 · 실 렌더 · 디스크 산출물."""
    bus = tmp_path / "bus"
    client = make_client(source_root, "inline")
    tid = put_target(copy_from=[tiny_geotiff])
    first = _render(client, tid)
    _envelope(bus, event_type="preview.backend-rerun", trigger="미리보기 뒷단 재실행",
              upload_id=tid)
    port = trigger_port.SpoolTriggerPort(bus)
    done = trigger_app.drain(port, jobs=client.app.state.jobs,
                             source=client.app.state.source)
    assert len(done) == 1
    outcome = done[0]
    assert outcome.job.status == "완료"
    assert outcome.job.render_id != first["renderId"]
    assert outcome.plan.trigger == "미리보기 뒷단 재실행"
    for a in outcome.job.artifacts.all():
        assert a.path.exists()
    assert list(bus.glob("*.json")) == [], "집행이 끝났는데 알림이 버스에 남았다"


def test_앱이_버스를_배선으로_받아_자기_자리에_세운다(source_root, tmp_path):
    """**배포 배선이 아니라 코드에 남는 연결이다**(RULING ㉗ 근거) — 자리가 설정으로
    주어지면 앱이 그 자리를 들고 선다."""
    bus = tmp_path / "bus"
    client = make_client(source_root, "inline", trigger_spool=bus)
    assert isinstance(client.app.state.triggers, trigger_port.SpoolTriggerPort)
    plain = make_client(source_root, "inline")
    assert plain.app.state.triggers is None, "자리를 안 주면 지어내지 않는다"


# ── ④ 음성 — 넘지 않는 선 ────────────────────────────────────────────────────
def test_범위_밖_종류는_트리거가_되지_않는다(tmp_path):
    """**음성.** 업로드 파이프라인의 진행 7종은 D7 이 무효화할 사실이 아니다."""
    bus = tmp_path / "bus"
    port = trigger_port.SpoolTriggerPort(bus)
    bus.mkdir(parents=True)
    (bus / "x.json").write_text(json.dumps({
        "eventId": "01JQ0000000000000000000AA3", "type": "upload.ready",
        "schemaVersion": "1.0", "source": "pipeline-worker",
        "occurredAt": "2026-08-31T04:20:10.100Z", "labId": _LAB, "actorAccountId": _ACC,
        "uploadId": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
        "idempotencyKey": "upload.ready:01ARZ3NDEKTSV4RRFFQ69G5FAV",
        "delivery": {"attempt": 1, "maxAttempts": 5,
                     "firstPublishedAt": "2026-08-31T04:20:10.200Z",
                     "publishedAt": "2026-08-31T04:20:10.200Z", "redelivery": False},
        "payload": {"renderable": True, "metadataComplete": True, "gridResolution": []},
    }, ensure_ascii=False), encoding="utf-8")
    assert list(port.poll()) == []


def test_아는_종류에_모르는_트리거가_실려_오면_거절한다(tmp_path):
    """**음성 · 조용히 넘기지 않는다.** 걸러내면 같은 버그가 다음에도 오고 그때는
    아무도 모른다(`invalidation.OutOfScope` 와 같은 자세)."""
    bus = tmp_path / "bus"
    _envelope(bus, event_type="preview.grid-changed", trigger="색 범위 확정",
              upload_id="01ARZ3NDEKTSV4RRFFQ69G5FAV")
    with pytest.raises(invalidation.UnknownTrigger):
        list(trigger_port.SpoolTriggerPort(bus).poll())


def test_그린_적_없는_대상의_트리거는_아무것도_지우지_않는다(source_root, put_target,
                                                    tiny_geotiff, tmp_path):
    """**음성.** 「무효화 범위를 지어내지 않는다」(`JobStore.regenerate` 축자)."""
    bus = tmp_path / "bus"
    client = make_client(source_root, "inline")
    tid = put_target(copy_from=[tiny_geotiff])
    base = storage_layout.target_dir(source_root, tid)
    before = {p.name: p.read_bytes() for p in sorted(base.rglob("*")) if p.is_file()}
    _envelope(bus, event_type="preview.file-added", trigger="파일 추가", upload_id=tid)
    done = trigger_app.drain(trigger_port.SpoolTriggerPort(bus),
                             jobs=client.app.state.jobs, source=client.app.state.source)
    assert done == []
    assert {p.name: p.read_bytes() for p in sorted(base.rglob("*")) if p.is_file()} == before


def test_배선을_지나도_원본과_기준_격자는_한_바이트도_안_바뀐다(source_root, put_target,
                                                       tiny_geotiff, tmp_path):
    """**음성 · `〈247〉` 의 본문을 배선 끝까지 잠근다.** 트리거가 D5 에서 와도
    자동으로 다시 만드는 것은 **보여주기 위한 산출물**뿐이다."""
    bus = tmp_path / "bus"
    client = make_client(source_root, "inline")
    tid = put_target(copy_from=[tiny_geotiff],
                     grid={"lat2d.npy": np.zeros((2, 2)), "lon2d.npy": np.zeros((2, 2))})
    _render(client, tid)
    base = storage_layout.target_dir(source_root, tid)
    before = {p.relative_to(base).as_posix(): p.read_bytes()
              for p in sorted(base.rglob("*")) if p.is_file()}
    assert before, "대상 디렉터리가 비었다 — 시험이 아무것도 안 재고 있다"
    for i, (t, trig) in enumerate(zip(_TYPES, _TRIGGERS)):
        _envelope(bus, event_type=t, trigger=trig, upload_id=tid,
                  event_id=f"01JQ000000000000000000AB{i}")
        trigger_app.drain(trigger_port.SpoolTriggerPort(bus),
                          jobs=client.app.state.jobs, source=client.app.state.source)
    after = {p.relative_to(base).as_posix(): p.read_bytes()
             for p in sorted(base.rglob("*")) if p.is_file()}
    assert after == before, "배선을 지난 재생성이 원본·기준 격자를 건드렸다"


def test_수신부에_D5_원장이나_발신_경로가_없다():
    """**음성 · 불변규칙 1.** D7 이 D5 의 표·outbox 를 읽는 길도, 트리거를 발신하는
    길도 이 단위에 없다. ⚠ 산문이 아니라 **식별자**를 잰다."""
    for mod in (trigger_port, trigger_app):
        src = Path(mod.__file__).read_bytes()
        names = {t.string for t in tokenize.tokenize(io.BytesIO(src).readline)
                 if t.type == tokenize.NAME}
        for forbidden in ("sqlalchemy", "psycopg", "requests", "httpx", "boto3", "kafka",
                          "publish", "outbox", "append_event", "d5_upload",
                          "d5_pipeline_event", "d4_lineage"):
            assert forbidden not in names, f"{Path(mod.__file__).name} 에 {forbidden} 이 들어왔다"


def test_버스_밖의_파일은_지우지_않는다(tmp_path):
    """**음성 · 이중 방어.** 지우는 자리가 버스 안으로 갇혀 있다."""
    bus = tmp_path / "bus"
    bus.mkdir()
    outsider = tmp_path / "원본.bin"
    outsider.write_bytes("원본".encode("utf-8"))
    port = trigger_port.SpoolTriggerPort(bus)
    with pytest.raises(trigger_port.OutsideSpool):
        port._discard(outsider)
    assert outsider.exists()
