"""렌더 작업 — 상태 3값 · 단계 3값 · 부분 실패.

**왜 작업(job)인가** — 서버 왕복이 수 초~수십 초라 동기 응답으로 두면 진행을 말할 수
없다. 정본이 요구하는 것은 「로딩 중」이 아니라 **어느 단계인지**다.

정본이 값을 준 자리는 그대로 쓴다:
  단계 = `파일 읽는 중` → `지도 그리는 중` → `범례 만드는 중` (문구 그대로)
  상태 = `그리는 중` · `완료` · `실패`. **취소를 두지 않는다** — 정본에 취소 화면이 없다.
  부분 실패는 **`완료`로 남는다** — 읽힌 조각으로 그린다. 전부 실패와 다른 자리다.
"""
from __future__ import annotations

import hashlib
import threading
import time
from collections import deque
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from ...kernel import signing
from ...kernel.ids import new_ulid
from ...ports.source import ResolvedTarget, SourcePart
from . import colormap, downsample, invalidation, palettes, preview, raster, scale
from .failures import FAILURE_MESSAGES, NotRenderableError, RenderError, RenderFailure
from .grid import GridUnavailableError, find_reference_grid
from .readers import Field, FieldReadError, read_field

STAGE_READ = "파일 읽는 중"
STAGE_DRAW = "지도 그리는 중"
STAGE_LEGEND = "범례 만드는 중"
STAGES = (STAGE_READ, STAGE_DRAW, STAGE_LEGEND)

STATUS_DRAWING = "그리는 중"
STATUS_DONE = "완료"
STATUS_FAILED = "실패"

#: 파일 안에서 격자를 **계산해 낼 수 있는** 포맷 (`DATA-PIPELINE-MEASUREMENT §1.1` 실측).
#: 오차 — GeoTIFF 2.8e-14° · HDF4 7e-14° · NetCDF 1.3e-5°(=1.45 m). 셋 다 격자 파일이
#: 필요 없다.
#:
#: ⚠ **`HDF4` 가 여기 들어온 것이 `C-3` 의 실물이다.** 옛 주석은 「MODIS 는 Sinusoidal
#: 격자라 좌표를 밖에서 받아야 한다」고 적었는데 **실측이 그것을 뒤집었다** — 꼬리의
#: `StructMetadata.0` 코너좌표 + Sinusoidal(R=6371007.181)로 7e-14° 에 재현된다.
#: **Binary(HSR) 만 남는다** — 헤더의 투영 파라미터 자리(36~63 B)가 실물에서 전부 0 이라
#: 재현이 불가능하고, 명세 기재값으로 재구성해도 0.053°(≈5.9 km) 틀린다(`§5.1`).
MAY_CARRY_COORDINATES = frozenset({"GeoTIFF", "NetCDF", "HDF4"})


@dataclass
class RenderSpec:
    target: ResolvedTarget
    palette: str
    class_count: int
    variable: str | None
    instant: str | None
    without_reference_grid: bool
    max_preview_side: int
    deadline_seconds: float
    preview_dir: Path
    preview_url_base: str


