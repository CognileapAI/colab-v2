"""I4 pipeline-worker 한 바퀴 구조화 요약."""
from __future__ import annotations

import json

from colab_pipeline.app import worker


def test_worker_pass_summary_is_structured_and_has_counts(capsys) -> None:
    emit = getattr(worker, "structured_worker_summary", None)
    assert callable(emit), "한 바퀴 결과를 구조화해서 남기는 표면이 없다"
    emit(processed=["u1", "u2"], sent=3, reaped=[])
    event = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert event["schema"] == "colab.ops.v1"
    assert event["service"] == "pipeline-worker"
    assert event["event"] == "worker.pass.completed"
    assert event["processed_count"] == 2
    assert event["sent_count"] == 3
    assert event["reaped_count"] == 0
    assert len(event["trace_id"]) == 32
    assert len(event["span_id"]) == 16
