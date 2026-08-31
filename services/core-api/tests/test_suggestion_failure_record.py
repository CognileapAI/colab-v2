"""계보 제안의 **거부·실패가 기록에 남는가** (`03-HANDOFF §5.5 DR-19`-㉯ · `PLAN-SoT §9 〈246〉`).

`DR-19` 가 등재한 것은 두 가지였다. 앞의 하나(중계가 계약과 다른 모양을 보낸다)는
`ccd28c6` 이 닫았다 — 그 자리는 `test_lineage_suggestions.py` 의 「나가는 요청」절이 지킨다.

**남은 하나가 이 파일이다.** 중계는 못 닿음·비200·범위 불일치를 전부
`honest_empty_suggestions` 로 접는데, 그때 **어떤 기록도 남지 않았다.** 화면은
`degraded` 로 「모른다」를 말할 수 있었지만(`〈211〉`), **기계가 긁을 이름이 없어
「지금 몇 건 거부당했나」를 아무도 못 셌다.** 이 세션에서 되풀이된 실패 유형
(입구 없는 200 · 빈 DB 를 본 게이트)과 같은 무늬다.

**갈라야 하는 셋** — 이름이 오라클이다(`catalog.py` 의 `search.unavailable` 과 같은 규약).
  ㈎ 거부   `lineage.suggest.rejected`    — 저쪽이 우리 요청을 물리쳤다. **우리 쪽 고장**이라
                                           재시도로 낫지 않는다. 그래서 `ERROR` 다.
  ㈏ 못 닿음 `lineage.suggest.unavailable` — 저쪽이 없거나 답을 못 했다. `WARNING`.
  ㈐ 빈 상태 **기록 없음**                 — 「살펴봤는데 없다」는 고장이 아니다.
                                           여기에 기록을 남기면 정직한 빈 상태가 오염된다.

⚠ **AI 응답 규격은 깨지 않는다.** 셋 다 응답은 그대로 200 이고 제안은 0건이다 —
억지 제안도 가짜 성공도 만들지 않는다 (`CLAUDE.md §3`).
"""
from __future__ import annotations

import logging

from conftest import LAB_A, TOKEN_RES, auth
from test_dataset_registration import make_upload
from test_lineage_suggestions import fake_ai  # noqa: F401  (픽스처를 다시 짓지 않는다)

from colab_core.app.main import API_PREFIX
from colab_core.app.relay import (SUGGEST_LOGGER, SUGGEST_REJECTED,
                                  SUGGEST_UNAVAILABLE)

_LIVE_EMPTY = {"degraded": False,
               "scope": {"labId": LAB_A, "labName": "A 연구실", "searchedCount": 2},
               "rawDataLikely": False, "suggestions": []}


def _get(client, upload_id, **params):
    return client.get(f"{API_PREFIX}/uploads/{upload_id}/lineage-suggestions",
                      params=params, headers=auth(TOKEN_RES))


def _events(caplog) -> list[str]:
    return [getattr(r, "event", "") for r in caplog.records
            if str(getattr(r, "event", "")).startswith("lineage.suggest.")]


def _run(client, caplog):
    receipt = make_upload(client)
    caplog.clear()
    with caplog.at_level(logging.DEBUG, logger=SUGGEST_LOGGER):
        return _get(client, receipt["uploadId"]).json(), _events(caplog)


def test_형식_오류로_거부되면_빈_상태가_아니라_실패로_드러난다(p2_client, fake_ai, caplog) -> None:
    """**이 항목의 red 본체.** 계약과 다른 모양을 보내 400 을 맞았을 때, 지금까지는
    응답이 정직한 빈 상태와 같아지고 기록이 한 줄도 남지 않아 **고장이 조용히 묻혔다.**"""
    base, fake = fake_ai
    fake.status = 400
    fake.payload = {"code": "bad_request", "message": "계약에 없는 열쇠다"}
    body, events = _run(p2_client(ai_base_url=base), caplog)

    assert body["suggestions"] == [], "거부를 억지 제안으로 메우지 않는다."
    assert body["degraded"] is True
    assert "lineage.suggest.rejected" in events, "거부가 기록에 이름으로 서지 않는다."

    hit = [r for r in caplog.records if getattr(r, "event", None) == "lineage.suggest.rejected"]
    assert hit[0].levelno >= logging.ERROR, "우리 요청이 물리쳐진 것은 경고가 아니라 오류다."
    assert getattr(hit[0], "code", None) == SUGGEST_REJECTED
    assert getattr(hit[0], "status", None) == 400
    assert getattr(hit[0], "labId", None) == LAB_A


