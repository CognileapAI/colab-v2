"""인증 판정의 **교체 가능한 경계** (`PLAN-SoT §9 〈90〉-㉮`).

## 이 파일이 하나뿐인 교체 지점이다

인증 **수단**을 바꿀 때 만지는 파일은 **여기 하나**다. 요청 경계(`app/deps.py`)도, 라우터도,
도메인도 수단을 알지 못한다 — 그들이 아는 것은 `Subject` 뿐이다.

정본은 로그인 수단을 **구글 계정 하나**로 못 박았고 비밀번호·다른 소셜 계정을 명시적으로 뺐다
(`PRD_계정과_연구실_소속 §5.1·§5.2`). 다만 그 화면(A-01~A-06)은 **P1 보류**라 1차 범위 밖이고
(`IA_사이트맵 §0` · `README_P1` · P-17), IdP 자격 증명도 이 레포에 없다. 그래서 지금 서는 것은
**심어 둔 접속 코드** 어댑터이고, 구글 어댑터는 인가되는 날 이 파일에 클래스 하나로 들어온다.
그때 계약·화면·요청 경계는 한 글자도 바뀌지 않는다 — 그것이 이 경계를 두는 이유다.

## 두 축을 가른다

  · `Authenticator`  — 이미 있는 자격(bearer 값)을 **주체로 판정**한다. 매 요청이 쓴다.
  · `CredentialIssuer` — 사람의 입력을 **세션으로 바꾼다**. 로그인 op 하나만 쓴다.

두 축이 한 인터페이스에 섞이면, 「토큰 판정만 바꾸고 싶다」와 「발급 수단만 바꾸고 싶다」가
같은 코드를 건드리게 된다.

## 병존 — 대체가 아니다

심어 둔 주체 표(`SubjectRegistry`)는 **그대로 살아 있다**. 도구·시험·기존 staging 설정이 전부
그 토큰을 쓰고 있고, 로그인을 세우면서 그것들을 한꺼번에 끊으면 이 회차가 되돌릴 수 없어진다.
판정은 **표 → 서명 세션** 순으로 훑고, 둘 중 하나가 맞으면 그 주체다.
"""
from __future__ import annotations

import dataclasses
import hashlib
from typing import Protocol, runtime_checkable

from .auth import Subject, SubjectRegistry
from .credentials import CredentialStore
from .password import verify_password
from .session_token import IssuedSession, SessionSigner


@dataclasses.dataclass(frozen=True)
class LoginAttempt:
    """로그인 입력 한 벌. **어느 수단인지는 발급기가 판단한다** — 라우터가 갈래를 알지 않는다."""

    access_code: str | None = None
    account_name: str | None = None
    password: str | None = None

    @property
    def key(self) -> str:
        """시도 제한이 세는 식별자. **비밀번호도 접속 코드 원문도 담지 않는다.**

        ⚠ **종전에는 접속 코드 로그인 전부가 상수 `"code:*"` 한 버킷이었다**
        (`CODE-REVIEW-20260903` #5). 결과 둘 —
          · 누구든 5회 실패시키면 창이 닫힐 때까지 **모든 접속 코드 사용자가 429** 다.
          · 성공 1회가 **전원의 카운터**를 지운다 — 유효 코드 하나를 섞는 추측 공격은
            한 번도 늦춰지지 않는다.
        코드를 해시해 버킷을 가른다. **원문을 키로 쓰지 않는다** — 키는 로그·덤프에
        따라다니고, 접속 코드는 그 자체가 자격이다.
        """
        if self.account_name:
            return f"name:{self.account_name}"
        if self.access_code:
            digest = hashlib.sha256(self.access_code.encode("utf-8")).hexdigest()
            return f"code:{digest[:16]}"
        # 두 형태 중 정확히 하나를 요구하는 것은 라우트(`routes/session.py`)이므로 여기
        # 닿지 않는다. 그래도 **키를 지어내지는 않는다** — 한 버킷으로 접히는 자리를
        # 다시 만들지 않기 위해 이름을 남긴다.
        return "code:없음"


