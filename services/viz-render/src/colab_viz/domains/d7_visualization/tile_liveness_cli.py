"""생존 판독기의 **별도 진입점** (`TL-1` 완료 정의 ⑷ 축자).

`ownership.scan()`·`grade()` 를 넓히지 않는다 — 판독은 이 문으로 들어온다.

    python -m colab_viz.domains.d7_visualization.tile_liveness_cli \\
        --previews /srv/viz-previews --storage /var/lib/colab --subjects -

**주체 목록은 원장이 준다** — 이 진입점은 DB 를 열지 않는다(D7 에 원장이 없다 · 불변규칙 1).
부르는 쪽이 읽기 전용 질의로 내려 TSV 로 물린다. 한 줄 = 주체 하나 ·
`<출신>\\t<file_id>\\t<storage_key>` (출신 = `데이터셋 파일` | `접수분`).

⛔ **아무것도 지우지 않는다.** 못 닿는 키를 **지목**할 뿐이고, 회수는 `invalidation` 한 자리이며
  그 결선은 대장 `TL-1` ⑹ 에 `[미확인]` 로 남아 있다.

**세 상태로 끝난다** — 종료 코드가 그것이다.
  `0`  판정했다. 계수를 냈다 (못 닿는 벌이 있어도 0 — **판독이지 판결이 아니다**)
  `78` **red(준비)** — 주체 0건이거나 못 연 주체가 있다. 판정을 시작하지 않았다
  `2`  부르는 법이 틀렸다 (자리·저장소 루트가 없다)
"""
from __future__ import annotations

import sys
from pathlib import Path

from ...kernel import storage_layout
from . import tile_liveness as tl

READINESS_EXIT = 78


def parse_subjects(text: str, storage_root: Path) -> list[tl.Subject]:
    """TSV 를 주체로 옮긴다. **모르는 출신·모양은 지어내지 않고 예외다.**"""
    out: list[tl.Subject] = []
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            raise ValueError(f"{lineno}행: 열이 셋이 아니다 — <출신>\\t<file_id>\\t<storage_key>")
        origin, file_id, key = (p.strip() for p in parts)
        if origin not in (tl.ORIGIN_DATASET, tl.ORIGIN_UPLOAD):
            raise ValueError(f"{lineno}행: 모르는 출신 {origin!r}")
        segs = Path(key).parts
        if len(segs) != 3 or segs[0] != storage_layout.UPLOADS_PREFIX:
            raise ValueError(
                f"{lineno}행: 본체의 저장 키 모양이 아니다 ({key!r}) — "
                f"규약은 {storage_layout.UPLOADS_PREFIX}/{{targetId}}/{{fileId}} 다")
        out.append(tl.Subject(file_id=file_id, origin=origin,
                              source=storage_root / key,
                              grid_dir=storage_layout.grid_dir(storage_root, segs[1])))
    return out


def main(argv: list[str]) -> int:
    import argparse

    ap = argparse.ArgumentParser(prog="tile-liveness", add_help=True)
    ap.add_argument("--previews", required=True, help="미리보기 산출물 루트 (자리)")
    ap.add_argument("--storage", required=True, help="저장소 루트 — 그 아래가 접수분이다")
    ap.add_argument("--subjects", required=True, help="주체 TSV 경로 · `-` 면 표준입력")
    a = ap.parse_args(argv[1:])

    previews, storage = Path(a.previews), Path(a.storage)
    for label, p in (("자리(미리보기 루트)", previews), ("저장소 루트", storage)):
        if not p.is_dir():
            print(f"::error::{label} 가 없다: {p} — 없는 자리를 「비어 있다」로 읽지 않는다",
                  file=sys.stderr)
            return 2

    text = sys.stdin.read() if a.subjects == "-" else Path(a.subjects).read_text(encoding="utf-8")
    try:
        subjects = parse_subjects(text, storage)
    except ValueError as e:
        print(f"::error::주체 목록을 읽지 못했다 — {e}", file=sys.stderr)
        return 2

    reached = tl.reach(subjects)
    tiles = tl.scan_tiles(previews)
    print(f"# 주체 {reached.subjects_seen}건 "
          f"(데이터셋 파일 {sum(1 for s in subjects if s.origin == tl.ORIGIN_DATASET)} · "
          f"접수분 {sum(1 for s in subjects if s.origin == tl.ORIGIN_UPLOAD)}) · "
          f"자리의 타일 {len(tiles)}벌 · 키 규칙 판 {storage_layout.MAP_TILE_KEY_VERSION}")

    if not reached.is_decidable():
        for u in reached.uncomputable:
            print(f"::계산불가::{u.file_id}\t{u.reason}")
        print(f"::계산불가건수::{len(reached.uncomputable)}")
        print("::error::tile-liveness red(준비) — **판정을 시작하지 않았다.**\n"
              f"   주체 {reached.subjects_seen}건 · 키를 못 지은 주체 {len(reached.uncomputable)}건.\n"
              "   ⚠ 못 센 주체를 조용히 빼면 그 주체가 가리키던 타일이 **고아로 둔갑한다** —\n"
              "     경계에 걸린 0 을 「없다」로 읽어 전건을 고아로 센 오판이 이 레포에서 실제로 났다\n"
              "     (DATA-REFERENCE §0 M-9). 「고아」도 「판정 불가」도 아닌 **제3의 상태**다.",
              file=sys.stderr)
        return READINESS_EXIT

    t = tl.tally(tiles, reached)
    for name in tl.GRADES:
        print(f"::계수::{name}\t{t.counts[name]}")
    print(f"::타일::{len(tiles)}")
    print(f"::계산불가건수::0")
    rows = tl.unreachable_rows(tiles, reached)
    for r in rows:
        print(f"::못닿음::{r['cache_key']}\t{r['age_days']}\t{r['mtime_iso']}\t{r['size_bytes']}")

    print(f"지도 타일 생존 — 자리의 타일 {len(tiles)}벌 · "
          f"살아 있다 {t.counts[tl.GRADE_LIVE]} · "
          f"접수분에만 닿는다 {t.counts[tl.GRADE_UPLOAD_ONLY]} · "
          f"고아(못 닿는다) {t.counts[tl.GRADE_ORPHAN]} · "
          f"판정 불가 {t.counts[tl.GRADE_UNDECIDABLE]} · 계산 불가 0")
    if rows:
        print(f"  못 닿는 벌 {len(rows)} — 가장 오래된 것 {rows[0]['cache_key']} "
              f"({rows[0]['age_days']}일 · {rows[0]['mtime_iso']})")
    print("  ⛔ 이 판독은 아무것도 지우지 않았다 — 회수는 invalidation 한 자리다 (TL-1 ⑹ [미확인])")
    return 0


if __name__ == "__main__":       # pragma: no cover
    raise SystemExit(main(sys.argv))
