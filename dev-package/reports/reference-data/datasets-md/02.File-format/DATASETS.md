# 포멧테스트(포맷 확인용) 데이터셋 정본

- 출처 문서: `#readme` 부재 — `file_format_*/01.Code/Lv1_Data Processing.py` 6벌(포맷별 변환 코드 머리 주석) · `file_format_3_bin/04.Lat_Lon_info/레이더합성자료포맷정보.pdf` · 추출일 2026-09-14 · 상태: 확정 — Ted 판정 2026-09-14
- 유형 폴더: `02.File-format/`(참조자료 뿌리 기준 · 이 문서가 놓이는 자리) — 아래 글롭은 전부 이 문서 폴더 기준 상대경로
- 표기 대응: 폴더 `Lv.N` ↔ 제품 값 `LvN` (제품 값 집합 `Lv0`~`Lv3` · `db/platform/schema.sql` CHECK)
- 프로젝트: 포멧테스트 · 설명: grib · nc · bin · tif · hdf4 다섯 포맷의 원자료와 변환 결과를 한 쌍씩 담아 포맷별 미리보기 렌더를 확인하는 프로젝트.
- 계수 기준: 파일 건수·바이트 = `glob` 매칭 후 `desktop.ini` 제외 · 2026-09-14 실측
- ⚠ **이 유형에는 Lv.0/Lv.1/Lv.2 표기가 출처에 없다.** 다른 세 유형과 달리 `#readme` 설명 문서가 없고 코드 주석만 있다. 레벨 칸의 제품 값은 폴더 규약으로 정한다 — `00.Data/` = `Lv0`(원자료) · `02.Results/` = `Lv1`(변환 결과) · 계보 파생값과 일치한다(Ted 확정 2026-09-14 ㈐). 출처에 Lv 표기가 없다는 사실은 각 행 비고에 적는다.
- ⚠ **데이터셋 경계 = 「목적 하나 = 데이터셋 하나」**(Ted 확정). 변환 결과를 물리량(변수)별로 쪼개지 않는다 — grib 3변수는 결과 1건, hdf4 6변수는 타일별 결과 1건이다. **타일별 분리(tif 2 · hdf4 2)는 목적 구분이 아니라 데이터셋당 기준 격자 파일 2건 상한이라는 시스템 제약에 따른 분리다**(`services/core-api/src/colab_core/app/routes/upload_transfers.py:40`).

## 데이터셋 표

| # | 이름 | 레벨 | 부모 | 파일 글롭 | 건수 | 바이트 | 기준 격자(쌍) | 포맷 | 미리보기 기대 | 비고 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | surface (ERA5 GRIB 원자료) | Lv0 | — | `file_format_1_grib/00.Data/surface.grib` | 1 | 149,514,336 | `file_format_1_grib/04.Lat_Lon_info/lat2d.npy`·`lon2d.npy` | GRIB1 | 렌더 성립(3패스 중 1회) | 등록됨 · 격자 칸 미출현 · 출처 Lv 표기 없음 |
| 2 | ERA5 변환 결과 | Lv1 | surface (ERA5 GRIB 원자료) | `file_format_1_grib/02.Results/slhf/ERA5_*_*.npy` ＋ `.../ssr/ERA5_*_*.npy` ＋ `.../str/ERA5_*_*.npy` | 72 | 299,022,336 | 같은 쌍 | npy | 미판정 대상 | 등록됨 · 격자 경계 위생 실패 · 출처 Lv 표기 없음 |
| 3 | GK-2A LST 원자료 | Lv0 | — | `file_format_2_nc/00.Data/gk2a_ami_le2_lst_ko_*.nc` | 143 | 50,707,958 | `file_format_2_nc/04.Lat_Lon_info/lat2d.npy`·`lon2d.npy` | NetCDF4 | 렌더 성립(3패스 중 1회) | 등록됨 · 격자 칸 미출현 · 출처 Lv 표기 없음 |
| 4 | GK-2A LST 변환 결과 | Lv1 | GK-2A LST 원자료 | `file_format_2_nc/02.Results/gk2a_ami_le2_lst_ko_*.npy` | 143 | 463,338,304 | 같은 쌍 | npy | 미판정 대상 | 등록됨 · 격자 칸 미출현 · 출처 Lv 표기 없음 |
| 5 | HSR 레이더합성 원자료 | Lv0 | — | `file_format_3_bin/00.Data/RDR_CMP_HSR_PUB_*.bin.gz` | 12 | 15,341,732 | `file_format_3_bin/04.Lat_Lon_info/Lat_HSR.npy`·`Lon_HSR.npy` | bin(gzip) | **렌더 미성립(3패스 전부)** | 등록됨 · 격자 칸 미출현 · 출처 Lv 표기 없음 |
| 6 | HSR 레이더합성 변환 결과 | Lv1 | HSR 레이더합성 원자료 | `file_format_3_bin/02.Results/RDR_CMP_HSR_PUB_*.npy` | 12 | 637,509,216 | 같은 쌍 | npy | 미판정 대상 | 등록됨 · 격자 재확인 통과 · 출처 Lv 표기 없음 |
| 7 | HLS S30 T51SYB 원자료 | Lv0 | — | `file_format_4_tif/00.Data/HLS.S30.T51SYB.*.tif` | 3 | 74,288,594 | `file_format_4_tif/04.Lat_Lon_info/HLS.S30.T51SYB.2025359T023019.v2.0_lat2d.npy`·`_lon2d.npy` | GeoTIFF | **렌더 미성립(3패스 전부)** | 등록됨 · 격자 칸 미출현 · 출처 Lv 표기 없음 |
| 8 | HLS S30 T52SCE 원자료 | Lv0 | — | `file_format_4_tif/00.Data/HLS.S30.T52SCE.*.tif` | 3 | 79,083,782 | `file_format_4_tif/04.Lat_Lon_info/HLS.S30.T52SCE.2025361T022121.v2.0_lat2d.npy`·`_lon2d.npy` | GeoTIFF | 미판정 대상 | 등록됨 · 격자 칸 미출현 · 출처 Lv 표기 없음 |
| 9 | HLS S30 T51SYB 변환 결과 | Lv1 | HLS S30 T51SYB 원자료 | `file_format_4_tif/02.Results/HLS.S30.T51SYB.*.npy` | 3 | 160,747,584 | T51SYB 쌍 | npy | 미판정 대상 | 등록됨 · 격자 재확인 통과 · 출처 Lv 표기 없음 |
| 10 | HLS S30 T52SCE 변환 결과 | Lv1 | HLS S30 T52SCE 원자료 | `file_format_4_tif/02.Results/HLS.S30.T52SCE.*.npy` | 3 | 160,747,584 | T52SCE 쌍 | npy | 미판정 대상 | 등록됨 · 격자 재확인 통과 · 출처 Lv 표기 없음 |
| 11 | hdf4 MOD15A2H h27v05 원자료 | Lv0 | — | `file_format_5_HDF5/00.Data/MOD15A2H.*.h27v05.*.hdf` | 4 | 37,562,489 | `file_format_5_HDF5/04.Lat_Lon_info/lat2d_h27v05.npy`·`lon2d_h27v05.npy` | HDF4 | **렌더 미성립(3패스 전부)** | 등록됨 · 격자 칸 미출현 · 출처 Lv 표기 없음 |
| 12 | hdf4 MOD15A2H h28v05 원자료 | Lv0 | — | `file_format_5_HDF5/00.Data/MOD15A2H.*.h28v05.*.hdf` | 4 | 17,687,060 | `file_format_5_HDF5/04.Lat_Lon_info/lat2d_h28v05.npy`·`lon2d_h28v05.npy` | HDF4 | 미판정 대상 | 등록됨 · 격자 칸 미출현 · 출처 Lv 표기 없음 |
| 13 | hdf4 MOD15A2H h27v05 변환 결과 | Lv1 | hdf4 MOD15A2H h27v05 원자료 | `file_format_5_HDF5/02.Results/MOD15A2H.*.h27v05.*.npy` | 24 | 552,963,072 | h27v05 쌍 | npy | 미판정 대상 | 등록됨 · 격자 재확인 통과 · 출처 Lv 표기 없음 |
| 14 | hdf4 MOD15A2H h28v05 변환 결과 | Lv1 | hdf4 MOD15A2H h28v05 원자료 | `file_format_5_HDF5/02.Results/MOD15A2H.*.h28v05.*.npy` | 24 | 552,963,072 | h28v05 쌍 | npy | 미판정 대상 | 등록됨 · 격자 재확인 통과 · 출처 Lv 표기 없음 |

