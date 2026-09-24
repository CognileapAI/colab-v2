"""`listUploadLineageSuggestions` — 중계, 그리고 **정직한 빈 상태**.

`ai-service` 가 지금 비어 있으므로 이 op 이 낼 수 있는 참인 답은 **0건**이다.
그것을 200 + `degraded: true` + 빈 배열로 말한다 (`P2.md §2-8`).

**억지 제안을 만들지 않는다.** 그리고 5xx 로 끝내지도 않는다 —
`AI 없이도 v2 는 완결된 제품이다` (`CLAUDE.md §3`). AI 가 없다는 사실이
「업로드를 못 한다」가 되면 그 성질을 잃는다.
"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from conftest import ACC_A_RES, DS_A1, DS_A2, DS_B1, LAB_A, TOKEN_RES, auth
from test_dataset_registration import make_upload

from colab_core.app.main import API_PREFIX


#: ⭑ **⟨K3 `WU-S1b` 2026-09-24⟩ 가공 단계를 안 고르면 모델을 부르지 않는다**(Ted 판정 ③ ·
#: 라운드 `WU-S1` Q2a). 그래서 아래 시험들은 「사람이 골랐다」를 **명시한다** — 안 고른 자리의
#: 응답은 이 파일의 `test_가공_단계를_안_고르면...` 이 따로 재는 **다른 사실**이다.
#: `Lv1` 인 이유: 시드의 후보(DSA1 파생 0 · DSA2 파생 1)가 둘 다 적격으로 남아 종전 오라클이
#: 그대로 선다. 적격 필터 자체는 도메인 시험이 잰다.
DEFAULT_USER_SET_LEVEL = "Lv1"


def _get(client, upload_id, *, processingLevelUserSet=DEFAULT_USER_SET_LEVEL, **params):
    if processingLevelUserSet is not None:
        params["processingLevelUserSet"] = processingLevelUserSet
    return client.get(f"{API_PREFIX}/uploads/{upload_id}/lineage-suggestions",
                      params=params, headers=auth(TOKEN_RES))


# ═════════════════════ ai-service 가 없을 때 (지금) ═════════════════════════
def test_with_no_ai_service_the_answer_is_zero_suggestions_not_an_error(p2_client) -> None:
    client = p2_client(ai_base_url=None)
    receipt = make_upload(client)
    r = _get(client, receipt["uploadId"])
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["suggestions"] == []
    assert body["degraded"] is True
    assert body["degradedReason"], "무엇이 없어서 0건인지 한 줄로 말해야 한다."


def test_the_searched_scope_comes_before_the_suggestions(p2_client) -> None:
    """**먼저 밝히는 범위** — 무엇을 근거로 삼았는지를 제안보다 앞에 둔다
    (`CLAUDE.md §3` · `AiSearchScope`). 0건이어도 어디를 찾았는지 말한다."""
    client = p2_client(ai_base_url=None)
    receipt = make_upload(client)
    scope = _get(client, receipt["uploadId"]).json()["scope"]
    assert scope["labId"] == LAB_A
    assert scope["labName"] == "A 연구실"
    # **연구실 경계 안에서 센다** — 시드의 3건 중 A 연구실 것은 둘이다(DSB1 은 B 것).
    # 범위 셈이 경계를 넘으면 「뒤진 범위」가 남의 연구실을 포함했다고 말하게 된다.
    assert scope["searchedCount"] == 2, "A 연구실의 데이터셋 2건을 뒤진 범위로 밝혀야 한다."


def test_no_confidence_percentage_field_exists_anywhere(p2_client) -> None:
    """확신도는 `확실|애매|모름` **enum** 이고 **숫자·퍼센트 필드가 없다** (`CLAUDE.md §3`)."""
    client = p2_client(ai_base_url=None)
    receipt = make_upload(client)
    body = json.dumps(_get(client, receipt["uploadId"]).json(), ensure_ascii=False)
    for forbidden in ("score", "confidencePercent", "probability", "%"):
        assert forbidden not in body


def test_a_missing_or_expired_upload_is_404(p2_client, sql) -> None:
    client = p2_client(ttl_hours=1, ai_base_url=None)
    receipt = make_upload(client)
    sql("UPDATE d5_upload SET created_at = created_at - interval '2 hours',"
        "                     expires_at = expires_at - interval '2 hours' WHERE id = :u",
        {"u": receipt["uploadId"]})
    assert _get(client, receipt["uploadId"]).status_code == 404


# ═════════════════════ ai-service 가 생겼을 때 (중계) ═══════════════════════
class _FakeAi(BaseHTTPRequestHandler):
    payload: dict = {}
    status: int = 200

    def do_POST(self) -> None:                                    # noqa: N802
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        raw = json.dumps(_FakeAi.payload).encode()
        self.send_response(_FakeAi.status)
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
    yield f"http://127.0.0.1:{server.server_port}", _FakeAi
    server.shutdown()
    server.server_close()


def test_a_real_answer_is_relayed_without_reshaping(p2_client, fake_ai) -> None:
    """스키마는 중계라 **재선언하지 않는다** — `core-ai.yaml` 정의를 그대로 지난다."""
    base, fake = fake_ai
    fake.status = 200
    fake.payload = {
        "degraded": False,
        "scope": {"labId": LAB_A, "labName": "A 연구실", "searchedCount": 3},
        "rawDataLikely": False,
        "suggestions": [{"suggestionId": "01ARZ3NDEKTSV4RRFFQ69G5FAV", "kind": "가공 전 데이터",
                         "confidence": "애매", "rationale": "이름이 비슷하다"}],
    }
    client = p2_client(ai_base_url=base)
    receipt = make_upload(client)
    body = _get(client, receipt["uploadId"]).json()
    assert body == fake.payload
    assert body["suggestions"][0]["confidence"] in ("확실", "애매", "모름")


def test_an_answer_from_another_lab_is_thrown_away(p2_client, fake_ai) -> None:
    """**요청의 범위와 다르면 응답을 버린다** (`core-ai.yaml LineageSuggestionResponse.scope`).

    버린 자리를 5xx 가 아니라 **0건**으로 메운다 — 화면은 계속 그려져야 한다.
    """
    base, fake = fake_ai
    fake.status = 200
    fake.payload = {
        "degraded": False,
        "scope": {"labId": "0000000000000000000000000B", "labName": "B 연구실",
                  "searchedCount": 9},
        "rawDataLikely": True,
        "suggestions": [{"suggestionId": "01ARZ3NDEKTSV4RRFFQ69G5FAV", "kind": "가공 전 데이터",
                         "confidence": "확실", "rationale": "남의 연구실 근거"}],
    }
    client = p2_client(ai_base_url=base)
    receipt = make_upload(client)
    body = _get(client, receipt["uploadId"]).json()
    assert body["suggestions"] == []
    assert body["degraded"] is True
    assert body["scope"]["labId"] == LAB_A


def test_an_ai_failure_degrades_instead_of_breaking_the_upload_screen(p2_client, fake_ai) -> None:
    base, fake = fake_ai
    fake.status = 500
    fake.payload = {"code": "INTERNAL", "message": "터졌다"}
    client = p2_client(ai_base_url=base)
    receipt = make_upload(client)
    r = _get(client, receipt["uploadId"])
    assert r.status_code == 200, "AI 장애가 제품을 멈췄다."
    assert r.json()["suggestions"] == []
    assert r.json()["degraded"] is True


# ═══════ 0건의 두 뜻을 가른다 (`PLAN-SoT §9 〈211〉`-㉮ 음성 판정) ═══════════
#
# ⚠ **제안 기능은 데이터가 없으면 무엇이든 0건이라 음성 테스트가 공짜로 통과한다.**
# 「제안하지 않았다」가 값어치를 가지려면 **제안이 가능했던 자리에서 하지 않은 것**이어야 한다.
# 그래서 아래 둘을 픽스처로 갈라 둔다 — 응답만 보고도 구별되어야 한다.
#
#   ㈏ searched-none    뒤질 대상이 **있었고**, 서비스가 **답했고**, 0건이 **참인 답**이다.
#                       → `degraded: false` · `scope.searchedCount > 0` · `suggestions: []`
#   ㈎ nothing-to-search 뒤질 대상이 **0건**이었다. 제안이 가능했던 적이 없다.
#                       → `scope.searchedCount == 0`
#   ㈐ not-asked        물어보지 못했다. 「없다」가 아니라 **모른다**다.
#                       → `degraded: true` + `degradedReason`


def test_a_live_service_that_searched_real_candidates_and_returned_none(
        p2_client, fake_ai) -> None:
    """㈏ **제안이 가능했으나 하지 않았다** — 이 자리가 음성 판정의 본체다.

    ai-service 가 살아 있고, 연구실 안에 뒤질 데이터셋이 실재하고(2건), 그 서비스가
    **0건을 참인 답으로** 돌려준다. 억지 제안이 만들어지지 않았음이 여기서 증명된다.
    """
    base, fake = fake_ai
    fake.status = 200
    fake.payload = {
        "degraded": False,
        "scope": {"labId": LAB_A, "labName": "A 연구실", "searchedCount": 2},
        "rawDataLikely": False,
        "suggestions": [],
    }
    client = p2_client(ai_base_url=base)
    receipt = make_upload(client)
    body = _get(client, receipt["uploadId"]).json()
    assert body["suggestions"] == []
    # **`degraded` 가 거짓이어야 한다** — 참이면 「못 물어봤다」가 되어 음성 판정이 아니다.
    assert body["degraded"] is False, "물어보지 못한 것을 「제안 안 함」으로 세면 안 된다."
    # **뒤진 대상이 0 이 아니어야 한다** — 0 이면 애초에 제안이 가능하지 않았다.
    assert body["scope"]["searchedCount"] > 0, "뒤질 대상이 없으면 음성 판정이 공짜다."
    assert "degradedReason" not in body or not body.get("degradedReason")


def test_a_scope_with_no_candidates_is_not_the_same_as_searched_and_found_none(
        p2_client, fake_ai, monkeypatch) -> None:
    """㈎ **뒤질 대상이 0건** — 「찾지 못했다」가 아니라 「살펴볼 것이 없었다」다.

    두 응답이 **같은 모양이면 화면이 구별할 수 없다.** 여기서 갈리는 값은 `scope.searchedCount`.
    """
    from colab_core.app.routes import ingestion as _ing
    monkeypatch.setattr(_ing.d3_catalog, "count_datasets", lambda db: 0)

    base, fake = fake_ai
    fake.status = 200
    fake.payload = {
        "degraded": False,
        "scope": {"labId": LAB_A, "labName": "A 연구실", "searchedCount": 0},
        "rawDataLikely": False,
        "suggestions": [],
    }
    client = p2_client(ai_base_url=base)
    receipt = make_upload(client)
    body = _get(client, receipt["uploadId"]).json()
    assert body["suggestions"] == []
    assert body["scope"]["searchedCount"] == 0


def test_the_three_zero_states_are_distinguishable_from_the_response_alone(
        p2_client, fake_ai, monkeypatch) -> None:
    """세 0건이 **응답만으로** 갈린다 — 갈리지 않으면 화면은 거짓말밖에 못 한다.

    ⚠ 이 시험이 이 항목의 green-by-skip 방지다. 위 셋을 따로 통과시켜도 셋이 **같은 값**이면
    「제안하지 않았다」는 아무것도 증명하지 않는다.
    """
    def kind(body: dict) -> str:
        if body["degraded"]:
            return "not-asked"
        return "nothing-to-search" if body["scope"]["searchedCount"] == 0 else "searched-none"

    base, fake = fake_ai
    fake.status = 200

    # ㈏ 살펴봤고 0건이 참이다
    fake.payload = {"degraded": False,
                    "scope": {"labId": LAB_A, "labName": "A 연구실", "searchedCount": 2},
                    "rawDataLikely": False, "suggestions": []}
    c = p2_client(ai_base_url=base)
    searched_none = _get(c, make_upload(c)["uploadId"]).json()

    # ㈐ 물어보지 못했다
    c2 = p2_client(ai_base_url=None)
    not_asked = _get(c2, make_upload(c2)["uploadId"]).json()

    # ㈎ 뒤질 대상이 0건
    from colab_core.app.routes import ingestion as _ing
    monkeypatch.setattr(_ing.d3_catalog, "count_datasets", lambda db: 0)
    fake.payload = {"degraded": False,
                    "scope": {"labId": LAB_A, "labName": "A 연구실", "searchedCount": 0},
                    "rawDataLikely": False, "suggestions": []}
    c3 = p2_client(ai_base_url=base)
    nothing_to_search = _get(c3, make_upload(c3)["uploadId"]).json()

    assert all(b["suggestions"] == [] for b in (searched_none, not_asked, nothing_to_search))
    kinds = {kind(searched_none), kind(not_asked), kind(nothing_to_search)}
    assert kinds == {"searched-none", "not-asked", "nothing-to-search"}, (
        f"세 0건이 응답에서 갈리지 않는다: {kinds}")


# ═══════ 나가는 요청이 계약과 같은 모양인가 (`core-ai.yaml` 이 오라클) ═══════
#
# ⚠ **여기가 지금까지 검사 대상이 없던 자리다.** 위의 `_FakeAi` 는 본문을 읽어 **버리고**
# 고정 응답만 냈다. 그래서 중계가 계약과 다른 모양을 보내도 어떤 시험도 red 를 내지 않았고,
# 계약 게이트는 정적 스펙만 보므로 실제 요청 바이트를 보지 않는다.
# **동결된 계약(2026-08-22)이 먼저이고 중계(2026-08-23)가 그 뒤에 다른 모양으로 섰다** —
# 그러므로 정본은 계약이고, 고치는 쪽은 중계다.

_SEEN: list[dict] = []


class _RecordingAi(_FakeAi):
    def do_POST(self) -> None:                                    # noqa: N802
        raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        _SEEN.append(json.loads(raw.decode()))
        out = json.dumps(_FakeAi.payload).encode()
        self.send_response(_FakeAi.status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)


@pytest.fixture()
def recording_ai():
    _SEEN.clear()
    server = HTTPServer(("127.0.0.1", 0), _RecordingAi)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    _FakeAi.status = 200
    _FakeAi.payload = {"degraded": False,
                       "scope": {"labId": LAB_A, "labName": "A 연구실", "searchedCount": 2},
                       "rawDataLikely": False, "suggestions": []}
    yield f"http://127.0.0.1:{server.server_port}", _SEEN
    server.shutdown()
    server.server_close()


def _contract_schemas():
    import pathlib

    import yaml
    repo = pathlib.Path(__file__).resolve().parents[3]
    spec = yaml.safe_load((repo / "contracts" / "seams" / "core-ai.yaml").read_text("utf-8"))
    return spec["components"]["schemas"]


def test_나가는_요청에_계약의_required_가_다_있다(p2_client, recording_ai) -> None:
    base, seen = recording_ai
    client = p2_client(ai_base_url=base)
    _get(client, make_upload(client)["uploadId"])
    assert seen, "요청이 나가지 않았다."
    schemas = _contract_schemas()
    required = set(schemas["LineageSuggestionRequest"]["required"])
    missing = required - set(seen[0])
    assert not missing, f"계약의 required 가 요청에 없다: {missing}"


def test_나가는_요청에_계약에_없는_열쇠가_없다(p2_client, recording_ai) -> None:
    """`additionalProperties: false` — 계약 밖 열쇠는 명시적 위반이다."""
    base, seen = recording_ai
    client = p2_client(ai_base_url=base)
    _get(client, make_upload(client)["uploadId"])
    schemas = _contract_schemas()
    allowed = set(schemas["LineageSuggestionRequest"]["properties"])
    extra = set(seen[0]) - allowed
    assert not extra, f"계약에 없는 열쇠를 보낸다: {extra}"
    file_allowed = set(schemas["UploadedFileMeta"]["properties"])
    file_extra = set(seen[0]["file"]) - file_allowed
    assert not file_extra, f"file 에 계약에 없는 열쇠를 보낸다: {file_extra}"


def test_파일_메타는_원장에_실재하는_값만_싣는다(p2_client, recording_ai) -> None:
    """**헤더를 못 읽은 항목은 생략한다** — 빈 문자열로 채우면 「못 읽음」과 「값 없음」이
    갈리지 않는다 (계약 `UploadedFileMeta` 산문). 지어낸 값이 실리면 red 다."""
    base, seen = recording_ai
    client = p2_client(ai_base_url=base)
    receipt = make_upload(client)
    _get(client, receipt["uploadId"])
    meta = seen[0]["file"]
    assert meta["fileName"], "묶음 이름이 없으면 제안의 근거가 없다"
    assert meta["kind"] in ("본체", "기준 격자 파일")
    for key, value in meta.items():
        assert value not in ("", [], None), f"{key} 를 빈 값으로 채웠다 — 생략해야 한다"


def test_소비자와_생산자가_같은_계약_한_벌을_본다(p2_client, recording_ai) -> None:
    """**두 시험이 각자 green 인데 서로 못 말하는 상태를 막는 자리다.**

    ⚠ 배포 단위를 import 해서 맞대지 않는다 — 그 순간 다섯 단위가 한 단위가 된다
    (`gates/config/importlinter.ini` units-independent). 대신 **동결된 계약 한 벌**을
    양쪽이 각자 오라클로 쓴다: 여기서는 나가는 요청을, ai-service 쪽
    `tests/test_http_suggestions.py` 에서는 들어오는 요청을 같은 yaml 로 대조한다.
    """
    base, seen = recording_ai
    client = p2_client(ai_base_url=base)
    _get(client, make_upload(client)["uploadId"])
    schemas = _contract_schemas()
    req, meta = schemas["LineageSuggestionRequest"], schemas["UploadedFileMeta"]
    assert req["additionalProperties"] is False and meta["additionalProperties"] is False
    body = seen[0]
    assert set(req["required"]) <= set(body)
    assert set(body) <= set(req["properties"])
    assert set(meta["required"]) <= set(body["file"])
    assert set(body["file"]) <= set(meta["properties"])


# ═════════ 후보를 골라 실어 보낸다 · 후보 밖 ID 를 버린다 (K3 `WU1b`) ═════════
#
# ⚠ **여기까지 오기 전에는 요청이 「무엇을 살펴볼지」를 말하지 않았다.** 생산자는 카탈로그에
# 닿지 못하므로(`CLAUDE.md §3-1`) 후보를 못 받으면 낼 수 있는 참인 답이 언제나 0건이다.
# 후보를 고르는 것은 D3 의 주인인 core-api 이고(`〈72〉-㉮` 검색과 같은 분담), 고른 모집단은
# 사람이 고르는 후보(`listLineageCandidates`)와 **같아야 한다** — `select_lineage_candidates`
# 한 함수만 부르는 이유다. 되받은 제안 중 **보낸 후보 밖의 부모**를 실은 것은 버린다.

#: ⚠ ULID 알파벳에는 `I`·`L`·`O`·`U` 가 없다 — `DSLNG1` 은 도메인 CHECK 에 걸린다.
_SUMMARY_SEED = "00000000000000000000DSSMR1"
_BARE_SEED = "00000000000000000000DSBAR1"
_VEG_SEED = "00000000000000000000DSVEG1"
TOPIC_VEG = "식생·NDVI"


def _seed_dataset(sql, dataset_id, *, name, topic=None, summary="시험 자료",
                  source_label=None, modified="2026-03-01T00:00:00Z",
                  lab=LAB_A, account=ACC_A_RES) -> None:
    """후보 모집단에 한 건을 더한다. **시드 3건(DSA1·DSA2·DSB1)은 고치지 않는다** —
    시드를 흔들면 다른 시험의 개수 오라클이 함께 흔들린다."""
    sql("""INSERT INTO d3_dataset(id, lab_id, owner_account_id, uploader_account_id,
                                  source_label, uploaded_at, last_modified_at)
           VALUES(:id, :lab, :account, :account, :source, :modified, :modified)""",
        {"id": dataset_id, "lab": lab, "account": account,
         "source": source_label, "modified": modified},
        account_id=account, lab_id=lab)
    sql("""INSERT INTO d3_dataset_description(dataset_id, lab_id, name, topic, summary)
           VALUES(:id, :lab, :name, :topic, :summary)""",
        {"id": dataset_id, "lab": lab, "name": name, "topic": topic, "summary": summary},
        account_id=account, lab_id=lab)


def _sent_candidates(seen) -> list[dict]:
    assert seen, "요청이 나가지 않았다."
    assert "candidates" in seen[0], "후보를 싣지 않으면 생산자가 낼 수 있는 답은 언제나 0건이다."
    return seen[0]["candidates"]


def _by_id(candidates) -> dict[str, dict]:
    return {c["datasetId"]: c for c in candidates}


def test_나가는_요청의_후보가_계약_열쇠_집합_안이다(p2_client, recording_ai) -> None:
    """`LineageParentCandidate` 가 오라클이다 — `additionalProperties: false` 이므로
    계약 밖 열쇠는 명시적 위반이고, `required` 둘은 언제나 있어야 한다."""
    base, seen = recording_ai
    client = p2_client(ai_base_url=base)
    _get(client, make_upload(client)["uploadId"])
    schema = _contract_schemas()["LineageParentCandidate"]
    allowed, required = set(schema["properties"]), set(schema["required"])
    candidates = _sent_candidates(seen)
    assert candidates, "연구실에 데이터셋이 2건 있는데 후보가 0건이다."
    for candidate in candidates:
        extra = set(candidate) - allowed
        assert not extra, f"계약에 없는 열쇠를 후보에 실었다: {extra}"
        assert required <= set(candidate), f"후보의 required 가 없다: {required - set(candidate)}"
        for key, value in candidate.items():
            assert value not in ("", [], None), f"{key} 를 빈 값으로 채웠다 — 생략해야 한다"


def test_후보에_다른_연구실_데이터셋은_없다(p2_client, recording_ai) -> None:
    """경계는 세션의 RLS 가 긋는다 — 후보 선정이 그 경계를 넘으면 남의 연구실 이름·설명이
    모델 입력으로 나간다. 여기가 그 유일한 직접 측정이다."""
    base, seen = recording_ai
    client = p2_client(ai_base_url=base)
    _get(client, make_upload(client)["uploadId"])
    ids = set(_by_id(_sent_candidates(seen)))
    assert DS_B1 not in ids, "B 연구실 데이터셋이 후보로 나갔다."
    assert {DS_A1, DS_A2} <= ids


def test_후보의_가공단계는_판정된_것만_싣는다(p2_client, recording_ai, sql) -> None:
    """**미지와 Lv0 은 다른 사실이다.** 판정이 없는 후보에 `0`·`null` 을 실으면
    「원자료다」로 읽힌다(계약 `processingLevel` 산문)."""
    _seed_dataset(sql, _BARE_SEED, name="판정 없는 자료", source_label=None)
    base, seen = recording_ai
    client = p2_client(ai_base_url=base)
    _get(client, make_upload(client)["uploadId"])
    sent = _by_id(_sent_candidates(seen))
    assert _BARE_SEED in sent, "새로 넣은 후보가 모집단에 없다."
    assert "processingLevel" not in sent[_BARE_SEED], \
        "판정이 없는 후보에 가공 단계를 실었다 — 「모른다」가 「Lv0」이 된다."
    # DSA2 는 확정된 부모(DSA1)가 있다 — 판정이 있는 쪽이다.
    assert sent[DS_A2]["processingLevel"] == 1
    for candidate in sent.values():
        assert candidate.get("processingLevel", 0) is not None


def test_후보의_설명과_원천표기를_계약_상한으로_잘라_보낸다(p2_client, recording_ai, sql) -> None:
    """상한은 본문이 부풀지 않게 **계약이** 걸고, 넘치면 core-api 가 잘라 보낸다
    (`LineageParentCandidate.summary` 산문). D3 의 저장값에는 상한이 없다."""
    long_summary, long_label = "가" * 300, "나" * 80
    _seed_dataset(sql, _SUMMARY_SEED, name="긴 설명 자료",
                  summary=long_summary, source_label=long_label)
    base, seen = recording_ai
    client = p2_client(ai_base_url=base)
    _get(client, make_upload(client)["uploadId"])
    schema = _contract_schemas()["LineageParentCandidate"]["properties"]
    sent = _by_id(_sent_candidates(seen))[_SUMMARY_SEED]
    assert len(sent["summary"]) == schema["summary"]["maxLength"]
    assert long_summary.startswith(sent["summary"])
    assert len(sent["sourceLabel"]) == schema["sourceLabel"]["maxLength"]
    assert long_label.startswith(sent["sourceLabel"])


def test_후보는_계약_상한_건수를_넘지_않는다(p2_client, recording_ai, sql) -> None:
    """상한 k=20 — 계약 `maxItems` 와 같은 값이다(미해결 질문 ④ · Ted 결정 ⑥)."""
    sql("""INSERT INTO d3_dataset(id, lab_id, owner_account_id, uploader_account_id,
                                  uploaded_at, last_modified_at)
           SELECT '0000000000000000000000DS' || to_char(n, 'FM00'), :lab, :acc, :acc,
                  CAST(:modified AS timestamptz), CAST(:modified AS timestamptz)
             FROM generate_series(1, 21) AS n""",
        {"lab": LAB_A, "acc": ACC_A_RES, "modified": "2026-04-01T00:00:00Z"})
    sql("""INSERT INTO d3_dataset_description(dataset_id, lab_id, name, summary)
           SELECT '0000000000000000000000DS' || to_char(n, 'FM00'), :lab,
                  '다수 후보 ' || n, '시험 자료'
             FROM generate_series(1, 21) AS n""",
        {"lab": LAB_A})
    base, seen = recording_ai
    client = p2_client(ai_base_url=base)
    _get(client, make_upload(client)["uploadId"])
    cap = _contract_schemas()["LineageSuggestionRequest"]["properties"]["candidates"]["maxItems"]
    assert len(_sent_candidates(seen)) == cap, "후보 상한을 넘겨 실었다."


def test_주제를_고른_업로드는_그_주제의_후보만_받는다(p2_client, recording_ai, sql) -> None:
    """후보 전략의 **잠정 기본값은 `filtered`** 다(Ted 결정 ① 2026-09-24 · J1 근거).
    환경변수로 갈아끼우는 자리를 두지 않는다 — 기본값이 측정 없이 흔들리는 자리가 된다."""
    from colab_core.app.routes import ingestion as _ing
    from colab_core.domains import d3_catalog as _d3

    assert _ing.LINEAGE_CANDIDATE_STRATEGY == _d3.FILTERED_CANDIDATES

    _seed_dataset(sql, _VEG_SEED, name="A 식생 NDVI 월평균", topic=TOPIC_VEG,
                  source_label="국립기상과학원")
    base, seen = recording_ai
    client = p2_client(ai_base_url=base)
    _get(client, make_upload(client)["uploadId"], subject=TOPIC_VEG)
    assert list(_by_id(_sent_candidates(seen))) == [_VEG_SEED], \
        "주제를 고른 업로드가 모집단 전체를 받았다 — 필터가 배선되지 않았다."


# ─── 자식 자신은 요청에 실리지 않는다 (Ted 결정 ⑦ · intent 「판정 기록 2회차」 7) ───
#
# luna 실측 J5 에서 억지 선택 6건 중 5건이 **자식 자신**이었다. 같은 자료가 이미 등록돼
# 있으면 그 데이터셋이 후보에 서고, 모델에게는 후보 밖 ID 가 아니라 **오답**으로 보인다.
# 빼는 조건은 이름 초안과 파일명이 **둘 다** 같을 때뿐이다(`d3_catalog` 의 같은 이름 절).
_TWIN_SEED = "00000000000000000000DSTWN1"
_TWIN_NAME = "A 강우 재적재 표본"
_TWIN_FILE = "twin_sample.npy"


def _seed_body_file(sql, dataset_id, file_id, *, file_name) -> None:
    sql("""INSERT INTO d3_file (id, lab_id, dataset_id, kind, file_name,
                                size_bytes, storage_key)
           VALUES (:id, :lab, :dataset, '본체', :file_name, 7, :key)""",
        {"id": file_id, "lab": LAB_A, "dataset": dataset_id,
         "file_name": file_name, "key": f"k/{file_id}"})


def test_이름과_파일명이_둘_다_같은_데이터셋은_후보로_나가지_않는다(
        p2_client, recording_ai, sql) -> None:
    """**중계까지 배선됐는가**가 이 시험의 전부다 — 도메인 단위 시험은
    `test_lineage_candidate_selection.py` 의 같은 이름 절이 따로 본다."""
    from test_uploads import one_body

    _seed_dataset(sql, _TWIN_SEED, name=_TWIN_NAME, topic="강우·강수",
                  source_label="기상청", modified="2026-05-01T00:00:00Z")
    _seed_body_file(sql, _TWIN_SEED, "00000000000000000000000FT1", file_name=_TWIN_FILE)
    base, seen = recording_ai
    client = p2_client(ai_base_url=base)
    receipt = make_upload(client, files=one_body(_TWIN_FILE))
    _get(client, receipt["uploadId"], datasetNameDraft=_TWIN_NAME)
    sent = _by_id(_sent_candidates(seen))
    assert _TWIN_SEED not in sent, "업로드와 이름·파일명이 둘 다 같은 데이터셋을 후보로 실었다."
    assert DS_A1 in sent, "자기 자신을 빼면서 남의 후보까지 지웠다."


def test_이름만_같은_다른_판본은_후보로_그대로_나간다(
        p2_client, recording_ai, sql) -> None:
    from test_uploads import one_body

    _seed_dataset(sql, _TWIN_SEED, name=_TWIN_NAME, topic="강우·강수",
                  source_label="기상청", modified="2026-05-01T00:00:00Z")
    _seed_body_file(sql, _TWIN_SEED, "00000000000000000000000FT1", file_name=_TWIN_FILE)
    base, seen = recording_ai
    client = p2_client(ai_base_url=base)
    receipt = make_upload(client, files=one_body("다른_표본.npy"))
    _get(client, receipt["uploadId"], datasetNameDraft=_TWIN_NAME)
    assert _TWIN_SEED in _by_id(_sent_candidates(seen)), \
        "이름만 같은 다른 판본을 뺐다 — 사람이 고를 수 있는 부모가 사라진다."


def test_후보가_0건이면_후보를_싣지_않고_응답은_여전히_200_0건이다(
        p2_client, recording_ai, monkeypatch) -> None:
    """빈 연구실의 첫 업로드는 **정상 응답**이다 — 5xx 로 끝내지 않는다."""
    from colab_core.app.routes import ingestion as _ing

    calls: list[dict] = []

    def _none(session, **kwargs):
        calls.append(kwargs)
        return []

    monkeypatch.setattr(_ing.d3_catalog, "select_lineage_candidates", _none)
    base, seen = recording_ai
    client = p2_client(ai_base_url=base)
    r = _get(client, make_upload(client)["uploadId"])
    assert len(calls) == 1, "후보 선정을 부르지 않았다 — 모집단이 두 벌이 되는 자리다."
    assert r.status_code == 200, r.text
    assert r.json()["suggestions"] == []
    assert seen and seen[0].get("candidates", []) == [], \
        "후보가 0건인데 빈 배열도 생략도 아닌 값을 실었다."


def test_후보_밖_ID_를_실은_제안은_버려지고_나머지는_남는다(
        p2_client, recording_ai, caplog) -> None:
    """**신뢰하지 않는 쪽에서 거른다** — 응답 `scope` 를 버리는 그 자리와 같은 규율이다
    (`〈72〉-㉮`). 한 건이 후보 밖이라고 응답 전체를 버리지 않는다."""
    import logging as _logging

    from colab_core.app import relay as _relay

    outside = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
    base, seen = recording_ai
    _FakeAi.payload = {
        "degraded": False,
        "scope": {"labId": LAB_A, "labName": "A 연구실", "searchedCount": 2},
        "rawDataLikely": False,
        "suggestions": [
            {"suggestionId": "01ARZ3NDEKTSV4RRFFQ69G5FA0", "kind": "가공 전 데이터",
             "confidence": "애매", "rationale": "이름이 비슷하다",
             "parentDatasetId": DS_A1, "parentDatasetName": "A 강우 원자료",
             "suggestedParentRole": "주입력"},
            {"suggestionId": "01ARZ3NDEKTSV4RRFFQ69G5FA1", "kind": "가공 전 데이터",
             "confidence": "확실", "rationale": "지어낸 부모",
             "parentDatasetId": outside, "parentDatasetName": "없는 데이터셋",
             "suggestedParentRole": "주입력"},
        ],
    }
    client = p2_client(ai_base_url=base)
    with caplog.at_level(_logging.ERROR, logger=_relay.SUGGEST_LOGGER):
        body = _get(client, make_upload(client)["uploadId"]).json()
    assert DS_A1 in {c["datasetId"] for c in _sent_candidates(seen)}
    got = [s["parentDatasetId"] for s in body["suggestions"]]
    assert got == [DS_A1], f"후보 밖 ID 가 응답에 남았거나 나머지까지 버렸다: {got}"
    rejected = [r for r in caplog.records
                if getattr(r, "event", None) == "lineage.suggest.rejected"]
    assert len(rejected) == 1, "버린 사실이 기록에 남지 않았다 — 아무도 건수를 못 센다."
    line = rejected[0].getMessage()
    assert "1" in str(getattr(rejected[0], "reason", "")), "버린 건수가 기록에 없다."
    assert "A 강우 원자료" not in line and "없는 데이터셋" not in line, \
        "기록에 데이터셋 이름을 적었다."


# ═══════════════════ 게이트 ② 판정 2026-09-24 ═══════════════════════════════
def test_가공_방식_제안의_부모도_후보_안이어야_남는다(p2_client, recording_ai) -> None:
    """**부모 ID 가 실리는 자리는 둘이다.**

    「가공 전 데이터」는 `parentDatasetId` 로, 「가공 방식」은 어느 부모와의 관계인지를
    가리키는 `appliesToParentDatasetId` 로 부모를 가리킨다
    (`core-ai.yaml ProcessingMethodSuggestion` 산문 · `DOMAINS §2 D4`). 한쪽만 보면
    나머지 한쪽으로 **후보 밖 ID 가 그대로 화면까지 간다** — 계약 산문 ⓑ 가 막으려던 것이
    문 하나만 잠긴 채 남는다.
    """
    outside = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
    base, seen = recording_ai
    _FakeAi.payload = {
        "degraded": False,
        "scope": {"labId": LAB_A, "labName": "A 연구실", "searchedCount": 2},
        "rawDataLikely": False,
        "suggestions": [
            {"suggestionId": "01ARZ3NDEKTSV4RRFFQ69G5FB0", "kind": "가공 방식",
             "confidence": "애매", "rationale": "격자를 잘라 썼다",
             "methodText": "0.25도 격자로 잘랐다", "appliesToParentDatasetId": DS_A1},
            {"suggestionId": "01ARZ3NDEKTSV4RRFFQ69G5FB1", "kind": "가공 방식",
             "confidence": "확실", "rationale": "지어낸 부모에 붙었다",
             "methodText": "평균을 냈다", "appliesToParentDatasetId": outside},
        ],
    }
    client = p2_client(ai_base_url=base)
    body = _get(client, make_upload(client)["uploadId"]).json()
    assert DS_A1 in {c["datasetId"] for c in _sent_candidates(seen)}
    got = [s.get("appliesToParentDatasetId") for s in body["suggestions"]]
    assert got == [DS_A1], f"후보 밖 부모를 가리킨 가공 방식이 남았거나 나머지까지 버렸다: {got}"


def test_부모를_가리키지_않는_가공_방식은_그대로_남는다(p2_client, recording_ai) -> None:
    """**어느 부모인지 모르면 생략한다**(계약 산문) — 생략을 「후보 밖」으로 읽어 버리면
    참인 답이 사라진다. 버리는 것은 **가리켰는데 후보 밖일 때**뿐이다."""
    base, seen = recording_ai
    _FakeAi.payload = {
        "degraded": False,
        "scope": {"labId": LAB_A, "labName": "A 연구실", "searchedCount": 2},
        "rawDataLikely": False,
        "suggestions": [
            {"suggestionId": "01ARZ3NDEKTSV4RRFFQ69G5FB2", "kind": "가공 방식",
             "confidence": "모름", "rationale": "어느 부모인지는 모른다",
             "methodText": "단위를 바꿨다"},
        ],
    }
    client = p2_client(ai_base_url=base)
    body = _get(client, make_upload(client)["uploadId"]).json()
    assert len(body["suggestions"]) == 1, "부모를 안 가리킨 제안까지 버렸다"


def test_후보의_기간이_나가는_요청에_실린다(p2_client, recording_ai, sql) -> None:
    """기간은 `d3_dataset_autometa` 가 아는 값이고 **근거 한 줄의 재료**다
    (`LineageParentCandidate.periodStart`). 여기서 떨어뜨리면 모델은 기간을 못 보는데
    계약도 게이트도 그 사실을 말하지 않는다 — 왕복의 한쪽 끝을 세는 자리다."""
    sql("""UPDATE d3_dataset_autometa
              SET period_start = CAST('2020-01-01T00:00:00Z' AS timestamptz),
                  period_end   = CAST('2024-12-31T00:00:00Z' AS timestamptz)
            WHERE dataset_id = :d""", {"d": DS_A1})
    base, seen = recording_ai
    client = p2_client(ai_base_url=base)
    _get(client, make_upload(client)["uploadId"])
    sent = _by_id(_sent_candidates(seen))[DS_A1]
    assert sent["periodStart"].startswith("2020-01-01"), sent
    assert sent["periodEnd"].startswith("2024-12-31"), sent


# ═════════ WU-S1b — 가공 단계가 있어야 묻는다 · 원메타 4축을 싣는다 ══════════
#
# **Lv 가 없으면 모델을 부르지 않는다**(라운드 `WU-S1` Q2a · Ted 판정 ③). 기준값이 없으면
# 적격을 가를 수 없고, 적격을 못 가르면 자손이 부모로 제안되는 자리가 그대로 열린다.
# 그때 참인 답은 「제안이 없다」이고, 그것을 **200 + 0건 + 사유 한 줄**로 말한다.


def test_가공_단계를_안_고르면_ai_service_를_부르지_않는다(p2_client, recording_ai) -> None:
    """**요청이 0회다.** 부르고 버리는 것과 안 부르는 것은 다르다 — 토큰도 감시 기록도 다르다."""
    from colab_core.app.routes import ingestion as _ing

    base, seen = recording_ai
    client = p2_client(ai_base_url=base)
    r = _get(client, make_upload(client)["uploadId"], processingLevelUserSet=None)
    assert r.status_code == 200, r.text
    assert seen == [], "가공 단계를 안 골랐는데 모델 쪽으로 요청이 나갔다."
    body = r.json()
    assert body["suggestions"] == []
    assert body["degraded"] is True
    assert body["degradedReason"] == _ing.LEVEL_REQUIRED_REASON


def test_가공_단계_사유는_기존_영_상태_사유와_다른_문장이다(p2_client, recording_ai) -> None:
    """**네 번째 영 상태다.** 기존 셋(㈎ 뒤질 대상 0 · ㈏ 뒤졌고 0건 · ㈐ 못 물어봤다)을
    그대로 두고 옆에 선다 — 사유 문자열이 같으면 화면이 「AI 가 죽었다」와 「네가 아직
    안 골랐다」를 구별하지 못한다. ⚠ 사유 **코드 enum 을 새로 만들지 않는다**: 오늘
    `degradedReason` 을 읽는 FE 소비자가 0건이라, 읽는 쪽이 생기는 회차가 그것을 정한다."""
    from colab_core.app.routes import ingestion as _ing

    base, _ = recording_ai
    client = p2_client(ai_base_url=base)
    not_chosen = _get(client, make_upload(client)["uploadId"],
                      processingLevelUserSet=None).json()
    offline = p2_client(ai_base_url=None)
    not_asked = _get(offline, make_upload(offline)["uploadId"]).json()
    assert not_chosen["degradedReason"] == _ing.LEVEL_REQUIRED_REASON
    assert not_chosen["degradedReason"] != not_asked["degradedReason"], \
        "「안 골랐다」와 「못 물어봤다」가 같은 문장으로 내려간다."
    assert not_chosen["scope"]["labId"] == LAB_A, "사유만 남기고 범위를 잃었다."


@pytest.mark.parametrize("bad", ["Lv9", "1", "lv1", "Lv", ""])
def test_계약_밖_가공_단계_값은_400_이다(p2_client, recording_ai, bad) -> None:
    """표면이 계약을 요구한다 — `fe-core.yaml` 의 enum 은 `Lv0`~`Lv3` 넷뿐이다.
    모르는 값을 조용히 「안 골랐다」로 접으면 오타가 영 상태로 둔갑한다."""
    base, seen = recording_ai
    client = p2_client(ai_base_url=base)
    r = _get(client, make_upload(client)["uploadId"], processingLevelUserSet=bad)
    assert r.status_code == 400, r.text
    assert seen == [], "계약 밖 값인데 모델 쪽으로 요청이 나갔다."


def test_나가는_요청에_사람이_고른_가공_단계가_정수로_실린다(p2_client, recording_ai) -> None:
    """계약 `LineageSuggestionRequest.processingLevel` 은 **정수**다(인라인 0..3).
    문자열→정수 변환 자리는 `d3_catalog.parse_user_set_level` 한 곳뿐이다."""
    base, seen = recording_ai
    client = p2_client(ai_base_url=base)
    _get(client, make_upload(client)["uploadId"], processingLevelUserSet="Lv2")
    assert seen, "요청이 나가지 않았다."
    sent = seen[0]["processingLevel"]
    assert sent == 2 and isinstance(sent, int) and not isinstance(sent, bool), sent
    schema = _contract_schemas()["LineageSuggestionRequest"]["properties"]["processingLevel"]
    assert schema["minimum"] <= sent <= schema["maximum"]


def test_후보의_원메타_네_축은_아는_것만_실린다(p2_client, recording_ai, sql) -> None:
    """⭑ 모델이 근거를 **인용**하려면 대조할 날값이 있어야 한다(계약 `WU-S0` 산문).
    ⚠ **날값만 싣는다** — 겹침·교집합 같은 파생 신호는 싣지 않는다(열린 권고 ① 채택).
    ⚠ **모르는 값은 열쇠를 만들지 않는다** — 자동 메타 행이 아예 없는 후보가 그 자리다."""
    sql("""UPDATE d3_dataset_autometa
              SET grid = '0.25도 정규격자', bundle_file_name = 'a1-body.csv'
            WHERE dataset_id = :d""", {"d": DS_A1})
    _seed_dataset(sql, _BARE_SEED, name="자동 메타가 없는 자료")
    base, seen = recording_ai
    client = p2_client(ai_base_url=base)
    _get(client, make_upload(client)["uploadId"])
    sent = _by_id(_sent_candidates(seen))
    known = sent[DS_A1]
    assert known["crs"] == "EPSG:5179"
    assert known["grid"] == "0.25도 정규격자"
    # 변수 목록의 정본은 `d3_dataset_variable` 이고 트리거가 자동 메타로 옮긴다 — 시드의
    # DSA1 은 세 행(`강우량`·`기온`·`유출량`)이다. 여기서 재는 것은 **날값 그대로**인가다.
    assert known["variables"] == ["강우량", "기온", "유출량"]
    assert known["fileName"] == "a1-body.csv"
    unknown = sent[_BARE_SEED]
    for axis in ("crs", "grid", "variables", "fileName"):
        assert axis not in unknown, f"{axis} 를 모르는데 열쇠를 만들었다 — 미지가 값이 된다"
    # **파생 신호는 나가지 않는다.** 모델이 베껴 돌려주면 인용 검증이 오라클 구실을 못 한다.
    allowed = set(_contract_schemas()["LineageParentCandidate"]["properties"])
    for candidate in sent.values():
        assert set(candidate) <= allowed, f"계약 밖 열쇠: {set(candidate) - allowed}"


def test_원메타_날값은_계약_상한으로_잘라_보낸다(p2_client, recording_ai, sql) -> None:
    """상한은 본문이 부풀지 않게 이쪽에서 건다 — D3 저장값에는 상한이 없다
    (`summary`·`sourceLabel` 과 같은 규율)."""
    sql("""UPDATE d3_dataset_autometa
              SET crs = :long, grid = :long, bundle_file_name = :long,
                  variables = CAST(:vars AS text[])
            WHERE dataset_id = :d""",
        {"d": DS_A1, "long": "가" * 300,
         "vars": "{" + ",".join(f"v{n}" for n in range(60)) + "}"})
    base, seen = recording_ai
    client = p2_client(ai_base_url=base)
    _get(client, make_upload(client)["uploadId"])
    schema = _contract_schemas()["LineageParentCandidate"]["properties"]
    sent = _by_id(_sent_candidates(seen))[DS_A1]
    for axis in ("crs", "grid", "fileName"):
        assert len(sent[axis]) == schema[axis]["maxLength"], axis
    assert len(sent["variables"]) == schema["variables"]["maxItems"]


def test_적격_필터가_라우트까지_배선됐다(p2_client, recording_ai) -> None:
    """도메인 시험이 재는 것은 함수이고, 여기서 재는 것은 **배선**이다.
    DSA2 는 확정된 부모(DSA1)가 있어 파생 Lv1 이라 `Lv0` 업로드의 부모가 될 수 없다."""
    base, seen = recording_ai
    client = p2_client(ai_base_url=base)
    _get(client, make_upload(client)["uploadId"], processingLevelUserSet="Lv0")
    ids = set(_by_id(_sent_candidates(seen)))
    assert DS_A2 not in ids, "Lv0 업로드에 파생 Lv1 후보가 나갔다 — 필터가 배선되지 않았다"
    assert DS_A1 in ids, "같은 단계(Lv0) 후보까지 지웠다"
    assert DS_B1 not in ids, "필터를 걸면서 연구실 경계가 넓어졌다"