#: 클라이언트 버킷의 접두. 자격 버킷(`name:`·`code:`)과 **한 이름 공간에서 갈린다.**
CLIENT_PREFIX = "client:"
#: 열쇠로 쓸 첫 홉의 길이 상한. 헤더는 사용자가 보내는 값이라 길이를 여기서 묶는다.
_MAX_CLIENT_KEY = 64


def client_key(forwarded_for: str | None) -> str | None:
    """부른 **클라이언트**의 버킷 열쇠 — `X-Forwarded-For` 의 첫 홉.

    **왜 버킷이 둘인가.** 자격 버킷만 두면 코드를 갈아 가며 하는 열거에 브레이크가 없고
    (`key` 를 코드별로 가른 순간 생기는 구멍이다), 클라이언트 버킷만 두면 여러 곳에서 한
    계정을 두드리는 것을 못 센다. 둘을 함께 센다.

    ⚠ **[Ted 판정 대기] 첫 홉은 사용자가 보낸 값이다.** `infra/staging/nginx.i2.conf:61`
    은 `$proxy_add_x_forwarded_for` 를 쓴다 — 들어온 헤더 **뒤에** `$remote_addr` 를 덧붙이는
    변수라, 클라이언트가 헤더를 실어 보내면 그 값이 첫 홉이 되고 **마지막 홉**이 nginx 가
    실제로 본 주소다. 그래서 이 버킷이 늦추는 것은 **헤더를 안 만지는 열거**뿐이고,
    헤더를 돌리는 상대에게는 브레이크가 아니다. 정직한 열쇠는 마지막 홉(또는 nginx 가
    단독으로 세팅하는 별도 헤더)이고, 그 전환은 배포 설정 변경이라 이 레인 밖이다
    (`kernel/throttle.py` 산문이 「IP 로 세지 않는다」고 적은 이유가 바로 이것이다).
    """
    if not forwarded_for:
        return None
    first = forwarded_for.split(",")[0].strip()
    if not first or len(first) > _MAX_CLIENT_KEY:
        return None
    return f"{CLIENT_PREFIX}{first}"



@runtime_checkable
class Authenticator(Protocol):
    """bearer 값 하나 → 주체 또는 None. **이유를 돌려주지 않는다.**"""

    name: str

    def authenticate(self, token: str) -> Subject | None: ...


@runtime_checkable
class CredentialIssuer(Protocol):
    """사람의 입력 → 세션. 실패는 None 이다."""

    name: str

    def issue(self, attempt: LoginAttempt) -> IssuedSession | None: ...


@dataclasses.dataclass(frozen=True)
class StaticTokenAuthenticator:
    """어댑터 ① — 개발자가 심어 둔 주체 표 (P-17). 현행 경로 그대로다."""

    registry: SubjectRegistry
    name: str = "planted-subject-table"

    def authenticate(self, token: str) -> Subject | None:
        return self.registry.resolve(token)


@dataclasses.dataclass(frozen=True)
class SignedSessionAuthenticator:
    """어댑터 ② — 로그인이 발급한 무상태 서명 세션 (`〈90〉-㉯`)."""

    signer: SessionSigner
    name: str = "signed-session"

    def authenticate(self, token: str) -> Subject | None:
        return self.signer.verify(token)


@dataclasses.dataclass(frozen=True)
class PlantedCodeIssuer:
    """발급 어댑터 — 심어 둔 표의 토큰을 **접속 코드**로 받아 세션으로 바꾼다.

    **회원가입이 아니다.** 표에 없는 코드는 계정을 만들지 않고 그냥 None 이다 (P-17).
    """

    registry: SubjectRegistry
    signer: SessionSigner
    name: str = "planted-access-code"

    def issue(self, attempt: LoginAttempt) -> IssuedSession | None:
        if not attempt.access_code:
            return None
        subject = self.registry.resolve(attempt.access_code)
        return None if subject is None else self.signer.issue(subject)


