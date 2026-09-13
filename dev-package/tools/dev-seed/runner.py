#!/usr/bin/env python3
"""dev 환경 실투입 러너 — agent-browser 로 실제 화면을 조작한다.

- 입력 = upload-plan.json (프로젝트 4 · 데이터셋 28 · 간선 18)
- 시나리오 = dev-package/scenarios/dev-minimal-data-setup.md 2·4·5·6·7 절
- 지목점 = dev-package/reports/r-dev-reset/agent-browser-capability.md 6 절
- 상태 = state.json (단계별 status · 화면에서 회수한 데이터셋 id · 시각)
- 표준 라이브러리만 사용. 단계는 멱등이고 재실행이 중단 지점을 이어 받는다.

주의 = 비밀번호는 argv 에 싣지 않는다. 표준입력으로만 넘긴다(--allow-argv-secret 로만 예외).
주의 = 등록 확정(reg-done)은 자동 재시도하지 않는다. 실패하면 덤프 후 비영 종료한다.
"""

import argparse
import getpass
import json
import os
import re
import secrets
import shlex
import stat
import string
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parent
DEFAULT_WORK_DIR = TOOL_DIR / ".work"

# 작업 자리 — 상태·로그·갈무리·자격 파일이 전부 이 아래에만 생긴다.
# 기본값은 이 폴더의 `.work/` 이고 레포 `.gitignore` 가 제외한다. `--work-dir` 로 옮긴다.
# ⛔ 레포 안에 절대경로를 적지 않는다(CLAUDE.md §5) — 자리는 인자·환경변수로만 받는다.
WORK_DIR = DEFAULT_WORK_DIR
PLAN_PATH = WORK_DIR / "upload-plan.json"
STATE_PATH = WORK_DIR / "state.json"
LOG_DIR = WORK_DIR / "logs"
SHOT_DIR = WORK_DIR / "shots"
FAIL_DIR = WORK_DIR / "fail"
VERIFY_PATH = WORK_DIR / "verify.json"
INITIAL_PW_PATH = WORK_DIR / "initial-password.txt"
NEW_PW_PATH = WORK_DIR / "new-password.txt"


def set_work_dir(work_dir, plan=None):
    """작업 자리를 정하고 그 아래 경로 전부를 다시 건다."""
    global WORK_DIR, PLAN_PATH, STATE_PATH, LOG_DIR, SHOT_DIR, FAIL_DIR
    global VERIFY_PATH, INITIAL_PW_PATH, NEW_PW_PATH
    WORK_DIR = Path(work_dir).expanduser().resolve()
    PLAN_PATH = Path(plan).expanduser().resolve() if plan else WORK_DIR / "upload-plan.json"
    STATE_PATH = WORK_DIR / "state.json"
    LOG_DIR = WORK_DIR / "logs"
    SHOT_DIR = WORK_DIR / "shots"
    FAIL_DIR = WORK_DIR / "fail"
    VERIFY_PATH = WORK_DIR / "verify.json"
    INITIAL_PW_PATH = WORK_DIR / "initial-password.txt"
    NEW_PW_PATH = WORK_DIR / "new-password.txt"


# 주소는 자리값을 코드에 두지 않는다 — `--base-url` 또는 `COLAB_DEV_URL`.
# dev 주소의 원본은 `docs/DEPLOY.md` · `.claude/rules/deploy.md` 다.
DEFAULT_URL = None
DEFAULT_SESSION = "colab-dev"
JS_SUB = "e" + "val"

PREVIEW_SEQS = [
    [15, "grib"],
    [17, "nc"],
    [19, "bin"],
    [21, "tif"],
    [25, "hdf4"],
]

# 미리보기 렌더를 판정하는 순번(포맷 5종) — 이 순번의 분석 실패는 건너뛰지 않는다.
PREVIEW_FORMAT_SEQS = set(x[0] for x in PREVIEW_SEQS)

ULID_RE = re.compile(r"/datasets/([0-9A-HJKMNP-TV-Za-hjkmnp-tv-z]{20,32})")
ANALYZE_DONE_CSS = '[data-testid="up-analyze"][data-stage="3"]'
PROJECT_ULID_RE = re.compile(r"/projects/([0-9A-HJKMNP-TV-Za-hjkmnp-tv-z]{20,32})")

# ── 「가공 단계」(Lv) ────────────────────────────────────────────────────────
# 저장값 4값의 원본 = frontend/src/components/upload/axisDict.ts `PROCESSING_LEVELS`.
# 러너는 **계획값을 매 행 명시 지정**한다 — 화면 기본값(`Lv2`)에도, 계보 자동 채움에도
# 기대지 않는다. 선택지가 빈 값으로 시작하도록 바뀌어도 같은 동작이 선다.
LEVEL_CSS = '[data-testid="reg-level"]'
PROCESSING_LEVELS = ("Lv0", "Lv1", "Lv2", "Lv3")

# 등록이 성립한 상태값. `done` 은 옛 상태 파일의 값이라 그대로 센다(하위 호환).
REGISTERED_STATUSES = ("done", "registered", "registered_no_preview")

SECRET_MARK = "***"

# ── 계정 관리 화면 = frontend/src/routes/AccountAdminPage.tsx · 경로 `/account-admin` ──
# ⚠ 칸에는 `data-testid` 가 없다. 구역만 `account-create` 이고 칸은 form `name` 이다.
#    `name` 은 화면이 FormData 로 직접 읽는 계약값이라 문면 변경에 흔들리지 않는다.
#    칸별 testid 부재는 후속 항목으로 올린다(NOTE 참조).
ACCOUNT_PATH = "/account-admin"
ACCOUNT_SECTION_CSS = '[data-testid="account-create"]'
ACCOUNT_CSS = {
    "name": ACCOUNT_SECTION_CSS + ' input[name="name"]',
    "email": ACCOUNT_SECTION_CSS + ' input[name="email"]',
    "lab": ACCOUNT_SECTION_CSS + ' select[name="labId"]',
    "role": ACCOUNT_SECTION_CSS + ' select[name="role"]',
    "password": ACCOUNT_SECTION_CSS + ' input[name="initialPassword"]',
    "admin": ACCOUNT_SECTION_CSS + ' input[name="operator"]',
    "submit": ACCOUNT_SECTION_CSS + ' button[type="submit"]',
    "status": ACCOUNT_SECTION_CSS + ' [role="status"]',
}
ACCOUNT_ROLES = ("교수", "연구원")

CFG = None
LOG_FH = None


def now():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def log(msg, echo=True):
    line = "[" + now() + "] " + str(msg)
    if LOG_FH:
        LOG_FH.write(line + "\n")
        LOG_FH.flush()
    if echo:
        print(line, flush=True)


def load_state():
    if STATE_PATH.exists():
        # 옛 상태 파일(version 1 · `accounts` 없음)도 그대로 읽는다 — 빠진 칸만 채운다.
        st = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        for key in ["steps", "projects", "datasets", "selectors", "accounts"]:
            if not isinstance(st.get(key), dict):
                st[key] = dict()
        return st
    st = dict()
    st["version"] = 1
    st["created"] = now()
    st["base_url"] = None
    st["session"] = None
    st["account"] = None
    st["password_rotated"] = False
    st["steps"] = dict()
    st["projects"] = dict()
    st["datasets"] = dict()
    st["selectors"] = dict()
    st["accounts"] = dict()
    return st


def save_state(st):
    if CFG and CFG.dry_run:
        return
    st["updated"] = now()
    tmp = STATE_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(STATE_PATH)


def mark_step(st, name, status, **extra):
    row = st["steps"].get(name) or dict()
    row["status"] = status
    row["at"] = now()
    row.update(extra)
    st["steps"][name] = row
    save_state(st)


class Fail(Exception):
    """단계 실패 — 덤프 후 비영 종료."""


class Blocked(Exception):
    """등록 불가 — 이 순번만 기록하고 다음 순번으로 간다(중단하지 않는다)."""


# ══════════════ 판정 함수 — 브라우저 없이 도는 자리(단위 시험 대상) ══════════════
# 시험 = tests/test_runner_plan_mapping.py. 화면을 부르지 않으므로 `CFG` 도 쓰지 않는다.


def is_registered(status):
    """등록이 성립한 상태값인가. 옛 상태 파일의 `done` 도 센다."""
    return str(status or "") in REGISTERED_STATUSES


def level_action(ds, options=None):
    """계획 한 행 → 「가공 단계」 선택 동작 한 개.

    `options` = 화면 select 가 실제로 가진 값들. 계획값이 그 안에 없으면
    **이름을 실어** 그 행만 실패시킨다(다른 행으로 옮겨 붙이지 않는다).
    """
    name = str(ds.get("name") or ("순번 " + str(ds.get("seq"))))
    value = str(ds.get("processing_level") or "").strip()
    if not value:
        raise Fail("가공 단계 값이 계획에 없다: " + name)
    if value not in PROCESSING_LEVELS:
        raise Fail("가공 단계 값이 정본 4값 밖이다: " + name + " · " + value)
    if options is not None and value not in list(options):
        raise Fail("가공 단계 선택지에 없는 값: " + name + " · " + value
                   + " · 화면 선택지 = " + ",".join(str(o) for o in options))
    return ["select", LEVEL_CSS, value]


