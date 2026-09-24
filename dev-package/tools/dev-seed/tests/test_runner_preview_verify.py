import importlib.util
import json
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("dev_seed_runner_preview", ROOT / "runner.py")
runner = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(runner)


def test_done_slot_requires_a_decoded_main_image():
    assert runner.classify_preview_measurement("done", 1, 0, 0, "") == (
        "안 그려짐", "완료 슬롯의 주 이미지가 아직 decode되지 않음")
    assert runner.classify_preview_measurement("done", 2, 1, 0, "총 120ms") == (
        "안 그려짐", "완료 슬롯의 표시 이미지가 모두 decode되지 않음")
    assert runner.classify_preview_measurement("done", 2, 2, 0, "") == (
        "안 그려짐", "화면 표시 시간 관측이 끝나지 않음")
    assert runner.classify_preview_measurement("done", 2, 2, 0, "총 120ms") == ("그려짐", "")


# 창 1280x577 · 보기 단추가 y≈288 에 오도록 스크롤된 상태에서 HDF4 지도는 범례 아래 = 접힌 선 밖에서
# 시작한다(dev 2026-09-25 seq 25 · slot done · 「총 2.4초」인데 imageCount 0 으로 120 s 시간 초과).
# 가짜 DOM 에 측정 스크립트를 실제로 돌린다 — scrollIntoView 는 아무것도 옮기지 않는다(범례가 길어
# 스크롤 뒤에도 지도가 접힌 선 밖에 남는 경우).
FAKE_PAGE_JS = """
const script = %s;
const box = (top) => () => ({top, bottom: top + 300, left: 0, right: 600, width: 600, height: 300});
const inSlot = [{getBoundingClientRect: box(700), complete: true, naturalWidth: 512}];
const outside = [{getBoundingClientRect: box(10), complete: false, naturalWidth: 0}];
let scrolled = 0;
const slot = {
  getAttribute: (n) => (n === 'data-preview-slot-state' ? 'done' : null),
  querySelectorAll: () => inSlot,
  scrollIntoView: () => { scrolled += 1; },
};
globalThis.window = {innerHeight: 577, innerWidth: 1280};
globalThis.document = {
  querySelector: (sel) => (sel.includes('dt-preview-slot') ? slot
    : sel.includes('dt-preview-total') ? {textContent: '총 2.4초'} : null),
  querySelectorAll: (sel) => (sel.includes('preview-unavailable') ? [] : inSlot.concat(outside)),
};
const got = new Function('return ' + script)();
process.stdout.write(JSON.stringify(Object.assign({}, got, {scrolled})));
"""


def run_measurement_on_fake_page(monkeypatch, tmp_path):
    node = shutil.which("node")
    assert node, "node 가 없어 측정 스크립트를 실행할 수 없다(준비 실패 · 건너뛰지 않는다)"
    captured = []
    monkeypatch.setattr(runner, "js", lambda script, default=None, **_k: captured.append(script) or {})
    runner._preview_measurement()
    assert len(captured) == 1
    page = tmp_path / "fake-page.js"
    page.write_text(FAKE_PAGE_JS % json.dumps(captured[0]), encoding="utf-8")
    out = subprocess.run([node, str(page)], capture_output=True, text=True, timeout=30, check=True)
    return json.loads(out.stdout)


def test_done_slot_image_below_the_fold_is_counted_after_scrolling_the_slot(monkeypatch, tmp_path):
    """완료 슬롯 안의 주 이미지는 접힌 선 아래여도 센다 — 슬롯을 스크롤하고 슬롯 밖 이미지는 세지 않는다."""
    got = run_measurement_on_fake_page(monkeypatch, tmp_path)

    assert got["slotState"] == "done"
    assert got["scrolled"] >= 1
    assert got["imageCount"] == 1
    assert got["decodedCount"] == 1
    assert got["totalText"] == "총 2.4초"
    assert runner.classify_preview_measurement(
        got["slotState"], got["imageCount"], got["decodedCount"], got["unavailable"],
        got["totalText"]) == ("그려짐", "")


