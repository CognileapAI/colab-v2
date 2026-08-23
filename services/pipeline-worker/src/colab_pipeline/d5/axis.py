"""기준 격자 파일의 **축 판별** — 서버가 파일에서 읽는다 (`〈63〉-㉰`).

사람에게 묻지 않는다 — 계약에 `gridAxis` 가 없고(`FileRef`·`UploadFileRef`·`DatasetFile`
전부 4값), `DATAMODEL §4.1`(`DR-14`)이 「좌표계·격자는 파일에서 자동 추출」로 이미 못박았다.

**출력은 `carries_lat` · `carries_lon` 두 불리언이다**(`〈66〉`) — 축 문자열 하나가 아니다.
실물 16건 중 2건이 한 파일에 `lat`·`lon` 을 다 담는다(`sessions/P2-W0-1-measurement.md §2.2`).

규칙 — 실측(`측정 §4.2`)이 지지하는 **합의(合議)** 이고 순서가 있다:

  ① **컨테이너 내부 변수명** (`.nc`/HDF5 의 `lat`·`lon`) — 파일이 스스로 축을 말한다.
     값 범위로 **교차검증**하고, 어긋나면 값을 따르고 불일치를 기록한다.
  ② **값 범위 — `max > 90` 또는 `min < -90` 이면 위도일 수 없다 → 경도.**
     **이 배제는 단독으로 성립한다**(`〈65〉` 유권해석). `〈63〉-ⓑ`「값 범위는 보조」는
     `[-90,90]` 안의 모호 구간을 겨눈 조문이고, 물리적 불가에 의한 배제는 그 대상이 아니다.
     실측 경도 8/8 이 이 한 단계로 확정됐다 — ⓑ 를 문면대로 구현하면 이미 확정된 것을
     쌍 정합으로 내려보낸다.
  ③ **쌍 정합**(1차 신호, `〈63〉-ⓑ`) — 한 업로드 안에 **형상이 같은 격자가 정확히 2건**이면
     하나는 위도·하나는 경도다. max·범위가 큰 쪽이 경도(실측 8/8). 하나가 이미 ②로 서 있으면
     나머지는 여집합으로 정해진다. **2건이 아니면 짝짓기가 미정의**다 — 지어내지 않는다
     (측정 R-3: `4_tif`·`5_HDF5` 는 4파일이 전부 같은 형상이고 MODIS 위도 2건은 값 통계까지 같다).
  ④ **이방성**(축별 변화량)은 **교차검증 전용**. 단독 14/16 이고, 틀릴 때 **경도를 조용히
     「위도」로 뒤집는다**(MODIS Sinusoidal 2건). 확정 근거로 쓰지 않는다.
  ⑤ **파일명**은 **대조 전용**. 실측 16/16 이지만 한 기관 관례라 표본 편향이다. 값과 어긋나면
     값을 따르고 불일치를 기록한다. **단독으로는 아무것도 확정하지 않는다.**
  ⑥ 어느 단계도 확정 못 하면 **판별 실패**다. `〈66〉` 유권해석 — 그 파일은 **거절**되고
     **축이 빈 행을 만들지 않는다.** 등록 자체는 막지 않는다(`〈63〉-ⓒ`).

**⚠ 못 정하면 지어내지 않는다** — PoC 가 좌표를 **합성**해(등간격 배열을 지어내) 「성공」을
반환했던 자리다(`DR-9`).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

LAT_LIMIT = 90.0

#: 축을 직접 말하는 내부 변수명. 대소문자 무시.
_LAT_NAMES = ("lat", "latitude", "y_lat")
_LON_NAMES = ("lon", "longitude", "long", "x_lon")

_MAX_SAMPLE = 4096          # 통계는 창으로 낸다 — 전체 적재 금지 (`DR-11`)


class AxisUndeterminedError(Exception):
    """축을 확정하지 못했다. **빈 축이 아니라 예외다** — 행을 만들지 않는다 (`〈66〉`)."""


@dataclass(frozen=True)
class AxisDetection:
    carries_lat: bool
    carries_lon: bool
    method: str
    evidence: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class UploadAxisResult:
    resolved: dict[Path, AxisDetection] = field(default_factory=dict)
    rejected: dict[Path, str] = field(default_factory=dict)


@dataclass(frozen=True)
class _Stats:
    shape: tuple[int, ...]
    vmin: float
    vmax: float
    mad_down: float
    mad_right: float

    @property
    def span(self) -> float:
        return self.vmax - self.vmin


# ── 값 읽기 ────────────────────────────────────────────────────────────────
def _stats(arr) -> _Stats:
    a = np.asarray(arr[: _MAX_SAMPLE, : _MAX_SAMPLE], dtype="f8")
    if a.ndim != 2:
        raise AxisUndeterminedError(f"2차원이 아니다: shape={getattr(arr, 'shape', None)}")
    finite = a[np.isfinite(a)]
    if finite.size == 0:
        raise AxisUndeterminedError("유한한 값이 없다")
    down = float(np.abs(np.diff(a, axis=0)).mean()) if a.shape[0] > 1 else 0.0
    right = float(np.abs(np.diff(a, axis=1)).mean()) if a.shape[1] > 1 else 0.0
    return _Stats(tuple(arr.shape), float(finite.min()), float(finite.max()), down, right)


def _read_npy(path: Path) -> _Stats:
    arr = np.load(path, mmap_mode="r", allow_pickle=False)
    return _stats(arr)


def _read_container(path: Path) -> dict[str, _Stats]:
    """`.nc`/HDF5 의 2차원 좌표 변수만 골라 읽는다. 없으면 빈 dict."""
    import h5py

    out: dict[str, _Stats] = {}
    with h5py.File(path, "r") as f:
        def _visit(name, obj):
            if isinstance(obj, h5py.Dataset) and obj.ndim == 2:
                base = name.rsplit("/", 1)[-1].lower()
                if base in _LAT_NAMES or base in _LON_NAMES:
                    out[base] = _stats(obj)
        f.visititems(_visit)
    return out


def _is_container(path: Path) -> bool:
    try:
        with open(path, "rb") as f:
            return f.read(8) == b"\x89HDF\r\n\x1a\n"
    except OSError:
        return False


# ── 보조 신호 (단독 판정 금지) ──────────────────────────────────────────────
def _name_claim(path: Path) -> str | None:
    n = path.name.lower()
    lat = any(k in n for k in ("lat",))
    lon = any(k in n for k in ("lon",))
    if lat and lon:
        return "둘 다"
    if lat:
        return "위도"
    if lon:
        return "경도"
    return None


def _cross_check(path: Path, s: _Stats, carries_lat: bool, carries_lon: bool) -> list[str]:
    """이방성·파일명은 여기서만 쓴다 — 확정에는 못 쓰고 불일치만 기록한다."""
    warnings: list[str] = []
    claim = _name_claim(path)
    decided = "둘 다" if carries_lat and carries_lon else ("위도" if carries_lat else "경도")
    if claim is not None and claim != decided:
        warnings.append(f"파일명은 「{claim}」이라는데 값 판정은 「{decided}」다 — 값을 따랐다")
    if not (carries_lat and carries_lon):
        aniso = "위도" if s.mad_down > s.mad_right else "경도"
        if aniso != decided:
            warnings.append(
                f"이방성 단독이면 「{aniso}」로 뒤집힌다(mad↓={s.mad_down:.6g} "
                f"mad→={s.mad_right:.6g}) — 교차검증 전용이라 따르지 않았다")
    return warnings


# ── 단독 판별 ──────────────────────────────────────────────────────────────
def detect_axes(path: Path) -> AxisDetection:
    """파일 하나만 보고 판별한다. 못 정하면 `AxisUndeterminedError`."""
    path = Path(path)
    if not path.is_file():
        raise AxisUndeterminedError(f"파일이 없다: {path.name}")

    # ① 컨테이너가 축을 직접 말한다
    if _is_container(path):
        found = _read_container(path)
        has_lat = any(k in _LAT_NAMES for k in found)
        has_lon = any(k in _LON_NAMES for k in found)
        if has_lat or has_lon:
            evidence = [f"내부 변수 {sorted(found)}"]
            warnings: list[str] = []
            for name, s in found.items():
                if name in _LAT_NAMES and (s.vmax > LAT_LIMIT or s.vmin < -LAT_LIMIT):
                    warnings.append(
                        f"내부 변수 `{name}` 이 위도 범위를 벗어난다(min={s.vmin:.6g} "
                        f"max={s.vmax:.6g}) — 이름과 값이 어긋난다")
            return AxisDetection(has_lat, has_lon, "컨테이너 내부 변수명", evidence, warnings)
        raise AxisUndeterminedError(f"컨테이너에 좌표 변수가 없다: {path.name}")

    if path.suffix.lower() != ".npy":
        raise AxisUndeterminedError(f"격자로 읽을 수 있는 형식이 아니다: {path.name}")

    s = _read_npy(path)
    # ② 물리적 불가에 의한 배제 — 〈65〉. 단독으로 선다
    if s.vmax > LAT_LIMIT or s.vmin < -LAT_LIMIT:
        ev = [f"min={s.vmin:.6g} max={s.vmax:.6g} — 위도일 수 없다(|값| > 90)"]
        return AxisDetection(False, True, "값 범위(물리적 불가)", ev,
                             _cross_check(path, s, False, True))

    # ③ 여기서부터 모호하다 — 단독으로는 못 정한다
    raise AxisUndeterminedError(
        f"값이 [-90,90] 안이라 단독으로는 모호하다(min={s.vmin:.6g} max={s.vmax:.6g}): "
        f"{path.name} — 쌍 정합이 필요하다")


# ── 업로드 단위 판별 (쌍 정합) ──────────────────────────────────────────────
def detect_axes_for_upload(paths: list[Path]) -> UploadAxisResult:
    """업로드 안의 격자 파일들을 함께 본다. 짝은 **형상**으로 짓는다.

    정본상 데이터셋당 격자는 0~2 건이므로(`〈58〉`), 형상이 같은 무리가 3건 이상이면
    그것은 **정상 업로드가 아니다** — 짝짓기를 지어내지 않고 미확정분을 거절한다.
    """
    paths = [Path(p) for p in paths]
    res = UploadAxisResult()
    stats: dict[Path, _Stats] = {}
    pending: list[Path] = []

    for p in paths:
        try:
            res.resolved[p] = detect_axes(p)
        except AxisUndeterminedError as e:
            res.rejected[p] = str(e)
            pending.append(p)
        try:
            if p.suffix.lower() == ".npy":
                stats[p] = _read_npy(p)
        except Exception:                      # 통계조차 못 내면 쌍 정합에도 못 쓴다
            stats.pop(p, None)

    # 형상별 무리
    groups: dict[tuple, list[Path]] = {}
    for p in paths:
        if p in stats:
            groups.setdefault(stats[p].shape, []).append(p)

    for shape, members in groups.items():
        if len(members) != 2:
            continue                            # 짝짓기 미정의 — 거절 상태로 둔다
        unresolved = [m for m in members if m in pending]
        if not unresolved:
            continue
        if len(unresolved) == 1:
            other = [m for m in members if m is not unresolved[0]][0]
            od = res.resolved.get(other)
            if od is None or (od.carries_lat and od.carries_lon):
                continue
            me = unresolved[0]
            carries_lat, carries_lon = (not od.carries_lat), (not od.carries_lon)
            ev = [f"쌍 정합 — 같은 형상 {shape} 의 짝 `{other.name}` 이 "
                  f"{'경도' if od.carries_lon else '위도'}로 확정됐다"]
            res.resolved[me] = AxisDetection(
                carries_lat, carries_lon, "쌍 정합", ev,
                _cross_check(me, stats[me], carries_lat, carries_lon))
            res.rejected.pop(me, None)
            continue

        # 둘 다 모호 — max·범위가 큰 쪽이 경도 (실측 8/8). 구분이 안 되면 거절한다.
        a, b = unresolved
        sa, sb = stats[a], stats[b]
        if sa.vmax == sb.vmax and sa.span == sb.span:
            continue                            # 값으로도 안 갈린다 — 지어내지 않는다
        lon_p, lat_p = (a, b) if (sa.vmax, sa.span) > (sb.vmax, sb.span) else (b, a)
        ev_common = f"쌍 정합 — 같은 형상 {shape} 2건 중 max·범위가 큰 쪽이 경도"
        for p, (cl, cn) in ((lat_p, (True, False)), (lon_p, (False, True))):
            res.resolved[p] = AxisDetection(
                cl, cn, "쌍 정합", [ev_common], _cross_check(p, stats[p], cl, cn))
            res.rejected.pop(p, None)

    return res
