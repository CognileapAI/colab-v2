"""Auto-generated knowledge boundary values; do not edit. Not authentication."""
from __future__ import annotations
from datetime import date
import hashlib
import json
import re
from typing import Annotated, Literal, Protocol
from pydantic import BaseModel, ConfigDict, Field, model_validator
from .ontology_wire import KEY_PATTERN

class WireValue(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False, hide_input_in_errors=True)

Id = Annotated[str, Field(min_length=26, max_length=26, pattern='^[0-9A-HJKMNP-TV-Z]{26}$')]

Digest = Annotated[str, Field(pattern='^[0-9a-f]{64}$')]

Version = Annotated[str, Field(min_length=1, max_length=100, pattern='\\S')]

ConceptId = Annotated[str, Field(min_length=1, max_length=60, pattern='^[a-z0-9]+(-[a-z0-9]+)*$')]

class SourceKey(WireValue):
    lab_id: Id
    dataset_id: Id
    source_kind: Literal['metadata', 'file', 'evidence', 'lineage']
    source_id: Id

class SourceVersion(WireValue):
    revision: Annotated[int, Field(ge=1)]
    digest: Digest
    deleted: bool

class ProcessingVersion(WireValue):
    generation: Annotated[int, Field(ge=1)]
    extractor_version: Version
    mapping_version: Version
    ontology_release: Digest

class Principal(WireValue):
    account_id: Id
    lab_id: Id
    session_version: Annotated[int, Field(ge=1)]

class EvidenceRepresentation(WireValue):
    fact_id: Id
    predicate: Literal['representation']
    value: Literal['spatial_grid', 'point_observations', 'table', 'array']
    source_locator: Annotated[str, Field(min_length=1, max_length=300)]
    source_version: SourceVersion
    evidence_kind: Literal['file_measurement', 'description_claim', 'human_review']

class EvidencePlatform(WireValue):
    fact_id: Id
    predicate: Literal['platform']
    value: Literal['satellite', 'ground', 'model', 'mixed']
    source_locator: Annotated[str, Field(min_length=1, max_length=300)]
    source_version: SourceVersion
    evidence_kind: Literal['file_measurement', 'description_claim', 'human_review']

class EvidenceFormat(WireValue):
    fact_id: Id
    predicate: Literal['format']
    value: Literal['npy', 'csv', 'netcdf', 'tif', 'hdf5']
    source_locator: Annotated[str, Field(min_length=1, max_length=300)]
    source_version: SourceVersion
    evidence_kind: Literal['file_measurement', 'description_claim', 'human_review']

class EvidenceProvider(WireValue):
    fact_id: Id
    predicate: Literal['provider']
    value: Annotated[str, Field(min_length=1, max_length=200)]
    source_locator: Annotated[str, Field(min_length=1, max_length=300)]
    source_version: SourceVersion
    evidence_kind: Literal['file_measurement', 'description_claim', 'human_review']

class EvidenceUnit(WireValue):
    fact_id: Id
    predicate: Literal['unit']
    value: Annotated[str, Field(min_length=1, max_length=100)]
    source_locator: Annotated[str, Field(min_length=1, max_length=300)]
    source_version: SourceVersion
    evidence_kind: Literal['file_measurement', 'description_claim', 'human_review']

class EvidenceStatistics(WireValue):
    fact_id: Id
    predicate: Literal['statistics']
    value: Annotated[list[Literal['instantaneous', 'daily_mean', 'daily_max', 'daily_min', 'monthly_mean', 'monthly_mean_daily_max', 'monthly_mean_daily_min']], Field(min_length=1, max_length=7)]
    source_locator: Annotated[str, Field(min_length=1, max_length=300)]
    source_version: SourceVersion
    evidence_kind: Literal['file_measurement', 'description_claim', 'human_review']

class EvidenceRoles(WireValue):
    fact_id: Id
    predicate: Literal['roles']
    value: Annotated[list[Literal['model_input', 'auxiliary_input', 'validation', 'prediction', 'index', 'documentation', 'analysis_code']], Field(min_length=1)]
    source_locator: Annotated[str, Field(min_length=1, max_length=300)]
    source_version: SourceVersion
    evidence_kind: Literal['file_measurement', 'description_claim', 'human_review']

    @model_validator(mode="after")
    def unique_roles(self):
        if len(set(self.value)) != len(self.value):
            raise ValueError("duplicate evidence roles")
        return self

class EvidencePeriodValue(WireValue):
    start: str
    end: str

    @model_validator(mode="after")
    def ordered(self):
        start, end = date.fromisoformat(self.start), date.fromisoformat(self.end)
        if str(start) != self.start or str(end) != self.end or end < start:
            raise ValueError("invalid evidence period")
        return self

class EvidencePeriod(WireValue):
    fact_id: Id
    predicate: Literal['period']
    value: EvidencePeriodValue
    source_locator: Annotated[str, Field(min_length=1, max_length=300)]
    source_version: SourceVersion
    evidence_kind: Literal['file_measurement', 'description_claim', 'human_review']

