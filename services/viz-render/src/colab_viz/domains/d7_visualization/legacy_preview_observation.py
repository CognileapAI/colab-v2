"""TL-2 S3 legacy preview observation. This module has no delete operation."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import ownership

MAX_SIDECAR_BYTES = 1 << 20
PREVIEW_SUFFIXES = frozenset({".png", ".webp", ".json", ".pgw"})


class ObservationNotReady(RuntimeError):
    pass


def _prefix(value: str) -> str:
    clean = str(value).strip("/")
    if clean != "previews" or "/" in clean:
        raise ObservationNotReady("관측 prefix는 previews/ 하나여야 한다")
    return clean + "/"


def _read_sidecar(client: Any, key: str, listed_size: int) -> dict:
    if listed_size < 0 or listed_size > MAX_SIDECAR_BYTES:
        raise ObservationNotReady(f"sidecar 크기 범위 위반: {key}")
    try:
        head_size, etag = client.head_object(key)
        if int(head_size) != int(listed_size) or not str(etag).strip():
            raise ObservationNotReady(f"목록/HEAD 크기 또는 버전 불일치: {key}")
        stream = client.get_object_stream(key, chunk_size=64 * 1024, expected_etag=etag)
        chunks, received = [], 0
        try:
            for chunk in stream:
                received += len(chunk)
                if received > head_size:
                    raise ObservationNotReady(f"HEAD보다 큰 sidecar 응답: {key}")
                chunks.append(chunk)
        finally:
            close = getattr(stream, "close", None)
            if callable(close):
                close()
        if received != head_size:
            raise ObservationNotReady(f"HEAD보다 짧은 sidecar 응답: {key}")
        doc = json.loads(b"".join(chunks))
    except ObservationNotReady:
        raise
    except Exception as exc:
        raise ObservationNotReady(f"sidecar metadata 실패: {key} ({type(exc).__name__})") from None
    if not isinstance(doc, dict):
        raise ObservationNotReady(f"sidecar JSON object가 아니다: {key}")
    return doc


def observe(client: Any, ledger: ownership.Ledger, *, prefix: str = "previews",
            observed_at: str | None = None) -> dict:
    """List exact ``previews/`` and GET only JSON sidecars; never mutates S3 or DB."""
    if ledger.is_structurally_empty():
        raise ObservationNotReady("원장 두 ID 집합이 모두 비었다")
    root = _prefix(prefix)
    buckets: dict[str, list[tuple[str, int]]] = {}
    try:
        listed, seen_objects = [], set()
        for item in client.list_objects(root):
            marker = (str(item[0]), int(item[1]))
            if marker[0] in seen_objects:
                raise ObservationNotReady(
                    "S3 pagination이 같은 객체를 반복했다 — 다음 page를 받지 못했다")
            seen_objects.add(marker[0])
            listed.append(marker)
    except Exception as exc:
        raise ObservationNotReady(f"S3 목록 실패 ({type(exc).__name__})") from None
    if not listed:
        raise ObservationNotReady("previews/ 목록이 0건이다")
    for key, raw_size in listed:
        if not key.startswith(root):
            raise ObservationNotReady("S3가 요청 prefix 밖 객체를 돌려줬다")
        rel = key[len(root):]
        path = Path(rel)
        if len(path.parts) != 1 or not path.name:
            raise ObservationNotReady(f"previews/가 flat 구조가 아니다: {key}")
        if path.suffix == ".tif" and path.stem.startswith(ownership.MAP_TILE_PREFIX):
            continue
        if path.suffix not in PREVIEW_SUFFIXES:
            raise ObservationNotReady(f"알 수 없는 preview 확장자: {key}")
        buckets.setdefault(path.stem, []).append((key, int(raw_size)))

    groups, snapshot = [], []
    for cache_key, objects in sorted(buckets.items()):
        suffixes = {Path(key).suffix for key, _ in objects}
        if not suffixes.intersection({".png", ".webp"}):
            raise ObservationNotReady(f"이미지 없는 preview 벌: {cache_key}")
        doc = None
        json_items = [(key, size) for key, size in objects if Path(key).suffix == ".json"]
        if len(json_items) > 1:
            raise ObservationNotReady(f"sidecar 중복: {cache_key}")
        if json_items:
            doc = _read_sidecar(client, *json_items[0])
        paths = tuple(Path(key[len(root):]) for key, _ in objects)
        groups.append(ownership.ArtifactGroup(cache_key, paths, doc))
        for key, size in sorted(objects):
            snapshot.append({"cache_key": cache_key, "extension": Path(key).suffix,
                             "size_bytes": size})

    try:
        ownership_tally = ownership.tally(groups, ledger)
        legacy = ownership.legacy_tally(groups, ledger)
    except (ownership.SidecarContractViolation, ownership.LegacyObservationNotReady) as exc:
        raise ObservationNotReady(str(exc)) from None
    undecidable = sum(legacy.counts.values())
    unreachable = (legacy.counts[ownership.LEGACY_SIDECAR_ABSENT]
                   + legacy.counts[ownership.LEGACY_SOURCE_LEDGER_ABSENT])
    return {
        "schema": "colab-tl2-observation/1",
        "observed_at": observed_at or datetime.now(timezone.utc).isoformat(),
        "prefix": root,
        "objects": len(listed),
        "preview_groups": len(groups),
        "legacy_groups": undecidable,
        "modern_groups": len(groups) - undecidable,
        "ownership_counts": ownership_tally.counts,
        "legacy_counts": legacy.counts,
        "rebake_unreachable": unreachable,
        "key_sets": {"legacy": sorted(legacy.verdicts),
                     "rebake_unreachable": sorted(legacy.unreachable_keys)},
        "metadata_snapshot": snapshot,
        "deleted": 0,
    }


def _ids(path: str) -> frozenset[str]:
    return frozenset(line.strip() for line in Path(path).read_text(encoding="utf-8").splitlines()
                     if line.strip())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="TL-2 read-only S3 legacy preview observation")
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--region", required=True)
    parser.add_argument("--d3-ids", required=True)
    parser.add_argument("--d5-ids", required=True)
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--prefix", default="previews")
    args = parser.parse_args(argv)
    from ...kernel.s3 import S3Client
    ledger = ownership.Ledger(_ids(args.d3_ids), _ids(args.d5_ids))
    try:
        result = observe(S3Client(bucket=args.bucket, region=args.region), ledger, prefix=args.prefix)
    except ObservationNotReady as exc:
        print(f"::관측준비실패::{exc}")
        return 78
    out = Path(args.snapshot)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = result["legacy_counts"]
    print("TL-2 관측 — 객체 {objects} · preview {preview_groups}벌 · 구판 {legacy_groups}벌 "
          "(사이드카 부재 {sidecar} · 원천 원장 부재 {ledger} · 원장 있음 {present}) · "
          "재굽기 불가 {unreachable} · 삭제 0건".format(
              **result, sidecar=counts[ownership.LEGACY_SIDECAR_ABSENT],
              ledger=counts[ownership.LEGACY_SOURCE_LEDGER_ABSENT],
              present=counts[ownership.LEGACY_SOURCE_LEDGER_PRESENT],
              unreachable=result["rebake_unreachable"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
