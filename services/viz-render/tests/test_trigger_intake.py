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
import threading
import time
import tokenize
from pathlib import Path

import numpy as np
import pytest

from colab_viz.app import triggers as trigger_app
from colab_viz.domains.d7_visualization import invalidation
from colab_viz.kernel import storage_layout
from colab_viz.app import trigger_bus as trigger_port
from colab_viz.app import trigger_loop

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


def test_아는_종류에_모르는_트리거가_실려_오면_격리한다(tmp_path):
    """**음성 · 조용히 넘기지 않는다.** 걸러내면 같은 버그가 다음에도 오고 그때는
    아무도 모른다(`invalidation.OutOfScope` 와 같은 자세).

    ⭑ ⟨개정 2026-09-03 · 코드리뷰 #2⟩ **거절의 방식이 바뀌었다.** ／ 종전 문면
    ~~`poll()` 이 `UnknownTrigger` 를 던진다~~ — 그 예외가 **제너레이터 안**에서 터져
    `triggers.drain` 의 `list(port.poll())` 를 통째로 죽였고, 그러면 같은 틱의 **멀쩡한
    봉투까지 한 건도 집행·ack 되지 못한 채** 매 틱 같은 자리에서 다시 터졌다(버전 스큐·
    수동 투입 시). 지금은 **어긋난 봉투 하나만** 버스 안의 격리 자리로 옮기고 사유를
    남긴다 — 조용히 걸러내는 것이 아니라, 나머지를 인질로 잡지 않는 것이다.
    """
    bus = tmp_path / "bus"
    path = _envelope(bus, event_type="preview.grid-changed", trigger="색 범위 확정",
                     upload_id="01ARZ3NDEKTSV4RRFFQ69G5FAV")
    port = trigger_port.SpoolTriggerPort(bus)
    assert list(port.poll()) == [], "계약에 없는 트리거가 사건이 됐다"
    assert not path.exists(), "어긋난 봉투가 버스에 남아 매 틱 다시 터진다"
    quarantined = bus / trigger_port.QUARANTINE_DIRNAME / path.name
    assert quarantined.exists(), "어긋난 봉투를 지워 버렸다 — 증거가 남아야 한다"
    assert len(port.quarantined) == 1
    assert "색 범위 확정" in port.quarantined[0].reason, "사유가 남지 않았다"
    # 격리 자리에 놓인 것은 다음 바퀴에 **다시 집히지 않는다.**
    assert list(port.poll()) == []


def test_어긋난_봉투_하나가_그_틱_전체를_막지_않는다(source_root, put_target, tiny_geotiff,
                                              tmp_path):
    """**코드리뷰 #2 의 형제** — 격리의 요점은 「나머지가 돈다」이다."""
    bus = tmp_path / "bus"
    client = make_client(source_root, "inline")
    tid = put_target(copy_from=[tiny_geotiff])
    _render(client, tid)
    # 사전순으로 **어긋난 것이 먼저** 온다 — 종전이면 여기서 틱이 죽었다.
    bad = _envelope(bus, event_type="preview.grid-changed", trigger="색 범위 확정",
                    upload_id=tid, event_id="01JQ000000000000000000AC0")
    good = _envelope(bus, event_type="preview.backend-rerun", trigger="미리보기 뒷단 재실행",
                     upload_id=tid, event_id="01JQ000000000000000000AC1")
    port = trigger_port.SpoolTriggerPort(bus)
    done = trigger_app.drain(port, jobs=client.app.state.jobs,
                             source=client.app.state.source)
    assert len(done) == 1, "어긋난 봉투 하나가 멀쩡한 봉투의 집행을 막았다"
    assert done[0].job.status == "완료"
    assert not good.exists(), "집행이 끝났는데 알림이 걷히지 않았다"
    assert not bad.exists() and (bus / trigger_port.QUARANTINE_DIRNAME / bad.name).exists()


def test_한_건이_터져도_같은_틱의_다음_건은_집행된다(source_root, put_target, tiny_geotiff,
                                              tmp_path):
    """`drain` 독스트링 축자 — 「**한 건이 실패해도 나머지를 멈추지 않는다** — 실패한
    건의 알림은 걷지 않는다」. 종전 코드는 `LookupError` 만 잡아 그 문장이 거짓이었다."""
    bus = tmp_path / "bus"
    client = make_client(source_root, "inline")
    tid = put_target(copy_from=[tiny_geotiff])
    _render(client, tid)
    real = client.app.state.jobs

    class 한_건만_터지는_jobs:
        def __init__(self):
            self.seen = 0

        def regenerate(self, event, *, source):
            self.seen += 1
            if self.seen == 1:
                raise RuntimeError("렌더가 터졌다")
            return real.regenerate(event, source=source)

    boom = _envelope(bus, event_type="preview.grid-changed", trigger="격자 변경",
                     upload_id=tid, event_id="01JQ000000000000000000AD0")
    good = _envelope(bus, event_type="preview.backend-rerun", trigger="미리보기 뒷단 재실행",
                     upload_id=tid, event_id="01JQ000000000000000000AD1")
    done = trigger_app.drain(trigger_port.SpoolTriggerPort(bus),
                             jobs=한_건만_터지는_jobs(), source=client.app.state.source)
    assert len(done) == 1, "한 건의 예외가 같은 틱의 다음 건을 막았다"
    assert boom.exists(), "실패한 건의 알림이 걷혔다 — 다음 바퀴가 다시 집을 수 없다"
    assert not good.exists()


