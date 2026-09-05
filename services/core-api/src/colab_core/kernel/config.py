"""설정 — 환경변수 하나가 값의 유일한 출처다. 코드에 기본 접속 문자열을 박지 않는다."""
from __future__ import annotations

import dataclasses
import os
import pathlib
from collections.abc import Mapping

#: 앱이 접속할 DB. **NOBYPASSRLS · 비소유자 롤**이어야 한다 (ops/app-role.sql).
#:
#: ⭑ **값 대신 경로로 받을 수 있다** — `COLAB_CORE_DATABASE_URL_FILE` (`〈121〉-㉯`).
#: `docker inspect` 의 환경변수 목록에 접속 문자열이 통째로 들어 있어 그 값이 작업 기록에
#: 남았다. 자격 파일을 `0600` 으로 두고 **경로만** 넘긴다 — `〈93〉`(주체 표) ·
#: `〈108〉-㉯`(자격 파일) 과 같은 방식이다. 규칙은 `resolve_env_or_file` 에 있다.
ENV_DATABASE_URL = "COLAB_CORE_DATABASE_URL"
#: 접미사는 **정확히 `_FILE`** 이다. 읽는 쪽과 배선하는 쪽의 이름이 한 글자라도 어긋나면
#: 배선은 있는데 아무도 안 읽는 상태가 되고, 그것은 에러를 내지 않는다.
FILE_SUFFIX = "_FILE"


