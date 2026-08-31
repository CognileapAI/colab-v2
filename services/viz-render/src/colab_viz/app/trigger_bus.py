"""**받는 자리의 실물** — D5 가 발행한 「미리보기가 낡았다」를 D7 이 집는다.

⭑ **⟨2026-08-31 · 12차 동결 해제 · `PLAN-SoT §9 〈253〉` · Ted RULING ㉗⟩**
`〈247〉` 회차가 세운 것은 `TriggerPort`(Protocol)까지였고 **보내는 쪽이 없어**
`Y-1` 이 닫히지 않았다(`03-HANDOFF §4 #55`). 판정은 셋 중 ⓐ 였다 — **이벤트 계약을
늘린다.** 이 파일은 그 계약의 **소비자 쪽 어댑터**다.

**왜 파일 스풀인가** — 전송 수단은 계약이 정하지 않았다(`〈61〉` · 봉투만 동결했고
브로커는 정본이 값을 주지 않았다). 지금 실물은 **두 배포 단위가 함께 보는 디렉터리**
하나이고, 브로커가 정해지면 이 어댑터를 하나 더 붙이는 일이 된다 — `SourcePort` 가
파일시스템 어댑터 하나로 서 있는 것과 **같은 모양**이다(`ports/source.py` 서두).

⚠ **왜 `ports/` 가 아니라 `app/` 인가 — 게이트가 가르쳤다.** 처음에 `ports/trigger.py` 로
두었더니 `import-boundary` 가 red 를 냈다: **viz-render 의 층은 `app > domains > ports >
kernel`** 이라 `ports` 가 `domains` 를 import 할 수 없는데, 이 어댑터는 도메인이 선언한
`TriggerPort`·`InvalidationEvent` 를 만족해야 한다. **우회하지 않았다**(`CLAUDE.md §4`) —
셋 중 어느 것도 아니었다: Port 를 더할 일도(도메인이 이미 `TriggerPort` 로 자리를 선언했다),
도메인 분할이 틀린 것도, 기획이 애매한 것도 아니고 **조립이 조립 층에 있지 않았을 뿐**이다.
`app/main.py` 가 `FilesystemSourcePort` 를 세우는 것과 같은 자리다. ⚠ `ports/source.py` 가
`ports` 에 사는 것은 **그 Protocol 자신이 거기 살기 때문**이고, 이 seam 은 Protocol 이
도메인에 산다 — 대칭이 깨진 것이 아니라 선언처가 다르다.

**경계**(`Y-1` 완료 정의 ⓔ · `CLAUDE.md §3-1`) —
  · 읽는 것은 **발행된 버스** 하나다. `d5_upload`·`d5_pipeline_event`(outbox)를 읽는
    길이 이 단위에 없다 — outbox 는 D5 의 표이고 그것을 읽으면 불변규칙 1 위반이다
  · **발신하지 않는다.** 여기에 있는 것은 받는 자리뿐이다
  · 지우는 것은 **버스 안의 알림 파일**뿐이다. 원본·기준 격자·미리보기 산출물은
    이 파일이 아는 자리가 아니다(`〈247〉`)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

from ..domains.d7_visualization.invalidation import InvalidationEvent, UnknownTrigger

#: 이벤트 종류 → 트리거 이름. **계약 축자**다
#: (`contracts/events/envelope.json#/$defs/EventType`·`InvalidationTrigger` ·
#: `core-pipeline.json#/$defs/PreviewBackendRerun` 외 2). 값을 여기서 새로 짓지 않고,
#: 시험이 계약 파일을 직접 읽어 대조한다.
TRIGGER_BY_EVENT_TYPE: dict[str, str] = {
    "preview.backend-rerun": "미리보기 뒷단 재실행",
    "preview.grid-changed": "격자 변경",
    "preview.file-added": "파일 추가",
}

#: 봉투가 대상을 말하는 자리 — 이 seam 의 집계 루트다(`envelope.json` 축자).
#: ⚠ `datasetId` 는 이 계약에 **없다** — 다른 도메인 식별자를 싣지 않기 때문이다.
_TARGET_FIELD = "uploadId"


class OutsideSpool(Exception):
    """**버스 밖을 지우려 했다.** 조용히 건너뛰지 않고 멈춘다."""


class SpoolTriggerPort:
    """`TriggerPort` 의 실물 하나 — 디렉터리를 버스로 쓴다.

    **순서가 규약이다**: `poll()` 로 집고 → 집행하고 → `ack()` 로 지운다.
    거꾸로 하면(먼저 지우면) 집행에 실패한 알림이 사라지고 **미리보기가 낡은 채 굳는다.**
    at-least-once 라 같은 사건이 두 번 오는 것은 정상이고, **멱등 키**가 그것을 거른다.
    """

    def __init__(self, spool_dir) -> None:
        self._root = Path(spool_dir)
        #: 이미 집행한 **작업의 정체성**(봉투 축자 — `eventId` 와 역할이 다르다).
        self._done: set[str] = set()
        self._inflight: dict[str, Path] = {}

    # ── TriggerPort ─────────────────────────────────────────────────────────
    def poll(self) -> Iterator[InvalidationEvent]:
        """버스에 놓인 알림을 사건으로 바꾼다.

        **거르는 것 둘** — ⑴ 내가 받는 3종이 아닌 봉투(업로드 파이프라인의 진행은 D7 이
        무효화할 사실이 아니다) ⑵ 이미 집행한 멱등 키(재전달).
        **거절하는 것 하나** — 아는 종류인데 **모르는 트리거**가 실려 온 것. 계약 위반은
        조용히 넘기지 않는다: 걸러내면 같은 버그가 다음에도 오고 그때는 아무도 모른다.
        """
        if not self._root.is_dir():
            return
        for path in sorted(self._root.glob("*.json")):
            try:
                envelope = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                # 반쯤 쓰인 파일 — 발행자가 `rename` 으로 놓으므로 정상 경로에서는
                # 안 나온다. 다음 바퀴가 다시 본다(지우지 않는다).
                continue
            event_type = envelope.get("type")
            if event_type not in TRIGGER_BY_EVENT_TYPE:
                continue
            key = str(envelope.get("idempotencyKey") or "")
            if key and key in self._done:
                continue
            trigger = (envelope.get("payload") or {}).get("trigger")
            if trigger != TRIGGER_BY_EVENT_TYPE[event_type]:
                raise UnknownTrigger(
                    f"계약에 없는 트리거가 실려 왔다: {trigger!r} — "
                    f"`{event_type}` 가 말할 수 있는 것은 "
                    f"{TRIGGER_BY_EVENT_TYPE[event_type]!r} 하나다")
            target = str(envelope.get(_TARGET_FIELD) or "")
            event = InvalidationEvent(trigger=trigger, target_id=target, delivery_key=key)
            self._inflight[key] = path
            yield event

    def ack(self, event: InvalidationEvent) -> None:
        """집행이 끝났다 — 알림을 버스에서 걷고 멱등 키를 기억한다."""
        path = self._inflight.pop(event.delivery_key, None)
        if event.delivery_key:
            self._done.add(event.delivery_key)
        if path is not None:
            self._discard(path)

    # ── 지우는 자리 하나 ────────────────────────────────────────────────────
    def _discard(self, path) -> None:
        """**이 단위가 파일을 지우는 유일한 자리이고, 버스 안으로 갇혀 있다.**

        지우는 것은 **알림**이지 산출물이 아니다 — 원본·기준 격자·미리보기 산출물은
        이 파일이 아는 자리가 아니다(`〈247〉`). 밖이면 아무것도 하지 않고 멈춘다.
        """
        p = Path(path)
        try:
            p.resolve().relative_to(self._root.resolve())
        except (ValueError, OSError):
            raise OutsideSpool(
                f"버스 밖의 자리는 이 단위가 지울 것이 아니다: {p.name}") from None
        if p.exists():
            p.unlink()
