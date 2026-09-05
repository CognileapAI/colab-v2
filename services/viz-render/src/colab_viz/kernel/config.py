"""설정 — 값의 근거를 값 옆에 적는다.

`max_render_bytes` 만 정본에서 오고(그것도 `[가정]` 표시가 붙어 있다) 나머지는 레포 결정이다.

**소스 모드·미리보기 싱크**(`PLAN-SoT §9 〈342〉-㉱·㉴`) — `local`(기본) | `s3`. **모르는 값은 기동 거부**다:
오타를 local 로 조용히 접으면 dev 가 EC2 디스크를 읽고도 아무도 모른다(core `COLAB_CORE_STORAGE_MODE`
와 같은 규칙). s3 는 버킷·리전·작업 디렉터리·**상한**이 전부 있어야 뜬다. 상한은 3상태다 —
숫자 · `none`(명시 무제한) · 미설정(**거부**) — 「없으면 무제한」은 green-by-skip 의 같은 모양이다.
"""
from __future__ import annotations

import math
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

#: 접미사는 **정확히 `_FILE`** 이다. 읽는 쪽과 배선하는 쪽의 이름이 한 글자라도 어긋나면
#: 배선은 있는데 아무도 안 읽는 상태가 되고, 그것은 에러를 내지 않는다.
FILE_SUFFIX = "_FILE"


def resolve_env_or_file(env: Mapping[str, str], name: str) -> str | None:
    """`<VAR>` 또는 `<VAR>_FILE` 에서 값을 뽑는다 (`PLAN-SoT §9 〈121〉-㉯` 와 같은 규칙).

    ① `_FILE` 이 있으면 그 파일을 읽는다 — **끝의 공백·개행만** 벗긴다(`rstrip`).
    ② 파일이 없거나 못 읽거나 비었으면 **죽는다.** 조용한 폴백은 없다 —
       「검사를 못 한 것은 통과가 아니다」와 같은 계열이다.
    ③ 둘 다 있으면 **죽는다.** 두 출처가 갈리면 어느 것이 진실인지 아무도 모른다.
    ④ 둘 다 없으면 `None` — 지금과 같은 동작이다(표면이 503 을 낸다).
    ⑤ **값을 로그·예외 메시지에 싣지 않는다.** 경로와 사유만 적는다.

    ⭑ ⟨2026-09-03 · 코드리뷰 #15⟩ **이 단위에는 이 장치 자체가 없었다.** 서비스 토큰과
    타일 서명 비밀이 생 env 로 들어와 `docker inspect` 한 번에 드러났고,
    `COLAB_VIZ_TILE_SIGNING_SECRET_FILE` 을 설정해도 **오류 없이 무시**돼 표면이 조용히
    503 만 냈다 — 무시된 변수 이름은 어디에도 안 나왔다.

    ⚠ **손사본이다.** core-api `kernel/config.resolve_env_or_file` 과 규칙이 같고 글자도
    거의 같다. 배포 단위가 서로 독립이라 공유 라이브러리로 빼지 않는 것이 이 레포의
    규율이지만(`CLAUDE.md §3-1`), 같은 규칙이 두 벌로 사는 것은 **codegen 통일 후보**다
    (`CODE-REVIEW-20260903-PLAN.md §4` 유보 1 — `ids.py`·`errors.py` 와 같은 묶음).
    """
    file_env = name + FILE_SUFFIX
    direct = (env.get(name) or "").strip()
    path = (env.get(file_env) or "").strip()
    if path and direct:
        raise RuntimeError(
            f"{name} 와 {file_env} 이 둘 다 설정돼 있다 — 두 출처가 갈리면 어느 것이 "
            "진실인지 아무도 모른다. 하나만 둔다.")
    if not path:
        return direct or None
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(
            f"{file_env} 이 가리키는 파일을 읽지 못했다: {path} "
            f"({type(exc).__name__}) — 못 읽은 것을 빈 값으로 넘기지 않는다.") from None
    value = raw.rstrip()
    if not value:
        raise RuntimeError(f"{file_env} 이 가리키는 파일이 비었다: {path}")
    return value

#: 정본 `Policy_데이터셋_상세 §8` — 「미리보기는 500MB까지 그려요」 **[가정]**.
#: 정본이 스스로 가정이라 표시한 값이라 우리도 그 표시를 지우지 않는다.
DEFAULT_MAX_RENDER_BYTES = 500 * 1024 * 1024

