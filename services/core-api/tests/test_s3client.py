"""S3 컨트롤 플레인 클라이언트 오라클 — `kernel/s3.py`.

전송층(transport)을 가짜로 주입해 AWS 없이 검증한다. §8 의 함정 네 가지가 오라클이다:
① Complete 는 200 OK 로 실패할 수 있다 ② 응답 XML 에 네임스페이스가 있다
③ Complete 본문은 네임스페이스 없이 PartNumber 오름차순 ④ 체크섬 헤더를 넣지 않는다.
실전 검증은 `ops/s3_smoke.py` 가 실제 버킷으로 한다.
"""
from __future__ import annotations

import pytest

from colab_core.kernel.s3 import Part, S3Client, S3Error
from colab_core.kernel.sigv4 import Credentials

CREDS = Credentials(access_key="AKIAEXAMPLE", secret_key="secret")

NS = 'xmlns="http://s3.amazonaws.com/doc/2006-03-01/"'


class StubTransport:
    """(status, headers, body) 큐를 순서대로 돌려주고 호출을 기록한다."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls: list[tuple] = []

    def __call__(self, method, url, headers, payload, timeout):
        self.calls.append((method, url, dict(headers), payload, timeout))
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def client(*responses) -> tuple[S3Client, StubTransport]:
    t = StubTransport(*responses)
    c = S3Client(bucket="test-bucket", region="ap-northeast-2", creds=CREDS,
                 transport=t, backoff_base=0)
    return c, t


# ── ② ListParts — 네임스페이스 + 페이지네이션 ──────────────────────────────

def test_list_parts_parses_namespaced_xml_across_pages():
    page1 = (200, {}, f"""<?xml version="1.0"?>
      <ListPartsResult {NS}>
        <IsTruncated>true</IsTruncated><NextPartNumberMarker>2</NextPartNumberMarker>
        <Part><PartNumber>1</PartNumber><ETag>"aaa"</ETag><Size>5242880</Size></Part>
        <Part><PartNumber>2</PartNumber><ETag>"bbb"</ETag><Size>5242880</Size></Part>
      </ListPartsResult>""".encode())
    page2 = (200, {}, f"""<ListPartsResult {NS}>
        <IsTruncated>false</IsTruncated>
        <Part><PartNumber>3</PartNumber><ETag>"ccc"</ETag><Size>1024</Size></Part>
      </ListPartsResult>""".encode())
    c, t = client(page1, page2)
    parts = c.list_parts("k", "UP1")
    assert parts == [Part(1, '"aaa"', 5242880), Part(2, '"bbb"', 5242880), Part(3, '"ccc"', 1024)]
    assert "part-number-marker=2" in t.calls[1][1]      # 두 번째 호출이 마커를 이어받는다


# ── ① Complete — 200 OK 인데 본문이 <Error> ────────────────────────────────

def test_complete_raises_on_200_with_error_body():
    c, _t = client((200, {}, b"<Error><Code>InternalError</Code><Message>x</Message></Error>"))
    with pytest.raises(S3Error) as e:
        c.complete_multipart_upload("k", "UP1", [Part(1, '"aaa"', 5)])
    assert e.value.code == "InternalError"


# ── ③ Complete 본문 — 네임스페이스 없음 · 오름차순 · ETag 따옴표 유지 ──────

def test_complete_body_is_plain_sorted_and_quoted():
    ok = (200, {}, f'<CompleteMultipartUploadResult {NS}><ETag>"final"</ETag>'
                   f'</CompleteMultipartUploadResult>'.encode())
    c, t = client(ok)
    etag = c.complete_multipart_upload("k", "UP1",
                                       [Part(2, '"bbb"', 5), Part(1, '"aaa"', 5)])
    assert etag == '"final"'
    body = t.calls[0][3].decode()
    assert body.startswith("<CompleteMultipartUpload>")  # 네임스페이스 없음
    assert body.index("<PartNumber>1</PartNumber>") < body.index("<PartNumber>2</PartNumber>")
    assert '<ETag>"aaa"</ETag>' in body                  # 따옴표 그대로


# ── ④ Create — 체크섬 헤더 금지 · UploadId 파싱 ────────────────────────────

def test_create_multipart_upload_has_no_checksum_header():
    ok = (200, {}, f'<InitiateMultipartUploadResult {NS}><Bucket>b</Bucket><Key>k</Key>'
                   f'<UploadId>UP123</UploadId></InitiateMultipartUploadResult>'.encode())
    c, t = client(ok)
    assert c.create_multipart_upload("폴더/데이터 1.bin", "application/octet-stream") == "UP123"
    method, url, headers, _payload, _timeout = t.calls[0]
    assert method == "POST" and "uploads=" in url
    assert "%ED%8F%B4%EB%8D%94/" in url                  # 한글 키 UriEncode + '/' 보존
    assert not any(h.lower().startswith("x-amz-checksum") for h in headers)


# ── 본문 있는 호출은 content-type 을 명시한다 (실전에서 잡힌 함정) ──────────
# urllib 은 Content-Type 없는 본문에 form-urlencoded 를 자동으로 붙이고,
# S3 는 폼 POST 의 본문을 쿼리로 해석한다 → 서명 불일치 403 (s3_smoke 실전 실측).

def test_payload_calls_send_explicit_content_type():
    ok = (200, {}, f'<CompleteMultipartUploadResult {NS}><ETag>"e"</ETag>'
                   f'</CompleteMultipartUploadResult>'.encode())
    c, t = client(ok)
    c.complete_multipart_upload("k", "UP1", [Part(1, '"a"', 5)])
    headers = {k.lower(): v for k, v in t.calls[0][2].items()}
    assert headers.get("content-type") == "application/xml"


# ── 재시도 — 5xx 는 3회 백오프, 4xx 는 즉시 실패 ───────────────────────────

def test_retries_5xx_then_succeeds():
    err = (500, {}, b"<Error><Code>InternalError</Code></Error>")
    ok = (204, {}, b"")
    c, t = client(err, err, ok)
    c.abort_multipart_upload("k", "UP1")                 # 예외 없이 통과해야 한다
    assert len(t.calls) == 3


def test_4xx_fails_immediately_without_retry():
    c, t = client((404, {}, b"<Error><Code>NoSuchUpload</Code><Message>gone</Message></Error>"))
    with pytest.raises(S3Error) as e:
        c.list_parts("k", "UP-dead")
    assert e.value.status == 404 and e.value.code == "NoSuchUpload"
    assert len(t.calls) == 1


# ── HeadObject — 크기·ETag 는 응답 헤더에서 ────────────────────────────────

def test_head_object_reads_headers():
    c, _t = client((200, {"Content-Length": "12345", "ETag": '"abc"'}, b""))
    assert c.head_object("k") == (12345, '"abc"')


# ── DeleteObjects — Content-MD5 필수 · 1000개 단위 배치 ────────────────────

def test_delete_objects_sends_md5_and_batches():
    ok = (200, {}, f'<DeleteResult {NS}></DeleteResult>'.encode())
    c, t = client(ok, ok)
    c.delete_objects([f"k{i}" for i in range(1001)])
    assert len(t.calls) == 2                             # 1000 + 1
    headers = t.calls[0][2]
    assert any(h.lower() == "content-md5" for h in headers)


# ── 다운로드 (`〈175〉-(다)`) — presign_get · get_object_stream ──────────────

class StreamStub:
    """스트림 전송 대역 — (status, headers, body) 큐. 2xx 본문은 읽기 객체로 준다."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls: list[tuple] = []
        self.closed = 0

    def __call__(self, method, url, headers, timeout):
        import io
        self.calls.append((method, url, dict(headers), timeout))
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        status, resp_headers, body = item
        if status >= 400:
            return status, resp_headers, body
        stub = self

        class Reader(io.BytesIO):
            def close(self):
                stub.closed += 1
                super().close()

        return status, resp_headers, Reader(body)