class EvidenceRegion(WireValue):
    fact_id: Id
    predicate: Literal['region']
    value: Annotated[str, Field(min_length=1, max_length=500)]
    source_locator: Annotated[str, Field(min_length=1, max_length=300)]
    source_version: SourceVersion
    evidence_kind: Literal['file_measurement', 'description_claim', 'human_review']

class EvidenceCadence(WireValue):
    fact_id: Id
    predicate: Literal['cadence']
    value: Literal['daily', 'weekly', 'monthly', '15min', 'hourly', '5min', '10min', 'yearly']
    source_locator: Annotated[str, Field(min_length=1, max_length=300)]
    source_version: SourceVersion
    evidence_kind: Literal['file_measurement', 'description_claim', 'human_review']

class EvidenceModel(WireValue):
    fact_id: Id
    predicate: Literal['model']
    value: Annotated[str, Field(min_length=1, max_length=500)]
    source_locator: Annotated[str, Field(min_length=1, max_length=300)]
    source_version: SourceVersion
    evidence_kind: Literal['file_measurement', 'description_claim', 'human_review']

class EvidenceVariable(WireValue):
    fact_id: Id
    predicate: Literal['variable']
    value: Annotated[str, Field(min_length=1, max_length=500)]
    source_locator: Annotated[str, Field(min_length=1, max_length=300)]
    source_version: SourceVersion
    evidence_kind: Literal['file_measurement', 'description_claim', 'human_review']

class EvidenceDirectObservation(WireValue):
    fact_id: Id
    predicate: Literal['directObservation']
    value: bool
    source_locator: Annotated[str, Field(min_length=1, max_length=300)]
    source_version: SourceVersion
    evidence_kind: Literal['file_measurement', 'description_claim', 'human_review']

class EvidenceNativeResolutionM(WireValue):
    fact_id: Id
    predicate: Literal['nativeResolutionM']
    value: Annotated[float, Field(gt=0)]
    source_locator: Annotated[str, Field(min_length=1, max_length=300)]
    source_version: SourceVersion
    evidence_kind: Literal['file_measurement', 'description_claim', 'human_review']

class EvidenceInterpolated(WireValue):
    fact_id: Id
    predicate: Literal['interpolated']
    value: bool
    source_locator: Annotated[str, Field(min_length=1, max_length=300)]
    source_version: SourceVersion
    evidence_kind: Literal['file_measurement', 'description_claim', 'human_review']

Evidence = Annotated[EvidenceRepresentation | EvidencePlatform | EvidenceFormat | EvidenceProvider | EvidenceUnit | EvidenceStatistics | EvidenceRoles | EvidencePeriod | EvidenceRegion | EvidenceCadence | EvidenceModel | EvidenceVariable | EvidenceDirectObservation | EvidenceNativeResolutionM | EvidenceInterpolated, Field(discriminator="predicate")]

class RuleBasis(WireValue):
    mapping_rule_id: Version

class ReviewBasis(WireValue):
    review_id: Id

class Mapping(WireValue):
    fact_id: Id
    concept_id: ConceptId
    basis: RuleBasis | ReviewBasis

    @model_validator(mode="after")
    def concept_key(self):
        if re.fullmatch(KEY_PATTERN, "concept:" + self.concept_id) is None:
            raise ValueError("invalid concept identifier")
        return self

class SourceDependency(WireValue):
    owner: Literal['D3', 'D4', 'D5']
    resource_id: Id
    revision: Annotated[int, Field(ge=1)]

class OntologyDependency(WireValue):
    owner: Literal['D9']
    resource_id: Annotated[str, Field(max_length=68, pattern='^(discovery|concept:[a-z0-9]+(-[a-z0-9]+)*)$')]
    revision: Digest

Dependency = SourceDependency | OntologyDependency

SourceGrant = Annotated[str, Field(min_length=1, max_length=512)]

class ReplaceCommand(WireValue):
    protocol: Literal['knowledge-lifecycle/1']
    grant: SourceGrant = Field(repr=False)
    source_key: SourceKey
    source_version: SourceVersion
    processing_version: ProcessingVersion
    facts: Annotated[list[Evidence], Field(min_length=1, max_length=1000)]
    mappings: Annotated[list[Mapping], Field(max_length=1000)]
    dependencies: Annotated[list[Dependency], Field(max_length=1000)]

    @model_validator(mode="after")
    def coherent(self):
        ids = {fact.fact_id for fact in self.facts}
        if self.source_version.deleted or len(ids) != len(self.facts):
            raise ValueError("deleted source or duplicate fact")
        if any(fact.source_version != self.source_version for fact in self.facts):
            raise ValueError("fact source version mismatch")
        if any(mapping.fact_id not in ids for mapping in self.mappings):
            raise ValueError("mapping references missing fact")
        keys = [(m.fact_id, m.concept_id) for m in self.mappings]
        if len(set(keys)) != len(keys):
            raise ValueError("duplicate mapping")
        return self

