"""Compose D2 access decisions with D3 ownership facts."""
from sqlalchemy.orm import Session
from ..domains.d2_access import DatasetAccessAdapter
from ..domains.d3_ownership import DatasetOwnershipAdapter


def dataset_access_adapter(session: Session) -> DatasetAccessAdapter:
    return DatasetAccessAdapter(session, DatasetOwnershipAdapter(session))