@dataclass
class RenderJob:
    render_id: str
    spec: RenderSpec
    #: **이 작업이 누구 것인가** (`CODE-REVIEW-20260903` #1). core-api 가 중계에 실어
    #: 보내는 `X-CoLAB-Lab` 을 접수 때 새기고, 조회·스크린샷이 이 값과 대조한다.
    #: ⚠ 빈 문자열은 **경계를 모르는 작업**이라 어떤 요청과도 맞지 않는다 — 접수 표면이
    #: 빈 값을 400 으로 막으므로 실제로 생기지 않지만, 기본값이 「전부와 맞는 값」이면
    #: 나중에 한 자리만 빠져도 조용히 열린다.
    lab: str = ""
    #: 누가 불렀는가. **판정에는 쓰지 않는다** — 출처 표시다.
    account: str = ""
    status: str = STATUS_DRAWING
    stage: str | None = STAGE_READ
    stage_history: list[str] = field(default_factory=list)
    expires_at: datetime | None = None
    rendered: raster.Rendered | None = None
    partial: dict | None = None
    failure: dict | None = None
    #: `core-viz.yaml#GridRejection` — 붙인 격자를 왜 못 썼는가. 거절이 아니면 `None`.
    grid_rejection: dict | None = None
    tile_url_template: str = ""
    #: **갈래 스위치**(`〈240〉`). `JobStore` 가 설정에서 받아 작업마다 새긴다.
    #: **기본값은 꺼짐** — 선언이 없으면 정본 문면대로 `imageUrl` 한 장이다.
    tile_branch_enabled: bool = False
    artifacts: "PreviewArtifacts | None" = None
    color_range: scale.ColorRange | None = None
    badge: str = preview.BADGE_NO_GRID
    value_variable: str = ""
    value_unit: str | None = None
    #: 이 작업이 지난 **무효화 범위**(`Y-1` 완료 정의 ⓒ). 자동 경로와 수동 경로가
    #: **같은 계산기**를 지났음을 여기 남긴다 — 두 경로가 각자 규칙을 갖지 않는다.
    #: `trigger` 가 `None` 이면 사람이 부른 경로다.
    invalidation: "invalidation.InvalidationPlan | None" = None
    #: 그 범위 중 **실제로 지워진 것**(`CODE-REVIEW-20260903` #2). 계산과 집행은 다른
    #: 사실이라 따로 남긴다 — 종전에는 집행 결과가 어디에도 안 적혀서, 한 번도 집행되지
    #: 않고 있다는 사실을 아무도 볼 수 없었다.
    invalidation_removed: tuple[Path, ...] = ()
    #: 완료(성공·실패 무관)를 알리는 자리. **바쁜 대기를 쓰지 않으려고 둔다.**
    #: `to_dict` 가 보지 않으므로 계약 표면에 나가지 않는다.
    done: threading.Event = field(default_factory=threading.Event, repr=False,
                                  compare=False)

    @property
    def tile_branch(self) -> bool:
        """이 결과를 **타일 갈래**로 낼 것인가 (`〈238〉` · 경계 ㈏㈐ · ㈎ 는 부르는 자리에서).

        ⭑ **⟨개정 2026-08-31 · Ted 판정 ⑬ · `PLAN-SoT §9 〈240〉`⟩ 선언된 스위치가 켜졌을
          때만 타일이다.** ／ 종전 문면 ~~등록 데이터셋의 지도형이면 타일 갈래다~~ —
          그 세 조건이 **암묵적으로 타일을 강제**했다. 정본(260826 델타 · POL-021)은
          축자로 「**타일 서버도 바탕 지도도 쓰지 않는다**」이고, 타일 전환(`〈238〉`)의
          근거였던 대장의 「타일 서빙」 문구는 **정본에 없는 문구**였다. 판정 ⑬ 은
          되돌리는 대신 **두 갈래를 다 두고 A/B 로 비교**하기로 했고, **기본은 한 장**이다.

        ⚠ **`is_upload` 로 가른다** — 「등록된 데이터셋인가」는 대상 해석이 이미 아는
        사실이고(`ports/source.ResolvedTarget`) 여기서 다시 판정하지 않는다.
        ⚠ **스위치는 경계를 넓히지 못한다.** 켜도 비지도형(㈎ · 부르는 자리)·미등록
        업로드(㈏)·서명 비밀 없음(㈐)은 **언제나 한 장**이다 — 스위치는 「타일을 내라」는
        선언이지 「없는 경계를 지어내라」는 선언이 아니다.
        """
        return (self.tile_branch_enabled
                and (not self.spec.target.is_upload)
                and bool(self.tile_url_template))

    def to_dict(self) -> dict:
        """`RenderJob` 스키마 그대로. **없는 것은 키째 뺀다** — null 을 넣지 않는다."""
        body: dict = {"renderId": self.render_id, "status": self.status}
        if self.status == STATUS_DRAWING and self.stage:
            body["stage"] = self.stage
        if self.expires_at is not None:
            body["expiresAt"] = self.expires_at.isoformat().replace("+00:00", "Z")
        if self.status == STATUS_DONE and self.artifacts is not None:
            # **`oneOf` 다** — 두 갈래를 함께 싣지 않는다. 둘을 함께 실으면 「무엇을
            # 그릴지 두 번 적힌 완료」다.
            #
            # ⭑ **⟨개정 2026-08-31 · Ted 판정 ⑩ · `PLAN-SoT §9 〈238〉`⟩ 등록된 데이터셋의
            #   지도형 결과는 타일 갈래로 낸다.** ／ 종전 문면 ~~stage 1 은 이미지 갈래만
            #   낸다 … 결과에 함께 싣지 않는다~~ — 그 한 줄이 `03-HANDOFF §4` `#48` 의
            #   실물이었다: 타일은 서빙도 서명도 서 있는데 **이음매에만 있고 화면에는 못
            #   갔다.** 판정이 그 문장을 갈았다.
            # ⚠ **전환의 경계는 셋이다 — 넓히지 않는다**(`CLAUDE.md §5`).
            #   ㈎ **지도형만** — 타일은 웹 메르카토르 `z/x/y` 라 경계 없이 낼 자리가 없다.
            #      ②비지도형은 그대로 `imageUrl` 하나다. **없는 경계를 지어내지 않는다**
            #      (`DR-9` · `CLAUDE.md §3`).
            #   ㈏ **등록된 데이터셋만** — `#48` 이 `P3` 소유로 남긴 것은 「데이터셋 상세의
            #      지도 화면」이다. 미등록 업로드(S-04·S-08)는 손대지 않는다.
            #   ㈐ **서명 비밀이 있을 때만** — 없으면 `_tile_url` 이 서명 없는 주소를 내므로
            #      (그 자리는 표면이 503 이라 도달하지 않는다) 이미지 갈래로 남는다.
            #
            # ⚠ **좌표가 있느냐로 갈린다** (`〈85〉` · 동결 2회 해제).
            #   ③이 있으면 지도형 — `bounds`·사이드카·월드파일이 함께 간다.
            #   ③이 없으면 ②비지도형 — `imageUrl` 하나다. **경계를 지어내지 않는다**
            #   (`DR-9`). 옛 코드는 이 자리를 `실패(REFERENCE_GRID_MISSING)` 로 두고
            #   산출물 URL 을 `failure.details` 로 밀어 넣었다 — 계약이 ②를 낼 자리를
            #   주지 않아서였고, 그 구멍이 닫혔다.
            a = self.artifacts
            result: dict = {"legend": self.legend_body(), "precisionBadge": self.badge,
                            "colorRangeStage": self.color_range.stage
                            if self.color_range else None}
            #
            # ⚠ **①②는 항상 함께 구워진다**(`build_value_layers`). 개정 전에는 실을 자리가
            # `imageUrl` 하나뿐이라 ③이 있으면 ②가, ③이 없으면 ①이 **버려졌다** —
            # 그 URL 들은 **실패 봉투로만** 나갔고, 즉 **렌더가 성공할수록 썸네일이 안
            # 보였다**(스윕 `A-1` · `〈88〉` 묶음 3). 이제 층마다 자기 자리가 있다.
            result["thumbnailUrl"] = a.thumbnail.url
            result["valuePreviewUrl"] = a.detail.url
            if a.map_image is not None and a.geometry is not None:
                result["sidecarUrl"] = a.sidecar.url
                result["worldFileUrl"] = a.world_file.url
                result["bounds"] = a.geometry.bounds_dict()
                if self.tile_branch:
                    result["tileUrlTemplate"] = self.tile_url_template
                else:
                    result["imageUrl"] = a.map_image.url
            else:
                # ②가 곧 주 화면인 갈래다 — 같은 URL 을 가리키는 것이 정상이다.
                result["imageUrl"] = a.detail.url
            if result["colorRangeStage"] is None:
                # 라벨 없는 산출물은 **범위 밖이다**(`§C.2 Q4`) — 키를 지우지 않고 실패로 둔다.
                raise RuntimeError("색 범위 단계 라벨 없이 결과를 낼 수 없다")
            body["result"] = result
        if self.status == STATUS_FAILED and self.failure is not None:
            body["failure"] = self.failure
        if self.partial is not None:
            body["partialFailure"] = self.partial
        if self.grid_rejection is not None:
            # ⚠ **`failure` 안이 아니다.** ②비지도형은 격자 없이도 `완료` 로 나가고,
            # 그때도 「왜 지도형이 안 떴는가」를 화면이 말해야 한다 (`§5.5` 보류).
            body["gridRejection"] = self.grid_rejection
        return body

    def legend_body(self) -> dict:
        """범례. **③이 없어도 범례는 있다** — ②도 같은 색 사다리로 칠해진 그림이다.

        지도형이 없을 때는 `Rendered` 가 없으므로(경계를 요구하는 자료형이다) 공통
        색 범위와 팔레트에서 곧바로 세운다. **구간을 프레임에서 다시 잡지 않는다**(`V-2`) —
        `raster.legend_from_range` 가 쓰는 범위는 `_color_range` 가 잡은 그 범위다.
        """
        if self.rendered is not None:
            return self.rendered.legend()
        if self.color_range is None:
            raise RuntimeError("색 범위 없이 범례를 세울 수 없다")
        return raster.legend_from_range(
            palette_key=self.spec.palette, class_count=self.spec.class_count,
            value_range=(self.color_range.vmin, self.color_range.vmax),
            variable=self.value_variable, unit=self.value_unit)

    @property
    def expired(self) -> bool:
        return self.expires_at is not None and datetime.now(timezone.utc) >= self.expires_at


