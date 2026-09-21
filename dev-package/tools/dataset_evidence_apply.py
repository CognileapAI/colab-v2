"""생성된 검색 근거 payload 를 한 트랜잭션으로 싣는다. **멱등**이고 재시드가 아니다.

⚠ **초안(규칙 추론) 사실은 쓰지 않는다** — 2026-09-21 Ted 결정 1. payload 의 `draftFacts` 는
`d3_search_evidence` 에 실리지 않는다. 그 표는 `file_id` 가 PK 이고 `status` 가 행 단위라
한 파일이 reviewed 와 draft 를 함께 가질 수 없고, 행을 통째로 draft 로 내리면 정본 전재
사실까지 조건 검색에서 사라진다. 이 스크립트는 `draft_withheld` 로 그 칸 수만 보고한다.
승격 구조(히트 측정 → 승격·폐기)는 별도 intent 의 몫이며 `rule:<ID>` locator 로 찾아온다.

무엇을 쓰나 (전부 추가·정합화이고 삭제가 없다):
  · `d3_search_evidence` — 데이터셋의 **본체 파일마다** 한 행(upsert). 조건 검색이 읽는 자리다.
  · `d3_dataset_description.topic` — 프로젝트 4 ↔ topic CHECK 6값 정합화(2026-09-15 후속 2번).
  · `d3_dataset.source_label` — 정본이 원천을 문면으로 고정한 9건만.

멱등: 이미 같은 `facts`·`source_sha256`·`status`·`file_revision` 이 실려 있으면 **쓰지 않는다**
(`revision` 을 괜히 올리지 않는다 — 올리면 낙관적 잠금의 `expectedRevision` 이 흔들린다).
파일 본문이 바뀌어 `content_revision` 이 오르면 근거는 그 자리에서 stale 이 되고, 이 스크립트가
새 `file_revision` 으로 다시 실어 준다.

DEV 적용은 **사용자 몫**이다(Ted 결정 5 — ㈎ 로컬 검증, DEV 적재는 별도 승인).
이 파일은 명령과 되돌림 경로를 제공할 뿐 스스로 DEV 에 붙지 않는다.

쓰는 법
  # ① 셈만 본다 — 아무것도 쓰지 않는다
  python3 dev-package/tools/dataset_evidence_apply.py --database-url "$URL" --reviewer <ULID> --dry-run
  # ② 실제 적재 (한 트랜잭션)
  python3 dev-package/tools/dataset_evidence_apply.py --database-url "$URL" --reviewer <ULID>
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_PAYLOADS = HERE / "generated" / "dataset-evidence-payloads.json"

_FIND_DATASET = """SELECT d.id AS dataset_id, d.lab_id AS lab_id, d.source_label AS source_label,
 dd.topic AS topic FROM d3_dataset d JOIN d3_dataset_description dd ON dd.dataset_id = d.id
 WHERE dd.name = :name AND d.deleted_at IS NULL"""

_BODY_FILES = """SELECT id AS file_id, content_revision FROM d3_file
 WHERE dataset_id = :dataset_id AND kind = '본체' ORDER BY created_at, id"""

_EXISTING = """SELECT facts, source_sha256, status, file_revision, revision
 FROM d3_search_evidence WHERE file_id = :file_id"""

_INSERT = """INSERT INTO d3_search_evidence
 (file_id, lab_id, dataset_id, file_revision, revision, status, facts,
  source_label, source_locator, source_text, source_sha256, reviewed_by, reviewed_at)
 VALUES (:file_id, :lab_id, :dataset_id, :file_revision, 1, :status, CAST(:facts AS jsonb),
  :source_label, :source_locator, :source_text, :source_sha256, :reviewed_by,
  CASE WHEN :status = 'reviewed' THEN now() ELSE NULL END)"""

_UPDATE = """UPDATE d3_search_evidence SET file_revision = :file_revision,
 revision = revision + 1, status = :status, facts = CAST(:facts AS jsonb),
 source_label = :source_label, source_locator = :source_locator, source_text = :source_text,
 source_sha256 = :source_sha256, reviewed_by = :reviewed_by,
 reviewed_at = CASE WHEN :status = 'reviewed' THEN now() ELSE NULL END, updated_at = now()
 WHERE file_id = :file_id"""

_SET_TOPIC = ("UPDATE d3_dataset_description SET topic = :topic "
              "WHERE dataset_id = :dataset_id AND topic IS DISTINCT FROM :topic")
_SET_SOURCE_LABEL = ("UPDATE d3_dataset SET source_label = :source_label "
                     "WHERE id = :dataset_id AND source_label IS DISTINCT FROM :source_label")


def apply_payloads(execute, payloads: dict, *, reviewer_id: str, dry_run: bool = False) -> dict:
    """`execute(sql, params) -> list[dict]` 하나만 받는다 — 시험은 앱 롤 세션을, DEV 명령은
    한 트랜잭션 연결을 넘긴다. 같은 SQL 이 두 자리에서 돈다(적용기를 두 벌로 두지 않는다)."""
    report = {"datasets": 0, "missing": [], "evidence": 0, "evidence_unchanged": 0,
              "topic": 0, "source_label": 0, "files": 0, "draft_withheld": 0}
    for row in payloads["datasets"]:
        found = execute(_FIND_DATASET, {"name": row["name"]})
        if not found:
            report["missing"].append(row["name"])
            continue
        if len(found) > 1:
            raise SystemExit(f"이름이 겹치는 데이터셋이 {len(found)}건이다: {row['name']!r}. "
                             "이름으로 고를 수 없으면 적재하지 않는다.")
        dataset = found[0]
        report["datasets"] += 1
        report["draft_withheld"] += len(row.get("draftFacts") or {})
        source = row["source"]
        facts_json = json.dumps(row["facts"], ensure_ascii=False, sort_keys=True)

        if row.get("topic") and dataset["topic"] != row["topic"]:
            report["topic"] += 1
            if not dry_run:
                execute(_SET_TOPIC, {"topic": row["topic"], "dataset_id": dataset["dataset_id"]})
        if row.get("sourceLabel") and dataset["source_label"] != row["sourceLabel"]:
            report["source_label"] += 1
            if not dry_run:
                execute(_SET_SOURCE_LABEL, {"source_label": row["sourceLabel"],
                                            "dataset_id": dataset["dataset_id"]})

        for body in execute(_BODY_FILES, {"dataset_id": dataset["dataset_id"]}):
            report["files"] += 1
            params = {
                "file_id": body["file_id"], "lab_id": dataset["lab_id"],
                "dataset_id": dataset["dataset_id"],
                "file_revision": body["content_revision"], "status": row["status"],
                "facts": facts_json, "source_label": source["label"],
                "source_locator": source["locator"], "source_text": source["text"],
                "source_sha256": source["sha256"],
                "reviewed_by": reviewer_id if row["status"] == "reviewed" else None,
            }
            current = execute(_EXISTING, {"file_id": body["file_id"]})
            if current:
                same = (json.dumps(current[0]["facts"], ensure_ascii=False, sort_keys=True)
                        == facts_json
                        and current[0]["source_sha256"] == source["sha256"]
                        and current[0]["status"] == row["status"]
                        and current[0]["file_revision"] == body["content_revision"])
                if same:
                    report["evidence_unchanged"] += 1
                    continue
            report["evidence"] += 1
            if not dry_run:
                execute(_INSERT if not current else _UPDATE, params)
    return report


def _sqlalchemy_executor(session):
    from sqlalchemy import text

    def execute(statement: str, params: dict | None = None):
        result = session.execute(text(statement), params or {})
        return [dict(r) for r in result.mappings()] if result.returns_rows else []

    return execute


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", required=True,
                        help="적재 대상. **DEV 적용은 사용자 승인 뒤에만 한다.**")
    parser.add_argument("--reviewer", required=True,
                        help="reviewed 근거의 검토자 계정 ULID. d1_account 에 있어야 한다.")
    parser.add_argument("--payloads", default=str(DEFAULT_PAYLOADS))
    parser.add_argument("--dry-run", action="store_true", help="셈만 찍고 아무것도 쓰지 않는다")
    args = parser.parse_args()

    payloads = json.loads(pathlib.Path(args.payloads).read_text(encoding="utf-8"))
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    engine = create_engine(args.database_url, future=True)
    with Session(engine) as session, session.begin():
        report = apply_payloads(_sqlalchemy_executor(session), payloads,
                                reviewer_id=args.reviewer, dry_run=args.dry_run)
        if args.dry_run:
            session.rollback()
    print(json.dumps(report, ensure_ascii=False))
    if report["missing"]:
        print(f"⚠ 이름으로 못 찾은 데이터셋 {len(report['missing'])}건 — 적재하지 않았다.",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
