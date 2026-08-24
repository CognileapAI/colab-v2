"""liveness 신호 — 배포 배관이지 도메인 로직이 아니다.

`implemented` 는 **이 배포 단위가 비어 있는가**를 나타내는 값이다. 스캐폴드 시점에는 false 가
사실이었으나 `〈73〉` 이 워커 루프(`app.worker`)를 켠 뒤로는 아니다. `03-HANDOFF §4` #23 —
실이미지가 false 를 계속 내어 **본문 대조 검증이 이 단위를 「빈 단위」로 읽었다.**
자리표시가 전 경로 200 을 내므로 상태 코드로는 구분되지 않는다. 값을 사실에 맞춘다.

표준 라이브러리만 쓴다 — 헬스 경로에 런타임 의존을 들이면 그 의존이 죽었을 때
생사 신호까지 함께 죽는다.
"""
from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

UNIT = "pipeline-worker"
PATH = "/healthz"


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self) -> None:  # noqa: N802 (BaseHTTPRequestHandler 규약)
        if self.path.split("?", 1)[0] != PATH:
            self.send_error(404, "not found")
            return
        body = json.dumps(
            {"unit": UNIT, "status": "alive", "implemented": True},
            ensure_ascii=False,
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args) -> None:
        return  # 헬스체크가 10초마다 로그를 채우게 두지 않는다


def serve() -> None:
    port = int(os.environ.get("COLAB_HEALTH_PORT", "8000"))
    ThreadingHTTPServer(("0.0.0.0", port), _Handler).serve_forever()


if __name__ == "__main__":
    serve()
