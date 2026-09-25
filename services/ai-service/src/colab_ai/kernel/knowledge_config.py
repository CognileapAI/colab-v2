"""Settings loaded only by the separate knowledge writer entrypoint, never D10."""
from dataclasses import dataclass, field
import math
import os
from urllib.parse import urlsplit
from .config import resolve_env_or_file
from .ids import Ulid


@dataclass(frozen=True)
class KnowledgeSettings:
    enabled: bool
    database_url: str | None = field(default=None,repr=False)
    writer_token: str | None = field(default=None,repr=False)
    callback_token: str | None = field(default=None,repr=False)
    ontology_token: str | None = field(default=None,repr=False)
    source_url: str | None = field(default=None,repr=False)
    timeout: float | None = None
    reader_token: str | None = field(default=None,repr=False)
    deletion_token: str | None = field(default=None,repr=False)
    deletion_lab: str | None = None
    deletion_enabled: bool | None = None

    def __post_init__(self):
        if type(self.enabled) is not bool:
            raise ValueError('knowledge mode required')
        if not self.enabled:return
        if type(self.deletion_enabled) is not bool:
            raise ValueError('explicit deletion mode required')
        values=(self.writer_token,self.callback_token,self.ontology_token,self.reader_token)
        if self.deletion_enabled:
            if (not isinstance(self.deletion_token,str) or not self.deletion_token.strip()
                or any(c in self.deletion_token for c in '\r\n') or self.deletion_token in values
                or not Ulid.is_valid(self.deletion_lab)):
                raise ValueError('distinct fixed-lab deletion capability required')
        if any(not isinstance(v,str) or not v.strip() or any(c in v for c in '\r\n') for v in values) or len(set(values))!=4:
            raise ValueError('distinct knowledge credentials required')
        parsed=urlsplit(self.source_url or '')
        if (not self.database_url or parsed.scheme not in {'http','https'} or not parsed.hostname
            or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in {'','/'}):
            raise ValueError('knowledge connection configuration invalid')
        if type(self.timeout) not in {int,float} or not math.isfinite(self.timeout) or not 0<self.timeout<=30:
            raise ValueError('finite knowledge timeout required')

    @classmethod
    def from_env(cls, env=None):
        env=os.environ if env is None else env
        mode=env.get('COLAB_KNOWLEDGE_ENABLED')
        if mode not in {'true','false'}:raise ValueError('explicit knowledge mode required')
        if mode=='false':return cls(False)
        deletion=env.get('COLAB_KNOWLEDGE_DELETION_ENABLED')
        if deletion not in {'true','false'}:raise ValueError('explicit deletion mode required')
        try:
            timeout=float(env.get('COLAB_KNOWLEDGE_TIMEOUT_SECONDS',''))
        except ValueError:raise ValueError('finite knowledge timeout required') from None
        return cls(True,resolve_env_or_file(env,'COLAB_AI_KNOWLEDGE_WRITER_DB_URL'),
            resolve_env_or_file(env,'COLAB_KNOWLEDGE_WRITER_TOKEN'),resolve_env_or_file(env,'COLAB_KNOWLEDGE_CALLBACK_TOKEN'),
            resolve_env_or_file(env,'COLAB_AI_SERVICE_TOKEN'),env.get('COLAB_KNOWLEDGE_SOURCE_URL'),timeout,
            resolve_env_or_file(env,'COLAB_KNOWLEDGE_READER_TOKEN'),
            resolve_env_or_file(env,'COLAB_KNOWLEDGE_DELETION_TOKEN'),env.get('COLAB_KNOWLEDGE_DELETION_LAB'),deletion=='true')