#: 등록 전 업로드 미리보기의 수명. **`NB-2` — 정본에 구체적 시간이 없다.**
#: 계약도 "레포 결정이며 값은 발행자가 채운다"로 열어 뒀다. 1시간은 레포 결정이다.
DEFAULT_RESULT_TTL_SECONDS = 3600

#: 한 렌더가 넘기면 「시간 초과」인 벽시계 예산. **[정본 무근거]** — 정본은 상황만 말한다.
DEFAULT_RENDER_DEADLINE_SECONDS = 120.0

#: 타일 서명의 수명 (`〈68〉-ⓓ` — 「서명 수명은 렌더 결과 수명 안에 든다」).
#: **결과 수명과 같은 값으로 둔다.** 더 짧게 잡으면 렌더는 살아 있는데 지도만 401 이 되고,
#: 다시 그리는 것 말고 갱신 경로가 없다(FE 는 템플릿을 그대로 쓸 뿐이다). 실제 만료는
#: 발급 시점에 **작업의 `expires_at` 로 한 번 더 깎인다** — 둘 중 이른 쪽이 이긴다.
#: ⚠ 서명 회전·폐기는 P2 범위가 아니다(`〈68〉` 한계 절).
DEFAULT_TILE_SIGNATURE_TTL_SECONDS = DEFAULT_RESULT_TTL_SECONDS

#: **갈래 스위치의 기본값 — 「한 장」이다** (`〈240〉` · 정본 `Policy_데이터셋_상세` v2.7 `§8`).
#: 정본 260826 델타가 축자로 「타일 서버도 바탕 지도도 쓰지 않는다」(POL-021)·「미리보기
#: 뷰어 = 타일 서버·바탕 지도 없이 **PNG 한 장 + 경계 좌표 4값**」이라 적었다. 그래서
#: **선언이 없으면 한 장이다.** 타일은 A/B 비교를 위해 **명시로 켰을 때만** 실린다.
#: ⚠ 값은 홈 env(`COLAB_VIZ_TILE_BRANCH`)에서 온다 — 레포에 켜진 값을 박지 않는다.
DEFAULT_TILE_BRANCH_ENABLED = False

#: 「켜짐」으로 읽는 표기. 그 밖의 모든 값(빈 문자열 포함)은 **꺼짐**이다 — 오타가
#: 조용히 타일을 켜지 않게, 켜는 쪽만 열거한다.
TILE_BRANCH_ON_VALUES = frozenset({"1", "true", "on", "yes"})


def _tile_branch_from_env(raw: str | None) -> bool:
    """스위치 한 자리 — **모르는 값은 꺼짐이다.**"""
    return (raw or "").strip().lower() in TILE_BRANCH_ON_VALUES


#: 트리거 버스를 비우는 주기(초) — **`#60` 의 실행자 간격**. pipeline-worker 의
#: `serve(interval_seconds=5.0)` 와 **같은 값**이다: 내는 쪽이 5초 간격으로 돌므로
#: 받는 쪽을 그보다 촘촘히 해도 볼 것이 없고, 더 성기게 하면 재생성만 늦는다.
DEFAULT_TRIGGER_POLL_SECONDS = 5.0


#: **지도 타일 회수의 세 값**(`TL-1` ⑹ · Ted 판정 「도는 배경 루프에 얹는다」).
#: ⚠ **기본은 관측 전용이다** — 선언이 없으면 세고 적기만 하고 **0건 지운다.** 자동
#:   삭제를 기본값으로 켜지 않는다: 첫 배포가 계수를 먼저 증명하고 그 다음에 켠다.
#:   켜는 자리는 배포 env 한 곳(`COLAB_VIZ_TILE_RECLAIM_APPLY`)뿐이고, 레포에 켜진 값을
#:   박지 않는다(`COLAB_VIZ_TILE_BRANCH` 와 같은 규율).
DEFAULT_TILE_RECLAIM_APPLY = False

#: 한 바퀴가 지울 수 있는 벌 수의 뚜껑. 정본은 `d7_visualization/tile_reclaim.py` 다.
DEFAULT_TILE_RECLAIM_MAX_KEYS = 20

#: 회수 주기(초) — **트리거 주기(5초)와 다르다.** 한 바퀴가 주체 전건의 다이제스트를
#: 다시 뜨므로 촘촘히 돌리면 저장소를 반복해서 읽는다.
DEFAULT_TILE_RECLAIM_INTERVAL_SECONDS = 3600.0


#: 미리보기 격자의 한 변 상한. 전체 적재 금지(`DR-11`)의 렌더 쪽 표현이다 — 레포 결정.
DEFAULT_MAX_PREVIEW_SIDE = 1024