@dataclass
class PreviewArtifacts:
    """미리보기 3층의 산출물. **③이 없어도 ①②는 있다**(`§5.5` — 실패가 아니라 보류)."""
    thumbnail: preview.Artifact
    detail: preview.Artifact
    #: ⭑ ⟨2026-09-02 · `A-1` 완료 정의 ⑹⟩ ①②의 동반 `.json`. **선택이 아니다** —
    #: 세 층 전부가 사이드카를 가져야 디스크만 보고 소유를 판정할 수 있다.
    thumbnail_sidecar: preview.Artifact
    detail_sidecar: preview.Artifact
    map_image: preview.Artifact | None = None
    sidecar: preview.Artifact | None = None
    world_file: preview.Artifact | None = None
    geometry: preview.MapGeometry | None = None

    def all(self) -> list[preview.Artifact]:
        return [a for a in (self.thumbnail, self.detail,
                            self.thumbnail_sidecar, self.detail_sidecar,
                            self.map_image, self.sidecar, self.world_file)
                if a is not None]


@dataclass
class _Read:
    """읽힌 조각 하나 — **값과 좌표를 함께 들고 다닌다.**

    ⚠ 값과 좌표를 갈라 두는 이유 — ①②는 **원본 배열 방향 그대로**이고 좌표를 쓰지
    않는다(`§2` 좌표계 열). ③만 좌표를 쓴다. 한 덩어리로 뭉치면 ①②가 좌표에 인질이
    되고, 그것이 「격자 없으면 미리보기 없음」이라는 거짓말의 출발점이었다.
    """
    part: SourcePart
    fmt: str
    field: Field
    reference: tuple | None = None
    from_uploaded_grid: bool = False


def _decimate_grid(arr, steps: tuple[int, int]):
    """기준 격자를 값과 같은 형상으로 줄인다 — **블록 중심의 실측 좌표를 집는다.**

    평균하면 양 끝이 안쪽으로 밀려 격자의 최솟값·최댓값이 바뀐다. 그 이동은 실물
    `.npy` 판과 `.nc` 판을 가르는 612 m 와 같은 크기다 — **우리가 만든 오차를 원본
    차이와 섞을 이유가 없다**(`downsample.sample_centers`).
    """
    return downsample.sample_centers(np.asarray(arr, dtype="f8"), steps).astype("f8")


def _read_part(part: SourcePart, spec: RenderSpec) -> _Read:
    """조각 하나를 읽는다. 좌표는 있으면 싣고, **없으면 없다고 말한다** — 지어내지 않는다."""
    fmt, field_ = read_field(part.path, variable=spec.variable, instant=spec.instant,
                             max_side=spec.max_preview_side)

    if field_.has_position:
        return _Read(part=part, fmt=fmt, field=field_)

    if spec.target.grid_dir is None:
        if spec.without_reference_grid and fmt == "Binary":
            # 계약이 이 조합만 명시로 막았다 — HSR 은 헤더로 격자를 세울 수 없고
            # **합성 격자를 만들지 않는다**(`core-viz.yaml` · `§10-9` · `DR-9`).
            raise RenderError(RenderFailure.NO_REFERENCE_GRID,
                              f"{part.file_name}: HSR 은 격자 파일 없이 지도를 그릴 수 없다")
        # ⚠ **실패가 아니라 보류다**(`§5.5`). ①②는 이 뒤에도 만들어진다 — 좌표가 없어
        # 못 만드는 것은 ③뿐이다. 옛 코드가 여기서 전체를 실패시켰다.
        return _Read(part=part, fmt=fmt, field=field_)

    # ⚠ 격자는 **솎기 전 원래 형상**으로 대조한다. 솎은 형상으로 찾으면 실물 격자가
    # 「안 맞는다」로 튕겨 나가고, 그 자리에 「짝 파일이 없다」는 **틀린 이유**가 붙는다.
    native = field_.native_shape or field_.values.shape
    try:
        grid = find_reference_grid(spec.target.grid_dir, expect_shape=native)
    except GridUnavailableError as e:
        # **거절 사유를 숫자·enum 으로 들려 보낸다** (`〈88〉` 묶음 1·2). 문장은 사람용으로만
        # 남는다 — 화면이 문장을 가르던 자리가 여기서 닫힌다(스윕 `C-1`).
        err = RenderError(RenderFailure.NO_REFERENCE_GRID, str(e))
        err.grid_rejection = e.rejection(file_name=part.file_name)
        raise err from e
    steps = field_.steps
    reference = (_decimate_grid(grid.lat, steps), _decimate_grid(grid.lon, steps))
    return _Read(part=part, fmt=fmt, field=field_, reference=reference,
                 from_uploaded_grid=True)


