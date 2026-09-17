from types import SimpleNamespace
from colab_viz.domains.d7_visualization.jobs import RenderJob


def test_pending_and_restored_jobs_expose_original_target_for_reauthorization():
    target = SimpleNamespace(is_upload=False, target_id="0000000000000000000000DSB1")
    job = RenderJob(render_id="00000000000000000000000001", spec=SimpleNamespace(target=target))
    assert job.to_dict()["target"] == {"datasetId": "0000000000000000000000DSB1"}
    job.persisted_body = {"renderId": job.render_id, "status": "실패"}
    assert job.to_dict()["target"] == {"datasetId": "0000000000000000000000DSB1"}
