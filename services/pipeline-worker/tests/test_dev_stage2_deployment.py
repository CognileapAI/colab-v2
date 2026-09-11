"""dev 배포 설정으로 실제 파일을 처리할 때 Stage 2 프로필이 남아야 한다."""
from pathlib import Path
import re

import numpy as np

from colab_pipeline.app.worker import stage2_declaration
from colab_pipeline.domains.d5_ingestion import IngestionService, UploadFileWork, UploadWork
from memory_ledger import MemoryLedger


def test_dev_worker_processes_body_profile_with_deployed_stage_selection(tmp_path):
    compose = (Path(__file__).resolve().parents[3] / "infra/dev/compose.yml").read_text()
    worker = re.search(r"^  pipeline-worker:\n(.*?)(?=^  \S)", compose, re.M | re.S).group(1)
    env = dict(re.findall(r"^\s+(COLAB_[A-Z0-9_]+):\s*([^\n]+)", worker, re.M))
    env = {key: value.strip().strip('\"') for key, value in env.items()}
    enabled, _ = stage2_declaration(env)
    body = tmp_path / "body.npy"
    np.save(body, np.arange(20, dtype="f4").reshape(4, 5))
    upload = "01JQ0000000000000000000003"
    lab = "01JQ0000000000000000000001"
    actor = "01JQ0000000000000000000002"
    ledger = MemoryLedger()
    ledger.accept(upload_id=upload, lab_id=lab, actor_account_id=actor)
    IngestionService(ledger).process_upload(UploadWork(
        upload_id=upload, lab_id=lab, actor_account_id=actor,
        workdir=tmp_path / "work", previews_root=tmp_path / "previews",
        files=[UploadFileWork("01JQ00000000000000000000B1", body, "본체", body.name)],
    ), stage1=not enabled)
    assert upload in ledger.grid_profiles, "dev 설정이 파일 분석/지도 프로필 생성을 건너뛴다"
    assert ledger.grid_profiles[upload]["body_shape"] == [4, 5]
    assert ledger.grid_profiles[upload]["map_state"] == "지도 없음"
    viz = re.search(r"^  viz-render:\n(.*?)(?=^  \S)", compose, re.M | re.S).group(1)
    preview = env.get("COLAB_WORKER_PREVIEW_DIR")
    assert preview and preview.startswith("/var/lib/colab/work/")
    assert re.search(r"COLAB_VIZ_PREVIEW_DIR:\s*" + re.escape(preview), viz)
    assert "work:/var/lib/colab/work" in worker
    assert "work:/var/lib/colab/work" in viz
