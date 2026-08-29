# D5-GRID — 파일 내부에서 격자·좌표계를 산출한다

브랜치 `d5-grid`. 범위는 한 문장이다 — **「파일 내부에서 격자·좌표계를 산출해, 지금 떨어지는 39건이 떨어지지 않게 한다」.** 그 밖은 건드리지 않았다.

## 0. 완료 정의

- **가공 뒷단 전체의 완료 정의는 미작성**이다(Ted 판정 대기). 이 조각만 위 한 문장으로 한정했다.
- **지시와 실물이 어긋난 것 1건** — 지시가 읽으라고 한 `dev-package/sessions/D5-STAGE2-SCOPE.md` 는 **레포에 없다**(실측: `ls dev-package/sessions/` 에 `D5.md`·`S2-STAGE1-VERIFY.md`·`STAGE1-CLOSE.md`·`STAGE2-PARALLEL-MAP.md`·`STAGE2-PREP.md`·`STAGE2-READY.md`). 근거는 `STAGE2-READY.md §175`(D5 stage 2 파트 ⑷ 좌표계 변환)로 대신했다. 조사 문서가 없어도 **작업의 근거는 실물 재측정**이라 진행했다.

## 1. 실측된 red — 재현

`grid_dir=None`(기준 격자 후주입 없음)으로 운영 이미지 안에서 실파일을 돌렸다.

```
tests/test_internal_grid_real.py  →  4 failed, 1 passed
  gk2a_ami_le2_lst_ko_202005010000.nc: ['좌표/격자 없음 — 지어내지 않는다 (DR-9): 기준 격자 디렉터리가 지정되지 않았다']
  … (GK-2A 141건 · MODIS 8건 전건 동일 사유)
  test_internal_grid_matches_the_shipped_reference_grid → ModuleNotFoundError: colab_pipeline.d5.internal_grid
```

**1 passed 는 음성 시험**(HSR 은 격자 없으면 실패여야 한다)이다 — 처음부터 green 인 것이 옳고, 완화가 HSR 로 번지지 않았음을 지킨다.

## 2. 정본 「✅확인」을 실물로 재확인 — **일치**

`DATA-REFERENCE §1.1` 이 HDF4·NetCDF 를 「파일 내부만으로 계산된다 ✅확인」으로 적었다. **정본을 근거로 코드를 고치지 않고, 먼저 다시 쟀다**(`§0` — ✅확인도 마지막으로 적은 값이다).

운영 이미지 `colab-v2/pipeline-worker:30b3e0a7b3f3` · 원천 읽기 전용 마운트 · `docker run --rm`.

| 포맷 | 파일이 실제로 주는 것 | 계산 vs 동봉 격자 최대오차 | 정본 기재 | 판정 |
|---|---|---|---|---|
| HDF4 (MODIS `h27v05`) | `StructMetadata.0` — `Projection=GCTP_SNSOID` · `ProjParams=(6371007.181,0,…)` · `UpperLeftPointMtrs=(10007554.677,4447802.078667)` · `LowerRightMtrs=(11119505.196667,3335851.559)` · `XDim=YDim=2400` | 위도 **0.0** · 경도 **2.84e-14°** | 7e-14° | **일치**(같은 자릿수, 합격선 안) |
| NetCDF (GK2A `ko020lc`) | `gk2a_imager_projection` — `lambert_conformal_conic` · 표준위도 30/60 · 원점 38/126 · `pixel_size=2000` · `image_width/height=900` · `upper_left_easting/northing=∓899000` | 위도 **6.91e-06°** · 경도 **1.26e-05°** | 1.3e-5° | **일치** |

⚠ **타원체는 재서 골랐다.** GK2A 는 타원체를 안 적는다. 구 `R=6371008.77` 로 세우면 위도 **1.997e-02°**·경도 3.376e-02°(약 2 km) 어긋나고, `R=6371000` 도 같다. **WGS84 타원체만 정본 합격선(1.3e-5°)을 만족한다.** 이 선택이 곧 좌표값의 판정이라 코드에 주석으로 박았다.

⚠ **HSR 은 그대로다** — 헤더 투영 파라미터 자리가 0 이라 기준 격자 파일이 계속 필수다(`§0 M-8`). 완화는 HDF4·NetCDF 에만 걸었다.

## 3. 직접 원인 — 재확인

- `services/pipeline-worker/src/colab_pipeline/d5/parse.py` `_parse_hdf4` 가 `meta.crs_embedded = False` 로 **고정**했다 → MODIS 8건이 후주입 강제로 실패.
- 같은 파일 `_parse_netcdf` 은 `lat`/`lon` **좌표 변수가 있을 때만** `crs_embedded=True` 로 올렸다. GK2A 는 좌표 변수가 없고 투영 변수만 있다 → 31건 실패.
- 경로는 지시가 말한 `domains/d5*/parse.py` 가 아니라 **`d5/parse.py`** 다(실측).

## 4. 구현

새 모듈 `d5/internal_grid.py` — 파일 내부만으로 위경도를 만든다.

