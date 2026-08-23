"""타일 URL 서명 — 렌더 하나에 묶인 단명 자격 (`PLAN-SoT §9-〈68〉`).

**왜 필요한가** — `getRenderTile` 은 **브라우저 지도 위젯이 직접 부르는 유일한 경로**다
(`core-viz.yaml` 이 core-api 프록시를 명시적으로 막았다). 위젯은 서비스 토큰을 가질 수
없고 가져서도 안 된다. 그래서 타일 경로만 **서비스 토큰 또는 서명** 둘 중 하나를 받는다.

**계약을 고치지 않는다** — 서명은 `tileUrlTemplate` **안에** 실린다. 계약은 이 값을
「core 는 해석하지 않고 전달만 한다」는 **불투명 문자열**로 정의했으므로(`core-viz.yaml`
`RenderResult.tileUrlTemplate`), 문자열 안에 무엇이 들었는지는 계약 사항이 아니다.
**FE 는 템플릿을 그대로 쓴다** — `{z}`·`{x}`·`{y}` 치환 말고 할 일이 없다.

**서명이 덮는 것 = `renderId` + 만료 시각.** 타일 좌표(`z/x/y`)는 **일부러 안 덮는다** —
한 렌더의 타일 수백 장이 서명 하나로 서야 지도가 성립하고, 렌더 경계는 이미
`renderId` 가 긋는다. 좌표를 덮으면 템플릿(치환 전 문자열) 자체가 성립하지 않는다.

**한계 (P2 범위)** — 회전·폐기·CDN 캐시 키는 P3·I3 몫이다. 비밀은 설정에서만 온다.
"""
from __future__ import annotations

import hmac
import time
from hashlib import sha256

#: 서명이 담기는 질의 인자 이름. 템플릿 문자열에 그대로 들어간다.
EXP_PARAM = "exp"
SIG_PARAM = "sig"


def sign(secret: str, render_id: str, expires_at: int) -> str:
    """`renderId` 와 만료 시각을 **둘 다** 덮는다.

    ⚠ 만료 시각을 서명에서 빼면 호출자가 `exp` 를 늘려 영구 자격을 만든다.
    구분자(`\\n`)를 두는 것도 같은 이유다 — 이어 붙이면 경계가 흐려진다.
    """
    payload = f"{render_id}\n{expires_at}".encode()
    return hmac.new(secret.encode(), payload, sha256).hexdigest()


def query(secret: str, render_id: str, expires_at: int) -> str:
    return f"{EXP_PARAM}={expires_at}&{SIG_PARAM}={sign(secret, render_id, expires_at)}"


def verify(secret: str, render_id: str, exp: str | None, sig: str | None,
           *, now: float | None = None) -> bool | None:
    """`True` 통과 · `False` 서명 불일치/부재 · `None` **만료**.

    셋을 가르는 이유는 응답 문구가 달라서다 — 「만료됐다」와 「서명이 틀렸다」를
    한 문장으로 뭉치면 FE 가 다시 그려야 할 때와 배선이 틀렸을 때를 구분 못 한다.
    비교는 **상수 시간**으로 한다.
    """
    if not sig or not exp:
        return False
    try:
        deadline = int(exp)
    except ValueError:
        return False
    if not hmac.compare_digest(sign(secret, render_id, deadline), sig):
        return False
    return None if (now if now is not None else time.time()) > deadline else True