def failure_path(reg_open_exists, reg_open_enabled, reason):
    """분석 실패 자리의 갈림. 반환 = (결정 · 사유).

    ⭑ 2026-09-14 개정 — 종전에는 「보기만 할게요」(reg-viewonly)로 모달을 닫아
    **데이터셋이 아예 생기지 않았다.** 화면이 분석 실패에서도 등록을 허용하도록
    바뀌었으므로(배너 축자 「등록은 됩니다」) 등록 결정 게이트가 열리면 그대로 등록한다.
    `blocked` 은 대기 뒤에도 `reg-open` 이 비활성인 자리에만 남는다.
    """
    text = str(reason or "")
    if not reg_open_exists:
        return "blocked", text + " · 등록 결정 게이트(reg-open)가 화면에 없다"
    if not reg_open_enabled:
        return "blocked", text + " · reg-open 이 대기 뒤에도 비활성으로 남았다"
    return "register", text


def read_secret_file(path, what):
    """0600 자격 파일 한 줄. 권한이 느슨하면 **고치지 않고 거절한다.**

    (`read_password_file` 은 옛 자격 파일용이라 0600 으로 조여 주고 잇는다 — 이쪽은
    사람이 만들어 넣는 파일이라 조용히 고치지 않는다.)
    """
    path = Path(path)
    if not path.exists():
        raise Fail(what + " 파일 없음: " + path.name + " (0600 으로 만들어 둔다)")
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & 0o077:
        raise Fail(what + " 파일 권한이 0600 이 아니다: " + path.name
                   + " · 현재 " + oct(mode) + " · `chmod 600` 후 다시 실행한다")
    value = path.read_text(encoding="utf-8").strip()
    if not value:
        raise Fail(what + " 파일이 비었다: " + path.name)
    return value


def load_accounts_file(path):
    """계정 목록 파일(0600 · JSON) → 항목 목록.

    항목 = {email · name · role · admin(불)} ＋ 선택 `lab`(연구실 이름).
    **비밀번호는 이 파일에 두지 않는다** — 별도 0600 파일 또는 표준입력이다.
    """
    path = Path(path)
    if not path.exists():
        raise Fail("계정 파일 없음: " + path.name)
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & 0o077:
        raise Fail("계정 파일 권한이 0600 이 아니다: " + path.name
                   + " · 현재 " + oct(mode) + " · `chmod 600` 후 다시 실행한다")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        raw = raw.get("accounts")
    if not isinstance(raw, list) or not raw:
        raise Fail("계정 파일이 목록이 아니거나 비었다: " + path.name)
    out = []
    for i, item in enumerate(raw):
        who = str((item or dict()).get("email") if isinstance(item, dict) else "") \
            or ("항목 " + str(i + 1))
        if not isinstance(item, dict):
            raise Fail("계정 항목이 객체가 아니다: " + who)
        if "initialPassword" in item or "password" in item:
            raise Fail("계정 파일에 비밀번호를 두지 않는다(별도 0600 파일 · 표준입력): " + who)
        entry = dict()
        for key in ["email", "name", "role"]:
            val = str(item.get(key) or "").strip()
            if not val:
                raise Fail("계정 항목에 " + key + " 가 없다: " + who)
            entry[key] = val
        if entry["role"] not in ACCOUNT_ROLES:
            raise Fail("계정 역할이 정본 2값 밖이다: " + who + " · " + entry["role"])
        admin = item.get("admin")
        if not isinstance(admin, bool):
            raise Fail("계정 항목의 admin 이 불 값이 아니다: " + who + " · " + repr(admin))
        entry["admin"] = admin
        lab = item.get("lab")
        if lab:
            entry["lab"] = str(lab).strip()
        out.append(entry)
    return out


def account_form_actions(entry):
    """계정 추가 한 건의 동작 목록.

    ⚠ 비밀번호는 **자리(`secret`)만** 싣고 값은 싣지 않는다 — 이 목록은 기록·상태
    파일로 흘러갈 수 있다. 값은 실행 시점에 `fill_secret`(표준입력 경로)이 넣는다.
    「첫 로그인 비밀번호 변경 강제」는 화면에 칸이 없다 — 서버가 늘 강제하므로 건드리지 않는다.
    """
    actions = [
        ["fill", ACCOUNT_CSS["name"], entry["name"]],
        ["fill", ACCOUNT_CSS["email"], entry["email"]],
        ["select", ACCOUNT_CSS["role"], entry["role"]],
    ]
    if entry.get("lab"):
        actions.append(["select-label", ACCOUNT_CSS["lab"], entry["lab"]])
    if entry.get("admin"):
        actions.append(["check", ACCOUNT_CSS["admin"]])
    actions.append(["secret", ACCOUNT_CSS["password"]])
    actions.append(["activate", ACCOUNT_CSS["submit"]])
    return actions


def account_state_row(entry, status, message=""):
    """상태 파일에 남길 한 행. 비밀번호 칸이 없다."""
    row = dict()
    row["email"] = entry["email"]
    row["name"] = entry["name"]
    row["role"] = entry["role"]
    row["admin"] = bool(entry.get("admin"))
    if entry.get("lab"):
        row["lab"] = entry["lab"]
    row["status"] = status
    row["message"] = str(message or "")[:200]
    row["at"] = now()
    return row


def account_log_line(entry):
    """기록 한 줄. 비밀번호 자리는 자리표뿐이다."""
    return ("계정 " + entry["email"] + " · " + entry["name"] + " · " + entry["role"]
            + " · 관리자 " + ("예" if entry.get("admin") else "아니오")
            + " · 초기 비밀번호 " + SECRET_MARK)


def ab_env():
    env = dict(os.environ)
    env["AGENT_BROWSER_SESSION_NAME"] = CFG.session
    env["AGENT_BROWSER_SCREENSHOT_DIR"] = str(SHOT_DIR)
    return env


def ab(args, stdin=None, timeout=120, expect_ok=True, secret=False, quiet=False):
    """agent-browser 한 줄 실행. 반환 = (rc · data · error)."""
    cmd = ["agent-browser", "--session", CFG.session] + list(args) + ["--json"]
    shown = shlex.join(cmd)
    if secret:
        shown = shown + "   # stdin = 비밀 스크립트 · 내용 미기록"
    elif stdin is not None:
        shown = shown + "   # stdin = " + str(len(stdin)) + " B"

    if CFG.dry_run:
        print(shown)
        if LOG_FH:
            LOG_FH.write(shown + "\n")
        return 0, dict(), ""

    if not quiet:
        log("$ " + shown, echo=CFG.verbose)
    try:
        proc = subprocess.run(cmd, input=stdin, capture_output=True, text=True,
                              env=ab_env(), timeout=timeout)
    except subprocess.TimeoutExpired:
        raise Fail("agent-browser 시간 초과(" + str(timeout) + "s): " + shown)

    data = None
    err = ""
    out = (proc.stdout or "").strip()
    if out:
        try:
            parsed = json.loads(out)
            if isinstance(parsed, dict) and "success" in parsed:
                data = parsed.get("data")
                err = parsed.get("error") or ""
            else:
                data = dict(raw=parsed)
        except json.JSONDecodeError:
            data = dict(raw=out)
    if proc.returncode != 0 and not err:
        err = (proc.stderr or "").strip() or ("rc=" + str(proc.returncode))
    if expect_ok and proc.returncode != 0:
        raise Fail("명령 실패: " + shown + "\n  -> " + err)
    return proc.returncode, data, err


def count(css):
    """요소 개수. dry-run 에서는 첫 후보가 성립한 것으로 본다."""
    if CFG.dry_run:
        ab(["get", "count", css], expect_ok=False, quiet=True)
        return 1
    rc, data, _ = ab(["get", "count", css], expect_ok=False, quiet=True)
    if rc != 0 or not isinstance(data, dict):
        return 0
    return int(data.get("count", 0))


def count_absent(css):
    """dry-run 에서는 0 으로 본다(이미 열려 있으면 건너뛰는 자리 등)."""
    if CFG.dry_run:
        return 0
    return count(css)


def enabled(css):
    if CFG.dry_run:
        return True
    rc, data, _ = ab(["is", "enabled", css], expect_ok=False, quiet=True)
    if rc != 0:
        return False
    if isinstance(data, dict):
        for key in ["enabled", "result", "value"]:
            if key in data:
                return bool(data[key])
    return True


def cur_url():
    if CFG.dry_run:
        return CFG.base_url + "/lab"
    rc, data, _ = ab(["get", "url"], expect_ok=False, quiet=True)
    if rc == 0 and isinstance(data, dict):
        return data.get("url", "")
    return ""


def body_text():
    if CFG.dry_run:
        return ""
    rc, data, _ = ab(["get", "text", "body"], expect_ok=False, quiet=True)
    if rc == 0 and isinstance(data, dict):
        return data.get("text", "") or ""
    return ""


def el_text(css):
    """지정한 요소의 문자열. 없으면 빈 문자열."""
    if CFG.dry_run:
        return ""
    rc, data, _ = ab(["get", "text", css], expect_ok=False, quiet=True)
    if rc == 0 and isinstance(data, dict):
        return data.get("text", "") or ""
    return ""


def js(script, default=None, secret=False, timeout=120):
    """페이지 안에서 JS 실행. 스크립트는 표준입력으로만 넘긴다(argv 노출 없음)."""
    if CFG.dry_run:
        ab([JS_SUB, "--stdin"], stdin=script, expect_ok=False, secret=secret)
        return default
    rc, data, err = ab([JS_SUB, "--stdin"], stdin=script, expect_ok=False,
                       secret=secret, timeout=timeout)
    if rc != 0 or not isinstance(data, dict):
        log("  ! js 실패: " + str(err))
        return default
    raw = data.get("result")
    if raw is None:
        return default
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw
    return raw


def as_css(cand):
    """후보를 CSS 선택자로 바꾼다. 의미 지목(label·text·role)은 None 을 돌려준다."""
    kind = cand[0]
    val = cand[1]
    if kind == "testid":
        return '[data-testid="' + val + '"]'
    if kind == "aria":
        return '[aria-label="' + val + '"]'
    if kind == "css":
        return val
    return None


