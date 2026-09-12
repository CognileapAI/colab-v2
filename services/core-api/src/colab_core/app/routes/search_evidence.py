"""HTTP surface for source-backed, file-versioned search evidence."""
from __future__ import annotations

import datetime as dt
import re
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator, model_validator
from sqlalchemy.orm import Session

from ...domains import d3_search_evidence
from ...kernel import errors
from ...kernel.auth import Subject
from ...kernel.ids import Ulid
from ..deps import current_subject, scoped_db
from .catalog import require_body_access
from .ingestion import _require_upload_edit

router = APIRouter()


class EvidencePeriod(BaseModel):
    model_config = ConfigDict(extra="forbid")
    start: dt.date
    end: dt.date

    @field_validator("start", "end", mode="before")
    @classmethod
    def iso_date_only(cls, value):
        if not isinstance(value, str) or re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) is None:
            raise ValueError("period must use YYYY-MM-DD")
        return value

    @model_validator(mode="after")
    def ordered(self):
        if self.end < self.start:
            raise ValueError("period end precedes start")
        return self


class EvidenceFacts(BaseModel):
    model_config = ConfigDict(extra="forbid")
    roles: list[Literal["model_input", "auxiliary_input", "validation", "prediction", "index",
                        "documentation", "analysis_code"]] | None = None
    period: EvidencePeriod | None = None
    region: str | None = Field(default=None, min_length=1, max_length=500)
    cadence: Literal["daily", "weekly", "monthly", "15min"] | None = None
    model: str | None = Field(default=None, min_length=1, max_length=500)
    variable: str | None = Field(default=None, min_length=1, max_length=500)
    directObservation: StrictBool | None = None
    nativeResolutionM: float | None = Field(default=None, gt=0, strict=True, allow_inf_nan=False)
    interpolated: StrictBool | None = None

    @model_validator(mode="after")
    def has_fact(self):
        if not any(getattr(self, name) is not None for name in type(self).model_fields):
            raise ValueError("at least one fact is required")
        if self.roles is not None and (not self.roles or len(set(self.roles)) != len(self.roles)):
            raise ValueError("roles must be non-empty and unique")
        return self

    @field_validator("region", "model", "variable")
    @classmethod
    def optional_text_not_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("fact text must not be blank")
        return value


class EvidenceSource(BaseModel):
    model_config = ConfigDict(extra="forbid")
    label: str = Field(min_length=1, max_length=200)
    locator: str = Field(min_length=1, max_length=300)
    text: str = Field(min_length=1, max_length=20000)

    @field_validator("label", "locator", "text")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("source fields must not be blank")
        return value


class EvidenceWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expectedRevision: int = Field(ge=0, strict=True)
    expectedFileRevision: int = Field(ge=1, strict=True)
    facts: EvidenceFacts
    source: EvidenceSource
    status: Literal["draft", "reviewed"]


def _iso(value):
    return value.astimezone(dt.timezone.utc).isoformat() if isinstance(value, dt.datetime) else value


def _json_evidence(value: dict) -> dict:
    value["reviewedAt"] = _iso(value["reviewedAt"])
    return value


def _ids(dataset_id: str, file_id: str | None = None) -> tuple[Ulid, Ulid | None]:
    if not Ulid.is_valid(dataset_id) or (file_id is not None and not Ulid.is_valid(file_id)):
        raise errors.bad_request("datasetId 또는 fileId가 정규 ID가 아니다.")
    return Ulid(dataset_id), None if file_id is None else Ulid(file_id)


@router.get("/datasets/{datasetId}/search-evidence", name="listDatasetSearchEvidence")
def list_search_evidence(datasetId: str, db: Session = Depends(scoped_db)) -> dict:
    dataset_id, _ = _ids(datasetId)
    require_body_access(db, dataset_id)
    items = d3_search_evidence.list_for_dataset(db, dataset_id)
    for item in items:
        if item["evidence"] is not None:
            _json_evidence(item["evidence"])
    return {"items": items}


@router.put("/datasets/{datasetId}/files/{fileId}/search-evidence",
            name="saveDatasetFileSearchEvidence")
def save_search_evidence(datasetId: str, fileId: str, payload: EvidenceWrite,
                         subject: Subject = Depends(current_subject),
                         db: Session = Depends(scoped_db)) -> dict:
    dataset_id, file_id = _ids(datasetId, fileId)
    _require_upload_edit(db, subject)
    require_body_access(db, dataset_id)
    file_row = d3_search_evidence.lock_file(db, dataset_id, file_id)
    if file_row is None:
        raise errors.not_found()
    saved = d3_search_evidence.save(
        db, file_row=file_row, expected_revision=payload.expectedRevision,
        expected_file_revision=payload.expectedFileRevision,
        facts=payload.facts.model_dump(exclude_none=True, mode="json"),
        source=payload.source.model_dump(), status=payload.status,
        reviewer_id=subject.account_id)
    if saved is None:
        raise errors.conflict("근거 또는 파일이 다른 요청에서 먼저 변경됐다.")
    return _json_evidence(saved)
