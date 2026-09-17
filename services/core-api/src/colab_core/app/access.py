"""Compose catalogue ownership and access policy without cross-domain table reads."""
from ..domains import d2_access, d3_catalog


def dataset_access(db):
    return d2_access.DatasetAccessAdapter(db, lambda ids: d3_catalog.dataset_labs(db, ids))