def spot(st, key, candidates, action="click", text=None, must=True):
    """지목점 해소 — testid 우선, 실패하면 라벨·문구로 폴백하고 통한 후보를 기록한다.

    후보 = ("testid", v) ("css", v) ("aria", v) ("label", v) ("text", v)
           ("placeholder", v) ("role", role, name)
    """
    cached = st.get("selectors", dict()).get(key)
    order = list(candidates)
    if cached:
        cached_t = tuple(cached)
        known = [tuple(c) for c in candidates]
        order = [c for c in candidates if tuple(c) == cached_t]
        order = order + [c for c in candidates if tuple(c) != cached_t]
        if cached_t not in known:
            order.insert(0, cached_t)

    last_err = "후보 없음"
    for cand in order:
        css = as_css(cand)
        try:
            if css is not None:
                if count(css) == 0:
                    last_err = str(cand) + " 미존재"
                    continue
                args = [action, css]
                if text is not None:
                    args.append(text)
                rc, _, err = ab(args, expect_ok=False)
            elif cand[0] == "role":
                args = ["find", "role", cand[1], action]
                if text is not None:
                    args.append(text)
                args = args + ["--name", cand[2]]
                rc, _, err = ab(args, expect_ok=False)
            else:
                args = ["find", cand[0], cand[1], action]
                if text is not None:
                    args.append(text)
                rc, _, err = ab(args, expect_ok=False)
            if rc == 0:
                st.setdefault("selectors", dict())[key] = list(cand)
                save_state(st)
                log("  · 지목점 " + key + " <- " + cand[0] + ":" + str(cand[1]))
                return cand
            last_err = str(cand) + " -> " + str(err)
        except Fail as exc:
            last_err = str(cand) + " -> " + str(exc)
    if must:
        raise Fail("지목점 " + key + " 해소 실패. 마지막 사유 = " + last_err)
    log("  ! 지목점 " + key + " 해소 실패(선택 단계라 계속): " + last_err)
    return None


def wait_any(conditions, timeout_s, poll=1.0, label="", dry=None):
    """conditions = [이름, 함수] 목록. 먼저 참이 되는 이름을 돌려준다. 초과면 None.

    dry = dry-run 에서 돌려줄 이름(성공 갈래). 생략하면 첫 조건 이름.
    """
    if CFG.dry_run:
        return dry or conditions[0][0]
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        for name, fn in conditions:
            try:
                if fn():
                    return name
            except Fail:
                pass
        time.sleep(poll)
    log("  ! 대기 시간 초과(" + str(timeout_s) + "s) " + str(label))
    return None


def wait_css(css, timeout_s, label=""):
    cond = [["ok", lambda: count(css) > 0]]
    return wait_any(cond, timeout_s, label=label or css) == "ok"


def wait_gone(css, timeout_s, label=""):
    cond = [["ok", lambda: count(css) == 0]]
    return wait_any(cond, timeout_s, label=label or css) == "ok"


def open_url(path=""):
    url = CFG.base_url.rstrip("/") + path
    ab(["open", url], timeout=180)
    ab(["wait", "--load", "networkidle"], expect_ok=False, timeout=180)
    return url


SET_VALUE_JS = """
(() => {
  const el = document.querySelector(__SEL__);
  if (!el) return JSON.stringify("no-element");
  const pass = __VAL__;
  const d = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value");
  d.set.call(el, pass);
  el.dispatchEvent(new Event("input", INIT));
  el.dispatchEvent(new Event("change", INIT));
  el.dispatchEvent(new Event("blur", INIT));
  return JSON.stringify(el.value.length === pass.length ? "ok" : "mismatch");
})()
"""


def build_set_value_js(css, value):
    init = "{ bubbles: true }"
    body = SET_VALUE_JS.replace("INIT", init)
    body = body.replace("__SEL__", json.dumps(css))
    body = body.replace("__VAL__", json.dumps(value))
    return body


def fill_secret(css, value, what):
    """비밀번호 입력 — 표준입력 경로가 기본. argv 경로는 --allow-argv-secret 일 때만."""
    if count(css) == 0:
        raise Fail(what + " 입력 칸 미존재: " + css)
    script = build_set_value_js(css, value)
    res = js(script, default=("ok" if CFG.dry_run else None), secret=True)
    if res == "ok":
        log("  · " + what + " 입력 완료(표준입력 경로 · 값 미기록)")
        return
    log("  ! " + what + " 표준입력 경로 실패: " + str(res))
    if not CFG.allow_argv_secret:
        raise Fail(what + " 입력 실패. argv 경로는 --allow-argv-secret 를 명시해야 쓴다(프로세스 목록 노출).")
    cmd = ["agent-browser", "--session", CFG.session, "fill", css, value, "--json"]
    log("  ! argv 경로로 " + what + " 입력(노출 감수)")
    if CFG.dry_run:
        print(shlex.join(cmd[:4] + ["***", "--json"]))
        return
    proc = subprocess.run(cmd, capture_output=True, text=True, env=ab_env(), timeout=60)
    if proc.returncode != 0:
        raise Fail(what + " 입력 실패(argv 경로)")


def read_password_file(path, what, generate=False):
    """0600 자격 파일에서 값을 읽는다. 값은 로그에 적지 않는다."""
    if not path.exists():
        if CFG.dry_run:
            return "DRY-RUN-PLACEHOLDER"
        if not generate:
            raise Fail(what + " 파일 없음: " + path.name + " (0600 으로 만들어 둔다)")
        alphabet = string.ascii_letters + string.digits + "-_.!@#"
        value = "".join(secrets.choice(alphabet) for _ in range(20))
        path.write_text(value + "\n", encoding="utf-8")
        os.chmod(path, 0o600)
        log("  · " + what + " 신규 생성 -> " + path.name + " (0600 · 값 미기록)")
        return value
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & 0o077:
        os.chmod(path, 0o600)
        log("  · " + path.name + " 권한 " + oct(mode) + " -> 0600 으로 조였다")
    value = path.read_text(encoding="utf-8").strip()
    if not value:
        raise Fail(what + " 파일이 비었다: " + path.name)
    return value


def dump_failure(tag, reason):
    """실패 자리 갈무리 — 화면 그림과 접근성 트리를 fail/ 에 남긴다."""
    FAIL_DIR.mkdir(parents=True, exist_ok=True)
    png = FAIL_DIR / (tag + ".png")
    txt = FAIL_DIR / (tag + ".txt")
    if CFG.dry_run:
        log("  ! (dry-run) 덤프 자리 = " + png.name + " · " + txt.name)
        return
    try:
        ab(["screenshot", "--full", str(png)], expect_ok=False, timeout=120)
    except Fail:
        pass
    parts = ["# 실패 덤프 " + tag, "- 시각 = " + now(), "- 사유 = " + str(reason)]
    try:
        parts.append("- URL = " + cur_url())
        rc, data, _ = ab(["snapshot", "-i"], expect_ok=False, timeout=120)
        snap = ""
        if isinstance(data, dict):
            snap = data.get("snapshot") or data.get("raw") or json.dumps(data, ensure_ascii=False)
        parts.append("\n## snapshot -i\n" + str(snap))
        parts.append("\n## body text\n" + body_text())
    except Fail:
        pass
    txt.write_text("\n".join(parts), encoding="utf-8")
    log("  ! 덤프 = " + png.name + " · " + txt.name)


LOGIN_ACCOUNT_CANDS = [
    ("testid", "login-account-name"),
    ("css", "#accountName"),
    ("label", "이메일"),
]
LOGIN_SUBMIT_CANDS = [
    ("testid", "login-submit"),
    ("role", "button", "들어가기"),
]


