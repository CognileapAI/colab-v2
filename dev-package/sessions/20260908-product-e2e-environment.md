# 제품 사용자 여정 E2E 환경 조사 — 2026-09-08

읽기 전용 조사. 소스 HEAD `ccf76ecf0bb53fa100088a36bcc112ae953ce3b9`.
본 조사에서는 앱 기동·컨테이너 변경·로그인·업로드·DB 변경을 실행하지 않았다.

## 확인 결과

- `docker ps` 실측: `colab_v2_staging_` 컨테이너 8개만 실행 중이었다.
  조회 시점 상태는 모두 `Up 4 seconds (health: starting)`였다. 본 조사에서 기동한 것이 아니다.
  제품 이미지 태그는 `8158e87c5bb9`, nginx 호스트 포트는 `127.0.0.1:3000`.
  따라서 localhost라는 이유로 3000을 일회용 쓰기 테스트 대상으로 삼을 수 없다.
- `frontend/package.json`: Vite dev/build, Vitest 명령만 존재. 브라우저 E2E 명령은 없다.
  `frontend/vite.config.ts`의 개발 프록시는 `/api` → `127.0.0.1:8000` 고정이다.
  Vite를 임의 기동하는 것만으로 격리된 백엔드가 생기지 않는다.
- `infra/dev/README.md`는 AWS EC2/RDS/S3 개발 배포 런북이다. 로컬 일회용 환경 문서가 아니다.
- `infra/staging/compose.throwaway.yml`은 별도 프로젝트/볼륨/tmpfs PostgreSQL로 분리하지만
  호스트 포트를 열지 않고 `:i2` 기존 이미지를 쓴다. `restore/throwaway-stack.sh`는
  platform/ai 덤프를 요구하고 기존 서빙 이미지와 alias freshness를 대조하는 복원 리허설이다.
  이를 그대로 실행하면 현재 미커밋 제품 코드의 브라우저 E2E 검증이 되지 않는다.
- `gates/tools/frontend-visual.sh`는 agent-browser 읽기 전용 글자 크기/대비/스크린샷 검사다.
  클릭·입력·제출을 하지 않으므로 사용자 여정 저장 검증을 대신하지 않는다.
- `frontend/test/auth.test.tsx`는 fetch를 stub하는 Vitest 테스트다. 실제 로그인 증거가 아니다.
- 테스트 계정 원본 후보는 `services/core-api/tests/fixtures/seed.sql`과 `subjects.json`.
  실계정·운영 자격 파일을 읽지 않았다. 격리 브라우저 로그인용 비밀번호/계정은 준비 확인 전이다.
- `services/pipeline-worker/tests/fixture_builders.py`에 실제 파싱 가능한 `make_netcdf` 및
  `make_readable_geotiff`가 있다. GeoTIFF 함수는 numpy/rasterio로 픽셀·EPSG:4326을 기록한다.
  같은 파일의 초기 TIFF 생성 함수들은 헤더 판정용으로 픽셀이 없으므로 업로드 성공 fixture로
  대체하면 안 된다. 프론트 테스트의 `new File(['x'], '*.nc')` 역시 실제 데이터 파일이 아니다.

## 실행 가능한 범위와 준비 과제

현재 확정한 안전 실행 범위는 파일 조사/등록 guard/Docker 목록 확인이다.
기존 staging 로그인 화면의 읽기 확인은 쓰기 여정과 별도이나 이 조사에서는 수행하지 않았다.
전체 사용자 여정은 아래 전제 없이는 준비 실패로 남긴다.

1. 현재 소스 SHA와 미커밋 변경 식별값으로 별도 이미지 또는 개발 프로세스를 준비한다.
2. 별도 DB 두 개·새 계정/서명 비밀·uploads/previews 저장소·네트워크를 분리한다.
   운영 staging 이름/볼륨/비밀/터널과 겹치지 않아야 한다. DB는 tmpfs+PGDATA 사용.
3. 새 테스트 URL을 명시하고 Vite API 목적지도 그 격리 백엔드로 연결한다.
   기존 복원 리허설 파일을 임의 포트 공개하도록 고치는 대신 별도 E2E 진입점을 검토한다.
4. 재사용 가능한 seed를 현재 마이그레이션 head와 검증하고 새 로그인 자격을 생성한다.
5. 실제 NetCDF/GeoTIFF와 손상 fixture를 생성한다. 고유 실행 ID와 정리 대상을 기록한다.

## 준비 후 agent-browser 시나리오

별도 `--session`을 만들고 화면 변화 후 매번 snapshot ref를 새로 얻는다.
비밀은 명령 로그/보고서에 기록하지 않는다.

| 시나리오 | 사전 기대 결과 |
|---|---|
| 비인증 진입 | 로그인 폼, 보호 데이터 접근 불가 |
| 잘못된 자격 제출 → 올바른 격리 계정 로그인 | 오류가 표시되고, 정상 계정은 연구실 화면 진입 |
| 실제 파일 선택 → 업로드 → 처리 완료 → 등록 | 파일 처리 상태와 필수 메타데이터 확인, 고유 데이터셋 생성 |
| 카탈로그/검색 → 상세 → 미리보기 | 등록한 이름/식별자가 같고 실제 파일의 미리보기가 표시됨 |
| 새로고침 및 새 로그인 세션 | 저장한 데이터셋과 메타데이터가 유지됨 |
| 손상 파일 업로드 | 처리 실패가 드러나고 정상 등록으로 오인되지 않음 |

브라우저 단계별 상태·대상 ID·스크린샷을 남기되 스크린샷만으로 성공을 판정하지 않는다.
이번 조사 결과는 E2E 통과가 아니며, 현재 소스에 연결된 격리 앱이 아직 확인되지 않았다는 준비 결과다.