def test_failed_and_empty_states_are_not_reported_as_rendered():
    assert runner.classify_preview_measurement("failed", 0, 0, 1, "") == (
        "안 그려짐", "미리보기 실패")
    assert runner.classify_preview_measurement("idle", 0, 0, 0, "") == (
        "미확인", "terminal 상태에 도달하지 않음")


# ══════════════ 보기 클릭 전 정착 대기 · 시간 초과 증거 · 행별 판정 ══════════════
# 화면 사실(배포 트리 ea21d8c2aa54 · frontend/src/components/datasetpreview/DatasetPreviewSection.tsx):
# - 파일 고르개 onPick 은 description 을 비우고 pick 을 새로 둔다(:347-351).
# - describe effect 의 의존은 [source, selectedFileId, loadAttempt] 뿐이다(:169-183) —
#   이미 선택된 파일을 다시 고르면 selectedFileId 가 그대로라 describe 를 다시 부르지 않는다.
# - 보기 버튼은 drawing · !selectedFileId · !description · 팔레트 0 이면 disabled 다(:354-355).
# - agent-browser 0.27.0 의 click 은 disabled 버튼에도 성공을 돌려주고 아무 일도 일어나지 않는다.
# dev 7회차 seq 15 는 이 셋이 겹쳐 POST /api/v1/previews 0건으로 120s 를 보냈다.

DRAW = '[data-testid="dt-preview-draw"]'
PICK = '[data-testid="dt-pick-file"]'


class Clock:
    def __init__(self):
        self.t = 0.0

    def time(self):
        return self.t

    def sleep(self, s):
        self.t += s


class FakePreviewPage:
    """DatasetPreviewSection 의 선택·describe·보기 전이를 흉내 낸다."""

    def __init__(self, clock, files, describe_s=2.0, covered=False, keyboard_ok=True, js_click_ok=True):
        self.clock = clock
        self.file_id = files[0]
        self.describe_s = describe_s
        self.description_at = clock.t + describe_s  # 첫 describe 가 날아가는 중
        self.drawing = False
        self.posts = []
        self.commands = []
        self.click_at = None
        # 버튼 중심이 떠 있는 층(「올리다 만 것이 있어요」)에 덮였는가 — 좌표 클릭은 그 층이 받는다.
        self.covered = covered
        self.keyboard_ok = keyboard_ok
        self.js_click_ok = js_click_ok
        self.focused = False
        self.js_clicks = 0

    def has_description(self):
        return self.description_at is not None and self.clock.t >= self.description_at

    def controls(self):
        desc = self.has_description()
        return {
            "fileId": self.file_id,
            "drawEnabled": desc and not self.drawing,
            "variableCount": 1 if desc else 0,
            "variableValue": "grib:1:2t" if desc else "",
            "instantCount": 1 if desc else 0,
            "slotState": "drawing" if self.drawing else "idle",
            "now": self.clock.t * 1000,
        }

    def activate(self):
        self.click_at = self.clock.t
        if self.controls()["drawEnabled"]:
            self.drawing = True
            self.posts.append(self.file_id)

    def hit(self):
        center = {"x": 50, "y": 300, "inViewport": True}
        cover = ({"tag": "div", "testid": "resume-drafts", "ancestorTestid": "resume-drafts",
                  "cls": "resume-float", "text": "올리다 만 것이 있어요 이어서 하기"}
                 if self.covered else None)
        return {"found": True, "before": dict(center, onButton=not self.covered, cover=cover),
                "after": dict(center, onButton=not self.covered, cover=cover)}

    def js(self, script, default=None, **_kwargs):
        if "elementFromPoint" in script:
            return self.hit()
        if ".click()" in script:
            self.commands.append(["js-click", DRAW])
            self.js_clicks += 1
            if self.js_click_ok:
                self.activate()
            return {"clicked": True}
        return self.controls()

    def ab(self, args, **_kwargs):
        self.commands.append(list(args))
        if args[0] == "select" and args[1] == PICK:
            if args[2] != self.file_id:
                self.file_id = args[2]
                self.description_at = self.clock.t + self.describe_s
            else:
                self.description_at = None  # 비워지고 다시 부르지 않는다
        elif args[0] == "click" and args[1] == DRAW:
            if not self.covered:  # 덮였으면 좌표 클릭은 덮은 층이 받는다(rc 는 0)
                self.activate()
        elif args[0] == "focus":
            self.focused = args[1] == DRAW
        elif args[:2] == ["press", "Enter"]:
            if self.focused and self.keyboard_ok:
                self.activate()
        return 0, {}, ""