def test_이미_집행한_봉투의_재전달본은_버스에_쌓이지_않는다(tmp_path):
    """**코드리뷰 #2 의 형제** — 멱등 키로 거르기만 하고 `ack` 를 못 하면 그 파일은
    `_inflight` 에 등록되지 않아 **영원히 못 걷는다.** 재전달이 정상인 계약에서
    (at-least-once) 그것은 스풀이 무한히 자라고 매 틱 재파싱된다는 뜻이다."""
    bus = tmp_path / "bus"
    port = trigger_port.SpoolTriggerPort(bus)
    _envelope(bus, event_type="preview.file-added", trigger="파일 추가",
              upload_id="01ARZ3NDEKTSV4RRFFQ69G5FAV", event_id="01JQ000000000000000000AE1")
    for e in list(port.poll()):
        port.ack(e)
    again = _envelope(bus, event_type="preview.file-added", trigger="파일 추가",
                      upload_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
                      event_id="01JQ000000000000000000AE2")
    assert list(port.poll()) == [], "같은 멱등 키의 재전달이 두 번 집행됐다"
    assert not again.exists(), "이미 집행한 봉투의 재전달본이 버스에 영구히 남았다"
    assert list(bus.glob("*.json")) == []


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


# ── ⑤ 실행자 — 아무도 안 불러도 스스로 돈다 (`03-HANDOFF §4 #60`) ────────────
def _wait(predicate, timeout: float = 10.0) -> bool:
    """조건이 설 때까지 기다린다 — **시험이 집행을 대신 부르지 않는다.**"""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return predicate()


def test_앱이_뜨면_아무도_안_불러도_버스가_비워진다(source_root, put_target, tiny_geotiff,
                                            tmp_path):
    """**#60 의 본체.** `drain` 에 런타임 호출자가 없어서 버스는 쌓이기만 했다.

    ⚠ 이 시험은 `trigger_app.drain` 을 **부르지 않는다** — 부르면 재는 것이 없어진다.
    앱을 띄우고(lifespan) 봉투를 놓은 뒤 **기다리기만** 한다.
    """
    bus = tmp_path / "bus"
    client = make_client(source_root, "inline", trigger_spool=bus,
                         trigger_poll_seconds=0.05)
    tid = put_target(copy_from=[tiny_geotiff])
    with client:                       # ← lifespan 이 실행자를 세운다
        first = _render(client, tid)
        _envelope(bus, event_type="preview.backend-rerun", trigger="미리보기 뒷단 재실행",
                  upload_id=tid)
        assert _wait(lambda: not list(bus.glob("*.json"))), \
            "루프가 돌지 않았다 — 봉투가 버스에 그대로 남아 있다"
        loop = client.app.state.trigger_loop
        assert loop is not None and loop.drained >= 1
        jobs = client.app.state.jobs
        latest = jobs._latest_for(tid)
        assert latest is not None and latest.render_id != first["renderId"], \
            "버스는 비었는데 재생성이 일어나지 않았다"
        for a in latest.artifacts.all():
            assert a.path.exists()
    assert not [t for t in threading.enumerate() if t.name == "viz-trigger-drain"], \
        "종료 뒤에도 트리거 스레드가 남았다"


def test_버스_자리가_없으면_실행자도_없다(source_root):
    """**자리를 지어내지 않는다** — 배선이 없으면 루프도 서지 않는다."""
    client = make_client(source_root, "inline")
    with client:
        assert client.app.state.trigger_loop is None


def test_한_건이_실패해도_루프는_죽지_않는다(tmp_path):
    """**실패한 봉투는 걷지 않고 로그만 남긴다.** 다음 바퀴가 다시 집는다."""
    class 터지는_jobs:
        def regenerate(self, event, *, source):
            raise RuntimeError("렌더가 터졌다")

    bus = tmp_path / "bus"
    _envelope(bus, event_type="preview.file-added", trigger="파일 추가",
              upload_id="01ARZ3NDEKTSV4RRFFQ69G5FAV")
    loop = trigger_loop.TriggerDrainLoop(trigger_port.SpoolTriggerPort(bus),
                                         jobs=터지는_jobs(), source=None,
                                         interval_seconds=0.01)
    loop.start()
    try:
        assert _wait(lambda: loop.passes >= 3), "예외 한 건이 루프를 죽였다"
    finally:
        loop.stop()
    assert list(bus.glob("*.json")), "실패한 봉투가 버스에서 걷혔다"


def test_주기는_설정에서_오고_못_읽는_값은_기본값이다(monkeypatch):
    """간격은 배포가 정한다 — 코드에 박지 않는다. **오타는 기본값으로 떨어진다.**"""
    from colab_viz.kernel import config as cfg
    monkeypatch.setenv("COLAB_VIZ_TRIGGER_POLL_SECONDS", "0.5")
    assert cfg.load_settings().trigger_poll_seconds == 0.5
    monkeypatch.setenv("COLAB_VIZ_TRIGGER_POLL_SECONDS", "다섯초")
    assert cfg.load_settings().trigger_poll_seconds == cfg.DEFAULT_TRIGGER_POLL_SECONDS
    monkeypatch.delenv("COLAB_VIZ_TRIGGER_POLL_SECONDS")
    assert cfg.load_settings().trigger_poll_seconds == cfg.DEFAULT_TRIGGER_POLL_SECONDS


def test_실행자에도_D5_원장이나_발신_경로가_없다():
    """**음성 · 불변규칙 1.** 실행자가 늘었다고 경계가 늘지 않는다."""
    src = Path(trigger_loop.__file__).read_bytes()
    names = {t.string for t in tokenize.tokenize(io.BytesIO(src).readline)
             if t.type == tokenize.NAME}
    for forbidden in ("sqlalchemy", "psycopg", "requests", "httpx", "boto3", "kafka",
                      "publish", "outbox", "d5_upload", "d5_pipeline_event", "d4_lineage"):
        assert forbidden not in names, f"trigger_loop.py 에 {forbidden} 이 들어왔다"