#: 배선이 아직 안 된 환경에서 쓰는 자리. `infra/` 는 이 레인의 소유 디렉터리가 아니라
#: (`P2-EXEC §3` 레인 표) 환경변수 주입을 여기서 못 넣는다 — 그래서 **없으면 뜨지 않는
#: 대신, 뜨되 렌더 표면이 503 을 낸다.** 인증 없이 열어 두는 것과 다르다.
DEFAULT_SOURCE_ROOT = Path("/srv/viz-sources")

#: 미리보기 3층 산출물이 놓이는 자리. **정적 자산이다** — 렌더 작업으로 매번 만드는
#: 물건이 아니고(`〈80〉-㉯ 2`), 목록 썸네일도 같은 자리에서 서빙된다.
#: ⚠ 서빙 자체는 이 레인이 아니다 — `imageUrl` 은 계약이 **불투명 문자열**로 둔 자리라
#: core 도 해석하지 않는다(`core-viz.yaml`).
DEFAULT_PREVIEW_DIR = Path("/srv/viz-previews")
DEFAULT_PREVIEW_URL_BASE = "/previews"

SOURCE_MODES = ("local", "s3")
PREVIEW_SINKS = ("local", "s3")
DEFAULT_PREVIEW_S3_PREFIX = "previews"

ENV_SOURCE_MODE = "COLAB_VIZ_SOURCE_MODE"
ENV_S3_BUCKET = "COLAB_VIZ_S3_BUCKET"
ENV_S3_REGION = "COLAB_VIZ_S3_REGION"
ENV_WORKDIR = "COLAB_VIZ_WORKDIR"
ENV_WORK_MAX_BYTES = "COLAB_VIZ_WORK_MAX_BYTES"
ENV_PREVIEW_SINK = "COLAB_VIZ_PREVIEW_SINK"
ENV_PREVIEW_S3_PREFIX = "COLAB_VIZ_PREVIEW_S3_PREFIX"


@dataclass(frozen=True)
class Settings:
    source_root: Path
    #: None 이면 **자격 증명이 배선되지 않은 것**이다. 열어 두지 않고 503 을 낸다.
    service_token: str | None
    #: 타일 URL 서명 비밀 (`〈68〉`). **None 이면 배선 안 된 것**이고 렌더 표면은 503 이다 —
    #: 「비밀이 없으니 서명 검사를 건너뛴다」는 곧 타일을 아무나 여는 것이다.
    tile_signing_secret: str | None = None
    execution: str = "thread"                  # thread | inline | manual
    max_render_bytes: int = DEFAULT_MAX_RENDER_BYTES
    result_ttl_seconds: int = DEFAULT_RESULT_TTL_SECONDS
    render_deadline_seconds: float = DEFAULT_RENDER_DEADLINE_SECONDS
    max_preview_side: int = DEFAULT_MAX_PREVIEW_SIDE
    #: **어느 갈래로 낼 것인가** (`〈240〉`). `False` 면 `imageUrl` 한 장, `True` 면
    #: 지도형·등록 데이터셋·서명 비밀 셋이 다 갖춰졌을 때 `tileUrlTemplate`.
    #: **기본값은 한 장이다** — 정본 문면이 그쪽이고, 타일은 A/B 를 위해 켜는 것이다.
    tile_branch_enabled: bool = DEFAULT_TILE_BRANCH_ENABLED
    tile_url_base: str = "/viz/v1"
    tile_signature_ttl_seconds: int = DEFAULT_TILE_SIGNATURE_TTL_SECONDS
    preview_dir: Path = DEFAULT_PREVIEW_DIR
    preview_url_base: str = DEFAULT_PREVIEW_URL_BASE
    #: **D5 가 낸 트리거가 놓이는 이벤트 버스**(`〈253〉` · 12차 해제 · `Y-1`).
    #: `None` 이면 배선이 안 된 것이고, **자리를 지어내지 않는다** — 트리거는 안 오고
    #: 사람이 부르는 경로(「미리보기 다시 만들기」)는 그대로 남는다(완료 정의 ⓒ).
    #: ⚠ pipeline-worker 의 `COLAB_WORKER_EVENT_SPOOL` 과 **같은 자리**여야 한다.
    trigger_spool: Path | None = None
    #: 버스를 비우는 주기(초). **버스 자리가 있을 때만 의미가 있다** — 자리가 없으면
    #: 루프 자체가 서지 않는다.
    trigger_poll_seconds: float = DEFAULT_TRIGGER_POLL_SECONDS
    #: **지운다/안 지운다** — 기본은 안 지운다(관측 전용).
    tile_reclaim_apply: bool = DEFAULT_TILE_RECLAIM_APPLY
    tile_reclaim_max_keys: int = DEFAULT_TILE_RECLAIM_MAX_KEYS
    tile_reclaim_interval_seconds: float = DEFAULT_TILE_RECLAIM_INTERVAL_SECONDS

    #: 소스 모드 — `local`(디스크, `source_root`) | `s3`(버킷 → `workdir` 로 내려받기). `〈342〉-㉴`
    source_mode: str = "local"
    s3_bucket: str | None = None
    s3_region: str | None = None
    workdir: Path | None = None
    #: 작업 디렉터리 상한(바이트). `math.inf` = 명시 무제한. None = 미설정(s3 모드에선 거부).
    work_max_bytes: float | None = None
    #: 미리보기 싱크 — `local`(디스크를 nginx 가 서빙) | `s3`(데이터 버킷 `previews/`). `〈342〉-㉮`
    preview_sink: str = "local"
    preview_s3_prefix: str = DEFAULT_PREVIEW_S3_PREFIX