@dataclasses.dataclass(frozen=True)
class PasswordIssuer:
    """발급 어댑터 ② — 계정 이름 + 비밀번호 (Ted 2026-08-26).

    **회원가입이 아니다** (P-17). 자격은 개발자가 `ops/set-password.py` 로 심고,
    저장은 **scrypt 해시뿐**이다 — 평문도 가역 암호화도 두지 않는다.

    ⚠ **계정의 존재 여부를 흘리지 않는다** — 없는 계정과 틀린 비밀번호가 **같은 None** 이다.
    """

    store: CredentialStore
    signer: SessionSigner
    name: str = "planted-password"

    def issue(self, attempt: LoginAttempt) -> IssuedSession | None:
        if not attempt.account_name or not attempt.password:
            return None
        record = self.store.find(attempt.account_name)
        if record is None:
            # 없는 계정에도 **해시 한 번을 태운다** — 즉답으로 돌아가면 응답 시간만으로
            # 계정의 존재 여부를 셀 수 있다.
            self.store.dummy_verify(attempt.password)
            return None
        if not verify_password(attempt.password, record.password):
            return None
        return self.signer.issue(record.subject)


class IssuerChain:
    """발급 어댑터를 순서대로 훑는다. **다음 수단은 여기 한 줄로 들어온다.**"""

    def __init__(self, issuers: tuple[CredentialIssuer, ...]) -> None:
        self._issuers = issuers
        self.name = "+".join(i.name for i in issuers) or "none"

    @property
    def issuers(self) -> tuple[CredentialIssuer, ...]:
        return self._issuers

    def issue(self, attempt: LoginAttempt) -> IssuedSession | None:
        for issuer in self._issuers:
            issued = issuer.issue(attempt)
            if issued is not None:
                return issued
        return None


class AuthenticatorChain:
    """어댑터를 순서대로 훑는다. 하나라도 맞으면 그 주체다.

    빈 사슬은 **모두 거부**한다 — 「검사할 것이 없으니 통과」는 정확히 이 프로젝트가
    게이트에서 금지한 무늬다 (`CLAUDE.md §4` green-by-skip).
    """

    def __init__(self, adapters: tuple[Authenticator, ...]) -> None:
        self._adapters = adapters

    @property
    def adapters(self) -> tuple[Authenticator, ...]:
        return self._adapters

    def resolve(self, token: str) -> Subject | None:
        for adapter in self._adapters:
            subject = adapter.authenticate(token)
            if subject is not None:
                return subject
        return None


def build(*, registry: SubjectRegistry, signer: SessionSigner | None,
          credentials: CredentialStore | None = None,
          ) -> tuple[AuthenticatorChain, CredentialIssuer | None]:
    """⭑ **다음 수단을 더할 때 만지는 함수가 이것 하나다.**

    서명 비밀값이 없으면 세션 어댑터도 발급기도 세우지 않는다 — 없는 것을 있는 척하지 않고,
    로그인 op 이 그 사실을 그대로 말한다 (`routes/session.py`).

    발급 순서 = **비밀번호 → 접속 코드**. 사람이 쓰는 수단이 앞이다.
    """
    adapters: list[Authenticator] = [StaticTokenAuthenticator(registry)]
    if signer is None:
        return AuthenticatorChain(tuple(adapters)), None
    adapters.append(SignedSessionAuthenticator(signer))
    issuers: list[CredentialIssuer] = []
    if credentials is not None and not credentials.empty:
        issuers.append(PasswordIssuer(credentials, signer))
    issuers.append(PlantedCodeIssuer(registry, signer))
    return AuthenticatorChain(tuple(adapters)), IssuerChain(tuple(issuers))
