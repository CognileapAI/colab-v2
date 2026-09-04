"""자동 무효화 — **사건 감지 → 무효화 범위 계산 → 재생성** (`Y-1` · `§J-7` 정의).

**stage 1 은 「자동 재생성을 하지 않는다」**(`〈74〉`-㉴ 축자) — 사람이 「다시 만들기」를
부르는 것이 stage 1 의 유일한 경로다. **그 원칙이 뒤집히는 자리는 이 WU 하나**이고
(`Y-1` 완료 정의 ⓓ), 뒤집히는 **범위**를 이 모듈이 문면으로 못 박는다.

⭑ **⟨2026-08-31 · Ted RULING ⑲ · `PLAN-SoT §9 〈247〉`⟩ 예외의 범위 = 「렌더 산출물 한정」.**
  **원본 데이터·기준 격자 파일·데이터셋은 어떤 트리거로도 자동으로 다시 만들지 않는다.
  자동으로 다시 만드는 것은 「보여주기 위한 산출물」뿐이다.**

  근거는 실측이다 — 렌더 산출물은 **미리보기 루트**(`layout.json` `roots` 의 둘째)에
  살고 원본·격자는 **접수분 루트**에 산다. 산출물은 원본에서 다시 만들 수 있는
  부산물이고 **카탈로그에 데이터셋으로 등록될 자리가 스키마에 없다**(`layout.json` —
  「미리보기 산출물은 원장에 행이 없다 … `FileKind` 를 넓히지 않는다」). 원칙의 취지
  (사용자가 모르는 사이 **데이터**가 바뀌는 것을 막는다)는 그대로 지켜진다.

**무효화 규칙을 새로 코딩하지 않는다** — 어느 산출물이 낡았는가는 `cache.py` 의 키가
이미 답한다(같은 입력이면 같은 키). 이 모듈이 더하는 것은 **「낡은 것을 실제로 치우고
다시 굽는 일을 누가 언제 시작하는가」** 하나다.

**경계**(완료 정의 ⓔ) — **무효화·재생성은 D7 소유, 트리거 발신은 D5** 다. 그래서 이
모듈에 있는 것은 **받는 자리(`TriggerPort`)** 뿐이고, D5 의 표·큐·outbox 에 붙는 코드가
없다(`CLAUDE.md §3-1` · 음성 시험이 잠근다).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Protocol

from ...kernel import storage_layout

#: 트리거 3종 — **대장 축자**다(`WORK-UNITS §10.2-b` `Y-1` 행 · `〈206〉`-㉮ 로 첫째의
#: 이름이 「재가공」에서 바뀌었다). 이름을 여기서 새로 짓지 않는다.
TRIGGER_BACKEND_RERUN = "미리보기 뒷단 재실행"
TRIGGER_GRID_CHANGED = "격자 변경"
TRIGGER_FILE_ADDED = "파일 추가"

#: ⚠ **목록을 넓히는 것은 별도 판정이다.** 특히 **색 범위 잠정→확정 전환은 여기 없다** —
#: `〈74〉`-㉴ 가 그것을 **stage 1 의 자기 절차**로 이미 규정했다(캐시 키의 단계 토큰 ·
#: 바뀐 뒤 한 번 알린다). 넣으려면 판정을 먼저 받는다(`Y-1` 행 말미 ⚠).
TRIGGERS: tuple[str, ...] = (TRIGGER_BACKEND_RERUN, TRIGGER_GRID_CHANGED, TRIGGER_FILE_ADDED)


class UnknownTrigger(ValueError):
    """모르는 사건은 **무효화를 일으키지 않는다.** 관대하게 받으면 목록이 코드로 넓어진다."""


class OutOfScope(Exception):
    """**`〈247〉` 의 바깥이다** — 렌더 산출물이 아닌 것을 지우려 했다.

    조용히 걸러내지 않고 **예외로 멈춘다.** 걸러내면 같은 버그가 다음에도 오고, 그때는
    아무도 모른다. 이 레포의 실패형이 정확히 그것이다(`DATA-REFERENCE §0` — 여덟 중
    일곱이 에러를 안 냈다).
    """


@dataclass(frozen=True)
class StaleCandidate:
    """이 대상 때문에 구워진 산출물 하나. `cache_key` 는 `render_cache_key` 의 값이다.

    ⭑ ⟨증보 · `V-1` ⑷⟩ `variant_key` = **팔레트를 뺀 서명**(`cache.render_variant_key`).
    비어 있으면 **모르는 것**이고, 모르는 것은 어떤 회수 대상도 되지 않는다 —
    `tile-` 처럼 D7 이 굽지 않은 벌이 그 자리다.
    """
    cache_key: str
    path: Path
    variant_key: str = ""


@dataclass(frozen=True)
class InvalidationEvent:
    """D5 가 보낸 사건 하나. **트리거 이름은 세 값 중 하나여야 한다.**

    ⭑ ⟨증보 2026-08-31 · 12차 해제 · `〈253〉`⟩ `delivery_key` 는 봉투의 **멱등 키**다
    (`<타입>:<uploadId>`). 받는 자리가 재전달을 거르고 집행을 확인(ack)하는 데 쓴다 —
    at-least-once 라 같은 사건이 두 번 오는 것은 예외가 아니라 정상이다.
    **비어 있으면 배선을 거치지 않은 사건**이다(시험·수동 경로).
    """
    trigger: str
    target_id: str
    delivery_key: str = ""

    def __post_init__(self) -> None:
        if self.trigger not in TRIGGERS:
            raise UnknownTrigger(
                f"모르는 사건이다: {self.trigger!r} — 트리거는 {list(TRIGGERS)} 셋뿐이다")
        if not str(self.target_id).strip():
            raise UnknownTrigger("대상이 없는 사건은 무효화 범위를 계산할 수 없다")


@dataclass(frozen=True)
class InvalidationPlan:
    """계산된 범위. **`trigger` 가 `None` 이면 사람이 부른 경로**다(완료 정의 ⓒ).

    수동은 트리거가 아니라 **경로**다 — 그래서 트리거 열거에 넣지 않고 `None` 으로
    가른다. 대신 **계산기는 하나**이므로 두 경로가 같은 범위를 얻는다.
    """
    trigger: str | None
    target_id: str
    stale: tuple[Path, ...]
    kept: tuple[Path, ...]
    regenerate: bool


class TriggerPort(Protocol):
    """**받는 자리다.** 사건을 만드는 것은 D5 이고, D7 은 받아서 자기 산출물만 다시 굽는다.

    ⚠ 실물 배선(어느 큐·어느 호출)은 **배포가 준다** — `SourcePort` 가 파일시스템 어댑터
    하나로 서 있는 것과 같은 모양이다(`ports/source.py` 서두). **Protocol 이 그 자리를
    비워 두었다는 것이 요점**이고, D7 이 D5 의 원장을 직접 읽는 길은 여기에 없다.
    """

    def poll(self) -> Iterable[InvalidationEvent]: ...

    def ack(self, event: InvalidationEvent) -> None:
        """집행이 **끝난 뒤** 부른다. 먼저 지우면 실패한 알림이 사라지고 미리보기가
        낡은 채 굳는다 — 그 상태는 아무 데도 안 적힌다."""
        ...


def _under(root: Path, path: Path) -> bool:
    try:
        Path(path).resolve().relative_to(Path(root).resolve())
    except (ValueError, OSError):
        return False
    return True


def plan(event: InvalidationEvent | None, *, produced: Iterable[StaleCandidate],
         previews_root: Path, keep_keys: Iterable[str] = (),
         target_id: str | None = None) -> InvalidationPlan:
    """**무효화 범위 계산기 — 자동 경로와 수동 경로가 함께 지나는 유일한 자리**(ⓒ).

    남기는 것 셋 —
      ⑴ `keep_keys` — 방금 다시 구운 산출물. 지우면 새 그림이 사라진다
      ⑵ **지도 타일 키(`tile-`)** — 같은 슬롯에 살지만 **D5 가 구운 지도용 산출물**이다.
         「그 밖의 산출물을 지우지 않는다」(ⓐ)의 실물이 이 한 줄이다
      ⑶ (해당 없음 — 그 밖의 것은 애초에 후보가 아니다)

    거절하는 것 하나 — **미리보기 루트 밖의 경로.** 원본·기준 격자는 **다른 루트**에
    살므로, 이 검사가 곧 `〈247〉` 의 경계다.
    """
    root = Path(previews_root)
    keep = set(keep_keys)
    tid = event.target_id if event is not None else (target_id or "")
    stale: list[Path] = []
    kept: list[Path] = []
    for c in produced:
        if not _under(root, c.path):
            raise OutOfScope(
                f"미리보기 루트 밖의 자리는 무효화 대상이 아니다: {Path(c.path).name} — "
                "원본·기준 격자·데이터셋은 자동으로 다시 만들지 않는다 (〈247〉)")
        if c.cache_key in keep or storage_layout.is_map_tile_key(c.cache_key):
            kept.append(c.path)
        else:
            stale.append(c.path)
    return InvalidationPlan(trigger=(event.trigger if event is not None else None),
                            target_id=tid, stale=tuple(stale), kept=tuple(kept),
                            regenerate=event is not None)


def reclaim_plan(groups, ledger, *, previews_root: Path,
                 target_id: str = "") -> InvalidationPlan:
    """**소유 회수 계획 — 고아 등급만 치운다**(`A-1` 완료 정의 ⑸ · 단계 6).

    ⭑ **집행 문을 늘리지 않는다**(완료 정의 ⑶). 이 함수는 계획을 새로 계산하지 않고
    **같은 계산기 `plan()` 을 부른다** — 고아가 **아닌** 키를 전부 `keep_keys` 로 넘기는
    것이 전부다. 그래서 다음 셋이 공짜로 따라온다:
      · `tile-` 키는 `kept` — `plan()` 이 이미 지도 타일을 가른다(완료 정의 ⑷)
      · **미리보기 루트 밖은 `OutOfScope`** — 접수분 루트(원본·기준 격자)·데이터셋 무접촉(`〈247〉`)
      · 집행은 `apply()` 한 자리 — 지우는 문은 여전히 하나다

    ⚠ **판정 불가(구판)는 `kept` 다.** 없는 필드를 근거로 지우면 그것이 오삭제다(덫 ②).
    ⚠ **`baked_for` 는 여기서도 읽지 않는다** — 등급은 `ownership.grade()` 가 내고,
      그 입력은 `sources` ＋ 원장뿐이다(덫 ①).
    """
    from . import ownership

    if ledger.is_structurally_empty():
        raise OutOfScope(
            "원장이 구조적으로 비어 있다 — 그 0 을 「없다」로 읽으면 전건이 고아가 된다. "
            "회수 계획을 세우지 않는다 (DATA-REFERENCE §0 M-9)")
    groups = list(groups)
    orphans = set(ownership.orphan_keys(groups, ledger))
    candidates = [StaleCandidate(cache_key=g.cache_key, path=p)
                  for g in groups for p in g.paths]
    keep = [g.cache_key for g in groups if g.cache_key not in orphans]
    return plan(None, produced=candidates, previews_root=previews_root,
                keep_keys=keep, target_id=target_id)


def supersede_plan(produced: Iterable[StaleCandidate], *, previews_root: Path,
                   variant_key: str, keep_keys: Iterable[str],
                   target_id: str = "") -> InvalidationPlan:
    """**팔레트만 바꾼 재렌더가 대체한 옛 벌**(`V-1` 완료 정의 ⑷ · `〈259〉`).

    ⭑ **집행 문도 계산기도 늘리지 않는다**(`Y-1` 완료 정의 ⓒ 와 같은 선). 이 함수는
    범위를 새로 계산하지 않고 **같은 계산기 `plan()` 을 부른다** — 회수 대상이 **아닌**
    키를 전부 `keep_keys` 로 넘기는 것이 전부다(`reclaim_plan` 과 같은 모양). 그래서
    다음 셋이 공짜로 따라온다:
      · `tile-` 키는 `kept` — `plan()` 이 이미 지도 타일을 가른다(⑷-c)
      · **미리보기 루트 밖은 `OutOfScope`** — 원본·기준 격자·데이터셋 무접촉(`〈247〉`)
      · 집행은 `apply()` 한 자리 — 지우는 문은 여전히 하나다

    **회수 대상 = 변이 키가 같고 캐시 키가 다른 벌** 하나뿐이다. 변이 키가 같다는 것은
    「같은 데이터·같은 색범위·같은 선택·같은 시각·같은 격자」라는 뜻이고, 그 위에서
    키가 갈렸다는 것은 **팔레트가 갈렸다**는 뜻이다(빠진 입력이 그것 하나다).
    ⟹ 원본이 바뀐 재렌더는 변이 키부터 갈리므로 **여기 들어오지 않는다** — 「사람이 부른
    렌더는 앞의 산출물을 지우지 않는다」(`Y-1`)가 그 자리에서 그대로 선다.

    ⚠ **변이 키를 모르는 후보(`""`)는 손대지 않는다.** 없는 근거로 지우면 그것이 오삭제다.
    """
    if not variant_key:
        raise OutOfScope(
            "변이 키 없이 회수 대상을 고르지 않는다 — 모르는 것을 지우면 그것이 오삭제다")
    produced = list(produced)
    fresh = set(keep_keys)
    keep = [c.cache_key for c in produced
            if c.variant_key != variant_key or c.cache_key in fresh]
    return plan(None, produced=produced, previews_root=previews_root,
                keep_keys=keep, target_id=target_id)


def apply(plan: InvalidationPlan, *, previews_root: Path) -> tuple[Path, ...]:
    """집행 — **미리보기 루트 안의 렌더 산출물만 지운다.**

    범위 계산이 이미 한 번 봤는데 여기서 또 보는 이유 = **이중 방어**다. 지우는 자리가
    이 단위에 하나뿐이므로(음성 시험이 그것을 잠근다) 이 한 줄이 마지막 문이다.
    **하나라도 밖이면 아무것도 지우지 않는다** — 반쯤 지우고 멈추지 않는다.
    """
    root = Path(previews_root)
    for p in plan.stale:
        if not _under(root, p):
            raise OutOfScope(
                f"미리보기 루트 밖을 지우려 했다: {Path(p).name} — 집행하지 않는다 (〈247〉)")
    removed: list[Path] = []
    for p in plan.stale:
        path = Path(p)
        if path.exists():
            path.unlink()
            removed.append(path)
    return tuple(removed)
