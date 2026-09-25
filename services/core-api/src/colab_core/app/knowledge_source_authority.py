"""Internal source-authority adapter, not an authenticated HTTP endpoint.

Principal must come from the trusted caller's authenticated identity. Each call
rechecks the existing credential store, then applies ordinary dataset/file RLS.
"""
from ..domains import d3_knowledge_source, d4_lineage
from ..kernel.db_credentials import DatabaseCredentialStore
from ..kernel.ids import Ulid
from ..kernel.knowledge_wire import SourceKey
from ..kernel.scope import scoped_session, read_only_scope


class DeletionAuthority:
    """Fixed-lab API capability, not a distinct body-isolated database role.

    No human credential, session or ontology dependency. Only body-free owner
    pointers are inspected; source transaction must have committed beforehand.
    """
    def __init__(self, session_factory, lab_id):
        if not Ulid.is_valid(lab_id):
            raise ValueError('fixed deletion lab required')
        self._factory, self._lab = session_factory, str(lab_id)

    def _run(self, key, operation):
        from sqlalchemy import text
        if key.lab_id != self._lab:
            raise ValueError('forbidden')
        with self._factory.begin() as session:
            for name,value in (('app.current_lab',self._lab),('app.current_account',''),('app.operator_read','')):
                session.execute(text('SELECT set_config(:name,:value,true)'),{'name':name,'value':value})
            return operation(session)

    def issue(self, key, expected_revision, *, ttl_seconds):
        key = SourceKey.model_validate(key.model_dump())
        return self._run(key,lambda session: d3_knowledge_source.issue_deletion(session,key,expected_revision,ttl_seconds=ttl_seconds))

    def validate(self, command):
        from ..kernel.knowledge_wire import InvalidateCommand
        command = InvalidateCommand.model_validate(command.model_dump())
        return self._run(command.source_key,lambda session: d3_knowledge_source.validate_deletion(session,command))


class SourceAuthority:
    def __init__(self, session_factory, credentials: DatabaseCredentialStore):
        self._factory = session_factory
        self._credentials = credentials

    def _subject(self, principal):
        credential = self._credentials.token_is_current(
            Ulid(principal.account_id), Ulid(principal.lab_id), principal.session_version)
        if credential is None or credential.status != 'active' or credential.must_change_password:
            raise ValueError('forbidden')
        # The credential store reads twice; revocation/membership may change
        # between those reads. Validate the returned identity, not only the query.
        if (str(credential.subject.account_id), str(credential.subject.lab_id), credential.session_version) != (
            principal.account_id, principal.lab_id, principal.session_version
        ):
            raise ValueError('forbidden')
        return credential.subject

    def issue(self, key, principal, *, ttl_seconds):
        subject = self._subject(principal)
        with scoped_session(self._factory,subject) as session:
            return d3_knowledge_source.issue(session,key,principal,ttl_seconds=ttl_seconds,
                lineage=d4_lineage.LineageRevisionAdapter(session))

    def validate(self, command, principal):
        try:
            subject = self._subject(principal)
        except ValueError:
            return 'forbidden'
        with scoped_session(self._factory,subject) as session:
            return d3_knowledge_source.validate(session,command,principal,
                lineage=d4_lineage.LineageRevisionAdapter(session))

    def authorize_read(self, receipt, principal):
        try:
            subject = self._subject(principal)
        except ValueError:
            return 'forbidden'
        with read_only_scope(self._factory,subject) as session:
            return d3_knowledge_source.authorize_read(session,receipt,principal,
                lineage=d4_lineage.LineageRevisionAdapter(session))