- `hdf4_sinusoidal_grid` — `StructMetadata.0` 파싱 → Sinusoidal(`+R=ProjParams[0]`) 역투영, 셀 **중심**.
- `netcdf_projection_grid` — CF `grid_mapping` 변수 → `lambert_conformal_conic` 만 지원. 다른 `grid_mapping_name` 은 **세우지 않고 예외**.
- `describe_internal_grid` — 파싱 단계에서 **실제로 한 번 세워 보고** 판정한다. 「속성이 있다」로 판정하지 않는다(`§0 M-8` — 필드가 있는 것과 값이 채워진 것은 다르다).
- 못 세우면 `InternalGridUnavailable` → 호출자는 기존대로 `[미상]` + FAILURE. **좌표를 지어내는 경로는 없다(DR-9).**

`parse.py`·`pipeline.py` 는 이 모듈을 부르도록만 고쳤다. `pipeline._embedded_latlon` 은 ① 좌표 변수 ② 투영 속성 순으로 본다.

## 5. green — 세는 기준

**세는 단위 = 원천 본체 파일 1건 · 시점 2026-08-29 · `grid_dir=None`(후주입 없음)으로 좌표계 단계 통과.**

| 항목 | 값 |
|---|---|
| GK-2A `.nc` 본체 | **141/141 통과** (`02.File-format/file_format_2_nc/00.Data/gk2a_*.nc` 실측 개수) |
| MODIS `.hdf` 본체 | **8/8 통과** |
| 합 | **149/149** |

운영 dry-run 의 39건(GK-2A 31 · MODIS 8)은 이 149건의 **부분집합**이다 — 원천 전량이 통과하므로 39건을 덮는다. ⚠ **운영 원장 12행에 등록된 그 39건 자체를 다시 돌려 센 것은 아니다** — 원장 되쓰기 금지·읽기 전용 제약 안에서 원천 상위집합으로 대신했다.

## 6. 오차 합격선

| 값 | 출처 |
|---|---|
| HDF4 **7e-14°** | `dev-package/DATA-REFERENCE.md §1.1` 표 |
| NetCDF **1.3e-5°** | 같은 표 |

새로 만들지 않았다. 시험 `tests/test_internal_grid_real.py` 의 `TOL_HDF4_DEG`·`TOL_NETCDF_DEG` 가 이 값이다.

## 7. 게이트 — 축자

```
### stage2-markers          (운영 이미지 안, COLAB_STAGE2_PY=/usr/local/bin/python)
17 passed, 140 deselected, 1 warning in 1.23s
stage2 마커 — 수집 17 · skipped 0 · failed 0 · errors 0
RC=0
### stage2-markers-selftest
  ✓ ⓐ 마커 0 건 — red
  ✓ ⓑ skip — red
  ✓ ⓒ fail — red
SELFTEST_RC=0
### import-boundary
Contracts: 8 kept, 0 broken.
import-boundary green — 계약 전부 통과.   RC=0
### banned-import
banned-import green — .py 116건, 금지 import 0.   RC=0
### ai-no-lineage-write
ai-no-lineage-write green — 계약·코드·체인 세 층 모두에서 쓰기 경로가 없다.   RC=0
### db-boundary
db-boundary: green — 단위 7개 · 스캔 대상 220건 · 위반 0   RC=0
```

시험 전량(운영 이미지 · 원천 마운트 · `-m "not dbint"`): **142 passed, 15 deselected**.

## 8. 범위 밖으로 남긴 것

- **워커 단계 스위치** `app/worker.py` 의 `stage1=True` — 안 켰다. 이 코드는 여전히 휴면이고, 이번 수정은 **휴면 모듈 안에서만** 효력이 있다. 켜는 판정은 가공 뒷단 전체 완료 정의(Ted)가 선행.
- **원장 되쓰기** — 자동 추출한 좌표계·격자를 누가 원장에 적는가는 Ted 판정 대기. 산출까지만 하고 저장 경로를 만들지 않았다.
- `contracts/**` · `core-api` · `viz-render` · `ai-service` · `frontend` · `work-items.yaml` · `03-HANDOFF.md` · `PLAN-SoT.md` · `WORK-UNITS*` — 미접촉.
- **GeoTIFF** — 정본이 같은 「완화 대상」 셋에 넣었으나 이미 `rasterio` 로 `crs_embedded=True` 라 실패 0건이었다. 손대지 않았다.

## 9. `[미확인]`

| 항목 | 무엇을 하면 풀리나 |
|---|---|
| **운영 원장 39건 자체의 사후 통과 수** | 원장 되쓰기 판정이 나온 뒤, 등록된 39건의 실제 경로로 dry-run 재실행 |
| **GK2A 타원체의 정본 근거** | 지금 근거는 「동봉 격자와의 오차가 합격선 안」뿐이다. KMA 산출 코드·명세로 타원체를 확인하면 확정된다. 명세만으로는 `🟧추론`(`§0 M-8`) |
| **`lambert_conformal_conic` 외 `grid_mapping`** | 원천에 다른 투영의 NetCDF 가 들어오면 그때 실물로 잰다. 지금은 예외로 떨어진다(지어내지 않는다) |
| **`rdr_500m_latlon.nc` ↔ `Lat_HSR.npy` 격자 갈림** | `§1` 의 열린 질문 그대로 — 이번 범위 밖 |
