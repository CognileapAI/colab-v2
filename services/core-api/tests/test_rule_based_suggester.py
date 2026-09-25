"""K3 `WU-S5` — **규칙 기반 팔.** 모델 호출 0회 · DB 접속 0회 · 쓰기 0건.

이 파일이 재는 것은 「모델 없이도 「없다」가 구조에서 나오는가」다. 규칙 팔은
`d3_lineage_signals.compare` 가 낸 **대조 결과**만 근거로 삼으므로, 맞는 축이 없는
후보는 어떤 문장으로도 제안이 되지 않는다 — 프롬프트가 아니라 여기가 보장한다.

⚠ **두 팔의 상위 k 절단이 같아야 한다**(Ted 판정 2회차 5 축자). 다르면 `WU-S6` 실측의
hit@3 이 「어느 팔이 더 낫나」가 아니라 「어느 팔이 더 많이 냈나」를 재게 된다. 그래서
이 파일은 두 팔을 **같은 적격 집합**에 나란히 돌려 건수를 맞대 본다.

DB 를 쓰지 않는다 — 규칙 팔은 **이미 고른 후보** 위의 순수 계산이고, 연구실 경계는
후보를 고른 자리(`select_lineage_candidates` · RLS)가 이미 그었다.
"""
from __future__ import annotations

import inspect
import json
import pathlib
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from colab_core.app import relay as _relay
from colab_core.app import rule_suggest as _rule
from colab_core.app.routes import ingestion as _ing
from colab_core.domains import d3_lineage_signals as _sig

LAB_ID = "0000000000000000000000000A"
LAB_NAME = "A 연구실"
#: 업로드 쪽 축 — 후보는 이 값과 맞느냐로만 갈린다.
UPLOAD = _sig.UploadAxes(
    file_name="rain_2024_daily.nc", crs="EPSG:4326", grid="0.25도 정규격자",
    variables=("강우량", "기온"),
    period_start="2024-01-01T00:00:00Z", period_end="2024-01-31T00:00:00Z")
FILE_META = {"fileName": UPLOAD.file_name, "kind": "단일 파일"}


def _id(n: int) -> str:
    """26자 Crockford Base32 — 시험이 세는 것은 값이 아니라 **짝이 맞는가**다."""
    return f"01ARZ3NDEKTSV4RRFFQ69G5{n:03d}"


def _pair(n: int, *, name: str | None = None, **axes):
    """후보 한 건 = 계약 본문 한 장 + 대조 축 한 벌. **같은 ID 로 짝을 맞춘다.**"""
    dataset_id = _id(n)
    payload = {"datasetId": dataset_id, "name": name or f"후보 {n}"}
    return payload, dataset_id, _sig.CandidateAxes(dataset_id=dataset_id, **axes)


def _case(*specs):
    payloads, axes = [], {}
    for payload, dataset_id, axis in specs:
        payloads.append(payload)
        axes[dataset_id] = axis
    return payloads, axes


def _suggest(candidates, axes, *, searched_count: int = 2, suggester=None) -> dict:
    arm = suggester if suggester is not None else _rule.RuleBasedLineageSuggester()
    return arm.suggest(
        lab_id=LAB_ID, lab_name=LAB_NAME, account_id="acc", file_meta=FILE_META,
        candidates=candidates, searched_count=searched_count,
        dataset_name_draft=None, subject=None, processing_level=1,
        upload_axes=UPLOAD, candidate_axes=axes)


# 맞는 축의 조각들 — 무엇이 맞아서 몇 종이 되는지를 시험이 눈으로 세게 한다.
_CRS = {"crs": "epsg:4326"}
_GRID = {"grid": " 0.25도 정규격자 "}
_VARS = {"variables": ("강우량", "유출량")}
_NAME = {"file_name": "rain_2024_daily_v2.nc"}
_PERIOD = {"period_start": "2024-01-15T00:00:00Z", "period_end": "2024-02-15T00:00:00Z"}
_NONE = {"crs": "EPSG:5179", "grid": "1km 격자", "variables": ("적설",),
         "file_name": "snow_1990.csv"}


