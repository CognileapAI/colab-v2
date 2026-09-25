"""Trusted assembly for receipt projection; no public Claim/Subject endpoint.

The future worker supplies its server-owned Claim. No network spans a DB
transaction or mutex; the tracked user is reauthenticated after the response.
"""

from dataclasses import asdict
from ..domains import d3_knowledge_projection, d4_lineage
from ..kernel.knowledge_wire import Principal, SourceKey
from ..kernel.scope import scoped_session
from .knowledge_client import KnowledgeHttpClient
from .knowledge_source_authority import SourceAuthority


class KnowledgeProjector:
    def __init__(
        self, factory, login_sessions, credentials, *, base_url, reader_token, timeout
    ):
        if login_sessions is None or credentials is None:
            raise ValueError("tracked session and credential stores required")
        self._factory = factory
        self._sessions = login_sessions
        self._authority = SourceAuthority(factory, credentials)
        self._reader = KnowledgeHttpClient(
            base_url, token=reader_token, timeout=timeout
        )

    def apply(self, claim, expected_receipt_id, *, session_token):
        key = SourceKey.model_validate(
            {
                k: asdict(claim)[k]
                for k in ("lab_id", "dataset_id", "source_kind", "source_id")
            }
        )
        result = self._reader.read(
            key, expected_receipt_id, session_token=session_token
        )
        try:
            subject = self._sessions.authenticate(session_token)
        except Exception:
            raise ValueError("dependency_unavailable") from None
        if (
            subject is None
            or subject.must_change_password
            or subject.credential_version is None
        ):
            raise ValueError("forbidden")
        principal = Principal(
            account_id=str(subject.account_id),
            lab_id=str(subject.lab_id),
            session_version=subject.credential_version,
        )
        # Reuse the exact existing current-credential/race check. Do not replace
        # the tracked version with a subsequently loaded credential version.
        self._authority._subject(principal)
        with scoped_session(self._factory, subject) as session:
            return d3_knowledge_projection.apply(session, claim, result, principal,
                lineage=d4_lineage.LineageRevisionAdapter(session))
