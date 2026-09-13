"""발행 순서 — **표식(`index`)이 산출물(`publish`)보다 먼저다** (`DL-2` ⓓ7).

표식 없이 놓인 산출물은 회수 때 목록 조회로 찾을 수 없고, 그 실패는 에러가 아니라
「지울 것이 없다」로 위장한다. 그래서 순서가 규약이고, 표식 실패는 **렌더 실패**다 —
반쪽 상태(그림은 서빙 중인데 되찾을 길이 없다)를 「완료」로 내지 않는다.
"""
from __future__ import annotations

import pytest
from conftest import AUTH


class _OrderedSink:
    """부른 순서를 그대로 적는다 — 「무엇을 불렀는가」가 아니라 **순서**가 판정이다."""

    def __init__(self, *, fail_index: bool = False) -> None:
        self.calls: list[str] = []
        self.pairs: list[tuple[str, str]] = []
        self.fail_index = fail_index

    def publish(self, artifacts) -> None:
        self.calls.append("publish")

    def index(self, pairs) -> None:
        self.calls.append("index")
        self.pairs.extend(pairs)
        if self.fail_index:
            raise RuntimeError("표식을 놓지 못했다")

    def remove(self, names, *, index_pairs) -> None:
        self.calls.append("remove")


def _render(client, target_id):
    return client.post("/viz/v1/renders",
                       json={"target": {"datasetId": target_id},
                             "style": {"palette": "단색-파랑"}},
                       headers=AUTH)


def test_표식을_먼저_놓고_산출물을_올린다(client, put_target, tiny_geotiff):
    sink = _OrderedSink()
    client.app.state.preview_sink = sink
    tid = put_target(copy_from=[tiny_geotiff])

    rid = _render(client, tid).json()["renderId"]
    job = client.app.state.jobs.get(rid)

    assert job.status == "완료", job.failure
    assert sink.calls == ["index", "publish"], sink.calls
    # 표식은 **그 렌더에 들어간 조각 전부**를 실은 `(fileId, contentKey)` 다.
    assert sink.pairs, "표식을 하나도 놓지 않았다"
    file_ids = {f for f, _ in sink.pairs}
    assert file_ids == set(job.artifacts.sources), (file_ids, job.artifacts.sources)
    assert {k for _, k in sink.pairs} == {a.cache_key for a in job.artifacts.all()}


def test_표식_실패는_렌더_실패이고_산출물을_올리지_않는다(client, put_target, tiny_geotiff):
    sink = _OrderedSink(fail_index=True)
    client.app.state.preview_sink = sink
    tid = put_target(copy_from=[tiny_geotiff])

    rid = _render(client, tid).json()["renderId"]
    job = client.app.state.jobs.get(rid)

    assert job.status == "실패", job.status
    assert sink.calls == ["index"], "표식이 실패했는데 산출물을 서빙 자리에 올렸다"