- 데이터셋 14 · 계보 간선 7 · 자료 바이트 3,251,477,119
- 기준 격자 파일 바이트 — grib 각 8,306,048 · nc 각 3,240,128 · bin 각 26,562,948 · tif 각 107,164,928 · hdf4 각 46,080,128
- 적재 제외 = `01.Code/`(py 6건) · `03.Figure/`(png) · `desktop.ini` · `04.Lat_Lon_info/gk2a_ko020lc_latlon.nc` · `04.Lat_Lon_info/rdr_500m_latlon.nc` · `04.Lat_Lon_info/레이더합성자료포맷정보.pdf`

## 데이터셋 상세

### surface (ERA5 GRIB 원자료)

- 레벨: Lv0(원자료) — 출처에 Lv 표기 없음 · 폴더 규약 `00.Data/` 가 원자료 자리다
- 부모: 없음 — 폴더 규약상 `00.Data/` 가 계보의 뿌리다
- 파일: `file_format_1_grib/00.Data/surface.grib` · 1건 · 149,514,336 B · 단일 파일(시각·타일 구분 없음 · 내부에 시각 24 × 변수 3)
- 격자: 파일 2건 `04.Lat_Lon_info/lat2d.npy`·`lon2d.npy` · 근거 = 형상 (721, 1440) 0.25° 전지구 격자가 결과 npy 형상과 일치(`dev-package/DATA-REFERENCE.md §1`)
- 설명: ERA5 지표 변수를 담은 GRIB1 원자료. 변환 코드 머리 주석 축자는 「ERA5 GRIB → NumPy Conversion & Visualization Script」이고 시각별 변수를 npy 로 바꾸는 것이 목적이다.
- 비고: 오늘 실측 — 등록됨(1건 · 화면 접수 166,126,432 B). 기준 격자 칸 미출현으로 격자 부착 생략. **미리보기 = 3패스 중 3패스에서 그려짐(렌더 성립)** · 1·2패스는 안 그려짐, 2패스 문면 「그리는 서버에 연결하지 못했다: timed out」.

### ERA5 변환 결과

- 레벨: Lv1(변환 결과) — 출처에 Lv 표기 없음 · 폴더 규약 `02.Results/` 자리 ＋ 계보 파생값과 일치
- 부모: surface (ERA5 GRIB 원자료) — 근거 = 변환 코드 축자 `file_name = f"ERA5_{var}_{time_strings[idx]}.npy"` 로 같은 폴더의 원자료에서 생성된다
- 파일: `02.Results/{slhf,ssr,str}/ERA5_*_*.npy` · 72건 · 299,022,336 B · 변수 3(`slhf`·`ssr`·`str`) × 시각 24 · `202509010000` ~ `202509012300` 1시간 간격
- 격자: 파일 2건 `04.Lat_Lon_info/lat2d.npy`·`lon2d.npy` · 근거 = 결과 형상 (721, 1440) 이 격자 형상과 일치
- 설명: GRIB 원자료에서 변수별·시각별로 뽑아 npy 로 저장한 결과. 변수는 잠열속(slhf)·단파복사(ssr)·장파복사(str) 셋이고 각 24시각이다. 목적이 하나이므로 변수별로 데이터셋을 나누지 않는다.
- 비고: 오늘 실측 — 등록됨(72건 · 화면 접수 315,634,432 B). **격자 경계 위생 실패 1건** — 축자 「! 격자 경계 위생 실패 — 지도형 미생성. 등록은 이어간다(seq 16)」. 등록은 성립했고 지도형 산출물만 만들어지지 않았다(전지구 격자라 한반도 경계 밖).

