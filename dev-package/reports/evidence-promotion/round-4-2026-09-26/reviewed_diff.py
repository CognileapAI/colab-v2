"""두 payload 의 reviewed 사실(`facts`)을 대조한다 — dev 반영 때 사라지는 확정값을 **이름 붙여** 드러낸다.

2회차 `round-2-2026-09-26/reviewed_diff.py` 와 같은 셈이다(적재기는 파일마다 `facts` 를 통째로 교체하므로 옛
payload 에 있던 키가 새 payload 에서 빠지면 dev 에서 그 확정값이 지워진다 — PR #174 규칙). 다른 점은
Ted 가 **명시 승인한 제거**를 `--approved seq:key` 로 받아 `reviewedRemovals` 절에 따로 적는 것이다.
승인 목록 밖의 제거가 하나라도 있으면 판정 실패다 — 조용히 지우지 않는다.

  python3 reviewed_diff.py <옛 payload> <새 payload> --approved 4:cadence --json <산출 경로>
종료코드: 0 승인 밖 제거 0 · 1 승인 밖 제거 ≥1 또는 승인했는데 제거되지 않음 · 78 입력을 못 읽음.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

APPROVAL = ("Ted 2026-09-26 「전부 권고대로」 — intent 2026-09-26-cadence-range-predicate 질문 2: "
            "rn15_sample(seq 4) 의 정본 문장이 자기 주기를 말하지 않아 reviewed cadence 를 거두고 "
            "계보 초안(rule:cadence-from-lineage-parent)으로 내린다")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("old", type=pathlib.Path)
    ap.add_argument("new", type=pathlib.Path)
    ap.add_argument("--approved", action="append", default=[])
    ap.add_argument("--json", type=pathlib.Path)
    args = ap.parse_args()
    try:
        old = dict((r["seq"], r) for r in json.loads(args.old.read_text(encoding="utf-8"))["datasets"])
        new = dict((r["seq"], r) for r in json.loads(args.new.read_text(encoding="utf-8"))["datasets"])
        approved = set((int(a.split(":")[0]), a.split(":")[1]) for a in args.approved)
    except (OSError, ValueError, KeyError, IndexError) as exc:
        print(f"준비 실패: {exc}", file=sys.stderr)
        return 78
    removed, approved_removed, added, changed = [], [], [], []
    for seq in sorted(set(old) | set(new)):
        before = (old.get(seq) or dict()).get("facts", dict())
        after = (new.get(seq) or dict()).get("facts", dict())
        draft_after = (new.get(seq) or dict()).get("draftProvenance", dict())
        for key in sorted(set(before) - set(after)):
            row = dict(seq=seq, name=(old.get(seq) or dict()).get("name"), key=key, old=before[key])
            if (seq, key) in approved:
                row.update(approval=APPROVAL, nowDraft=(new.get(seq) or dict()).get("draftFacts", dict()).get(key),
                           nowDraftProvenance=draft_after.get(key))
                approved_removed.append(row)
            else:
                removed.append(row)
        for key in sorted(set(after) - set(before)):
            added.append(dict(seq=seq, key=key, new=after[key]))
        for key in sorted(set(before) & set(after)):
            if before[key] != after[key]:
                changed.append(dict(seq=seq, key=key, old=before[key], new=after[key]))
    missing = sorted(approved - set((r["seq"], r["key"]) for r in approved_removed))
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()  # noqa: E731
    result = dict(schema="colab-reviewed-diff/2",
                  old=dict(path=str(args.old), sha256=digest(args.old)),
                  new=dict(path=str(args.new), sha256=digest(args.new)),
                  datasets=dict(old=len(old), new=len(new)),
                  removedReviewedKeys=len(removed), approvedRemovals=len(approved_removed),
                  addedReviewedKeys=len(added), changedReviewedKeys=len(changed),
                  reviewedRemovals=approved_removed, removed=removed, added=added, changed=changed,
                  approvedButNotRemoved=[f"{s}:{k}" for s, k in missing])
    text = json.dumps(result, ensure_ascii=False, indent=1) + "\n"
    if args.json:
        args.json.write_text(text, encoding="utf-8")
    print(json.dumps(dict((k, result[k]) for k in ("removedReviewedKeys", "approvedRemovals", "addedReviewedKeys",
                                                   "changedReviewedKeys", "approvedButNotRemoved")), ensure_ascii=False))
    return 1 if removed or missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
