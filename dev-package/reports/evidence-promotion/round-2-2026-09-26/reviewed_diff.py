"""두 payload 의 **reviewed 사실**(`facts`)을 데이터셋마다 대조한다 — dev 반영 시 사라지는 확정값이 있는가.

2026-09-26 Ted 「PR #174 수정」 — 이 payload 를 dev 에 실었을 때 reviewed 키가 하나도 사라지면 안 된다.
적재기(`dataset_evidence_apply.py`)는 파일마다 `facts` 를 통째로 교체하므로, 옛 payload 에 있던 키가
새 payload 에서 빠지면 dev 에서 그 확정값이 지워진다. 이 스크립트가 그 수를 센다.

  python3 reviewed_diff.py <옛 payload> <새 payload> [--json <산출 경로>]
종료코드: 0 사라진 키 0 · 1 사라진 키 ≥1 · 78 입력을 못 읽음.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("old", type=pathlib.Path)
    ap.add_argument("new", type=pathlib.Path)
    ap.add_argument("--json", type=pathlib.Path)
    args = ap.parse_args()
    try:
        old = {r["seq"]: r for r in json.loads(args.old.read_text(encoding="utf-8"))["datasets"]}
        new = {r["seq"]: r for r in json.loads(args.new.read_text(encoding="utf-8"))["datasets"]}
    except (OSError, ValueError, KeyError) as exc:
        print(f"준비 실패: {exc}", file=sys.stderr)
        return 78
    removed, added, changed = [], [], []
    for seq in sorted(set(old) | set(new)):
        before, after = (old.get(seq) or {}).get("facts", {}), (new.get(seq) or {}).get("facts", {})
        for key in sorted(set(before) - set(after)):
            removed.append({"seq": seq, "key": key, "old": before[key]})
        for key in sorted(set(after) - set(before)):
            added.append({"seq": seq, "key": key, "new": after[key]})
        for key in sorted(set(before) & set(after)):
            if before[key] != after[key]:
                changed.append({"seq": seq, "key": key, "old": before[key], "new": after[key]})
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()  # noqa: E731
    result = {"schema": "colab-reviewed-diff/1",
              "old": {"path": str(args.old), "sha256": digest(args.old)},
              "new": {"path": str(args.new), "sha256": digest(args.new)},
              "datasets": {"old": len(old), "new": len(new)},
              "removedReviewedKeys": len(removed), "addedReviewedKeys": len(added),
              "changedReviewedKeys": len(changed),
              "removed": removed, "added": added, "changed": changed}
    text = json.dumps(result, ensure_ascii=False, indent=1) + "\n"
    if args.json:
        args.json.write_text(text, encoding="utf-8")
    print(f"사라진 reviewed 키 {len(removed)} · 추가 {len(added)} · 값 변경 {len(changed)}")
    for row in added:
        print(f"  + seq {row['seq']} {row['key']} = {row['new']!r}")
    for row in changed:
        print(f"  ~ seq {row['seq']} {row['key']}: {row['old']!r} → {row['new']!r}")
    for row in removed:
        print(f"  - seq {row['seq']} {row['key']} (옛 값 {row['old']!r})")
    return 0 if not removed else 1


if __name__ == "__main__":
    raise SystemExit(main())
