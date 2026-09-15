"""`runner.py` 판정 함수 시험 — 브라우저 없이 도는 순수 단위 시험.

- 대상 = 계획 행 → 「가공 단계」 선택 동작 · 분석 실패 자리의 갈림 · 계정 파일 수용 판정.
- 브라우저(`agent-browser`)를 부르지 않는다. `CFG` 도 세우지 않는다.
- 판정 = 반환값과 예외 문면. 이름이 실린 실패만 수용한다.
"""

import importlib.util
import json
import os
import pathlib

import pytest

TOOL_DIR = pathlib.Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("dev_seed_runner", TOOL_DIR / "runner.py")
runner = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(runner)

LEVEL_OPTIONS = ["Lv0", "Lv1", "Lv2", "Lv3"]


def row(seq, name, level):
    ds = dict()
    ds["seq"] = seq
    ds["name"] = name
    if level is not None:
        ds["processing_level"] = level
    return ds


# ── ⑴ 계획 행 → 「가공 단계」 선택 동작 ────────────────────────────────────


def test_모든_계획_행이_계획값_그대로의_선택_동작을_낸다():
    rows = [row(i + 1, "데이터셋 " + str(i + 1), lv) for i, lv in enumerate(LEVEL_OPTIONS)]
    for ds in rows:
        action = runner.level_action(ds, LEVEL_OPTIONS)
        assert action[0] == "select"
        assert action[1] == runner.LEVEL_CSS
        assert action[2] == ds["processing_level"]


def test_가공_단계_없는_행은_이름이_실린_실패다():
    with pytest.raises(runner.Fail) as exc:
        runner.level_action(row(7, "HSR 레이더 반사도 원자료", None), LEVEL_OPTIONS)
    assert "HSR 레이더 반사도 원자료" in str(exc.value)


def test_선택지에_없는_값은_이름과_값이_실린_실패다():
    with pytest.raises(runner.Fail) as exc:
        runner.level_action(row(8, "SPI-4weeks", "Lv3"), ["Lv0", "Lv1", "Lv2"])
    assert "SPI-4weeks" in str(exc.value)
    assert "Lv3" in str(exc.value)


def test_정본_4값_밖의_값은_실패다():
    with pytest.raises(runner.Fail) as exc:
        runner.level_action(row(9, "NDVI 변형", "Lv9"), LEVEL_OPTIONS)
    assert "NDVI 변형" in str(exc.value)


# ── ⑵ 분석 실패 자리의 갈림 ───────────────────────────────────────────────


def test_분석_실패라도_reg_open_이_활성이면_등록으로_잇는다():
    decision, reason = runner.failure_path(True, True, "형식 인식 실패")
    assert decision == "register"
    assert "형식 인식 실패" in reason


def test_보기만_할게요_는_갈림에_남아_있지_않다():
    decision, _ = runner.failure_path(True, True, "형식 인식 실패")
    assert decision != "view-only"
    assert "reg-viewonly" not in json.dumps(runner.failure_path(True, True, "x"), ensure_ascii=False)


def test_reg_open_이_대기_뒤에도_비활성이면_사유가_실린_blocked_다():
    decision, reason = runner.failure_path(True, False, "형식 인식 실패")
    assert decision == "blocked"
    assert "형식 인식 실패" in reason
    assert "reg-open" in reason


def test_reg_open_이_아예_없으면_사유가_실린_blocked_다():
    decision, reason = runner.failure_path(False, False, "파일을 받지 못했어요")
    assert decision == "blocked"
    assert "파일을 받지 못했어요" in reason
    assert "reg-open" in reason


# ── ⑶ 계정 파일 · 비밀 취급 ───────────────────────────────────────────────

ACCOUNTS = [
    {"email": "op@example.com", "name": "운영자", "role": "교수", "lab": "연구실 A", "admin": True},
    {"email": "one@example.com", "name": "한 사람", "role": "연구원", "lab": "연구실 A", "admin": False},
]


def write_accounts(tmp_path, mode, payload=None):
    path = tmp_path / "accounts.json"
    path.write_text(json.dumps(payload if payload is not None else ACCOUNTS,
                               ensure_ascii=False), encoding="utf-8")
    os.chmod(path, mode)
    return path


def test_0644_계정_파일은_거절한다(tmp_path):
    path = write_accounts(tmp_path, 0o644)
    with pytest.raises(runner.Fail) as exc:
        runner.load_accounts_file(path)
    assert "0600" in str(exc.value)
    assert path.name in str(exc.value)


def test_0600_계정_파일은_수용한다(tmp_path):
    entries = runner.load_accounts_file(write_accounts(tmp_path, 0o600))
    assert [e["email"] for e in entries] == ["op@example.com", "one@example.com"]
    assert entries[0]["admin"] is True
    assert entries[1]["admin"] is False


def test_admin_이_불_값이_아니면_이메일이_실린_실패다(tmp_path):
    bad = [{"email": "x@example.com", "name": "엑스", "role": "교수", "admin": "yes"}]
    path = write_accounts(tmp_path, 0o600, bad)
    with pytest.raises(runner.Fail) as exc:
        runner.load_accounts_file(path)
    assert "x@example.com" in str(exc.value)


def test_필수_칸이_빠지면_실패다(tmp_path):
    bad = [{"email": "y@example.com", "admin": False}]
    path = write_accounts(tmp_path, 0o600, bad)
    with pytest.raises(runner.Fail) as exc:
        runner.load_accounts_file(path)
    assert "y@example.com" in str(exc.value)


SECRET = "initial-password-12345"