# ═══════════════════ 근거가 있는 후보만 제안이 된다 ═════════════════════════
def test_맞는_축이_있는_후보만_제안이_된다() -> None:
    """**신호 0종 후보는 제안하지 않는다** — 규칙 팔에서도 「없다」는 구조가 말한다."""
    candidates, axes = _case(_pair(1, **_CRS), _pair(2, **_NONE))
    body = _suggest(candidates, axes)
    assert [s["parentDatasetId"] for s in body["suggestions"]] == [_id(1)]
    assert body["degraded"] is False, "살펴보고 찾은 답이다 — 「못 물어봤다」가 아니다."


def test_신호_종류가_많은_후보가_앞에_선다() -> None:
    """순위는 **검증된 신호 종류 수 내림차순**이다(라운드 `WU-S5` 축자)."""
    candidates, axes = _case(_pair(1, **_CRS), _pair(2, **{**_CRS, **_GRID, **_VARS}),
                             _pair(3, **{**_CRS, **_GRID}))
    order = [s["parentDatasetId"] for s in _suggest(candidates, axes)["suggestions"]]
    assert order == [_id(2), _id(3), _id(1)]


def test_동률이면_후보가_들어온_순서를_지킨다() -> None:
    """동률의 갈림은 **후보 선정이 매긴 순서**다 — 이 자리에서 새 순위를 만들지 않는다.

    ⚠ 라운드 초안은 `last_modified_at` 최신순을 적었는데 **그 값은 이 표면에 오지 않는다**
    (Port 가 나르는 것은 계약 본문과 대조 축뿐이다). 여기서 DB 를 다시 읽으면 「보낸 값」과
    「순위에 쓴 값」이 갈린다 — `WU-S2` 가 인용 검증에서 막아 둔 바로 그 자리다.
    """
    candidates, axes = _case(_pair(1, **_CRS), _pair(2, **_CRS))
    assert [s["parentDatasetId"] for s in _suggest(candidates, axes)["suggestions"]] \
        == [_id(1), _id(2)]
    flipped, flipped_axes = _case(_pair(2, **_CRS), _pair(1, **_CRS))
    assert [s["parentDatasetId"] for s in _suggest(flipped, flipped_axes)["suggestions"]] \
        == [_id(2), _id(1)]


# ═══════════════ 확신도·근거 한 줄은 `WU-S2` 와 같은 파생 규칙 ═══════════════
def test_확신도는_검증된_축의_종류_수에서_파생된다() -> None:
    candidates, axes = _case(_pair(1, **{**_CRS, **_GRID}), _pair(2, **_CRS))
    picked = {s["parentDatasetId"]: s for s in _suggest(candidates, axes)["suggestions"]}
    assert picked[_id(1)]["confidence"] == _sig.CONFIDENCE_SURE
    assert picked[_id(2)]["confidence"] == _sig.CONFIDENCE_VAGUE


def test_근거_한_줄도_대조_결과에서_다시_쓴다() -> None:
    """**모델의 자연어가 없는 팔이다** — 문장의 산지는 `d3_lineage_signals.rationale` 하나다."""
    candidates, axes = _case(_pair(1, **{**_CRS, **_GRID}))
    suggestion = _suggest(candidates, axes)["suggestions"][0]
    expected = _sig.rationale([_sig.Evidence(item["field"], item["uploadValue"],
                                             item["candidateValue"])
                               for item in suggestion["evidence"]])
    assert suggestion["rationale"] == expected and expected
    assert "\n" not in suggestion["rationale"]


def test_근거는_대조_결과_그대로_실린다() -> None:
    candidates, axes = _case(_pair(1, **{**_CRS, **_GRID}))
    suggestion = _suggest(candidates, axes)["suggestions"][0]
    assert [item["field"] for item in suggestion["evidence"]] == ["crs", "grid"]
    assert all(item["uploadValue"] and item["candidateValue"]
               for item in suggestion["evidence"])


# ═════════════════════════ 부모 역할 — 잠정 어림 ════════════════════════════
@pytest.mark.parametrize("axes_kwargs, role", [
    (_NAME, "주입력"),
    (_VARS, "주입력"),
    (_CRS, "보조입력"),
    (_PERIOD, "보조입력"),
])
def test_부모_역할은_파일명_변수_근거일_때만_주입력이다(axes_kwargs, role) -> None:
    """**잠정 어림이다** — 정본은 사람이 확인할 때 고른다(`Policy §5 부모 역할`)."""
    candidates, axes = _case(_pair(1, **axes_kwargs))
    assert _suggest(candidates, axes)["suggestions"][0]["suggestedParentRole"] == role


