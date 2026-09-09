# 모든 지원 포맷 미리보기 사양

## 범위

렌더 가능 포맷은 `NetCDF`, `Binary`, `HDF4`, `GeoTIFF`, `NumPy`, `GRIB`, `HDF5` 일곱 종이다. 업로드 형식 제한은 두지 않되 pipeline-worker 자동 감지가 이 일곱 이름을 반환하고 `renderable=true`로 연결한다. 계약 enum은 추가하지 않고 `contracts/events/core-pipeline.json`의 설명만 실제 범위와 맞춘다.

## GRIB

GRIB1과 GRIB2 메시지를 rasterio에 포함된 GDAL GRIB 드라이버로 디코딩한다. 변수 목록은 파일 순서대로 안정적이며 선택 ID에 메시지 순번, `GRIB_ELEMENT`, `GRIB_VALID_TIME`, `GRIB_SHORT_NAME`, `GRIB_COMMENT`, 격자 유형 태그(없으면 미상)와 메시지 번호를 넣어 동명·시각·층 메시지를 구별한다. 생략 시 첫 수치 2D 메시지를 고른다. 잘못된 ID는 가능한 ID를 포함한 읽기 오류다. GDAL이 좌표계를 제공할 때만 지도형에 사용하고, CRS가 없지만 수치 2D 값은 읽히는 메시지는 비지도 결과로 낸다.

## 일반 HDF5

HDF5 루트의 NetCDF4 식별 메타데이터와 try-open 결과로 NetCDF4와 일반 HDF5를 가른다. 모든 그룹을 순회해 복소수를 제외한 실수·정수형 2차원 이상 dataset을 percent-escape된 전체 경로의 `hdf5:` 선택 ID로 노출한다. 3차원 이상은 `hdf5:/path[index,...]` 형태의 명시적 선행 차원 slice ID를 노출하며 dataset당 4,096개를 넘으면 전체 개수와 상한을 밝히고 거절한다. `_FillValue` 또는 `missing_value`를 원시값에서 정확 일치로 마스킹한 뒤 `scale_factor`, `add_offset`을 적용한다. 선택 dataset과 같은 그룹의 lat/lon만 같은 규칙으로 판독하고 형상이 같을 때 좌표로 사용한다. 없거나 모호하면 비지도 결과를 낸다.

## 실패와 검증

문자열뿐인 HDF5, 전부 결측인 선택, 손상 GRIB/HDF5, 범위 밖 slice는 영구 또는 읽기 실패로 정직히 반환한다. 실제 h5py 저장 fixture와 실제 GRIB 원천으로 디코딩을 증명한다. 일곱 포맷 커버리지와 신규 두 포맷 브라우저 사용자 여정이 완료 기준이다.
