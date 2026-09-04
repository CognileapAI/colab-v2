"""지도 타일 **생존 판독기** — `tile-` 벌이 지금도 닿는 자리인가 (`TL-1`).

**왜 별도 자리인가** — `ownership.py` 의 등급은 **사이드카의 `sources` 를 원장에 대조**해
매겨진다. 그런데 `tile-` 벌에는 사이드카가 **0건**이다(D5 가 쓰지 않는다). 그래서
`scan()`·`grade()` 는 타일을 판정 대상에서 뺀다. Ted 판정(`PLAN-SoT §9 〈302〉`)은 그 함수를
**넓히지 않는다**로 났고(`〈296〉`-㉶ 와 같은 선), 대신 **별도 진입점**을 세운다 —
이 파일이다(대장 `TL-1` 완료 정의 ⑷).

**무엇을 답하는가** — 자리에 놓인 타일 한 벌을 **지금의 주체 중 누군가가 다시 만들어 낼 수
있는가.** 답하는 법은 사이드카가 아니라 **키 재계산**이다: 지도 타일 키는 내용 주소라
(`contracts/storage/layout.json` `contentKeys.지도 타일.why`) 굽는 쪽이 쓴 재료 여섯을
읽는 쪽이 그대로 다시 모으면 같은 이름이 나온다(`〈294〉`). 그 이름 집합에 없는 타일은
**아무도 다시 가리키지 않는 자리**다.

**판정 규칙** (대장 `TL-1` 완료 정의 ⑴ 축자)
  「살아 있는 데이터셋 파일 또는 보류 업로드가 **하나라도** 가리키면 산다」
  ⟹ **첫 주체가 지워져도 타일은 살고, 마지막 주체가 사라질 때만 고아다.**
  3 주체 공유가 실표본이다 — 같은 타일 키를 살아 있는 데이터셋 2개 ＋ 미등록 업로드 1개가
  가리킨다(`sessions/ARTIFACT-OWNER-DESIGN-20260831.md §㉯`).

**네 등급을 그대로 쓴다** (완료 정의 ⑶ · 이름·순서는 `ownership.GRADES` 하나가 갖는다)
  ⑴ `살아 있다`         — 등록된 데이터셋의 본체 하나가 이 키를 낳는다
  ⑵ `접수분에만 닿는다`  — 미등록 접수분만 낳는다. **고아가 아니다**
  ⑶ `고아`             — 지금의 어느 주체도 이 키를 낳지 않는다 = **키가 갈렸거나 원본이 사라졌다**
  ⑷ `판정 불가`         — **타일에는 서지 않아야 한다.** 키 재계산이 사이드카의 자리를 메우는
                         것이 이 항목의 핵심이라, 여기 값이 서면 그것이 결함이다

⚠⚠ **제3의 상태 — 「계산 불가」는 「고아」가 아니다.**
  주체의 본체를 못 열면 그 주체가 낳을 키를 **모른다.** 그것을 조용히 빼면 그 주체가
  가리키던 타일이 **고아로 둔갑한다** — 경계에 걸린 0 을 「없다」로 읽어 전건을 고아로 센
  파괴적 오판이 이 레포에서 실제로 났다(`DATA-REFERENCE §0 M-9`). 그래서 계산 불가가 한
  건이라도 있으면 **판정을 시작하지 않는다**(`ReaderNotReady`). 주체 0건도 같다.

⛔ **이것은 판독기이지 회수자가 아니다 — 아무것도 지우지 않는다.**
  회수는 `invalidation.apply()` **한 자리**이고 그 결선(누가 언제 부르는가)은 대장
  `TL-1` 완료 정의 ⑹ 에 `[미확인]` 로 남아 있다. **지어내지 않는다.**

**의존 0** — 표준 라이브러리와 `kernel.storage_layout`(그 자신도 표준 라이브러리뿐인
  생성물)만 쓴다. 판정 규칙을 두 곳에 적으면 그것이 세 번째 규칙이 된다.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

from ...kernel import storage_layout
from .ownership import (GRADE_LIVE, GRADE_ORPHAN, GRADE_UNDECIDABLE, GRADE_UPLOAD_ONLY,
                        GRADES, MAP_TILE_PREFIX)

__all__ = ["GRADES", "ORIGIN_DATASET", "ORIGIN_UPLOAD", "ORIGIN_STORAGE",
           "ReaderNotReady", "Subject",
           "Uncomputable", "Reach", "Verdict", "TileArtifact", "Tally",
           "file_digest", "candidate_tile_keys", "reach", "grade", "scan_tiles",
           "subjects_from_storage", "tally", "unreachable_keys", "unreachable_rows"]

#: 주체의 두 갈래. **등급의 이름이 아니라 주체의 출신이다** — 등급은 `ownership.GRADES` 다.
ORIGIN_DATASET = "데이터셋 파일"     # d3_file — 등록된 데이터셋이 소유한다
ORIGIN_UPLOAD = "접수분"            # d5_upload_file — 아직 등록 전이다

#: **원장을 안 열고 자리에서 모은 주체** — 등록 여부(데이터셋인가 접수분인가)를 D7 이 모른다.
#: ⚠ 지어내지 않는다: 저장 배치는 등록 전후를 **가르지 않는다**(`kernel/storage_layout` 서두
#:   「`targetId` 가 무엇인가」 — 등록 전에는 `uploadId`, 등록 뒤에는 `datasetId` 이고 자리는
#:   하나다). `ports/source.FilesystemSourcePort` 도 같은 말을 한다 — 「등록된 데이터셋인지
#:   등록 전 업로드인지를 **파일 배치로 구분하지 않는다**」. 그래서 출신을 둘 중 하나로
#:   **찍지 않고** 셋째 이름을 준다. 회수 판정에는 영향이 없다 — 둘 다 「닿는다」이고
#:   회수 대상은 **어느 주체도 낳지 않는 키** 하나뿐이다.
ORIGIN_STORAGE = "자리의 주체"


class ReaderNotReady(RuntimeError):
    """**판정을 시작하지 않았다.** 못 센 것을 「고아」로 세지 않는다(⚠⚠ 제3의 상태).

    green-by-skip 의 반대다 — 부르는 쪽은 이 예외를 **red(준비)** 로 옮겨 적는다.
    """


@dataclass(frozen=True)
class Subject:
    """키를 낳을 수 있는 **주체 하나** = 원장 한 행 ＋ 그 본체 바이트가 놓인 자리.

    `grid_dir` 은 그 대상의 기준 격자 자리다(`storage_layout.grid_dir`). 없으면 `None` —
    **없는 것을 지어내지 않는다.** 있으면 후보 키가 둘이 된다(격자를 썼는가/안 썼는가).
    """
    file_id: str
    origin: str
    source: Path
    grid_dir: Path | None = None


@dataclass(frozen=True)
class Uncomputable:
    """**키를 짓지 못한 주체.** 「고아」의 근거가 아니라 판정 중단의 근거다."""
    file_id: str
    reason: str


@dataclass(frozen=True)
class Reach:
    """지금의 주체들이 낳는 **이름 전부** — 자리를 뒤진 것이 아니라 계약이 낳은 것이다.

    `storage_keys` 는 **원장 없이 자리에서 모은 주체**(`ORIGIN_STORAGE`)가 낳는 이름이다.
    등록 여부를 모르므로 `dataset_keys`·`upload_keys` 중 어느 쪽으로도 **섞지 않는다** —
    섞으면 로그가 모르는 것을 아는 것처럼 적는다.
    """
    dataset_keys: dict[str, tuple[str, ...]]
    upload_keys: dict[str, tuple[str, ...]]
    uncomputable: tuple[Uncomputable, ...]
    subjects_seen: int
    storage_keys: dict[str, tuple[str, ...]] = field(default_factory=dict)

    def is_decidable(self) -> bool:
        """**주체를 한 건이라도 봤고, 못 센 주체가 없다.** 둘 중 하나만 어긋나도 거짓이다."""
        return self.subjects_seen > 0 and not self.uncomputable

    def reached_by(self, cache_key: str) -> int:
        """그 키를 낳는 주체가 **몇인가** — ⑴ 의 「하나라도」를 세는 자리."""
        return (len(self.dataset_keys.get(cache_key, ()))
                + len(self.upload_keys.get(cache_key, ()))
                + len(self.storage_keys.get(cache_key, ())))


@dataclass(frozen=True)
class Verdict:
    grade: str
    reason: str
    file_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class TileArtifact:
    """자리에 실재하는 **타일 한 벌**. 지도 타일의 확장자는 `.tif` 하나다."""
    cache_key: str
    paths: tuple[Path, ...]
    mtime: float


@dataclass(frozen=True)
class Tally:
    counts: dict[str, int]
    verdicts: dict[str, Verdict]


def file_digest(path) -> str:
    """본체 바이트의 sha256 — **굽는 쪽(`d5/pipeline.file_digest`)과 같은 계산이다.**"""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def candidate_tile_keys(source, *, grid_dir) -> list[tuple[str, bool]]:
    """규약 규칙이 낳는 **후보 키 전부** — `(키, 기준 격자를 썼는가)`. 최대 둘이다.

    ⚠ **경로를 지어내는 것이 아니다** — 후보는 계약의 키 규칙(`map_tile_content_key`)과
    승격된 변환 설정(`〈294〉`)만으로 나온다. 그 둘 밖의 이름은 이 함수가 만들 수 없다.

    ⚠ **`used_reference_grid` 를 D7 이 알 수 없다** — 그것은 D5 의 파서가 포맷별로 내리는
    판정이고 D7 에 그 사다리가 없다. 지어내지 않고 **후보 둘을 다 낸다.** 읽는 쪽
    (`value_lookup.find_tile`)은 자리에 실재하는 것을 고르고, 판독기는 **둘 다 「닿는다」로
    센다** — 어느 쪽으로 구웠든 그 주체가 낳을 수 있는 이름이기 때문이다.
    """
    digest = file_digest(source)
    size = Path(source).stat().st_size
    kind = storage_layout.MAP_TILE_CONVERSION_KIND
    common = {
        "sourceDigest": digest,
        "sourceByteSize": size,
        "conversionKind": kind,
        "overviewResampling": storage_layout.MAP_TILE_OVERVIEW_RESAMPLING[kind],
        "compression": storage_layout.MAP_TILE_COMPRESSION,
    }
    grid_digests = [(storage_layout.map_tile_grid_digest(None, False), False)]
    if grid_dir is not None and Path(grid_dir).is_dir():
        with_grid = storage_layout.map_tile_grid_digest(grid_dir, True)
        if with_grid not in [g for g, _ in grid_digests]:
            grid_digests.append((with_grid, True))
    return [(storage_layout.map_tile_content_key(gridDigest=g, **common), used)
            for g, used in grid_digests]


def reach(subjects: Iterable[Subject]) -> Reach:
    """주체 전부를 키로 옮긴다. **못 옮긴 주체는 세어서 드러낸다** — 조용히 빼지 않는다."""
    ds: dict[str, list[str]] = {}
    up: dict[str, list[str]] = {}
    st: dict[str, list[str]] = {}
    bad: list[Uncomputable] = []
    seen = 0
    for s in subjects:
        seen += 1
        try:
            keys = candidate_tile_keys(s.source, grid_dir=s.grid_dir)
        except (OSError, ValueError) as e:
            bad.append(Uncomputable(s.file_id, f"{type(e).__name__}: {e}"))
            continue
        bucket = {ORIGIN_DATASET: ds, ORIGIN_UPLOAD: up}.get(s.origin, st)
        for key, _used in keys:
            bucket.setdefault(key, []).append(s.file_id)
    return Reach(dataset_keys={k: tuple(v) for k, v in ds.items()},
                 upload_keys={k: tuple(v) for k, v in up.items()},
                 uncomputable=tuple(bad), subjects_seen=seen,
                 storage_keys={k: tuple(v) for k, v in st.items()})


def grade(cache_key: str, reached: Reach) -> Verdict:
    """한 타일의 등급. **입력은 키와 재계산 결과뿐이다** — 사이드카를 보지 않는다.

    ⚠ 판정 불가로 떨어지지 않는다(완료 정의 ⑶). 판정을 못 할 상태는 등급이 아니라
    **예외**다 — 등급표 안에 숨기면 보류에 섞여 영영 안 보인다.
    """
    if not reached.is_decidable():
        raise ReaderNotReady(
            f"주체 {reached.subjects_seen}건 · 계산 불가 {len(reached.uncomputable)}건 — "
            "판정을 시작하지 않는다. 못 센 것을 「고아」로 세면 그것이 오삭제의 근거가 된다")
    if cache_key in reached.dataset_keys:
        return Verdict(GRADE_LIVE, "등록된 데이터셋의 본체가 이 키를 낳는다",
                       reached.dataset_keys[cache_key])
    if cache_key in reached.upload_keys:
        return Verdict(GRADE_UPLOAD_ONLY, "미등록 접수분만 이 키를 낳는다 (등록 전)",
                       reached.upload_keys[cache_key])
    if cache_key in reached.storage_keys:
        # **닿는다 — 그러나 등록 여부는 모른다.** 원장이 없는 자리(`ORIGIN_STORAGE`)에서
        # 모은 주체라 「등록된 데이터셋」인지 「등록 전 접수분」인지를 D7 이 가를 수 없다.
        # ⚠ 회수 판정에는 차이가 없다 — 둘 다 **지우지 않는다.** 사유 문구가 그 사실을
        #   드러낸 채로 남는 것이 요점이고, 모르는 것을 아는 것처럼 적지 않는다.
        return Verdict(GRADE_LIVE,
                       "자리의 주체가 이 키를 낳는다 — 등록 여부는 D7 이 모른다 (원장 없음)",
                       reached.storage_keys[cache_key])
    return Verdict(GRADE_ORPHAN,
                   "지금의 어느 주체도 이 키를 낳지 않는다 — 키가 갈렸거나 원본이 사라졌다")


def scan_tiles(previews_root) -> list[TileArtifact]:
    """자리에서 **`tile-` 벌만** 골라 키별로 묶는다. 렌더 산출물은 건드리지 않는다.

    ⚠ `ownership.scan()` 을 부르지 않는다 — 그 함수는 자리 전체를 읽고 사이드카를 싣는데,
    타일에는 사이드카가 없고 렌더 산출물은 이 판독의 대상이 아니다(완료 정의 ⑷).
    """
    root = Path(previews_root)
    buckets: dict[str, list[Path]] = {}
    for p in sorted(root.iterdir() if root.is_dir() else []):
        if p.is_file() and p.stem.startswith(MAP_TILE_PREFIX):
            buckets.setdefault(p.stem, []).append(p)
    out: list[TileArtifact] = []
    for key, paths in sorted(buckets.items()):
        out.append(TileArtifact(cache_key=key, paths=tuple(paths),
                                mtime=min(p.stat().st_mtime for p in paths)))
    return out


def subjects_from_storage(storage_root) -> list[Subject]:
    """**원장을 열지 않고** 저장소 루트에서 주체를 모은다 (`TL-1` ⑹ 의 입력).

    **왜 이것이 「살아 있는 주체」인가 — 지어낸 것이 아니라 이 레포가 이미 그렇게 산다.**
      ⑴ 규약 축자 — 「그리는 쪽(D7)에는 원장이 없어 **디렉터리가 곧 사실**」
         (`kernel/storage_layout` 서두 「`targetId` 가 무엇인가」).
      ⑵ core-api 가 그 사실을 **유지한다** — 원장에서 사라진 파일은 바이트도 치운다
         (`services/core-api/src/colab_core/app/routes/ingestion.py` `_discard()` 축자:
         「원장에서 사라진 격자의 **바이트도** 치운다 … 읽는 쪽(`viz-render`)에는 원장이
         없어 **폴더가 곧 사실**이라」).
      ⑶ D7 이 그릴 때 쓰는 자리도 **이 자리 하나**다(`ports/source.FilesystemSourcePort`).
         그리는 입력과 판독하는 입력이 갈리면 「그려지는데 고아」가 성립한다.

    ⚠ **출신은 `ORIGIN_STORAGE` 다** — 배치가 등록 전후를 가르지 않으므로 둘 중 하나로
      찍지 않는다. 회수 판정은 「닿는가」 하나라 이 모름이 지우는 쪽으로 기울지 않는다.
    ⚠ **격자는 주체가 아니다** — `grid/` 아래는 좌표를 준 재료이고, 타일 키의 본체가 아니다.
      대신 그 자리를 `grid_dir` 로 물려 후보 키 둘이 다 나오게 한다(하나만 내면 나머지가
      **고아로 둔갑한다**).
    ⚠ **없는 자리를 「비어 있다」로 읽지 않는다** — 루트가 없으면 빈 목록이고, 빈 목록은
      `reach()` 가 `is_decidable()` 거짓으로 받아 **판정 자체를 시작하지 않는다**.
    """
    root = storage_layout.uploads_root(storage_root)
    out: list[Subject] = []
    if not Path(root).is_dir():
        return out
    for target in sorted(Path(root).iterdir()):
        if not target.is_dir():
            continue
        grid = target / storage_layout.GRID_DIRNAME
        for body in sorted(target.iterdir()):
            if not body.is_file() or body.name == "desktop.ini":
                continue
            out.append(Subject(file_id=body.name, origin=ORIGIN_STORAGE, source=body,
                               grid_dir=grid if grid.is_dir() else None))
    return out


def tally(tiles: Sequence[TileArtifact], reached: Reach) -> Tally:
    """네 등급 계수. **회차마다 재현 가능**해야 한다 — 순서는 `GRADES` 가 고정한다."""
    if not reached.is_decidable():
        raise ReaderNotReady(
            f"주체 {reached.subjects_seen}건 · 계산 불가 {len(reached.uncomputable)}건 — "
            "계수를 내지 않는다. 판정하지 못한 회차를 0 으로 적으면 그것이 green-by-skip 이다")
    counts = {g: 0 for g in GRADES}
    verdicts: dict[str, Verdict] = {}
    for t in tiles:
        v = grade(t.cache_key, reached)
        counts[v.grade] += 1
        verdicts[t.cache_key] = v
    assert counts[GRADE_UNDECIDABLE] == 0, "타일은 판정 불가로 떨어지지 않는다 (완료 정의 ⑶)"
    return Tally(counts=counts, verdicts=verdicts)


def unreachable_keys(tiles: Sequence[TileArtifact], reached: Reach) -> tuple[str, ...]:
    """**지목만 한다.** 이 목록이 회수 대상의 후보이지 회수 명령이 아니다."""
    t = tally(tiles, reached)
    return tuple(k for k, v in sorted(t.verdicts.items()) if v.grade == GRADE_ORPHAN)


def unreachable_rows(tiles: Sequence[TileArtifact], reached: Reach, *,
                     now: float | None = None) -> list[dict]:
    """못 닿는 키 ＋ **나이** — 「언제부터 자리에 있었나」가 회수 판정의 재료다."""
    import time as _time

    at = _time.time() if now is None else now
    keys = set(unreachable_keys(tiles, reached))
    rows = []
    for t in tiles:
        if t.cache_key not in keys:
            continue
        rows.append({
            "cache_key": t.cache_key,
            "age_days": round((at - t.mtime) / 86400.0, 2),
            "mtime_iso": _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime(t.mtime)),
            "size_bytes": sum(p.stat().st_size for p in t.paths),
            "files": len(t.paths),
        })
    return sorted(rows, key=lambda r: (-r["age_days"], r["cache_key"]))
