"""Fixed callback transport; no redirects, ambient proxies or response body logs.

Uses the same bounded urllib pattern as core's OntologyHttpClient. Service
packages stay independent: no cross-service production import.
"""
import json
import math
import time
from urllib.parse import urlsplit
from urllib.error import HTTPError
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler
from ..kernel.knowledge_wire import SourceValidateResponse, DeletionValidateResponse


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):return None


class SourceForbidden(ValueError):
    """Authenticated callback rejected the supplied identities, not a retryable outage."""


class SourceAuthorityClient:
    def __init__(self,base_url,*,token,timeout,max_bytes=1024*1024):
        parsed=urlsplit(base_url)
        if (parsed.scheme not in {'http','https'} or not parsed.hostname or parsed.username or parsed.password
            or parsed.query or parsed.fragment or parsed.path not in {'','/'}):raise ValueError('invalid source endpoint')
        if not isinstance(token,str) or not token.strip() or any(c in token for c in '\r\n'):raise ValueError('callback credential required')
        if type(timeout) not in {float,int} or not math.isfinite(timeout) or not 0<timeout<=30:raise ValueError('invalid timeout')
        if type(max_bytes) is not int or not 1<=max_bytes<=1024*1024:raise ValueError('invalid response limit')
        self._url=base_url.rstrip('/')+'/internal/knowledge/source/validate'
        self._token,self._timeout,self._max_bytes=token,timeout,max_bytes
        self._opener=build_opener(ProxyHandler({}),_NoRedirect())

    def request(self,payload,*,session_token):
        return self._request(self._url,payload,session_token=session_token)

    def read(self,receipt,*,session_token):
        return self._request(self._url.rsplit('/',1)[0]+'/read',{'receipt':receipt.model_dump(mode='json')},session_token=session_token)

    def deletion(self,command):
        try:
            return self._request(self._url.replace('/source/','/deletion/'),
                {'command':command.model_dump(mode='json')},session_token=None,deletion=True).status
        except SourceForbidden:
            return 'forbidden'

    def _request(self,url,payload,*,session_token,deletion=False):
        try:
            if not deletion and (not isinstance(session_token,str) or not session_token or len(session_token)>16384 or any(c in session_token for c in '\r\n')):
                raise ValueError('invalid session')
            body=json.dumps(payload,ensure_ascii=False,allow_nan=False).encode()
            if len(body)>1024*1024:raise ValueError('request too large')
            headers={'Authorization':'Bearer '+self._token,'Content-Type':'application/json','Accept':'application/json'}
            if not deletion:headers['X-CoLAB-Session']=session_token
            request=Request(url,data=body,headers=headers)
            deadline=time.monotonic()+self._timeout
            with self._opener.open(request,timeout=self._timeout) as response:
                if response.status!=200:raise ValueError('unexpected response')
                body=bytearray()
                while len(body)<=self._max_bytes:
                    if time.monotonic()>deadline:raise ValueError('deadline exceeded')
                    chunk=response.read1(min(65536,self._max_bytes+1-len(body)))
                    if not chunk:break
                    body.extend(chunk)
                if len(body)>self._max_bytes:raise ValueError('response too large')
            return (DeletionValidateResponse if deletion else SourceValidateResponse).model_validate_json(body)
        except HTTPError as exc:
            status=exc.code
            exc.close()
            if status in {401,403}:raise SourceForbidden('forbidden') from None
            raise ValueError('source authority unavailable') from None
        except Exception:
            raise ValueError('source authority unavailable') from None


class DeletionAuthority:
    """Fixed deletion-only transport; no session or caller-selected endpoint."""
    def __init__(self,client):
        self._client=client

    def validate(self,command):
        return self._client.deletion(command)


class RequestAuthority:
    """Short-lived session token holder; never persisted or printed."""
    def __init__(self,client,session_token):
        self._client,self._session_token=client,session_token

    def validate(self,command,principal):
        try:
            result=self._client.request({'command':command.model_dump(mode='json')},session_token=self._session_token)
        except SourceForbidden:return 'forbidden'
        if result.principal != principal:return 'forbidden'
        return result.status

    def authorize_read(self,receipt):
        result=self._client.read(receipt,session_token=self._session_token)
        if result.status != 'current':raise ValueError(result.status)
        if result.principal.lab_id != receipt.source_key.lab_id:raise ValueError('forbidden')
        return result.principal
