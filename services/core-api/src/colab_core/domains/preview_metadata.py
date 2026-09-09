"""Original file metadata for render responses; storage keys stay renderer-owned."""
from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session
from .d5_ingestion import UploadLedgerAdapter


_FILES = text("""
    SELECT id, file_name, dataset_id AS target_id, 'datasetId' AS target_kind
      FROM d3_file WHERE id IN :ids
""").bindparams(bindparam("ids", expanding=True))


def file_names(db: Session, ids: list[str]) -> list[dict]:
    """Scoped session/RLS bounds the rows; caller still checks body/owner access."""
    if not ids:
        return []
    names = [dict(row) for row in db.execute(_FILES, {"ids": ids}).mappings()]
    names.extend({"id": row["id"], "file_name": row["file_name"],
                  "target_id": row["upload_id"], "target_kind": "uploadId"}
                 for row in UploadLedgerAdapter(db).metadata_for_file_ids(ids))
    return names