def install_page(monkeypatch, page, clock):
    monkeypatch.setattr(runner, "CFG", SimpleNamespace(dry_run=False, verbose=False))
    monkeypatch.setattr(runner, "time", clock)
    monkeypatch.setattr(runner, "log", lambda *a, **k: None)
    monkeypatch.setattr(runner, "js", page.js)
    monkeypatch.setattr(runner, "ab", page.ab)


def test_draw_click_after_describe_reaches_create_without_wiping_description(monkeypatch):
    """(a) dev 7회차 재현 — describe 가 끝난 뒤 같은 파일을 다시 골라 설명을 비우고 곧바로 누르면
    disabled 버튼을 누른 것이라 POST 가 나가지 않는다. 고친 러너는 설명이 선 상태에서 누른다."""
    clock = Clock()
    page = FakePreviewPage(clock, ["01M39V0YFJ3W1EHQWM8FCDJXDX"])
    install_page(monkeypatch, page, clock)
    clock.t = 5.0  # describe 가 이미 도착한 뒤(러너가 상세를 연 뒤 1.7s)

    assert runner.request_selected_preview() == "01M39V0YFJ3W1EHQWM8FCDJXDX"
    assert page.posts == ["01M39V0YFJ3W1EHQWM8FCDJXDX"]
    assert page.has_description()


def test_draw_waits_for_the_selected_files_description_before_click(monkeypatch):
    """(a) 다른 파일을 고르면 그 파일의 describe 가 도착하고 보기가 켜진 뒤에만 누른다."""
    clock = Clock()
    page = FakePreviewPage(clock, ["FILE-1", "FILE-2"], describe_s=2.0)
    install_page(monkeypatch, page, clock)
    clock.t = 5.0

    assert runner.request_selected_preview("FILE-2") == "FILE-2"
    select_at = 5.0
    assert ["select", PICK, "FILE-2"] in page.commands
    assert page.click_at is not None and page.click_at >= select_at + 2.0
    assert page.posts == ["FILE-2"]


def test_draw_is_not_clicked_when_the_page_never_settles(monkeypatch):
    """정착이 끝내 오지 않으면 누르지 않고 실패한다 — 누르지 않은 행을 `client_no_request` 로 읽지 않게."""
    clock = Clock()
    page = FakePreviewPage(clock, ["FILE-1"])
    page.description_at = None
    install_page(monkeypatch, page, clock)

    with pytest.raises(runner.Fail, match="준비"):
        runner.request_selected_preview()
    assert not any(c[0] in ("click", "focus", "press", "js-click") for c in page.commands)


# ══════════════ 보기 누름 — 적중 검사 · 초점 ＋ Enter · JS click 폴백 ══════════════
# dev 2026-09-25 00:45–01:00 KST — 정착 확인(파일 일치 · 보기 활성 · slot idle · 1 s) 뒤
# `agent-browser click` 이 5행 모두 rc 0 이었는데 요청 0건 · slot idle 그대로였다(onClick 미실행).
# 로컬 대역 페이지 실측(agent-browser 0.27.0): 좌표 클릭은 ⑴ 버튼이 화면 밖이면 스크롤 없이 화면 밖
# 좌표를 누르고 ⑵ 버튼 중심이 고정 층에 덮이면 그 층을 누른다 — 둘 다 rc 0 · 처리기 0회.