def phase_login(st, plan):
    """2 절 — 로그인 · 첫 비밀번호 변경 · /lab 진입 확인."""
    account = CFG.account or st.get("account")
    if not account:
        raise Fail("계정(이메일)을 모른다 — --account 로 주거나 state.json 의 account 를 채운다.")
    st["account"] = account
    st["base_url"] = CFG.base_url
    st["session"] = CFG.session
    save_state(st)

    open_url("/")
    if count('[data-testid="login-submit"]') == 0 and "/lab" in cur_url():
        log("· 이미 로그인 상태 — login 단계 건너뜀")
        mark_step(st, "login", "done", note="기존 세션 재사용")
        return

    rotated = bool(st.get("password_rotated"))
    pw_path = NEW_PW_PATH if rotated else INITIAL_PW_PATH
    pw_what = "새 비밀번호" if rotated else "초기 비밀번호"
    password = read_password_file(pw_path, pw_what)

    spot(st, "login-account", LOGIN_ACCOUNT_CANDS, action="fill", text=account)
    fill_secret('[data-testid="login-password"]', password, "비밀번호")
    cond = [["ok", lambda: enabled('[data-testid="login-submit"]')]]
    if not wait_any(cond, 30, label="들어가기 활성"):
        raise Fail("「들어가기」가 활성화되지 않았다 — 두 칸 입력 상태를 확인한다.")
    spot(st, "login-submit", LOGIN_SUBMIT_CANDS)

    after = wait_any([
        ["change", lambda: count('[data-testid="new-password"]') > 0],
        ["landed", lambda: "/lab" in cur_url()],
        ["error", lambda: count('[data-testid="login-error"]') > 0],
    ], 90, label="로그인 결과", dry="change")
    if after == "error":
        dump_failure("login-error", "로그인 거절")
        raise Fail("로그인 거절 — 화면 문구 「계정 또는 비밀번호가 맞지 않아요.」. 자격 행부터 확인한다.")
    if after is None:
        dump_failure("login-timeout", "로그인 결과 미확인")
        raise Fail("로그인 결과를 확인하지 못했다.")

    if after == "change":
        log("· 첫 비밀번호 변경 화면(시나리오 2 절)")
        new_pw = read_password_file(NEW_PW_PATH, "새 비밀번호", generate=True)
        if len(new_pw) < 10:
            raise Fail("새 비밀번호가 10자 미만 — 제품 하한은 10자다.")
        if new_pw == password:
            raise Fail("새 비밀번호가 초기 비밀번호와 같다 — 화면 규칙이 막는다.")
        fill_secret('[data-testid="new-password"]', new_pw, "새 비밀번호")
        fill_secret('[data-testid="confirm-password"]', new_pw, "새 비밀번호 확인")
        spot(st, "change-password", [("testid", "change-password"), ("role", "button", "비밀번호 변경")])
        st["password_rotated"] = True
        save_state(st)
        nxt = wait_any([
            ["relogin", lambda: count('[data-testid="password-relogin"]') > 0],
            ["landed", lambda: "/lab" in cur_url()],
        ], 90, label="비밀번호 변경 결과", dry="relogin")
        if nxt == "relogin":
            log("· 다시 로그인 요구 — 새 비밀번호로 재로그인")
            spot(st, "password-relogin", [("testid", "password-relogin")])
            wait_css('[data-testid="login-submit"]', 60, "로그인 화면 복귀")
            spot(st, "login-account", LOGIN_ACCOUNT_CANDS, action="fill", text=account)
            fill_secret('[data-testid="login-password"]', new_pw, "새 비밀번호")
            wait_any([["ok", lambda: enabled('[data-testid="login-submit"]')]], 30)
            spot(st, "login-submit", LOGIN_SUBMIT_CANDS)
        elif nxt is None:
            dump_failure("password-change", "비밀번호 변경 결과 미확인")
            raise Fail("비밀번호 변경 결과를 확인하지 못했다.")

    if not wait_any([["ok", lambda: "/lab" in cur_url()]], 90, label="/lab 진입"):
        dump_failure("login-landing", "/lab 진입 미확인")
        raise Fail("진입 화면이 /lab 이 아니다 — 현재 " + cur_url())
    SHOT_DIR.mkdir(parents=True, exist_ok=True)
    ab(["screenshot", str(SHOT_DIR / "login-landed.png")], expect_ok=False)
    log("· /lab 진입 확인")
    mark_step(st, "login", "done", account=account)


LINKS_JS = """
(() => {
  const out = [];
  document.querySelectorAll('a[href*="__PREFIX__"]').forEach((a) => {
    const href = a.getAttribute("href") || "";
    const m = href.match(__RE__);
    if (!m) return;
    const row = new Object();
    row.id = m[1];
    row.text = (a.innerText || "").trim();
    out.push(row);
  });
  return JSON.stringify(out);
})()
"""


def link_index(prefix, regex_literal):
    """목록 화면의 링크에서 이름 -> id 대응을 만든다(목록 testid 가 없는 자리의 대체 수단)."""
    script = LINKS_JS.replace("__PREFIX__", prefix).replace("__RE__", regex_literal)
    rows = js(script, default=[]) or []
    index = dict()
    for row in rows:
        if isinstance(row, dict) and row.get("text") and row.get("id"):
            index.setdefault(row["text"].strip(), row["id"])
    return index


def project_index():
    return link_index("/projects/", "/\\/projects\\/([^/?#]+)/")


def dataset_index():
    return link_index("/datasets/", "/\\/datasets\\/([^/?#]+)/")


PROJECT_NEW_CANDS = [
    ("css", ".pj-new"),
    ("testid", "project-new"),
    ("role", "button", "새 프로젝트"),
    ("text", "+ 새 프로젝트"),
    ("text", "새 프로젝트"),
]
PROJECT_NAME_CANDS = [
    ("label", "이름"),
    ("css", '[data-testid="project-form-modal"] input[id$="-name"]'),
]
PROJECT_DESC_CANDS = [
    ("label", "설명"),
    ("css", '[data-testid="project-form-modal"] textarea[id$="-desc"]'),
    ("css", '[data-testid="project-form-modal"] [id$="-desc"]'),
]
PROJECT_SUBMIT_CANDS = [
    ("role", "button", "만들기"),
    ("text", "만들기"),
]


def phase_projects(st, plan):
    """4 절 — 프로젝트 4건 생성. 목록에 이미 있으면 건너뛴다."""
    for proj in plan["projects"]:
        name = proj["name"]
        known = st["projects"].get(name) or dict()
        if known.get("status") == "done":
            log("· 프로젝트 " + name + " — 이미 완료(건너뜀)")
            continue
        open_url("/projects")
        index = project_index()
        page = body_text()
        if name in index or (page and name in page):
            pid = index.get(name)
            log("· 프로젝트 " + name + " — 목록에 이미 있다. id=" + str(pid))
            row = dict()
            row["id"] = pid
            row["status"] = "done"
            row["at"] = now()
            row["source"] = "기존"
            st["projects"][name] = row
            save_state(st)
            continue

        log("· 프로젝트 생성 " + name)
        spot(st, "project-new-button", PROJECT_NEW_CANDS)
        if not wait_css('[data-testid="project-form-modal"]', 30, "새 프로젝트 모달"):
            dump_failure("project-" + name + "-modal", "모달 미개방")
            raise Fail("프로젝트 모달이 열리지 않았다: " + name)

        spot(st, "project-field-name", PROJECT_NAME_CANDS, action="fill", text=name)
        spot(st, "project-field-desc", PROJECT_DESC_CANDS, action="fill", text=proj["description"])
        type_cands = [
            ("role", "button", CFG.project_type),
            ("text", CFG.project_type),
        ]
        spot(st, "project-field-type", type_cands, must=False)
        spot(st, "project-submit", PROJECT_SUBMIT_CANDS)

        if not wait_gone('[data-testid="project-form-modal"]', 60, "모달 닫힘"):
            err = ""
            if count('[data-testid="project-form-error"]') > 0:
                rc, data, _ = ab(["get", "text", '[data-testid="project-form-error"]'],
                                 expect_ok=False)
                err = (data or dict()).get("text", "")
            dump_failure("project-" + name + "-submit", "생성 실패 " + str(err))
            raise Fail("프로젝트 생성 실패(" + name + "): " + str(err))

        ab(["wait", "--load", "networkidle"], expect_ok=False, timeout=60)
        pid = project_index().get(name)
        if pid is None:
            m = PROJECT_ULID_RE.search(cur_url())
            if m:
                pid = m.group(1)
                log("  · 프로젝트 id 회수 <- 상세 URL")
        if pid is None:
            pid = ("DRY-" + name) if CFG.dry_run else None
            log("  ! 프로젝트 id 회수 실패(" + name + ") — 목록 링크에서 찾지 못했다")
        row = dict()
        row["id"] = pid
        row["status"] = "done"
        row["at"] = now()
        row["type"] = CFG.project_type
        st["projects"][name] = row
        save_state(st)
        log("  · 생성 완료 " + name + " id=" + str(pid))

    done = [n for n, v in st["projects"].items() if v.get("status") == "done"]
    status = "done" if len(done) >= len(plan["projects"]) else "partial"
    mark_step(st, "projects", status, count=len(done))


def analyze_timeout(nbytes, nfiles=0):
    """상한 = 60s + 10s/MB + 5s/파일. 상한 6시간.

    ⚠ 파일 수도 셈는다 — seq 16(72건)은 바이트만으로 재면 짧게 나왔다.
    """
    mb = float(nbytes) / (1024.0 * 1024.0)
    return int(min(6 * 3600, 60 + 10 * mb + 5 * int(nfiles or 0)))


def find_dataset_row(st, name):
    for row in st["datasets"].values():
        if row.get("name") == name:
            return row
    return None


def capture_dataset_id(name):
    """등록 직후 데이터셋 id 회수 — URL · 현재 화면 링크 · 목록 화면 순."""
    m = ULID_RE.search(cur_url())
    if m:
        return m.group(1)
    for text, did in dataset_index().items():
        if name and name in text:
            return did
    open_url("/datasets")
    for text, did in dataset_index().items():
        if name and name in text:
            return did
    return None


def open_upload_modal(st):
    if count_absent('[data-testid="upload-modal"]') > 0:
        return
    cands = [
        ("testid", "gnb-upload"),
        ("aria", "업로드"),
        ("role", "button", "업로드"),
    ]
    spot(st, "gnb-upload", cands)
    if not wait_css('[data-testid="upload-modal"]', 30, "업로드 모달"):
        raise Fail("업로드 모달이 열리지 않았다.")


def open_register(st):
    """등록 결정 게이트(reg-gate)의 「다음 →」(reg-open) 을 누른다.

    「짝 파일 없이 그려 보기」는 누르지 않는다 — 그것은 미리보기 선택이고 등록 경로가 아니다.
    """
    if count('[data-testid="reg-area"]') > 0:
        return
    if count('[data-testid="reg-open"]') == 0:
        raise Fail("등록 결정 게이트(reg-open)가 화면에 없다.")
    limit = time.time() + 600
    while time.time() < limit:
        if enabled('[data-testid="reg-open"]'):
            break
        time.sleep(2)
    else:
        raise Fail("reg-open 이 비활성 상태로 머물렀다(분석 미완 또는 격자 처리 중).")
    spot(st, "reg-open", [("testid", "reg-open")])


LEVEL_READ_JS = """
(() => {
  const el = document.querySelector(__SEL__);
  if (!el) return JSON.stringify(null);
  return JSON.stringify({
    value: el.value,
    options: Array.from(el.options).map((o) => o.value).filter((v) => v !== ""),
  });
})()
"""