def test_부모_역할은_계약_enum_안이다() -> None:
    common = json.loads((pathlib.Path(__file__).resolve().parents[3] / "contracts"
                         / "schemas" / "common.json").read_text("utf-8"))
    allowed = set(common["$defs"]["ParentRole"]["enum"])
    candidates, axes = _case(_pair(1, **_NAME), _pair(2, **_CRS))
    roles = {s["suggestedParentRole"] for s in _suggest(candidates, axes)["suggestions"]}
    assert roles and roles <= allowed


# ═══════════════════════ 「없다」는 구조가 말한다 ════════════════════════════
def test_맞는_축이_하나도_없으면_빈_제안과_안정된_사유다() -> None:
    candidates, axes = _case(_pair(1, **_NONE), _pair(2, **_NONE))
    body = _suggest(candidates, axes)
    assert body["suggestions"] == []
    assert body["degraded"] is True
    assert body["degradedReason"] == _rule.NO_MATCHING_AXIS_REASON


def test_후보가_0건이어도_같은_모양의_빈_제안이다() -> None:
    body = _suggest([], {})
    assert body["suggestions"] == [] and body["degradedReason"] == _rule.NO_MATCHING_AXIS_REASON
    assert body["scope"] == {"labId": LAB_ID, "labName": LAB_NAME, "searchedCount": 2}


def test_대조_축이_없는_사유는_가공_단계_사유와_다른_문장이다() -> None:
    """네 번째 영 상태와 섞지 않는다 — **고칠 사람이 다르다**(한쪽은 사람이 Lv 를 고르면 된다)."""
    assert _rule.NO_MATCHING_AXIS_REASON != _ing.LEVEL_REQUIRED_REASON


def test_짝이_되는_축이_없는_후보는_조용히_빠진다() -> None:
    """후보 본문은 왔는데 자동 메타가 없는 자리 — **없는 축을 지어내지 않는다.**"""
    payload, _, _ = _pair(9, **_CRS)
    body = _suggest([payload], {})
    assert body["suggestions"] == []


# ═════════════════ 상위 k 절단이 모델 팔과 **같다** ═════════════════════════
class _FakeAi(BaseHTTPRequestHandler):
    payload: dict = {}

    def do_POST(self) -> None:                                    # noqa: N802
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        raw = json.dumps(_FakeAi.payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *args) -> None:
        return


@pytest.fixture()
def fake_ai():
    server = HTTPServer(("127.0.0.1", 0), _FakeAi)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    server.server_close()


def _many(count: int):
    return _case(*[_pair(n, **{**_CRS, **_GRID}) for n in range(1, count + 1)])


def test_상위_k_는_한_상수이고_후보_상한과_같다() -> None:
    assert _rule.SUGGESTION_LIMIT == _relay.SUGGESTION_LIMIT == _ing.LINEAGE_CANDIDATE_LIMIT


def test_두_팔이_같은_적격_집합에서_같은_건수로_잘린다(fake_ai) -> None:
    """실측(`WU-S6`)이 두 팔을 맞댈 수 있는 전제다 — 절단이 다르면 hit@3 이
    「어느 팔이 나은가」가 아니라 「어느 팔이 많이 냈나」를 잰다."""
    over = _relay.SUGGESTION_LIMIT + 2
    candidates, axes = _many(over)
    _FakeAi.payload = {
        "degraded": False,
        "scope": {"labId": LAB_ID, "labName": LAB_NAME, "searchedCount": over},
        "rawDataLikely": False,
        "suggestions": [{"suggestionId": _id(n), "kind": "가공 전 데이터",
                         "confidence": "모름", "rationale": "모델이 쓴 문장",
                         "parentDatasetId": _id(n), "parentDatasetName": f"후보 {n}",
                         "suggestedParentRole": "주입력",
                         "evidence": [{"field": "crs", "uploadValue": "EPSG:4326",
                                       "candidateValue": "epsg:4326"}]}
                        for n in range(1, over + 1)],
    }
    model = _suggest(candidates, axes, searched_count=over,
                     suggester=_relay.HttpLineageSuggestionRelay(fake_ai))
    rules = _suggest(candidates, axes, searched_count=over)
    assert len(model["suggestions"]) == len(rules["suggestions"]) == _relay.SUGGESTION_LIMIT


