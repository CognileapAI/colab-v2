"""D3 file search evidence persistence and reviewed-only search input."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy import String, bindparam, text
from sqlalchemy.orm import Session

from ..kernel.ids import Ulid

_LIST = text("""SELECT f.id file_id,f.file_name,f.content_revision,e.file_revision,e.revision,
 e.status,e.facts,e.source_label,e.source_locator,e.source_text,e.source_sha256,e.reviewed_by,e.reviewed_at
 FROM d3_file f LEFT JOIN d3_search_evidence e ON e.file_id=f.id
 WHERE f.dataset_id=:dataset_id ORDER BY f.created_at,f.id""")
_LOCK_FILE = text("""SELECT id,lab_id,dataset_id,file_name,kind,content_revision FROM d3_file
 WHERE id=:file_id AND dataset_id=:dataset_id FOR UPDATE""")
_LOCK_EVIDENCE = text("SELECT revision FROM d3_search_evidence WHERE file_id=:file_id FOR UPDATE")
_INSERT = text("""INSERT INTO d3_search_evidence
 (file_id,lab_id,dataset_id,file_revision,revision,status,facts,source_label,source_locator,
  source_text,source_sha256,reviewed_by,reviewed_at)
 VALUES (:file_id,:lab_id,:dataset_id,:file_revision,1,:status,CAST(:facts AS jsonb),:source_label,
 :source_locator,:source_text,:source_sha256,:reviewed_by,
 CASE WHEN :status='reviewed' THEN now() ELSE NULL END)
 RETURNING revision,status,facts,source_label,source_locator,source_text,source_sha256,reviewed_by,reviewed_at""")
_UPDATE = text("""UPDATE d3_search_evidence SET file_revision=:file_revision,revision=revision+1,
 status=:status,facts=CAST(:facts AS jsonb),source_label=:source_label,source_locator=:source_locator,
 source_text=:source_text,source_sha256=:source_sha256,reviewed_by=:reviewed_by,
 reviewed_at=CASE WHEN :status='reviewed' THEN now() ELSE NULL END,updated_at=now()
 WHERE file_id=:file_id
 RETURNING revision,status,facts,source_label,source_locator,source_text,source_sha256,reviewed_by,reviewed_at""")
_REVIEWED = text("""SELECT e.dataset_id,e.file_id,f.file_name,f.kind file_kind,e.facts,e.source_label,
 e.source_locator,CASE WHEN :include_source_text THEN e.source_text ELSE NULL END source_text,
 e.source_sha256,e.reviewed_by,e.reviewed_at
 FROM d3_search_evidence e JOIN d3_file f
 ON f.id=e.file_id AND f.dataset_id=e.dataset_id AND f.lab_id=e.lab_id
 WHERE e.status='reviewed' AND e.file_revision=f.content_revision
 AND (:all_datasets OR e.dataset_id IN :dataset_ids) ORDER BY e.dataset_id,e.file_id""").bindparams(
     bindparam("dataset_ids", expanding=True, type_=String()))


def _source(row: Any, include_text: bool = True) -> dict[str, Any]:
    out = {"label": row.source_label, "locator": row.source_locator, "sha256": row.source_sha256}
    if include_text:
        out["text"] = row.source_text
    return out


def evidence_ref(row: Any, stale: bool = False) -> dict[str, Any]:
    return {"revision": row.revision, "status": "stale" if stale else row.status,
            "facts": row.facts, "source": _source(row), "reviewedBy": row.reviewed_by,
            "reviewedAt": row.reviewed_at}


def list_for_dataset(session: Session, dataset_id: Ulid) -> list[dict[str, Any]]:
    out = []
    for row in session.execute(_LIST, {"dataset_id": str(dataset_id)}):
        evidence = None if row.revision is None else evidence_ref(
            row, stale=row.file_revision != row.content_revision)
        out.append({"fileId": row.file_id, "fileName": row.file_name,
                    "fileRevision": row.content_revision, "evidence": evidence})
    return out


def lock_file(session: Session, dataset_id: Ulid, file_id: Ulid):
    return session.execute(_LOCK_FILE, {"dataset_id": str(dataset_id), "file_id": str(file_id)}).first()


def save(session: Session, *, file_row: Any, expected_revision: int,
         expected_file_revision: int, facts: dict[str, Any], source: dict[str, str],
         status: str, reviewer_id: Ulid) -> dict[str, Any] | None:
    if file_row.content_revision != expected_file_revision:
        return None
    current = session.execute(_LOCK_EVIDENCE, {"file_id": file_row.id}).first()
    if (0 if current is None else current.revision) != expected_revision:
        return None
    params = {"file_id": file_row.id, "lab_id": file_row.lab_id, "dataset_id": file_row.dataset_id,
              "file_revision": file_row.content_revision, "status": status,
              "facts": json.dumps(facts, ensure_ascii=False), "source_label": source["label"],
              "source_locator": source["locator"], "source_text": source["text"],
              "source_sha256": hashlib.sha256(source["text"].encode()).hexdigest(),
              "reviewed_by": str(reviewer_id) if status == "reviewed" else None}
    return evidence_ref(session.execute(_INSERT if current is None else _UPDATE, params).one())


def read_reviewed(session: Session, dataset_ids: list[str] | None = None, *,
                  include_source_text: bool = True) -> list[dict[str, Any]]:
    if dataset_ids == []:
        return []
    ids = [] if dataset_ids is None else dataset_ids
    rows = session.execute(_REVIEWED, {"all_datasets": dataset_ids is None, "dataset_ids": ids,
                                      "include_source_text": include_source_text})
    return [{"dataset_id": r.dataset_id, "file_id": r.file_id, "file_name": r.file_name,
             "file_kind": r.file_kind, "facts": r.facts, "source": _source(r, include_source_text),
             "reviewed_by": r.reviewed_by, "reviewed_at": r.reviewed_at} for r in rows]