def _positive_int_from_env(raw: str | None, default: int) -> int:
    """**못 읽는 값·0·음수는 기본값이다.** 뚜껑이 오타 하나로 사라지지 않게 한다."""
    try:
        value = int((raw or "").strip())
    except ValueError:
        return default
    return value if value > 0 else default


def _positive_float_from_env(raw: str | None, default: float) -> float:
    try:
        value = float((raw or "").strip())
    except ValueError:
        return default
    return value if value > 0 else default


def _poll_seconds_from_env(raw: str | None) -> float:
    """**못 읽는 값은 기본값이다.** 오타 하나로 루프가 안 뜨거나 폭주하지 않게 한다."""
    try:
        value = float((raw or "").strip())
    except ValueError:
        return DEFAULT_TRIGGER_POLL_SECONDS
    return value if value > 0 else DEFAULT_TRIGGER_POLL_SECONDS


def parse_work_max_bytes(raw: str | None) -> float | None:
    """3상태 — 숫자(양의 정수) · `none`(명시 무제한, `math.inf`) · 미설정/공백(None). 그 외는 거부."""
    if raw is None:
        return None
    text = raw.strip()
    if not text:
        return None
    if text.lower() == "none":
        return math.inf
    if not text.isdigit() or int(text) <= 0:
        raise RuntimeError(
            f"{ENV_WORK_MAX_BYTES} 가 규칙에 맞지 않는다: {raw!r} — 양의 정수(바이트) 또는 `none`(명시 무제한)")
    return int(text)


def _mode(raw: str | None, *, env_name: str, allowed: tuple[str, ...]) -> str:
    value = (raw or "local").strip().lower() or "local"
    if value not in allowed:
        raise RuntimeError(f"{env_name} 가 모르는 값이다: {value!r} — {'|'.join(allowed)} 중 하나. "
                           "모르는 값을 local 로 접지 않는다")
    return value


def validate(settings: Settings) -> Settings:
    """반쪽 설정을 그 이름을 말하며 거부한다. `load_settings` 와 `create_app` 둘 다 부른다."""
    _mode(settings.source_mode, env_name=ENV_SOURCE_MODE, allowed=SOURCE_MODES)
    _mode(settings.preview_sink, env_name=ENV_PREVIEW_SINK, allowed=PREVIEW_SINKS)
    if settings.source_mode == "s3" or settings.preview_sink == "s3":
        missing = [n for n, v in ((ENV_S3_BUCKET, settings.s3_bucket), (ENV_S3_REGION, settings.s3_region))
                   if not v]
        if missing:
            raise RuntimeError(f"s3 를 쓰는데 {' · '.join(missing)} 가 없다 — 반쪽 설정으로 뜨지 않는다")
    if settings.source_mode == "s3":
        if settings.workdir is None:
            raise RuntimeError(f"{ENV_SOURCE_MODE}=s3 인데 {ENV_WORKDIR} 가 없다 — 내려받을 자리가 없다")
        if settings.work_max_bytes is None:
            raise RuntimeError(
                f"{ENV_SOURCE_MODE}=s3 인데 {ENV_WORK_MAX_BYTES} 가 없다 — 상한은 숫자 또는 `none`(명시 무제한)으로 적는다")
    return settings


