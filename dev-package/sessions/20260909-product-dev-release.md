# 제품 검증 및 dev 배포 완료 — 2026-09-09 KST

- 접속: https://d31zgpff2091oh.cloudfront.net/
- 최종 배포: `47cce303f0efb9d9bfa37d1f5a086030caea1ab6` (main).
- 원격 복구 기준 태그: `dev-20260909-1`, 같은 SHA를 가리킴.
- PR #7: https://github.com/CognileapAI/colab-v2/pull/7
- 비동기 시험 대기 수정 PR #8: https://github.com/CognileapAI/colab-v2/pull/8
- 최종 main CI 성공: https://github.com/CognileapAI/colab-v2/actions/runs/34243107014

## 검증

- 최초 제품 PR의 서비스·스키마·계약·게이트 검사 성공. core-api 로컬 전체 981개 통과.
- 최종 main 프런트엔드: 81파일, 1,087개 통과. 이후 시험만 변경된 경로에서는 서비스 등 비관련 CI가 생략됨.
- 최종 소스 로컬 planning-freshness: 문서 15블록 MATCH, 적용 상태 4건 COPIED.
- 깨끗한 최종 main 작업 사본에서 ARM64 이미지 5개 및 프런트엔드 빌드 성공.
- 서버 4개 healthy, S3 저장 모드 및 EC2 인스턴스 역할 사용 유지.
- 웹 96파일 배포 완료. 최종 프런트엔드 빌드 index와 CloudFront 응답 바이트 동일.
- 최종 배포 후 deploy_doctor 단일 실행: 15/15, 실패 0, 생략 0.
- agent-browser 실서비스 로그인 화면·빈 입력 제출 비활성 및 스크린샷 육안 확인.
- 배포 전 격리 환경 E2E: 로그인·GeoTIFF 업로드·워커 처리·등록·렌더 이미지·재접속·로그아웃 통과. 실서비스 데이터 업로드 시험은 수행하지 않음.

## 발견 및 조치

초기 a3389bd 배포 사후 doctor는 EC2→CloudFront 연결 reset으로 14/15였고, 전체 재실행은 15/15였다. 최종 47cce30 배포의 사후 검사는 첫 실행에서 15/15로 통과했다.

main CI는 프로젝트 정렬 시험에서 첫 행이 두 정렬에 공통인 탓에 이전 순서를 읽어 실패했다. 전체 예상 순서를 기다리도록 수정했다. 이어 업로드 미리보기 시험의 초기 팔레트 응답 전 클릭도 발견해 선택값 준비를 기다리도록 수정했다. 관련 65개 로컬 시험과 최종 원격 전체 시험이 통과했다. 제품 실행 코드 변경은 없다.

검증 증거: `.codex/artifacts/dev-release-20260909/`의 `doctor-final.log`, `runtime-final.log`, `planning-final.json`, `build-final.sha`, `ci-final-main-watch.log`. 초기 실패 로그도 같은 폴더에 보존했다. 임시 디렉터리 로그가 사라져 최종 doctor는 영구 작업 폴더에 직접 저장하도록 한 번 더 실행했고, 다시 15/15·생략0으로 통과했다.

## 범위 및 인계

이번 검증·dev 배포는 완료했다. S3 정리 보관 기간/구현, J-1 묶음, Google IdP는 후속 개발 항목이며 전체 기능 완료로 판정하지 않는다. 실제 모델 eval은 이번 배포 증거에 포함하지 않는다.

작업 루트는 최신 main으로 갱신했다. 기존 Claude/Codex 하네스 수정 및 미추적 파일과 이전 배포 이미지는 보존했다. 이 완료 기록과 라운드 체크 갱신은 배포 후 로컬 인계 문서이며 배포 태그의 커밋에는 포함되지 않는다.
