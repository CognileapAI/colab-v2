"""`reclaimPreviews` 라우트 — 사용자 지시 삭제의 회수 한 바퀴 (`DL-2` · 22차 해제 ㉯).

여기서 재는 것 — **판정은 재지 않는다**(그 자리는 `test_reclaim_on_delete.py`). 이 파일이
잠그는 것은 **표면**이다.

  ⑴ 인증이 다른 렌더 표면과 **같은 자리**에서 걸린다 — 토큰 없으면 401.
  ⑵ 경계 헤더가 없으면 400 이고, 요청 모양이 틀려도 400 이다(viz 는 422 를 내지 않는다).
  ⑶ 200 본문은 계약 `PreviewReclaimResult` 다섯 칸 — 지어낸 칸도, 빠진 칸도 없다.
  ⑷ **멱등** — 같은 요청 두 번째는 `stale 0` 이다. core 가 삭제를 재시도해도 같다.
  ⑸ 저장 모드가 `s3` 면 **그 클라이언트로 표식을 조회**하고 **싱크로 지운다** —
     라우트가 자기 삭제 문을 따로 만들지 않는다.
"""
from __future__ import annotations

import json

import pytest
from conftest import AUTH, TOKEN, make_client

_PATH = "/viz/v1/reclaims"
#: 정규 ID 26자 — 계약 `common.json#Ulid` 그대로다. 시험이 짧은 문자열을 쓰면 400 갈래가
#: 통과 갈래를 덮어 「모양 검사가 있다」만 재고 「200 이 난다」를 못 잰다.
F1 = "01JQ0000000000000000000FA1"
F2 = "01JQ0000000000000000000FA2"
TARGET = "01JQ00000000000000000000D1"


def _key(tag: str) -> str:
    return (tag * 64)[:64]


def _lay(root, key: str, sources: list[str]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / f"{key}.png").write_bytes(b"\x89PNG")
    (root / f"{key}.webp").write_bytes(b"RIFF")
    (root / f"{key}.json").write_text(
        json.dumps({"sidecarVersion": 2, "name": f"{key}.png", "layer": "detail",
                    "source": sources[0], "sources": list(sources),
                    "baked_for": {"target_id": TARGET, "is_upload": False}}),
        encoding="utf-8")


class _StubClient:
    """표식 목록만 돌려준다 — 삭제는 싱크가 진다(`S3PreviewSink.remove`)."""

    def __init__(self, index: dict[str, list[str]]) -> None:
        self.index = index
        self.listed: list[str] = []

    def list_objects(self, prefix: str):
        self.listed.append(prefix)
        file_id = prefix.rstrip("/").rsplit("/", 1)[-1]
        for content_key in self.index.get(file_id, []):
            yield (f"{prefix}{content_key}", 0)


class _StubSink:
    def __init__(self) -> None:
        self.removes: list[tuple[list[str], list[tuple[str, str]]]] = []

    def publish(self, artifacts) -> None:
        return None

    def index(self, pairs) -> None:
        return None

    def remove(self, names, *, index_pairs) -> None:
        self.removes.append((list(names), list(index_pairs)))


@pytest.fixture
def reclaim_client(source_root):
    """로컬 싱크 앱에 **기록하는 대역**을 꽂는다 — 자리는 렌더 라우트가 쓰는 그 자리다."""
    client = make_client(source_root, "inline")
    sink = _StubSink()
    client.app.state.preview_sink = sink
    return client, sink


def _previews_root(client):
    return client.app.state.settings.preview_dir


# ══════════════════════════ ⑴ 인증 ══════════════════════════════════════════
def test_no_token_is_401(reclaim_client) -> None:
    client, _ = reclaim_client
    r = client.post(_PATH, json={"targetId": TARGET, "fileIds": [F1]},
                    headers={"X-CoLAB-Lab": "01JQ", "X-CoLAB-Account": "01JQ"})
    assert r.status_code == 401, r.text


# ══════════════════════════ ⑵ 400 셋 ════════════════════════════════════════
@pytest.mark.parametrize("body", [
    {"targetId": TARGET, "fileIds": []},                 # 빈 집합 — 전건 회수가 되어 버린다
    {"targetId": TARGET, "fileIds": ["not-a-ulid"]},     # 모양 밖
    {"targetId": "not-a-ulid", "fileIds": [F1]},
    {"targetId": TARGET, "fileIds": [F1], "extra": 1},   # 모르는 칸을 받아 주지 않는다
])
def test_malformed_requests_are_400(reclaim_client, body) -> None:
    """**422 가 아니라 400 이다** — viz 는 `RequestValidationError` 를 400 으로 바꾼다."""
    client, _ = reclaim_client
    r = client.post(_PATH, json=body, headers=AUTH)
    assert r.status_code == 400, f"{body} → {r.status_code} {r.text}"