# ═══════════════════ 모델을 부르지 않는다 · 같은 Port ═══════════════════════
def test_규칙_팔은_모델을_한_번도_부르지_않는다(monkeypatch) -> None:
    """전송 자리를 막아 둔다 — 부르면 **시험이 터진다**(토큰 0의 오라클)."""
    calls: list = []

    def _explode(*args, **kwargs):
        calls.append(args)
        raise AssertionError("규칙 팔이 나가는 요청을 만들었다.")

    monkeypatch.setattr(_relay, "_request", _explode)
    monkeypatch.setattr(_relay.urllib.request, "urlopen", _explode)
    candidates, axes = _case(_pair(1, **_CRS), _pair(2, **_NONE))
    assert len(_suggest(candidates, axes)["suggestions"]) == 1
    assert calls == []


def test_규칙_팔은_모델_팔과_같은_Port_다() -> None:
    assert (inspect.signature(_rule.RuleBasedLineageSuggester.suggest)
            == inspect.signature(_relay.HttpLineageSuggestionRelay.suggest))


def test_규칙_팔은_세션도_질의도_들지_않는다() -> None:
    """RLS 는 **후보를 고른 자리**가 이미 그었다 — 이 팔은 그 뒤의 순수 계산이다."""
    source = inspect.getsource(_rule)
    for forbidden in ("sqlalchemy", "Session", "select(", "d3_catalog"):
        assert forbidden not in source, f"규칙 팔이 DB 에 닿는다: {forbidden}"


def test_규칙_팔은_계약의_required_를_다_채운다() -> None:
    import yaml
    repo = pathlib.Path(__file__).resolve().parents[3]
    schemas = yaml.safe_load(
        (repo / "contracts" / "seams" / "core-ai.yaml").read_text("utf-8")
    )["components"]["schemas"]
    base = set(schemas["AiSuggestionBase"]["required"])
    parent = set(schemas["ParentCandidateSuggestion"]["allOf"][1]["required"])
    evidence_keys = set(schemas["ParentCandidateSuggestion"]["allOf"][1]["properties"]
                        ["evidence"]["items"]["properties"])
    candidates, axes = _case(_pair(1, **{**_CRS, **_GRID}))
    body = _suggest(candidates, axes)
    assert set(schemas["LineageSuggestionResponse"]["allOf"][1]["required"]) <= set(body)
    suggestion = body["suggestions"][0]
    assert (base | parent) <= set(suggestion)
    assert suggestion["kind"] == _relay.PARENT_SUGGESTION_KIND
    assert all(set(item) == evidence_keys for item in suggestion["evidence"])


# ═══════════════════════════ 팔 고르기 스위치 ═══════════════════════════════
def test_기본_팔은_모델이라_기존_동작이_그대로다() -> None:
    assert _rule.LINEAGE_SUGGESTER_ARM == _rule.ARM_MODEL
    assert isinstance(_rule.build_lineage_suggester(None), _relay.HttpLineageSuggestionRelay)


@pytest.mark.parametrize("value", ["rule", "both", "", "MODEL", "규칙", None])
def test_모르는_값은_기본_팔로_떨어진다(value) -> None:
    """`config.py` 선례 — **오타가 새 동작을 켜지 않는다.**"""
    assert isinstance(_rule.build_lineage_suggester(None, arm=value),
                      _relay.HttpLineageSuggestionRelay)


def test_rules_를_고르면_규칙_팔이_선다() -> None:
    assert isinstance(_rule.build_lineage_suggester(None, arm=_rule.ARM_RULES),
                      _rule.RuleBasedLineageSuggester)


def test_조립_루트가_이_고르는_자리를_지난다() -> None:
    """스위치가 **코드에 있는데 아무도 안 부르는** 자리가 되지 않게 한다."""
    from colab_core.app import main as _main
    assert "build_lineage_suggester" in inspect.getsource(_main.create_app)
