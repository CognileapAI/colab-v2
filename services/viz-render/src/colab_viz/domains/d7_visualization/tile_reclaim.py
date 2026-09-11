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

import hashlib
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import (invalidation, legacy_preview_observation, ownership, ownership_snapshot,
               tile_liveness)
from ...kernel.ids import is_ulid
from ...kernel import storage_layout

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


def _legacy_local(previews_root: Path, ledger: ownership.Ledger) -> dict:
    groups = ownership.scan(previews_root)
    tally = ownership.tally(groups, ledger)
    legacy = ownership.legacy_tally(groups, ledger)
    unreachable = (legacy.counts[ownership.LEGACY_SIDECAR_ABSENT]
                   + legacy.counts[ownership.LEGACY_SOURCE_LEDGER_ABSENT])
    return {"preview_groups": len([g for g in groups if not g.is_map_tile()]),
            "ownership_counts": tally.counts, "legacy_counts": legacy.counts,
            "legacy_groups": sum(legacy.counts.values()),
            "rebake_unreachable": unreachable, "deleted": 0}


def _legacy_summary(result: dict) -> str:
    own, legacy = result["ownership_counts"], result["legacy_counts"]
    return ("TL-2 구판 관측 — preview {preview_groups}벌 · 소유 [살아 있다 {live} · "
            "접수분에만 닿는다 {upload} · 고아 {orphan} · 판정 불가 {unknown}] · "
            "구판 [사이드카 부재 {missing} · 원천 원장 부재 {absent} · 원천 원장 있음 "
            "{present}] · 재굽기 불가 {unreachable} · 삭제 0건").format(
                **result, live=own[ownership.GRADE_LIVE],
                upload=own[ownership.GRADE_UPLOAD_ONLY], orphan=own[ownership.GRADE_ORPHAN],
                unknown=own[ownership.GRADE_UNDECIDABLE],
                missing=legacy[ownership.LEGACY_SIDECAR_ABSENT],
                absent=legacy[ownership.LEGACY_SOURCE_LEDGER_ABSENT],
                present=legacy[ownership.LEGACY_SOURCE_LEDGER_PRESENT],
                unreachable=result["rebake_unreachable"])


def _observe_legacy(job, *, s3: bool) -> None:
    job.last_legacy_result = None
    job.legacy_not_ready = None
    if job.ledger_snapshot_path is None:
        job.legacy_not_ready = "원장 snapshot 경로가 설정되지 않았다"
        log.error("TL-2 구판 관측 red(준비) — %s", job.legacy_not_ready)
        return
    try:
        ledger = ownership_snapshot.load(
            job.ledger_snapshot_path, max_age_seconds=job.ledger_snapshot_max_age_seconds,
            expected_owner_uid=job.ledger_snapshot_owner_uid,
            expected_group_gid=job.ledger_snapshot_group_gid)
        result = (legacy_preview_observation.observe(
                    job.client, ledger, prefix=job.previews_prefix)
                  if s3 else _legacy_local(job.previews_root, ledger))
    except (ownership_snapshot.SnapshotNotReady, ownership.SidecarContractViolation,
            ownership.LegacyObservationNotReady, legacy_preview_observation.ObservationNotReady) as exc:
        job.legacy_not_ready = str(exc)
        log.error("TL-2 구판 관측 red(준비) — %s", exc)
        return
    job.last_legacy_result = result
    log.info("%s", _legacy_summary(result))


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
    ledger_snapshot_path: Path | None = None
    ledger_snapshot_max_age_seconds: float = 7200.0
    ledger_snapshot_owner_uid: int | None = None
    ledger_snapshot_group_gid: int | None = None
    last_result: PassResult | None = field(default=None, init=False)
    last_legacy_result: dict | None = field(default=None, init=False)
    legacy_not_ready: str | None = field(default=None, init=False)
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
        _observe_legacy(self, s3=False)
        return self.last_result


# ── S3 dev 관측 ────────────────────────────────────────────────────────────────
def _prefix(value: str, *, expected: str) -> str:
    """버킷 루트 목록을 만들 수 없는 한 층 prefix만 받는다."""
    clean = str(value).strip("/")
    if not clean or "/" in clean or clean != expected:
        raise ValueError(f"S3 회수 prefix는 {expected}/ 하나여야 한다")
    return clean + "/"


def _s3_not_ready(reason: str, *, max_keys: int) -> PassResult:
    log.error("지도 타일 회수 red(준비) — %s", reason)
    return PassResult(ready=False, reason=reason, subjects=0, tiles=0,
                      reachable=0, unreachable=0, capped=False,
                      max_keys=max_keys, applied=False)


_S3_OBSERVATION_CHUNK_BYTES = 1 << 20


