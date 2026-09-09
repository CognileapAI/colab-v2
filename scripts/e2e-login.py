"""격리 DB를 사용하는 실제 core-api + agent-browser 로그인/재접속 회귀.

E2E_DATABASE_URL은 일회용 fixture DB만 받는다. 운영 환경 파일을 읽지 않는다.
run through e2e-login.sh; all children and the browser session are closed on exit.
"""
import argparse
import json
import os
from pathlib import Path
import re
import secrets
import signal
import subprocess
import sys
import tempfile
import time
import urllib.request
import urllib.error
import urllib.parse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/core-api/src"))
from colab_core.kernel.password import hash_password


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--frontend-root", required=True, type=Path)
    parser.add_argument("--inspect", action="store_true")
    parser.add_argument("--inspect-upload", action="store_true")
    parser.add_argument("--upload", action="store_true", help="Validate real supported-format processing and registration")
    parser.add_argument("--upload-file", type=Path)
    parser.add_argument("--preview-only", action="store_true")
    parser.add_argument("--require-variable-selection", action="store_true")
    parser.add_argument("--pipeline-python", type=Path)
    parser.add_argument("--viz-python", type=Path)
    parser.add_argument("--journey", type=Path, help="Explicit local browser scenario module")
    parser.add_argument("--artifacts", type=Path, help="Persistent scenario evidence directory")
    parser.add_argument("--extra-file", type=Path, action="append", default=[])
    parser.add_argument("--grid-file", type=Path, action="append", default=[])
    parser.add_argument("--connections", action="store_true", help="Verify project and lineage persistence")
    args = parser.parse_args()
    if args.upload and not args.pipeline_python:
        parser.error("--upload requires --pipeline-python")
    frontend = args.frontend_root.resolve()
    head = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"])
    if subprocess.check_output(["git", "-C", str(frontend), "rev-parse", "HEAD"]) != head:
        raise RuntimeError("Frontend and backend must use the same HEAD")
    # 외부 사본의 의존성을 재사용할 때는 실제 실행 소스가 이번 사본과 같아야 한다.
    # 현재 사본 자체는 미커밋 제품 변경도 검증할 수 있어야 한다.
    if frontend != ROOT / "frontend":
        for relative in ("src", "index.html", "vite.config.ts", "package.json", "package-lock.json"):
            subprocess.run(["git", "diff", "--no-index", "--quiet",
                            str(ROOT / "frontend" / relative), str(frontend / relative)], check=True)
    browser = Path.home() / ".npm-global/bin/agent-browser"
    if not browser.is_file():
        raise RuntimeError("agent-browser is unavailable")
    db = os.environ["E2E_DATABASE_URL"]
    session = "colab-login-" + secrets.token_hex(5)
    password = secrets.token_urlsafe(24)
    base = {k: v for k, v in os.environ.items() if k in ("PATH", "HOME", "LANG", "TMPDIR")}
    processes = []
    with tempfile.TemporaryDirectory(prefix="colab-login-") as temp:
        temp = Path(temp)
        if (args.inspect_upload or args.upload) and args.pipeline_python and not args.upload_file:
            args.upload_file = temp / "e2e-geotiff.tif"
            subprocess.run([str(args.pipeline_python), "-c",
                "from pathlib import Path; import sys; from fixture_builders import make_readable_geotiff; make_readable_geotiff(Path(sys.argv[1]))",
                str(args.upload_file)], check=True, timeout=30,
                env={**base, "PYTHONPATH": str(ROOT / "services/pipeline-worker/tests")})
        if args.upload_file and (not args.upload_file.is_file() or args.upload_file.stat().st_size == 0):
            raise RuntimeError("Upload fixture must exist and contain real bytes")
        credential = temp / "credentials.json"
        credential.write_text(json.dumps({"e2e-researcher": {
            "accountId": "000000000000000000000000A1",
            "labId": "0000000000000000000000000A",
            **hash_password(password).as_dict(),
        }}))
        credential.chmod(0o600)
        env = {**base, "PYTHONPATH": str(ROOT / "services/core-api/src"),
               "COLAB_CORE_DATABASE_URL": db,
               "COLAB_CORE_SUBJECTS_FILE": str(ROOT / "services/core-api/tests/fixtures/subjects.json"),
               "COLAB_CORE_CREDENTIALS_FILE": str(credential),
               "COLAB_CORE_SESSION_SECRET": secrets.token_urlsafe(48),
               "COLAB_CORE_UPLOAD_DIR": str(temp / "uploads"),
               "COLAB_E2E_RUN": session}
        (temp / "uploads").mkdir()
        viz_token = secrets.token_urlsafe(32)
        if args.viz_python:
            env.update(COLAB_CORE_VIZ_BASE_URL="http://127.0.0.1:8003/viz/v1",
                       COLAB_CORE_VIZ_SERVICE_TOKEN=viz_token)
        log = (temp / "server.log").open("w")

        def command(*parts, private=False):
            # Credential-bearing commands use stdin, never argv or logs.
            if private:
                call = [str(browser), "--session", session, "batch", "--bail"]
                result = subprocess.run(call, input=json.dumps([list(parts)]), text=True,
                                        capture_output=True, env=base, timeout=40)
            else:
                result = subprocess.run([str(browser), "--session", session, *parts],
                                        text=True, capture_output=True, env=base, timeout=40)
            if result.returncode:
                raise RuntimeError((result.stderr or result.stdout).replace(password, "[redacted]"))
            return result.stdout

        def wait_url(url, *, owned=False, status=200):
            for _ in range(60):
                if any(p.poll() is not None for p in processes):
                    raise RuntimeError("An isolated app process exited before readiness")
                try:
                    try:
                        response = urllib.request.urlopen(url, timeout=1)
                    except urllib.error.HTTPError as error:
                        response = error
                    with response:
                        if owned and response.headers.get("X-CoLAB-E2E-Run") != session:
                            raise RuntimeError("Readiness reached a server outside this E2E run")
                        if response.status == status:
                            return
                except OSError:
                    pass
                time.sleep(.5)
            raise RuntimeError("Isolated app readiness timeout")

        browser_started = False
        try:
            if args.viz_python:
                viz_env = {**base, "PYTHONPATH": str(ROOT / "services/viz-render/src"),
                    "COLAB_E2E_RUN": session, "COLAB_VIZ_SERVICE_TOKEN": viz_token,
                    "COLAB_VIZ_TILE_SIGNING_SECRET": secrets.token_urlsafe(48),
                    "COLAB_VIZ_SOURCE_ROOT": str(temp / "uploads"),
                    "COLAB_VIZ_PREVIEW_URL_BASE": "http://127.0.0.1:8003/previews",
                    "COLAB_VIZ_PREVIEW_DIR": str(temp / "previews")}
                (temp / "previews").mkdir(exist_ok=True)
                processes.append(subprocess.Popen([str(args.viz_python), str(Path(__file__).resolve()), "--serve-viz"],
                    cwd=ROOT, env=viz_env, stdout=log, stderr=log))
                wait_url("http://127.0.0.1:8003/healthz", owned=True)
            processes.append(subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--serve"],
                cwd=ROOT, env=env, stdout=log, stderr=log))
            wait_url("http://127.0.0.1:8000/healthz", owned=True)
            processes.append(subprocess.Popen(["node", "node_modules/vite/bin/vite.js",
                "--host", "127.0.0.1", "--port", "43173", "--strictPort"],
                cwd=frontend, env=base, stdout=log, stderr=log))
            wait_url("http://127.0.0.1:43173/")
            wait_url("http://127.0.0.1:43173/api/v1/me", owned=True, status=401)
            if args.pipeline_python:
                worker_env = {**base,
                    "PYTHONPATH": str(ROOT / "services/pipeline-worker/src"),
                    "COLAB_PIPELINE_DB_URL": db,
                    "COLAB_WORKER_STORAGE_MODE": "local",
                    "COLAB_WORKER_UPLOAD_DIR": str(temp / "uploads"),
                    "COLAB_WORKER_STAGE2": "on",
                    "COLAB_WORKER_PREVIEW_DIR": str(temp / "previews"),
                    "COLAB_WORKER_EVENT_SPOOL": str(temp / "events")}
                processes.append(subprocess.Popen([str(args.pipeline_python), "-c",
                    "from colab_pipeline.app.worker import serve; serve(0.5)"],
                    cwd=ROOT, env=worker_env, stdout=log, stderr=log))
            browser_started = True
            command("open", "http://127.0.0.1:43173/")
            first = command("snapshot", "-i")
            if 'button "들어가기" [disabled' not in first:
                raise RuntimeError("Empty login submission is not disabled")
            account = re.search(r'textbox "계정" \[ref=(e\d+)\]', first)
            secret = re.search(r'textbox "비밀번호" \[ref=(e\d+)\]', first)
            if not account or not secret:
                raise RuntimeError("Login inputs missing")
            command("fill", "@" + account[1], "e2e-researcher")
            command("fill", "@" + secret[1], "invalid-e2e-password", private=True)
            command("click", '[data-testid="login-submit"]')
            command("wait", "--text", "계정 또는 비밀번호가 맞지 않아요.")
            rejected = command("snapshot", "-i")
            if "로그아웃" in rejected:
                raise RuntimeError("Invalid credentials established a session")
            command("fill", '[data-testid="login-password"]', password, private=True)
            filled = command("snapshot", "-i")
            submit = re.search(r'button "들어가기" \[ref=(e\d+)\]', filled)
            if not submit:
                raise RuntimeError("Filled login submission unavailable")
            command("click", "@" + submit[1])
            command("wait", "--text", "로그아웃")
            command("reload")
            command("wait", "--text", "로그아웃")
            logged_in = command("snapshot", "-i")
            if args.journey:
                import importlib.util
                spec = importlib.util.spec_from_file_location("colab_journey", args.journey.resolve())
                journey = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(journey)
                journey.run(command, args, session)
                logged_in = command("snapshot", "-i")
            if args.inspect:
                print(logged_in)
            if args.inspect_upload or args.upload:
                upload = re.search(r'button "업로드" \[ref=(e\d+)\]', logged_in)
                if not upload:
                    raise RuntimeError("Upload action missing")
                command("click", "@" + upload[1])
                if args.upload_file:
                    command("upload", '[data-testid="up-drop-input"]', str(args.upload_file.resolve()))
                    command("wait", "--text", args.upload_file.name)
                    if args.viz_python and args.require_variable_selection:
                        command(
                            "wait",
                            "--fn",
                            "document.querySelectorAll('[data-testid=up-pick-variable] option').length >= 2",
                        )
                        variable_selector = '[data-testid="up-pick-variable"]'
                        option_count = int(command("get", "count", variable_selector + " option").strip())
                        if option_count < 2:
                            raise RuntimeError("second preview variable is required")
                        selected_target = json.loads(command("eval", "document.querySelector('[data-testid=up-pick-variable]').options[1].value").strip())
                        selected_label = json.loads(command("eval", "document.querySelector('[data-testid=up-pick-variable]').options[1].textContent").strip())
                        if not selected_target.startswith(("hdf5:", "grib:")):
                            raise RuntimeError("second preview variable has no stable format selection ID: " + selected_target)
                        command("select", variable_selector, selected_target)
                        selected_value = command("get", "value", variable_selector).strip()
                        if selected_value != selected_target:
                            raise RuntimeError(f"preview variable selection did not stick: {selected_value!r} != {selected_target!r}")
                        command("focus", '[data-testid="up-preview-draw"]')
                        focused = json.loads(command("eval", "document.activeElement?.dataset?.testid || ''").strip())
                        if focused != "up-preview-draw":
                            raise RuntimeError("Preview draw action did not receive keyboard focus")
                        command("press", "Enter")
                        rendered_selector = '[data-testid="up-preview-image"], [data-testid="up-preview-tile"]'
                        selected_json = json.dumps(selected_target)
                        command("wait", "--fn", f'Array.from(document.querySelectorAll(\'{rendered_selector}\')).some(img => img.dataset.previewVariable === {selected_json} && img.complete && img.naturalWidth > 0)')
                        rendered = json.loads(command("eval", f'JSON.stringify(Array.from(document.querySelectorAll(\'{rendered_selector}\')).find(img => img.dataset.previewVariable === {selected_json})?.getAttribute("src") || "")').strip())
                        rendered_variable = selected_target if rendered else ""
                        rendered_path = urllib.parse.urlsplit(rendered).path
                        if not rendered_path.endswith(".png"):
                            raise RuntimeError("rendered preview is not a PNG: " + rendered_path)
                        if rendered_variable != selected_target:
                            raise RuntimeError(f"rendered variable does not match selected ID: {rendered_variable!r} != {selected_target!r}")
                        print("PASS: explicit second preview variable selected through agent-browser and rendered:",
                              json.dumps({"selectionId": selected_target, "label": selected_label,
                                          "renderedVariable": rendered_variable,
                                          "imagePath": rendered_path}, ensure_ascii=False))
                        if args.preview_only:
                            print("PASS: upload, variable selection, and rendered preview image load completed")
                            return
                        command("eval", "(() => { const b=document.querySelector('[data-testid=up-grid-skip]'); if(b){b.click(); return true;} return false; })()")
                    command("click", '[data-testid="reg-open"]')
                    if args.pipeline_python:
                        command("wait", '[data-testid="reg-next"]:not(:disabled)')
                        registration = command("snapshot", "-i")
                        next_button = re.search(r'button "다음 →" \[ref=(e\d+)\]', registration)
                        if not next_button:
                            raise RuntimeError("Enabled registration next action missing")
                        command("focus", "@" + next_button[1])
                        focused = json.loads(command("eval", "document.activeElement?.dataset?.testid || ''").strip())
                        if focused != "reg-next":
                            raise RuntimeError("Registration next action did not receive keyboard focus")
                        command("press", "Enter")
                        command("wait", '[data-testid="reg-name"]')
                        command("fill", '[data-testid="reg-name"]', "E2E " + args.upload_file.stem + " " + session)
                        command("click", '[data-testid="reg-next"]')
                        command("wait", '[data-testid="reg-done"]')
                        command("click", '[data-testid="reg-done"]')
                        command("wait", '[data-testid="reg-summary-error"]')
                        command("fill", '[data-testid="reg-summary"]', "Isolated supported-format E2E")
                        command("click", '[data-testid="reg-next"]')
                        command("wait", '[data-testid="reg-done"]')
                        command("click", '[data-testid="reg-done"]')
                        command("wait", "--fn", '!document.querySelector(\'[data-testid="upload-modal"]\')')
                        if args.viz_python:
                            command("wait", "--fn", 'Array.from(document.querySelectorAll(\'[data-testid="preview-single-image"]\')).some(img => img.complete && img.naturalWidth > 0)')
                if args.inspect_upload:
                    print("INSPECT ONLY: upload flow; no upload acceptance claimed")
                    print(command("snapshot"))
                    return
                command("wait", '[data-testid="detail-header"]')
                command("reload")
                command("wait", '[data-testid="detail-header"]')
                if args.viz_python:
                    command("wait", "--fn", 'Array.from(document.querySelectorAll(\'[data-testid="preview-single-image"]\')).some(img => img.complete && img.naturalWidth > 0)')
                    artifact = ROOT / ".codex/artifacts/product-e2e-preview.png"
                    artifact.parent.mkdir(parents=True, exist_ok=True)
                    command("screenshot", str(artifact))
                detail = command("snapshot")
                for expected in ("E2E " + args.upload_file.stem + " " + session,
                                 "Isolated supported-format E2E", args.upload_file.name):
                    if expected not in detail:
                        raise RuntimeError("Registered dataset did not retain expected metadata: " + expected)
                if args.upload_file.name == "e2e-geotiff.tif":
                    for expected in ("EPSG:4326", "300x300"):
                        if expected not in detail:
                            raise RuntimeError("GeoTIFF regression lost expected metadata: " + expected)
                if any(p.poll() is not None for p in processes):
                    raise RuntimeError("An isolated service exited during upload verification")
                logged_in = command("snapshot", "-i")
            logout = re.search(r'button "로그아웃" \[ref=(e\d+)\]', logged_in)
            if not logout:
                raise RuntimeError("Authenticated session did not survive reload")
            command("click", "@" + logout[1])
            command("wait", "--text", "계정은 개발자가 만들어 드려요.")
            if 'textbox "비밀번호"' not in command("snapshot", "-i"):
                raise RuntimeError("Logout did not return to login")
        except Exception:
            if (args.inspect_upload or args.upload) and browser_started:
                try:
                    print(command("snapshot"))
                except Exception:
                    print("Failure snapshot unavailable", file=sys.stderr)
            log.flush()
            diagnostic = (temp / "server.log").read_text(errors="replace")[-5000:]
            print(diagnostic.replace(password, "[redacted]").replace(viz_token, "[redacted]").replace(db, "[disposable-db]"), file=sys.stderr)
            raise
        finally:
            cleanup_error = None
            try:
                if browser_started:
                    subprocess.run([str(browser), "--session", session, "close"], env=base,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   timeout=15, check=True)
            except (subprocess.SubprocessError, OSError) as error:
                cleanup_error = error
            for process in reversed(processes):
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            log.close()
            if cleanup_error:
                raise RuntimeError("E2E browser cleanup failed") from cleanup_error
    print("PASS: empty login disabled; invalid login rejected; real login; reload persists session; logout returns to login; app/browser/temp cleanup completed")
    if args.upload:
        print("PASS: real supported-format upload and worker processing; missing description rejected; registration and metadata persist after reload.")
        print("PASS: rendered preview image loads before and after reload" if args.viz_python else "Map rendering not tested.")


if __name__ == "__main__":
    if sys.argv[1:] in (["--serve"], ["--serve-viz"]):
        import uvicorn
        if sys.argv[1] == "--serve-viz":
            from colab_viz.app.main import create_app
            port = 8003
        else:
            from colab_core.app.main import create_app
            port = 8000
        app = create_app()
        if port == 8003:
            from fastapi.staticfiles import StaticFiles
            app.mount("/previews", StaticFiles(directory=os.environ["COLAB_VIZ_PREVIEW_DIR"]), name="e2e-previews")

        @app.middleware("http")
        async def identify_run(request, call_next):
            response = await call_next(request)
            response.headers["X-CoLAB-E2E-Run"] = os.environ["COLAB_E2E_RUN"]
            return response

        uvicorn.run(app, host="127.0.0.1", port=port)
    else:
        def interrupted(signum, frame):
            raise KeyboardInterrupt("E2E interrupted")
        signal.signal(signal.SIGTERM, interrupted)
        main()