def test_못_닿은_것과_거부당한_것이_기록에서_갈린다(p2_client, fake_ai, caplog) -> None:
    """둘 다 화면에는 「모른다」로 뜨지만 **고칠 사람과 고칠 방법이 다르다.**"""
    base, fake = fake_ai
    fake.status = 503
    fake.payload = {"code": "unavailable", "message": "터졌다"}
    _, down = _run(p2_client(ai_base_url=base), caplog)

    fake.status = 422
    fake.payload = {"code": "bad_request", "message": "file 이 없다"}
    _, refused = _run(p2_client(ai_base_url=base), caplog)

    assert down == ["lineage.suggest.unavailable"]
    assert refused == ["lineage.suggest.rejected"]
    assert set(down).isdisjoint(refused), "거부와 장애가 같은 이름으로 서면 세지 못한다."


def test_정직한_빈_상태에는_실패_기록이_남지_않는다(p2_client, fake_ai, caplog) -> None:
    """㈐ **「살펴봤는데 없다」는 고장이 아니다.** 여기에 기록이 서면 거부와 빈 상태가
    기록에서 다시 붙어 버리고, 감시가 매 업로드마다 울어 아무도 안 보게 된다."""
    base, fake = fake_ai
    fake.status = 200
    fake.payload = dict(_LIVE_EMPTY)
    body, events = _run(p2_client(ai_base_url=base), caplog)

    assert body["degraded"] is False and body["suggestions"] == []
    assert events == [], f"빈 상태가 실패로 기록됐다: {events}"


def test_아직_연결되지_않은_것은_거부가_아니다(p2_client, caplog) -> None:
    """주소가 없는 것은 **결정된 상태**다(`K3` 는 아직 stage 3 이다). 고장으로 세면
    「AI 없이도 v2 는 완결된 제품」이 매 업로드마다 오류 한 줄을 낸다."""
    body, events = _run(p2_client(ai_base_url=None), caplog)
    assert body["degraded"] is True and body["suggestions"] == []
    assert "lineage.suggest.rejected" not in events


def test_남의_연구실_범위로_답한_것은_거부로_기록된다(p2_client, fake_ai, caplog) -> None:
    """버린 응답도 **버렸다는 사실이 남아야 한다** — 지금은 화면에서 0건과 구별되지만
    기록이 없어 「몇 번 버렸나」를 못 센다. 경계 위반이므로 `ERROR` 다."""
    base, fake = fake_ai
    fake.status = 200
    fake.payload = {"degraded": False,
                    "scope": {"labId": "0000000000000000000000000B", "labName": "B 연구실",
                              "searchedCount": 9},
                    "rawDataLikely": False, "suggestions": []}
    body, events = _run(p2_client(ai_base_url=base), caplog)
    assert body["scope"]["labId"] == LAB_A and body["suggestions"] == []
    assert events == ["lineage.suggest.rejected"]


def test_기록_이름_셋을_계약처럼_고정한다() -> None:
    """문구는 바뀌어도 이 셋은 대시보드 질의가 그 위에 서므로 바꾸지 않는다
    (`catalog.py:_search_log` 가 같은 규약을 검색 쪽에 세웠다)."""
    assert SUGGEST_LOGGER == "colab_core.suggest"
    assert SUGGEST_REJECTED == "LINEAGE_SUGGEST_REJECTED"
    assert SUGGEST_UNAVAILABLE == "LINEAGE_SUGGEST_UNAVAILABLE"