def test_missing_tenant_headers_is_400(reclaim_client) -> None:
    client, _ = reclaim_client
    r = client.post(_PATH, json={"targetId": TARGET, "fileIds": [F1]},
                    headers={"Authorization": f"Bearer {TOKEN}"})
    assert r.status_code == 400, r.text
    assert r.json()["code"] == "TENANT_SCOPE_MISSING"


# ══════════════════════════ ⑶⑷ 200 · 멱등 ═══════════════════════════════════
def test_a_stale_artifact_is_reclaimed_and_the_body_has_five_fields(reclaim_client) -> None:
    client, sink = reclaim_client
    root = _previews_root(client)
    key = _key("a")
    _lay(root, key, [F1])

    r = client.post(_PATH, json={"targetId": TARGET, "fileIds": [F1]}, headers=AUTH)
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body) == {"targetId", "stale", "kept", "unindexed", "removed"}, body
    assert body["targetId"] == TARGET
    assert body["stale"] == 1
    assert body["kept"] == 0
    assert sorted(body["removed"]) == sorted(f"{key}{ext}"
                                             for ext in (".webp", ".png", ".json", ".pgw"))
    # 로컬 파일은 `invalidation.apply()` 가 지운다 — 지우는 문을 라우트가 늘리지 않는다.
    assert not (root / f"{key}.png").exists()
    assert sink.removes, "싱크에 회수를 알리지 않았다 — S3 객체가 그대로 남는다."


def test_the_second_call_is_stale_zero(reclaim_client) -> None:
    """**멱등** — core 의 삭제 재시도가 같은 답을 받는다."""
    client, _ = reclaim_client
    _lay(_previews_root(client), _key("b"), [F1])
    first = client.post(_PATH, json={"targetId": TARGET, "fileIds": [F1]}, headers=AUTH)
    assert first.json()["stale"] == 1
    second = client.post(_PATH, json={"targetId": TARGET, "fileIds": [F1]}, headers=AUTH)
    assert second.status_code == 200, second.text
    assert second.json() == {"targetId": TARGET, "stale": 0, "kept": 0,
                             "unindexed": 0, "removed": []}


def test_an_artifact_whose_sources_are_not_all_deleted_is_kept(reclaim_client) -> None:
    """`sources ⊆ D` 가 아니면 남는다 — 살아 있는 파일의 미리보기를 지우지 않는다."""
    client, sink = reclaim_client
    root = _previews_root(client)
    key = _key("c")
    _lay(root, key, [F1, F2])
    r = client.post(_PATH, json={"targetId": TARGET, "fileIds": [F1]}, headers=AUTH)
    assert r.status_code == 200, r.text
    assert r.json()["stale"] == 0
    assert (root / f"{key}.png").exists()
    assert sink.removes == []


# ══════════════════════════ ⑸ S3 모드 배선 ══════════════════════════════════
def test_s3_mode_uses_the_index_client_and_the_sink(source_root, monkeypatch) -> None:
    """저장 모드가 `s3` 면 **표식 목록 조회 1회/파일** ＋ 싱크 삭제다.

    로컬에 그림이 없어도(캐시에서 밀렸어도) 이름은 표식에서 계산된다 — 그것이 표식을
    두는 이유다.
    """
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "x")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "y")
    key = _key("d")
    client = make_client(source_root, "inline", preview_sink="s3",
                         s3_bucket="bucket", s3_region="ap-northeast-2")
    stub = _StubClient({F1: [key]})
    sink = _StubSink()
    client.app.state.s3_client = stub
    client.app.state.preview_sink = sink
    # 사이드카는 로컬 자리에 둔다 — 판정 입력이지 후보 목록이 아니다.
    _lay(_previews_root(client), key, [F1])

    r = client.post(_PATH, json={"targetId": TARGET, "fileIds": [F1]}, headers=AUTH)
    assert r.status_code == 200, r.text
    assert stub.listed == [f"preview-index/by-file/{F1}/"], stub.listed
    assert r.json()["stale"] == 1
    names, pairs = sink.removes[0]
    assert f"{key}.png" in names
    assert (F1, key) in pairs
