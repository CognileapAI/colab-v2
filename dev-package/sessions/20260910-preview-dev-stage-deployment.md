# GRIB·일반 HDF5 미리보기 dev·staging 배포 완료

- 사용자 승인: “좋아 배포 dv stage 전부”. prod·제품 데이터 삭제는 수행하지 않았다.
- 완료 시점: 2026-09-10 KST. 원격 main, dev 실행 이미지 4종, staging 실행 이미지 5종 모두 `89a28d9c0fd5d130bd88e158b69b803c590ebbd4`.
- 릴리스 태그: `dev-20260910-2`. PR #9는 같은 커밋으로 merged. H3가 PR merge 명령을 차단하여, 로컬 전수와 원격 CI 확인 후 허용된 오케스트레이터 fast-forward push를 사용했다.
- dev: https://d31zgpff2091oh.cloudfront.net . staging 검증 주소: http://127.0.0.1:3000 . staging 공개 도메인은 기존 edge 403이어서 공개 경로 E2E로 주장하지 않는다.

## 배포 후 검증

- staging: 배포 스크립트 green, 상태 15/15·skip 0, DB 체인 2/2. 최신 백업 DB 2종·볼륨 2종 재검사 통과. previews 원장 오라클은 기존 명시 면제 1건이며 해시·경로·크기 검사는 실행했다.
- dev: ARM 이미지 5종 빌드 및 실제 아키텍처 확인. doctor 15/15·실패 0·skip 0 한 번의 전체 실행 통과. 최신 저장소 판정기 해시 일치, main 조상 확인. 임시 운영자 환경 파일 삭제 확인.
- 두 환경 모두 실제 GRIB2·일반 HDF5 업로드, 두 번째 변수 ID와 서버 legend 일치, PNG 디코딩, 결과 재조회 통과. 시험 업로드 식별자는 각 smoke JSON에 보존했다. 제품 데이터는 삭제하지 않았다.
- staging은 정식 multipart 업로드를 사용했다. 처음 S3 transfer 경로 호출은 501로 종료했고 데이터 생성은 없었다.
- dev는 S3 transfer를 사용했다. 기존 단계에서는 ready=true, renderable/metadataComplete=null이 정상적으로 가능하다. 처음 시험의 과도한 ready 조건은 timeout이었고, 계약의 nullable 값을 반영한 뒤 같은 GRIB 업로드를 재사용해 실제 describe/render/PNG/재조회로 통과를 확인했다. dev의 자동 메타데이터 stage 2 활성화 또는 자동 미리보기 표시는 이번 결과로 주장하지 않는다.
- dev 공개 index와 staging index 모두 빌드 결과와 일치: SHA256 `ce4b982a7f64cb5faf33231c264e530e49ee75232aa2ac408c459f0f5cfe04de`.

## 통합 근거와 공개된 예외

- 최종 CI: https://github.com/CognileapAI/colab-v2/actions/runs/34418808832 — success.
- 서비스 통합: viz 387, pipeline 268, 프런트 1164, 타입 검사, 7포맷 17건 통과. 브라우저 HDF5·GRIB2 선택/PNG/키보드 등록/reload 및 GeoTIFF 회귀 통과. ARM에서 HDF5와 GRIB1·2 실파일 판독 통과.
- 로컬 전체 실행은 최초 green 54 / red(판정) 4 / red(준비) 0. 오래된 staging 주소 2건과 사라진 적용 시험 DB 1건은 올바른 입력으로 해당 게이트를 재실행해 통과했다. 최초 실패 기록을 성공으로 덮어쓰지 않았다.
- artifact-ownership의 실제 고아 9키(19파일·1,624,447B)는 기존 2026-09-08 캐시다. 키·증거 해시·책임·해제 조건을 정본에 명시해 증거로 보존했다. 기존 구판 19건은 별도 보류 정책이다. 배포 후에도 신규 미선언 고아 없이 통과했으며 삭제 0건이다.
- 모델 행동 평가 20과제와 별도 디자인 계측(페이지 0)은 이번 변경 범위 밖으로 명시 제외했다. 실제 사용자 흐름 E2E와 구분한다.
- GRIB/HDF5 대용량 지연 및 149MB GRIB 전체 COG 비용은 미실측이다. 지연 25 samples는 기존 5포맷만 측정했다.

## 기록 보관과 작업 사본

증거는 `dev-package/reports/20260910-preview-all/deployment-89a28d9/`에 있으며 `sha256.json`으로 복사 무결성을 확인했다. 원래 작업 사본의 미커밋 변경은 보존했다. 그 사본의 로컬 main HEAD는 배포 원격 main과 다르므로, 배포 소스의 정본은 위 원격 커밋과 태그다. 별도 `fix/upload-progress-feedback` 브랜치는 변경하지 않았다.