def resolve_env_or_file(env: Mapping[str, str], name: str) -> str | None:
    """`<VAR>` 또는 `<VAR>_FILE` 에서 값을 뽑는다 (`PLAN-SoT §9 〈121〉-㉯`).

    ① `_FILE` 이 있으면 그 파일을 읽는다 — **끝의 공백·개행만** 벗긴다(`rstrip`).
       URL 중간의 공백은 손대지 않는다.
    ② 파일이 없거나 못 읽거나 비었으면 **죽는다.** 조용한 폴백은 없다 —
       「검사를 못 한 것은 통과가 아니다」와 같은 계열이다.
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
#: 개발자가 심은 계정의 토큰 표 (P-17). 로그인이 서도 이 표는 **그대로 남는다** —
#: 도구·시험·기존 배포 설정이 이 토큰으로 붙어 있고, 병존이 `〈90〉-㉱` 의 결정이다.
ENV_SUBJECTS_FILE = "COLAB_CORE_SUBJECTS_FILE"

#: 세션 서명 비밀값 (`PLAN-SoT §9 〈90〉-㉯`). **없으면 로그인을 세우지 않는다** —
#: 서명 없는 세션은 아무나 위조할 수 있고, 그것은 인증이 아니다. 기본값을 코드에 두지 않는 이유도
#: 같다(`ENV_DATABASE_URL` 과 같은 규칙).
#:
#: ⭑ **값 대신 경로로 받는다** — `COLAB_CORE_SESSION_SECRET_FILE` (`CODE-REVIEW-20260903` #15).
#: 이것이 생 env 뿐이라 `compose.i2.yml` 이 **세션 서명 HMAC 키**를 `docker inspect` 로
#: 읽히는 자리에 뒀다 — 그 키 하나면 임의의 accountId/labId 토큰을 위조해 **모든 연구실
#: 경계가 무력**해진다. 게다가 `_FILE` 을 설정하면 오류 없이 무시돼 로그인이 500 만 냈다.
ENV_SESSION_SECRET = "COLAB_CORE_SESSION_SECRET"
#: 세션 수명(분). **[정본 무근거]** — 정본에 「세션」이라는 낱말 자체가 없다(2026-08-26 전수 조사).
#: 그래서 숫자를 정본인 척 적지 않고 **운영 설정**에 둔다 (`〈90〉-㉲`).
ENV_SESSION_TTL_MINUTES = "COLAB_CORE_SESSION_TTL_MINUTES"
#: 초기값 720 분(12 시간) — 근무 한 나절을 다시 로그인하지 않고 쓰는 값이다. 근거는 정본이 아니라
#: 이 값 하나뿐이며, Ted 판정으로 바뀔 수 있다.
DEFAULT_SESSION_TTL_MINUTES = 720

#: 자격 파일 — 계정 이름 → 주체 ＋ **비밀번호 해시** (`PLAN-SoT §9 〈108〉-㉯`).
#: 주체 표와 갈라 둔다: 파일 권한(`0600`)과 배포 경로를 따로 쥐기 위해서다.
#: 값이 없으면 비밀번호 어댑터가 서지 않는다 — 접속 코드 경로는 그대로 돈다.
ENV_CREDENTIALS_FILE = "COLAB_CORE_CREDENTIALS_FILE"

#: 로그인 시도 제한 (`〈108〉-㉰`). **[정본 무근거]** — 정본은 비밀번호도 시도 제한도 다루지 않는다.
ENV_LOGIN_MAX_FAILURES = "COLAB_CORE_LOGIN_MAX_FAILURES"
ENV_LOGIN_WINDOW_SECONDS = "COLAB_CORE_LOGIN_WINDOW_SECONDS"
#: 초기값 = 창 900 초(15 분) 안에 실패 5 회. 사전 추측을 느리게 만드는 최소선이고,
#: 사람이 오타로 잠기지 않는 선이다. 근거는 이 값 하나뿐이며 Ted 판정으로 바뀐다.
DEFAULT_LOGIN_MAX_FAILURES = 5
DEFAULT_LOGIN_WINDOW_SECONDS = 900

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

#: 접수한 바이트를 두는 자리(저장 모드 local 일 때). core-api ↔ 스토리지 사이는
#: **배포 내부 사정**이고 이 seam 의 것이 아니다 (`fe-core.yaml createUpload` 산문).
#: 값이 없으면 프로세스마다 한 번 만드는 임시 디렉터리를 쓴다 — 바이트를 버리고
#: 201 을 내리지 않기 위해서다 (`routes/ingestion.py` 의 실동작과 일치시킨 서술).
ENV_UPLOAD_STORAGE_DIR = "COLAB_CORE_UPLOAD_DIR"

#: 업로드 저장 백엔드 — `local`(로컬 디스크, 기본) | `s3` (`PLAN-SoT §9 〈337〉`).
#: 로컬 개발은 local 이 기본값이라 아무 설정 없이 지금까지와 같이 돈다.
#: s3 를 켜려면 버킷·리전이 **함께** 있어야 한다 — 반쪽 설정이면 뜨지 않는 것이 맞다.
#: AWS 자격증명은 표준 환경변수 사슬(`kernel/aws_credentials.py` — env→ECS→IMDSv2)로 온다.
ENV_STORAGE_MODE = "COLAB_CORE_STORAGE_MODE"
ENV_S3_BUCKET = "COLAB_CORE_S3_BUCKET"
ENV_S3_REGION = "COLAB_CORE_S3_REGION"
STORAGE_MODES = ("local", "s3")

#: 중계 대상 두 곳. 없으면 중계를 시도하지 않고 **정직하게** 답한다
#: (미리보기는 503 성격의 봉투, AI 제안은 `degraded: true` + 0건).
ENV_VIZ_BASE_URL = "COLAB_CORE_VIZ_BASE_URL"
#: viz-render 로 나갈 **서비스 자격 증명** (`core-viz.yaml` `security: [serviceToken]`).
#: ⚠ **이것이 없어서 중계가 실제 viz-render 앞에서 통째로 401 이었다** — 계약이 모든 렌더
#: 표면에 bearer 를 요구하는데 중계는 경계 헤더만 실었고, 시험용 가짜 viz 가 자격 증명을
#: 검사하지 않아 아무도 못 봤다(실서버 2대로 실측). 값이 없으면 **중계를 시도하지 않고
#: 503 을 낸다** — 「토큰이 없으니 안 보낸다」로 통과시키면 저쪽이 검사를 켜는 순간
#: 전 표면이 조용히 죽는다.
#:
#: ⭑ **값 대신 경로로 받는다** — `COLAB_CORE_VIZ_SERVICE_TOKEN_FILE`
#: (`CODE-REVIEW-20260903` #15 · 세션 비밀값과 같은 규칙).
ENV_VIZ_SERVICE_TOKEN = "COLAB_CORE_VIZ_SERVICE_TOKEN"
ENV_AI_BASE_URL = "COLAB_CORE_AI_BASE_URL"


@dataclasses.dataclass(frozen=True)
class Settings:
    database_url: str
    subjects_file: str | None
    session_secret: str | None = None
    session_ttl_minutes: int = DEFAULT_SESSION_TTL_MINUTES
    credentials_file: str | None = None
    login_max_failures: int = DEFAULT_LOGIN_MAX_FAILURES
    login_window_seconds: int = DEFAULT_LOGIN_WINDOW_SECONDS
    upload_ttl_hours: int = DEFAULT_UPLOAD_TTL_HOURS
    upload_storage_dir: str | None = None
    storage_mode: str = "local"
    s3_bucket: str | None = None
    s3_region: str | None = None
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


def _storage_settings() -> tuple[str, str | None, str | None]:
    # ⚠ **배포에서 이 기본값(`local`)에 기대지 않는다.** 안 주면 조용히 로컬 모드가 이기고,
    #    업로드는 성공한 것처럼 보이면서 **바이트가 EC2 디스크에만 쌓인다** — 재배포·인스턴스
    #    재생성으로 사라지고 `pg_dump` 백업에도 RDS 스냅샷에도 안 들어간다. 그래서 dev compose 는
    #    이 값을 **치환이 아니라 리터럴**로 박았다(`docs/DEPLOY.md §2-1`). 로컬은 local 이 정상이고,
    #    배포는 s3 가 정상이다. 어긋남은 `GET /healthz/storage` 와 doctor ⑪ 이 잡는다.
    mode = (os.environ.get(ENV_STORAGE_MODE) or "local").strip().lower()
    if mode not in STORAGE_MODES:
        raise RuntimeError(
            f"{ENV_STORAGE_MODE} 가 모르는 값이다: {mode!r} — {'|'.join(STORAGE_MODES)} 중 하나. "
            "오타를 local 로 조용히 접으면 dev 가 로컬 디스크에 쓰고도 아무도 모른다."
        )
    bucket = os.environ.get(ENV_S3_BUCKET) or None
    region = os.environ.get(ENV_S3_REGION) or None
    if mode == "s3" and not (bucket and region):
        missing = [n for n, v in ((ENV_S3_BUCKET, bucket), (ENV_S3_REGION, region)) if not v]
        raise RuntimeError(
            f"저장 모드가 s3 인데 {' 와 '.join(missing)} 가 없다 — 반쪽 설정이면 뜨지 않는 것이 맞다."
        )
    return mode, bucket, region


def load_settings() -> Settings:
    url = resolve_env_or_file(os.environ, ENV_DATABASE_URL)
    if not url:
        raise RuntimeError(
            f"{ENV_DATABASE_URL} (또는 {ENV_DATABASE_URL}{FILE_SUFFIX}) 가 비었다. "
            "접속 문자열의 기본값을 코드에 두지 않는다 — 설정이 없으면 뜨지 않는 것이 맞다."
        )
    storage_mode, s3_bucket, s3_region = _storage_settings()
    return Settings(
        database_url=url,
        subjects_file=os.environ.get(ENV_SUBJECTS_FILE) or None,
        # ⭑ **비밀값 둘도 `_FILE` 로 받는다** (`CODE-REVIEW-20260903` #15). DB URL 과 같은
        # 판독기다 — 종전에는 이 둘만 생 env 라 `compose.i2.yml` 이 세션 서명 HMAC 키와
        # 서비스 토큰을 `docker inspect` 로 읽히는 자리에 뒀고, `_FILE` 을 설정하면
        # **오류 없이 무시**돼 로그인이 500 만 내는 조용한 실패가 났다.
        # **뒤로 호환된다** — 생 env 만 있으면 지금과 같다.
        session_secret=resolve_env_or_file(os.environ, ENV_SESSION_SECRET),
        session_ttl_minutes=_positive_int(
            ENV_SESSION_TTL_MINUTES, os.environ.get(ENV_SESSION_TTL_MINUTES),
            DEFAULT_SESSION_TTL_MINUTES),
        credentials_file=os.environ.get(ENV_CREDENTIALS_FILE) or None,
        login_max_failures=_positive_int(
            ENV_LOGIN_MAX_FAILURES, os.environ.get(ENV_LOGIN_MAX_FAILURES),
            DEFAULT_LOGIN_MAX_FAILURES),
        login_window_seconds=_positive_int(
            ENV_LOGIN_WINDOW_SECONDS, os.environ.get(ENV_LOGIN_WINDOW_SECONDS),
            DEFAULT_LOGIN_WINDOW_SECONDS),
        upload_ttl_hours=_positive_int(
            ENV_UPLOAD_TTL_HOURS, os.environ.get(ENV_UPLOAD_TTL_HOURS),
            DEFAULT_UPLOAD_TTL_HOURS),
        upload_storage_dir=os.environ.get(ENV_UPLOAD_STORAGE_DIR) or None,
        storage_mode=storage_mode,
        s3_bucket=s3_bucket,
        s3_region=s3_region,
        viz_base_url=os.environ.get(ENV_VIZ_BASE_URL) or None,
        viz_service_token=resolve_env_or_file(os.environ, ENV_VIZ_SERVICE_TOKEN),
        ai_base_url=os.environ.get(ENV_AI_BASE_URL) or None,
    )
