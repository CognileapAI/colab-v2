"""렌더 작업 — 상태 3값 · 단계 3값 · 부분 실패.

**왜 작업(job)인가** — 서버 왕복이 수 초~수십 초라 동기 응답으로 두면 진행을 말할 수
없다. 정본이 요구하는 것은 「로딩 중」이 아니라 **어느 단계인지**다.

정본이 값을 준 자리는 그대로 쓴다:
  단계 = `파일 읽는 중` → `지도 그리는 중` → `범례 만드는 중` (문구 그대로)
  상태 = `그리는 중` · `완료` · `실패`. **취소를 두지 않는다** — 정본에 취소 화면이 없다.
  부분 실패는 **`완료`로 남는다** — 읽힌 조각으로 그린다. 전부 실패와 다른 자리다.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ...kernel import signing
from ...ports.source import ResolvedTarget, SourcePart
from . import raster
from .failures import FAILURE_MESSAGES, NotRenderableError, RenderError, RenderFailure
from .grid import GridUnavailableError, find_reference_grid
from .readers import FieldReadError, read_field

STAGE_READ = "파일 읽는 중"
STAGE_DRAW = "지도 그리는 중"
STAGE_LEGEND = "범례 만드는 중"
STAGES = (STAGE_READ, STAGE_DRAW, STAGE_LEGEND)

STATUS_DRAWING = "그리는 중"
STATUS_DONE = "완료"
STATUS_FAILED = "실패"

#: 파일 안에 위경도가 들어 있을 수 있는 포맷 (`DATA-REFERENCE §1.1`).
#: Binary(HSR)·HDF4 는 실측상 좌표를 밖에서 받아야 한다 — 헤더의 투영 파라미터 칸이
#: 실물에서 전부 0 이고(HSR), MODIS 는 Sinusoidal 투영 격자다.
MAY_CARRY_COORDINATES = frozenset({"GeoTIFF", "NetCDF"})


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

    def to_dict(self) -> dict:
        """`RenderJob` 스키마 그대로. **없는 것은 키째 뺀다** — null 을 넣지 않는다."""
        body: dict = {"renderId": self.render_id, "status": self.status}
        if self.status == STATUS_DRAWING and self.stage:
            body["stage"] = self.stage
        if self.expires_at is not None:
            body["expiresAt"] = self.expires_at.isoformat().replace("+00:00", "Z")
        if self.status == STATUS_DONE and self.rendered is not None:
            body["result"] = {
                "tileUrlTemplate": self.tile_url_template,
                "bounds": self.rendered.bounds_dict(),
                "legend": self.rendered.legend(),
            }
        if self.status == STATUS_FAILED and self.failure is not None:
            body["failure"] = self.failure
        if self.partial is not None:
            body["partialFailure"] = self.partial
        return body

    @property
    def expired(self) -> bool:
        return self.expires_at is not None and datetime.now(timezone.utc) >= self.expires_at


def _read_part(part: SourcePart, spec: RenderSpec) -> raster.Rendered:
    """조각 하나를 읽어 규칙 격자로 놓는다. 못 읽으면 예외 — 지어내지 않는다."""
    fmt, field_ = read_field(part.path, variable=spec.variable, instant=spec.instant,
                             max_side=spec.max_preview_side)

    reference = None
    if not field_.has_position:
        if spec.target.grid_dir is None and fmt not in MAY_CARRY_COORDINATES \
                and not spec.without_reference_grid:
            # 미리 막는 것이 옳은 유일한 자리다 — 이 포맷은 파일 안에 좌표가 없다.
            # 화면은 `짝 파일 없이 그려 보기`로 이 판단을 뒤집을 수 있다.
            raise RenderError(RenderFailure.NO_REFERENCE_GRID,
                              f"{part.file_name}: 위경도를 담은 짝 파일이 없다")
        # ⚠ 격자는 **솎기 전 원래 형상**으로 대조한다. 솎은 형상으로 찾으면 실물 격자가
        # 「안 맞는다」로 튕겨 나가고, 그 자리에서 「짝 파일이 없다」는 **틀린 이유**가 붙는다.
        native = field_.native_shape or field_.values.shape
        try:
            grid = find_reference_grid(spec.target.grid_dir, expect_shape=native)
        except GridUnavailableError as e:
            raise RenderError(RenderFailure.NO_REFERENCE_GRID, str(e)) from e
        sy, sx = field_.steps
        reference = (grid.lat[::sy, ::sx], grid.lon[::sy, ::sx])

    return raster.build(field_, palette_key=spec.palette,
                        class_count=spec.class_count, reference=reference)


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
        drawn: list[raster.Rendered] = []
        missing: list[dict] = []
        first_error: RenderError | None = None
        for part in spec.target.parts:
            try:
                drawn.append(_read_part(part, spec))
            except RenderError as e:
                first_error = first_error or e
                missing.append({"fileId": part.file_id, "fileName": part.file_name})
            except (FieldReadError, NotRenderableError, Exception) as e:  # noqa: BLE001
                first_error = first_error or RenderError(RenderFailure.UNKNOWN, str(e))
                missing.append({"fileId": part.file_id, "fileName": part.file_name})

        if not drawn:
            raise first_error or RenderError(RenderFailure.UNKNOWN, "읽힌 조각이 없다")

        _stage(STAGE_DRAW)
        merged = raster.merge(drawn)

        _stage(STAGE_LEGEND)
        job.rendered = merged
        if missing:
            # ⚠ 상태를 `실패` 로 만들지 않는다. 읽힌 조각으로 그린다.
            job.partial = {"totalParts": len(spec.target.parts),
                           "renderedParts": len(drawn),
                           "missingParts": missing}
        job.stage = None
        job.status = STATUS_DONE
    except RenderError as e:
        job.stage = None
        job.status = STATUS_FAILED
        details = {"detail": e.detail} if e.detail else None
        job.failure = {"code": e.code,
                       "message": FAILURE_MESSAGES.get(e.code, e.message),
                       **({"details": details} if details else {})}
    except Exception as e:                       # noqa: BLE001 — 마지막 그물
        job.stage = None
        job.status = STATUS_FAILED
        job.failure = {"code": RenderFailure.UNKNOWN,
                       "message": FAILURE_MESSAGES[RenderFailure.UNKNOWN],
                       "details": {"detail": f"{type(e).__name__}: {e}"}}


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