def test_비밀번호는_동작_목록에도_상태_행에도_기록에도_없다():
    entry = dict(ACCOUNTS[0])
    actions = runner.account_form_actions(entry)
    state = runner.account_state_row(entry, "created", "추가했어요")
    line = runner.account_log_line(entry)
    blob = json.dumps([actions, state, line], ensure_ascii=False)
    # 칸 이름(`initialPassword`)은 선택자라 남는다. 남으면 안 되는 것은 **값**이다.
    assert SECRET not in blob
    assert runner.SECRET_MARK in line
    assert state["email"] == entry["email"]
    assert "initial_password" not in state
    assert SECRET not in line


def test_비밀번호_칸은_값_없이_자리만_실린다():
    actions = runner.account_form_actions(dict(ACCOUNTS[1]))
    secret_actions = [a for a in actions if a[0] == "secret"]
    assert len(secret_actions) == 1
    assert secret_actions[0][1] == runner.ACCOUNT_CSS["password"]
    assert len(secret_actions[0]) == 2


def test_0644_초기_비밀번호_파일은_거절한다(tmp_path):
    path = tmp_path / "initial.txt"
    path.write_text(SECRET + "\n", encoding="utf-8")
    os.chmod(path, 0o644)
    with pytest.raises(runner.Fail) as exc:
        runner.read_secret_file(path, "초기 비밀번호")
    assert "0600" in str(exc.value)
    assert SECRET not in str(exc.value)


def test_0600_초기_비밀번호_파일은_값을_돌려주고_이름만_기록한다(tmp_path):
    path = tmp_path / "initial.txt"
    path.write_text(SECRET + "\n", encoding="utf-8")
    os.chmod(path, 0o600)
    assert runner.read_secret_file(path, "초기 비밀번호") == SECRET


# ── 상태 파일 하위 호환 ───────────────────────────────────────────────────


def test_옛_상태값_done_도_등록된_것으로_센다():
    assert runner.is_registered("done") is True
    assert runner.is_registered("registered") is True
    assert runner.is_registered("registered_no_preview") is True
    assert runner.is_registered("blocked") is False
    assert runner.is_registered("failed") is False
    assert runner.is_registered(None) is False


# ── set_checkbox — `click` 이 아니라 `check`/`uncheck` 로 상태를 맞춘다 ──────────
# 왜 = 계정 관리 화면의 「관리자로 등록」은 `<label>` 이 `<input type="checkbox">` 를 감싸고 있어
#   `click` 이 상태를 바꾸지 못했다(2026-09-14 4회차 계정 단계 실측 · click 뒤에도 checked=false ·
#   `check` 는 true). 이 시험은 그 동작 이름과 fail-closed(바뀌지 않으면 이름을 대고 멈춤)를 고정한다.

def _checkbox_world(monkeypatch, initial, honors):
    """대역 브라우저 — `honors` 에 든 동작만 체크 상태를 바꾼다. 반환 = (호출 목록, 상태 상자)."""
    calls = []
    box = {"checked": initial}

    def fake_ab(args, **kw):
        calls.append(list(args))
        if args[0] in honors:
            if args[0] == "check":
                box["checked"] = True
            elif args[0] == "uncheck":
                box["checked"] = False
            elif args[0] == "click":
                box["checked"] = not box["checked"]
        return (0, "", "")

    def fake_js(script, default=None, **kw):
        return box["checked"]

    monkeypatch.setattr(runner, "ab", fake_ab)
    monkeypatch.setattr(runner, "js", fake_js)
    return calls, box


def test_관리자_체크는_check_로_켠다(monkeypatch):
    calls, box = _checkbox_world(monkeypatch, initial=False, honors={"check", "uncheck"})
    runner.set_checkbox('[data-testid="account-create"] input[name="operator"]', True, "관리자로 등록")
    assert [c[0] for c in calls] == ["check"]
    assert box["checked"] is True


def test_이미_켜져_있으면_건드리지_않는다(monkeypatch):
    calls, _ = _checkbox_world(monkeypatch, initial=True, honors={"check", "uncheck"})
    runner.set_checkbox("css", True, "관리자로 등록")
    assert calls == []


def test_끄는_쪽은_uncheck_다(monkeypatch):
    calls, box = _checkbox_world(monkeypatch, initial=True, honors={"check", "uncheck"})
    runner.set_checkbox("css", False, "관리자로 등록")
    assert [c[0] for c in calls] == ["uncheck"]
    assert box["checked"] is False


def test_label_이_감싼_칸처럼_click_만_듣는_대역에서는_이름을_대고_멈춘다(monkeypatch):
    # 실물 재현 — check 를 무시하고 click 만 듣는 세계에서는 상태가 안 바뀌고, 그때 조용히 지나가면 안 된다.
    _checkbox_world(monkeypatch, initial=False, honors={"click"})
    with pytest.raises(runner.Fail) as exc:
        runner.set_checkbox("css", True, "관리자로 등록")
    assert "체크 상태를 바꾸지 못했다" in str(exc.value)


def test_account_creation_unchecks_default_admin_for_regular_user(monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(runner, 'CFG', SimpleNamespace(dry_run=False))
    calls, box = _checkbox_world(monkeypatch, initial=True, honors={"check", "uncheck"})
    for name in ('open_account_form', 'fill_secret', 'activate', 'select_by_label'):
        monkeypatch.setattr(runner, name, lambda *args: None)
    monkeypatch.setattr(runner, 'wait_css', lambda *args: True)
    monkeypatch.setattr(runner, 'el_text', lambda *args: '계정을 추가했어요.')
    runner.create_account({}, ACCOUNTS[1], 'fixture-secret')
    assert box['checked'] is False
