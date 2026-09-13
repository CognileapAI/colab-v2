"""**사용자가 지운 데이터셋의 미리보기 산출물 회수 한 바퀴** (`DL-2` · 회부문 ⓓ3·ⓓ6).

⭑ **자동 회수 루프와 다른 문이다.** `tile_reclaim` 은 **스스로 도는** 배경 루프라
  판정이 한 번 틀리면 아무도 안 보는 사이에 지운다 — 그래서 그쪽의 S3 삭제는 0건으로
  잠겨 있고 **그 잠금은 그대로다.** 이 문의 방아쇠는 **사람이 데이터셋 삭제를 누른 것**
  하나이고, 입력은 그때 실제로 지워진 `fileId` 집합 `D` 다.

**왜 원장 등급으로는 안 되는가** — `ownership.grade()` 는 묘비 데이터셋의 `fileId` 를
  `d5_upload_file` 잔존 때문에 「접수분에만 닿는다」로 읽는다. **그것은 고아가 아니다**
  ⟹ 배경 루프로는 영원히 회수되지 않는다. 판정식은 `invalidation.deletion_keep_reason`
  한 자리에 있고 이 모듈은 그것을 **부르기만 한다.**

**후보를 어디서 모으는가 — 둘의 합집합**
  ⑴ **표식**(`preview-index/by-file/{fileId}/`) — 지워진 `fileId` 마다 목록 조회 **1회**.
     버킷 접두 전체 스캔 0 이고 비용이 `|D|` 에만 비례한다.
  ⑵ **로컬 자리**(`ownership.scan`) — 표식은 `DL-2` 회차부터 찍힌다. **그 전에 구워진
     산출물에는 표식이 없어** 로컬 훑기로 보충하고, 표식 밖이었던 벌 수를 `unindexed`
     로 **센다**(세지 않으면 옛 산출물이 얼마나 남았는지 아무도 모른다).

**지우는 문은 늘지 않는다** — 로컬은 `invalidation.apply()`(`unlink`) 하나이고 원격은
  `PreviewSinkPort.remove` 하나다. 로컬에 없어도 **S3 이름은 키에서 계산된다** —
  dev 의 로컬 캐시는 LRU 라 밀려난 벌이 S3 에만 남는다.

**멱등** — 두 번째 호출은 표식이 이미 없고 로컬 파일도 없으므로 `stale 0` 이다. core 가
  삭제를 재시도해도 같은 결과가 나온다.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from ...kernel.preview_sinks import CONTENT_TYPES
from ...kernel.storage_layout import PREVIEW_INDEX_PREFIX
from . import invalidation, ownership

#: 한 벌이 차지할 수 있는 확장자 — 싱크가 아는 것과 **같은 표**를 쓴다. 여기서 다시 적으면
#: 그 순간 규칙이 둘이 되고, 갈린 쪽이 지우지 못한 객체는 조용히 남는다.
PREVIEW_SUFFIXES: tuple[str, ...] = tuple(CONTENT_TYPES)


@dataclass(frozen=True)
class ReclaimResult:
    """한 바퀴의 결과. **계수와 이름을 함께** 낸다 — 계수만으로는 무엇이 남았는지 모른다."""
    stale: int
    kept: int
    unindexed: int
    removed: tuple[str, ...]
    kept_reasons: dict[str, int] = field(default_factory=dict)
    #: **고아 표식** — 가리키는 산출물도 사이드카도 없어 걷어낸 표식 수 (`DL-2` D9).
    orphan_index: int = 0


def _index_pairs(client: Any, file_ids: Iterable[str]) -> list[tuple[str, str]]:
    """지워진 파일마다 표식 접두 목록 **1회**. `(fileId, contentKey)` 로 돌려준다.

    ⚠ **어느 파일의 표식이었는지를 버리지 않는다** — 고아 표식을 걷을 때 지울 자리가
    그 쌍이고, `D` 전체를 곱하면 있지도 않은 자리를 지우라고 보내게 된다.
    """
    found: list[tuple[str, str]] = []
    if client is None:
        return found
    for file_id in file_ids:
        prefix = f"{PREVIEW_INDEX_PREFIX}/by-file/{file_id}/"
        for key, _size in client.list_objects(prefix):
            tail = str(key)[len(prefix):].strip("/")
            if tail and "/" not in tail:
                found.append((file_id, tail))
    return found


def _has_any_object(client: Any, previews_root: Path, previews_prefix: str,
                    content_key: str) -> bool:
    """이 벌의 산출물이 **한 조각이라도** 실재하는가 — 로컬 먼저, 없으면 원격.

    ⚠ **「없다」로 단정하는 자리라 관대하게 읽지 않는다.** 원격 조회가 실패(권한·장애)하면
    `True` 로 읽는다 — 못 물어본 것을 「없다」로 접으면 살아 있는 산출물의 표식을 지우고,
    그 산출물은 그 순간부터 **되찾을 길이 없다.**
    """
    root = Path(previews_root)
    for ext in PREVIEW_SUFFIXES:
        if (root / f"{content_key}{ext}").exists():
            return True
    if client is None:
        return False
    head = getattr(client, "head_object", None)
    if head is None:
        return True                 # 물어볼 길이 없으면 「있다」로 읽는다
    for ext in PREVIEW_SUFFIXES:
        try:
            head(f"{previews_prefix}/{content_key}{ext}")
            return True
        except FileNotFoundError:
            continue
        except Exception:           # noqa: BLE001 — 못 물어본 것은 「없다」가 아니다
            return True
    return False


def _local_sidecar(previews_root: Path, content_key: str) -> dict | None:
    path = Path(previews_root) / f"{content_key}.json"
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return doc if isinstance(doc, dict) else None


def _remote_sidecar(client: Any, previews_prefix: str, content_key: str) -> dict | None:
    """로컬에 사이드카가 없으면 서빙 자리에서 읽는다 — **크기를 먼저 확인한다.**

    판독은 `legacy_preview_observation._read_sidecar` 를 **그대로 쓴다.** 같은 규칙을 두 곳에
    적으면 갈라지고, 갈라진 판독기는 서로 다른 것을 「구판」이라 부른다.
    """
    if client is None:
        return None
    from .legacy_preview_observation import ObservationNotReady, _read_sidecar

    key = f"{previews_prefix}/{content_key}.json"
    try:
        size, _etag = client.head_object(key)
        return _read_sidecar(client, key, int(size))
    except ObservationNotReady:
        return None
    except Exception:       # noqa: BLE001 — 못 읽은 것은 「없다」이지 「지워도 된다」가 아니다
        return None


def run(*, client: Any, sink: Any, previews_root: Path, target_id: str,
        file_ids: Iterable[str], previews_prefix: str = "previews") -> ReclaimResult:
    """한 바퀴. **판정은 `invalidation` 이, 집행은 `apply()`＋`sink.remove` 가 진다.**

    ⚠ `file_ids` 가 비면 `invalidation.deletion_plan` 이 `OutOfScope` 로 멈춘다 — 빈 집합에
    대해 「모든 원천이 포함된다」가 참이 되어 **전건이 회수 대상**이 되기 때문이다.
    """
    deleted = [str(f).strip() for f in file_ids if str(f).strip()]
    root = Path(previews_root)

    index_pairs = _index_pairs(client, deleted)
    indexed = {key for _fid, key in index_pairs}
    # 로컬 자리에서 **규칙을 충족하는 벌만** 보탠다 — 전건을 끌어오지 않는다.
    local_groups = {g.cache_key: g for g in ownership.scan(root)}
    local_hits = {key for key, g in local_groups.items()
                  if invalidation.deletion_keep_reason(g, deleted) is None}
    candidates = sorted(indexed | local_hits)
    unindexed = len(local_hits - indexed)

    groups: list[ownership.ArtifactGroup] = []
    for content_key in candidates:
        doc = _local_sidecar(root, content_key)
        if doc is None:
            doc = _remote_sidecar(client, previews_prefix, content_key)
        # 후보 경로는 **존재하지 않아도 후보다** — 로컬 캐시에서 밀려난 벌의 S3 이름을
        # 이름으로 계산해야 지울 수 있다. `apply()` 는 있는 것만 unlink 한다.
        paths = tuple(root / f"{content_key}{ext}" for ext in PREVIEW_SUFFIXES)
        groups.append(ownership.ArtifactGroup(cache_key=content_key, paths=paths,
                                              sidecar=doc))

    plan = invalidation.deletion_plan(groups, deleted, previews_root=root,
                                      target_id=target_id)

    reasons: dict[str, int] = {}
    stale_groups: list[ownership.ArtifactGroup] = []
    for group in groups:
        why = invalidation.deletion_keep_reason(group, deleted)
        if why is None:
            stale_groups.append(group)
        else:
            reasons[why] = reasons.get(why, 0) + 1

    invalidation.apply(plan, previews_root=root)

    names = [f"{g.cache_key}{ext}" for g in stale_groups for ext in PREVIEW_SUFFIXES]
    # 표식 쌍은 **그 벌의 사이드카가 말한 원천**에서 온다 — `D` 전체를 곱하면 있지도 않은
    # 자리를 지우라고 보내게 되고, 그 요청은 실패하지 않으므로 계수가 부풀지도 않는다.
    pairs = [(file_id, g.cache_key)
             for g in stale_groups
             for file_id in ownership.source_file_ids(g.sidecar or {})]

    # ⭑ ⟨2026-09-13 · prod 임시 검증 실측 · D9⟩ **고아 표식을 걷는다.** 렌더는 표식을
    #   `publish` 보다 **먼저** 쓰므로(ⓓ7), 그 사이에 렌더가 죽으면 가리키는 산출물이 없는
    #   표식만 남는다 — 실측 10개. 그 표식은 사이드카가 없어 판정이 영원히 `kept` 이고,
    #   다음 회수가 매번 같은 후보를 되짚는다. **자정되지 않는 자리**라 여기서 끊는다.
    # ⛔ 지우는 것은 **표식뿐**이다(`names` 에 한 글자도 더하지 않는다) · 그것도 **`D` 의
    #   표식만**이다(`_index_pairs` 가 `D` 의 접두만 훑는다).
    kept_keys = {g.cache_key for g in groups} - {g.cache_key for g in stale_groups}
    sidecarless = {g.cache_key for g in groups if g.sidecar is None}
    orphan_pairs = [(fid, key) for fid, key in index_pairs
                    if key in kept_keys and key in sidecarless
                    and not _has_any_object(client, root, previews_prefix, key)]
    pairs = pairs + orphan_pairs

    if names or pairs:
        sink.remove(names, index_pairs=pairs)

    return ReclaimResult(stale=len(stale_groups), kept=len(groups) - len(stale_groups),
                         unindexed=unindexed, removed=tuple(names), kept_reasons=reasons,
                         orphan_index=len(orphan_pairs))


__all__ = ["PREVIEW_SUFFIXES", "ReclaimResult", "run"]