def load_settings() -> Settings:
    """환경에서 읽는다.

    **자격 증명이 없어도 프로세스는 뜬다** — 헬스(`/healthz`)는 배포 배관이라 살아 있어야
    하고, staging 은 지금 이 단위를 헬스로만 보고 있다. 대신 **렌더 표면은 열리지 않고
    503 을 낸다**(계약이 5xx 자리를 이미 뒀다). 인증을 조용히 끄는 것과 정반대다.
    반면 **저장 모드의 반쪽 설정은 뜨지 않는다** — 읽을 자리가 없는 렌더러는 살아 있다고 대답만 한다.
    ⚠ 환경변수 주입은 `infra/*/compose.*.yml` 이 할 일이고 이 레인의 소유가 아니다.
    """
    root = os.environ.get("COLAB_VIZ_SOURCE_ROOT")
    workdir = os.environ.get(ENV_WORKDIR)
    settings = Settings(
        source_root=Path(root) if root else DEFAULT_SOURCE_ROOT,
        # ⭑ ⟨2026-09-03 · 코드리뷰 #15⟩ **값 대신 경로로 받을 수 있다**(`_FILE`).
        # 생 env 로 넘기면 `docker inspect` 한 번에 드러난다 — DB 비밀번호가 작업 기록에
        # 새어 core-api 가 `_FILE` 을 도입했던 바로 그 경로다.
        service_token=resolve_env_or_file(os.environ, "COLAB_VIZ_SERVICE_TOKEN"),
        # **비밀을 코드에 박지 않는다.** 없으면 None 이고 렌더 표면은 503 이다 —
        # 기본값을 하나 지어 넣으면 그것이 모든 배포에서 같은 비밀이 된다.
        tile_signing_secret=resolve_env_or_file(os.environ,
                                                "COLAB_VIZ_TILE_SIGNING_SECRET"),
        execution=os.environ.get("COLAB_VIZ_EXECUTION", "thread"),
        # **선언이 없으면 한 장이다.** 배포가 아무것도 안 적으면 정본 문면대로 나간다.
        tile_branch_enabled=_tile_branch_from_env(os.environ.get("COLAB_VIZ_TILE_BRANCH")),
        preview_dir=Path(os.environ.get("COLAB_VIZ_PREVIEW_DIR") or DEFAULT_PREVIEW_DIR),
        preview_url_base=os.environ.get("COLAB_VIZ_PREVIEW_URL_BASE")
        or DEFAULT_PREVIEW_URL_BASE,
        # **선언이 없으면 버스가 없는 것이다.** 기본 경로를 하나 지어 넣으면 그 자리가
        # 모든 배포에서 같은 자리가 되고, 비어 있어도 아무도 그 사실을 모른다.
        trigger_spool=(Path(os.environ["COLAB_VIZ_TRIGGER_SPOOL"])
                       if os.environ.get("COLAB_VIZ_TRIGGER_SPOOL") else None),
        trigger_poll_seconds=_poll_seconds_from_env(
            os.environ.get("COLAB_VIZ_TRIGGER_POLL_SECONDS")),
        # **선언이 없으면 지우지 않는다.** 자동 삭제는 명시로만 켠다 —
        # 모르는 값(오타 포함)도 꺼짐이다(`_tile_branch_from_env` 와 같은 표).
        tile_reclaim_apply=_tile_branch_from_env(
            os.environ.get("COLAB_VIZ_TILE_RECLAIM_APPLY")),
        tile_reclaim_max_keys=_positive_int_from_env(
            os.environ.get("COLAB_VIZ_TILE_RECLAIM_MAX_KEYS"),
            DEFAULT_TILE_RECLAIM_MAX_KEYS),
        tile_reclaim_interval_seconds=_positive_float_from_env(
            os.environ.get("COLAB_VIZ_TILE_RECLAIM_INTERVAL_SECONDS"),
            DEFAULT_TILE_RECLAIM_INTERVAL_SECONDS),
        source_mode=_mode(os.environ.get(ENV_SOURCE_MODE), env_name=ENV_SOURCE_MODE, allowed=SOURCE_MODES),
        s3_bucket=os.environ.get(ENV_S3_BUCKET) or None,
        s3_region=os.environ.get(ENV_S3_REGION) or None,
        workdir=Path(workdir) if workdir else None,
        work_max_bytes=parse_work_max_bytes(os.environ.get(ENV_WORK_MAX_BYTES)),
        preview_sink=_mode(os.environ.get(ENV_PREVIEW_SINK), env_name=ENV_PREVIEW_SINK, allowed=PREVIEW_SINKS),
        preview_s3_prefix=(os.environ.get(ENV_PREVIEW_S3_PREFIX) or DEFAULT_PREVIEW_S3_PREFIX).strip("/"),
    )
    return validate(settings)