### GK-2A LST 원자료

- 레벨: Lv0(원자료) — 출처에 Lv 표기 없음 · 폴더 규약 `00.Data/`
- 부모: 없음
- 파일: `file_format_2_nc/00.Data/gk2a_ami_le2_lst_ko_*.nc` · 143건 · 50,707,958 B · `202005010000` ~ `202005012350` 10분 간격(하루 144 시각 중 143건 · 1 시각 결번)
- 격자: 파일 2건 `04.Lat_Lon_info/lat2d.npy`·`lon2d.npy` · 근거 = 형상 (900, 900) `ko020lc` 격자가 결과 형상과 일치
- 설명: GK-2A 지표온도(LST)를 10분 간격으로 담은 NetCDF4 원자료. 변환 코드 머리 주석 축자는 「GK2A NC → NumPy Conversion & Visualization Script」다.
- 비고: 오늘 실측 — 등록됨(143건 · 화면 접수 57,188,214 B). 기준 격자 칸 미출현. **미리보기 = 1패스에서 그려짐(렌더 성립)** · 2·3패스는 안 그려짐.

### GK-2A LST 변환 결과

- 레벨: Lv1(변환 결과) — 출처에 Lv 표기 없음 · 폴더 규약 `02.Results/` 자리 ＋ 계보 파생값과 일치
- 부모: GK-2A LST 원자료 — 근거 = 파일명이 원자료와 1:1 대응(`gk2a_ami_le2_lst_ko_<시각>.nc` → `.npy`)
- 파일: `02.Results/gk2a_ami_le2_lst_ko_*.npy` · 143건 · 463,338,304 B · 시각 범위는 원자료와 동일
- 격자: 파일 2건 `04.Lat_Lon_info/lat2d.npy`·`lon2d.npy`
- 설명: nc 원자료를 시각별 배열로 바꾼 결과. 변수는 지표온도 하나이고 시각별로 파일이 갈린다.
- 비고: 오늘 실측 — 등록됨(143건 · 화면 접수 469,818,560 B). 미리보기 판정 대상 아님.

### HSR 레이더합성 원자료

- 레벨: Lv0(원자료) — 출처에 Lv 표기 없음 · 폴더 규약 `00.Data/`
- 부모: 없음
- 파일: `file_format_3_bin/00.Data/RDR_CMP_HSR_PUB_*.bin.gz` · 12건 · 15,341,732 B · `202508131000` ~ `202508131055` 5분 간격
- 격자: 파일 2건 `04.Lat_Lon_info/Lat_HSR.npy`·`Lon_HSR.npy` · 근거 = **다섯 포맷 중 유일하게 격자 파일이 반드시 필요한 포맷**이다. 헤더가 주는 것은 `nx=2305`·`ny=2881`·`dxy=500`·`map_code=1` 뿐이고 투영 파라미터 자리(36~63 B)가 전부 0 이다(`dev-package/DATA-REFERENCE.md §1.1`). 같은 폴더의 `rdr_500m_latlon.nc` 는 형상은 같으나 값이 다르고 표준위도가 없어 정본이 아니다
- 설명: 기상청 HSR 합성 반사도 바이너리 원자료. 파일 안에 좌표도 투영 파라미터도 없어 위경도 npy 쌍을 밖에서 붙여야 한다.
- 비고: 오늘 실측 — 등록됨(12건 · 화면 접수 68,467,628 B). 기준 격자 칸 미출현. **미리보기 = 3패스 전부 안 그려짐(렌더 미성립)** · 문면도 이미지도 없이 미리보기 칸이 빈 채로 남는다(`unavailable` 0 · `images` 0).

### HSR 레이더합성 변환 결과

- 레벨: Lv1(변환 결과) — 출처에 Lv 표기 없음 · 폴더 규약 `02.Results/` 자리 ＋ 계보 파생값과 일치
- 부모: HSR 레이더합성 원자료 — 근거 = 파일명이 원자료와 1:1 대응(`.bin.gz` → `.npy`)
- 파일: `02.Results/RDR_CMP_HSR_PUB_*.npy` · 12건 · 637,509,216 B · 시각 범위는 원자료와 동일
- 격자: 파일 2건 `04.Lat_Lon_info/Lat_HSR.npy`·`Lon_HSR.npy`
- 설명: bin 원자료를 시각별 합성 반사도 배열로 바꾼 결과. 형상은 (2881, 2305) 로 격자 파일과 일치한다.
- 비고: 오늘 실측 — 등록됨(12건 · 화면 접수 690,635,112 B). 격자 재확인(전체 파일 기준 영역 변경)이 떠서 확인 조작으로 통과. 미리보기 판정 대상 아님.

### HLS S30 T51SYB 원자료