def test_covered_draw_is_pressed_by_focus_enter_and_hit_test_names_the_cover(monkeypatch):
    clock = Clock()
    page = FakePreviewPage(clock, ["FILE-1"], covered=True)
    install_page(monkeypatch, page, clock)
    clock.t = 5.0
    diag = {}

    assert runner.request_selected_preview(diag=diag) == "FILE-1"
    assert page.posts == ["FILE-1"]
    assert diag["activation"] == "focus+Enter"
    assert "resume-drafts" in diag["hit_summary"] and "올리다 만 것" in diag["hit_summary"]
    assert ["click", DRAW] not in page.commands
    assert page.commands.index(["focus", DRAW]) < page.commands.index(["press", "Enter"])
    assert page.js_clicks == 0


def test_keyboard_press_not_reflected_falls_back_to_one_js_click(monkeypatch):
    clock = Clock()
    page = FakePreviewPage(clock, ["FILE-1"], covered=True, keyboard_ok=False)
    install_page(monkeypatch, page, clock)
    clock.t = 5.0
    diag = {}

    runner.request_selected_preview(diag=diag)
    assert diag["activation"] == "js-click"
    assert page.js_clicks == 1
    assert page.posts == ["FILE-1"]


def test_no_method_reflected_is_recorded_as_none(monkeypatch):
    clock = Clock()
    page = FakePreviewPage(clock, ["FILE-1"], covered=True, keyboard_ok=False, js_click_ok=False)
    install_page(monkeypatch, page, clock)
    clock.t = 5.0
    diag = {}

    runner.request_selected_preview(diag=diag)
    assert diag["activation"] == "none"
    assert page.js_clicks == 1
    assert page.posts == []


def test_hit_summary_reports_off_viewport_center_before_scroll():
    got = runner.describe_hit({"found": True,
                               "before": {"x": 50, "y": 1412, "inViewport": False, "onButton": False,
                                          "cover": None, "vw": 1280, "vh": 577},
                               "after": {"x": 50, "y": 288, "inViewport": True, "onButton": True,
                                         "cover": None, "vw": 1280, "vh": 577}})
    assert "화면 밖" in got and "보기 단추" in got
    assert runner.describe_hit(None) == "적중 검사 못 함"
    assert "없음" in runner.describe_hit({"found": False})


def test_timeout_classification_separates_client_and_server():
    """(c) 클릭 뒤 POST 관측 여부로 가른다. 증거를 못 읽으면 판정불가이고 차단이다."""
    def post(status=None):
        row = {"method": "POST", "url": "https://dev.invalid/api/v1/previews"}
        if status is not None:
            row["status"] = status
        return row

    classify = runner.classify_preview_timeout
    assert classify(True, [], 0) == "client_no_request"
    assert classify(True, [{"method": "GET", "url": "https://dev.invalid/api/v1/previews/R1",
                            "status": 200}], 0) == "client_no_request"
    assert classify(True, [post()], 0) == "server_pending"
    assert classify(True, [post(502)], 0) == "server_http_502"
    assert classify(True, [post(202)], 0) == "server_no_terminal"
    assert classify(False, [], 0) == "evidence_unavailable"
    # 요청 기록은 0건인데 페이지 자원 기록에 POST 가 있으면 기록을 믿지 않는다
    assert classify(True, [], 1) == "evidence_unavailable"
    blocks = runner.preview_row_blocks
    assert blocks({"render": "안 그려짐", "classification": "client_no_request"}) is False
    for cls in ["server_pending", "server_http_502", "server_no_terminal", "evidence_unavailable",
                "runner_not_ready", ""]:
        assert blocks({"render": "안 그려짐", "classification": cls}) is True
    assert blocks({"render": "그려짐", "classification": ""}) is False


PREVIEW_ROWS = [
    (15, "surface (ERA5 GRIB 원자료)", "렌더 성립(3패스 중 1회)"),
    (17, "nc 대상", "렌더 성립"),
    (19, "bin 대상", "렌더 성립"),
    (21, "tif 대상", "렌더 성립"),
    (25, "hdf4 대상", "렌더 성립"),
]
NO_DATE = "파일 내부 날짜 정보는 없음"


