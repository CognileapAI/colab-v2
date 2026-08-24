"""설정 — 환경변수 하나가 값의 유일한 출처다. 코드에 기본 접속 문자열을 박지 않는다."""
from __future__ import annotations

import dataclasses
import os

#: 앱이 접속할 DB. **NOBYPASSRLS · 비소유자 롤**이어야 한다 (ops/app-role.sql).
ENV_DATABASE_URL = "COLAB_CORE_DATABASE_URL"
#: 개발자가 심은 계정의 토큰 표 (P-17). 로그인 흐름은 P1 이다.
ENV_SUBJECTS_FILE = "COLAB_CORE_SUBJECTS_FILE"

#: 미등록 업로드의 수명 — **운영 설정이다** (`PLAN-SoT §9 〈67〉-ⓐ`).
#: 정본(E-04 Policy v2.3)은 규칙 셋만 말하고 **숫자를 갖지 않는다**:
#:   ① 미등록 업로드는 수명이 있다 ② 시계가 처리를 앞지르지 않는다 ③ 만료 뒤에는 404.
#: 그래서 숫자는 여기(운영 설정)에 있고, **판정 로직 안에 상수로 박히지 않는다** —
#: 로직은 언제나 `Settings.upload_ttl_hours` 를 읽는다. 재는 날 값만 바꾼다.
ENV_UPLOAD_TTL_HOURS = "COLAB_CORE_UPLOAD_TTL_HOURS"
#: 초기값 24 — Ted 승인(`〈67〉-ⓐ`).
#: ⚠ **재 본 적 없는 최악 처리 시간 위에 얹힌 값이다.** `DR-11` 의 50 GB 는 가정이고
#: 실증된 최대는 `SEED-DATA` 의 1.3 GB 묶음이다. 값이 정본 밖에 있는 이유가 이것이다.
DEFAULT_UPLOAD_TTL_HOURS = 24

#: 접수한 바이트를 두는 자리. core-api ↔ 스토리지 사이는 **배포 내부 사정**이고 이 seam 의
#: 것이 아니다 (`fe-core.yaml createUpload` 산문). 값이 없으면 접수를 거절한다 —
#: 바이트를 버리고 201 을 내리는 것은 거짓말이다.
ENV_UPLOAD_STORAGE_DIR = "COLAB_CORE_UPLOAD_DIR"

#: 중계 대상 두 곳. 없으면 중계를 시도하지 않고 **정직하게** 답한다
#: (미리보기는 503 성격의 봉투, AI 제안은 `degraded: true` + 0건).
ENV_VIZ_BASE_URL = "COLAB_CORE_VIZ_BASE_URL"
#: viz-render 로 나갈 **서비스 자격 증명** (`core-viz.yaml` `security: [serviceToken]`).
#: ⚠ **이것이 없어서 중계가 실제 viz-render 앞에서 통째로 401 이었다** — 계약이 모든 렌더
#: 표면에 bearer 를 요구하는데 중계는 경계 헤더만 실었고, 시험용 가짜 viz 가 자격 증명을
#: 검사하지 않아 아무도 못 봤다(실서버 2대로 실측). 값이 없으면 **중계를 시도하지 않고
#: 503 을 낸다** — 「토큰이 없으니 안 보낸다」로 통과시키면 저쪽이 검사를 켜는 순간
#: 전 표면이 조용히 죽는다.
ENV_VIZ_SERVICE_TOKEN = "COLAB_CORE_VIZ_SERVICE_TOKEN"
ENV_AI_BASE_URL = "COLAB_CORE_AI_BASE_URL"


@dataclasses.dataclass(frozen=True)
class Settings:
    database_url: str
    subjects_file: str | None
    upload_ttl_hours: int = DEFAULT_UPLOAD_TTL_HOURS
    upload_storage_dir: str | None = None
    viz_base_url: str | None = None
    viz_service_token: str | None = None
    ai_base_url: str | None = None


def _positive_int(name: str, raw: str | None, fallback: int) -> int:
    if raw is None or not raw.strip():
        return fallback
    try:
        value = int(raw.strip())
    except ValueError:
        raise RuntimeError(f"{name} 가 정수가 아니다: {raw!r}") from None
    if value <= 0:
        raise RuntimeError(f"{name} 는 1 이상이어야 한다: {value}")
    return value


def load_settings() -> Settings:
    url = os.environ.get(ENV_DATABASE_URL, "").strip()
    if not url:
        raise RuntimeError(
            f"{ENV_DATABASE_URL} 가 비었다. 접속 문자열의 기본값을 코드에 두지 않는다 — "
            "설정이 없으면 뜨지 않는 것이 맞다."
        )
    return Settings(
        database_url=url,
        subjects_file=os.environ.get(ENV_SUBJECTS_FILE) or None,
        upload_ttl_hours=_positive_int(
            ENV_UPLOAD_TTL_HOURS, os.environ.get(ENV_UPLOAD_TTL_HOURS),
            DEFAULT_UPLOAD_TTL_HOURS),
        upload_storage_dir=os.environ.get(ENV_UPLOAD_STORAGE_DIR) or None,
        viz_base_url=os.environ.get(ENV_VIZ_BASE_URL) or None,
        viz_service_token=os.environ.get(ENV_VIZ_SERVICE_TOKEN) or None,
        ai_base_url=os.environ.get(ENV_AI_BASE_URL) or None,
    )