def level_state():
    """화면 select 의 현재 값과 선택지. 못 읽으면 None."""
    got = js(LEVEL_READ_JS.replace("__SEL__", json.dumps(LEVEL_CSS)), default=None)
    if isinstance(got, dict) and isinstance(got.get("options"), list):
        return got
    return None


def select_level(st, ds):
    """「가공 단계」를 **계획값으로 명시 지정**한다. 반환 = 넣은 값.

    화면 기본값에도, 계보에서 나온 자동 채움에도 기대지 않는다 — 러너가 매 행 직접 넣는다.
    (등록 카드 ① 단계에만 있는 칸이다 · RegisterArea.tsx `StepClassify`.)
    """
    if not wait_css(LEVEL_CSS, 60, "가공 단계 선택 칸"):
        raise Fail("「가공 단계」 선택 칸이 없다: " + str(ds.get("name")))
    before = level_state()
    options = (before or dict()).get("options") if before else None
    action = level_action(ds, options)
    ab(list(action))
    after = level_state()
    if after is not None and after.get("value") != action[2]:
        raise Fail("가공 단계가 들어가지 않았다: " + str(ds.get("name"))
                   + " · 기대 " + action[2] + " · 화면 " + str(after.get("value")))
    st.setdefault("selectors", dict())["reg-level"] = ["testid", "reg-level"]
    log("  · 가공 단계 = " + action[2] + " (계획값 명시 지정)")
    return action[2]


def activate(css, label=""):
    """단추를 확실히 누른다 — 보이는 자리로 옮기고 초점을 준 뒤 Enter.

    ⚠ 2026-09-13 실측 — 「+ 추가」(연관 프로젝트)는 `click` 이 성공을 돌려주면서도
    React 의 onClick 이 동작하지 않았다(모달 스크롤 밖 좌표). seq 1 은 그 탓에
    프로젝트 연결 없이 등록됐고, 화면은 아무 오류도 내지 않았다.
    초점 ＋ Enter 는 같은 자리에서 동작한다.
    """
    if CFG.dry_run:
        log("agent-browser (activate) " + css)
        return
    ab(["scrollintoview", css], expect_ok=False, quiet=True)
    rc, _, _ = ab(["focus", css], expect_ok=False)
    if rc != 0:
        raise Fail("단추 초점 실패: " + (label or css))
    ab(["press", "Enter"])
    time.sleep(0.4)


def settle_grid(st):
    """전체 파일 기준 미리보기가 도착하면 격자 판정이 「위치 확인」으로 되돌아온다.

    그때 「맞습니다」(up-grid-accept)를 다시 누르지 않으면 기준 격자가 붙지 않는다.
    """
    if count('[data-testid="up-grid-mismatch"]') > 0:
        raise Fail("기준 격자 불일치(up-grid-mismatch) — 판정이 필요하다.")
    if count('[data-testid="up-grid-accept"]') > 0:
        log("  · 격자 재확인(전체 파일 기준 영역 변경)")
        ab(["click", '[data-testid="up-grid-accept"]'], expect_ok=False)
        time.sleep(0.5)