def _source_digest(reads: list[_Read]) -> str:
    """원본을 가리키는 값 (`§7.2` 「원본 해시」).

    ⚠ **내용 해시가 아니다.** 500 MB 를 렌더마다 다시 읽는 비용을 아직 안 쟀다 —
    `[미측정]`. 지금은 `(파일명, 크기, 수정시각)` 이고, **원본이 바뀌면 키가 바뀐다**는
    성질은 그대로 선다. 내용 해시로 바꾸는 것은 이 함수 하나를 고치는 일이다.
    """
    h = hashlib.sha256()
    for r in sorted(reads, key=lambda r: r.part.file_name):
        st = r.part.path.stat()
        h.update(f"{r.part.file_name}|{st.st_size}|{st.st_mtime_ns}|".encode())
    return h.hexdigest()


#: 이 개수 이하의 격자는 **전량**을 해시한다. f8 기준 512 KB — 해시 비용이 렌더 한 회의
#: 잡음 안에 든다. 실물 기준 격자(2881²≈8.3M)는 이 위라 표본 구간으로 간다.
_DIGEST_FULL_MAX_ELEMENTS = 1 << 16
#: 표본 구간에서 집는 점의 개수. 균등 보폭이라 **자리가 결정적**이다 — 무작위 표본을
#: 쓰면 같은 격자가 매번 다른 키를 내고, 그것은 캐시가 아니라 난수다.
_DIGEST_SAMPLE_COUNT = 4096
#: NaN 자리에 넣는 표식. **NaN 의 비트 표현에 기대지 않는다** — 페이로드가 갈리면
#: 같은 격자가 다른 키를 낼 수 있다. 실측 좌표가 절대 갖지 않는 크기를 쓴다.
_DIGEST_NAN_SENTINEL = -9.87654321e30


