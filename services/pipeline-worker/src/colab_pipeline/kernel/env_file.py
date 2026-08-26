"""환경변수를 **값으로** 받을지 **파일 경로로** 받을지 (`PLAN-SoT §9 〈121〉-㉯`).

`docker inspect` 의 환경변수 목록에 접속 문자열이 통째로 들어 있어 그 값이 작업 기록에
남았다. 자격 파일을 `0600` 으로 두고 **경로만** 넘긴다 — `〈93〉`(주체 표) ·
`〈108〉-㉯`(자격 파일) 과 같은 방식이다.

⚠ 배포 단위는 서로 독립이라 이 판독기를 공유 라이브러리로 빼지 않는다 (`CLAUDE.md §3-1`).
같은 규칙이 core-api·ai-service 의 `kernel/config.py` 안에 따로 산다.
"""
from __future__ import annotations

import pathlib
from collections.abc import Mapping

#: 접미사는 **정확히 `_FILE`** 이다. 읽는 쪽과 배선하는 쪽의 이름이 한 글자라도 어긋나면
#: 배선은 있는데 아무도 안 읽는 상태가 되고, 그것은 에러를 내지 않는다.
FILE_SUFFIX = "_FILE"


def resolve_env_or_file(env: Mapping[str, str], name: str) -> str | None:
    """`<VAR>` 또는 `<VAR>_FILE` 에서 값을 뽑는다.

    ① `_FILE` 이 있으면 그 파일을 읽는다 — **끝의 공백·개행만** 벗긴다(`rstrip`).
       URL 중간의 공백은 손대지 않는다.
    ② 파일이 없거나 못 읽거나 비었으면 **죽는다.** 조용한 폴백은 없다 —
       「검사를 못 한 것은 통과가 아니다」와 같은 계열이다.
    ③ 둘 다 있으면 **죽는다.** 두 출처가 갈리면 어느 것이 진실인지 아무도 모른다.
    ④ 둘 다 없으면 `None` — 지금과 같은 동작이다.
    ⑤ **값을 로그·예외 메시지에 싣지 않는다.** 경로와 사유만 적는다.
    """
    file_env = name + FILE_SUFFIX
    direct = (env.get(name) or "").strip()
    path = (env.get(file_env) or "").strip()
    if path and direct:
        raise RuntimeError(
            f"{name} 와 {file_env} 이 둘 다 설정돼 있다 — 두 출처가 갈리면 어느 것이 "
            "진실인지 아무도 모른다. 하나만 둔다."
        )
    if not path:
        return direct or None
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