def goto_step(st, label, key, ready_css, seconds=60):
    """등록 카드의 단계를 옮긴다.

    ⚠ 단계 표시기의 탭 단추(「③ 연결」 등)는 **눌려도 단계가 안 바뀌는 자리가
    있다**(2026-09-13 실측 · seq 1 에서 60초 정체). `reg-next` 는 항상 듣는다 —
    그것을 1순위로 쓰고 탭은 폴백으로만 둔다.
    """
    if count(ready_css) > 0:
        return
    for attempt in range(4):
        settle_grid(st)
        if count('[data-testid="reg-next"]') > 0 and enabled('[data-testid="reg-next"]'):
            ab(["click", '[data-testid="reg-next"]'], expect_ok=False)
            if attempt == 0:
                log("  · 지목점 " + key + " <- testid:reg-next")
        else:
            spot(st, key, [("role", "button", label), ("text", label)], must=False)
        if wait_css(ready_css, max(10, seconds // 4), label):
            return
    dump_failure("step-" + key, "단계 이동 실패 " + label)
    raise Fail("단계 이동 실패: " + label + " (기대 " + ready_css + ")")


def ensure_step_two(st):
    """② 메타데이터 입력 단계까지 나아간다."""
    open_register(st)
    goto_step(st, "② 메타데이터 입력", "reg-step-2", '[data-testid="reg-name"]')


def do_grid(st, ds):
    """기준 격자 — 쌍 지정 또는 건너뛰기. 불일치는 자동 진행하지 않는다."""
    grid = ds.get("grid_files") or []
    if ds.get("grid_skip") or not grid:
        log("  · 기준 격자 건너뛰기")
        cands = [
            ("testid", "up-grid-skip"),
            ("text", "건너뛰기 — 나중에 올릴게요"),
        ]
        spot(st, "grid-skip", cands, must=False)
        return
    log("  · 기준 격자 " + str(len(grid)) + "건 지정")
    if not wait_css('[data-testid="up-grid-input"]', 180, "격자 칸"):
        # 격자 블록은 「좌표 없음」 판정일 때만 붙는다 — 붙지 않았다면
        # 화면이 「이 파일은 좌표를 가졌다」고 판정한 것이다. 오류가 아니라 기록한다.
        log("  ! 격자 칸 미출현 — 화면이 좌표 보유로 판정. 격자 부착 생략")
        st.setdefault("grid_absent", [])
        if ds["seq"] not in st["grid_absent"]:
            st["grid_absent"].append(ds["seq"])
        save_state(st)
        return
    limit = analyze_timeout(ds.get("grid_bytes", 0), len(grid) + ds["file_count"])
    ab(["upload", '[data-testid="up-grid-input"]'] + grid, timeout=limit)
    bound_css = '[data-testid="up-grid-block"][data-grid-state="경계 위생 실패"]'
    reject_css = ('[data-testid="up-grid-block"][data-grid-state="형상 불일치"],'
                  '[data-testid="up-grid-block"][data-grid-state="축 판별 실패"],'
                  '[data-testid="up-grid-block"][data-grid-state="짝 불일치"]')
    outcome = wait_any([
        ["mismatch", lambda: count('[data-testid="up-grid-mismatch"]') > 0],
        ["reject", lambda: count(reject_css) > 0],
        ["bounds", lambda: count(bound_css) > 0],
        ["gate", lambda: count('[data-testid="grid-attach-confirm"]') > 0],
        ["accept", lambda: count('[data-testid="up-grid-accept"]') > 0],
    ], limit, label="격자 판정", dry="accept")
    if outcome == "bounds":
        # 화면 축자 — 「격자를 적용했지만 결과 위치가 한반도 밖으로 나왔습니다.
        # 지도형을 만들지 않았습니다.」 등록 자체는 막히지 않는다 — 기록하고 이어간다.
        log("  ! 격자 경계 위생 실패 — 지도형 미생성. 등록은 이어간다(seq " + str(ds["seq"]) + ")")
        st.setdefault("grid_bounds_fail", [])
        if ds["seq"] not in st["grid_bounds_fail"]:
            st["grid_bounds_fail"].append(ds["seq"])
        save_state(st)
        return
    if outcome == "reject":
        raise Fail("기준 격자 거절(형상·축·짝 불일치) — 판정이 필요하다.")
    if outcome == "mismatch":
        raise Fail("기준 격자 불일치(up-grid-mismatch) — 판정이 필요하다. 자동 진행하지 않는다.")
    if outcome == "gate":
        spot(st, "grid-attach-confirm", [("testid", "grid-attach-confirm")])
    elif outcome == "accept":
        spot(st, "grid-accept", [("testid", "up-grid-accept")], must=False)
    else:
        raise Fail("기준 격자 판정 표시가 나타나지 않았다.")


def do_lineage(st, ds):
    """6 절 — 부모를 사람이 직접 고른다. AI 제안(lin-ask)은 누르지 않는다.

    화면 순서가 네 계단이다(LineageStep.tsx · ParentPicker.tsx 실물) —
      ① `lin-add`            「앞 데이터 직접 추가」 → `lin-picker` 개방
      ② `lin-pick-<id>`      행을 고를 뿐 — **이것만으로는 부모가 붙지 않는다**
      ③ 「이 데이터로 연결」   고르개의 확정 단추(testid 없음 · 역할+이름으로 지목)
      ④ `lin-confirm`        카드의 「확인」 — **확인된 것만 서버로 간다**
    """
    parents = ds.get("parents") or []
    if not parents:
        log("  · 부모 없음 — 계보 미설정")
        return
    for idx, pname in enumerate(parents):
        prow = find_dataset_row(st, pname)
        pid = (prow or dict()).get("dataset_id")
        if not pid:
            if CFG.dry_run:
                pid = "DRYPARENT"
            else:
                raise Fail("부모 데이터셋 id 미확보: " + pname + " — 부모 순번을 먼저 끝낸다.")
        log("  · 계보 부모 추가 " + pname + " (" + str(pid) + ")")
        activate('[data-testid="lin-add"]', "앞 데이터 직접 추가")
        if not wait_css('[data-testid="lin-picker"]', 30, "부모 고르개"):
            raise Fail("부모 고르개(lin-picker)가 열리지 않았다.")
        row_css = '[data-testid="lin-pick-' + str(pid) + '"]'
        if count(row_css) == 0:
            spot(st, "lin-lv-filter", [("testid", "lin-lv-filter")], must=False)
            if not wait_css(row_css, 20, "부모 행"):
                dump_failure(str(ds["seq"]).zfill(2) + "-lineage", "부모 행 미발견 " + str(pid))
                raise Fail("부모 행 미발견: lin-pick-" + str(pid) + " (" + pname + ")")
        if not enabled(row_css):
            raise Fail("부모 행이 비활성(자기 Lv 를 넘는 부모): " + pname)
        activate(row_css, "부모 행 " + str(pid))
        # ③ 고르개는 모달이라 행 클릭이 곧 부모 추가가 아니다(ParentPicker.tsx `onClose` 분기).
        activate(".lin-find .modal-f .btn-primary", "이 데이터로 연결")
        card_css = ".lin-cards .lin-card:nth-child(" + str(idx + 1) + ")"
        if not wait_css(card_css, 30, "계보 카드 " + str(idx + 1)):
            raise Fail("계보 카드가 붙지 않았다: " + pname)
        # ④ 확인된 관계만 서버로 간다(LineageStep.tsx `confirmed` 거르개).
        activate(card_css + ' [data-testid="lin-confirm"]', "계보 확인 " + str(idx + 1))
    made = count(".lin-cards .lin-card")
    log("  · 계보 카드 " + str(made) + "건 · 계획 " + str(len(parents)) + "건")
    if made < len(parents):
        raise Fail("계보 카드 수 미달: " + str(made) + " / " + str(len(parents)))


def handle_analysis_failure(st, ds, outcome):
    """분석 실패 자리 — **등록으로 잇는다.** 반환 = 실패 사유 문면(등록은 이어감).

    ⭑ 2026-09-14 개정 — 종전에는 「보기만 할게요」(reg-viewonly)로 모달을 닫아
    데이터셋이 **아예 생기지 않았다**(2026-09-13 실측 · `.gpkg` 2건). 화면이
    분석 실패에서도 등록을 허용하도록 바뀌었으므로(배너 축자 「등록은 됩니다」)
    등록 결정 게이트가 열릴 때까지 기다렸다가 정상 경로와 똑같이 등록한다.
    `blocked` 은 대기 뒤에도 `reg-open` 이 비활성인 자리에만 남긴다.
    갈림 자체는 `failure_path` 가 판정한다(브라우저 없이 시험된다).
    """
    seq = str(ds["seq"])
    reason = "분석 완료 표시를 받지 못했다. 결과 = " + str(outcome)
    screen = ""
    text = body_text()
    for msg in ["파일 분석을 마치지 못했어요", "형식 인식 실패", "파일을 받지 못했어요"]:
        if msg in text:
            screen = screen + ("" if not screen else " · ") + msg
    if screen:
        reason = reason + " · 화면 = 「" + screen + "」"
    dump_failure(seq.zfill(2) + "-analysis", reason)

    exists = count('[data-testid="reg-open"]') > 0
    ready = False
    if exists:
        limit = time.time() + 600
        while time.time() < limit:
            if enabled('[data-testid="reg-open"]'):
                ready = True
                break
            time.sleep(2)
    decision, detail = failure_path(exists, ready, reason)

    row = st["datasets"].get(seq) or dict()
    row["seq"] = ds["seq"]
    row["name"] = ds["name"]
    if decision == "register":
        row["analysis_failed"] = True
        row["analysis_failure_reason"] = screen or reason
        st["datasets"][seq] = row
        save_state(st)
        log("  · 분석 실패 — 미리보기 없이 등록으로 잇는다: " + (screen or reason))
        return screen or reason
    row["status"] = "blocked"
    row["blocked_reason"] = detail
    row["blocked_at"] = now()
    st["datasets"][seq] = row
    save_state(st)
    raise Blocked(detail)


def do_dataset(st, ds):
    """5 절 — 한 순번을 끝까지 투입한다. 실패는 예외로 올린다."""
    seq = str(ds["seq"])
    name = ds["name"]
    total_bytes = int(ds.get("bytes", 0)) + int(ds.get("grid_bytes", 0))
    log("■ seq " + seq + " · " + name + " · 파일 " + str(ds["file_count"]) + "건 · "
        + format(total_bytes, ",") + " B")
    started = time.time()
    prev = st["datasets"].get(seq) or dict()
    row = dict()
    row["seq"] = ds["seq"]
    row["name"] = name
    row["project"] = ds["project"]
    row["status"] = "running"
    row["started"] = now()
    row["bytes"] = total_bytes
    row["file_count"] = ds["file_count"]
    row["dataset_id"] = prev.get("dataset_id")
    st["datasets"][seq] = row
    save_state(st)

    open_url("/lab")
    open_upload_modal(st)

    log("  · 본문 파일 " + str(len(ds["files"])) + "건 지정")
    limit = analyze_timeout(ds["bytes"], ds["file_count"])
    ab(["upload", '[data-testid="up-drop-input"]'] + ds["files"], timeout=limit)
    outcome = wait_any([
        ["fail", lambda: count('[data-testid="up-analysis-failure"]') > 0
            or count('[data-testid="up-intake-error"]') > 0
            or count('[data-testid="up-status-error"]') > 0],
        ["done", lambda: count(ANALYZE_DONE_CSS) > 0],
    ], limit, label="분석 완료", dry="done")
    no_preview = None
    if outcome != "done":
        no_preview = handle_analysis_failure(st, ds, outcome)
    else:
        log("  · 분석 완료 표시 확인")

    # 등록 결정 게이트를 먼저 열어 미리보기 렌더를 부른다 —
    # 격자 블록은 렌더 결과(「좀표 없음」)에서만 붙는다(PreviewPanel.tsx · gridFlow.ts).
    open_register(st)
    # 「가공 단계」는 계획값을 **매 행 명시 지정**한다(등록 카드 ① 단계).
    st["datasets"][seq]["processing_level"] = select_level(st, ds)
    save_state(st)
    do_grid(st, ds)
    ensure_step_two(st)

    spot(st, "reg-name", [("testid", "reg-name"), ("label", "데이터셋 이름")],
         action="fill", text=name)
    spot(st, "reg-summary", [("testid", "reg-summary"), ("label", "설명")],
         action="fill", text=ds["summary"])

    goto_step(st, "③ 연결", "reg-step-3", '[data-testid="reg-proj-select"]')
    # option 의 value 는 projectId 다(RegisterArea.tsx `value={r.projectId}`) — 이름이 아니라 id 로 고른다.
    prow = (st.get("projects") or dict()).get(ds["project"]) or dict()
    proj_value = prow.get("id") or ds["project"]
    ab(["select", '[data-testid="reg-proj-select"]', str(proj_value)])
    activate('[data-testid="reg-proj-select"] ~ button', "연관 프로젝트 + 추가")
    st.setdefault("selectors", dict())["reg-proj-add"] = ["activate", "reg-proj-select ~ button"]
    if not CFG.dry_run and not wait_css('[data-testid="reg-proj-table"]', 20, "연관 프로젝트 표"):
        dump_failure(str(ds["seq"]).zfill(2) + "-proj", "연관 프로젝트 표 미출현")
        raise Fail("연관 프로젝트가 담기지 않았다: " + ds["project"])
    log("  · 연관 프로젝트 담김 " + ds["project"])

    do_lineage(st, ds)

    settle_grid(st)
    if not CFG.dry_run and not enabled('[data-testid="reg-done"]'):
        raise Fail("「데이터셋 만들기」가 비활성 — 자기 Lv 를 넘는 연결이 남았는지 확인한다.")
    log("  · 등록 확정(reg-done) — 자동 재시도 없음")
    spot(st, "reg-done", [("testid", "reg-done"), ("text", "데이터셋 만들기")])

    limit = analyze_timeout(total_bytes, ds["file_count"])
    closed = wait_any([
        ["error", lambda: count('[data-testid="up-status-error"]') > 0
            or count('[data-testid="up-intake-error"]') > 0],
        ["closed", lambda: count('[data-testid="upload-modal"]') == 0],
    ], limit, label="등록 완료", dry="closed")
    if closed != "closed":
        raise Fail("등록 완료를 확인하지 못했다. 결과 = " + str(closed)
                   + " · 상한 " + str(limit) + "s")

    did = ("DRYID" + seq) if CFG.dry_run else capture_dataset_id(name)
    if not did:
        raise Fail("데이터셋 id 를 회수하지 못했다(URL · 목록 링크 모두 실패).")
    elapsed = round(time.time() - started, 1)
    SHOT_DIR.mkdir(parents=True, exist_ok=True)
    ab(["screenshot", str(SHOT_DIR / (seq.zfill(2) + ".png"))], expect_ok=False)
    st["datasets"][seq]["status"] = "registered_no_preview" if no_preview else "done"
    if no_preview:
        st["datasets"][seq]["analysis_failure_reason"] = no_preview
    st["datasets"][seq]["dataset_id"] = did
    st["datasets"][seq]["finished"] = now()
    st["datasets"][seq]["elapsed_s"] = elapsed
    save_state(st)
    log("  + seq " + seq + " 완료(" + st["datasets"][seq]["status"] + ") · id="
        + str(did) + " · " + str(elapsed) + "s")


def phase_datasets(st, plan):
    rows = sorted(plan["datasets"], key=lambda d: d["seq"])
    if CFG.only_seq:
        rows = [d for d in rows if d["seq"] in CFG.only_seq]
    elif CFG.from_seq:
        rows = [d for d in rows if d["seq"] >= CFG.from_seq]
    for ds in rows:
        seq = str(ds["seq"])
        cur = st["datasets"].get(seq) or dict()
        if is_registered(cur.get("status")) and not CFG.force:
            log("· seq " + seq + " 이미 등록됨(" + str(cur.get("status")) + ") — 건너뜀")
            continue
        if cur.get("status") == "blocked" and not CFG.force:
            log("· seq " + seq + " 등록 불가로 기록됨 — 건너뜀 ("
                + str(cur.get("blocked_reason") or "") + ")")
            continue
        try:
            do_dataset(st, ds)
        except Blocked as exc:
            log("! seq " + seq + " 등록 불가 — 건너뛰고 잇는다: " + str(exc))
            continue
        except Fail as exc:
            hold = st["datasets"].get(seq) or dict()
            hold["status"] = "failed"
            hold["error"] = str(exc)
            hold["failed_at"] = now()
            st["datasets"][seq] = hold
            save_state(st)
            mark_step(st, "datasets", "failed", failed_seq=ds["seq"])
            dump_failure(seq.zfill(2) + "-failed", str(exc))
            log("x seq " + seq + " 실패: " + str(exc))
            log("  재개 = python3 runner.py --phase datasets --from-seq " + seq)
            sys.exit(2)
    done = 0
    for v in st["datasets"].values():
        if is_registered(v.get("status")):
            done = done + 1
    status = "done" if done >= len(plan["datasets"]) else "partial"
    mark_step(st, "datasets", status, done=done)


SELECT_BY_LABEL_JS = """
(() => {
  const el = document.querySelector(__SEL__);
  if (!el) return JSON.stringify(null);
  const want = __VAL__;
  const hit = Array.from(el.options).find((o) => (o.textContent || "").trim() === want);
  return JSON.stringify(hit ? hit.value : null);
})()
"""

CHECKED_JS = """
(() => {
  const el = document.querySelector(__SEL__);
  if (!el) return JSON.stringify(null);
  return JSON.stringify(!!el.checked);
})()
"""


def select_by_label(css, label, what):
    """보이는 이름으로 option 을 고른다 — option 의 value 는 id 라 이름으로 짚는다."""
    script = SELECT_BY_LABEL_JS.replace("__SEL__", json.dumps(css))
    script = script.replace("__VAL__", json.dumps(label))
    value = js(script, default="DRY")
    if not value:
        raise Fail(what + " 선택지에 없는 이름: " + label)
    ab(["select", css, str(value)])


def set_checkbox(css, want, what):
    """체크 상태를 원하는 값으로 맞춘다. 이미 그 값이면 누르지 않는다."""
    script = CHECKED_JS.replace("__SEL__", json.dumps(css))
    cur = js(script, default=(not want))
    if cur is None:
        raise Fail(what + " 칸이 화면에 없다: " + css)
    if bool(cur) == bool(want):
        return
    ab(["click", css], expect_ok=False)
    after = js(script, default=want)
    if bool(after) != bool(want):
        raise Fail(what + " 체크 상태를 바꾸지 못했다: " + css)


def account_initial_password():
    """초기 비밀번호 — 0600 파일 또는 표준입력. **argv 로는 받지 않는다.**"""
    if CFG.accounts_password_file:
        return read_secret_file(Path(CFG.accounts_password_file).expanduser(),
                                "계정 초기 비밀번호")
    if CFG.dry_run:
        return "DRY-RUN-PLACEHOLDER"
    if sys.stdin.isatty():
        value = getpass.getpass("계정 초기 비밀번호(입력은 보이지 않는다): ").strip()
    else:
        value = sys.stdin.readline().strip()
    if not value:
        raise Fail("계정 초기 비밀번호를 받지 못했다"
                   "(--accounts-password-file 0600 파일 또는 표준입력).")
    return value


def create_account(st, entry, secret):
    """계정 한 건을 **계정 관리 화면으로** 만든다. API·DB 직접 쓰기 없음."""
    for action in account_form_actions(entry):
        kind = action[0]
        css = action[1]
        if kind == "secret":
            fill_secret(css, secret, "초기 비밀번호")
        elif kind == "activate":
            activate(css, "계정 추가")
        elif kind == "check":
            set_checkbox(css, True, "관리자로 등록")
        elif kind == "select-label":
            select_by_label(css, action[2], "연구실")
        else:
            ab(list(action))
    if CFG.dry_run:
        return "created", "(dry-run)"
    if not wait_css(ACCOUNT_CSS["status"], 60, "계정 추가 결과 문면"):
        raise Fail("계정 추가 결과 문면이 뜨지 않았다: " + entry["email"])
    message = el_text(ACCOUNT_CSS["status"])
    if "계정을 추가했어요" in message:
        return "created", message
    return "failed", message


def phase_accounts(st, plan):
    """선택 단계 — dev 초기화로 지워진 운영자·사용자 계정을 화면으로 되만든다.

    ⛔ 「첫 로그인 비밀번호 변경 강제」는 화면에 칸이 없다 — 서버가 늘 강제한다.
       화면이 정하는 대로 두고 러너가 건드리지 않는다(AccountAdminPage.tsx 도움말 축자).
    """
    if not CFG.accounts_file:
        log("· 계정 단계 건너뜀 — --accounts-file 미지정")
        mark_step(st, "accounts", "skipped")
        return
    entries = load_accounts_file(Path(CFG.accounts_file).expanduser())
    secret = account_initial_password()
    log("· 계정 " + str(len(entries)) + "건 · 초기 비밀번호 " + SECRET_MARK + "(값 미기록)")

    open_url(ACCOUNT_PATH)
    if not wait_css(ACCOUNT_SECTION_CSS, 60, "계정 추가 화면"):
        raise Fail("계정 관리 화면(account-create)이 열리지 않았다 — "
                   "관리자 권한 계정으로 로그인했는지 확인한다.")
    rows = st.setdefault("accounts", dict())
    made = 0
    for entry in entries:
        prev = rows.get(entry["email"]) or dict()
        if prev.get("status") == "created" and not CFG.force:
            log("· " + entry["email"] + " 이미 생성됨 — 건너뜀")
            made = made + 1
            continue
        log("  · " + account_log_line(entry))
        try:
            status, message = create_account(st, entry, secret)
        except Fail as exc:
            status = "failed"
            message = str(exc)
        rows[entry["email"]] = account_state_row(entry, status, message)
        save_state(st)
        if status == "created":
            made = made + 1
            log("  + " + entry["email"] + " 추가됨")
        else:
            log("  x " + entry["email"] + " 추가 실패: " + str(message))
        open_url(ACCOUNT_PATH)
        wait_css(ACCOUNT_SECTION_CSS, 60, "계정 추가 화면")
    mark_step(st, "accounts", "done" if made >= len(entries) else "partial",
              made=made, planned=len(entries))


CATALOG_COUNT_RE = re.compile(r"(\d[\d,]*)\s*건")


def catalog_total():
    """목록 화면의 데이터셋 총 건수. 반환 = (총계 · 방법 · 한 쪽의 행 수).

    ⚠ 2026-09-13 실측 — 26건을 넣고 표 행을 세니 20 이 나왔다. 목록 계약의 `limit` 기본값이
    20 이고(`catalog.py` `limit: int = Query(default=20 …)`) 화면은 `limit` 을 보내지 않는다
    (`catalogSource.ts` `api.GET('/datasets' …)`). 곧 **표 행 수는 한 쪽 분량이라 계수가 아니다.**
    화면 머리의 「N건」(`.hcnt`)은 서버가 준 `totalCount` 라 쪽에서 잘리지 않는다
    (`DatasetsPage.tsx`). 그 값을 총계로 쓰고, 못 읽으면 본문 전체에서 같은 꼴을 찾고,
    그것도 없으면 표 행 수로 내려가되 방법 문자열에 「쪽 잘림 가능」을 남긴다.
    """
    rows = count("table.catalog tbody tr.clk")
    if CFG.dry_run:
        return rows, ".catalog-page .hcnt (dry-run)", rows
    head = el_text(".catalog-page .hcnt")
    m = CATALOG_COUNT_RE.search(head or "")
    if m:
        return (int(m.group(1).replace(",", "")),
                ".catalog-page .hcnt 「" + head.strip() + "」", rows)
    m = CATALOG_COUNT_RE.search(body_text() or "")
    if m:
        return int(m.group(1).replace(",", "")), "본문의 「N건」(머리 선택자 실패)", rows
    log("  ! 화면 머리의 건수를 읽지 못했다 — 표 행 수로 내려간다(한 쪽 분량일 수 있다)")
    return rows, "table.catalog tbody tr.clk (쪽 잘림 가능)", rows


def phase_verify(st, plan):
    """7 절 — 데이터셋 계수 · 계보 간선 · 미리보기 렌더 5포맷."""
    result = dict()
    result["at"] = now()
    result["base_url"] = CFG.base_url

    open_url("/datasets")
    total, method, rows_on_page = catalog_total()
    result["dataset_count_ui"] = total
    result["dataset_count_method"] = method
    result["dataset_rows_on_page"] = rows_on_page
    result["dataset_count_note"] = ("표는 한 쪽(기본 20행)만 그린다 — "
                                    "화면 머리의 「N건」(.hcnt)이 전체 계수다.")
    state_done = 0
    by_project = dict()
    for v in st["datasets"].values():
        if is_registered(v.get("status")):
            state_done = state_done + 1
            key = v.get("project")
            by_project[key] = by_project.get(key, 0) + 1
    result["dataset_count_state"] = state_done
    result["dataset_count_expected"] = len(plan["datasets"])
    result["by_project"] = by_project
    log("· 데이터셋 계수 화면 " + str(result["dataset_count_ui"])
        + " / 계획 " + str(result["dataset_count_expected"]))

    edges_ok = 0
    edges_missing = []
    for edge in plan["edges"]:
        child = find_dataset_row(st, edge["child"])
        cid = (child or dict()).get("dataset_id")
        miss = dict()
        miss["child"] = edge["child"]
        miss["parent"] = edge["parent"]
        if not cid:
            miss["reason"] = "자식 데이터셋 id 미확보"
            edges_missing.append(miss)
            continue
        open_url("/datasets/" + str(cid))
        text = body_text()
        if CFG.dry_run or (edge["parent"] in text):
            edges_ok = edges_ok + 1
        else:
            miss["reason"] = "자식 상세 화면에 부모 이름 미노출"
            edges_missing.append(miss)
    result["edges_ok"] = edges_ok
    result["edges_expected"] = len(plan["edges"])
    result["edges_missing"] = edges_missing
    log("· 계보 간선 " + str(edges_ok) + " / " + str(len(plan["edges"])))

    previews = []
    for pair in PREVIEW_SEQS:
        seq = pair[0]
        fmt = pair[1]
        row = st["datasets"].get(str(seq)) or dict()
        did = row.get("dataset_id")
        entry = dict()
        entry["seq"] = seq
        entry["format"] = fmt
        entry["dataset_id"] = did
        if not did:
            entry["render"] = "미확인"
            entry["reason"] = "데이터셋 id 미확보"
            previews.append(entry)
            continue
        open_url("/datasets/" + str(did))
        ok = wait_css('[data-testid="dataset-preview"]', 120, "미리보기")
        time.sleep(6)
        bad = count('[data-testid="preview-unavailable"]')
        imgs = count('[data-testid="dataset-preview"] img')
        entry["preview_section"] = 1 if ok else 0
        entry["unavailable"] = bad
        entry["images"] = imgs
        entry["status_text"] = ""
        if bad > 0:
            rc, data, _ = ab(["get", "text", '[data-testid="preview-unavailable"]'],
                             expect_ok=False, quiet=True)
            entry["status_text"] = ((data or dict()).get("text") or "")[:400]
        entry["render"] = "그려짐" if (ok and bad == 0 and imgs > 0) else "안 그려짐"
        SHOT_DIR.mkdir(parents=True, exist_ok=True)
        shot = SHOT_DIR / ("verify-preview-" + str(seq).zfill(2) + "-" + fmt + ".png")
        ab(["screenshot", str(shot)], expect_ok=False)
        entry["screenshot"] = shot.name
        previews.append(entry)
        log("· 미리보기 " + fmt + "(seq " + str(seq) + ") = " + entry["render"])
    result["previews"] = previews

    open_url("/projects")
    # 프로젝트도 카드다 — id 는 testid 접미에 실려 있다(ProjectCards.tsx:31).
    result["project_count_ui"] = count('[data-testid^="project-card-"]')
    result["project_count_expected"] = len(plan["projects"])

    if not CFG.dry_run:
        VERIFY_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    passed = result["dataset_count_ui"] == result["dataset_count_expected"]
    passed = passed and edges_ok == len(plan["edges"])
    for p in previews:
        if p.get("render") != "그려짐":
            passed = False
    mark_step(st, "verify", "done" if passed else "partial")
    log("· verify.json 기록 · 판정 = " + ("전건 통과" if passed else "미달 있음"))


def phase_report(st, plan):
    """순번 · 이름 · 상태 · 데이터셋 id · 소요 · 바이트 표."""
    head = ["순번", "이름", "Lv", "상태", "데이터셋 id", "소요(s)", "바이트"]
    rows = []
    for ds in sorted(plan["datasets"], key=lambda d: d["seq"]):
        row = st["datasets"].get(str(ds["seq"])) or dict()
        nbytes = int(ds.get("bytes", 0)) + int(ds.get("grid_bytes", 0))
        elapsed = row.get("elapsed_s")
        rows.append([
            str(ds["seq"]),
            ds["name"][:34],
            str(row.get("processing_level") or ds.get("processing_level") or "-"),
            row.get("status") or "미착수",
            str(row.get("dataset_id") or "-"),
            (str(elapsed) if elapsed else "-"),
            format(nbytes, ","),
        ])
    widths = []
    for i, h in enumerate(head):
        w = len(h)
        for r in rows:
            w = max(w, len(r[i]))
        widths.append(w)

    def fmt(cols):
        out = []
        for i, c in enumerate(cols):
            out.append(c.ljust(widths[i]))
        return " | ".join(out)

    print(fmt(head))
    print("-+-".join("-" * w for w in widths))
    for r in rows:
        print(fmt(r))
    done = 0
    for r in rows:
        if is_registered(r[3]):
            done = done + 1
    total = 0
    for d in plan["datasets"]:
        total = total + int(d.get("bytes", 0)) + int(d.get("grid_bytes", 0))
    print("")
    print("완료 " + str(done) + " / " + str(len(rows)) + " · 계획 총량 " + format(total, ",") + " B")
    for name in ["login", "accounts", "projects", "datasets", "verify"]:
        s = st["steps"].get(name) or dict()
        print("단계 " + name + ": " + str(s.get("status") or "미착수") + " " + str(s.get("at") or ""))
    if VERIFY_PATH.exists():
        v = json.loads(VERIFY_PATH.read_text(encoding="utf-8"))
        pv = []
        for p in v.get("previews", []):
            pv.append(str(p.get("format")) + "=" + str(p.get("render")))
        print("verify: 데이터셋 " + str(v.get("dataset_count_ui")) + "/"
              + str(v.get("dataset_count_expected")) + " · 간선 " + str(v.get("edges_ok")) + "/"
              + str(v.get("edges_expected")) + " · 미리보기 " + ", ".join(pv))


def main():
    global CFG, LOG_FH
    ap = argparse.ArgumentParser(description="dev 실투입 러너(agent-browser)")
    ap.add_argument("--phase", required=True,
                    choices=["login", "accounts", "projects", "datasets",
                             "verify", "report", "all"])
    ap.add_argument("--base-url", default=os.environ.get("COLAB_DEV_URL", DEFAULT_URL),
                    help="대상 주소. 환경변수 COLAB_DEV_URL 로도 준다. 기본값 없음")
    ap.add_argument("--work-dir", default=os.environ.get("COLAB_SEED_WORK_DIR"),
                    help="상태·로그·갈무리·자격 파일 자리. 기본값 = 이 폴더의 .work/")
    ap.add_argument("--plan", default=None,
                    help="계획 파일. 기본값 = <work-dir>/upload-plan.json")
    ap.add_argument("--session", default=DEFAULT_SESSION)
    ap.add_argument("--account", default=None,
                    help="로그인 이메일. 최초 1회만 주면 state.json 에 남는다")
    ap.add_argument("--project-type", default="국가과제",
                    help="프로젝트 유형. 정본 미지정이라 4건을 하나로 통일하고 기록한다")
    ap.add_argument("--from-seq", type=int, default=None, help="이 순번부터 재개")
    ap.add_argument("--only-seq", default=None, help="쉼표로 구분한 순번만 실행")
    ap.add_argument("--dry-run", action="store_true",
                    help="실행 없이 agent-browser 명령만 출력")
    ap.add_argument("--force", action="store_true", help="완료 표시된 순번도 다시 실행")
    ap.add_argument("--accounts-file", default=None,
                    help="계정 목록 JSON(0600). 주면 accounts 단계가 동작한다")
    ap.add_argument("--accounts-password-file", default=None,
                    help="계정 초기 비밀번호 파일(0600). 없으면 표준입력으로 받는다")
    ap.add_argument("--allow-argv-secret", action="store_true",
                    help="비밀번호 argv 폴백 허용(프로세스 목록 노출)")
    ap.add_argument("--verbose", action="store_true")
    CFG = ap.parse_args()
    set_work_dir(CFG.work_dir or DEFAULT_WORK_DIR, CFG.plan)
    if not CFG.base_url:
        print("대상 주소가 없다 — --base-url 또는 COLAB_DEV_URL 을 준다"
              "(dev 주소의 원본 = docs/DEPLOY.md).", file=sys.stderr)
        return 2
    CFG.base_url = CFG.base_url.rstrip("/")
    if CFG.only_seq:
        picked = set()
        for x in CFG.only_seq.split(","):
            if x.strip():
                picked.add(int(x))
        CFG.only_seq = picked
    else:
        CFG.only_seq = None

    WORK_DIR.mkdir(parents=True, exist_ok=True)
    if not PLAN_PATH.exists():
        print("계획 파일 없음: " + str(PLAN_PATH)
              + " — 먼저 `python3 build_plan.py` 로 만든다.", file=sys.stderr)
        return 2
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))

    for d in [LOG_DIR, SHOT_DIR, FAIL_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    LOG_FH = open(LOG_DIR / ("run-" + stamp + ".log"), "a", encoding="utf-8")

    st = load_state()
    log("phase=" + CFG.phase + " dry_run=" + str(CFG.dry_run)
        + " base=" + CFG.base_url + " session=" + CFG.session)

    table = dict()
    table["login"] = phase_login
    table["accounts"] = phase_accounts
    table["projects"] = phase_projects
    table["datasets"] = phase_datasets
    table["verify"] = phase_verify
    table["report"] = phase_report
    if CFG.phase == "all":
        # `accounts` 는 `--accounts-file` 을 준 실행에서만 실질 동작한다(없으면 건너뜀).
        order = ["login", "accounts", "projects", "datasets", "verify", "report"]
    else:
        order = [CFG.phase]

    try:
        for name in order:
            log("=== 단계 " + name + " 시작 ===")
            table[name](st, plan)
            log("=== 단계 " + name + " 종료 ===")
    except Fail as exc:
        log("x 실패: " + str(exc))
        target = CFG.phase if CFG.phase != "all" else "all"
        mark_step(st, target, "failed", error=str(exc))
        dump_failure(target + "-fail", str(exc))
        return 2
    except KeyboardInterrupt:
        log("중단(사용자) — state.json 에 진행분이 남는다")
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
