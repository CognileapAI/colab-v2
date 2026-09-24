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


@pytest.mark.parametrize('web,legacy,cli,expected', [
    ('https://web.invalid', 'https://legacy.invalid', None, 'https://web.invalid'),
    ('https://web.invalid', 'https://legacy.invalid', 'https://cli.invalid', 'https://cli.invalid'),
    ('', 'https://legacy.invalid', None, 'https://legacy.invalid'),
    ('https://web.invalid', '', None, 'https://web.invalid'),
    ('', '', None, None),
])
def test_base_url_cli_and_environment_precedence(monkeypatch, tmp_path, web, legacy, cli, expected):
    monkeypatch.setenv('COLAB_DEV_WEB_URL', web)
    monkeypatch.setenv('COLAB_DEV_URL', legacy)
    (tmp_path / 'upload-plan.json').write_text('{}')
    argv = ['runner.py', '--phase', 'report', '--work-dir', str(tmp_path)]
    if cli:
        argv += ['--base-url', cli]
    monkeypatch.setattr('sys.argv', argv)
    seen = []
    monkeypatch.setattr(runner, 'phase_report', lambda *_: seen.append(runner.CFG.base_url))
    try:
        assert runner.main() == (0 if expected else 2)
        assert seen == ([expected] if expected else [])
    finally:
        if runner.LOG_FH:
            runner.LOG_FH.close()
            runner.LOG_FH = None


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


def test_월_기간은_연월까지만_화면입력동작을_낸다():
    ds = {"name": "DEM", "period": {"start": "2023-05", "end": "2023-05",
                                          "granularity": "월"}}
    assert runner.period_form_actions(ds) == [
        ["click", '[data-testid="reg-period-open"]'],
        ["click", '[data-testid="reg-period-unit-월"]'],
        ["fill", '[data-testid="reg-period-pop-start-year"]', "2023"],
        ["fill", '[data-testid="reg-period-pop-start-month"]', "05"],
        ["fill", '[data-testid="reg-period-pop-end-year"]', "2023"],
        ["fill", '[data-testid="reg-period-pop-end-month"]', "05"],
        ["click", '[data-testid="reg-period-apply"]'],
    ]


def test_기간_누락과_월을_일값으로_바꾼_계획은_거절한다():
    with pytest.raises(runner.Fail, match="기간.*DEM"):
        runner.period_form_actions({"name": "DEM"})
    with pytest.raises(runner.Fail, match="정밀도"):
        runner.period_form_actions({"name": "DEM", "period": {
            "start": "2023-05-01", "end": "2023-05-31", "granularity": "월"}})
    with pytest.raises(runner.Fail, match="정밀도"):
        runner.period_form_actions({"name": "bad", "period": {
            "start": "2023-02-31", "end": "2023-02-31", "granularity": "일"}})


def test_prediction_registration_excludes_auxiliary_parents_then_api_adds_them():
    ds = {"name": "Prediction (공간상세화)",
          "parents": ["GK2A_NDVI_mean_202305", "DEM", "Aspect"],
          "parent_roles": {"DEM": "보조입력", "Aspect": "보조입력"}}
    registration, auxiliary = runner.split_lineage_parents(ds)
    assert registration == ["GK2A_NDVI_mean_202305"]
    assert auxiliary == ["DEM", "Aspect"]


def test_auxiliary_resume_only_requests_missing_links():
    desired = [("DEM-ID", "보조입력"), ("ASPECT-ID", "보조입력")]
    graph = {"edges": [
        {"childDatasetId": "PRED-ID", "parentDatasetId": "DEM-ID", "parentRole": "보조입력"},
        {"childDatasetId": "OTHER-ID", "parentDatasetId": "ASPECT-ID", "parentRole": "주입력"},
    ]}
    assert runner.missing_auxiliary_links(desired, graph, "PRED-ID") == [("ASPECT-ID", "보조입력")]
    wrong = {"edges": [{"childDatasetId": "PRED-ID", "parentDatasetId": "DEM-ID",
                         "parentRole": "주입력"}]}
    with pytest.raises(runner.Fail, match="역할"):
        runner.missing_auxiliary_links(desired, wrong, "PRED-ID")