- 레벨: Lv0(원자료) — 출처에 Lv 표기 없음 · 폴더 규약 `00.Data/`
- 부모: 없음
- 파일: `file_format_4_tif/00.Data/HLS.S30.T51SYB.*.tif` · 3건 · 74,288,594 B · 밴드 3(`B02` 24,577,705 · `B03` 24,819,967 · `B04` 24,890,922) · 촬영 `2025359T023019`
- 격자: 파일 2건 `04.Lat_Lon_info/HLS.S30.T51SYB.2025359T023019.v2.0_lat2d.npy`·`_lon2d.npy` · 근거 = 타일마다 위경도 npy 쌍이 따로 있고 형상 (3660, 3660) 이 결과와 일치
- 설명: HLS S30 T51SYB 타일의 Blue·Green·Red 3밴드 GeoTIFF 원자료. 변환 코드 축자는 「HLS S30 Bands: B02: Blue (459-479 nm) / B03: Green (545-565 nm) / B04: Red (620-670 nm)」다.
- 비고: 오늘 실측 — 등록됨(3건 · 화면 접수 288,618,450 B). 기준 격자 칸 미출현. **미리보기 = 3패스 전부 안 그려짐(렌더 미성립)** · 2·3패스 문면 「그리는 서버에 연결하지 못했다: timed out」.

### HLS S30 T52SCE 원자료

- 레벨: Lv0(원자료) — 출처에 Lv 표기 없음 · 폴더 규약 `00.Data/`
- 부모: 없음
- 파일: `file_format_4_tif/00.Data/HLS.S30.T52SCE.*.tif` · 3건 · 79,083,782 B · 밴드 3(`B02` 25,748,555 · `B03` 26,326,160 · `B04` 27,009,067) · 촬영 `2025361T022121`
- 격자: 파일 2건 `04.Lat_Lon_info/HLS.S30.T52SCE.2025361T022121.v2.0_lat2d.npy`·`_lon2d.npy`
- 설명: HLS S30 T52SCE 타일의 Blue·Green·Red 3밴드 GeoTIFF 원자료. T51SYB 와 같은 구성이고 촬영 시각과 타일 위치가 다르다.
- 비고: 오늘 실측 — 등록됨(3건 · 화면 접수 293,413,638 B). 기준 격자 칸 미출현. 미리보기 판정 대상 아님(판정은 T51SYB 하나로 했다).

### HLS S30 T51SYB 변환 결과

- 레벨: Lv1(변환 결과) — 출처에 Lv 표기 없음 · 폴더 규약 `02.Results/` 자리 ＋ 계보 파생값과 일치
- 부모: HLS S30 T51SYB 원자료 — 근거 = 파일명이 원자료와 1:1 대응(`.tif` → `.npy` · 같은 타일·같은 3밴드)
- 파일: `02.Results/HLS.S30.T51SYB.*.npy` · 3건 · 160,747,584 B · 밴드 3 · 파일당 53,582,528 B 동일
- 격자: 파일 2건 T51SYB 쌍
- 설명: T51SYB 타일 3밴드를 배열로 바꾼 결과. 형상은 (3660, 3660) 이고 재격자 없이 원자료 격자 위에 그대로 있다.
- 비고: 오늘 실측 — 등록됨(3건 · 화면 접수 375,077,440 B). 격자 재확인 확인 조작으로 통과.

### HLS S30 T52SCE 변환 결과

- 레벨: Lv1(변환 결과) — 출처에 Lv 표기 없음 · 폴더 규약 `02.Results/` 자리 ＋ 계보 파생값과 일치
- 부모: HLS S30 T52SCE 원자료 — 근거 = 파일명 1:1 대응
- 파일: `02.Results/HLS.S30.T52SCE.*.npy` · 3건 · 160,747,584 B · 밴드 3
- 격자: 파일 2건 T52SCE 쌍
- 설명: T52SCE 타일 3밴드를 배열로 바꾼 결과. 형상·구성은 T51SYB 결과와 같다.
- 비고: 오늘 실측 — 등록됨(3건 · 화면 접수 375,077,440 B). 격자 재확인 확인 조작으로 통과.

### hdf4 MOD15A2H h27v05 원자료

- 레벨: Lv0(원자료) — 출처에 Lv 표기 없음 · 폴더 규약 `00.Data/`
- 부모: 없음
- 파일: `file_format_5_HDF5/00.Data/MOD15A2H.*.h27v05.*.hdf` · 4건 · 37,562,489 B · 날짜 4(`A2019273`·`A2019281`·`A2019289`·`A2019297`)
- 격자: 파일 2건 `04.Lat_Lon_info/lat2d_h27v05.npy`·`lon2d_h27v05.npy` · 근거 = Sinusoidal 타일마다 쌍이 따로 있고 형상 (2400, 2400) 이 결과와 일치
- 설명: MODIS MOD15A2H 엽면적지수·광합성유효복사흡수율 산출물의 h27v05 타일 4일치. 폴더 이름은 `file_format_5_HDF5` 이나 파일 매직은 HDF4 라 데이터셋 이름을 hdf4 로 적는다.
- 비고: 오늘 실측 — 등록됨(4건 · 화면 접수 129,722,745 B). 기준 격자 칸 미출현. **미리보기 = 3패스 전부 안 그려짐(렌더 미성립)** · 2·3패스 문면 「그리는 서버에 연결하지 못했다: timed out」.

### hdf4 MOD15A2H h28v05 원자료

- 레벨: Lv0(원자료) — 출처에 Lv 표기 없음 · 폴더 규약 `00.Data/`
- 부모: 없음
- 파일: `file_format_5_HDF5/00.Data/MOD15A2H.*.h28v05.*.hdf` · 4건 · 17,687,060 B · 날짜 4(h27v05 와 동일)
- 격자: 파일 2건 `04.Lat_Lon_info/lat2d_h28v05.npy`·`lon2d_h28v05.npy`
- 설명: MOD15A2H 의 h28v05 타일 4일치. 폴더 이름은 hdf5 이나 실물은 HDF4 다. 타일이 다르면 위경도 쌍도 달라 별도 데이터셋이다.
- 비고: 오늘 실측 — 등록됨(4건 · 화면 접수 109,847,316 B). 기준 격자 칸 미출현.

