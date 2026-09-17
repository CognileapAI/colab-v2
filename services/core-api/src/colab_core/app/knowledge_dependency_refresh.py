"""Bounded tracked-user sweep, not a scheduler or unattended service identity."""
from ..domains import d3_knowledge_dependencies, d4_lineage
from ..kernel.ids import Ulid
from ..kernel.knowledge_wire import Principal, SourceKey
from ..kernel.scope import scoped_session
from .knowledge_source_authority import SourceAuthority


class KnowledgeDependencyRefresh:
    def __init__(self, factory, login_sessions, credentials):
        if login_sessions is None or credentials is None:
            raise ValueError('tracked session and credential stores required')
        self._factory,self._sessions=factory,login_sessions
        self._authority=SourceAuthority(factory,credentials)

    def _subject(self, token):
        try:subject=self._sessions.authenticate(token)
        except Exception:raise ValueError('dependency_unavailable') from None
        if subject is None or subject.must_change_password or subject.credential_version is None:
            raise ValueError('forbidden')
        principal=Principal(account_id=str(subject.account_id),lab_id=str(subject.lab_id),
                            session_version=subject.credential_version)
        self._authority._subject(principal)
        return subject,principal

    def run_once(self, session_token, *, after_source=None, limit=100):
        if type(limit) is not int or not 1<=limit<=100:raise ValueError('limit must be 1..100')
        subject,principal=self._subject(session_token)
        cursor=SourceKey.model_validate(after_source) if after_source is not None else None
        if cursor is not None and (cursor.lab_id!=principal.lab_id or cursor.source_kind not in {'file','evidence'}):
            raise ValueError('forbidden')
        # Successful cursor is returned only after the entire bounded batch commits.
        with scoped_session(self._factory,subject) as session:
            keys=d3_knowledge_dependencies.page(session,after_source=cursor,limit=limit)
            keys=d3_knowledge_dependencies.lock_batch(session,keys,principal)
            # The lock wait may span relationship changes; never reuse pre-wait revisions.
            current=d4_lineage.LineageRevisionAdapter(session).revisions(
                [Ulid(value) for value in sorted({key.dataset_id for key in keys})])
            requeued=sum(d3_knowledge_dependencies.requeue_if_lineage_changed(
                session,key,principal,current.get(key.dataset_id)) for key in keys)
            if self._subject(session_token)[1]!=principal:raise ValueError('forbidden')
        return {'scanned':len(keys),'requeued':requeued,
                'after_source':keys[-1].model_dump() if len(keys)==limit else None}
