"""배포 상태 검사기 `ops/deploy_doctor.py` · core `GET /healthz/storage` 오라클 (`PLAN-SoT §9 〈342〉-㉲` · G2).

**red 를 먼저 봤다** — `ops/deploy_doctor.py` 가 없던 시점에 subprocess 가 파일 부재로 죽었고,
`/healthz/storage` 는 404 였다.

선례: `test_password_login.py` 가 `ops/set-password.py` 를 **subprocess** 로 부른다 — 같은 모양이다.
검사기는 값(비밀·URL 전체·키)을 출력하지 않는다 — 시험이 그 성질도 본다.

**실 AWS 는 부르지 않는다.** 버킷 인자를 주지 않으면 자격증명 항목이 ─ 라서 STS·S3 호출이
없고, 스텁 HTTP 서버(`http.server` 스레드)가 CloudFront·core 자리를 대신한다.
subprocess 환경에서 `AWS_*`·`COLAB_*` 를 걷어낸다 — 검사기는 환경변수를 읽지 않지만, 읽게
바뀌는 날 이 시험이 그것을 드러낸다.
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
import os
import pathlib
import re
import subprocess
import sys
import threading
import time
import tomllib
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from conftest import auth  # noqa: F401 — conftest 경로 확보

CORE_API = pathlib.Path(__file__).resolve().parents[1]
REPO_ROOT = CORE_API.parents[1]
DOCTOR = CORE_API / "ops" / "deploy_doctor.py"
MARKS = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮"


# ── 도구 ────────────────────────────────────────────────────────────────────

def run_doctor(*args: str) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if not k.startswith(("AWS_", "COLAB_"))}
    return subprocess.run([sys.executable, str(DOCTOR), *args],
                          capture_output=True, text=True, env=env, timeout=120)


def summary_statuses(stdout: str) -> dict[str, str]:
    """요약표의 「① 제목 …… ✓」 줄에서 항목별 상태를 뽑는다."""
    out: dict[str, str] = {}
    in_summary = False
    for line in stdout.splitlines():
        if "요약" in line and "──" in line:
            in_summary = True
            continue
        if not in_summary:
            continue
        m = re.match(r"^\s*([①-⑮])\s.*?([✓✗─])\s*$", line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def item_lines(stdout: str, mark: str) -> list[str]:
    """본문에서 그 항목의 줄들(다음 항목 머리 전까지)."""
    lines = stdout.splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.strip().startswith(mark + " "))
    body: list[str] = []
    for ln in lines[start + 1:]:
        if re.match(r"^\s*[①-⑮] ", ln) or ("요약" in ln and "──" in ln):
            break
        body.append(ln)
    return body


def load_doctor():
    """`ops/` 는 패키지가 아니다 — 파일 경로로 올린다 (dataclass 가 `sys.modules` 등록을 요구한다)."""
    if "deploy_doctor" in sys.modules:
        return sys.modules["deploy_doctor"]
    spec = importlib.util.spec_from_file_location("deploy_doctor", DOCTOR)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["deploy_doctor"] = mod
    spec.loader.exec_module(mod)
    return mod


class _Stub(BaseHTTPRequestHandler):
    routes: dict[str, tuple[int, str, bytes]] = {}

    def do_GET(self) -> None:                                     # noqa: N802
        status, ctype, body = self.routes.get(self.path, (404, "text/plain; charset=utf-8", b"no"))
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args) -> None:                         # 시험 출력을 더럽히지 않는다
        return


@pytest.fixture()
def stub_server():
    servers: list[HTTPServer] = []

    def start(routes: dict[str, tuple[int, str, bytes]]) -> str:
        handler = type("Stub", (_Stub,), {"routes": routes})
        server = HTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        servers.append(server)
        return f"http://127.0.0.1:{server.server_port}"

    yield start
    for s in servers:
        s.shutdown()
        s.server_close()


HTML = (200, "text/html; charset=utf-8", b"<!doctype html><html><body>SPA</body></html>")
JSON_401 = (401, "application/json", json.dumps({"code": "UNAUTHORIZED", "message": "x"}).encode())
NOT_FOUND = (404, "application/xml", b"<Error><Code>NoSuchKey</Code></Error>")


def storage_json(bucket: str, source: str | None = "imds") -> tuple[int, str, bytes]:
    payload = {"storageMode": "s3", "bucket": bucket, "region": "ap-northeast-2",
               "credentialSource": source}
    return 200, "application/json", json.dumps(payload).encode()


ALIVE = (200, "application/json", json.dumps({"unit": "core-api", "status": "alive"}).encode())


# ── ① 무입력 → 전 항목 ✗/─ · exit 1 ─────────────────────────────────────────

def test_인자_없이_돌리면_전_항목이_실패_또는_건너뜀이고_exit_1_이다() -> None:
    done = run_doctor()
    assert done.returncode == 1, done.stdout + done.stderr
    statuses = summary_statuses(done.stdout)
    assert len(statuses) == 15, done.stdout
    assert set(statuses.values()) <= {"✗", "─"}, statuses
    assert "✓ 0 ·" in done.stdout, "요약줄이 ✓ 건수를 말해야 한다"
    assert "─ 14" in done.stdout, "요약줄이 ─ 건수를 숨기면 안 된다"
    # ─ 줄은 「무엇을 주면 검사하는가」를 말한다
    assert "--endpoint" in done.stdout and "--db-url-file" in done.stdout


# ── ⑬ 라우팅 — /api/v1/me 가 HTML 200 이면 SPA 로 샌 것 ────────────────────

def test_api_경로가_HTML_200_이면_라우팅_항목이_실패다(stub_server) -> None:
    base = stub_server({"/": HTML, "/api/v1/me": HTML, "/previews/__probe": NOT_FOUND})
    done = run_doctor("--endpoint", base)
    assert summary_statuses(done.stdout)["⑬"] == "✗", done.stdout
    assert "SPA" in "\n".join(item_lines(done.stdout, "⑬"))
    assert done.returncode == 1


def test_api_경로가_JSON_401_이면_라우팅_항목이_통과다(stub_server) -> None:
    base = stub_server({"/": HTML, "/api/v1/me": JSON_401, "/previews/__probe": NOT_FOUND})
    done = run_doctor("--endpoint", base)
    assert summary_statuses(done.stdout)["⑬"] == "✓", done.stdout
    lines = "\n".join(item_lines(done.stdout, "⑬"))
    assert "401" in lines and "404" in lines


def test_previews_가_HTML_로_새면_실패다(stub_server) -> None:
    base = stub_server({"/": HTML, "/api/v1/me": JSON_401, "/previews/__probe": HTML})
    done = run_doctor("--endpoint", base)
    assert summary_statuses(done.stdout)["⑬"] == "✗", done.stdout


# ── ⑧ RLS 판정기 — FORCE 결손 ✗ (판정기 단위 시험) ──────────────────────────

def _green_facts() -> list[tuple[str, str, str, str, str]]:
    """allow-list 정본에서 「통과하는 최소 facts」를 만든다 — 목록을 시험에 다시 적지 않는다."""
    cfg = tomllib.loads((REPO_ROOT / "gates/config/rls-allowlist.toml").read_text(encoding="utf-8"))
    lab, body = cfg["policy_naming"]["lab_boundary"], cfg["policy_naming"]["body_access"]
    rows: list[tuple[str, str, str, str, str]] = []
    for chain in ("platform", "ai"):
        sec = cfg[chain]
        for t in sec["allow_no_rls"]:
            rows.append((chain, t, "f", "f", ""))
        for t in sec["body_tables"]:
            rows.append((chain, t, "t", "t", f"{body},{lab}"))
        rows.append((chain, f"d0_{chain}_probe", "t", "t", lab))
    return rows


def test_RLS_판정기는_FORCE_빠진_표를_실패로_본다() -> None:
    dd = load_doctor()
    ok, _out = dd.judge_rls_facts(_green_facts())
    assert ok is True, _out
    weakened = [(c, t, r, "f" if t.startswith("d0_platform") else f, p)
                for c, t, r, f, p in _green_facts()]
    ok, out = dd.judge_rls_facts(weakened)
    assert ok is False
    assert "FORCE" in out


def test_RLS_판정기는_한_체인이_0건이면_실패다() -> None:
    dd = load_doctor()
    only_platform = [row for row in _green_facts() if row[0] == "platform"]
    ok, out = dd.judge_rls_facts(only_platform)
    assert ok is False and "0건" in out


# ── ⑫ 환경 짝 — 접미사 불일치 ✗ ────────────────────────────────────────────

def test_env_dev_인데_앱_버킷이_prod_면_환경_짝이_실패다(stub_server) -> None:
    base = stub_server({"/healthz": ALIVE, "/healthz/storage": storage_json("colab-data-prod")})
    done = run_doctor("--env", "dev", "--app-base", base)
    statuses = summary_statuses(done.stdout)
    assert statuses["⑪"] == "✓", done.stdout          # imds · s3 — 출처 자체는 맞다
    assert statuses["⑫"] == "✗", done.stdout
    assert done.returncode == 1


def test_env_dev_이고_앱_버킷이_dev_면_환경_짝이_통과다(stub_server) -> None:
    base = stub_server({"/healthz": ALIVE, "/healthz/storage": storage_json("colab-data-dev")})
    done = run_doctor("--env", "dev", "--app-base", base)
    assert summary_statuses(done.stdout)["⑫"] == "✓", done.stdout


def test_앱_자격증명_출처가_env_면_실패다(stub_server) -> None:
    base = stub_server({"/healthz": ALIVE, "/healthz/storage": storage_json("colab-data-dev", "env")})
    done = run_doctor("--env", "dev", "--app-base", base)
    assert summary_statuses(done.stdout)["⑪"] == "✗", done.stdout


def test_환경_짝_판정_함수_인자_버킷과_DB_호스트() -> None:
    dd = load_doctor()
    rows = dd.env_pair_findings("dev", app_bucket=None, bucket_arg="colab-data-prod",
                                web_bucket=None, hosts={"platform": "colab-dev.x.rds.amazonaws.com",
                                                        "ai": None})
    by_label = {label: status for status, label, _detail in rows}
    assert by_label["--bucket"] == dd.BAD
    assert by_label["DB 호스트(platform)"] == dd.OK
    assert by_label["DB 호스트(ai)"] == dd.SKIP


# ── ⑥⑦ 스키마 head — 불일치 ✗ ──────────────────────────────────────────────

def test_head_불일치는_실패이고_일치는_통과다() -> None:
    dd = load_doctor()
    head, detail = dd.repo_head("ai")
    assert head, detail
    assert dd.judge_head("ai", [head])[0] == dd.OK
    status, detail = dd.judge_head("ai", ["0000_없는_리비전"])
    assert status == dd.BAD and head in detail
    assert dd.judge_head("ai", [])[0] == dd.BAD                   # 행 0건은 통과가 아니다
    assert dd.judge_head("platform", [head, head])[0] == dd.BAD   # 행 2건도 아니다


# ── ④⑨ 실 DB(시험 DB) — 연결·롤 속성 · 값 미출력 ────────────────────────────

def test_시험_DB_로_연결_항목과_롤_속성이_통과이고_비밀이_출력에_없다(app_db_url, tmp_path) -> None:
    f = tmp_path / "platform.url"
    f.write_text(app_db_url + "\n", encoding="utf-8")
    f.chmod(0o600)
    done = run_doctor("--db-url-file", str(f))
    statuses = summary_statuses(done.stdout)
    assert statuses["④"] == "✓", done.stdout
    assert statuses["⑨"] == "✓", done.stdout
    assert statuses["⑤"] == "─" and statuses["⑧"] == "─", statuses
    secret = urllib.parse.urlsplit(app_db_url).password
    assert secret and secret not in done.stdout and secret not in done.stderr
    assert app_db_url not in done.stdout


def test_DB_URL_파일이_0600_이_아니면_실패다(app_db_url, tmp_path) -> None:
    f = tmp_path / "platform.url"
    f.write_text(app_db_url, encoding="utf-8")
    f.chmod(0o644)
    done = run_doctor("--db-url-file", str(f))
    assert summary_statuses(done.stdout)["④"] == "✗", done.stdout
    assert "0600" in "\n".join(item_lines(done.stdout, "④"))


# ── 판정 규칙 — ─ 는 통과가 아니다 ──────────────────────────────────────────

def test_판정_규칙_건너뜀은_통과가_아니다() -> None:
    dd = load_doctor()
    assert dd.verdict([dd.SKIP] * 14)[0] == 1
    assert dd.verdict([dd.OK] * 13 + [dd.BAD])[0] == 1
    # 아무 말 없이 ─ 가 남으면 실패 — 면제는 명시해야 한다 (green-by-skip 금지의 같은 모양)
    code, text = dd.verdict([dd.OK] + [dd.SKIP] * 13)
    assert code == 1 and "─ 13" in text and "--allow-skip" in text
    code, text = dd.verdict([dd.OK] + [dd.SKIP] * 13, allow_skip=True)
    assert code == 0 and "─ 13" in text
    assert text.split("\n")[-1].strip().startswith("부분 통과 · 면제 명시")
    code, text = dd.verdict([dd.OK] * 14)
    assert code == 0 and "─ 0" in text
    assert text.split("\n")[-1].strip().startswith("전 항목 통과")


# ── core `GET /healthz/storage` ─────────────────────────────────────────────

def _s3_mode(client):
    from colab_core.kernel.config import Settings
    app = client.app
    app.state.settings = Settings(**{**app.state.settings.__dict__, "storage_mode": "s3",
                                     "s3_bucket": "test-bucket", "s3_region": "ap-northeast-2"})
    return client


@pytest.fixture()
def no_ambient_creds(monkeypatch):
    from colab_core.kernel import aws_credentials
    for k in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN",
              "AWS_CONTAINER_CREDENTIALS_RELATIVE_URI"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr(aws_credentials, "_from_imds", lambda: None)   # 노트북에서 IMDS 를 두드리지 않는다
    aws_credentials.clear_cache()
    yield
    aws_credentials.clear_cache()


def test_healthz_storage_local_모드(p2_client) -> None:
    res = p2_client().get("/healthz/storage")
    assert res.status_code == 200
    assert res.json() == {"storageMode": "local"}


def test_healthz_storage_s3_모드_자격증명_없음(p2_client, no_ambient_creds) -> None:
    res = _s3_mode(p2_client()).get("/healthz/storage")
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["storageMode"] == "s3" and body["bucket"] == "test-bucket"
    assert body["credentialSource"] is None
    assert body["error"]


def test_healthz_storage_s3_모드_출처와_만료만_실린다(p2_client, no_ambient_creds, monkeypatch) -> None:
    from colab_core.kernel import aws_credentials
    from colab_core.kernel.sigv4 import Credentials
    expires = dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=5)
    creds = Credentials(access_key="AKIAFAKEFAKEFAKEFAKE", secret_key="fake-secret-0123",
                        session_token="fake-session-token", expires_at=expires)
    monkeypatch.setattr(aws_credentials, "load_credentials", lambda now=None: (creds, "imds"))
    res = _s3_mode(p2_client()).get("/healthz/storage")
    body = res.json()
    assert body["credentialSource"] == "imds"
    assert body["expiresAt"] == expires.isoformat()
    for secret in ("AKIAFAKEFAKEFAKEFAKE", "fake-secret-0123", "fake-session-token"):
        assert secret not in res.text


def test_healthz_storage_는_1초를_넘기지_않는다(p2_client, no_ambient_creds, monkeypatch) -> None:
    from colab_core.kernel import aws_credentials

    def slow(now=None):
        time.sleep(3)
        raise RuntimeError("늦다")

    monkeypatch.setattr(aws_credentials, "load_credentials", slow)
    t0 = time.monotonic()
    res = _s3_mode(p2_client()).get("/healthz/storage")
    assert time.monotonic() - t0 < 2.5
    body = res.json()
    assert body["credentialSource"] is None and body["error"]


# ── ⑮ 실행 sha ∈ main — `MAIN_SHA` 대조 (WU-D3) ─────────────────────────────
# EC2 에 git 이 없다. 그래서 판정은 **문자열 대조**다 — `ship.sh` 가 반입할 때 적어 둔
# `MAIN_SHA` 한 줄과 `CURRENT_SHA` 를 맞춰 본다. 파일이 없다는 것은 반입 게이트를 거치지
# 않았다는 뜻이라 ─(준비)가 아니라 **✗** 다(spec 우려 4 ⓐ — ─ 로 두면 옛 반입이 영원히 통과한다).

SHIP_SH = REPO_ROOT / "infra" / "dev" / "ship.sh"
ANC_A, ANC_B = "a1b2c3d4e5f6", "9f8e7d6c5b4a"


def state_dir(tmp_path, current: str, main_line: str | None) -> str:
    """`/opt/colab-v2` 마운트를 흉내낸다 — `CURRENT_SHA` ＋ `MAIN_SHA`."""
    d = tmp_path / "state"
    d.mkdir()
    (d / "CURRENT_SHA").write_text(current + "\n", encoding="utf-8")
    if main_line is not None:
        (d / "MAIN_SHA").write_text(main_line + "\n", encoding="utf-8")
    return str(d)


def item15(*args: str) -> tuple[str, list[str]]:
    done = run_doctor(*args)
    return summary_statuses(done.stdout).get("⑮", ""), item_lines(done.stdout, "⑮")


def test_반입_sha_가_main_조상이고_후보가_일치하면_15번째_항목이_통과다(tmp_path) -> None:
    d = state_dir(tmp_path, ANC_A, f"main={ANC_B} candidate={ANC_A} ancestor=yes")
    status, body = item15("--state-dir", d)
    assert status == "✓", body


def test_우회_반입은_실패이고_사유가_남는다(tmp_path) -> None:
    d = state_dir(tmp_path, ANC_A, f"main={ANC_B} candidate={ANC_A} ancestor=bypass")
    status, body = item15("--state-dir", d)
    assert status == "✗", body
    assert any("우회" in ln for ln in body), body


def test_조상이_아니라고_적힌_반입은_실패다(tmp_path) -> None:
    d = state_dir(tmp_path, ANC_A, f"main={ANC_B} candidate={ANC_A} ancestor=no")
    status, body = item15("--state-dir", d)
    assert status == "✗", body


def test_MAIN_SHA_파일이_없으면_실패이고_사유는_파일_없음이다(tmp_path) -> None:
    d = state_dir(tmp_path, ANC_A, None)
    status, body = item15("--state-dir", d)
    assert status == "✗", body
    assert any("파일 없음" in ln for ln in body), body
    assert not any("마운트 없음" in ln for ln in body), "마운트 부재와 파일 부재는 사유가 달라야 한다"


def test_state_디렉터리가_마운트되지_않으면_실패이고_사유는_마운트_없음이다(tmp_path) -> None:
    status, body = item15("--state-dir", str(tmp_path / "없는자리"))
    assert status == "✗", body
    assert any("마운트 없음" in ln for ln in body), body
    assert any("/opt/colab-v2:/state:ro" in ln for ln in body), "고치는 법이 사유에 있어야 한다"


def test_MAIN_SHA_형식이_다르면_실패이고_사유는_형식_불일치다(tmp_path) -> None:
    d = state_dir(tmp_path, ANC_A, "nonmain:a1b2c3d4e5f6")   # 폐기된 옛 표기
    status, body = item15("--state-dir", d)
    assert status == "✗", body
    assert any("형식" in ln for ln in body), body


def test_후보가_실행_sha_와_다르면_실패다(tmp_path) -> None:
    d = state_dir(tmp_path, ANC_A, f"main={ANC_B} candidate={ANC_B} ancestor=yes")
    status, body = item15("--state-dir", d)
    assert status == "✗", body
    assert any("불일치" in ln for ln in body), body


def test_요약줄이_항목_15_를_말하고_MARKS_가_15_다(tmp_path) -> None:
    d = state_dir(tmp_path, ANC_A, f"main={ANC_B} candidate={ANC_A} ancestor=yes")
    done = run_doctor("--state-dir", d)
    assert "항목 15" in done.stdout, done.stdout
    assert len(load_doctor().MARKS) == 15


def test_docker_run_명령이_state_를_읽기_전용으로_마운트한다() -> None:
    """마운트가 없으면 ⑮ 는 영원히 ✗ 다 — 점검기와 운영 문서가 같은 자리를 말해야 한다."""
    deploy_md = (REPO_ROOT / "docs" / "DEPLOY.md").read_text(encoding="utf-8")
    assert "-v /opt/colab-v2:/state:ro" in deploy_md


def test_ship_sh_가_적는_형식을_점검기가_그대로_읽는다(tmp_path) -> None:
    """생산자·소비자 한 계약 — `ship.sh` 의 printf 형식이 바뀌면 여기서 red 가 난다."""
    ship = SHIP_SH.read_text(encoding="utf-8")
    m = re.search(r"printf '([^']*)'.*MAIN_SHA", ship)
    assert m, "ship.sh 에서 MAIN_SHA 를 적는 printf 형식을 찾지 못했다"
    fmt = m.group(1).replace("\\n", "")
    assert fmt.count("%s") == 3, fmt
    line = fmt.replace("%s", "{}", 3).format(ANC_B, ANC_A, "yes")
    d = state_dir(tmp_path, ANC_A, line)
    status, body = item15("--state-dir", d)
    assert status == "✓", f"ship.sh 형식 「{line}」 을 점검기가 읽지 못한다 · {body}"
