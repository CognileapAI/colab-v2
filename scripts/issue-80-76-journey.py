"""Issues 80/76: real browser, API and disposable database value preservation."""

import hashlib
import json
import os
from pathlib import Path

from sqlalchemy import create_engine, text


LAB = "0000000000000000000000000A"
ACCOUNT = "000000000000000000000000A1"
LOW = "0000000000000000000000DSA1"
HIGH = "0000000000000000000000DSA2"


def run(command, args, session):
    if not args.artifacts or not args.upload_file:
        raise RuntimeError("artifacts and real upload fixture are required")
    out = Path(args.artifacts).resolve()
    out.mkdir(parents=True, exist_ok=True)
    evidence = {"session": session, "environment": "disposable local API/DB", "steps": []}
    root = Path(__file__).resolve().parents[1]
    evidence["sourceHashes"] = {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (
            root / "frontend/src/components/upload/UploadModal.tsx",
            root / "frontend/src/components/lineage/LineageStep.tsx",
            root / "frontend/src/components/detail/DatasetEditForm.tsx",
            root / "frontend/src/components/detail/editFields.ts",
            root / "frontend/src/components/upload/PeriodCalendarPopover.tsx",
        )
    }
    engine = create_engine(os.environ["E2E_DATABASE_URL"].split("\t")[0], future=True)

    def db(query, values=None, *, fixture=False):
        with engine.begin() as connection:
            if connection.execute(text("SELECT current_database()")).scalar_one() != "colab_e2e_login":
                raise RuntimeError("only the disposable E2E database may be used")
            if not fixture:
                connection.execute(text("SET TRANSACTION READ ONLY"))
            connection.execute(text("SELECT set_config('app.current_lab', :v, true)"), {"v": LAB})
            connection.execute(text("SELECT set_config('app.current_account', :v, true)"), {"v": ACCOUNT})
            result = connection.execute(text(query), values or {})
            return [dict(row) for row in result.mappings()] if result.returns_rows else []

    def persist():
        (out / "journey.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2))

    def record(step, **values):
        evidence["steps"].append({"step": step, **values})
        persist()
        print("PASS:", step, flush=True)

    def selector(testid):
        return f'[data-testid="{testid}"]'

    def wait(testid):
        command("wait", selector(testid))

    def click(testid):
        command("scrollintoview", selector(testid))
        command("click", selector(testid))

    def fill(testid, value):
        command("fill", selector(testid), value)

    def evaluate(expression):
        return json.loads(command("eval", expression).strip())

    def assert_dom(expression, message):
        if not evaluate(expression):
            raise AssertionError(message)

    def capture(name):
        (out / f"{name}.txt").write_text(command("snapshot"))
        command("screenshot", str(out / f"{name}.png"))

    def period(dataset_id):
        rows = db("""SELECT to_char(period_start AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS') AS start,
                     to_char(period_end AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS') AS end,
                     period_granularity AS unit
                FROM d3_dataset_autometa WHERE dataset_id=:id""", {"id": dataset_id})
        if len(rows) != 1:
            raise AssertionError("expected exactly one period row")
        return rows[0]

    def edit_open():
        command("wait", '[data-testid="detail-edit-open"]:not(:disabled)')
        click("detail-edit-open")
        wait("detail-edit-save")

    def save_reload():
        click("detail-edit-save")
        command("wait", '[data-testid="detail-edit-open"]:not(:disabled)')
        command("reload")
        command("wait", '[data-testid="detail-edit-open"]:not(:disabled)')

    def step(number):
        target = f'[data-testid="reg-steps"] button:nth-of-type({number})'
        command("focus", target)
        command("press", "Enter")
        wait({1: "reg-level", 2: "reg-name", 3: "lin-add"}[number])

    def connect(dataset_id):
        click("lin-add")
        wait(f"lin-pick-{dataset_id}")
        click(f"lin-pick-{dataset_id}")
        command("find", "role", "button", "click", "--name", "이 데이터로 연결", "--exact")
        wait("lin-card")

    try:
        # Fixture preparation only; later browser operations must persist through the real API.
        db("UPDATE d3_dataset SET processing_level_user_set=:level WHERE id=:id",
           {"level": "Lv0", "id": LOW}, fixture=True)
        db("UPDATE d3_dataset SET processing_level_user_set=:level WHERE id=:id",
           {"level": "Lv2", "id": HIGH}, fixture=True)
        db("""UPDATE d3_dataset_autometa SET period_start='2026-09-18T23:30:17Z',
               period_end='2026-09-19T01:45:29Z', period_granularity='분' WHERE dataset_id=:id""",
           {"id": LOW}, fixture=True)
        original = period(LOW)
        evidence["fixture"] = {"period": original, "lowDatasetId": LOW, "highDatasetId": HIGH}
        persist()
        command("set", "viewport", "1440", "1100")
        command("open", f"http://127.0.0.1:43173/datasets/{LOW}")
        wait("detail-edit-open")
        edit_open()
        capture("01-period-edit")
        # This assertion fails on the pre-fix date-only editor.
        wait("edit-period-open")
        click("edit-period-open")
        wait("reg-period-pop-start-minute")
        assert_dom("document.querySelector('[data-testid=reg-period-pop-start-hour]').value === '23' && "
                   "document.querySelector('[data-testid=reg-period-pop-start-minute]').value === '30'",
                   "minute precision was not displayed")
        assert_dom("(()=>{const b=document.querySelector('[data-testid=edit-period-open]');return b.scrollHeight<=b.clientHeight+2})()",
                   "period trigger text overflows its height")
        capture("02-period-minute-input")
        command("set", "viewport", "390", "844")
        command("scrollintoview", selector("edit-period-open"))
        assert_dom("(()=>{const r=document.querySelector('[data-testid=reg-period-pop]').getBoundingClientRect();return r.left>=0&&r.right<=innerWidth})()",
                   "period popup overflows the narrow viewport")
        capture("02b-period-narrow-input")
        command("set", "viewport", "1440", "1100")
        click("reg-period-apply")
        save_reload()
        if period(LOW) != original:
            raise AssertionError("untouched apply lost sub-minute original timestamps")
        record("#76 no-op period apply preserved exact original timestamps", period=original)

        edit_open()
        fill("edit-summary", "기간 보존 브라우저 검증")
        save_reload()
        if period(LOW) != original:
            raise AssertionError("unrelated edit changed the period")
        record("#76 other-field save and reload preserved timestamps")

        edit_open()
        click("edit-period-open")
        fill("reg-period-pop-start-minute", "35")
        click("reg-period-apply")
        save_reload()
        changed = period(LOW)
        if changed != {"start": "2026-09-18 23:35:00", "end": "2026-09-19 01:45:00", "unit": "분"}:
            raise AssertionError(f"minute edit persisted unexpected values: {changed}")
        edit_open()
        click("edit-period-open")
        assert_dom("document.querySelector('[data-testid=reg-period-pop-start-minute]').value === '35'",
                   "saved minute did not reopen")
        capture("03-period-saved-reopened")
        click("reg-period-unit-일")
        click("reg-period-apply")
        save_reload()
        if period(LOW) != {"start": "2026-09-18 00:00:00", "end": "2026-09-19 00:00:00", "unit": "일"}:
            raise AssertionError("coarser precision did not discard hidden time")
        record("#76 minute edit and explicit day conversion persisted after reload")

        # Null granularity must not silently become day precision on no-op apply.
        db("""UPDATE d3_dataset_autometa SET period_start='2026-09-18T23:30:17Z',
               period_end=NULL, period_granularity=NULL WHERE dataset_id=:id""", {"id": LOW}, fixture=True)
        command("reload")
        wait("detail-edit-open")
        null_unit = period(LOW)
        edit_open()
        click("edit-period-open")
        click("reg-period-apply")
        fill("edit-summary", "미지정 단위와 시각 보존 검증")
        save_reload()
        if period(LOW) != null_unit:
            raise AssertionError("null granularity or open end changed on unrelated edit")
        record("#76 null granularity and open end preserved on no-op apply and text save")

        command("find", "role", "button", "click", "--name", "업로드", "--exact")
        command("upload", selector("up-drop-input"), str(Path(args.upload_file).resolve()))
        command("wait", '[data-testid="up-analyze"][data-stage="3"]')
        command("wait", '[data-testid="reg-open"]:not(:disabled)')
        click("reg-open")
        wait("reg-level")
        assert_dom("document.querySelector('[data-testid=reg-level]').value === 'Lv0'", "initial level is not Lv0")
        for testid in ("reg-category", "reg-datatype"):
            value = evaluate(f"document.querySelector({json.dumps(selector(testid))}).querySelector('option:not([value=\"\"])').value")
            command("select", selector(testid), value)
        step(2)
        fill("reg-name", "계보 단계 보존 " + session)
        fill("reg-summary", "실제 브라우저 등록과 단계 유지 검증")
        click("reg-period-open")
        click("reg-period-unit-일")
        for side in ("start", "end"):
            for part, value in (("year", "2026"), ("month", "09"), ("day", "18")):
                fill(f"reg-period-pop-{side}-{part}", value)
        click("reg-period-apply")
        step(3)
        click("lin-add")
        wait(f"lin-pick-{HIGH}")
        assert_dom(f"document.querySelector('[data-testid=lin-pick-{HIGH}]').disabled", "untouched Lv0 allowed a higher parent")
        assert_dom(f"!document.querySelector('[data-testid=lin-pick-{LOW}]').disabled", "same-level parent was rejected")
        capture("04-default-level-parent-limit")
        click(f"lin-pick-{LOW}")
        command("find", "role", "button", "click", "--name", "이 데이터로 연결", "--exact")
        wait("lin-card")
        step(1)
        assert_dom("document.querySelector('[data-testid=reg-level]').value === 'Lv0'", "same-level connection overwrote Lv0")
        step(3)
        click("lin-del")
        step(1)
        assert_dom("document.querySelector('[data-testid=reg-level]').value === 'Lv0'", "disconnect changed Lv0")
        command("select", selector("reg-level"), "Lv2")
        step(3)
        connect(HIGH)
        step(1)
        assert_dom("document.querySelector('[data-testid=reg-level]').value === 'Lv2'", "explicit level changed after connection")
        command("select", selector("reg-level"), "Lv0")
        step(3)
        wait("lin-conflict-note")
        assert_dom("document.querySelectorAll('[data-testid=lin-card]').length === 1 && document.querySelector('[data-testid=reg-done]').disabled",
                   "lowering level did not retain card and block registration")
        capture("05-lowered-level-conflict")
        step(1)
        command("select", selector("reg-level"), "Lv2")
        step(3)
        assert_dom("!document.querySelector('[data-testid=reg-done]').disabled", "raising level did not resolve conflict")
        click("lin-del")
        step(1)
        assert_dom("document.querySelector('[data-testid=reg-level]').value === 'Lv2'", "disconnect overwrote explicit level")
        step(3)
        connect(HIGH)
        record("#80 default/explicit level, same-level connection, disconnect, step round-trip and conflict checks")
        click("reg-done")
        wait("detail-header")
        command("wait", "--fn", "!document.querySelector('[data-testid=upload-modal]')")
        dataset_id = command("get", "url").strip().rstrip("/").split("/")[-1]
        command("reload")
        wait("detail-header")
        saved = db("SELECT processing_level_user_set AS level FROM d3_dataset WHERE id=:id", {"id": dataset_id})
        parents = db("SELECT parent_dataset_id AS parent FROM d4_lineage_edge WHERE child_dataset_id=:id", {"id": dataset_id})
        if saved != [{"level": "Lv2"}] or parents != [{"parent": HIGH}]:
            raise AssertionError(f"registered level/parent mismatch: {saved}, {parents}")
        capture("06-registered-level-after-reload")
        record("#80 selected level and parent persisted after real registration and reload", datasetId=dataset_id, level="Lv2")
        evidence["status"] = "passed"
        persist()
    except Exception as error:
        evidence["status"] = "failed"
        evidence["failure"] = str(error)
        persist()
        try:
            capture("failure")
        except Exception:
            pass
        raise
    finally:
        engine.dispose()
