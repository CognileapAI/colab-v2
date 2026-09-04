"""트리거 집행의 **실행자** — 주기 배경 루프 (`03-HANDOFF §4 #60`).

`〈253〉` 회차가 세운 것은 받는 자리(`SpoolTriggerPort`)와 집행 한 바퀴
(`app/triggers.drain`)까지였고, **그 한 바퀴를 부르는 자가 런타임에 없었다** —
`main.py` 는 `app.state.triggers` 를 세우기만 했고 유일한 호출자가 시험이었다.
그래서 버스에 봉투가 쌓여도 미리보기는 낡은 채 굳었다(`#60`).

**왜 주기 루프인가**(Ted 판정) — 셋 중 하나였다: ⓐ 관리 HTTP op ⓑ 기동 시 1회
ⓒ 주기 배경 루프. ⓐ 는 D7 의 HTTP 표면을 늘리고 **계약 개정**을 부른다(`core-viz.yaml`
동결). ⓑ 는 기동 이후에 온 봉투를 영원히 안 집는다. ⓒ 는 **표면 0 · 계약 개정 0** 이다.

**모양은 pipeline-worker 를 그대로 따른다** — `app/worker.serve()` 가 `run_once()` 를
간격을 두고 반복하는 것과 같은 배치이고, 다른 것은 종료 신호를 `threading.Event` 로
받는 것 하나다(FastAPI 는 lifespan 으로 내려오는 종료가 있고, 그때 스레드를 남기면
SIGTERM 에 컨테이너가 매달린다).

**한 건이 실패해도 루프는 죽지 않는다** — 한 바퀴가 예외로 끊기면 **로그만 남기고**
다음 바퀴가 다시 집는다. 실패한 봉투는 `ack` 되지 않았으므로 버스에 남아 있다
(at-least-once 의 소비자 쪽 짝 — 멱등 키가 중복 집행을 거른다).
⚠ **멱등은 여기서 새로 만들지 않는다.** 집행·ack·멱등 키는 전부
`triggers.drain` + `SpoolTriggerPort` 의 것이고 이 파일은 **부르기만 한다.**

⭑ **⟨증보 2026-09-05 · Ted 판정 「도는 배경 루프에 얹는다」 · `TL-1` ⑹⟩ 이 루프가
  지도 타일 회수도 부른다.** 셋 중 하나였고(관리 HTTP op · 별도 스레드/크론 · 도는 루프)
  판정은 셋째다 — **이미 돌고 있고 · HTTP 표면이 0 이며 · 계약 개정이 0** 이다.
  ⚠ **여기에 회수 규칙이 없다.** 무엇을 지울지는 `tile_liveness` 가 판정하고 범위는
  `invalidation.plan()` 이 계산하며 집행은 `invalidation.apply()` 하나다. 이 파일이
  더하는 것은 **부름 한 자리**이고, 그 부름도 `drain` 과 **같은 규칙**으로 감싼다 —
  **한 바퀴가 터져도 루프는 죽지 않는다.**
"""
from __future__ import annotations

import logging
import threading

from . import triggers

log = logging.getLogger("colab_viz.trigger_loop")


class TriggerDrainLoop:
    """버스를 주기로 비우는 배경 스레드 하나.

    **데몬 스레드가 아니다** — `stop()` 이 실제로 합류(join)하는 것이 종료 규약이고,
    합류에 실패하면 그 사실을 로그로 남긴다(조용히 새는 것을 만들지 않는다).
    """

    def __init__(self, port, *, jobs, source, interval_seconds: float,
                 reclaim=None) -> None:
        self._port = port
        self._jobs = jobs
        self._source = source
        self._interval = float(interval_seconds)
        #: 지도 타일 회수 조각(`d7_visualization.tile_reclaim.ReclaimJob`). **`None` 이면
        #: 얹히지 않는다** — 배선이 없으면 회수도 없다(자리를 지어내지 않는다).
        self._reclaim = reclaim
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        #: 관측용 — 돈 바퀴 수와 집행 건수. 시험이 「루프가 실제로 돌았는가」를 잰다.
        self.passes = 0
        self.drained = 0
        #: 관측용 — 회수 바퀴가 실제로 돌았는가. **판정한 바퀴만 센다.**
        self.reclaim_passes = 0

    # ── 수명 ────────────────────────────────────────────────────────────────
    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="viz-trigger-drain",
                                        daemon=False)
        self._thread.start()

    def stop(self, timeout: float = 10.0) -> None:
        """**깨끗이 멈춘다** — 대기 중이면 즉시 깬다(간격만큼 매달리지 않는다)."""
        self._stop.set()
        thread, self._thread = self._thread, None
        if thread is None:
            return
        thread.join(timeout)
        if thread.is_alive():
            log.warning("트리거 루프가 %.1f초 안에 멈추지 않았다 — 집행 중인 렌더가 있다",
                        timeout)

    # ── 한 바퀴 ─────────────────────────────────────────────────────────────
    def tick(self) -> int:
        """한 바퀴 — **예외를 밖으로 내보내지 않는다.** 실패는 로그로 남고 루프는 산다."""
        self.passes += 1
        try:
            done = triggers.drain(self._port, jobs=self._jobs, source=self._source)
        except Exception:  # noqa: BLE001 — 어떤 봉투도 루프를 죽이지 못한다
            log.exception("트리거 집행 한 바퀴가 실패했다 — 다음 바퀴가 다시 집는다")
            return 0
        self.drained += len(done)
        if done:
            log.info("트리거 집행 %d건 — 미리보기를 다시 만들었다", len(done))
        self._reclaim_tick()
        return len(done)

    def _reclaim_tick(self) -> None:
        """회수 한 바퀴 — **주기가 됐을 때만** 돌고, **터져도 루프를 죽이지 않는다.**

        ⚠ 트리거 집행과 **격리**돼 있다. 회수가 실패해도 미리보기 재생성은 계속 돌고,
          그 반대도 같다 — 한쪽의 예외가 다른 쪽을 인질로 잡지 않는다.
        """
        if self._reclaim is None:
            return
        try:
            result = self._reclaim.run_due()
        except Exception:  # noqa: BLE001 — 회수 한 바퀴가 루프를 죽이지 못한다
            log.exception("지도 타일 회수 한 바퀴가 실패했다 — 다음 주기가 다시 본다")
            return
        if result is not None:
            self.reclaim_passes += 1
            log.info("%s", result.summary())

    def _run(self) -> None:
        while not self._stop.is_set():
            self.tick()
            self._stop.wait(self._interval)
