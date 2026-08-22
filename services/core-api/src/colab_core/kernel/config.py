"""설정 — 환경변수 하나가 값의 유일한 출처다. 코드에 기본 접속 문자열을 박지 않는다."""
from __future__ import annotations

import dataclasses
import os

#: 앱이 접속할 DB. **NOBYPASSRLS · 비소유자 롤**이어야 한다 (ops/app-role.sql).
ENV_DATABASE_URL = "COLAB_CORE_DATABASE_URL"
#: 개발자가 심은 계정의 토큰 표 (P-17). 로그인 흐름은 P1 이다.
ENV_SUBJECTS_FILE = "COLAB_CORE_SUBJECTS_FILE"


@dataclasses.dataclass(frozen=True)
class Settings:
    database_url: str
    subjects_file: str | None


def load_settings() -> Settings:
    url = os.environ.get(ENV_DATABASE_URL, "").strip()
    if not url:
        raise RuntimeError(
            f"{ENV_DATABASE_URL} 가 비었다. 접속 문자열의 기본값을 코드에 두지 않는다 — "
            "설정이 없으면 뜨지 않는 것이 맞다."
        )
    return Settings(database_url=url, subjects_file=os.environ.get(ENV_SUBJECTS_FILE) or None)
