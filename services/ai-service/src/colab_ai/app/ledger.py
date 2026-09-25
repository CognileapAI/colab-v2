"""모델 호출 실행 원장의 **적재 쪽** — `ports.ModelCallLedgerPort` 의 구현 둘.

정본 = `dev-package/intent/2026-09-24-d10-model-call-ledger.md` 「판정 기록 (2026-09-24 Ted)」
      · 근거 `dev-package/PLAN-SoT.md §9-㊷` 추기 ② (2026-09-24 — 처리 리전 기록 의무 철회).

**이 단위가 쓰는 유일한 표다.** 사전 조회는 여전히 `READ ONLY` 트랜잭션이고
(`app/dictionaries.py`), 여기만 한 행을 넣는다. 넣는 것은 **호출 자체의 운영
메타데이터**이지 제안도 질의도 아니다 — 제안은 여전히 응답과 함께 죽는다
(`DOMAINS.md` 「제안은 D10 안에서 태어나 D10 안에서 죽는다」).

⚠ **쓰기 실패가 응답을 죽이지 않는다.** `record_call` 이 모든 예외를 잡아 경고 한 줄로
바꾼다 — `CLAUDE.md §3` 이 「AI 없이도 v2 는 완결된 제품이다」라고 못 박은 것의 한 칸
아래다: **원장 없이도 AI 는 완결된다.** 원장 때문에 검색이 5xx 를 내면 관측 장치가
제품을 망가뜨린 것이고, 그건 관측이 아니다.

⚠ **자기 트랜잭션으로 넣고 바로 닫는다.** 요청 트랜잭션에 얹으면 원장 실패가 그 트랜잭션을
통째로 물들이고, 반대로 요청이 되돌아갈 때 「호출은 실제로 일어났다」는 사실까지 같이
사라진다 — 호출은 이미 돈을 썼고 시간을 썼다. 그 사실은 되돌려지지 않는다.
"""
from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.engine import Engine

from colab_ai.kernel.config import Settings
from colab_ai.kernel.db import make_engine
from colab_ai.ports import ModelCallEntry, ModelCallLedgerPort

#: 운영자가 기계로 긁을 이름. `interpret.INTERPRETER_LOGGER` 와 **같은 채널·같은 규약**이다.
LEDGER_LOGGER = "colab_ai.degraded"
_log = logging.getLogger(LEDGER_LOGGER)

#: 원장 쓰기가 실패했다는 표식. **응답에는 한 글자도 나가지 않는다.**
LEDGER_FAIL_EVENT = "ledger.write_failed"
#: 원장 자리가 배선되지 않았다는 표식. 프로세스 수명 동안 **한 번만** 찍는다 —
#: 매 호출마다 찍으면 진짜 사고 줄이 그 안에 묻힌다.
LEDGER_DISABLED_EVENT = "ledger.disabled"

#: 열 이름을 **적어서** 넣는다. 위치 기반으로 넣으면 나중에 칸이 하나 끼어들 때
#: 값들이 통째로 한 칸씩 밀리고, 타입이 맞으면 DB 가 그것을 거절하지 못한다.
INSERT_SQL = text(
    """
    INSERT INTO d10_model_call (
      id, called_at, call_site, provider, model_requested, model_returned,
      outcome, not_called_reason, latency_ms, prompt_tokens, completion_tokens,
      cached_prompt_tokens, input_count, result_count, lab_id
    ) VALUES (
      :id, :called_at, :call_site, :provider, :model_requested, :model_returned,
      :outcome, :not_called_reason, :latency_ms, :prompt_tokens, :completion_tokens,
      :cached_prompt_tokens, :input_count, :result_count, :lab_id
    )
    """
)