def test_pending_auxiliary_resume_does_not_upload_again(monkeypatch):
    ds = {"seq": 12, "name": "Prediction (공간상세화)", "project": "vegetation",
          "bytes": 1, "grid_bytes": 0, "file_count": 1,
          "parents": ["DEM"], "parent_roles": {"DEM": "보조입력"}}
    st = {"datasets": {"12": {"seq": 12, "name": ds["name"],
                                 "status": "registered_pending_auxiliary",
                                 "dataset_id": "PRED-ID"}}}
    monkeypatch.setattr(runner, "reconcile_auxiliary_lineage", lambda *_: 1)
    monkeypatch.setattr(runner, "save_state", lambda *_: None)
    monkeypatch.setattr(runner, "open_url", lambda *_: pytest.fail("resume must not upload"))
    runner.do_dataset(st, ds)
    assert st["datasets"]["12"]["status"] == "done"
    assert st["datasets"]["12"]["auxiliary_verified"] == 1
    assert not runner.is_registered("registered_pending_auxiliary")


def test_dataset_without_auxiliary_does_not_call_lineage_api(monkeypatch):
    ds = {"name": "ordinary", "parents": ["source"]}
    st = {"datasets": {"1": {"name": "source", "dataset_id": "SOURCE-ID"}}}
    monkeypatch.setattr(runner, "lineage_api", lambda *_: pytest.fail("no auxiliary API call"))
    assert runner.reconcile_auxiliary_lineage(st, ds, "CHILD-ID") == 0


def test_lineage_checks_radio_then_connects_confirmed_card(monkeypatch):
    ds = {"seq": 3, "name": "child", "parents": ["parent"]}
    st = {"datasets": {"2": {"name": "parent", "dataset_id": "PARENT-ID"}}}
    actions = []
    checked = set()

    def browser(args, **_kwargs):
        actions.append(args)
        if args[0] == "check":
            checked.add(args[1])
        if args[:2] == ["is", "checked"]:
            return 0, {"checked": args[2] in checked}, ""
        return 0, {}, ""

    monkeypatch.setattr(runner, "ab", browser)
    monkeypatch.setattr(runner, "activate", lambda css, label="": actions.append(["activate", css]))
    monkeypatch.setattr(runner, "wait_css", lambda *_: True)
    monkeypatch.setattr(runner, "enabled", lambda *_: True)
    monkeypatch.setattr(runner, "count", lambda _css: 1)

    runner.do_lineage(st, ds)

    radio = '[data-testid="lin-pick-PARENT-ID"]'
    assert ["check", radio] in actions
    assert ["is", "checked", radio] in actions
    assert ["activate", ".lin-find .modal-f .btn-primary"] in actions
    assert not any("lin-confirm" in str(action) for action in actions)


def test_stored_period_verification_preserves_month_granularity():
    expected = {"start": "2023-05", "end": "2023-05", "granularity": "월"}
    stored = {"start": "2023-05-01T00:00:00Z", "end": "2023-05-01T00:00:00Z",
              "granularity": "월"}
    assert runner.stored_period_matches(expected, stored)
    assert not runner.stored_period_matches(expected, dict(stored, granularity="일"))


def test_verify_contract_rejects_missing_period_or_model_input_description():
    good = {"dataset_count_ui": 28, "dataset_count_expected": 28,
            "periods_ok": 28, "periods_expected": 28,
            "model_input_descriptions_ok": 2, "edges_ok": 18, "edges_expected": 18,
            "previews": [{"render": "그려짐"}]}
    assert runner.verify_result_passes(good)
    assert not runner.verify_result_passes(dict(good, periods_ok=27))
    assert not runner.verify_result_passes(dict(good, model_input_descriptions_ok=1))
    assert not runner.verify_result_passes(dict(good, periods_missing=[{"name": "DEM"}]))


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