class KnowledgePayload(WireValue):
    protocol: Literal['knowledge-lifecycle/1']
    source_key: SourceKey
    source_version: SourceVersion
    processing_version: ProcessingVersion
    facts: Annotated[list[Evidence], Field(min_length=1, max_length=1000)]
    mappings: Annotated[list[Mapping], Field(max_length=1000)]
    dependencies: Annotated[list[Dependency], Field(max_length=1000)]

    @model_validator(mode="after")
    def coherent(self):
        ids = {fact.fact_id for fact in self.facts}
        if self.source_version.deleted or len(ids) != len(self.facts):
            raise ValueError("deleted source or duplicate fact")
        if any(fact.source_version != self.source_version for fact in self.facts):
            raise ValueError("fact source version mismatch")
        if any(mapping.fact_id not in ids for mapping in self.mappings):
            raise ValueError("mapping references missing fact")
        keys = [(m.fact_id, m.concept_id) for m in self.mappings]
        if len(set(keys)) != len(keys):
            raise ValueError("duplicate mapping")
        return self

class DeletedSourceVersion(WireValue):
    revision: Annotated[int, Field(ge=1)]
    deleted: Literal[True]

    @model_validator(mode="before")
    @classmethod
    def strict_deleted(cls, value):
        if isinstance(value, dict) and value.get("deleted") is not True:
            raise ValueError("explicit deleted boolean required")
        return value

class DeletionProcessingVersion(WireValue):
    generation: Annotated[int, Field(ge=1)]

class InvalidateCommand(WireValue):
    protocol: Literal['knowledge-lifecycle/1']
    grant: SourceGrant = Field(repr=False)
    source_key: SourceKey
    source_version: DeletedSourceVersion
    processing_version: DeletionProcessingVersion
    reason: Literal['deleted']

class DeletionIssueRequest(WireValue):
    source_key: SourceKey
    expected_revision: Annotated[int, Field(ge=1)]

class DeletionValidateRequest(WireValue):
    command: InvalidateCommand

class DeletionValidateResponse(WireValue):
    status: Literal['current', 'forbidden', 'stale_source', 'stale_generation']

class InvalidationReceipt(WireValue):
    protocol: Literal['knowledge-lifecycle/1']
    issuer: Literal['D9']
    receipt_id: Id
    source_key: SourceKey
    source_version: DeletedSourceVersion
    processing_version: DeletionProcessingVersion
    publication_sequence: Annotated[int, Field(ge=1)]
    payload_digest: Digest
    status: Literal['invalidated']

class SourceIssueRequest(WireValue):
    source_key: SourceKey

class SourceIssueResponse(WireValue):
    command: ReplaceCommand
    principal: Principal

class SourceValidateRequest(WireValue):
    command: ReplaceCommand

class SourceValidateResponse(WireValue):
    status: Literal['current', 'forbidden', 'stale_source', 'stale_generation', 'stale_release']
    principal: Principal

class KnowledgeReplaceRequest(WireValue):
    command: ReplaceCommand
    principal: Principal

class KnowledgeReceipt(WireValue):
    protocol: Literal['knowledge-lifecycle/1']
    issuer: Literal['D9']
    receipt_id: Id
    source_key: SourceKey
    source_version: SourceVersion
    processing_version: ProcessingVersion
    publication_sequence: Annotated[int, Field(ge=1)]
    payload_digest: Digest
    status: Literal['replaced', 'invalidated']

class SourceReadRequest(WireValue):
    receipt: KnowledgeReceipt

class KnowledgeReadRequest(WireValue):
    source_key: SourceKey
    expected_receipt_id: Id

class AuthorizedKnowledge(WireValue):
    payload: KnowledgePayload
    receipt: KnowledgeReceipt

    @model_validator(mode="after")
    def coherent(self):
        if self.receipt.status != "replaced":
            raise ValueError("knowledge unavailable")
        for field in ("protocol", "source_key", "source_version", "processing_version"):
            if getattr(self.payload, field) != getattr(self.receipt, field):
                raise ValueError("knowledge mismatch")
        if payload_digest(self.payload) != self.receipt.payload_digest:
            raise ValueError("knowledge digest mismatch")
        return self


def payload_digest(command: ReplaceCommand | InvalidateCommand | KnowledgePayload) -> str:
    """Canonical wire digest excludes the secret grant; it is NOT authentication.

    Lists retain their order. Retry producers must preserve the exact ordered
    payload. The authority binds this digest to source/processing/principal.
    """
    body = command.model_dump(mode="json", exclude={"grant"})
    return hashlib.sha256(json.dumps(body, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()


class KnowledgeWriter(Protocol):
    def replace(self, command: ReplaceCommand) -> KnowledgeReceipt: ...
    def invalidate(self, command: InvalidateCommand) -> InvalidationReceipt: ...