def _s3_object_digest(client: Any, key: str, listed_size: int) -> tuple[str, int]:
    """같은 S3 객체 버전을 디스크에 쓰지 않고 끝까지 읽어 sha256을 계산한다."""
    head_size, etag = client.head_object(key)
    if int(head_size) != int(listed_size):
        raise ValueError(f"{key}: 목록 크기 {listed_size} ≠ HeadObject 크기 {head_size}")
    if not str(etag).strip():
        raise ValueError(f"{key}: 같은 버전 GET을 고정할 ETag가 없다")
    stream = client.get_object_stream(
        key, chunk_size=_S3_OBSERVATION_CHUNK_BYTES, expected_etag=etag)
    digest = hashlib.sha256()
    received = 0
    try:
        for chunk in stream:
            received += len(chunk)
            if received > head_size:
                raise ValueError(f"{key}: HeadObject 크기 {head_size}보다 많은 바이트를 받았다")
            digest.update(chunk)
    finally:
        close = getattr(stream, "close", None)
        if callable(close):
            close()
    if received != head_size:
        raise ValueError(f"{key}: HeadObject 크기 {head_size} ≠ 받은 바이트 {received}")
    return digest.hexdigest(), received


def run_s3_observation(*, client: Any, source: Any,
                       uploads_prefix: str = "uploads",
                       previews_prefix: str = "previews",
                       apply: bool = False,
                       max_keys: int = DEFAULT_MAX_KEYS_PER_PASS) -> PassResult:
    """S3의 지도 타일을 읽기만 하는 한 바퀴.

    S3에서는 삭제 문을 아예 연결하지 않는다. dev의 첫 관측이 안전하다는 증거를 얻기 전
    로컬 볼륨용 자동 삭제를 객체 저장소까지 넓히면 삭제 범위가 새로 생긴다. 따라서
    apply=True도 요청 사실만 경고하고 결과는 언제나 applied=False다.

    주체 키는 ETag가 아니라 streaming으로 끝까지 읽은 실제 바이트로 계산한다. ETag는
    HeadObject와 GetObject가 같은 객체 버전인지 If-Match로 고정하는 데만 쓴다. 로컬 렌더
    cache와 작업 디렉터리는 읽거나 쓰지 않는다.
    """
    try:
        upload_root = _prefix(uploads_prefix, expected="uploads")
        preview_root = _prefix(previews_prefix, expected="previews")

        bodies: dict[str, set[str]] = {}
        body_objects: dict[tuple[str, str], tuple[str, int]] = {}
        grid_objects: dict[str, dict[str, tuple[str, int]]] = {}
        for key, size in client.list_objects(upload_root):
            if not key.startswith(upload_root):
                raise ValueError("S3가 요청 prefix 밖의 객체를 돌려줬다")
            rest = key[len(upload_root):]
            parts = rest.split("/")
            if len(parts) == 2 and is_ulid(parts[0]) and is_ulid(parts[1]):
                bodies.setdefault(parts[0], set()).add(parts[1])
                body_objects[(parts[0], parts[1])] = (key, int(size))
            elif (len(parts) == 3 and is_ulid(parts[0])
                  and parts[1] == storage_layout.GRID_DIRNAME):
                name = storage_layout.safe_file_name(parts[2])
                grid_objects.setdefault(parts[0], {})[name] = (key, int(size))
            elif rest:
                raise ValueError("uploads/ 아래 객체 키가 저장 규약과 다르다")

        storage_keys: dict[str, list[str]] = {}
        bad: list[tile_liveness.Uncomputable] = []
        seen = sum(len(names) for names in bodies.values())
        for target_id, expected_names in sorted(bodies.items()):
            try:
                grid_entries = []
                for name, (key, size) in sorted(grid_objects.get(target_id, {}).items()):
                    digest, _received = _s3_object_digest(client, key, size)
                    grid_entries.append((name, digest))
                grid_digest = (storage_layout.map_tile_grid_digest_entries(grid_entries)
                               if grid_entries else None)
            except Exception as exc:  # noqa: BLE001 — 한 주체라도 못 읽으면 판정 전체를 멈춘다
                bad.extend(tile_liveness.Uncomputable(name, type(exc).__name__)
                           for name in sorted(expected_names))
                continue
            for name in sorted(expected_names):
                try:
                    key, size = body_objects[(target_id, name)]
                    digest, received = _s3_object_digest(client, key, size)
                    candidates = tile_liveness.candidate_tile_keys_from_digests(
                        source_digest=digest, source_byte_size=received,
                        grid_digest=grid_digest)
                except Exception as exc:  # noqa: BLE001 — 일부 실패도 전체 판정을 막는다
                    bad.append(tile_liveness.Uncomputable(name, type(exc).__name__))
                    continue
                for cache_key, _used_grid in candidates:
                    storage_keys.setdefault(cache_key, []).append(name)

        reached = tile_liveness.Reach(
            dataset_keys={}, upload_keys={},
            uncomputable=tuple(bad), subjects_seen=seen,
            storage_keys={key: tuple(ids) for key, ids in storage_keys.items()},
        )

        tile_sizes: dict[str, int] = {}
        for key, size in client.list_objects(preview_root):
            if not key.startswith(preview_root):
                raise ValueError("S3가 요청 prefix 밖의 객체를 돌려줬다")
            rest = key[len(preview_root):]
            path = Path(rest)
            if (rest and len(path.parts) == 1 and path.suffix == ".tif"
                    and path.stem.startswith(tile_liveness.MAP_TILE_PREFIX)):
                tile_sizes[path.stem] = int(size)
    except Exception as exc:  # noqa: BLE001 — 자격/목록/바이트 실패를 고아 0으로 접지 않는다
        return _s3_not_ready(
            f"{type(exc).__name__}: S3 관측 입력을 읽지 못했다", max_keys=max_keys)

    if not reached.is_decidable():
        reason = (f"주체 {reached.subjects_seen}건 · 계산 불가 "
                  f"{len(reached.uncomputable)}건 — 판정을 시작하지 않았다")
        result = _s3_not_ready(reason, max_keys=max_keys)
        return PassResult(**{**result.__dict__, "subjects": reached.subjects_seen,
                             "tiles": len(tile_sizes)})

    rows: list[dict] = []
    reachable = 0
    for cache_key, size in sorted(tile_sizes.items()):
        verdict = tile_liveness.grade(cache_key, reached)
        if verdict.grade == tile_liveness.GRADE_ORPHAN:
            rows.append({"cache_key": cache_key, "grade": verdict.grade,
                         "size_bytes": size, "files": 1, "age_days": None})
        else:
            reachable += 1
    unreachable = len(rows)
    capped = unreachable > max_keys
    if apply:
        log.warning("S3 지도 타일 회수 apply 요청을 무시했다 — 관측 전용이며 삭제 문이 없다")
    for row in rows:
        log.info("못 닿는 S3 타일: %s · 등급 %s · %d바이트",
                 row["cache_key"], row["grade"], row["size_bytes"])
    reason = ("S3 관측 전용 — 세고 적기만 한다 (삭제 문 없음)"
              if not capped else
              f"못 닿는 벌 {unreachable} > 상한 {max_keys} — S3 관측 전용, 삭제 0")
    return PassResult(
        ready=True, reason=reason, subjects=reached.subjects_seen,
        tiles=len(tile_sizes), reachable=reachable, unreachable=unreachable,
        capped=capped, max_keys=max_keys, applied=False, rows=tuple(rows))