def test_labless_operator_profile_is_accepted(tmp_path):
    entry = {"email": "operator@example.com", "name": "운영자", "admin": True}
    rows = runner.load_accounts_file(write_accounts(tmp_path, 0o600, [entry]))
    assert rows[0]["role"] == ""
    assert not rows[0].get("lab")
    assert rows[0]["admin"] is True


def test_lab_and_role_must_be_supplied_together(tmp_path):
    entry = {"email": "operator@example.com", "name": "운영자", "admin": True, "role": "교수"}
    with pytest.raises(runner.Fail):
        runner.load_accounts_file(write_accounts(tmp_path, 0o600, [entry]))


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


# ── ⑸ 업로드 마법사 필수 칸 — 분류·유형(①) · 관측 간격(②) · Lv0 출처 두 칸(③) ─────────
# 2026-09-24 dev 3회차 실측 — 「분류 필수」·「유형 필수」가 「직접 선택해 주세요」로 남아
# 「다음 →」이 비활성이었고 러너는 ① 에서 멈췄다(6705675d). 관측 간격·Lv0 출처는 e171c5c2 부터
# 제출 시점 필수다(`UploadModal.tsx` 의 제출 검사 · 서버 `_validate_create_required_metadata`).

def classified(seq=1, name="HSR 레이더 반사도 원자료", level="Lv0", parents=None, **over):
    ds = {"seq": seq, "name": name, "processing_level": level, "parents": parents or [],
          "category": "기상·기후 인자", "data_type": "지상관측자료",
          "observation_interval": {"value": "5", "unit": "분"}}
    if level == "Lv0":
        ds["source"] = {"url": "https://apihub.kma.go.kr/", "downloaded_on": "2025-08-13"}
    ds.update(over)
    return ds


def test_분류_유형은_계획값_그대로_두_칸을_고른다():
    assert runner.classify_actions(classified()) == [
        ["select", '[data-testid="reg-category"]', "기상·기후 인자"],
        ["select", '[data-testid="reg-datatype"]', "지상관측자료"],
    ]


@pytest.mark.parametrize("key,value,needle", [
    ("category", None, "분류"), ("category", "기상 인자", "분류"),
    ("data_type", "", "유형"), ("data_type", "레이더자료", "유형"),
])
def test_분류_유형이_없거나_사전_밖이면_이름이_실린_실패다(key, value, needle):
    with pytest.raises(runner.Fail) as exc:
        runner.classify_actions(classified(**{key: value}))
    assert "HSR 레이더 반사도 원자료" in str(exc.value) and needle in str(exc.value)


def test_관측_간격은_숫자_칸과_단위_칸을_채운다():
    assert runner.interval_actions(classified()) == [
        ["fill", '[data-testid="reg-interval-value"]', "5"],
        ["select", '[data-testid="reg-interval-unit"]', "분"],
    ]


@pytest.mark.parametrize("interval", [None, {"value": "5"}, {"value": "0", "unit": "분"},
                                      {"value": "1.5", "unit": "분"}, {"value": "1", "unit": "주"}])
def test_관측_간격이_비었거나_형상이_틀리면_실패다(interval):
    with pytest.raises(runner.Fail) as exc:
        runner.interval_actions(classified(observation_interval=interval))
    assert "관측 간격" in str(exc.value)


def test_Lv0_는_출처_주소와_내려받은_날을_채운다():
    assert runner.source_actions(classified()) == [
        ["fill", '[data-testid="reg-source-url"]', "https://apihub.kma.go.kr/"],
        ["fill", '[data-testid="reg-source-downloaded-on"]', "2025-08-13"],
    ]


def test_Lv0_가_아니면_출처_동작이_없다():
    assert runner.source_actions(classified(level="Lv1", parents=["x"])) == []


