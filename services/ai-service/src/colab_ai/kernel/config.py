"""런타임 설정. **값이 없어도 프로세스는 뜬다.**

셋 다 없어도 `/healthz` 는 200 이고 `/searches` 는 **뒤진 범위를 먼저 밝힌 빈 결과**를 낸다.
필수(`:?`)로 걸면 「모델 키가 없다」가 「배포가 죽는다」가 되는데, 그건 정확히
`CLAUDE.md §3` 이 금지한 모양이다 — AI 없이도 v2 는 완결된 제품이다.

환경변수 이름의 근거
  `OPENAI_API_KEY` · `COLAB_MODEL_HELPER` 는 **이미 배선돼 있다**(`infra/staging/compose.i2.yml`
  ai-service 블록 · `PLAN-SoT §9-㊷`). 이름을 새로 만들지 않고 그 통로를 그대로 소비한다.
  DB URL 둘은 이 레인이 처음 필요로 하는 값이고, `pipeline-worker` 의 `COLAB_PIPELINE_DB_URL`
  관례를 따라 이름을 붙였다. **`infra/` 배선은 이 레인의 소유가 아니다** — 값이 안 오면
  degraded 로 답한다(그 사실을 세션 보고서에 남긴다).
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    #: D3 카탈로그(검색 색인)를 **읽기 전용**으로 붙는 URL. 앱 롤이어야 RLS 가 산다.
    platform_db_url: str | None = None
    #: D9 사전 3종(`db/ai` 체인) URL.
    dict_db_url: str | None = None
    openai_api_key: str | None = None
    model: str = "gpt-5.6-luna"
    #: 모델 대기 시간(초). 안 답하는 모델이 검색 요청을 붙잡아 두지 않는다.
    model_timeout_seconds: float = 8.0

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "Settings":
        e = os.environ if env is None else env
        return cls(
            platform_db_url=e.get("COLAB_AI_CATALOG_DB_URL") or None,
            dict_db_url=e.get("COLAB_AI_DB_URL") or None,
            openai_api_key=e.get("OPENAI_API_KEY") or None,
            model=e.get("COLAB_MODEL_HELPER") or "gpt-5.6-luna",
        )
