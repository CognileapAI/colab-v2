"""WU-S1a — 축 대조 비교기(순수 함수). **DB·모델·계약 호출 0건.**

여기서 재는 것은 `d3_lineage_signals` 하나다. 적격 필터(WU-S1b)·인용 검증 집행(WU-S2)·
규칙 팔(WU-S5)은 같은 모듈을 부르지만 다른 파일에서 검사한다 — 비교기가 두 벌이 되면
「계산한 것」과 「검증하는 것」이 갈려 J3′ 의 오라클이 무의미해진다(`R-K3-STRUCTURE.md`).
"""
import pathlib

import pytest

from colab_core.domains import d3_lineage_signals as sig

U = sig.UploadAxes
C = sig.CandidateAxes


def _fields(upload, cand):
    return [e.field for e in sig.compare(upload, cand)]


def _one(upload, cand, field):
    return next(e for e in sig.compare(upload, cand) if e.field == field)


# ──────────────────────────── 기간 ────────────────────────────
@pytest.mark.parametrize("u_s,u_e,c_s,c_e,expected", [
    ("2023-01-01", "2023-12-31", "2023-06-01", "2024-06-01", True),   # 겹침
    ("2023-01-01", "2023-01-31", "2023-02-01", "2023-02-28", False),  # 안 겹침
    ("2023-01-01", "2023-06-01", "2023-06-01", "2023-12-01", True),   # 맞닿기 = 포함 겹침
    ("2023-01-01", None, "2024-01-01", "2024-02-01", True),           # 업로드 쪽 열린 구간
    ("2023-01-01", "2023-02-01", "2024-01-01", None, False),          # 후보 쪽 열린 구간
    (None, "2023-12-31", "2023-01-01", "2023-12-31", False),          # 시작이 없으면 비교 없음
    ("2023-01-01", "2023-12-31", None, None, False),                  # 후보 값 없음
])
def test_기간은_겹침이고_시작이_없으면_근거가_없다(u_s, u_e, c_s, c_e, expected):
    ev = _fields(U(period_start=u_s, period_end=u_e),
                 C(period_start=c_s, period_end=c_e))
    assert ("period" in ev) is expected


def test_기간은_타임존과_무관하게_같은_순간으로_읽는다():
    ev = _fields(U(period_start="2023-01-01T00:00:00Z", period_end="2023-01-02T00:00:00Z"),
                 C(period_start="2023-01-01T09:00:00+09:00", period_end="2023-03-01"))
    assert "period" in ev


# ──────────────────────────── CRS · 격자 ────────────────────────────
@pytest.mark.parametrize("u_crs,c_crs,expected", [
    ("EPSG:4326", "epsg:4326", True),
    ("EPSG:4326", " EPSG 4326 ", True),
    ("EPSG:4326", "epsg_4326", True),
    ("EPSG:4326", "EPSG:5179", False),
    ("EPSG:4326", None, False),
    (None, "EPSG:4326", False),
])
def test_좌표계는_정규화_동등이다(u_crs, c_crs, expected):
    assert ("crs" in _fields(U(crs=u_crs), C(crs=c_crs))) is expected


@pytest.mark.parametrize("u_grid,c_grid,expected", [
    ("1km  격자", " 1KM 격자 ", True),
    ("1km 격자", "5km 격자", False),
    ("1km 격자", "", False),
])
def test_격자는_공백·대소문자만_접는다(u_grid, c_grid, expected):
    assert ("grid" in _fields(U(grid=u_grid), C(grid=c_grid))) is expected


# ──────────────────────────── 변수 ────────────────────────────
def test_변수는_교집합_1건이면_근거다():
    ev = _one(U(variables=("NDVI", "LST")), C(variables=("ndvi", "rain")), "variables")
    assert ev.upload_value == "NDVI" and ev.candidate_value == "ndvi"


def test_변수_교집합이_없으면_근거가_없다():
    assert "variables" not in _fields(U(variables=("NDVI",)), C(variables=("RAIN",)))


def test_변수_근거는_나열_순서에_흔들리지_않는다():
    a = _one(U(variables=("LST", "NDVI")), C(variables=("ndvi", "lst")), "variables")
    b = _one(U(variables=("NDVI", "LST")), C(variables=("lst", "ndvi")), "variables")
    assert a == b