@pytest.mark.parametrize("source", [None, {"url": "", "downloaded_on": "2025-08-13"},
                                    {"url": "https://x.invalid/", "downloaded_on": "2025-02-31"},
                                    {"url": "https://x.invalid/", "downloaded_on": "2025/08/13"}])
def test_Lv0_출처가_비었거나_날짜가_틀리면_실패다(source):
    with pytest.raises(runner.Fail) as exc:
        runner.source_actions(classified(source=source))
    assert "출처" in str(exc.value)


def test_datasets_국면은_업로드_전에_계획_전행의_필수값을_본다(monkeypatch):
    # 한 행이라도 비면 **첫 업로드 전에** 이름을 대고 멈춘다 — 파일을 올린 뒤 ① 에서 서는 일을 막는다.
    from types import SimpleNamespace
    rows = [classified(seq=1), classified(seq=2, name="rn15 15분 누적강수", category=None)]
    monkeypatch.setattr(runner, "CFG", SimpleNamespace(only_seq=None, from_seq=None, force=False))
    monkeypatch.setattr(runner, "do_dataset", lambda *_: pytest.fail("must not upload"))
    with pytest.raises(runner.Fail) as exc:
        runner.phase_datasets({"datasets": {}, "steps": {}}, {"datasets": rows})
    assert "rn15 15분 누적강수" in str(exc.value)


def test_fill_period_는_여는_단추와_적용_단추를_초점_Enter_로_누른다(monkeypatch):
    # 2026-09-24 로컬 실측(ea21d8c2 번들) — 「기간」 단추 중심이 모달 머리(.modal-h) 아래에 깔려
    # `click` 이 rc 0 인데 팝오버가 0 이었다. 여는·적용 단추는 activate(초점 ＋ Enter)여야 한다.
    from types import SimpleNamespace
    ds = {"name": "HSR", "period": {"start": "2019-07-28", "end": "2024-07-09", "granularity": "일"}}
    seen = []
    monkeypatch.setattr(runner, "CFG", SimpleNamespace(dry_run=False))
    monkeypatch.setattr(runner, "activate", lambda css, label="": seen.append(("activate", css)))
    monkeypatch.setattr(runner, "ab", lambda action, **_: seen.append(tuple(action[:2])) or (0, {}, ""))
    monkeypatch.setattr(runner, "wait_css", lambda *_: True)
    monkeypatch.setattr(runner, "wait_gone", lambda *_: True)
    runner.fill_period(ds)
    assert seen[0] == ("activate", '[data-testid="reg-period-open"]')
    assert seen[-1] == ("activate", '[data-testid="reg-period-apply"]')
    assert ("click", '[data-testid="reg-period-open"]') not in seen


def test_분류_선택은_화면값을_되읽어_확인한다(monkeypatch):
    screen = {}

    def fake_ab(action, **_):
        screen[action[1]] = action[2]
        return 0, {}, ""
    options = ["수문 인자", "기상·기후 인자", "식생·탄소 인자", "사회·경제 인자", "환경 인자",
               "지상관측자료", "위성자료", "재분석자료", "수치모형자료", "합성자료", "관측 기반 산출물"]
    from types import SimpleNamespace
    monkeypatch.setattr(runner, "CFG", SimpleNamespace(dry_run=False))
    monkeypatch.setattr(runner, "ab", fake_ab)
    monkeypatch.setattr(runner, "wait_css", lambda *_: True)
    monkeypatch.setattr(runner, "select_state", lambda css: {"value": screen.get(css, ""), "options": options})
    runner.select_classify(classified())
    assert screen['[data-testid="reg-category"]'] == "기상·기후 인자"
    assert screen['[data-testid="reg-datatype"]'] == "지상관측자료"
    monkeypatch.setattr(runner, "select_state", lambda css: {"value": "", "options": options})
    with pytest.raises(runner.Fail) as exc:
        runner.select_classify(classified())
    assert "들어가지 않았다" in str(exc.value)
