"""Bounded authenticated HTTP adapter for the ontology manifest Port."""
from __future__ import annotations

import json
import math
import time
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler
from ..kernel.ontology_wire import MANIFEST_PATH, LOOKUP_PATH, PROPOSAL_PATH
from ..ports.ontology import validate_manifest, validate_lookup


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class OntologyHttpClient:
    def __init__(self, base_url: str, *, token: str, timeout: float = 5.0, max_bytes: int = 16*1024*1024):
        parsed=urlsplit(base_url)
        if parsed.scheme not in {'http','https'} or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError('invalid ontology service URL')
        if not isinstance(token,str) or not token.strip() or any(c in token for c in '\r\n'):
            raise ValueError('ontology service token required')
        if not isinstance(timeout,(int,float)) or isinstance(timeout,bool) or not math.isfinite(timeout) or not 0<timeout<=30:
            raise ValueError('invalid ontology timeout')
        if type(max_bytes) is not int or not 1<=max_bytes<=16*1024*1024:
            raise ValueError('invalid ontology byte limit')
        self._base=base_url.rstrip('/')
        self._url=self._base+MANIFEST_PATH
        self._token,self._timeout,self._max_bytes=token,timeout,max_bytes
        self._opener=build_opener(ProxyHandler({}),_NoRedirect())

    def load_manifest(self) -> dict:
        return validate_manifest(self._request(MANIFEST_PATH))

    def lookup(self, *, query: str, manifest: dict) -> dict:
        if not isinstance(query,str) or len(query)>16000:
            raise ValueError('invalid concept query')
        manifest=validate_manifest(manifest)
        return validate_lookup(self._request(LOOKUP_PATH,{'query':query,'expected_version':manifest['version']}),manifest)

    def propose(self, source: dict, concepts: list[dict]) -> dict:
        payload={'source':{'facts':source['facts']},
                 'concepts':[{**p['node'],'edges':p['edges'],'neighbors':p['neighbors']} for p in concepts]}
        if len(json.dumps(payload,ensure_ascii=False).encode())>128*1024:
            raise ValueError('proposal context exceeds bound')
        return self._request(PROPOSAL_PATH,payload,timeout=30.0)

    def _request(self, path: str, payload=None, *, timeout=None) -> dict:
        try:
            request=Request(self._base+path,data=None if payload is None else json.dumps(payload,ensure_ascii=False).encode(),
                headers={'Authorization':'Bearer '+self._token,'Accept':'application/json','Content-Type':'application/json'})
            timeout=self._timeout if timeout is None else timeout
            deadline=time.monotonic()+timeout
            with self._opener.open(request,timeout=timeout) as response:
                if response.status!=200:
                    raise ValueError('unexpected response')
                body=bytearray()
                while len(body)<=self._max_bytes:
                    if time.monotonic()>deadline:
                        raise ValueError('request deadline exceeded')
                    part=response.read1(min(65536,self._max_bytes+1-len(body)))
                    if not part:break
                    body.extend(part)
                if len(body)>self._max_bytes:
                    raise ValueError('response too large')
            return json.loads(body)
        except Exception:
            # Do not expose URLs, credentials, server bodies or transport tracebacks.
            raise ValueError('ontology manifest request failed') from None