def stream_client(*responses) -> tuple[S3Client, StreamStub]:
    t = StreamStub(*responses)
    c = S3Client(bucket="test-bucket", region="ap-northeast-2", creds=CREDS,
                 stream_transport=t, backoff_base=0)
    return c, t


def test_presign_get_is_the_get_twin_of_presign_put():
    """같은 서명기(`sigv4.presign`)에 메서드만 GET — 쿼리(응답 헤더 덮어쓰기)도 서명에 든다."""
    import datetime as dt
    import urllib.parse

    from colab_core.kernel.sigv4 import presign
    c, _t = stream_client()
    now = dt.datetime(2026, 8, 29, 0, 0, tzinfo=dt.timezone.utc)
    query = {"response-content-disposition": "attachment; filename*=UTF-8''%EA%B0%95.nc"}
    url = c.presign_get("폴더/강.nc", query=query, expires=600, now=now)
    assert url == presign(method="GET", host=c.host, key="폴더/강.nc", region=c.region,
                          creds=CREDS, query=query, expires=600, now=now)
    assert url.startswith("https://test-bucket.s3.ap-northeast-2.amazonaws.com/%ED%8F%B4%EB%8D%94/")
    parsed = dict(urllib.parse.parse_qsl(url.split("?", 1)[1]))
    assert parsed["X-Amz-Expires"] == "600"
    assert parsed["response-content-disposition"] == query["response-content-disposition"]


def test_get_object_stream_yields_chunks_and_closes_the_response():
    c, t = stream_client((200, {"Content-Length": "10"}, b"0123456789"))
    chunks = list(c.get_object_stream("k", chunk_size=4))
    assert chunks == [b"0123", b"4567", b"89"]
    assert t.closed == 1
    method, url, headers, _timeout = t.calls[0]
    assert method == "GET" and url.endswith("/k")
    assert headers["x-amz-content-sha256"].startswith("e3b0c442")   # 빈 본문 해시 — 본문 없는 GET
    assert not any(h.lower() == "content-type" for h in headers)     # 본문이 없으니 함정도 없다


def test_get_object_stream_404_raises_when_called_not_on_first_chunk():
    """호출 시점에 예외다 — 제너레이터를 돌려주고 첫 `next()` 에서 터지면 라우트는 이미 200 을 보낸 뒤다."""
    c, _t = stream_client((404, {}, b"<Error><Code>NoSuchKey</Code><Message>x</Message></Error>"))
    with pytest.raises(S3Error) as e:
        c.get_object_stream("k")
    assert e.value.status == 404 and e.value.code == "NoSuchKey"


def test_get_object_stream_retries_5xx_before_the_first_byte():
    err = (500, {}, b"<Error><Code>InternalError</Code></Error>")
    c, t = stream_client(err, (200, {}, b"ok"))
    assert b"".join(c.get_object_stream("k")) == b"ok"
    assert len(t.calls) == 2
