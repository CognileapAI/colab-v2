"""liveness 신호 — 배포 배관이지 도메인 로직이 아니다.

이 배포 단위는 아직 비어 있다(D7 은 뒤의 WU 가 채운다). walking skeleton 이
요구하는 것은 "프로세스가 살아 있고 오케스트레이터가 그것을 기계로 확인할 수 있다" 뿐이고,
이 파일은 딱 그것만 한다.

표준 라이브러리만 쓴다 — 빈 단위에 런타임 의존을 들이면 나중에 실제 스택을 고를 때
이미 골라 버린 셈이 된다. 프레임워크 선택은 이 단위를 실제로 채우는 WU 의 몫이다.
"""
from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

UNIT = "viz-render"
PATH = "/healthz"


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self) -> None:  # noqa: N802 (BaseHTTPRequestHandler 규약)
        if self.path.split("?", 1)[0] != PATH:
            self.send_error(404, "not found")
            return
        body = json.dumps(
            {"unit": UNIT, "status": "alive", "implemented": False},
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
    port = int(os.environ.get("COLAB_HEALTH_PORT", "8100"))
    ThreadingHTTPServer(("0.0.0.0", port), _Handler).serve_forever()


if __name__ == "__main__":
    serve()
