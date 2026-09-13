"""파일별 표식 백필 — `DL-2` 이전에 구운 산출물에 `preview-index/` 표식을 놓는다 (회부문 ⓓ5).

⛔ **`--apply` 는 Ted ⓓ5 GO 뒤에만 부른다.** 기본은 dry-run 이고, 그 실행이 내는 계수
(`사이드카`·`쌍`·`건너뜀`·`타일`)가 GO 판정의 입력이다 — 얼마나 쓸지 모르는 채로 쓰기
시작하지 않는다.

**왜 필요한가** — 표식은 `jobs.py` 가 **발행 시점**에 놓는다. 그 줄이 없던 때에 구워진
산출물에는 표식이 없고, 삭제 회수는 그 벌을 **로컬 자리 훑기로만** 찾는다. dev 의 로컬
미리보기 자리는 LRU 캐시라 밀려난 벌은 **어느 쪽으로도 안 잡힌다** — 그 구멍을 한 번 메운다.

**무엇을 하지 않는가**
  · **지우지 않는다.** 이 모듈에 `delete_objects` 호출이 0건이다(음성 시험이 잠근다).
  · **접두 밖을 보지 않는다.** 목록 조회는 `previews/` 하나이고 버킷 전체 스캔이 없다.
  · **그림을 읽지 않는다.** GET 하는 것은 `.json` 사이드카뿐이다.
  · **지도 타일(`tile-`)에 표식을 놓지 않는다.** 그 벌은 회수 대상이 아니다.
  · **못 읽은 것에 표식을 지어내지 않는다** — 구판·`sources` 없음은 건너뛰고 센다.

**멱등** — 표식 PUT 은 같은 키에 0바이트를 다시 쓰는 것이라 몇 번 돌려도 같은 상태다.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Any, Iterable

from ..domains.d7_visualization import ownership
from ..domains.d7_visualization.legacy_preview_observation import (
    MAX_SIDECAR_BYTES, ObservationNotReady, _read_sidecar,
)
from ..kernel.storage_layout import MAP_TILE_KEY_PREFIX, preview_index_key

SIDECAR_SUFFIX = ".json"


@dataclass(frozen=True)
class BackfillReport:
    """한 번 돈 결과. **계수를 갈라 낸다** — 합계 하나로는 무엇을 못 읽었는지 모른다."""
    sidecars: int          #: 접두에서 만난 `.json` 개수(타일 포함)
    pairs: int             #: 놓을(놓은) `(fileId, contentKey)` 표식 수
    skipped: int           #: 구판·`sources` 없음·못 읽음 — 표식을 놓지 않은 벌
    tiles: int             #: 지도 타일이라 건너뛴 벌
    applied: bool          #: `--apply` 였는가. `False` 면 PUT 0건이다
    samples: tuple[str, ...] = ()   #: 표본 표식 키 몇 개(사람이 눈으로 대조할 자리)

    def summary(self) -> str:
        mode = "적용" if self.applied else "dry-run(쓰기 0건)"
        return (f"backfill-preview-index {mode} — 사이드카 {self.sidecars} · "
                f"표식 {self.pairs} · 건너뜀 {self.skipped} · 타일 {self.tiles}")


def _content_key(object_key: str, previews_prefix: str) -> str | None:
    """`previews/{contentKey}.json` 에서 내용 키만 떼어 낸다. 하위 경로는 대상이 아니다."""
    head = f"{previews_prefix}/"
    if not object_key.startswith(head) or not object_key.endswith(SIDECAR_SUFFIX):
        return None
    tail = object_key[len(head):-len(SIDECAR_SUFFIX)]
    # `previews/` 아래는 평평하다(`legacy_preview_observation.observe` 가 그것을 잰다).
    return tail if tail and "/" not in tail else None


def _sidecar_doc(client: Any, key: str, size: int) -> dict | None:
    if size < 0 or size > MAX_SIDECAR_BYTES:
        return None
    try:
        doc = _read_sidecar(client, key, int(size))
    except ObservationNotReady:
        return None
    except Exception:       # noqa: BLE001 — 못 읽은 것은 「없다」이지 「표식을 지어도 된다」가 아니다
        return None
    return doc if isinstance(doc, dict) else None


def _decidable(doc: dict) -> bool:
    """판정 가능한 판인가 — `ownership._is_legacy` 와 **같은 규칙**을 부른다.

    여기서 판 번호를 다시 적으면 그 순간 「구판」의 정의가 둘이 되고, 갈린 쪽이 놓은
    표식은 회수가 못 읽는 자리를 가리킨다.
    """
    return not ownership._is_legacy(doc)


def run(*, client: Any, previews_prefix: str = "previews",
        apply: bool = False, sample_limit: int = 5) -> BackfillReport:
    """한 바퀴. **기본은 dry-run** 이고 `apply=True` 일 때만 표식을 PUT 한다."""
    prefix = previews_prefix.strip("/")
    sidecars = skipped = tiles = 0
    pairs: list[tuple[str, str]] = []

    for object_key, size in client.list_objects(f"{prefix}/"):
        content_key = _content_key(str(object_key), prefix)
        if content_key is None:
            continue
        sidecars += 1
        if content_key.startswith(MAP_TILE_KEY_PREFIX):
            tiles += 1
            continue
        doc = _sidecar_doc(client, str(object_key), int(size))
        if doc is None or not _decidable(doc):
            skipped += 1
            continue
        sources = ownership.source_file_ids(doc)
        if not sources:
            skipped += 1
            continue
        pairs.extend((file_id, content_key) for file_id in sources)

    if apply:
        _put_markers(client, pairs)
    samples = tuple(preview_index_key(f, k) for f, k in pairs[:sample_limit])
    return BackfillReport(sidecars=sidecars, pairs=len(pairs), skipped=skipped,
                          tiles=tiles, applied=apply, samples=samples)


def _put_markers(client: Any, pairs: Iterable[tuple[str, str]]) -> None:
    """표식은 **0바이트 객체**다 — 자리 자체가 사실이라 담을 값이 없다.

    싱크(`S3PreviewSink.index`)와 **같은 자리 계산기**(`preview_index_key`)를 쓴다.
    """
    for file_id, content_key in pairs:
        client.put_object(preview_index_key(file_id, content_key), b"", "application/json")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="미리보기 산출물에 파일별 표식(preview-index/)을 백필한다. 기본은 dry-run.")
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--region", required=True)
    parser.add_argument("--previews-prefix", default="previews")
    parser.add_argument("--apply", action="store_true",
                        help="실제로 표식을 놓는다. ⛔ Ted ⓓ5 GO 뒤에만 쓴다.")
    parser.add_argument("--json", action="store_true", help="계수를 JSON 한 줄로 낸다.")
    args = parser.parse_args(argv)

    from ..kernel.s3 import S3Client

    report = run(client=S3Client(bucket=args.bucket, region=args.region),
                 previews_prefix=args.previews_prefix, apply=args.apply)
    if args.json:
        print(json.dumps({"sidecars": report.sidecars, "pairs": report.pairs,
                          "skipped": report.skipped, "tiles": report.tiles,
                          "applied": report.applied, "samples": list(report.samples)},
                         ensure_ascii=False))
    else:
        print(report.summary())
        for key in report.samples:
            print(f"  표본 {key}")
    return 0


__all__ = ["BackfillReport", "main", "run"]


if __name__ == "__main__":       # pragma: no cover — 사람이 부르는 자리
    raise SystemExit(main())
