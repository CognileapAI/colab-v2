"""워커 조립 루트 — 릴레이와 reaper 를 돌린다. 도메인 판단은 여기 없다.

두 고리를 **한 프로세스 안에서 따로** 돈다:
  ① **릴레이** — outbox 의 미발행 이벤트를 내보내고 발행 시각을 찍는다(at-least-once)
  ② **reaper** — 만료된 미등록 업로드를 지운다(`〈64〉-ⓒ`). TTL 초과분 회수는 README 요구다

**발행 대상(큐·브로커)은 아직 고르지 않았다** — `〈61〉` 동결 계약은 봉투만 못박았고 전송
수단은 정본이 값을 주지 않았다(`[정본 무근거]`). 그래서 기본 발행자는 **표준 출력 한 줄**
이고, 실제 전송 수단이 정해지면 `publish` 를 갈아 끼운다. **원장에 남는 사실은 같다.**
"""
from __future__ import annotations

import json
import os
import time

from ..domains.d5_ingestion import SqlLedger, reap_expired_uploads, relay_unpublished
from ..kernel.db import apply_scope, make_engine, make_session_factory

ENV_DB = "COLAB_PIPELINE_DB_URL"
ENV_LAB = "COLAB_WORKER_LAB_ID"
ENV_ACCOUNT = "COLAB_WORKER_ACCOUNT_ID"


def stdout_publish(envelope: dict) -> None:
    print(json.dumps(envelope, ensure_ascii=False), flush=True)


def run_once(*, publish=stdout_publish) -> tuple[int, list[str]]:
    """릴레이 1회 + reaper 1회. 돌려주는 것은 (내보낸 건수, 지운 업로드)."""
    url = os.environ.get(ENV_DB)
    if not url:
        raise RuntimeError(f"{ENV_DB} 가 없다 — 원장 없이 워커를 돌리지 않는다")
    lab, account = os.environ.get(ENV_LAB), os.environ.get(ENV_ACCOUNT)
    if not lab or not account:
        # 경계는 이벤트에도 실린다 — 큐에서 꺼낸 메시지에는 주체가 없다(envelope.json labId).
        raise RuntimeError(f"{ENV_LAB}·{ENV_ACCOUNT} 가 있어야 연구실 경계를 세운다")

    engine = make_engine(url)
    factory = make_session_factory(engine)
    session = factory()
    try:
        session.begin()
        apply_scope(session, lab_id=lab, account_id=account)
        ledger = SqlLedger(session)
        sent = relay_unpublished(ledger, publish=publish)
        reaped = reap_expired_uploads(ledger)
        session.commit()
        return sent, reaped
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()
        engine.dispose()


def serve(interval_seconds: float = 5.0) -> None:  # pragma: no cover - 배관
    while True:
        run_once()
        time.sleep(interval_seconds)


if __name__ == "__main__":  # pragma: no cover - 배관
    serve()
