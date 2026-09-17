# Spec: 개발 초기화 계정 프로필 검증
출처 intent: `dev-package/intent/2026-09-16-dev-reseed-profile-validation.md` (승인 2026-09-16 · Ted 최종 승인 "응")
## 문제 진술
- dev-reseed 자체 시험이 운영자 개인 승인 파일에 기대어 CI와 로컬에서 다른 경로를 검사한다.
- 실행 후보가 아닌 기본 파일에서 교수 신원을 추출하고, 조회 실패 뒤 빈 값·출력 검색이 false green을 만들 수 있다.
## 해법 개요
- 외부 승인 파일을 trust root로 유지하고 `--accounts-file` 후보를 그 기준과 대조한 뒤 같은 후보에서 교수 신원을 추출한다.
- 시험은 공개 예제에서 별도 0600 승인·후보 파일을 만들며 실제 개인 설정과 외부 시스템을 사용하지 않는다.
## 사용자 스토리
1. 개발 초기화 운영자로서 실제 실행할 계정 후보가 승인 기준과 일치하는지 파괴 단계 전에 확인하고 싶다.
2. CI 유지보수자로서 개인 설정 유무와 관계없이 같은 성공·거절 조건을 검사하고 싶다.
## 구현 결정
- 모듈 · 인터페이스: `accounts.py`의 기존 승인 기준 경로와 `--profile` 후보 분리 검증을 재사용한다. `reseed.sh`는 `professor --profile "$ACCOUNTS_FILE"` 성공과 비어 있지 않은 5개 필드를 확인한 뒤에만 후보 값을 적용한다.
- 오류 구분: 후보 검증 실패와 명시 override 불일치를 각각 `ACCOUNT_PROFILE_INVALID`, `ACCOUNT_OVERRIDE_INVALID`로 전달하고 preflight의 계정 입력 오류로 종료한다.
- SQL 식별자 정책: `provision-lab.sql`에서 읽는 교수 id·이름·역할 기본값과 `accounts.py sql`의 고정 신원 대조를 유지한다.
- 스키마 · 마이그레이션: 없음.
- API 계약: 비파괴. CLI `--accounts-file` 의미를 바로잡고 기존 외부 승인 파일 기본값을 유지한다.
## 시험 결정
- 외부 행위 기준 검증 항목: 정상 후보 통과, 누락·0644·symlink·승인 기준과 다른 후보·빈 이메일·조회 명령 실패·override 불일치 거절, 일치 override 통과.
- 실패 산출물: `preflight.json`의 failed 배열 중복 0·passed와 교집합 0·계수 일치, `stages/preflight.json.exitCode=1`, `result.json.outcome=failed`, `failedStage=preflight`, report 단계 exitCode=0.
- 판정 정확성: `secrets`, `build-plan`, `seed-inputs` 판정은 출력과 JSON에서 각 1회이며 정상 계정은 `seed-inputs` 통과. 빈 문자열을 `grep` 성공으로 읽지 않는다.
- 재사용 seam: 기존 `private`, `validate`, `professor`, `validate_seed_inputs`, preflight fixture 대역.
- 해당 서비스 단독 게이트 이름: `dev-reseed-selftest`, `selftest`.
- green-by-skip 방지: shell fixture 7건 전부 실행 계수와 각 fixture 내부 사례 계수를 출력하고 기대 개수와 일치시킨다.
## 정책 대조 (작성 시점 제약)
- 제품 도메인·스키마·계약 저촉: 없음. 개발 초기화 도구와 자체 시험만 변경한다.
- 계약 동결 해제 필요: 아니오.
### 디자인 제약 확인
대상 화면: 해당 없음(CLI 개발 도구 전용).
## 우려 항목 (판정 필요)
- 없음. intent의 결정기준과 최종 승인이 범위를 확정했다.
## 범위 밖
- 승인 기준 파일의 별도 지문·갱신 절차.
- 실제 개인 계정·비밀 열람, 실제 dev/운영 초기화·재적재·배포.
- 제품 메타데이터 필수 입력과 dev-seed 전체 호환성 검증.
## 산출 계획
- 라운드 파일: `dev-package/prd/rounds/R-DEV-RESEED-PROFILE-VALIDATION.md`.
- 예상 레인 수: 1. 계정 CLI와 preflight fixture가 같은 실행 경로를 공유하여 직렬 TDD로 처리한다.
