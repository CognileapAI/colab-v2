"""지도 타일 **회수 한 바퀴** — 판독기의 지목을 회수 문 하나로 잇는다 (`TL-1` ⑷ 후단·⑹).

⭑ **⟨2026-09-05 · Ted 판정 「도는 배경 루프에 얹는다」⟩** 대장 `TL-1` 이 열어 둔 두 자리가
  이 파일과 `app/trigger_loop.py` 한 줄로 닫힌다 —
  ⑷ **후단** = 판독기(`tile_liveness`)가 회수(`invalidation.apply()`)와 결선된다
  ⑹ **회수 주체·주기** = `#60` 이 세운 **그 주기 배경 루프**다. 새 주체를 세우지 않는다:
     그 루프는 이미 돌고 있고, **HTTP 표면이 0** 이며(계약 개정 0), 같은 무늬가 이미 한 번
     같은 문제를 풀었다(`〈286〉` — 관리 op 도 기동 1회도 아닌 주기 루프).

**무엇을 지우는가 — 한 종류뿐이다.**
  `tile_liveness` 가 **고아(못 닿는다)** 로 판정한 `tile-` 키의 파일. 그 밖의 전부는 남는다:
  계산 불가 · 살아 있다 · 접수분에만 닿는다 · 판정 불가 · `tile-` 아닌 키.
  판정 규칙을 여기서 새로 적지 않는다 — 등급은 판독기가, 범위는 `invalidation.plan()` 이,
  집행은 `invalidation.apply()` 가 진다. **이 파일이 더하는 것은 「언제·얼마나까지」 하나다.**

**자동 삭제이므로 가드가 곧 산출물이다** — 셋을 문면으로 못 박는다.
  ⑴ **fail-closed** — 주체를 못 모으거나(0건) 못 연 주체가 하나라도 있으면 **판정을 시작하지
     않는다**(`ReaderNotReady`). 못 센 것을 「고아」로 세면 그것이 오삭제의 근거가 된다
     (`DATA-REFERENCE §0 M-9` — 경계에 걸린 0 을 「없다」로 읽어 전건을 고아로 센 오판).
  ⑵ **상한** — 한 바퀴가 지울 수 있는 벌 수에 뚜껑이 있다. 넘으면 **한 벌도 안 지우고 멈춘다.**
     상한을 넘었다는 것은 「고아가 많다」가 아니라 **주체 쪽이 무너졌다**는 신호다(마운트가
     빠졌다·자리가 갈렸다). 그 상태에서 지우는 것이 정확히 이 레포가 막으려는 실패다.
  ⑶ **기본은 관측 전용** — 배포가 명시로 켜기 전에는 **세고 적기만 하고 0건 지운다.**
     첫 배포가 계수를 먼저 증명하고, 그 다음에 켠다.

**지운 것은 전건이 로그에 남는다** — 키 · 등급 · 나이 · 크기. 지운 뒤 「무엇이 있었나」를
답하지 못하면 그것은 회수가 아니라 유실이다(`〈309〉`-㉯ 의 스냅숏과 같은 취지).
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

from . import invalidation, tile_liveness

log = logging.getLogger("colab_viz.tile_reclaim")

#: **한 바퀴가 지울 수 있는 벌 수의 뚜껑.** 근거는 실측이다 —
#: · staging 자리의 `tile-` 벌은 **2벌**이고 못 닿는 벌은 **0** 이었다(`〈313〉`-㉱)
#: · 이 레포에서 한 번에 회수한 최대치는 `RC-1` 의 **14벌**이었다(`〈309〉`-㉰ · 타일 아님)
#: ⟹ 20 은 **관측된 어떤 한 바퀴보다도 크고**, 주체 쪽이 무너졌을 때(마운트 소실·자리 이동)
#:    나오는 「전건 고아」보다는 **훨씬 작다.** 그 사이에 뚜껑을 두는 것이 요점이다.
#: ⚠ 뚜껑에 걸린 회차는 **실패가 아니라 보고**다 — 지우지 않고 건수를 드러낸 채 멈춘다.
DEFAULT_MAX_KEYS_PER_PASS = 20

#: 회수 한 바퀴의 주기(초). **트리거 주기(5초)와 같은 값을 쓰지 않는다** — 한 바퀴가
#: 주체 전건의 sha256 을 다시 뜨므로(내용 주소라 그것이 판정의 재료다) 5초마다 돌면
#: 저장소를 통째로 반복해서 읽는다. 1시간은 레포 결정이고, 값은 배포가 준다.
DEFAULT_INTERVAL_SECONDS = 3600.0


@dataclass(frozen=True)
class PassResult:
    """한 바퀴의 결과. **판정하지 못한 회차와 「고아 0」인 회차를 가른다.**"""
    ready: bool
    reason: str
    subjects: int
    tiles: int
    reachable: int
    unreachable: int
    capped: bool
    max_keys: int
    applied: bool
    removed: tuple[Path, ...] = ()
    rows: tuple[dict, ...] = ()

    def summary(self) -> str:
        if not self.ready:
            return f"지도 타일 회수 red(준비) — {self.reason}"
        return (f"지도 타일 회수 — 주체 {self.subjects} · 자리의 타일 {self.tiles}벌 · "
                f"닿는다 {self.reachable} · 못 닿는다 {self.unreachable} · "
                f"상한 {self.max_keys} · "
                f"{'지웠다' if self.applied else '관측 전용(0건 지웠다)'} "
                f"{len(self.removed)}파일")


def run_pass(*, previews_root, storage_root, apply: bool = False,
             max_keys: int = DEFAULT_MAX_KEYS_PER_PASS,
             now: float | None = None) -> PassResult:
    """회수 한 바퀴 — **판정 → 상한 확인 → (켜져 있으면) 집행.**

    ⚠ **예외를 밖으로 흘리지 않는 것은 부르는 쪽(루프)의 규약이다.** 여기서는 판정 못 할
      상태를 `ready=False` 로 **값으로** 돌려준다 — 못 한 것을 0 으로 적지 않기 위해서다.
    """
    subjects = tile_liveness.subjects_from_storage(storage_root)
    reached = tile_liveness.reach(subjects)
    tiles = tile_liveness.scan_tiles(previews_root)

    if not reached.is_decidable():
        reason = (f"주체 {reached.subjects_seen}건 · 계산 불가 "
                  f"{len(reached.uncomputable)}건 — 판정을 시작하지 않았다. "
                  "못 센 주체가 가리키던 타일이 고아로 둔갑한다 (DATA-REFERENCE §0 M-9)")
        log.warning("지도 타일 회수 red(준비) — %s", reason)
        for u in reached.uncomputable:
            log.warning("  계산 불가: %s — %s", u.file_id, u.reason)
        return PassResult(ready=False, reason=reason, subjects=reached.subjects_seen,
                          tiles=len(tiles), reachable=0, unreachable=0, capped=False,
                          max_keys=max_keys, applied=False)

    rows = []
    for r in tile_liveness.unreachable_rows(tiles, reached, now=now):
        row = dict(r)
        row["grade"] = tile_liveness.grade(r["cache_key"], reached).grade
        rows.append(row)
    unreachable = len(rows)
    reachable = len(tiles) - unreachable

    for row in rows:
        log.info("못 닿는 타일: %s · 등급 %s · 나이 %.2f일 · %d바이트 · 파일 %d",
                 row["cache_key"], row["grade"], row["age_days"], row["size_bytes"],
                 row["files"])

    if unreachable > max_keys:
        reason = (f"못 닿는 벌 {unreachable} > 상한 {max_keys} — **한 벌도 지우지 않는다.** "
                  "한 바퀴가 상한을 넘는 것은 고아가 늘어난 것이 아니라 주체 쪽이 무너진 "
                  "신호다(자리 소실·마운트 누락). 사람이 본 뒤에 집행한다")
        log.error("지도 타일 회수 정지 — %s", reason)
        return PassResult(ready=True, reason=reason, subjects=reached.subjects_seen,
                          tiles=len(tiles), reachable=reachable, unreachable=unreachable,
                          capped=True, max_keys=max_keys, applied=False,
                          rows=tuple(rows))

    if not apply:
        reason = "관측 전용 — 세고 적기만 한다 (COLAB_VIZ_TILE_RECLAIM_APPLY 미선언)"
        log.info("%s · 못 닿는 벌 %d", reason, unreachable)
        return PassResult(ready=True, reason=reason, subjects=reached.subjects_seen,
                          tiles=len(tiles), reachable=reachable, unreachable=unreachable,
                          capped=False, max_keys=max_keys, applied=False,
                          rows=tuple(rows))

    plan = invalidation.tile_reclaim_plan(tiles, reached, previews_root=previews_root)
    removed = invalidation.apply(plan, previews_root=previews_root)
    for row in rows:
        log.warning("지도 타일 회수 — 지웠다: %s · 등급 %s · 나이 %.2f일 · %d바이트",
                    row["cache_key"], row["grade"], row["age_days"], row["size_bytes"])
    result = PassResult(ready=True, reason="집행했다", subjects=reached.subjects_seen,
                        tiles=len(tiles), reachable=reachable, unreachable=unreachable,
                        capped=False, max_keys=max_keys, applied=True,
                        removed=tuple(removed), rows=tuple(rows))
    log.info("%s", result.summary())
    return result


@dataclass
class ReclaimJob:
    """**배경 루프에 얹히는 한 조각** — 자기 주기를 자기가 안다.

    루프는 트리거 버스를 5초로 비우고(`#60`), 이 조각은 그보다 성긴 자기 주기로만 돈다.
    ⚠ **스레드를 새로 만들지 않는다.** 주체가 하나 더 생기면 종료 규약도 하나 더 생긴다 —
      Ted 판정이 「도는 루프에 얹는다」인 이유가 그것이다.
    """
    previews_root: Path
    storage_root: Path
    apply: bool = False
    max_keys: int = DEFAULT_MAX_KEYS_PER_PASS
    interval_seconds: float = DEFAULT_INTERVAL_SECONDS
    last_result: PassResult | None = field(default=None, init=False)
    _next_at: float | None = field(default=None, init=False)

    def run_due(self, now: float | None = None) -> PassResult | None:
        """주기가 됐으면 한 바퀴, 아니면 **아무것도 하지 않는다**(`None`)."""
        at = time.monotonic() if now is None else now
        if self._next_at is not None and at < self._next_at:
            return None
        self._next_at = at + max(0.0, float(self.interval_seconds))
        self.last_result = run_pass(previews_root=self.previews_root,
                                    storage_root=self.storage_root,
                                    apply=self.apply, max_keys=self.max_keys)
        return self.last_result