# ──────────────────────────── 파일명 ────────────────────────────
@pytest.mark.parametrize("u_name,c_name,expected", [
    ("rainfall_2023.nc", "rain_2022.nc", True),      # 토큰 접두
    ("rain_2023.nc", "rain_2022.nc", True),          # 같은 토큰
    ("rainfall_2023.nc", "xrainfall.nc", False),     # 중간 일치는 접두가 아니다
    ("rain_2023.nc", "ndvi_2022.nc", False),
    ("2023.nc", "2022.nc", False),                   # 숫자 토큰은 세지 않는다
    ("rain_2023.nc", None, False),
])
def test_파일명은_토큰_접두다(u_name, c_name, expected):
    assert ("fileName" in _fields(U(file_name=u_name), C(file_name=c_name))) is expected


def test_값이_없는_축은_근거가_한_건도_없다():
    assert sig.compare(U(), C()) == ()


# ──────────────────────────── 인용 검증 ────────────────────────────
@pytest.fixture()
def 쌍():
    return (U(file_name="rain_2023.nc", crs="EPSG:4326", grid="1km 격자",
              variables=("NDVI", "LST"), period_start="2023-01-01", period_end="2023-12-31"),
            C(dataset_id="DS1", file_name="rain_2022.nc", crs="epsg 4326", grid="1KM 격자",
              variables=("ndvi",), period_start="2023-06-01", period_end="2024-06-01"))


def test_참인_인용은_통과한다(쌍):
    upload, cand = 쌍
    for ev in sig.compare(upload, cand):
        assert sig.verify(ev, upload, cand) is True


def test_인용은_실제_값의_부분문자열이면_통과한다(쌍):
    assert sig.verify(sig.Evidence("period", "2023-01", "2024-06"), *쌍) is True
    assert sig.verify(sig.Evidence("crs", "EPSG:4326", "EPSG:4326"), *쌍) is True


def test_지어낸_값의_인용은_버린다(쌍):
    assert sig.verify(sig.Evidence("crs", "EPSG:4326", "EPSG:5179"), *쌍) is False
    assert sig.verify(sig.Evidence("variables", "NDVI", "RAIN"), *쌍) is False


def test_맞지_않는_축의_인용은_버린다():
    upload, cand = U(crs="EPSG:4326"), C(crs="EPSG:5179", variables=("ndvi",))
    assert sig.verify(sig.Evidence("crs", "EPSG:4326", "EPSG:5179"), upload, cand) is False
    assert sig.verify(sig.Evidence("variables", "NDVI", "ndvi"), upload, cand) is False


def test_계약_밖_축_이름은_인용이_되지_않는다(쌍):
    assert sig.Evidence.from_claim({"field": "생김새", "uploadValue": "a",
                                    "candidateValue": "b"}) is None
    assert sig.Evidence.from_claim({"field": "crs", "uploadValue": "",
                                    "candidateValue": "b"}) is None


# ──────────────────────────── 파생 확신도 · 근거 한 줄 ────────────────────────────
def test_확신도는_검증된_축_종류_수에서_파생된다():
    p = sig.Evidence("period", "a", "a")
    c = sig.Evidence("crs", "b", "b")
    assert sig.derive_confidence(()) is None
    assert sig.derive_confidence((p,)) == "애매"
    assert sig.derive_confidence((p, p)) == "애매"        # 같은 축 두 건은 한 종류다
    assert sig.derive_confidence((p, c)) == "확실"


def test_근거_한_줄은_검증된_항목만으로_결정적이다():
    ev = (sig.Evidence("crs", "EPSG:4326", "EPSG:4326"),
          sig.Evidence("period", "2023-01-01~2023-12-31", "2023-06-01~2024-06-01"))
    line = sig.rationale(ev)
    assert line == sig.rationale(tuple(reversed(ev)))     # 나열 순서와 무관
    assert line.startswith("기간(") and "좌표계(EPSG:4326)" in line
    assert "\n" not in line and len(line) <= 120
    assert sig.rationale(()) == ""


def test_근거_한_줄은_값이_길어도_상한을_넘지_않는다():
    ev = tuple(sig.Evidence(f, "업" * 120, "후" * 120) for f in sig.EVIDENCE_FIELDS)
    assert len(sig.rationale(ev)) <= 120


# ──────────────────────────── 경계 ────────────────────────────
def test_비교기는_app_층을_import_하지_않는다():
    src = pathlib.Path(sig.__file__).read_text(encoding="utf-8")
    assert "colab_core.app" not in src
    assert "sqlalchemy" not in src