@dataclass
class S3ReclaimJob:
    """dev S3 배포에 붙는 주기 job. 삭제 포트는 받지 않는다."""
    client: Any
    source: Any
    uploads_prefix: str = "uploads"
    previews_prefix: str = "previews"
    apply_requested: bool = False
    max_keys: int = DEFAULT_MAX_KEYS_PER_PASS
    interval_seconds: float = DEFAULT_INTERVAL_SECONDS
    ledger_snapshot_path: Path | None = None
    ledger_snapshot_max_age_seconds: float = 7200.0
    ledger_snapshot_owner_uid: int | None = None
    ledger_snapshot_group_gid: int | None = None
    last_result: PassResult | None = field(default=None, init=False)
    last_legacy_result: dict | None = field(default=None, init=False)
    legacy_not_ready: str | None = field(default=None, init=False)
    _next_at: float | None = field(default=None, init=False)

    def run_due(self, now: float | None = None) -> PassResult | None:
        at = time.monotonic() if now is None else now
        if self._next_at is not None and at < self._next_at:
            return None
        self._next_at = at + max(0.0, float(self.interval_seconds))
        self.last_result = run_s3_observation(
            client=self.client, source=self.source,
            uploads_prefix=self.uploads_prefix, previews_prefix=self.previews_prefix,
            apply=self.apply_requested, max_keys=self.max_keys)
        _observe_legacy(self, s3=True)
        return self.last_result


@dataclass
class NotReadyReclaimJob:
    """source와 preview 저장 모드가 갈린 배포를 고아 0으로 숨기지 않는다."""
    reason: str
    max_keys: int = DEFAULT_MAX_KEYS_PER_PASS
    interval_seconds: float = DEFAULT_INTERVAL_SECONDS
    last_result: PassResult | None = field(default=None, init=False)
    _next_at: float | None = field(default=None, init=False)

    def run_due(self, now: float | None = None) -> PassResult | None:
        at = time.monotonic() if now is None else now
        if self._next_at is not None and at < self._next_at:
            return None
        self._next_at = at + max(0.0, float(self.interval_seconds))
        self.last_result = _s3_not_ready(self.reason, max_keys=self.max_keys)
        return self.last_result
