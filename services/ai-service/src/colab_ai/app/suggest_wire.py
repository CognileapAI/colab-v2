"""계보 제안의 **전송 쪽** — 본문 조립 · OpenAI 왕복 · 계수 한 줄.

⚠ **왜 `suggest.py` 에서 갈라져 나왔나** (게이트 ① 판정 2026-09-24). WU2 가 ~300줄을
넘으면 **포트·파서 ↔ 전송**으로 나누라는 수정 조건이 붙었다. 나누는 선은
「모델을 어떻게 부르는가」(이 파일)와 「그 답을 무엇으로 읽는가」(`suggest.py`)다.

전송은 `LlmQueryInterpreter._http_transport`(`interpret.py:158-166`)와 **같은 모양**이다 —
`response_format: json_object` · 고정 seed · `temperature` 없음 · 주입 가능.

⚠ **저장이 없다.** 이 파일이 아는 바깥 주소는 모델 하나뿐이다 (`CLAUDE.md §3-2`).
"""
from __future__ import annotations

import json
import logging
import time
import urllib.request
from typing import Callable

from colab_ai.ports import ParentCandidate

#: 운영자가 기계로 긁을 이름. `interpret.INTERPRETER_LOGGER` 와 **같은 규약·같은 채널**이다.
SUGGESTER_LOGGER = "colab_ai.degraded"
_degraded_log = logging.getLogger(SUGGESTER_LOGGER)

#: 호출 1회당 계수 한 줄의 표식 (게이트 ① 판정 — 모델·지연·후보 수·제안 수·결과).
#: 실측(`eval/k3-lineage`)과 운영이 같은 줄을 긁는다. **부르지 않은 회차에는 이 줄이 없다.**
CALL_EVENT = "d10.suggest.call"
#: 원시 예외 전용 줄. 응답에 나가는 문구와 **다른 자리**다.
FAIL_EVENT = "d10.suggest.unreachable"

#: 요청 본문에 고정으로 싣는 `seed`. 값 자체에 뜻은 없다 — 회차 간 같기만 하면 된다.
SEED = 20260924

#: 후보 요약의 상한. 계약 `LineageParentCandidate.summary.maxLength` 와 **같은 값**이다 —
#: 정본을 새로 정하는 것이 아니라 옮겨 적는다. core-api 가 이미 잘라 보내지만 여기서도
#: 자른다: 상한이 한 곳에만 있으면 그 한 곳이 언젠가 어긋나고, 그때 본문이 통째로 부푼다.
MAX_CANDIDATE_SUMMARY = 200


def candidate_payload(c: ParentCandidate) -> dict:
    """후보 한 건을 **데이터로** 편다. 모르는 값은 열쇠를 만들지 않는다 — 계약 산문과 같은 규율."""
    body: dict = {"datasetId": c.dataset_id, "name": c.name}
    if c.topic:
        body["topic"] = c.topic
    if c.summary:
        body["summary"] = c.summary[:MAX_CANDIDATE_SUMMARY]
    if c.source_label:
        body["sourceLabel"] = c.source_label
    if c.processing_level is not None:
        body["processingLevel"] = c.processing_level
    if c.period_start:
        body["periodStart"] = c.period_start
    if c.period_end:
        body["periodEnd"] = c.period_end
    return body


def build_payload(*, model: str, system_prompt: str, file_meta: dict,
                  candidates: tuple[ParentCandidate, ...],
                  dataset_name_draft: str | None, subject: str | None) -> dict:
    """왕복 본문 한 벌. **후보는 지시문이 아니라 데이터로 실린다** — 지시문은 한 장뿐이다."""
    user: dict = {"file": file_meta,
                  "candidates": [candidate_payload(c) for c in candidates]}
    if dataset_name_draft:
        user["datasetNameDraft"] = dataset_name_draft
    if subject:
        user["subject"] = subject
    return {
        "model": model,
        "messages": [{"role": "system", "content": system_prompt},
                     {"role": "user", "content": json.dumps(user, ensure_ascii=False)}],
        "response_format": {"type": "json_object"},
        # `temperature` 는 넣지 않는다 — `gpt-5.6-luna` 가 `temperature: 0` 을
        # 400 `unsupported_value` 로 거부한다 (2026-08-26 실측 · `interpret.py:178-181`).
        "seed": SEED,
    }


def http_transport(*, base_url: str, api_key: str | None,
                   timeout: float) -> Callable[[dict], str]:
    """OpenAI chat completions 왕복 한 번. 실패는 **호출자가** 잡는다(여기서 삼키지 않는다)."""

    def send(payload: dict) -> str:
        req = urllib.request.Request(
            base_url, method="POST",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {api_key}"})
        with urllib.request.urlopen(req, timeout=timeout) as res:
            body = json.loads(res.read() or b"{}")
        return body["choices"][0]["message"]["content"]

    return send


def log_call(*, model: str, started: float, candidates: int, suggestions: int,
             outcome: str) -> None:
    """**호출 1회에 계수 한 줄.** 모델을 부르지 않은 회차에는 이 줄이 없다."""
    _degraded_log.info(
        "event=%s model=%s latency_ms=%d candidates=%d suggestions=%d outcome=%s",
        CALL_EVENT, model, int((time.monotonic() - started) * 1000),
        candidates, suggestions, outcome)


def log_unreachable(exc: BaseException) -> None:
    """**원시 예외는 로그로만 간다** — urllib 예외 문구에는 내부 주소·포트가 들어 있다."""
    _degraded_log.warning("event=%s exc=%s: %s", FAIL_EVENT, type(exc).__name__, exc)
