# 2026-09-10 모든 포맷 미리보기 구현 기록

> 후속 배포 당시 기록은 `dev-package/sessions/20260910-preview-dev-stage-deployment.md`에 보존했다. 2026-09-10 main 동기화에서 복구한 과거 기록이며, 현재 실행 환경을 다시 검증했다는 의미가 아니다.

- 요청 원문: `GRIB과 일반 HDF5까지 미리보기를 확장하는 작업. 미리보기 모두 지원하는 작업`
- 기준: `47cce303f0efb9d9bfa37d1f5a086030caea1ab6`
- 격리 브랜치: `codex/preview-all-formats`
- lifecycle task: `812a8440e4444ffca061109141e6e142`
- 구현 가정과 완료 조건: `dev-package/intent/2026-09-10-preview-all-formats.md`, `dev-package/prd/specs/preview-all-formats.md`
- 상태: 구현·로컬 검증 완료, 배포 대기

## 구현 결과

pipeline-worker와 viz-render의 지원 범위를 NetCDF, Binary, HDF4, GeoTIFF, NumPy, GRIB, HDF5 일곱 종으로 맞췄다. GRIB1/2는 GDAL 메시지 메타데이터로 메시지·시각·층·격자를 가르고, HDF5는 percent-escape된 전체 dataset 경로와 명시 slice를 선택 ID로 쓴다. UI는 opaque ID 대신 HDF5 경로·slice와 GRIB 메시지·시각·층·격자 label을 표시한다. HDF5 slice는 dataset당 4,096개를 넘으면 명시적으로 거절하며, 같은 그룹의 유일한 유효 lat/lon 쌍만 좌표로 쓴다.

## 실측 근거

- pipeline-worker service 시험 `261 passed / 0 failed / 46 deselected`; 부모 독립 신규 포맷 집중 재실행 `21 passed / 0 failed / 0 skipped`.
- 실제 GRIB1/2 각 4 message(2026-01-01 00/06 UTC × 850/500 hPa)의 서로 다른 값을 복원했다. fixture SHA-256은 GRIB1 `83ffe60847ffd9d1a39f55a031d42dc50a234efb74df64788a28c2e1a8217a13`, GRIB2 `7ee2d6ff2548d39434c89aca522dc7426d5b51fc45e60e9e3d4735ce91d38a05`다. 149 MB `surface.grib` 72 bands도 실제 판독했다.
- browser disposable 환경에서 HDF5와 GRIB2는 `agent-browser select`로 두 번째 선택 ID를 고른 뒤 select 값과 서버 `legend.variable`이 같은지 확인하고 PNG를 decode했다. 등록 첫 이동은 버튼에 키보드 focus를 확인하고 Enter로 실행했으며 포인터 클릭 성공을 입증한 것은 아니다. 등록 메타데이터와 상세 기본 이미지, reload 뒤 기본 이미지도 확인했다. 로그는 `dev-package/reports/20260910-preview-all/supplemental/browser-hdf5-full.log`, `browser-grib2-full.log`이다. GRIB1은 preview-only와 실제 decoder 회귀로 구분해 증명했다.
- viz-render와 pipeline-worker x86_64 Docker build는 exit 0이며 실행 이미지에서 h5py 3.16.0, rasterio 1.5.1, GDAL GRIB·HDF5 driver를 확인했다. 로그는 같은 supplemental 디렉터리의 `docker-pipeline.log`, `docker-pipeline-runtime.log`이다.

## 미실측·제약

`render-latency` 25 samples는 기존 다섯 포맷만 잰다. GRIB/HDF5 지연과 149 MB GRIB 전체 72-band COG 비용, Docker arm64, staging/dev 배포와 배포 후 E2E는 미실측이다. 이 작업의 구현 완료는 격리 사본의 로컬 검증 완료이며 배포 완료를 뜻하지 않는다.
