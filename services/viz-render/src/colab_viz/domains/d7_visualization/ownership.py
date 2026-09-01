"""산출물 소유 **등급 판정** — `A-1` 안 ⑷ 갈래 B(게이트 대조)의 판정 규칙 **한 자리**.

**무엇을 답하는가** — 자리에 놓인 산출물 한 벌이 지금 **누구 것인가.**
**어떻게 답하는가** — 사이드카의 `sources`(fileId 배열)를 **원장에 대조한다.**
  이음은 `d5_upload_file.id = d3_file.id`(`NB-A` 동일성)이고, 그것이 유일한 다리다
  (불변규칙 1 로 업로드→데이터셋 FK 가 없다 · 선례 `gates/tools/autometa-loss.sh:14`).

**네 등급**
  ⑴ `살아 있다`            — 조각 하나라도 `d3_file` 에 있다 = 등록된 데이터셋이 소유한다
  ⑵ `접수분에만 닿는다`     — `d5_upload_file` 에만 있다 = 아직 등록 전이다. **고아가 아니다**
  ⑶ `고아`                — 어느 표에도 없다 = 원본이 사라졌다. **회수 대상은 이것뿐이다**
  ⑷ `판정 불가`            — 사이드카가 없거나 **구판**이다. 보류이지 고아가 아니다

⚠⚠ **덫 ① — `baked_for` 는 판정 입력이 아니다.**
  그 필드는 「**구울 때의** 대상」이고 등록 전환(`createDataset`) 뒤 **낡는다.** 그것을
  「현재 소유」로 읽으면 **등록된 대상이 전부 불일치로 뜬다**(대장 `A-1` `note` 축자).
  이 모듈은 `baked_for` 를 **스냅숏에만 적고 등급에는 쓰지 않는다** — `grade()` 의 본문에
  그 이름이 없다는 것이 그 증명이고, 시험이 변이로 다시 증명한다.

⚠⚠ **덫 ② — 구판은 「고아」가 아니라 「구판 · 판정 보류」다.**
  `sidecarVersion` 이 없거나 `baked_for` 가 없으면 **판정을 하지 않는다.**
  **없는 필드를 근거로 지우면 그것이 오삭제다**(대장 `A-1` `evidence` ㉱ 축자).

⚠ **원장이 구조적으로 비면 판정을 시작하지 않는다.** 경계 롤로 조회하면 예외가 아니라 **0**
  이 돌아오고, 그 0 을 「없다」로 읽어 전건을 고아로 세는 파괴적 오판이 이 레포에서 실제로
  났다(`DATA-REFERENCE §0 M-9` · `gates/tools/autometa-loss.sh` 머리말). 부르는 쪽이
  `Ledger.is_structurally_empty()` 로 먼저 막는다.

**의존 0** — 표준 라이브러리만 쓴다. 게이트가 이 파일을 **경로로 그대로 실어** 같은 규칙으로
  판정하기 때문이다(판정 규칙을 두 곳에 적으면 그것이 세 번째 규칙이 된다).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

#: 사이드카가 **판정에 쓸 수 있는** 최소 판 번호. 이보다 낮거나 없으면 구판이다.
MIN_DECIDABLE_SIDECAR_VERSION = 2

GRADE_LIVE = "살아 있다"
GRADE_UPLOAD_ONLY = "접수분에만 닿는다"
GRADE_ORPHAN = "고아"
GRADE_UNDECIDABLE = "판정 불가"

#: 계수 출력의 **고정 순서**. 회차마다 같은 순서로 나와야 값을 대조할 수 있다.
GRADES: tuple[str, ...] = (GRADE_LIVE, GRADE_UPLOAD_ONLY, GRADE_ORPHAN, GRADE_UNDECIDABLE)

#: 지도 타일 접두사 — `contracts/storage/layout.json` `contentKeys.지도 타일.prefix`.
#: **D5 가 구운 것이라 이 판정의 대상이 아니다**(`〈247〉` 경계 · 완료 정의 ⑷).
MAP_TILE_PREFIX = "tile-"


class SidecarContractViolation(ValueError):
    """판 번호는 2 인데 `sources` 가 비었다 — **관대하게 넘기지 않는다.**

    조용히 「판정 불가」로 접으면 규약 위반이 보류에 섞여 영원히 안 보인다.
    """


@dataclass(frozen=True)
class Ledger:
    """원장 두 표의 `id` 집합. **게이트가 채우고 이 모듈은 읽기만 한다.**"""
    dataset_files: frozenset[str]
    upload_files: frozenset[str]

    def is_structurally_empty(self) -> bool:
        """둘 다 비었다 = 잘못된 DB 이거나 경계에 걸린 조회다. **판정을 시작하지 않는다.**"""
        return not self.dataset_files and not self.upload_files


@dataclass(frozen=True)
class ArtifactGroup:
    """한 캐시 키 아래 나란히 선 산출물 **한 벌**(`.png`·`.webp`·`.json`·`.pgw`).

    세는 단위가 파일이 아니라 **벌**인 이유 = 한 벌은 함께 살고 함께 죽는다
    (`layout.json` `why ④`「확장자가 층을 가른다」).
    """
    cache_key: str
    paths: tuple[Path, ...]
    sidecar: dict | None = None

    def is_map_tile(self) -> bool:
        return str(self.cache_key).startswith(MAP_TILE_PREFIX)


@dataclass(frozen=True)
class Verdict:
    grade: str
    reason: str
    file_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class Tally:
    counts: dict[str, int]
    verdicts: dict[str, Verdict] = field(default_factory=dict)


def source_file_ids(doc: dict) -> tuple[str, ...]:
    """사이드카가 말하는 조각 전부. `sources` 가 정본이고 `source` 는 그 첫 조각이다."""
    raw: Sequence = doc.get("sources") or ([doc["source"]] if doc.get("source") else [])
    return tuple(str(x) for x in raw if str(x).strip())


def _is_legacy(doc: dict | None) -> bool:
    if doc is None:
        return True
    try:
        version = int(doc.get("sidecarVersion") or 0)
    except (TypeError, ValueError):
        return True
    # **판 번호와 `baked_for` 둘 다 있어야 판정 가능한 판이다** — 어느 한쪽만으로는 보류다.
    return version < MIN_DECIDABLE_SIDECAR_VERSION or "baked_for" not in doc


def grade(group: ArtifactGroup, ledger: Ledger) -> Verdict:
    """한 벌의 등급. **입력은 `sources` 와 원장뿐이다** — `baked_for` 는 여기 없다(덫 ①).

    지도 타일은 이 판정의 대상이 아니다 — 부르는 쪽이 먼저 가른다.
    """
    doc = group.sidecar
    if _is_legacy(doc):
        why = "사이드카 부재" if doc is None else "구판 — sidecarVersion·baked_for 가 없다"
        # ⚠ **고아가 아니다.** 없는 필드를 근거로 지우면 그것이 오삭제다.
        return Verdict(GRADE_UNDECIDABLE, why)

    assert doc is not None
    fids = source_file_ids(doc)
    if not fids:
        raise SidecarContractViolation(
            f"판 번호 {doc.get('sidecarVersion')} 인데 sources 가 비었다: {group.cache_key} — "
            "규약 위반을 판정 보류로 접지 않는다")

    if any(f in ledger.dataset_files for f in fids):
        return Verdict(GRADE_LIVE, "등록된 데이터셋의 파일이다 (d3_file)", fids)
    if any(f in ledger.upload_files for f in fids):
        return Verdict(GRADE_UPLOAD_ONLY, "접수분에만 있다 (d5_upload_file · 등록 전)", fids)
    return Verdict(GRADE_ORPHAN, "어느 표에도 없다 — 원본이 사라졌다", fids)


def tally(groups: Iterable[ArtifactGroup], ledger: Ledger) -> Tally:
    """네 등급 계수. **회차마다 재현 가능**해야 한다(완료 정의 ⑸)."""
    counts = {g: 0 for g in GRADES}
    verdicts: dict[str, Verdict] = {}
    for group in groups:
        if group.is_map_tile():
            continue
        v = grade(group, ledger)
        counts[v.grade] += 1
        verdicts[group.cache_key] = v
    return Tally(counts=counts, verdicts=verdicts)


def snapshot_rows(groups: Iterable[ArtifactGroup], ledger: Ledger) -> list[dict]:
    """**회수 전 전수 스냅숏** — 키·확장자·크기·사이드카 `source` ＋ 등급(완료 정의 ⑸).

    파일 한 줄씩이다. 지운 뒤에 「무엇이 있었나」를 답할 수 있는 유일한 기록이라
    **회수보다 먼저** 남긴다.
    """
    rows: list[dict] = []
    for group in sorted(groups, key=lambda g: g.cache_key):
        if group.is_map_tile():
            g_name, src = "지도 타일 (대상 아님)", ""
        else:
            v = grade(group, ledger)
            g_name = v.grade
            src = (group.sidecar or {}).get("source", "") or ""
        for p in sorted(group.paths, key=lambda x: x.name):
            path = Path(p)
            rows.append({"cache_key": group.cache_key, "extension": path.suffix,
                         "size_bytes": path.stat().st_size if path.exists() else -1,
                         "source": src, "grade": g_name})
    return rows


def orphan_keys(groups: Iterable[ArtifactGroup], ledger: Ledger) -> tuple[str, ...]:
    """**회수 대상은 이것뿐이다.** 판정 불가·접수분·지도 타일은 여기 들어오지 않는다."""
    return tuple(g.cache_key for g in groups
                 if not g.is_map_tile() and grade(g, ledger).grade == GRADE_ORPHAN)


def scan(previews_root: Path) -> list[ArtifactGroup]:
    """자리를 훑어 **키별로 한 벌씩** 묶는다. 사이드카(`.json`)가 있으면 실어 준다."""
    import json as _json

    root = Path(previews_root)
    buckets: dict[str, list[Path]] = {}
    for p in sorted(root.iterdir() if root.is_dir() else []):
        if p.is_file():
            buckets.setdefault(p.stem, []).append(p)
    groups: list[ArtifactGroup] = []
    for key, paths in sorted(buckets.items()):
        doc = None
        for p in paths:
            if p.suffix == ".json":
                try:
                    loaded = _json.loads(p.read_text(encoding="utf-8"))
                except (ValueError, OSError):
                    loaded = None
                # 사이드카가 못 읽히면 **보류**다 — 못 읽은 것을 「없다」로 세지 않는다.
                doc = loaded if isinstance(loaded, dict) else None
        groups.append(ArtifactGroup(cache_key=key, paths=tuple(paths), sidecar=doc))
    return groups
