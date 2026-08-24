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
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from ...kernel import signing
from ...ports.source import ResolvedTarget, SourcePart
from . import colormap, downsample, palettes, preview, raster, scale
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
    status: str = STATUS_DRAWING
    stage: str | None = STAGE_READ
    stage_history: list[str] = field(default_factory=list)
    expires_at: datetime | None = None
    rendered: raster.Rendered | None = None
    partial: dict | None = None
    failure: dict | None = None
    tile_url_template: str = ""
    artifacts: "PreviewArtifacts | None" = None
    color_range: scale.ColorRange | None = None
    badge: str = preview.BADGE_NO_GRID
    value_variable: str = ""
    value_unit: str | None = None

    def to_dict(self) -> dict:
        """`RenderJob` 스키마 그대로. **없는 것은 키째 뺀다** — null 을 넣지 않는다."""
        body: dict = {"renderId": self.render_id, "status": self.status}
        if self.status == STATUS_DRAWING and self.stage:
            body["stage"] = self.stage
        if self.expires_at is not None:
            body["expiresAt"] = self.expires_at.isoformat().replace("+00:00", "Z")
        if self.status == STATUS_DONE and self.artifacts is not None:
            # **`oneOf` 다** — stage 1 은 이미지 갈래만 낸다. `tileUrlTemplate` 은 계약에
            # 살아 있고(stage 2 확대 뷰) 서명도 그대로 발급되지만, **결과에 함께 싣지
            # 않는다.** 둘을 함께 실으면 「무엇을 그릴지 두 번 적힌 완료」다.
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
            if a.map_image is not None and a.geometry is not None:
                result["imageUrl"] = a.map_image.url
                result["sidecarUrl"] = a.sidecar.url
                result["worldFileUrl"] = a.world_file.url
                result["bounds"] = a.geometry.bounds_dict()
            else:
                result["imageUrl"] = a.detail.url
            if result["colorRangeStage"] is None:
                # 라벨 없는 산출물은 **범위 밖이다**(`§C.2 Q4`) — 키를 지우지 않고 실패로 둔다.
                raise RuntimeError("색 범위 단계 라벨 없이 결과를 낼 수 없다")
            body["result"] = result
        if self.status == STATUS_FAILED and self.failure is not None:
            body["failure"] = self.failure
        if self.partial is not None:
            body["partialFailure"] = self.partial
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
    map_image: preview.Artifact | None = None
    sidecar: preview.Artifact | None = None
    world_file: preview.Artifact | None = None
    geometry: preview.MapGeometry | None = None

    def all(self) -> list[preview.Artifact]:
        return [a for a in (self.thumbnail, self.detail, self.map_image,
                            self.sidecar, self.world_file) if a is not None]


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
        raise RenderError(RenderFailure.NO_REFERENCE_GRID, str(e)) from e
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


def _grid_digest(reads: list[_Read]) -> str | None:
    """지도형 키에만 들어가는 격자 값 — **격자를 갈면 지도형만 무효화된다**(`§7.2`)."""
    parts = [f"{r.reference[0].shape}:{float(np.nanmin(r.reference[0])):.6f}:"
             f"{float(np.nanmax(r.reference[1])):.6f}"
             for r in reads if r.from_uploaded_grid and r.reference is not None]
    if not parts:
        return None
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


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
                      palette=spec.palette, selection=merged.variable)
    out_dir = Path(spec.preview_dir)

    values = reads[0].field.values if len(reads) == 1 else merged.values
    thumb, detail = preview.build_value_layers(
        values, color_range=color_range, lut=lut, out_dir=out_dir,
        url_base=spec.preview_url_base, key_params=key_params)
    artifacts = PreviewArtifacts(thumbnail=thumb, detail=detail)

    coords = _map_coordinates(reads, merged if not isinstance(merged, _ValuesOnly) else None)
    if coords is None:
        return artifacts
    map_values, lat, lon = coords
    image, sidecar, world, geom = preview.build_map_layer(
        map_values, lat, lon, color_range=color_range, lut=lut, out_dir=out_dir,
        url_base=spec.preview_url_base, key_params=key_params,
        grid_digest=_grid_digest(reads), source_name=reads[0].part.file_name)
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
            except (FieldReadError, NotRenderableError, Exception) as e:  # noqa: BLE001
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
        job.failure = _failure(e.code, e.detail, job,
                               message=FAILURE_MESSAGES.get(e.code, e.message))
    except Exception as e:                       # noqa: BLE001 — 마지막 그물
        job.stage = None
        job.status = STATUS_FAILED
        job.failure = _failure(RenderFailure.UNKNOWN, f"{type(e).__name__}: {e}", job)


class JobStore:
    """렌더 작업 보관 — 프로세스 안 메모리다.

    ⚠ **의도적으로 여기까지다.** 미리보기 결과는 정본이 「임시로만 둔다」고 못박은 것이라
    영속 저장소를 요구하지 않는다. 다만 **인스턴스가 여럿이면 타일 요청이 다른 인스턴스로
    갈 수 있다** — 배포 형상(고정 라우팅이냐 공유 캐시냐)은 `WU-I1` 판단이고 이 레인의
    소유가 아니다. 감추지 않고 적어 둔다.
    """

    def __init__(self, *, execution: str, tile_url_base: str, ttl_seconds: int,
                 tile_signing_secret: str | None = None,
                 signature_ttl_seconds: int | None = None) -> None:
        self._jobs: dict[str, RenderJob] = {}
        self._pending: list[RenderJob] = []
        self._lock = threading.Lock()
        self._execution = execution
        self._tile_url_base = tile_url_base.rstrip("/")
        self._ttl = ttl_seconds
        self._secret = tile_signing_secret
        self._sig_ttl = ttl_seconds if signature_ttl_seconds is None else signature_ttl_seconds

    def submit(self, render_id: str, spec: RenderSpec, *, temporary: bool) -> RenderJob:
        job = RenderJob(render_id=render_id, spec=spec)
        now = datetime.now(timezone.utc)
        if temporary:
            # 등록 전 업로드의 미리보기 결과는 서버에 임시로만 둔다 (정본 §8 ③ · `NB-2`)
            job.expires_at = now + timedelta(seconds=self._ttl)
        job.tile_url_template = self._tile_url(render_id, job.expires_at, now)
        with self._lock:
            self._jobs[render_id] = job

        if self._execution == "inline":
            _run(job)
        elif self._execution == "manual":
            self._pending.append(job)
        else:
            threading.Thread(target=_run, args=(job,), daemon=True).start()
        return job

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
            _run(self._pending.pop(0))

    def get(self, render_id: str) -> RenderJob | None:
        return self._jobs.get(render_id)
