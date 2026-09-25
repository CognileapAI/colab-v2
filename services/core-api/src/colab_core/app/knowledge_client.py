"""Fixed D9 reader transport; no ambient proxies, redirects or sensitive errors."""

import json
import math
import os
from pathlib import Path
import selectors
import subprocess
import sys
import time
from urllib.parse import urlsplit
from ..kernel.knowledge_wire import AuthorizedKnowledge, KnowledgeReadRequest


def _exchange(request, timeout):
    """Bound startup + nonblocking IPC + HTTP; cleanup time is additional.

    An isolated short-lived child lets us interrupt even blocking DNS/header
    reads without leaving resolver or transport threads running. Never inherit
    application credentials or pass request data through argv/environment.
    """
    deadline = time.monotonic() + timeout
    pending = memoryview(json.dumps(request).encode())
    if len(pending) > 32768:
        raise ValueError("request limit exceeded")
    output = bytearray()
    process = subprocess.Popen(
        [
            sys.executable,
            "-I",
            str(Path(__file__).with_name("knowledge_http_process.py").resolve()),
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        env={},
        bufsize=0,
    )
    try:
        with selectors.DefaultSelector() as selector:
            os.set_blocking(process.stdin.fileno(), False)
            os.set_blocking(process.stdout.fileno(), False)
            selector.register(process.stdin, selectors.EVENT_WRITE)
            selector.register(process.stdout, selectors.EVENT_READ)
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise ValueError("deadline exceeded")
                for key, _ in selector.select(remaining):
                    if key.fileobj is process.stdin:
                        written = os.write(key.fd, pending[:65536])
                        pending = pending[written:]
                        if not pending:
                            selector.unregister(process.stdin)
                            process.stdin.close()
                    else:
                        # Refuse the first excess byte, not after unbounded
                        # communicate() has collected an arbitrary child output.
                        chunk = os.read(key.fd, min(65536, 1048581 - len(output)))
                        if not chunk:
                            selector.unregister(process.stdout)
                        output.extend(chunk)
                        if len(output) > 1048580:
                            raise ValueError("response limit exceeded")
            remaining = deadline - time.monotonic()
            if remaining <= 0 or process.wait(timeout=remaining) != 0:
                raise ValueError("transport failed")
        return bytes(output)
    finally:
        if process.poll() is None:
            process.kill()
        process.wait()
        process.stdin.close()
        process.stdout.close()


class KnowledgeHttpClient:
    def __init__(self, base_url, *, token, timeout):
        parsed = urlsplit(base_url)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or parsed.path not in {"", "/"}
        ):
            raise ValueError("invalid knowledge endpoint")
        if (
            not isinstance(token, str)
            or not token.strip()
            or any(c in token for c in "\r\n")
        ):
            raise ValueError("reader credential required")
        if (
            type(timeout) not in {int, float}
            or not math.isfinite(timeout)
            or not 0 < timeout <= 30
        ):
            raise ValueError("finite timeout required")
        self._url = base_url.rstrip("/") + "/internal/knowledge/read"
        self._token, self._timeout = token, timeout

    def read(self, key, expected_receipt_id, *, session_token):
        try:
            body = KnowledgeReadRequest.model_validate(
                {
                    "source_key": key.model_dump(),
                    "expected_receipt_id": expected_receipt_id,
                }
            )
            if (
                not isinstance(session_token, str)
                or not session_token
                or len(session_token) > 16384
                or any(c in session_token for c in "\r\n")
            ):
                raise ValueError("invalid session")
            request = {
                "url": self._url,
                "body": body.model_dump_json(),
                "timeout": self._timeout,
                "headers": {
                    "Authorization": "Bearer " + self._token,
                    "X-CoLAB-Session": session_token,
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            }
            raw = _exchange(request, self._timeout)
            code, data = raw.split(b"\n", 1)
            if code in {b"401", b"403"}:
                error = "forbidden"
            elif code == b"409":
                status = json.loads(data).get("code")
                error = (
                    status
                    if status
                    in {
                        "stale_source",
                        "stale_generation",
                        "stale_release",
                        "idempotency_conflict",
                    }
                    else "dependency_unavailable"
                )
            else:
                error = "dependency_unavailable"
            if code != b"200":
                # Raise sanitized protocol failures outside the broad catch.
                result = None
            else:
                result = AuthorizedKnowledge.model_validate_json(data)
            if result is not None and (
                result.receipt.source_key != body.source_key
                or result.receipt.receipt_id != body.expected_receipt_id
            ):
                raise ValueError("response mismatch")
        except Exception:
            raise ValueError("dependency_unavailable") from None
        if result is None:
            raise ValueError(error)
        return result