### hdf4 MOD15A2H h27v05 변환 결과

- 레벨: Lv1(변환 결과) — 출처에 Lv 표기 없음 · 폴더 규약 `02.Results/` 자리 ＋ 계보 파생값과 일치
- 부모: hdf4 MOD15A2H h27v05 원자료 — 근거 = `.hdf` 파일명 어간이 그대로 이어지고 변수 접미만 붙는다(예 `MOD15A2H.A2019273.h27v05.061.2020313082826_Fpar_500m.npy`)
- 파일: `02.Results/MOD15A2H.*.h27v05.*.npy` · 24건 · 552,963,072 B · 변수 6(`Fpar_500m`·`Lai_500m`·`FparStdDev_500m`·`LaiStdDev_500m`·`FparLai_QC`·`FparExtra_QC`) × 날짜 4 · 파일당 23,040,128 B 동일
- 격자: 파일 2건 h27v05 쌍
- 설명: h27v05 타일의 HDF4 내부 서브데이터셋 6종을 날짜별로 배열로 뽑은 결과. 목적이 하나이므로 변수별로 데이터셋을 나누지 않는다.
- 비고: 오늘 실측 — 등록됨(24건 · 화면 접수 645,123,328 B). 격자 재확인 확인 조작으로 통과.

### hdf4 MOD15A2H h28v05 변환 결과

- 레벨: Lv1(변환 결과) — 출처에 Lv 표기 없음 · 폴더 규약 `02.Results/` 자리 ＋ 계보 파생값과 일치
- 부모: hdf4 MOD15A2H h28v05 원자료 — 근거 = 위와 같은 파일명 대응
- 파일: `02.Results/MOD15A2H.*.h28v05.*.npy` · 24건 · 552,963,072 B · 변수 6 × 날짜 4
- 격자: 파일 2건 h28v05 쌍
- 설명: h28v05 타일의 HDF4 서브데이터셋 6종을 날짜별로 배열로 뽑은 결과. h27v05 결과와 같은 구성이고 타일만 다르다.
- 비고: 오늘 실측 — 등록됨(24건 · 화면 접수 645,123,328 B). 격자 재확인 확인 조작으로 통과.

## 판정 기록 (Ted 확정 2026-09-14)

㈎ **다섯 포맷 중 셋이 화면에 안 그려진다 — bin · tif · hdf4.** 같은 대상을 시각을 달리해 3회 쟀고 grib·nc 만 어느 한 패스에서 그려졌다. 진단은 뒷단 한계 셋(중계 타임아웃 10초 고정인데 렌더 실소요 20~38초 · viz-render OOM kill 2회 · 413 4회)이고 대장 항목 `PV-2` 가 열려 있다. ⓐ 뒷단을 고친 뒤 다시 잰다(포맷 완주 판정을 그때로 미룬다) / ⓑ 지금 계수를 정본으로 적고 셋을 미달로 남긴다.

→ 확정: ⓑ 지금 계수를 정본으로 기록한다 — grib·nc 렌더 성립 · bin·tif·hdf4 렌더 미성립을 미달로 남긴다. 뒷단 한계 해소는 `PV-2`.

㈏ **이 유형에는 설명 문서가 없다 — 설명 칸의 근거가 코드 주석뿐이다.** 다른 세 유형은 `#readme/*.docx` 가 인자·처리 과정·레벨을 문장으로 준다. 포멧테스트는 `01.Code/*.py` 머리 주석이 전부이고, 그중 `file_format_4_tif/01.Code/Lv1_Data Processing.py` 의 머리 주석은 「ERA5 GRIB → NumPy Conversion & Visualization Script」로 **폴더와 어긋난다**(복사 흔적 · 같은 폴더의 `_SY.py`·`_SY_ver.2.py` 가 HLS S30 을 바르게 적는다). ⓐ 생산자에게 포맷별 설명 문서를 요청한다 / ⓑ 이 초안의 설명 문장을 정본으로 확정한다.

→ 확정: ⓑ 초안 설명 문장을 정본으로 확정 — 출처는 「코드 주석」으로 표기한다. 폴더와 어긋난 주석(`file_format_4_tif/01.Code/Lv1_Data Processing.py` 머리의 GRIB 문구)은 비고로 남긴다. 생산자 문서 요청은 비차단 후속.

㈐ **레벨 칸을 무엇으로 채울지.** 출처에 Lv 표기가 없어 현재 초안은 「원자료 / 변환 결과」로 적었다. ⓐ 그대로 둔다 / ⓑ 폴더 규약(`00.Data`=Lv.0 · `02.Results`=Lv.1)에 맞추어 Lv.N 을 부여한다(출처 없는 값을 화면에 세우게 된다).

→ 확정: ⓑ 폴더 규약으로 제품 값을 부여 — `00.Data` → `Lv0` · `02.Results` → `Lv1`. 근거는 폴더 규약 ＋ 계보 파생값과의 일치이고, 출처에 Lv 표기가 없다는 사실은 각 행 비고에 적는다.

㈑ **타일별 분리가 시스템 제약에서 나온 것이라 상한이 풀리면 경계가 바뀐다.** tif 2건·hdf4 2건은 목적이 달라서가 아니라 데이터셋당 기준 격자 파일 2건 상한 때문에 갈렸다. 상한이 풀리면 tif 원자료 2→1 · tif 결과 2→1 · hdf4 원자료 2→1 · hdf4 결과 2→1 로 데이터셋 14→10 · 간선 7→5 가 된다. ⓐ 현행 14/7 을 정본으로 두고 상한 완화는 별도 항목 / ⓑ 상한 완화를 먼저 하고 경계를 다시 잡는다.

→ 확정: ⓐ 현행 데이터셋 14 · 간선 7 을 유지 — 2026-09-13 확정분이고 재개봉하지 않는다. 기준 격자 파일 2건 상한의 완화는 별도 항목으로 다룬다.

