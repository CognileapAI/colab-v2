# AI 검색 main 통합·WSL stage 배포 기록

2026-09-13 사용자 승인: 최신 main 통합, 충돌 해결, WSL stage 배포, 검색 관련 변경 시 자동 골든 검사. dev 배포 제외와 실제 모델 평가 보류 유지.

## 반영

- `dee33683`: 레퍼런스 근거 저장·조회·검색 연결 및 화면과 ELI HTML.
- `77b7c606`: 최신 main `b0ebd4c6` 통합. 충돌 3개 해결, 운영자 읽기 의도 보존. 미배포 migration은 `0031_search_evidence`로 이동하고 `0030_merge_audit_and_backoffice`를 잇는다.
- `fe4bb48a`: 검색 관련 diff의 `search-golden` CI 잡과 일회용 DB 러너.
- `d47edbf1`: 새 본체 표의 권한 실효 검사, 보호 정책 제거 음성 시험, 팔레트 준비 대기.
- `95c9667e`: 계정 목록의 실제 행 표시를 기다리도록 시험 보완.

## 검증

- 로컬 서버 전체 1,186건 및 추가 운영자 근거 접근 경계 시험 묶음 9건 통과.
- 화면 전체 1,316건과 빌드 통과. Linux 검증 사본의 프런트 335개 추적 경로가 동일함을 대조. 이후 비동기 준비 보완은 CI 전체 시험으로 재확인.
- helper 43건, 공개 API 골든 12문항, 러너 자체 시험 3건 통과.
- 계약 호환성, 생성물, import 경계, migration head, schema drift, RLS, 대장 일치 검사 통과.
- 권한 실효는 40개 연구실 경계 표 전수 검사. 보호 장치를 제거하는 자체 시험 등 20건 통과.
- [최종 기능·시험 변경 CI 성공](https://github.com/CognileapAI/colab-v2/actions/runs/34708684365). [RLS와 서버 전체 재검증](https://github.com/CognileapAI/colab-v2/actions/runs/34708440182)의 화면 대기 실패는 최종 실행에서 해결.

## 배포

WSL stage [공개 주소](https://www.colab-hydro.com)에 표준 `infra/staging/deploy.sh --target staging`으로 배포했다. 최초 기능 커밋 `fe4bb48a57e5`는 배포 전 백업 2프로파일, 상태 15항목, DB 체인 2항목을 전부 통과했다. 공개 JS는 배포 컨테이너 파일과 바이트 동일하며, 새 근거 API의 비인증 요청은 401이다. 후속 `d47edbf11c6b` 자동 배포도 green. 이후 커밋은 시험·기록 변경이며 제품 코드는 동일하다.

최종 커밋별 실제 배포 상태는 저장소 `.git/deploy-releases/`와 `~/colab-v2-releases/release-ledger.tsv`의 표준 실행 기록에 남는다. 운영자 알림은 spool에 queued 상태로 기록하며 실제 전달 완료로 말하지 않는다.

## 계속 보강할 것

[골든셋 자동 검사·보강 방법](../../../eval/k4-search/README.md). PR/main 변경 감지의 정본은 `.github/workflows/ci.yml`의 `search-golden` 필터다.

실제 Sonnet 호출 품질 평가와 인증된 stage 저장·검색 사용자 여정은 이번 통과 범위 밖이다. 고정 해석의 API 회귀를 모델 품질 평가로 대체하지 않는다. K4는 품질 수용 전까지 열린 상태를 유지한다.
