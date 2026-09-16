"""Issue 71: project dates persist through the real browser, API and disposable DB."""

import json
import os
from pathlib import Path

from sqlalchemy import create_engine, text


LAB = "0000000000000000000000000A"
ACCOUNT = "000000000000000000000000A1"


def run(command, args, session):
    if not args.artifacts:
        raise RuntimeError("artifacts are required")
    out = Path(args.artifacts).resolve()
    out.mkdir(parents=True, exist_ok=True)
    engine = create_engine(os.environ["E2E_DATABASE_URL"].split("\t")[0], future=True)

    def evaluate(expression):
        return json.loads(command("eval", expression).strip())

    def enter_date(selector, digits):
        command("focus", selector)
        for digit in digits:
            command("press", digit)
        command("press", "Tab")

    command("set", "viewport", "1280", "900")
    command("open", "http://127.0.0.1:43173/projects")
    command("find", "role", "button", "click", "--name", "+ 새 프로젝트", "--exact")
    command("fill", '[data-testid="project-name"]', f"일자 달력 검증 {session}")
    enter_date('[data-testid="project-period-start"]', "09162026")
    enter_date('[data-testid="project-period-end"]', "10312026")
    values = evaluate("[document.querySelector('[data-testid=project-period-start]').value, document.querySelector('[data-testid=project-period-end]').value]")
    if values != ["2026-09-16", "2026-10-31"]:
        raise AssertionError(f"date inputs did not retain calendar days: {values}")
    command("screenshot", str(out / "project-dates-before-save.png"))
    command("find", "role", "button", "click", "--name", "만들기", "--exact")
    command("wait", "h1")
    project_id = evaluate("location.pathname.split('/').pop()")
    command("reload")
    command("wait", "h1")
    page = command("get", "text", "body")
    if "2026.09.16~10.31" not in page:
        raise AssertionError("saved dates were not shown after reload")
    with engine.begin() as connection:
        if connection.execute(text("SELECT current_database()" )).scalar_one() != "colab_e2e_login":
            raise RuntimeError("only the disposable E2E database may be used")
        connection.execute(text("SET TRANSACTION READ ONLY"))
        connection.execute(text("SELECT set_config('app.current_lab', :v, true)"), {"v": LAB})
        connection.execute(text("SELECT set_config('app.current_account', :v, true)"), {"v": ACCOUNT})
        row = connection.execute(text("SELECT period_start, period_end FROM d6_project WHERE id=:id"), {"id": project_id}).mappings().one()
    stored = [row["period_start"].isoformat(), row["period_end"].isoformat()]
    if stored != ["2026-09-16", "2026-10-31"]:
        raise AssertionError(f"database dates differ: {stored}")
    command("screenshot", str(out / "project-dates-after-reload.png"))
    (out / "journey.json").write_text(json.dumps({"session": session, "projectId": project_id, "input": values, "stored": stored}, ensure_ascii=False, indent=2))
    print("PASS: #71 project dates persisted through browser, API, reload and database", flush=True)