def _array_fingerprint(h: "hashlib._Hash", arr) -> None:
    """배열 하나를 digest 에 접어 넣는다 — **형상 + 양 끝 + 값 표본**.

    ⭑ ⟨2026-09-03 · 코드리뷰 #3 형제⟩ 종전에는 lat 의 shape · `nanmin(lat)` ·
    `nanmax(lon)` **세 값**뿐이었다. 그 셋이 같은 다른 격자로 갈아 끼우면 키가 같아지고
    `invalidation` 의 `keep_keys` 가 구 산출물을 「신선」으로 보존한다 — **격자를 바꿨는데
    옛 그림이 남는다.** 값 자신을 보지 않는 digest 는 격자 교체를 못 본다.
    """
    a = np.asarray(arr, dtype="f8")
    h.update(f"|shape={a.shape}|".encode())
    flat = np.ascontiguousarray(a.reshape(-1))
    # 양 끝은 **전량에서** 정확히 잰다 — 표본이 놓치더라도 범위 변화는 반드시 잡힌다.
    finite = flat[np.isfinite(flat)]
    lo = float(finite.min()) if finite.size else float("nan")
    hi = float(finite.max()) if finite.size else float("nan")
    h.update(f"min={lo!r}|max={hi!r}|n={flat.size}|".encode())
    if flat.size > _DIGEST_FULL_MAX_ELEMENTS:
        step = -(-flat.size // _DIGEST_SAMPLE_COUNT)      # ceil — 보폭이 결정적이다
        flat = flat[::step]
    sample = np.where(np.isfinite(flat), flat, _DIGEST_NAN_SENTINEL)
    h.update(np.ascontiguousarray(sample, dtype="<f8").tobytes())


def _grid_digest(reads: list[_Read]) -> str | None:
    """지도형 키에만 들어가는 격자 값 — **격자를 갈면 지도형만 무효화된다**(`§7.2`).

    **위도와 경도를 둘 다 본다.** 종전에는 위도의 최솟값과 경도의 최댓값만 봐서,
    한쪽만 갈린 격자가 그대로 통과했다.
    """
    used = [r for r in reads if r.from_uploaded_grid and r.reference is not None]
    if not used:
        return None
    h = hashlib.sha256()
    for r in used:
        _array_fingerprint(h, r.reference[0])
        _array_fingerprint(h, r.reference[1])
        h.update(b"||")
    return h.hexdigest()


def _mesh_from_bounds(values, bounds):
    """규칙 격자의 좌표 배열. **파일이 말한 경계에서 나온 값**이고 합성이 아니다."""
    w, s, e, n = bounds
    ny, nx = values.shape
    lat = np.repeat(np.linspace(n, s, ny)[:, None], nx, axis=1)
    lon = np.repeat(np.linspace(w, e, nx)[None, :], ny, axis=0)
    return values, lat, lon


def _map_coordinates(reads: list[_Read], merged):
    """③에 쓸 (값, 위도, 경도). **좌표를 지어내지 않는다** — 없으면 `None` 이다.

    조각이 하나면 **그 조각의 실측 좌표에서 바로** 3857 로 간다(`V-3`) — 4326 규칙
    격자를 거치면 재배치가 한 번 더 낀다. 여러 조각이면 합친 층의 경계에서 격자를
    세운다(합치는 순간 조각별 곡선 좌표는 이미 한 격자로 접혔다).
    """
    if len(reads) == 1:
        r = reads[0]
        if r.field.lat is not None and r.field.lon is not None:
            return r.field.values, r.field.lat, r.field.lon
        if r.reference is not None:
            return r.field.values, r.reference[0], r.reference[1]
        if r.field.bounds is not None:
            return _mesh_from_bounds(r.field.values, r.field.bounds)
        return None
    if merged is not None:
        return _mesh_from_bounds(merged.values, merged.bounds)
    return None


def _badge_for(reads: list[_Read], has_map: bool) -> str:
    if not has_map:
        return preview.BADGE_NO_GRID
    if any(r.from_uploaded_grid for r in reads):
        return preview.BADGE_ATTACHED_GRID
    return preview.BADGE_COMPUTED_GRID


def _color_range(spec: RenderSpec, arrays: list) -> scale.ColorRange:
    """**잠정/확정 2단계**(`§D.4-⑶`). 등록 전 업로드는 잠정, 데이터셋은 확정이다."""
    target_id = spec.target.target_id
    try:
        if spec.target.is_upload:
            return scale.for_upload(target_id, arrays)
        return scale.for_dataset(target_id, arrays)
    except scale.RangeUnavailableError:
        # 유효값이 하나도 없다 — `§9` 는 이것을 **실패가 아니라 전부 투명한 PNG** 로 둔다.
        # 어떤 범위를 넣어도 그림이 같다(전 픽셀 알파 0). 값이 그림에 들어가지 않으므로
        # **값을 지어내는 것이 아니다.**
        if spec.target.is_upload:
            return scale.ColorRange(vmin=0.0, vmax=1.0, stage=scale.STAGE_PROVISIONAL,
                                    scope=scale.SCOPE_UPLOAD, scope_id=target_id)
        return scale.ColorRange(vmin=0.0, vmax=1.0, stage=scale.STAGE_FINAL,
                                scope=scale.SCOPE_DATASET, scope_id=target_id)


class _ValuesOnly:
    """좌표 없는 층의 자리끼움 — `_build_artifacts` 가 보는 것은 `values`·`variable` 뿐이다."""

    def __init__(self, field: Field) -> None:
        self.values = field.values
        self.variable = field.variable
        self.bounds = None


def _build_artifacts(job: RenderJob, reads: list[_Read], merged,
                     color_range: scale.ColorRange) -> PreviewArtifacts:
    """①②를 먼저 만들고, 좌표가 있으면 ③을 **덧붙인다.** 순서가 곧 `§5.5` 다."""
    spec = job.spec
    lut = colormap.lut256(palettes.get(spec.palette).anchors)
    key_params = dict(source_digest=_source_digest(reads),
                      fills=tuple(sorted({f for r in reads for f in r.field.fills})),
                      palette=spec.palette, selection=merged.variable,
                      # **시각도 산출물을 가른다**(코드리뷰 #3) — 없으면 T1·T2 가 한 파일이다.
                      instant=spec.instant)
    out_dir = Path(spec.preview_dir)

    values = reads[0].field.values if len(reads) == 1 else merged.values
    # ⭑ ⟨2026-09-02 · `A-1` 안 ⑷ 최소 묶음 1·3⟩ 사이드카가 실을 두 가지.
    #   `source`/`sources` = **`fileId`** 다(파일명이 아니다 — `SourcePart.file_id`).
    #   `owner` = **구운 시점의 대상**이다. 둘 다 **이미 D7 안에 있다 — Port 를 열지 않는다.**
    source_ids = tuple(r.part.file_id for r in reads)
    owner = preview.BakeOwner(target_id=spec.target.target_id,
                              is_upload=spec.target.is_upload)
    thumb, detail, thumb_sc, detail_sc = preview.build_value_layers(
        values, color_range=color_range, lut=lut, out_dir=out_dir,
        url_base=spec.preview_url_base, key_params=key_params,
        source=source_ids[0], sources=source_ids, owner=owner)
    artifacts = PreviewArtifacts(thumbnail=thumb, detail=detail,
                                 thumbnail_sidecar=thumb_sc, detail_sidecar=detail_sc)

    coords = _map_coordinates(reads, merged if not isinstance(merged, _ValuesOnly) else None)
    if coords is None:
        return artifacts
    map_values, lat, lon = coords
    image, sidecar, world, geom = preview.build_map_layer(
        map_values, lat, lon, color_range=color_range, lut=lut, out_dir=out_dir,
        url_base=spec.preview_url_base, key_params=key_params,
        grid_digest=_grid_digest(reads), source=source_ids[0], sources=source_ids,
        owner=owner)
    artifacts.map_image, artifacts.sidecar = image, sidecar
    artifacts.world_file, artifacts.geometry = world, geom
    return artifacts


def _failure(code: str, detail: str, job: RenderJob, message: str | None = None) -> dict:
    """실패 봉투. **값 미리보기가 이미 있으면 그 자리를 함께 말한다.**

    ⚠ **좌표 없는 렌더는 더 이상 여기 오지 않는다** — `〈85〉` 로 계약이 ②비지도형을
    「완료」로 받게 됐고, `failure.details` 로 산출물 URL 을 밀어 넣던 우회가 사라졌다.
    지금 이 자리에 남은 것은 **진짜 실패**뿐이다 — 붙인 격자를 못 쓰는 경우, HSR 에
    `withoutReferenceGrid` 를 건 경우(`DR-9`), 경계가 상식 밖인 경우, 시간 초과.
    그중에도 ①②가 이미 구워졌으면 그 자리를 함께 말한다 — 있는 것을 감추지 않는다.
    """
    details: dict = {}
    if detail:
        details["detail"] = detail
    if job.artifacts is not None:
        details["thumbnailUrl"] = job.artifacts.thumbnail.url
        details["valuePreviewUrl"] = job.artifacts.detail.url
        details["precisionBadge"] = job.badge
        if job.color_range is not None:
            details["colorRangeStage"] = job.color_range.stage
    out = {"code": code, "message": message or FAILURE_MESSAGES.get(code, code)}
    if details:
        out["details"] = details
    return out


def _run(job: RenderJob) -> None:
    started = time.monotonic()
    spec = job.spec

    def _stage(name: str) -> None:
        job.stage = name
        job.stage_history.append(name)
        if time.monotonic() - started >= spec.deadline_seconds:
            raise RenderError(RenderFailure.TIMEOUT)

    try:
        _stage(STAGE_READ)
        reads: list[_Read] = []
        missing: list[dict] = []
        first_error: RenderError | None = None
        for part in spec.target.parts:
            try:
                reads.append(_read_part(part, spec))
            except RenderError as e:
                first_error = first_error or e
                missing.append({"fileId": part.file_id, "fileName": part.file_name})
            except NotRenderableError as e:
                # ⭑ ⟨2026-09-03 · 레인 C 수용 검토 #2⟩ **「알 수 없는 오류」가 아니다.**
                # `is_retry_pointless` 가 이 형으로 재시도 무의미를 판정하는데, 여기서
                # `RENDER_UNKNOWN_ERROR` 로 접어 버리면 화면은 그 판정을 못 본다 —
                # 없는 시각·안 그리는 포맷에 「다시 그리기」가 뜨고, 눌러도 영원히 같은
                # 실패가 돌아온다. 코드는 라우트가 415 로 내는 것과 **같은 문자열**이다.
                first_error = first_error or RenderError(
                    RenderFailure.NOT_RENDERABLE, str(e))
                missing.append({"fileId": part.file_id, "fileName": part.file_name})
            except (FieldReadError, Exception) as e:  # noqa: BLE001
                first_error = first_error or RenderError(RenderFailure.UNKNOWN, str(e))
                missing.append({"fileId": part.file_id, "fileName": part.file_name})

        if not reads:
            raise first_error or RenderError(RenderFailure.UNKNOWN, "읽힌 조각이 없다")

        _stage(STAGE_DRAW)
        # **공통 범위를 먼저 잡고 그 범위로 구간을 정한다.** 순서가 뒤집히면 프레임이
        # 자기 값으로 구간을 잡고, 그것이 `§10-7` 이 금지한 그것이다.
        color_range = _color_range(spec, [r.field.values for r in reads])
        job.color_range = color_range
        vr = (color_range.vmin, color_range.vmax)

        drawn = [raster.build(r.field, palette_key=spec.palette,
                              class_count=spec.class_count, reference=r.reference,
                              value_range=vr)
                 for r in reads if r.field.has_position or r.reference is not None]
        merged = raster.merge(drawn, vr) if drawn else None

        _stage(STAGE_LEGEND)
        job.value_variable = reads[0].field.variable
        job.value_unit = reads[0].field.unit
        if merged is None:
            # 좌표가 하나도 없다 — ①②만 굽고 **지도형은 보류**다. `Rendered` 는 경계를
            # 요구하므로 만들지 않는다. **경계를 지어내지 않는다**(`DR-9`).
            #
            # ⚠ **여기서 실패시키지 않는다**(`〈85〉` · Ted 2026-08-24 판정 ㈎).
            # 이것은 ②비지도형이고 계약이 이제 그 형태를 「완료」로 받는다 —
            # `bounds` 는 지도형 갈래에만 필수다. 격자를 붙였는데 못 쓰는 경우는
            # 이 자리에 오지 않는다: `_read_part` 가 이미 실패로 끊는다.
            job.artifacts = _build_artifacts(job, reads, _ValuesOnly(reads[0].field),
                                             color_range)
            job.badge = preview.BADGE_NO_GRID
        else:
            job.rendered = merged
            job.artifacts = _build_artifacts(job, reads, merged, color_range)
            job.badge = _badge_for(reads, job.artifacts.map_image is not None)
        if missing:
            # ⚠ 상태를 `실패` 로 만들지 않는다. 읽힌 조각으로 그린다.
            job.partial = {"totalParts": len(spec.target.parts),
                           "renderedParts": len(reads),
                           "missingParts": missing}
        job.stage = None
        job.status = STATUS_DONE
    except preview.BboxSanityError as e:
        # ⑪ — 격자는 있었는데 결과가 상식 밖이다. **지도형만 실패하고 ①②는 남는다.**
        job.stage = None
        job.status = STATUS_FAILED
        job.badge = preview.BADGE_NO_GRID
        job.failure = _failure(RenderFailure.MAP_BOUNDS_IMPLAUSIBLE, str(e), job)
    except RenderError as e:
        job.stage = None
        job.status = STATUS_FAILED
        job.grid_rejection = getattr(e, "grid_rejection", None)
        job.failure = _failure(e.code, e.detail, job,
                               message=FAILURE_MESSAGES.get(e.code, e.message))
    except Exception as e:                       # noqa: BLE001 — 마지막 그물
        job.stage = None
        job.status = STATUS_FAILED
        job.failure = _failure(RenderFailure.UNKNOWN, f"{type(e).__name__}: {e}", job)


#: 렌더 예산을 다 쓴 작업이 마무리(범위 계산·집행)까지 마칠 여유. **예산이 아니다** —
#: 마감을 넘긴 렌더는 이미 `TIMEOUT` 으로 끊기고, 이 값은 그 뒤 정리에 주는 시간이다.
_COMPLETION_GRACE_SECONDS = 10.0

#: 남겨 두는 묘비의 개수 (`CODE-REVIEW-20260903` #11). **묘비도 무한하면 같은 결함이다.**
#: 묘비 하나는 식별자·경계·만료시각뿐이라 수 KB 도 안 되지만, 「가벼우니 무한히」가
#: 정확히 이 항목이 고치는 사고방식이다. 이 수를 넘으면 가장 오래된 것부터 놓고,
#: 그때는 404 다 — 그 id 에 대해 아는 것이 없다는 뜻이라 정직하다.
#: **`[정본 무근거]`** — 정본은 만료 뒤 화면을 말할 뿐 서버가 얼마나 기억하는지 말하지 않는다.
_MAX_TOMBSTONES = 4096


class JobStore:
    """렌더 작업 보관 — 프로세스 안 메모리다.

    ⚠ **의도적으로 여기까지다.** 미리보기 결과는 정본이 「임시로만 둔다」고 못박은 것이라
    영속 저장소를 요구하지 않는다. 다만 **인스턴스가 여럿이면 타일 요청이 다른 인스턴스로
    갈 수 있다** — 배포 형상(고정 라우팅이냐 공유 캐시냐)은 `WU-I1` 판단이고 이 레인의
    소유가 아니다. 감추지 않고 적어 둔다.
    """

    def __init__(self, *, execution: str, tile_url_base: str, ttl_seconds: int,
                 tile_signing_secret: str | None = None,
                 signature_ttl_seconds: int | None = None,
                 tile_branch_enabled: bool = False) -> None:
        self._jobs: dict[str, RenderJob] = {}
        #: 수명이 붙은 작업의 (만료시각, id). **넣는 순서가 곧 만료 순서**다(TTL 이
        #: 상수라서). 그래서 앞에서만 보면 되고, 축출이 전체 스캔이 되지 않는다.
        self._expiring: "deque[tuple[datetime, str]]" = deque()
        #: 축출된 id 의 묘비 — 만료된 id 도 계약이 요구하는 410 을 계속 답해야 한다.
        self._tombstones: "deque[str]" = deque()
        self._max_tombstones = _MAX_TOMBSTONES
        #: **대상 → 그 대상 때문에 구운 산출물**(`CODE-REVIEW-20260903` #11).
        #: 작업 표를 훑는 대신 여기서 찾는다. ⚠ **작업에 매달지 않는다** — 작업이
        #: 축출돼도 디스크의 산출물은 그대로라, 함께 잊으면 그 파일들은 영원히
        #: 무효화되지 않는다.
        self._produced: dict[str, dict[str, invalidation.StaleCandidate]] = {}
        self._pending: list[RenderJob] = []
        self._pending_events: dict[str, object] = {}
        self._lock = threading.Lock()
        self._execution = execution
        self._tile_url_base = tile_url_base.rstrip("/")
        self._ttl = ttl_seconds
        self._secret = tile_signing_secret
        self._sig_ttl = ttl_seconds if signature_ttl_seconds is None else signature_ttl_seconds
        # **기본값은 꺼짐이다** (`〈240〉`) — 부르는 자리가 아무 말도 안 하면 한 장이다.
        self._tile_branch_enabled = tile_branch_enabled

    def submit(self, render_id: str, spec: RenderSpec, *, temporary: bool,
               event: "invalidation.InvalidationEvent | None" = None,
               lab: str = "", account: str = "") -> RenderJob:
        """`event` 가 없으면 **사람이 부른 경로**다 — 둘 다 같은 계산기를 지난다(ⓒ)."""
        job = RenderJob(render_id=render_id, spec=spec, lab=lab, account=account,
                        tile_branch_enabled=self._tile_branch_enabled)
        now = datetime.now(timezone.utc)
        if temporary:
            # 등록 전 업로드의 미리보기 결과는 서버에 임시로만 둔다 (정본 §8 ③ · `NB-2`)
            job.expires_at = now + timedelta(seconds=self._ttl)
        job.tile_url_template = self._tile_url(render_id, job.expires_at, now)
        with self._lock:
            # **새 것을 넣기 전에 지난 것을 놓는다** — 넣는 자리가 곧 치우는 자리다.
            self._evict_expired(now)
            self._jobs[render_id] = job
            if job.expires_at is not None:
                self._expiring.append((job.expires_at, render_id))

        # **완료 경로는 하나다**(`CODE-REVIEW-20260903` #2). 실행기마다 「끝난 뒤에 할 일」을
        # 따로 적으면 그중 하나가 빠지고, 빠진 쪽이 하필 운영 기본값이었다.
        if self._execution == "inline":
            self._run_and_plan(job, event)
        elif self._execution == "manual":
            self._pending.append(job)
            self._pending_events[job.render_id] = event
        else:
            threading.Thread(target=self._run_and_plan, args=(job, event), daemon=True).start()
        return job

    def _run_and_plan(self, job: RenderJob,
                      event: "invalidation.InvalidationEvent | None") -> None:
        """**렌더가 끝난 자리** — 범위 계산도 집행도 여기서 한다.

        ⭑ ⟨2026-09-03 · 코드리뷰 #2⟩ 집행(`invalidation.apply`)이 `regenerate` 안에,
        그것도 `submit()` **직후**에 있었다. 기본 실행기(`thread`)에서 그 시점의
        `job.invalidation` 은 언제나 `None` 이라 **집행이 한 번도 일어나지 않았고**
        트리거는 ack 됐다 — 레이스가 아니라 상시였다. 집행을 완료 경로로 옮기면
        thread·inline·manual 셋이 **같은 자리**를 지난다.

        ⚠ **집행은 사건이 있을 때만이다**(`plan.regenerate`). 사람이 부른 평범한 렌더도
        범위 계산은 지나지만(완료 정의 ⓒ), 거기서 지우면 스타일만 바꿔 다시 그리는
        요청이 앞의 그림을 지운다.
        ⚠ **실패한 렌더는 지우지 않는다** — 「새 것이 선 뒤에 낡은 것을 치운다」의
        나머지 절반이다. 새 것이 못 섰는데 치우면 볼 그림이 하나도 안 남는다.
        """
        try:
            _run(job)
            # **색인이 먼저다** — 방금 구운 것도 후보에 들어야 `keep_keys` 가 그것을
            # 살리고 나머지가 낡은 것으로 갈린다.
            with self._lock:
                self._remember_produced(job)
            plan = self._plan_for(job, event)
            job.invalidation = plan
            if plan.regenerate and job.status == STATUS_DONE:
                job.invalidation_removed = invalidation.apply(
                    plan, previews_root=Path(job.spec.preview_dir))
        finally:
            job.done.set()

    def _tile_url(self, render_id: str, expires_at: datetime | None,
                  now: datetime) -> str:
        """`tileUrlTemplate` — **불투명 문자열**이다(계약). 서명은 이 안에 실린다.

        **수명은 둘 중 이른 쪽이다** (`〈68〉-ⓓ` 「서명 수명은 렌더 결과 수명 안에 든다」) —
        결과가 먼저 죽는데 서명만 살아 있으면 그 서명은 아무 데도 못 쓰면서 유효하다.
        """
        base = f"{self._tile_url_base}/renders/{render_id}/tiles/{{z}}/{{x}}/{{y}}.png"
        if not self._secret:
            # 비밀이 없으면 서명을 못 단다. 이 상태는 렌더 표면이 503 이라 도달하지 않지만
            # (`app/deps.py`), **조용히 서명 없는 주소를 발급하지 않는다**는 것을 코드로 남긴다.
            return base
        deadline = int((now + timedelta(seconds=self._sig_ttl)).timestamp())
        if expires_at is not None:
            deadline = min(deadline, int(expires_at.timestamp()))
        return f"{base}?{signing.query(self._secret, render_id, deadline)}"

    def run_pending(self) -> None:
        """`manual` 실행기 전용 — 시험이 「그리는 중」 상태를 붙잡아 보기 위한 자리다."""
        while self._pending:
            job = self._pending.pop(0)
            self._run_and_plan(job, self._pending_events.pop(job.render_id, None))

    def get(self, render_id: str) -> RenderJob | None:
        with self._lock:
            self._evict_expired(datetime.now(timezone.utc))
            return self._jobs.get(render_id)

    # ── 보관 (`CODE-REVIEW-20260903` #11) ────────────────────────────────────
    def _evict_expired(self, now: datetime) -> None:
        """**수명이 다한 작업만** 놓는다. 호출자가 이미 잠금을 들고 있다.

        ⚠ **완료 시점이 아니다.** 타일(`getRenderTile`)과 스크린샷(`createScreenshot`)이
        `job.rendered` 를 메모리에서 읽으므로, 완료 직후에 놓으면 성공한 렌더가 곧바로
        못 쓰는 렌더가 된다. 놓는 조건은 `expires_at` 하나다 — 개수도, 순서도 아니다.

        ⚠ **묘비를 남긴다.** 만료된 id 는 계약이 요구하는 410 을 계속 답해야 한다
        (`core-viz.yaml` `getRenderTile` `"410"`). 묘비는 식별자·경계·만료시각만 들고
        래스터와 산출물 목록을 놓은 같은 객체다 — 부르는 자리(`job.expired` ·
        `job.lab` · `to_dict`)가 그대로 선다.
        """
        while self._expiring and self._expiring[0][0] <= now:
            _, render_id = self._expiring.popleft()
            job = self._jobs.get(render_id)
            if job is None:
                continue
            # **여기서만 놓는다** — f4 2D 래스터와 산출물 목록.
            job.rendered = None
            job.artifacts = None
            job.partial = None
            job.invalidation = None
            if len(self._tombstones) >= self._max_tombstones:
                self._jobs.pop(self._tombstones.popleft(), None)
            self._tombstones.append(render_id)

    def _remember_produced(self, job: RenderJob) -> None:
        """구운 산출물을 **대상별 색인**에 넣는다 — `_produced_for` 의 입력이다."""
        if job.artifacts is None:
            return
        bucket = self._produced.setdefault(job.spec.target.target_id, {})
        for a in job.artifacts.all():
            bucket[str(a.path)] = invalidation.StaleCandidate(cache_key=a.cache_key,
                                                              path=a.path)

    # ── 자동 무효화 (`Y-1`) ──────────────────────────────────────────────────
    def _produced_for(self, target_id: str) -> list[invalidation.StaleCandidate]:
        """그 대상 때문에 **이 인스턴스가 실제로 구운** 산출물들.

        ⚠ **디렉터리를 훑지 않는다.** 미리보기 자리는 평평하고 대상이 경로에 없으므로
        (`layout.json` ③) 훑으면 **남의 대상 산출물까지 집는다.** D7 에는 원장이 없고,
        이 인스턴스가 아는 사실은 「내가 무엇을 구웠는가」뿐이다 — 아는 것만 센다.

        ⭑ ⟨2026-09-03 · 코드리뷰 #11⟩ **작업 표도 훑지 않는다.** 종전에는 submit 마다
        전 작업을 순회해 1000번째 submit 이 그리기 전에 1000회를 돌았고, 작업이 축출되면
        그 산출물이 후보에서 사라져 **영원히 무효화되지 않는** 파일이 생겼다.
        """
        return list(self._produced.get(target_id, {}).values())

    def _plan_for(self, job: RenderJob,
                  event: invalidation.InvalidationEvent | None) -> invalidation.InvalidationPlan:
        """**자동·수동이 함께 지나는 한 자리**(완료 정의 ⓒ).

        방금 이 작업이 낸 키는 `keep_keys` 로 살린다. 나머지 낡은 것이 범위다.
        """
        fresh = {a.cache_key for a in (job.artifacts.all() if job.artifacts else [])}
        return invalidation.plan(event, produced=self._produced_for(job.spec.target.target_id),
                                 previews_root=Path(job.spec.preview_dir),
                                 keep_keys=fresh, target_id=job.spec.target.target_id)

    def regenerate(self, event: invalidation.InvalidationEvent, *,
                   source) -> "Regeneration":
        """**stage 1 의 「자동 재생성 안 함」이 뒤집히는 그 한 자리**(완료 정의 ⓓ · `〈247〉`).

        순서 = **사건 감지 → 재생성 → 무효화 범위 계산 → 집행**. 굽기 전에 지우면
        실패했을 때 볼 그림이 하나도 안 남는다 — **새 것이 선 뒤에 낡은 것을 치운다.**

        ⚠ **대상을 다시 해석한다**(`SourcePort`) — 「파일 추가」·「격자 변경」은 대상
        디렉터리가 바뀐 사건이라 옛 해석을 그대로 쓰면 사건을 못 본다. ⚠ **원본은 읽기만
        한다** — 이 경로에 원본·기준 격자를 쓰거나 지우는 자리가 없다(음성 시험이 잠근다).
        """
        previous = self._latest_for(event.target_id)
        if previous is None:
            raise LookupError(
                f"이 인스턴스가 그린 적 없는 대상이다: {event.target_id} — "
                "무효화 범위를 지어내지 않는다")
        target = source.resolve(dataset_id=None if previous.spec.target.is_upload else event.target_id,
                                upload_id=event.target_id if previous.spec.target.is_upload else None,
                                file_ids=None)
        spec = replace(previous.spec, target=target)
        # **경계를 직전 작업에서 이어받는다**(코드리뷰 #1). 트리거 봉투에도 `labId` 가
        # 실려 오지만 이 seam 의 `InvalidationEvent` 에는 그 자리가 없고(계약을 넓히지
        # 않는다), 재생성은 **이미 그린 적 있는 대상**에만 서므로 직전 작업이 답을 안다.
        job = self.submit(new_ulid(), spec, temporary=target.is_upload, event=event,
                          lab=previous.lab, account=previous.account)
        # **끝난 뒤에 답한다**(코드리뷰 #2). 집행은 완료 경로가 하므로, 여기서 기다리지
        # 않으면 「무효화 몇 건」이 언제나 0 인 보고서가 나가고 트리거는 그 상태로 ack 된다.
        # ⚠ `manual` 실행기는 `run_pending` 이 부를 때까지 아무것도 돌지 않는다 —
        #   기다리면 그대로 멈춘다. 그 실행기는 시험 전용이고 시험이 순서를 정한다.
        if self._execution != "manual":
            job.done.wait(timeout=spec.deadline_seconds + _COMPLETION_GRACE_SECONDS)
        return Regeneration(job=job, plan=job.invalidation,
                            removed=job.invalidation_removed)

    def _latest_for(self, target_id: str) -> RenderJob | None:
        """그 대상의 가장 최근 완료 작업. **렌더 파라미터를 지어내지 않으려고** 둔다."""
        found = None
        for job in self._jobs.values():
            if job.spec.target.target_id == target_id and job.status == STATUS_DONE:
                found = job
        return found


@dataclass(frozen=True)
class Regeneration:
    """재생성 한 회의 결과 — 세 단계가 각각 관측된다(완료 정의 ⓑ)."""
    job: RenderJob
    plan: "invalidation.InvalidationPlan | None"
    removed: tuple[Path, ...]
