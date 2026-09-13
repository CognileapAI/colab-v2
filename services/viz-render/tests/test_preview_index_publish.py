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


# ── 렌더-삭제 경합 (prod 임시 검증 2026-09-13 21:35 실측) ──────────────────────

class _VanishingSink(_OrderedSink):
    """`publish` 직전에 **산출물이 사라진 자리**를 그대로 재현한다.

    실측 — 등록 직후 자동 렌더가 같은 데이터셋의 삭제(회수 200)와 겹쳤고, 회수의
    `invalidation.apply()` 가 방금 구운 파일을 unlink 한 뒤 `publish` 가 그것을 읽었다.
    `S3PreviewSink.publish` 는 `path.read_bytes()` 라 **`FileNotFoundError` 가 그대로**
    올라왔고, `_run` 의 포괄 처리기가 그것을 `RENDER_UNKNOWN_ERROR` 로 접었다.
    """

    def publish(self, artifacts) -> None:
        self.calls.append("publish")
        raise FileNotFoundError("/srv/colab/viz-previews/deadbeef.webp")


def test_산출물이_사라진_채_올리면_알_수_없는_오류가_아니다(client, put_target, tiny_geotiff):
    """**「알 수 없는 오류」로 접지 않는다.** 사라진 산출물은 원인이 분명하고 복구도 분명하다 —
    다시 그리면 된다. 「알 수 없다」로 내면 사용자가 자기 파일을 의심하고, 운영자는
    경합인지 진짜 결함인지 로그에서 가르지 못한다."""
    from colab_viz.domains.d7_visualization.failures import RenderFailure

    sink = _VanishingSink()
    client.app.state.preview_sink = sink
    tid = put_target(copy_from=[tiny_geotiff])

    rid = _render(client, tid).json()["renderId"]
    job = client.app.state.jobs.get(rid)

    assert job.status == "실패", job.status
    assert job.failure["code"] == RenderFailure.ARTIFACT_MISSING, job.failure
    assert job.failure["message"] == "미리보기 산출물이 사라져 다시 그려야 해요."