## 참조

- 출처: `file_format_1_grib/01.Code/Lv1_Data Processing.py`(ERA5 GRIB → NumPy) · `file_format_2_nc/01.Code/Lv1_Data Processing.py`(GK2A NC → NumPy) · `file_format_3_bin/01.Code/Lv1_Data Processing.py` · `file_format_4_tif/01.Code/Lv1_Data Processing_SY.py`(HLS S30 밴드 정의) · `file_format_5_HDF5/01.Code/Lv1_Data Processing.py`(MODIS HDF → Lat/Lon)
- 재고 조사: `dev-package/reports/reference-data/2026-09-13-inventory-v2.md` §3 · §5-4 · §5-6
- 오늘 등록 실측: `dev-package/sessions/DR-3-run-2026-09-13.md` §1 순번 15~28 · §5 · §6
- 판정: `dev-package/intent/2026-09-13-dev-reset-reference-scenario.md` 판정 ㈏(파일 전건) · ㈐(hdf4 이름) · Q13(목적 단위) · Q14(타일 분리)
- 기계 등재표: `dev-package/tools/dev-seed/plan-manifest.yaml` seq 15~28

## 기계 블록 (생성기 입력)

```yaml
# colab-datasets v1 — 이 블록이 생성기의 입력이다. 표와 어긋나면 생성기가 비영 종료한다.
# `summary` = 러너가 화면에 그대로 치는 한 줄. `description`·`note` = 문서 요약(생성기 미출력).
project: format-test
project_name: "포멧테스트"
project_description: "grib · nc · bin · tif · hdf4 다섯 포맷의 원자료와 변환 결과를 한 쌍씩 담아 포맷별 미리보기 렌더를 확인하는 프로젝트."
folder: 02.File-format   # 참조자료 뿌리 기준 · 아래 files/grid_files 는 이 폴더 기준
datasets:
  - seq: 15
    name: "surface (ERA5 GRIB 원자료)"
    level: Lv0
    parents: []
    summary: "ERA5 지표 변수 GRIB 원본"
    files: ["file_format_1_grib/00.Data/surface.grib"]
    file_count: 1
    bytes: 149514336
    grid_files: ["file_format_1_grib/04.Lat_Lon_info/lat2d.npy", "file_format_1_grib/04.Lat_Lon_info/lon2d.npy"]
    format: "GRIB1"
    preview_expected: "렌더 성립(3패스 중 1회)"
    description: "ERA5 지표 변수를 담은 GRIB1 원자료. 변환 코드 머리 주석 축자는 「ERA5 GRIB → NumPy Conversion & Visualization Script」이고 시각별 변수를 npy 로 바꾸는 것이 목적이다."
    note: "오늘 실측 — 등록됨(1건 · 화면 접수 166,126,432 B). 기준 격자 칸 미출현으로 격자 부착 생략. **미리보기 = 3패스 중 3패스에서 그려짐(렌더 성립)** · 1·2패스는 안 그려짐, 2패스 문면 「그리는 서버에 연결하지 못했다: timed out」."
  - seq: 16
    name: "ERA5 변환 결과"
    level: Lv1
    parents: ["surface (ERA5 GRIB 원자료)"]
    summary: "GRIB 에서 변환한 slhf·ssr·str 시각별 배열"
    files: ["file_format_1_grib/02.Results/slhf/ERA5_*_*.npy", "file_format_1_grib/02.Results/ssr/ERA5_*_*.npy", "file_format_1_grib/02.Results/str/ERA5_*_*.npy"]
    file_count: 72
    bytes: 299022336
    grid_files: ["file_format_1_grib/04.Lat_Lon_info/lat2d.npy", "file_format_1_grib/04.Lat_Lon_info/lon2d.npy"]
    format: "npy"
    preview_expected: "미판정 대상"
    description: "GRIB 원자료에서 변수별·시각별로 뽑아 npy 로 저장한 결과. 변수는 잠열속(slhf)·단파복사(ssr)·장파복사(str) 셋이고 각 24시각이다. 목적이 하나이므로 변수별로 데이터셋을 나누지 않는다."
    note: "오늘 실측 — 등록됨(72건 · 화면 접수 315,634,432 B). **격자 경계 위생 실패 1건** — 축자 「! 격자 경계 위생 실패 — 지도형 미생성. 등록은 이어간다(seq 16)」. 등록은 성립했고 지도형 산출물만 만들어지지 않았다(전지구 격자라 한반도 경계 밖)."
  - seq: 17
    name: "GK-2A LST 원자료"
    level: Lv0
    parents: []
    summary: "GK-2A 지표온도 10분 간격 원본"
    files: ["file_format_2_nc/00.Data/gk2a_ami_le2_lst_ko_*.nc"]
    file_count: 143
    bytes: 50707958
    grid_files: ["file_format_2_nc/04.Lat_Lon_info/lat2d.npy", "file_format_2_nc/04.Lat_Lon_info/lon2d.npy"]
    format: "NetCDF4"
    preview_expected: "렌더 성립(3패스 중 1회)"
    description: "GK-2A 지표온도(LST)를 10분 간격으로 담은 NetCDF4 원자료. 변환 코드 머리 주석 축자는 「GK2A NC → NumPy Conversion & Visualization Script」다."
    note: "오늘 실측 — 등록됨(143건 · 화면 접수 57,188,214 B). 기준 격자 칸 미출현. **미리보기 = 1패스에서 그려짐(렌더 성립)** · 2·3패스는 안 그려짐."
  - seq: 18
    name: "GK-2A LST 변환 결과"
    level: Lv1
    parents: ["GK-2A LST 원자료"]
    summary: "nc 에서 변환한 지표온도 배열"
    files: ["file_format_2_nc/02.Results/gk2a_ami_le2_lst_ko_*.npy"]
    file_count: 143
    bytes: 463338304
    grid_files: ["file_format_2_nc/04.Lat_Lon_info/lat2d.npy", "file_format_2_nc/04.Lat_Lon_info/lon2d.npy"]
    format: "npy"
    preview_expected: "미판정 대상"
    description: "nc 원자료를 시각별 배열로 바꾼 결과. 변수는 지표온도 하나이고 시각별로 파일이 갈린다."
    note: "오늘 실측 — 등록됨(143건 · 화면 접수 469,818,560 B). 미리보기 판정 대상 아님."
  - seq: 19
    name: "HSR 레이더합성 원자료"
    level: Lv0
    parents: []
    summary: "HSR 합성 바이너리 원본"
    files: ["file_format_3_bin/00.Data/RDR_CMP_HSR_PUB_*.bin.gz"]
    file_count: 12
    bytes: 15341732
    grid_files: ["file_format_3_bin/04.Lat_Lon_info/Lat_HSR.npy", "file_format_3_bin/04.Lat_Lon_info/Lon_HSR.npy"]
    format: "bin(gzip)"
    preview_expected: "**렌더 미성립(3패스 전부)**"
    description: "기상청 HSR 합성 반사도 바이너리 원자료. 파일 안에 좌표도 투영 파라미터도 없어 위경도 npy 쌍을 밖에서 붙여야 한다."
    note: "오늘 실측 — 등록됨(12건 · 화면 접수 68,467,628 B). 기준 격자 칸 미출현. **미리보기 = 3패스 전부 안 그려짐(렌더 미성립)** · 문면도 이미지도 없이 미리보기 칸이 빈 채로 남는다(`unavailable` 0 · `images` 0)."
  - seq: 20
    name: "HSR 레이더합성 변환 결과"
    level: Lv1
    parents: ["HSR 레이더합성 원자료"]
    summary: "bin 에서 변환한 합성 반사도 배열"
    files: ["file_format_3_bin/02.Results/RDR_CMP_HSR_PUB_*.npy"]
    file_count: 12
    bytes: 637509216
    grid_files: ["file_format_3_bin/04.Lat_Lon_info/Lat_HSR.npy", "file_format_3_bin/04.Lat_Lon_info/Lon_HSR.npy"]
    format: "npy"
    preview_expected: "미판정 대상"
    description: "bin 원자료를 시각별 합성 반사도 배열로 바꾼 결과. 형상은 (2881, 2305) 로 격자 파일과 일치한다."
    note: "오늘 실측 — 등록됨(12건 · 화면 접수 690,635,112 B). 격자 재확인(전체 파일 기준 영역 변경)이 떠서 확인 조작으로 통과. 미리보기 판정 대상 아님."
  - seq: 21
    name: "HLS S30 T51SYB 원자료"
    level: Lv0
    parents: []
    summary: "HLS S30 T51SYB 타일 밴드 3종"
    files: ["file_format_4_tif/00.Data/HLS.S30.T51SYB.*.tif"]
    file_count: 3
    bytes: 74288594
    grid_files: ["file_format_4_tif/04.Lat_Lon_info/HLS.S30.T51SYB.2025359T023019.v2.0_lat2d.npy", "file_format_4_tif/04.Lat_Lon_info/HLS.S30.T51SYB.2025359T023019.v2.0_lon2d.npy"]
    format: "GeoTIFF"
    preview_expected: "**렌더 미성립(3패스 전부)**"
    description: "HLS S30 T51SYB 타일의 Blue·Green·Red 3밴드 GeoTIFF 원자료. 변환 코드 축자는 「HLS S30 Bands: B02: Blue (459-479 nm) / B03: Green (545-565 nm) / B04: Red (620-670 nm)」다."
    note: "오늘 실측 — 등록됨(3건 · 화면 접수 288,618,450 B). 기준 격자 칸 미출현. **미리보기 = 3패스 전부 안 그려짐(렌더 미성립)** · 2·3패스 문면 「그리는 서버에 연결하지 못했다: timed out」."
  - seq: 22
    name: "HLS S30 T52SCE 원자료"
    level: Lv0
    parents: []
    summary: "HLS S30 T52SCE 타일 밴드 3종"
    files: ["file_format_4_tif/00.Data/HLS.S30.T52SCE.*.tif"]
    file_count: 3
    bytes: 79083782
    grid_files: ["file_format_4_tif/04.Lat_Lon_info/HLS.S30.T52SCE.2025361T022121.v2.0_lat2d.npy", "file_format_4_tif/04.Lat_Lon_info/HLS.S30.T52SCE.2025361T022121.v2.0_lon2d.npy"]
    format: "GeoTIFF"
    preview_expected: "미판정 대상"
    description: "HLS S30 T52SCE 타일의 Blue·Green·Red 3밴드 GeoTIFF 원자료. T51SYB 와 같은 구성이고 촬영 시각과 타일 위치가 다르다."
    note: "오늘 실측 — 등록됨(3건 · 화면 접수 293,413,638 B). 기준 격자 칸 미출현. 미리보기 판정 대상 아님(판정은 T51SYB 하나로 했다)."
  - seq: 23
    name: "HLS S30 T51SYB 변환 결과"
    level: Lv1
    parents: ["HLS S30 T51SYB 원자료"]
    summary: "T51SYB 타일 밴드 3종의 변환 배열"
    files: ["file_format_4_tif/02.Results/HLS.S30.T51SYB.*.npy"]
    file_count: 3
    bytes: 160747584
    grid_files: ["file_format_4_tif/04.Lat_Lon_info/HLS.S30.T51SYB.2025359T023019.v2.0_lat2d.npy", "file_format_4_tif/04.Lat_Lon_info/HLS.S30.T51SYB.2025359T023019.v2.0_lon2d.npy"]
    format: "npy"
    preview_expected: "미판정 대상"
    description: "T51SYB 타일 3밴드를 배열로 바꾼 결과. 형상은 (3660, 3660) 이고 재격자 없이 원자료 격자 위에 그대로 있다."
    note: "오늘 실측 — 등록됨(3건 · 화면 접수 375,077,440 B). 격자 재확인 확인 조작으로 통과."
  - seq: 24
    name: "HLS S30 T52SCE 변환 결과"
    level: Lv1
    parents: ["HLS S30 T52SCE 원자료"]
    summary: "T52SCE 타일 밴드 3종의 변환 배열"
    files: ["file_format_4_tif/02.Results/HLS.S30.T52SCE.*.npy"]
    file_count: 3
    bytes: 160747584
    grid_files: ["file_format_4_tif/04.Lat_Lon_info/HLS.S30.T52SCE.2025361T022121.v2.0_lat2d.npy", "file_format_4_tif/04.Lat_Lon_info/HLS.S30.T52SCE.2025361T022121.v2.0_lon2d.npy"]
    format: "npy"
    preview_expected: "미판정 대상"
    description: "T52SCE 타일 3밴드를 배열로 바꾼 결과. 형상·구성은 T51SYB 결과와 같다."
    note: "오늘 실측 — 등록됨(3건 · 화면 접수 375,077,440 B). 격자 재확인 확인 조작으로 통과."
  - seq: 25
    name: "hdf4 MOD15A2H h27v05 원자료"
    level: Lv0
    parents: []
    summary: "폴더명 hdf5 · 실물 HDF4. h27v05 타일 4일치"
    files: ["file_format_5_HDF5/00.Data/MOD15A2H.*.h27v05.*.hdf"]
    file_count: 4
    bytes: 37562489
    grid_files: ["file_format_5_HDF5/04.Lat_Lon_info/lat2d_h27v05.npy", "file_format_5_HDF5/04.Lat_Lon_info/lon2d_h27v05.npy"]
    format: "HDF4"
    preview_expected: "**렌더 미성립(3패스 전부)**"
    description: "MODIS MOD15A2H 엽면적지수·광합성유효복사흡수율 산출물의 h27v05 타일 4일치. 폴더 이름은 `file_format_5_HDF5` 이나 파일 매직은 HDF4 라 데이터셋 이름을 hdf4 로 적는다."
    note: "오늘 실측 — 등록됨(4건 · 화면 접수 129,722,745 B). 기준 격자 칸 미출현. **미리보기 = 3패스 전부 안 그려짐(렌더 미성립)** · 2·3패스 문면 「그리는 서버에 연결하지 못했다: timed out」."
  - seq: 26
    name: "hdf4 MOD15A2H h28v05 원자료"
    level: Lv0
    parents: []
    summary: "폴더명 hdf5 · 실물 HDF4. h28v05 타일 4일치"
    files: ["file_format_5_HDF5/00.Data/MOD15A2H.*.h28v05.*.hdf"]
    file_count: 4
    bytes: 17687060
    grid_files: ["file_format_5_HDF5/04.Lat_Lon_info/lat2d_h28v05.npy", "file_format_5_HDF5/04.Lat_Lon_info/lon2d_h28v05.npy"]
    format: "HDF4"
    preview_expected: "미판정 대상"
    description: "MOD15A2H 의 h28v05 타일 4일치. 폴더 이름은 hdf5 이나 실물은 HDF4 다. 타일이 다르면 위경도 쌍도 달라 별도 데이터셋이다."
    note: "오늘 실측 — 등록됨(4건 · 화면 접수 109,847,316 B). 기준 격자 칸 미출현."
  - seq: 27
    name: "hdf4 MOD15A2H h27v05 변환 결과"
    level: Lv1
    parents: ["hdf4 MOD15A2H h27v05 원자료"]
    summary: "폴더명 hdf5 · 실물 HDF4. h27v05 변수 6종 × 4일"
    files: ["file_format_5_HDF5/02.Results/MOD15A2H.*.h27v05.*.npy"]
    file_count: 24
    bytes: 552963072
    grid_files: ["file_format_5_HDF5/04.Lat_Lon_info/lat2d_h27v05.npy", "file_format_5_HDF5/04.Lat_Lon_info/lon2d_h27v05.npy"]
    format: "npy"
    preview_expected: "미판정 대상"
    description: "h27v05 타일의 HDF4 내부 서브데이터셋 6종을 날짜별로 배열로 뽑은 결과. 목적이 하나이므로 변수별로 데이터셋을 나누지 않는다."
    note: "오늘 실측 — 등록됨(24건 · 화면 접수 645,123,328 B). 격자 재확인 확인 조작으로 통과."
  - seq: 28
    name: "hdf4 MOD15A2H h28v05 변환 결과"
    level: Lv1
    parents: ["hdf4 MOD15A2H h28v05 원자료"]
    summary: "폴더명 hdf5 · 실물 HDF4. h28v05 변수 6종 × 4일"
    files: ["file_format_5_HDF5/02.Results/MOD15A2H.*.h28v05.*.npy"]
    file_count: 24
    bytes: 552963072
    grid_files: ["file_format_5_HDF5/04.Lat_Lon_info/lat2d_h28v05.npy", "file_format_5_HDF5/04.Lat_Lon_info/lon2d_h28v05.npy"]
    format: "npy"
    preview_expected: "미판정 대상"
    description: "h28v05 타일의 HDF4 서브데이터셋 6종을 날짜별로 배열로 뽑은 결과. h27v05 결과와 같은 구성이고 타일만 다르다."
    note: "오늘 실측 — 등록됨(24건 · 화면 접수 645,123,328 B). 격자 재확인 확인 조작으로 통과."
```
