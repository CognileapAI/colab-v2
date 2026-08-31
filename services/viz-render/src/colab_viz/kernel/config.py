"""설정 — 값의 근거를 값 옆에 적는다.

`max_render_bytes` 만 정본에서 오고(그것도 `[가정]` 표시가 붙어 있다) 나머지는 레포 결정이다.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

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


def load_settings() -> Settings:
    """환경에서 읽는다.

    **자격 증명이 없어도 프로세스는 뜬다** — 헬스(`/healthz`)는 배포 배관이라 살아 있어야
    하고, staging 은 지금 이 단위를 헬스로만 보고 있다. 대신 **렌더 표면은 열리지 않고
    503 을 낸다**(계약이 5xx 자리를 이미 뒀다). 인증을 조용히 끄는 것과 정반대다.
    ⚠ 환경변수 주입은 `infra/staging/compose.*.yml` 이 할 일이고 이 레인의 소유가 아니다.
    """
    root = os.environ.get("COLAB_VIZ_SOURCE_ROOT")
    return Settings(
        source_root=Path(root) if root else DEFAULT_SOURCE_ROOT,
        service_token=os.environ.get("COLAB_VIZ_SERVICE_TOKEN") or None,
        # **비밀을 코드에 박지 않는다.** 없으면 None 이고 렌더 표면은 503 이다 —
        # 기본값을 하나 지어 넣으면 그것이 모든 배포에서 같은 비밀이 된다.
        tile_signing_secret=os.environ.get("COLAB_VIZ_TILE_SIGNING_SECRET") or None,
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
    )
