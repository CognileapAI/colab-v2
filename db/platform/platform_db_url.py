"""platform 체인의 접속 URL 판독기 (`PLAN-SoT §9 〈121〉-㉯`).

`COLAB_PLATFORM_DB_URL` 은 값으로도, **`COLAB_PLATFORM_DB_URL_FILE` 로 경로로도** 들어온다.
`docker inspect` 의 환경변수 목록에 접속 문자열이 통째로 들어 있어 그 값이 작업 기록에
남았기 때문이다 — 자격 파일을 `0600` 으로 두고 경로만 넘긴다.

⚠ **ai 체인과 공유하지 않는다.** 두 체인은 마이그레이션 체인이 갈라져 있고(`CLAUDE.md §3-3`)
그 분리를 「같은 헬퍼를 쓰니까」로 도로 붙이지 않는다. 같은 규칙이 `db/ai/ai_db_url.py` 에
따로 산다.
"""
from __future__ import annotations

import os
import pathlib
from collections.abc import Mapping

ENV = "COLAB_PLATFORM_DB_URL"
#: 접미사는 **정확히 `_FILE`** 이다. 읽는 쪽과 배선하는 쪽의 이름이 한 글자라도 어긋나면
#: 배선은 있는데 아무도 안 읽는 상태가 되고, 그것은 에러를 내지 않는다.
FILE_SUFFIX = "_FILE"


def resolve_db_url(env: Mapping[str, str] | None = None) -> str:
    """접속 URL 을 돌려준다. 없으면 `""` — 지금과 같은 동작이다.

    ① `_FILE` 이 있으면 그 파일을 읽는다 — **끝의 공백·개행만** 벗긴다(`rstrip`).
    ② 파일이 없거나 못 읽거나 비었으면 **죽는다.** 조용한 폴백은 없다.
    ③ 둘 다 있으면 **죽는다.** 두 출처가 갈리면 어느 것이 진실인지 아무도 모른다.
    ④ 둘 다 없으면 `""`.
    ⑤ **값을 로그·예외 메시지에 싣지 않는다.** 경로와 사유만 적는다.
    """
    e = os.environ if env is None else env
    file_env = ENV + FILE_SUFFIX
    direct = (e.get(ENV) or "").strip()
    path = (e.get(file_env) or "").strip()
    if path and direct:
        raise RuntimeError(
            f"{ENV} 와 {file_env} 이 둘 다 설정돼 있다 — 두 출처가 갈리면 어느 것이 "
            "진실인지 아무도 모른다. 하나만 둔다."
        )
    if not path:
        return direct
    try:
        raw = pathlib.Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(
            f"{file_env} 이 가리키는 파일을 읽지 못했다: {path} "
            f"({type(exc).__name__}) — 못 읽은 것을 빈 값으로 넘기지 않는다."
        ) from None
    value = raw.rstrip()
    if not value:
        raise RuntimeError(f"{file_env} 이 가리키는 파일이 비었다: {path}")
    return value
