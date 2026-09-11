"""e2e-login.sh의 일회용 서비스에서 직접 격자 업로드 → 재사용 → 저장을 검증한다."""
import json
import os
from pathlib import Path
import subprocess
import tempfile

from sqlalchemy import create_engine, text


def run(command, args, session):
    if not args.pipeline_python or not args.viz_python or not args.artifacts:
        raise RuntimeError("grid journey requires pipeline-python, viz-python and artifacts")
    root = Path(__file__).resolve().parents[1]
    evidence = {"session": session, "steps": [], "datasets": [],
                "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
                "source": "current dirty checkout", "url": "http://127.0.0.1:43173"}
    out = args.artifacts.resolve()
    out.mkdir(parents=True, exist_ok=True)

    def record(step):
        evidence["steps"].append(step)
        (out / "journey.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2))
        print("PASS:", step, flush=True)

    def click(testid):
        selector = f'[data-testid="{testid}"]'
        command("scrollintoview", selector)
        command("click", selector)

    def wait(testid):
        command("wait", f'[data-testid="{testid}"]')

    def register(name):
        click("reg-next")
        wait("reg-name")
        command("fill", '[data-testid="reg-name"]', name)
        command("fill", '[data-testid="reg-summary"]', "격리 환경 격자 가져오기 실검증")
        click("reg-next")
        wait("reg-done")
        click("reg-done")
        command("wait", "--fn", '!document.querySelector(\'[data-testid="upload-modal"]\')')
        wait("detail-header")
        dataset_id = command("get", "url").strip().rstrip("/").split("/")[-1]
        command("reload")
        wait("detail-header")
        command("wait", "--fn", "Array.from(document.querySelectorAll('[data-testid=preview-single-image]')).some(i => i.complete && i.naturalWidth > 0)")
        if name not in command("get", "text", '[data-testid="detail-header"]'):
            raise AssertionError("dataset name did not persist after reload")
        evidence["datasets"].append(dataset_id)
        return dataset_id

    with tempfile.TemporaryDirectory(prefix="colab-grid-fixture-") as fixture:
        fixture = Path(fixture)
        subprocess.run([str(args.pipeline_python.absolute()), "-c", """
import numpy as np, sys
from pathlib import Path
p = Path(sys.argv[1])
np.save(p / 'body.npy', np.arange(20, dtype='f4').reshape(4, 5))
np.save(p / 'lat.npy', np.repeat(np.linspace(31., 34., 4)[:, None], 5, axis=1))
np.save(p / 'lon.npy', np.repeat(np.linspace(124., 128., 5)[None, :], 4, axis=0))
""", str(fixture)], check=True, timeout=30)
        command("set", "viewport", "1440", "1000")
        names = ["격자 원본 " + session, "격자 재사용 " + session]
        for index, name in enumerate(names):
            command("find", "role", "button", "click", "--name", "업로드", "--exact")
            command("upload", '[data-testid="up-drop-input"]', str(fixture / "body.npy"))
            command("wait", '[data-testid="up-analyze"][data-stage="3"]')
            if index == 0:
                click("reg-open")
                wait("up-grid-input")
                command("upload", '[data-testid="up-grid-input"]', str(fixture / "lat.npy"), str(fixture / "lon.npy"))
            else:
                click("reg-open")
                diagnostic = create_engine(os.environ["E2E_DATABASE_URL"], future=True)
                try:
                    with diagnostic.begin() as connection:
                        connection.execute(text("SET TRANSACTION READ ONLY"))
                        connection.execute(text("SELECT set_config('app.current_lab', :lab, true)"),
                                           {"lab": "0000000000000000000000000A"})
                        evidence["candidateInputs"] = {
                            "datasets": [dict(row) for row in connection.execute(text("SELECT dataset_id, body_shape, grid_shape, grid_digest, map_state FROM d3_dataset_grid_profile")).mappings()],
                            "uploads": [dict(row) for row in connection.execute(text("SELECT upload_id, body_shape, grid_shape, grid_digest, map_state FROM d5_upload_grid_profile")).mappings()],
                        }
                finally:
                    diagnostic.dispose()
                record("candidate inputs captured from isolated DB")
                (out / "candidate-screen.txt").write_text(command("snapshot"))
                command("wait", f'[aria-label={json.dumps(names[0] + " 가져오기", ensure_ascii=False)}]')
                command("find", "role", "button", "click", "--name", names[0] + " 가져오기", "--exact")
            wait("up-grid-accept")
            click("up-grid-accept")
            register(name)
            command("screenshot", str(out / f"dataset-{index + 1}.png"))
            record("direct grid registration persists" if index == 0 else "reused grid registration persists and renders after reload")

        engine = create_engine(os.environ["E2E_DATABASE_URL"], future=True)
        try:
            with engine.begin() as connection:
                connection.execute(text("SET TRANSACTION READ ONLY"))
                connection.execute(text("SELECT set_config('app.current_lab', :lab, true)"),
                                   {"lab": "0000000000000000000000000A"})
                rows = [dict(connection.execute(text("""
                    SELECT grid_digest, west, south, east, north, map_state
                      FROM d3_dataset_grid_profile WHERE dataset_id=:dataset
                """), {"dataset": dataset}).mappings().one()) for dataset in evidence["datasets"]]
                if rows[0] != rows[1] or rows[0]["map_state"] != "지도 있음":
                    raise AssertionError("copied grid digest, bounds or map state differs from direct upload")
                if [rows[0][key] for key in ("west", "south", "east", "north")] != [124, 31, 128, 34]:
                    raise AssertionError("stored bounds differ from actual fixture coordinates")
                target = {"dataset": evidence["datasets"][1]}
                activity = connection.execute(text("SELECT count(*) FROM d8_activity WHERE target_id=:dataset AND action='격자 가져오기'"), target).scalar_one()
                lineage = connection.execute(text("SELECT count(*) FROM d4_lineage_edge WHERE child_dataset_id=:dataset OR parent_dataset_id=:dataset"), target).scalar_one()
                if activity != 1 or lineage != 0:
                    raise AssertionError("grid reuse activity is not exactly one or lineage was modified")
                evidence["profiles"] = rows
        finally:
            engine.dispose()
        record("actual DB: identical digest/bounds/map state; one reuse activity; zero lineage edges")
        command("open", "http://127.0.0.1:43173/datasets")
        command("wait", '[aria-label="지도 상태"]')
        command("select", '[aria-label="지도 상태"]', "지도 있음")
        command("wait", "--text", names[1])
        command("select", '[aria-label="지도 상태"]', "지도 없음")
        command("wait", "--fn", f'!document.body.innerText.includes({json.dumps(names[1])})')
        record("catalog map-state filter includes and excludes the saved dataset")
