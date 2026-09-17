"""Browser proof for issues #33, #41, and #42 on the disposable E2E stack."""

import hashlib
import json
import os
from pathlib import Path

from sqlalchemy import create_engine, text


LAB_ID = "0000000000000000000000000A"
ACCOUNT_ID = "000000000000000000000000A1"


def run(command, args, session):
    if not args.upload_file or not args.artifacts or not args.viz_python:
        raise RuntimeError("journey requires upload-file, artifacts, and viz-python")
    source = args.upload_file.resolve()
    out = args.artifacts.resolve()
    out.mkdir(parents=True, exist_ok=True)
    evidence = {
        "session": session,
        "source": source.name,
        "sourceBytes": source.stat().st_size,
        "sourceSha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "steps": [],
    }

    def record(step, **values):
        evidence["steps"].append({"step": step, **values})
        (out / "journey.json").write_text(
            json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print("PASS:", step, flush=True)

    def snapshot(name):
        (out / f"{name}.txt").write_text(command("snapshot"), encoding="utf-8")
        command("screenshot", str(out / f"{name}.png"))

    def click(testid):
        selector = f'[data-testid="{testid}"]'
        command("scrollintoview", selector)
        command("click", selector)

    def wait(testid):
        command("wait", f'[data-testid="{testid}"]')

    def db_rows(query, values=None):
        engine = create_engine(os.environ["E2E_DATABASE_URL"].split("\t")[0], pool_pre_ping=True, future=True)
        try:
            with engine.begin() as connection:
                connection.execute(text("SET TRANSACTION READ ONLY"))
                connection.execute(
                    text("SELECT set_config('app.current_lab', :value, true)"), {"value": LAB_ID}
                )
                connection.execute(
                    text("SELECT set_config('app.current_account', :value, true)"),
                    {"value": ACCOUNT_ID},
                )
                return [dict(row) for row in connection.execute(text(query), values or {}).mappings()]
        finally:
            engine.dispose()

    try:
        command("set", "viewport", "1440", "1000")
        command("find", "role", "button", "click", "--name", "업로드", "--exact")
        command("upload", '[data-testid="up-drop-input"]', str(source))
        command("wait", '[data-testid="up-analyze"][data-stage="3"]')
        upload_rows = db_rows(
            """
            SELECT u.id AS upload_id, u.registered_at
              FROM d5_upload u
              JOIN d5_upload_file f ON f.upload_id = u.id
             WHERE f.file_name = :name AND u.lab_id = :lab
             ORDER BY u.created_at DESC LIMIT 1
            """,
            {"name": source.name, "lab": LAB_ID},
        )
        if len(upload_rows) != 1 or upload_rows[0]["registered_at"] is not None:
            raise AssertionError("actual unregistered upload was not found")
        upload_id = upload_rows[0]["upload_id"]
        snapshot("01-upload-analyzed")
        record("actual GeoTIFF upload reached completed analysis before registration", uploadId=upload_id)

        click("upload-close")
        command("wait", "--fn", "!document.querySelector('[data-testid=upload-modal]') || !!document.querySelector('[data-testid=upload-close-confirm]')")
        if int(command("get", "count", '[data-testid="upload-close-confirm"]').strip()):
            command("find", "role", "button", "click", "--name", "닫고 나가기", "--exact")
        command("wait", "--fn", "!document.querySelector('[data-testid=upload-modal]')")
        command("reload")
        command("wait", f'[data-testid="unfinished-register-{upload_id}"]')
        snapshot("02-unfinished-after-reload")
        click(f"unfinished-register-{upload_id}")
        wait("reg-steps")
        wait("reg-category")
        restored_file = command("get", "text", '[data-testid="reg-file"]').strip()
        if source.name not in restored_file:
            raise AssertionError("registration recovery did not restore the uploaded filename")
        snapshot("03-registration-restored")
        record("registration step 1 restored after reload without re-upload", uploadId=upload_id)

        for selector in ('[data-testid="reg-category"]', '[data-testid="reg-datatype"]'):
            value = json.loads(
                command(
                    "eval",
                    f"document.querySelector({json.dumps(selector)}).querySelector('option:not([value=\"\"])').value",
                ).strip()
            )
            command("select", selector, value)
        click("reg-next")
        wait("reg-name")
        dataset_name = "User feature journey " + session
        command("fill", '[data-testid="reg-name"]', dataset_name)
        command("fill", '[data-testid="reg-summary"]', "Reload recovery and preview proof")
        click("reg-period-open")
        click("reg-period-unit-일")
        for side, values in (("start", ("2026", "09", "15")), ("end", ("2026", "09", "16"))):
            for field, value in zip(("year", "month", "day"), values):
                command("fill", f'[data-testid="reg-period-pop-{side}-{field}"]', value)
        click("reg-period-apply")
        click("reg-next")
        wait("reg-done")
        wait("reg-proj-select")
        registration_project = json.loads(command(
            "eval",
            "document.querySelector('[data-testid=reg-proj-select] option:not([value=\"\"])').value",
        ).strip())
        command("select", '[data-testid="reg-proj-select"]', registration_project)
        click("reg-proj-add")
        wait("reg-proj-table")
        if int(command("get", "count", '[data-testid="reg-proj-row-name"]').strip()) != 1:
            raise AssertionError("clicking the registration add button did not add exactly one project")
        snapshot("03b-registration-project-click")
        record("registration project add button added a row by pointer click", projectId=registration_project)
        click("reg-done")
        command("wait", "--fn", "!document.querySelector('[data-testid=upload-modal]')")
        wait("detail-header")
        dataset_url = command("get", "url").strip()
        dataset_id = dataset_url.rstrip("/").split("/")[-1]
        transition = db_rows(
            """
            SELECT u.id AS upload_id, u.registered_at, count(DISTINCT f.dataset_id) AS datasets,
                   min(f.dataset_id) AS dataset_id
              FROM d5_upload u
              JOIN d5_upload_file uf ON uf.upload_id = u.id
              JOIN d3_file f ON f.id = uf.id
             WHERE u.id = :upload_id
             GROUP BY u.id, u.registered_at
            """,
            {"upload_id": upload_id},
        )
        if (
            len(transition) != 1
            or transition[0]["registered_at"] is None
            or transition[0]["datasets"] != 1
            or transition[0]["dataset_id"] != dataset_id
        ):
            raise AssertionError("dataset was not registered from the recovered uploadId")
        uploads = db_rows(
            "SELECT count(DISTINCT upload_id) AS count FROM d5_upload_file WHERE file_name=:name AND lab_id=:lab",
            {"name": source.name, "lab": LAB_ID},
        )
        if uploads[0]["count"] != 1:
            raise AssertionError("registration recovery created another upload")
        record("recovered uploadId became exactly the opened dataset", datasetId=dataset_id)

        command("wait", '[data-testid="dt-preview-slot"][data-preview-slot-state="done"]')
        command(
            "wait",
            "--fn",
            "Array.from(document.querySelectorAll('[data-testid=dt-preview-slot][data-preview-slot-state=done] [data-testid=preview-single-image],[data-testid=dt-preview-slot][data-preview-slot-state=done] [data-testid=preview-tile]')).some(i=>i.complete&&i.naturalWidth>0)",
        )
        command("scrollintoview", '[data-testid="dt-preview-slot"]')
        snapshot("04-detail-preview")
        record("registered dataset preview reached a decoded terminal image")

        command("reload")
        wait("detail-header")
        wait(f"usage-project-unlink-{registration_project}")
        if len(db_rows(
            "SELECT project_id FROM d6_project_dataset WHERE dataset_id=:dataset AND project_id=:project",
            {"dataset": dataset_id, "project": registration_project},
        )) != 1:
            raise AssertionError("project added by registration click did not persist")
        record("registration project click persisted after registration and reload", projectId=registration_project)
        click(f"usage-project-unlink-{registration_project}")
        command("wait", "--fn", f"!document.querySelector('[data-testid=usage-project-unlink-{registration_project}]')")
        command("reload")
        wait("detail-header")
        wait("usage-project-select")
        if db_rows(
            "SELECT project_id FROM d6_project_dataset WHERE dataset_id=:dataset AND project_id=:project",
            {"dataset": dataset_id, "project": registration_project},
        ):
            raise AssertionError("registration project link remains after detail removal")
        record("registration project was removed through dataset detail", projectId=registration_project)

        wait("usage-project-select")
        project_id = json.loads(
            command(
                "eval",
                "document.querySelector('[data-testid=usage-project-select] option:not([value=\"\"])').value",
            ).strip()
        )
        command("select", '[data-testid="usage-project-select"]', project_id)
        click("usage-project-add")
        command("wait", '[data-testid="usage-count"]')
        command("wait", f'[data-testid="usage-project-unlink-{project_id}"]')
        command("reload")
        wait("detail-header")
        command("wait", f'[data-testid="usage-project-unlink-{project_id}"]')
        linked = db_rows(
            "SELECT project_id FROM d6_project_dataset WHERE dataset_id=:dataset AND project_id=:project",
            {"dataset": dataset_id, "project": project_id},
        )
        if len(linked) != 1:
            raise AssertionError("project link did not persist on the server")
        snapshot("05-project-linked")
        record("project attachment persisted after detail reload", projectId=project_id)

        click(f"usage-project-unlink-{project_id}")
        command("wait", "--fn", f"!document.querySelector('[data-testid=usage-project-unlink-{project_id}]')")
        command("reload")
        wait("detail-header")
        if int(command("get", "count", f'[data-testid="usage-project-unlink-{project_id}"]').strip()):
            raise AssertionError("removed project returned after reload")
        if db_rows(
            "SELECT project_id FROM d6_project_dataset WHERE dataset_id=:dataset AND project_id=:project",
            {"dataset": dataset_id, "project": project_id},
        ):
            raise AssertionError("project link remains on the server after removal")
        snapshot("06-project-removed")
        record("project removal persisted after detail reload", projectId=project_id)
    except Exception as error:
        evidence["failure"] = str(error)
        (out / "journey.json").write_text(
            json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        snapshot("failure")
        raise
