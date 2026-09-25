"""Internal trusted adapter, not a public endpoint or authentication provider.

Construct outside D10 with a dedicated writer factory and fixed authority.
Protected reads live in knowledge_reader; deletion uses a separate capability.
"""
from ..domains import d9_dataset_knowledge
from ..kernel.knowledge_wire import Principal, ReplaceCommand, InvalidateCommand
from ..kernel.ids import Ulid
from .ontology_manifest import load_manifest


class KnowledgeInvalidator:
    """Deletion-only fixed capability. No ontology or human session dependency.

    Owner callback and DB commit are not one distributed transaction; subsequent
    source projection still needs its own current revision/sequence checks.
    """
    def __init__(self, session_factory, authority, lab_id):
        if not Ulid.is_valid(lab_id):
            raise ValueError('fixed deletion lab required')
        self._factory,self._authority,self._lab = session_factory,authority,str(lab_id)

    def invalidate(self, command):
        command = InvalidateCommand.model_validate(command.model_dump())
        if command.source_key.lab_id != self._lab:
            raise ValueError('forbidden')
        try:
            verdict = self._authority.validate(command)
        except Exception:
            raise ValueError('dependency_unavailable') from None
        if verdict != 'current':
            raise ValueError(verdict if verdict in {'forbidden','stale_source','stale_generation'} else 'dependency_unavailable')
        with self._factory.begin() as session:
            return d9_dataset_knowledge.invalidate(session,command)


class KnowledgeWriter:
    def __init__(self, session_factory, authority):
        self._factory = session_factory
        self._authority = authority

    def replace(self, command: ReplaceCommand, principal_claim: Principal):
        command = ReplaceCommand.model_validate(command.model_dump())
        principal = Principal.model_validate(principal_claim.model_dump())
        if principal.lab_id != command.source_key.lab_id:
            raise ValueError('forbidden')
        try:
            verdict = self._authority.validate(command, principal)
        except Exception:
            raise ValueError('dependency_unavailable') from None
        if verdict != 'current':
            raise ValueError(verdict if verdict in {'forbidden', 'stale_source', 'stale_generation',
                                                   'stale_release'} else 'dependency_unavailable')
        with self._factory.begin() as session:
            try:
                manifest = load_manifest(session.get_bind())
            except Exception:
                raise ValueError('dependency_unavailable') from None
            if manifest['version'] != command.processing_version.ontology_release:
                raise ValueError('stale_release')
            # Separate read and write transactions are not distributed atomicity.
            # Subsequent protected readers/projections must revalidate the release.
            return d9_dataset_knowledge.replace(session, command)
