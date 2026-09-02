"""헬스 본문 — 배포 배관이지 도메인 로직이 아니다.

`sourceMode`·`previewSink` 는 **설정에 선언된** 값이다(정적 — 버킷·자격증명·네트워크를 안 본다).
`deploy_doctor` 가 이 키 이름을 읽으므로 고정이다. 버킷·경로 같은 값은 싣지 않는다 — 모드만 말한다.
"""
from __future__ import annotations

from .config import Settings

UNIT = "viz-render"


def healthz_body(settings: Settings) -> dict:
    return {"unit": UNIT, "status": "alive", "implemented": True,
            "sourceMode": settings.source_mode, "previewSink": settings.preview_sink}