class SqlModelCallLedger:
    """행 하나를 `db/ai` 체인에 넣는다. **읽지 않는다** — 읽는 것은 운영자의 psql 이다."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def record(self, entry: ModelCallEntry) -> None:
        with self._engine.begin() as conn:
            conn.execute(INSERT_SQL, {
                "id": entry.id,
                "called_at": entry.called_at,
                "call_site": entry.call_site,
                "provider": entry.provider,
                "model_requested": entry.model_requested,
                "model_returned": entry.model_returned,
                "outcome": entry.outcome,
                "not_called_reason": entry.not_called_reason,
                "latency_ms": entry.latency_ms,
                "prompt_tokens": entry.prompt_tokens,
                "completion_tokens": entry.completion_tokens,
                "cached_prompt_tokens": entry.cached_prompt_tokens,
                "input_count": entry.input_count,
                "result_count": entry.result_count,
                "lab_id": entry.lab_id,
            })


class NullModelCallLedger:
    """DB 주소가 없을 때의 원장. **터지지 않는다 — 그리고 통과했다고도 말하지 않는다.**

    `Settings` 는 값이 하나도 없어도 프로세스를 띄운다(`kernel/config.py` 머리말).
    그 상태에서 원장이 예외를 던지면 「설정이 없으면 뜬다」가 거짓이 된다. 대신
    **처음 한 번 경고를 남긴다** — 조용히 사라지면 운영자는 원장이 비어 있는 것을
    「호출이 없었다」로 읽는다. 그 둘은 다른 사실이다.
    """

    def __init__(self) -> None:
        self._warned = False

    def record(self, entry: ModelCallEntry) -> None:
        if self._warned:
            return
        self._warned = True
        _log.warning("event=%s reason=no_db_url call_site=%s "
                     "— 원장 주소가 배선되지 않았다. 「행 0건」을 「호출 0건」으로 읽지 않는다.",
                     LEDGER_DISABLED_EVENT, entry.call_site)


def failure_outcome(exc: BaseException) -> str:
    """전송이 던진 것을 **원장의 두 칸으로 가른다.** 두 호출 지점이 같은 규칙을 쓴다.

    「기다렸는데 안 왔다」(`timeout`)와 「애초에 닿지 못했다」(`unreachable`)는 **고칠 곳이
    다르다** — 앞은 대기 시간·모델·본문 크기의 문제이고 뒤는 배선·키·네트워크의 문제다.
    접으면 원장을 보고 어느 쪽을 만져야 하는지 알 수 없다.

    ⚠ `urllib` 은 읽기 시간 초과를 `URLError(TimeoutError(...))` 로 **감싸서** 던진다 —
    바깥 타입만 보면 전부 `unreachable` 이 되고 시간 초과가 원장에서 사라진다.
    """
    if isinstance(exc, TimeoutError):
        return "timeout"
    if isinstance(getattr(exc, "reason", None), TimeoutError):
        return "timeout"
    return "unreachable"


def build_ledger(settings: Settings) -> ModelCallLedgerPort:
    """조립 — 주소가 있으면 SQL, 없으면 빈 원장. **키 유무로 가르지 않는다.**"""
    if settings.dict_db_url:
        return SqlModelCallLedger(make_engine(settings.dict_db_url))
    return NullModelCallLedger()


def record_call(ledger: ModelCallLedgerPort | None, entry: ModelCallEntry) -> None:
    """**호출 경로가 부르는 유일한 자리.** 어떤 예외도 여기서 멎는다.

    `ledger` 가 `None` 이면 아무 일도 없다 — 원장을 배선하지 않은 조립(끈 회차·시험)이
    그 상태이고, 그때 행이 없는 것이 정상이다.
    """
    if ledger is None:
        return
    try:
        ledger.record(entry)
    except Exception as exc:                                      # noqa: BLE001
        # ⛔ `BaseException` 을 잡지 않는다 — `KeyboardInterrupt`·`SystemExit` 까지 삼키면
        #   프로세스를 세우는 신호가 원장 한 줄 때문에 사라진다.
        # **원시 예외는 로그로만 간다** — 접속 문자열이 예외 문구에 들어 있을 수 있다.
        _log.warning("event=%s call_site=%s outcome=%s exc=%s: %s",
                     LEDGER_FAIL_EVENT, entry.call_site, entry.outcome,
                     type(exc).__name__, exc)