def verify_env(monkeypatch, tmp_path, requests_for_15):
    """phase_verify 를 화면 없이 돌린다. seq 15 만 terminal/display 에 끝내 닿지 않는다."""
    clock = Clock()
    logs = []
    runner.set_work_dir(tmp_path)
    monkeypatch.setattr(runner, "CFG", SimpleNamespace(dry_run=False, verbose=False,
                                                       base_url="https://dev.invalid"))
    monkeypatch.setattr(runner, "time", clock)
    monkeypatch.setattr(runner, "save_state", lambda st: None)
    monkeypatch.setattr(runner, "log", lambda msg, echo=True: logs.append(str(msg)))
    datasets = [dict(seq=seq, name=name, preview_expected=exp, period="p", summary="s")
                for seq, name, exp in PREVIEW_ROWS]
    datasets += [dict(seq=1, name="DEM", period="p", summary="DEM " + NO_DATE,
                      preview_expected="미측정"),
                 dict(seq=2, name="Aspect", period="p", summary="Aspect " + NO_DATE,
                      preview_expected="미측정")]
    plan = {"datasets": datasets, "edges": [], "projects": []}
    st = {"steps": {}, "datasets": {
        str(d["seq"]): {"dataset_id": "D" + str(d["seq"]), "status": "done", "name": d["name"]}
        for d in datasets}}
    details = {"D" + str(d["seq"]): {"basicInfo": {"period": "p"}, "summary": d["summary"]}
               for d in datasets}
    current = {"did": ""}
    opened = []
    monkeypatch.setattr(runner, "catalog_total", lambda: (len(datasets), "m", len(datasets)))
    monkeypatch.setattr(runner, "stored_period_matches", lambda e, s: True)
    monkeypatch.setattr(runner, "authenticated_api",
                        lambda method, path: details[path.rsplit("/", 1)[1]])
    monkeypatch.setattr(runner, "open_url",
                        lambda path="": current.__setitem__("did", path.rsplit("/", 1)[-1]))
    monkeypatch.setattr(runner, "wait_css", lambda *a, **k: True)
    monkeypatch.setattr(runner, "count", lambda css: 1)
    monkeypatch.setattr(runner, "body_text", lambda: "")
    monkeypatch.setattr(runner, "dump_failure", lambda tag, reason: None)
    monkeypatch.setattr(runner, "request_selected_preview",
                        lambda *a, **k: opened.append(current["did"]) or ("F-" + current["did"]))

    def js(script, default=None, **_kwargs):
        stuck = current["did"] == "D15"
        if "imageCount" in script:
            if stuck:
                return {"slotState": "idle", "imageCount": 0, "decodedCount": 0,
                        "unavailable": 0, "totalText": ""}
            return {"slotState": "done", "imageCount": 1, "decodedCount": 1,
                    "unavailable": 0, "totalText": "총 1.0초"}
        if "getEntriesByType" in script:
            return {"posts": 0}
        return {"fileId": "F-" + current["did"], "drawEnabled": False, "slotState": "idle",
                "variableCount": 0, "variableValue": "", "instantCount": 0, "now": 0}

    def ab(args, **_kwargs):
        if args[:2] == ["network", "requests"]:
            return 0, {"requests": requests_for_15 if current["did"] == "D15" else []}, ""
        if args[0] == "console":
            return 0, {"messages": [{"type": "error", "text": "boom"}]}, ""
        if args[0] == "errors":
            return 0, {"errors": []}, ""
        return 0, {}, ""

    monkeypatch.setattr(runner, "js", js)
    monkeypatch.setattr(runner, "ab", ab)
    return st, plan, opened, logs


def read_table(tmp_path):
    lines = (tmp_path / "verify-previews.tsv").read_text(encoding="utf-8").splitlines()
    return [line.split("\t") for line in lines]


