"""Fixed bounded D9 reader transport, without request-controlled authority."""

import importlib
import importlib.util
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
import pytest
from colab_core.kernel.knowledge_wire import SourceKey
from colab_core.kernel.knowledge_wire import KnowledgePayload, payload_digest

KEY = SourceKey(
    lab_id="0" * 26, dataset_id="1" * 26, source_kind="evidence", source_id="2" * 26
)


def client_type():
    name = "colab_core.app.knowledge_client"
    assert importlib.util.find_spec(name), "fixed knowledge reader client missing"
    return importlib.import_module(name).KnowledgeHttpClient


@pytest.fixture(autouse=True)
def no_remaining_transport_children(monkeypatch):
    import subprocess

    module = importlib.import_module("colab_core.app.knowledge_client")
    real_popen = subprocess.Popen
    children = []

    def launch(*args, **kwargs):
        child = real_popen(*args, **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr(module.subprocess, "Popen", launch)
    yield
    assert all(child.returncode is not None for child in children)
    assert all(child.stdin.closed and child.stdout.closed for child in children)


@pytest.mark.parametrize(
    "mode,expected",
    [
        ("redirect", "dependency_unavailable"),
        ("large", "dependency_unavailable"),
        ("forbidden", "forbidden"),
        ("stale", "stale_source"),
        ("conflict", "idempotency_conflict"),
    ],
)
def test_reader_transport_fails_closed(mode, expected):
    reads = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            reads.append(self.path)
            self.send_response(
                {
                    "redirect": 302,
                    "large": 200,
                    "forbidden": 403,
                    "stale": 409,
                    "conflict": 409,
                }[mode]
            )
            if mode == "redirect":
                self.send_header("Location", "/untrusted")
            self.end_headers()
            self.wfile.write(
                b"x" * 1048577
                if mode == "large"
                else json.dumps(
                    {
                        "code": "idempotency_conflict"
                        if mode == "conflict"
                        else "stale_source",
                        "message": "secret-server-body",
                    }
                ).encode()
            )

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        client = client_type()(
            "http://127.0.0.1:" + str(server.server_port),
            token="secret-reader",
            timeout=1,
        )
        with pytest.raises(ValueError) as error:
            client.read(KEY, "4" * 26, session_token="secret-session")
        assert str(error.value) == expected
        assert reads == ["/internal/knowledge/read"]
        assert not any(
            secret in str(error.value)
            for secret in (
                "secret-reader",
                "secret-session",
                "secret-server-body",
                "127.0.0.1",
            )
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def response_body():
    version = {"revision": 1, "digest": "a" * 64, "deleted": False}
    payload = {
        "protocol": "knowledge-lifecycle/1",
        "source_key": KEY.model_dump(),
        "source_version": version,
        "processing_version": {
            "generation": 1,
            "extractor_version": "reviewed-evidence-v1",
            "mapping_version": "no-mappings-v1",
            "ontology_release": "b" * 64,
        },
        "facts": [
            {
                "fact_id": "3" * 26,
                "predicate": "roles",
                "value": ["validation"],
                "source_locator": "readme:1#/roles",
                "evidence_kind": "human_review",
                "source_version": version,
            }
        ],
        "mappings": [],
        "dependencies": [],
    }
    typed = KnowledgePayload.model_validate(payload)
    return {
        "payload": payload,
        "receipt": {
            "protocol": "knowledge-lifecycle/1",
            "issuer": "D9",
            "receipt_id": "4" * 26,
            "source_key": KEY.model_dump(),
            "source_version": payload["source_version"],
            "processing_version": payload["processing_version"],
            "publication_sequence": 1,
            "payload_digest": payload_digest(typed),
            "status": "replaced",
        },
    }


@pytest.mark.parametrize("change", ["none", "key", "receipt", "digest", "timeout"])
def test_reader_binds_response_and_never_reuses_user_session(change):
    import time

    sessions = []
    body = response_body()
    if change == "key":
        body["payload"]["source_key"]["source_id"] = "5" * 26
        body["receipt"]["source_key"]["source_id"] = "5" * 26
        body["receipt"]["payload_digest"] = payload_digest(
            KnowledgePayload.model_validate(body["payload"])
        )
    elif change == "receipt":
        body["receipt"]["receipt_id"] = "5" * 26
    elif change == "digest":
        body["receipt"]["payload_digest"] = "f" * 64

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            sessions.append(self.headers.get("X-CoLAB-Session"))
            self.send_response(200)
            self.end_headers()
            if change == "timeout":
                time.sleep(0.8)
            try:
                self.wfile.write(json.dumps(body).encode())
            except (BrokenPipeError, ConnectionResetError):
                pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        client = client_type()(
            "http://127.0.0.1:" + str(server.server_port),
            token="reader",
            timeout=0.5 if change == "timeout" else 1,
        )
        for token in ("first-tracked-session", "second-tracked-session"):
            if change == "none":
                result = client.read(KEY, "4" * 26, session_token=token)
                assert (
                    result.receipt.receipt_id == "4" * 26
                    and result.payload.source_key == KEY
                )
            else:
                with pytest.raises(ValueError, match="dependency_unavailable"):
                    client.read(KEY, "4" * 26, session_token=token)
        assert sessions == ["first-tracked-session", "second-tracked-session"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


@pytest.mark.parametrize("timeout", [0, -1, float("nan"), float("inf"), True, None])
def test_reader_requires_finite_positive_timeout(timeout):
    with pytest.raises(ValueError):
        client_type()("http://127.0.0.1:1", token="reader", timeout=timeout)


def test_stale_error_trickling_cannot_extend_total_deadline():
    import time

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            self.send_response(409)
            self.end_headers()
            try:
                for part in (
                    b'{"code":',
                    b'"stale_',
                    b'source"',
                    b',"message":',
                    b'"x"}',
                ):
                    self.wfile.write(part)
                    self.wfile.flush()
                    time.sleep(0.15)
            except (BrokenPipeError, ConnectionResetError):
                pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        client = client_type()(
            "http://127.0.0.1:" + str(server.server_port), token="reader", timeout=0.4
        )
        with pytest.raises(ValueError, match="dependency_unavailable"):
            client.read(KEY, "4" * 26, session_token="tracked")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_stall_near_deadline_uses_remaining_socket_timeout():
    import time

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            self.send_response(200)
            self.end_headers()
            try:
                self.wfile.write(b"{")
                self.wfile.flush()
                time.sleep(0.35)
                self.wfile.write(b" ")
                self.wfile.flush()
                time.sleep(0.7)
            except (BrokenPipeError, ConnectionResetError):
                pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        client = client_type()(
            "http://127.0.0.1:" + str(server.server_port), token="reader", timeout=0.5
        )
        started = time.monotonic()
        with pytest.raises(ValueError, match="dependency_unavailable"):
            client.read(KEY, "4" * 26, session_token="tracked")
        assert time.monotonic() - started < 0.7
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_header_trickle_cannot_extend_total_deadline():
    import time
    from threading import Event

    reached_headers = Event()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            try:
                self.connection.sendall(b"HTTP/1.1 200 OK\r\nX-Slow: ")
                reached_headers.set()
                for _ in range(12):
                    self.connection.sendall(b"x")
                    time.sleep(0.1)
                self.connection.sendall(b"\r\nContent-Length: 2\r\n\r\n{}")
            except (BrokenPipeError, ConnectionResetError):
                pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        client = client_type()(
            "http://127.0.0.1:" + str(server.server_port), token="reader", timeout=0.3
        )
        started = time.monotonic()
        with pytest.raises(ValueError, match="dependency_unavailable"):
            client.read(KEY, "4" * 26, session_token="tracked")
        assert time.monotonic() - started < 0.7
        assert reached_headers.is_set(), (
            "test must reach HTTP headers, not startup timeout"
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


@pytest.mark.parametrize("mode", ["dns", "connect", "stdin", "stdout", "exit"])
def test_child_failure_is_bounded_and_reaped(monkeypatch, mode):
    import subprocess
    import sys
    import time

    module = importlib.import_module("colab_core.app.knowledge_client")
    real_popen = subprocess.Popen
    children = []
    # Fault injection occurs inside a real disposable child, not a mock wait:
    # DNS/connect block indefinitely, IPC stops draining or floods, or exits.
    faults = {
        "dns": "socket.getaddrinfo = lambda *a, **k: time.sleep(10)",
        "connect": "socket.create_connection = lambda *a, **k: time.sleep(10)",
        "stdin": "time.sleep(10)",
        "stdout": "sys.stdout.buffer.write(b'x' * 2000000); sys.stdout.flush(); time.sleep(10)",
        "exit": "sys.exit(7)",
    }

    def launch(argv, **kwargs):
        from pathlib import Path

        child_path = str(
            Path(module.__file__).with_name("knowledge_http_process.py").resolve()
        )
        assert argv == [sys.executable, "-I", child_path]
        assert kwargs["env"] == {} and kwargs["stderr"] == subprocess.DEVNULL
        code = "import socket, time, sys, runpy; " + faults[mode]
        if mode in {"dns", "connect"}:
            code += "; runpy.run_path(" + repr(child_path) + ", run_name='__main__')"
        child = real_popen([sys.executable, "-c", code], **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr(module.subprocess, "Popen", launch)
    client = client_type()("http://127.0.0.1:1", token="reader-secret", timeout=0.3)
    started = time.monotonic()
    with pytest.raises(ValueError) as error:
        client.read(KEY, "4" * 26, session_token="s" * 16000)
    assert str(error.value) == "dependency_unavailable"
    assert time.monotonic() - started < 0.8
    assert len(children) == 1 and children[0].returncode is not None
    assert children[0].stdin.closed and children[0].stdout.closed
