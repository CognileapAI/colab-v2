"""런타임 설정. **값이 없어도 프로세스는 뜬다.**

둘 다 없어도 `/healthz` 는 200 이고 `/searches` 는 **뒤진 범위를 먼저 밝힌 정직한 응답**을 낸다.
필수(`:?`)로 걸면 「모델 키가 없다」가 「배포가 죽는다」가 되는데, 그건 정확히
`CLAUDE.md §3` 이 금지한 모양이다 — AI 없이도 v2 는 완결된 제품이다.

⚠ **`COLAB_AI_CATALOG_DB_URL` 이 사라졌다** (2026-08-25 판정 ㈎). 이 단위는 플랫폼 DB(D3)에
붙지 않는다 — 붙을 자리가 있는 한 D10 이 D3 를 읽는 일이 다시 생긴다 (`CLAUDE.md §3-1`).
**`infra/` 배선에 그 변수가 남아 있어도 이제 아무도 읽지 않는다.** 그 정리는 인프라 소유
레인의 몫이라 여기서 건드리지 않고 세션 보고서에 남긴다.

환경변수 이름의 근거
  `OPENAI_API_KEY` · `COLAB_MODEL_HELPER` 는 **이미 배선돼 있다**(`infra/staging/compose.i2.yml`
  ai-service 블록 · `PLAN-SoT §9-㊷`). 이름을 새로 만들지 않고 그 통로를 그대로 소비한다.
"""
from __future__ import annotations

import os
import pathlib
from collections.abc import Mapping
from dataclasses import dataclass

#: D9 사전 DB 의 접속 URL. **값 대신 경로로 받을 수 있다** — `COLAB_AI_DB_URL_FILE`
#: (`PLAN-SoT §9 〈121〉-㉯`). `docker inspect` 의 환경변수 목록에 접속 문자열이 통째로
#: 들어 있어 그 값이 작업 기록에 남았기 때문이다.
ENV_DB_URL = "COLAB_AI_DB_URL"
#: 접미사는 **정확히 `_FILE`** 이다. 읽는 쪽과 배선하는 쪽의 이름이 한 글자라도 어긋나면
#: 배선은 있는데 아무도 안 읽는 상태가 되고, 그것은 에러를 내지 않는다.
FILE_SUFFIX = "_FILE"


def resolve_env_or_file(env: Mapping[str, str], name: str) -> str | None:
    """`<VAR>` 또는 `<VAR>_FILE` 에서 값을 뽑는다 (`PLAN-SoT §9 〈121〉-㉯`).

    ① `_FILE` 이 있으면 그 파일을 읽는다 — **끝의 공백·개행만** 벗긴다(`rstrip`).
    ② 파일이 없거나 못 읽거나 비었으면 **죽는다.** 조용한 폴백은 없다.
       ⚠ 이것은 「값이 없어도 뜬다」와 모순되지 않는다 — **경로를 줬는데 못 읽는 것**은
       「없다」가 아니라 **「배선이 틀렸다」**다. 그 둘을 같은 상태로 보이게 하지 않는다.
    ③ 둘 다 있으면 **죽는다.** 두 출처가 갈리면 어느 것이 진실인지 아무도 모른다.
    ④ 둘 다 없으면 `None` — 지금과 같은 동작이다.
    ⑤ **값을 로그·예외 메시지에 싣지 않는다.** 경로와 사유만 적는다.

    ⚠ 배포 단위는 서로 독립이라 이 판독기를 공유 라이브러리로 빼지 않는다
    (`CLAUDE.md §3-1`). 같은 규칙이 각 단위의 `kernel/` 안에 따로 산다.
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


@dataclass(frozen=True)
class Settings:
    #: D9 사전 3종(`db/ai` 체인) URL. **이 단위가 붙는 유일한 저장소다.**
    dict_db_url: str | None = None
    openai_api_key: str | None = None
    model: str = "gpt-5.6-luna"
    #: 모델 대기 시간(초). 안 답하는 모델이 검색 요청을 붙잡아 두지 않는다.
    model_timeout_seconds: float = 8.0
    #: 질의 해석 방식 — `"literal"`(낱말 그대로) | `"llm"`(모델 해석). **기본은 `literal`.**
    #:
    #: `PLAN-SoT §9 〈136〉` — 정본 결정 2-5 가 이번 릴리즈에서 자연어 검색을 뺐다. 다만
    #: **「빼는 결정이 아니라 순서 결정」**이라 인프라·평가셋·회귀 게이트는 살려 둔다.
    #:
    #: ⚠ **키 유무로 가르지 않는다.** 종전 규칙(「키가 있으면 LLM」)으로 끄려면 키를 빼야
    #: 하는데, 그러면 ① 결정이 코드에 안 보이고 ② Phase 2 에 켤 자리가 안 남으며
    #: ③ **「키를 못 넣은 것」과 「안 쓰기로 한 것」이 같은 상태로 보인다.**
    #: `〈136〉-㉲` 가 요구한 것은 그 반대다 — **켜는 시점을 값으로 정할 수 있어야 한다.**
    query_interpretation: str = "literal"

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "Settings":
        e = os.environ if env is None else env
        # 모르는 값은 **끈 쪽으로** 떨어뜨린다 — 오타가 검색을 몰래 켜지 않는다.
        mode = (e.get("COLAB_AI_QUERY_INTERPRETATION") or "").strip().lower()
        return cls(
            dict_db_url=resolve_env_or_file(e, ENV_DB_URL),
            openai_api_key=e.get("OPENAI_API_KEY") or None,
            model=e.get("COLAB_MODEL_HELPER") or "gpt-5.6-luna",
            query_interpretation="llm" if mode == "llm" else "literal",
        )