def test_failing_preview_row_does_not_abort_later_rows_and_yields_table(monkeypatch, tmp_path):
    """(b)·(c) 서버 쪽 실패(POST 502)는 나머지 행을 계속 점검하되 단계를 실패시킨다."""
    st, plan, opened, logs = verify_env(monkeypatch, tmp_path, [
        {"method": "POST", "url": "https://dev.invalid/api/v1/previews", "status": 502,
         "headers": {"Authorization": "Bearer secret"}}])

    with pytest.raises(runner.Fail):
        runner.phase_verify(st, plan)

    assert opened == ["D15", "D17", "D19", "D21", "D25"]
    table = read_table(tmp_path)
    assert table[0][:7] == ["seq", "name", "format", "preview_expected", "outcome",
                            "classification", "verdict"]
    rows = {r[0]: r for r in table[1:]}
    assert sorted(rows, key=int) == ["15", "17", "19", "21", "25"]
    assert rows["15"][1] == "surface (ERA5 GRIB 원자료)"
    assert rows["15"][3] == "렌더 성립(3패스 중 1회)"
    assert rows["15"][5] == "server_http_502"
    assert rows["15"][6] == "차단"
    assert "fail/verify-preview-15-grib-network.json" in rows["15"][7]
    assert all(rows[s][6] == "통과" for s in ["17", "19", "21", "25"])
    # 행마다 슬롯 안 주 이미지 계수 · decode 계수를 판정표에 남긴다(시간 초과 행 포함).
    assert table[0][10:12] == ["images", "decoded"]
    assert rows["15"][10:12] == ["0", "0"]
    assert all(rows[s][10:12] == ["1", "1"] for s in ["17", "19", "21", "25"])
    assert any("imageCount 0" in line and "decodedCount 0" in line for line in logs)
    assert st["steps"]["verify"]["status"] == "partial"
    network = json.loads((tmp_path / "fail" / "verify-preview-15-grib-network.json").read_text())
    assert "secret" not in json.dumps(network)
    assert any("server_http_502" in line for line in logs)


def test_client_no_request_row_is_observed_and_does_not_fail_the_phase(monkeypatch, tmp_path):
    """(c) 클릭 뒤 POST 0건은 「관측 · 제품 결함 추적」 — 단계는 통과한다(Ted 판단 2026-09-25)."""
    st, plan, opened, logs = verify_env(monkeypatch, tmp_path, [])

    runner.phase_verify(st, plan)

    assert opened == ["D15", "D17", "D19", "D21", "D25"]
    rows = {r[0]: r for r in read_table(tmp_path)[1:]}
    assert rows["15"][5] == "client_no_request"
    assert rows["15"][6] == "관측 · 제품 결함 추적"
    assert st["steps"]["verify"]["status"] == "done"
    assert (tmp_path / "fail" / "verify-preview-15-grib-console.json").exists()
    assert any("client_no_request" in line for line in logs)


def test_press_method_and_hit_test_reach_table_and_unreflected_press_skips_display_wait(
        monkeypatch, tmp_path):
    """누름 방법·적중 검사가 판정표·증거에 남고, 어떤 누름도 반영되지 않은 행은 표시 대기 없이 적힌다."""
    st, plan, opened, logs = verify_env(monkeypatch, tmp_path, [])
    current = {"n": 0}

    def fake_request(target_file_id=None, diag=None):
        did = "D" + str(PREVIEW_ROWS[current["n"]][0])
        current["n"] += 1
        opened.append(did)
        diag["activation"] = "none" if did == "D15" else "focus+Enter"
        diag["hit_summary"] = "스크롤 뒤 중심 (50,300) 을 덮은 요소 = div testid=resume-drafts"
        return "F-" + did

    monkeypatch.setattr(runner, "request_selected_preview", fake_request)
    started = runner.time.time()
    runner.phase_verify(st, plan)

    table = read_table(tmp_path)
    assert table[0][8:10] == ["activation", "hit_test"]
    rows = {r[0]: r for r in table[1:]}
    assert rows["15"][4] == "누름 미반영"
    assert rows["15"][5] == "client_no_request"
    assert rows["15"][8] == "none" and "resume-drafts" in rows["15"][9]
    assert rows["17"][8] == "focus+Enter" and rows["17"][6] == "통과"
    network = json.loads((tmp_path / "fail" / "verify-preview-15-grib-network.json").read_text())
    assert network["activation"] == "none" and "resume-drafts" in network["hit_test"]
    # 행 15 는 120 s 표시 대기를 하지 않았다(나머지 네 행은 곧바로 display 에 닿는다).
    assert runner.time.time() - started < runner.PREVIEW_DISPLAY_WAIT_S
