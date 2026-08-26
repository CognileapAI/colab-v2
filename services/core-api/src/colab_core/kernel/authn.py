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
from typing import Protocol, runtime_checkable

from .auth import Subject, SubjectRegistry
from .session_token import IssuedSession, SessionSigner


@runtime_checkable
class Authenticator(Protocol):
    """bearer 값 하나 → 주체 또는 None. **이유를 돌려주지 않는다.**"""

    name: str

    def authenticate(self, token: str) -> Subject | None: ...


@runtime_checkable
class CredentialIssuer(Protocol):
    """사람의 입력 → 세션. 실패는 None 이다."""

    name: str

    def issue(self, access_code: str) -> IssuedSession | None: ...


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

    def issue(self, access_code: str) -> IssuedSession | None:
        subject = self.registry.resolve(access_code)
        return None if subject is None else self.signer.issue(subject)


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


def build(*, registry: SubjectRegistry,
          signer: SessionSigner | None) -> tuple[AuthenticatorChain, CredentialIssuer | None]:
    """⭑ **다음 수단을 더할 때 만지는 함수가 이것 하나다.**

    서명 비밀값이 없으면 세션 어댑터도 발급기도 세우지 않는다 — 없는 것을 있는 척하지 않고,
    로그인 op 이 그 사실을 그대로 말한다 (`routes/session.py`).
    """
    adapters: list[Authenticator] = [StaticTokenAuthenticator(registry)]
    issuer: CredentialIssuer | None = None
    if signer is not None:
        adapters.append(SignedSessionAuthenticator(signer))
        issuer = PlantedCodeIssuer(registry, signer)
    return AuthenticatorChain(tuple(adapters)), issuer
