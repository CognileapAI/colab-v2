# 제품 마감 실행 증거 — 2026-09-08

기준 HEAD `ccf76ec`, 작업 브랜치 `integration/r-product-finish`. 미커밋 변경 상태.
전체 제품 완료 아님. 원격 CI·배포는 실행하지 않았다.

## 확인한 실패와 변경

- 최신 main CI `34216692424`: 서비스 4개 잡 성공. 실패는 schema-gates, planning-gates, harness-eval.
- schema: 두 체인의 적용 DB 입력이 없어 78. `gates/tools/ci-schema-diff.sh`가 기존 `_pg.sh`로 일회용 DB 두 개를 준비하고, 기존 schema-diff로 실제 upgrade/비교한다.
- 홈 env 재로딩 위험은 실행 전 의존성 설치 단계에서 중단 후 수정. wrapper는 `COLAB_TEST_ENV_SOURCED=1`, 외부 입력 override 제거, 슬롯 정수 >=2 확인. 운영 DB를 시험 대상으로 사용하지 않는다.
- 최종 schema 실측: platform/ai 각각 upgrade head 뒤 선언=적용 green. 종료 후 `colab_v2_gatepg_` 잔존 컨테이너 0.
- eval: 모델을 실행하지 않는 CI 잡의 API 키 선검사를 제거. 러너와 판정부 회귀를 추가하고 과제 20건 미실행을 명시한다.
- planning: 원본은 로컬에만 존재. 원본 중복 방지 요청에 따라 로컬 원본 검사를 필수로 유지하고 CI는 합성 fixture 판정부 회귀로 분리. CI의 원본 미실행은 notice로 표시. 비공개 원본 저장소 연결을 선택하면 배치를 재조정할 수 있다.

## 실행 결과

| 검사 | 결과 | 한계 |
|---|---|---|
| 로컬 eval 러너 selftest | 7개 통과 | 모델 호출 0 |
| eval 게이트 selftest | 4개 통과 | CI 필터 근사 포함 |
| 명시 면제 게이트 | 과제 20건 미실행 표시 | 모델 성능 통과 아님 |
| 연결·CI·격리·기획 판정부 unittest | 23개 통과 | 합성 입력 포함, 제품 E2E 아님 |
| 스크린샷/대시보드/CSS 토큰 Vitest | 3파일 41개 통과 | React act 경고·jsdom navigation 미지원 출력 있음 |
| 실제 로컬 기획 원본 | 15블록 일치·적용 4건 정합 | 화면 최신성은 별도 |
| 두 체인 schema-diff | 실제 upgrade 후 양쪽 green | 원격 CI 실행 아님 |
| agent-browser | 현재 소스 Vite 로그인 폼·빈 입력 제출 disabled 확인 | 인증/등록/저장 미실행 |

브라우저는 별도 세션 `product-finish-readonly-0908`을 닫았고 Vite 임시 프로세스도 종료했다.
staging localhost는 Windows HTTP 200, WSL 브라우저에서는 연결 거절. 운영 설정을 바꾸지 않았다.
사용자 여정 전체 검증에는 격리 backend/DB/계정/저장소 준비가 여전히 필요하다.

## 실행 중 발견한 다른 쓰기

22:38~22:39에 메인이 작성하지 않은 `.agents/skills` 추가·`.codex/hooks.json`·
`scripts/agent-bridge.py` 변경 확인. bridge check가 2개가 아닌 12개 스킬 연결을 보고했다.
해당 공통 파일 편집은 멈추고 사용자에게 다른 쓰기 작업 존재 여부를 질문했다.
우리 CI/제품 변경을 이 외부 변경의 검증 근거로 쓰지 않는다.

## 남은 제품 범위

대장 19행의 상세는 `20260908-product-remaining-audit.md` 참조.
S3 고아 회수 archive 태그는 구현이 아니라 조사 문서다(`20260908-upload-reaper-reuse.md`).
완결 전송 원장 보존 기간은 아직 확인된 제품 결정이 없다. 기존 기간을 임의로 만들어 삭제하지 않는다.
Google IdP, 편의 기능 묶음, 배포/운영 검증 등의 미완료를 CI 수정 완료와 합쳐 닫지 않는다.
# 현재 작업 위치 갱신

후속: 하네스 작업 idle 확인 후 검증한 제품 변경을 원래 루트에 충돌 없이 반영했다.
현재 통합 결과는 루트, 상세는 `20260908-product-local-verification.md`.
루트에서 실제 로그인→GeoTIFF처리→등록→이미지표시→reload→로그아웃 E2E 재통과, DB 잔존0.
격리 사본은 중간 작업을 보존한 것이며 이후 상태 정본은 루트 대장/계획이다.

다른 `colab-v2-codex-harness` 작업이 같은 루트에서 공통 설정을 수정하는 것을 확인했다.
제품 추가 작업은 `.codex/worktrees/product-finish`의 `lane/product-finish` 브랜치로 격리했다.
최신 실행 계획과 E2E·stderr 수정은 그 사본의 `dev-package/prd/rounds/R-PRODUCT-FINISH.md`와
`scripts/e2e-login.sh`, `scripts/e2e-login.py`, `gates/tools/_pg.sh`에 있다.
초기 CI 변경은 루트에도 남아 있으므로 일괄 덮어쓰기·삭제하지 않는다.
core-api 980개, frontend 1,083개 통과. 실제 로그인·잘못된 비밀번호 거절·재접속·로그아웃 통과.
원격 CI·배포 완료는 아직 아니다.
