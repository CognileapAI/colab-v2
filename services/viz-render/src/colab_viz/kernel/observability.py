"""CoLAB 운영 관측 커널 — W3C trace context와 비밀 없는 JSON 한 줄.

이 파일이 정본이고 다른 Python 배포 단위는 생성물 등기부로 같은 바이트를 받는다.
외부 추적 수집기가 없어도 서비스 사이 trace-id를 잃지 않으며, stdout JSON은 Docker의
기존 로그 회전/수집 경로를 그대로 탄다.
"""
from __future__ import annotations

import json
import re
import secrets
import time
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterator


SCHEMA = "colab.ops.v1"
TRACE_HEADER = b"traceparent"
_TRACEPARENT = re.compile(
    r"^00-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$")
_FORBIDDEN_FIELD_PARTS = (
    "authorization", "cookie", "password", "secret", "token", "query", "body",
    "database_url", "db_url", "s3_url",
)


@dataclass(frozen=True)
class TraceContext:
    trace_id: str
    span_id: str
    parent_span_id: str | None
    flags: str

    @property
    def traceparent(self) -> str:
        return f"00-{self.trace_id}-{self.span_id}-{self.flags}"


_CURRENT: ContextVar[TraceContext | None] = ContextVar("colab_trace", default=None)


def _new_hex(nbytes: int) -> str:
    while True:
        value = secrets.token_hex(nbytes)
        if int(value, 16) != 0:
            return value


def parse_traceparent(value: str | None) -> tuple[str, str, str] | None:
    """유효한 v00 `(trace_id, parent_span_id, flags)`만 받는다."""
    if not value:
        return None
    matched = _TRACEPARENT.fullmatch(value)
    if matched is None:
        return None
    trace_id, parent_id, flags = matched.groups()
    if int(trace_id, 16) == 0 or int(parent_id, 16) == 0:
        return None
    return trace_id, parent_id, flags


def _child(value: str | None = None) -> TraceContext:
    incoming = parse_traceparent(value)
    if incoming is not None:
        trace_id, parent_span_id, flags = incoming
        return TraceContext(trace_id, _new_hex(8), parent_span_id, flags)
    parent = _CURRENT.get()
    if parent is not None:
        return TraceContext(parent.trace_id, _new_hex(8), parent.span_id, parent.flags)
    return TraceContext(_new_hex(16), _new_hex(8), None, "01")


@contextmanager
def local_span(traceparent: str | None = None) -> Iterator[TraceContext]:
    context = _child(traceparent)
    token = _CURRENT.set(context)
    try:
        yield context
    finally:
        _CURRENT.reset(token)


def current_traceparent() -> str | None:
    context = _CURRENT.get()
    return context.traceparent if context is not None else None


def structured_event(*, service: str, event: str, level: str = "INFO", **fields: Any) -> None:
    """운영 JSON 한 줄. 비밀·본문 계열 필드 이름은 실수라도 거부한다."""
    for name in fields:
        lowered = name.lower()
        if any(part in lowered for part in _FORBIDDEN_FIELD_PARTS):
            raise ValueError(f"운영 로그 금지 필드다: {name}")
    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace(
            "+00:00", "Z"),
        "level": level,
        "event": event,
        "service": service,
    }
    context = _CURRENT.get()
    if context is not None:
        payload.update(trace_id=context.trace_id, span_id=context.span_id)
        if context.parent_span_id is not None:
            payload["parent_span_id"] = context.parent_span_id
    payload.update({key: value for key, value in fields.items() if value is not None})
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
          flush=True)


class TraceMiddleware:
    """의존 없는 ASGI middleware — HTTP 요청에 server span 하나를 만든다."""

    def __init__(self, app, *, service_name: str) -> None:
        self.app = app
        self.service_name = service_name

    async def __call__(self, scope, receive, send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        values = []
        for name, raw in scope.get("headers", []):
            if name.lower() == TRACE_HEADER:
                try:
                    values.append(raw.decode("ascii"))
                except UnicodeDecodeError:
                    values.append("")
        incoming = values[0] if len(values) == 1 else None
        started = time.perf_counter()
        status = 500
        with local_span(incoming) as context:
            async def send_with_trace(message) -> None:
                nonlocal status
                if message.get("type") == "http.response.start":
                    status = int(message.get("status", 500))
                    headers = [(name, value) for name, value in message.get("headers", [])
                               if name.lower() != TRACE_HEADER]
                    headers.append((TRACE_HEADER, context.traceparent.encode("ascii")))
                    message = {**message, "headers": headers}
                await send(message)

            try:
                await self.app(scope, receive, send_with_trace)
            except BaseException:
                structured_event(
                    service=self.service_name, event="http.server.request", level="ERROR",
                    method=scope.get("method", ""), path=scope.get("path", ""), status=500,
                    duration_ms=round((time.perf_counter() - started) * 1000, 3))
                raise
            else:
                structured_event(
                    service=self.service_name, event="http.server.request",
                    level="ERROR" if status >= 500 else "INFO",
                    method=scope.get("method", ""), path=scope.get("path", ""), status=status,
                    duration_ms=round((time.perf_counter() - started) * 1000, 3))
